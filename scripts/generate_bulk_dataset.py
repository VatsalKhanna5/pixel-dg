import os
import sys
import time
import psutil
import argparse
import numpy as np
import h5py
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import threading
from glob import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.generators.matrix_generator import PixelLayoutGenerator
from src.simulators.openems_simulator import PixelEMSimulator
from src.utils.data_augmenter import SParamAugmenter

def generate_matrices(target_samples, only_connected=True):
    """Pre-generate a batch of matrices to separate logic and save time."""
    generator = PixelLayoutGenerator()
    matrices = []
    
    with tqdm(total=target_samples, desc="[1/3] Generating valid matrices", leave=True) as pbar:
        while len(matrices) < target_samples:
            mat = generator.generate_raw_matrix()
            is_conn = generator.check_dfs_connectivity(mat)
            if only_connected and not is_conn:
                continue
            matrices.append((mat, is_conn))
            pbar.update(1)
            
    return matrices

def simulate_sample(task, sim_base_dir="data/processed/sim_workers"):
    """Worker function to simulate one matrix."""
    import contextlib
    idx, mat, is_conn = task
    # Create thread-safe simulation directory
    sim_dir = os.path.join(sim_base_dir, f"worker_{os.getpid()}_{idx}")
    os.makedirs(sim_dir, exist_ok=True)
    
    simulator = PixelEMSimulator(config_path="configs/config.yaml")
    start_time = time.time()
    
    try:
        # Suppress OpenEMS native C++ console output natively
        fd_out = os.dup(1)
        fd_err = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        
        try:
            s_matrix_4x4 = simulator.run_simulation(mat, sim_dir)
        finally:
            os.dup2(fd_out, 1)
            os.dup2(fd_err, 2)
            os.close(devnull)
            os.close(fd_out)
            os.close(fd_err)
                
        # Store all variants to capture maximum info
        variants = SParamAugmenter.generate_8_variants(s_matrix_4x4, simulator.freq_points)
        variants_arr = np.array(variants, dtype=np.complex64)
        
        # Save raw 4x4 matrix too for future-proofing
        result = {
            'matrix': mat.astype(np.int8),
            'variants': variants_arr,
            's_matrix_4x4': np.array(s_matrix_4x4, dtype=np.complex64),
            'dfs_status': is_conn,
            'time_taken': time.time() - start_time,
            'status': 'success'
        }
        
    except Exception as e:
        result = {'idx': idx, 'status': 'failed', 'error': str(e)}
        
    return idx, result

def worker_health_monitor(stop_event):
    """Background thread to monitor system health without spamming."""
    while not stop_event.is_set():
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        # Update tqdm post-fix string instead of printing
        tqdm.write(f"\r[Health] CPU: {cpu}% | RAM: {ram}%", end="")
        time.sleep(10)

def master_pipeline(target_samples, max_workers, output_h5="data/processed/final_dataset.h5"):
    # Step 1: Pre-generate matrices
    matrices = generate_matrices(target_samples, only_connected=True)
    
    tasks = [(i, m[0], m[1]) for i, m in enumerate(matrices)]
    
    # Checkpoint directory
    checkpoint_dir = "data/processed/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Identify already completed tasks to resume
    existing_files = glob(f"{checkpoint_dir}/sample_*.npz")
    if existing_files:
        completed_indices = set([int(os.path.basename(f).split('_')[1].split('.')[0]) for f in existing_files])
        max_idx = max(completed_indices)
    else:
        completed_indices = set()
        max_idx = -1
        
    # User asks for `target_samples` NEW samples to be generated, 
    # we offset all current task indices to start strictly AFTER `max_idx`.
    # Update indices in our tasks array so they don't overwrite old data
    tasks = [(max_idx + 1 + i, m[0], m[1]) for i, m in enumerate(matrices)]
    
    print(f"\n[2/3] Resuming safely... {len(completed_indices)} already exist. Starting new tasks from index {max_idx + 1} up to {max_idx + target_samples}.")
    
    # Step 2: Parallel Simulation
    stop_event = threading.Event()
    health_thread = threading.Thread(target=worker_health_monitor, args=(stop_event,), daemon=True)
    health_thread.start()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(simulate_sample, t): t[0] for t in tasks}
        
        # Display progress out of the number of target new samples requested
        with tqdm(total=target_samples, desc="[2/3] Running Simulations") as pbar:
            for future in as_completed(futures):
                idx, result = future.result()
                
                if result['status'] == 'success':
                    # Save atomically to prevent data corruption
                    np.savez_compressed(
                        os.path.join(checkpoint_dir, f"sample_{idx}.npz"),
                        matrix=result['matrix'],
                        variants=result['variants'],
                        s_matrix_4x4=result['s_matrix_4x4'], # Keeping max info
                        dfs_status=result['dfs_status']
                    )
                pbar.update(1)
                
    stop_event.set()
    health_thread.join()
    
    # Step 3: Aggregate into massive HDF5
    print("\n[3/3] Aggregating results into final HDF5...")
    all_files = sorted(glob(f"{checkpoint_dir}/sample_*.npz"), key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
    
    with h5py.File(output_h5, "w") as f:
        # Create extendable datasets or just fit exact size
        total_valid = len(all_files)
        
        # Sneak peek at first valid file to get shapes
        if total_valid > 0:
            samp = np.load(all_files[0])
            f.create_dataset("matrices", shape=(total_valid, 15, 15), dtype="int8")
            f.create_dataset("s_parameters", shape=(total_valid, *samp['variants'].shape), dtype="complex64")
            f.create_dataset("s_parameters_raw_4x4", shape=(total_valid, *samp['s_matrix_4x4'].shape), dtype="complex64")
            f.create_dataset("dfs_status", shape=(total_valid,), dtype="bool")
            
            for i, fp in enumerate(tqdm(all_files, desc="Writing to HDF5")):
                try:
                    data = np.load(fp)
                    f["matrices"][i] = data["matrix"]
                    f["s_parameters"][i] = data["variants"]
                    f["s_parameters_raw_4x4"][i] = data["s_matrix_4x4"]
                    f["dfs_status"][i] = data["dfs_status"]
                except Exception as e:
                    print(f"Error loading {fp}: {e}")
                    
    print(f"\n✅ Dataset successfully aggregated and saved to {output_h5}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=20, help="Number of valid samples.")
    parser.add_argument("--workers", type=int, default=max(1, psutil.cpu_count(logical=False)-1), help="Max parallel processes")
    args = parser.parse_args()
    
    master_pipeline(args.samples, args.workers)
