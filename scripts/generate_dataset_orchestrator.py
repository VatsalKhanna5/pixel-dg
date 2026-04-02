import os
import sys
import h5py
import time
import logging
import argparse
import numpy as np

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.generators.matrix_generator import PixelLayoutGenerator
from src.simulators.openems_simulator import PixelEMSimulator
from src.utils.data_augmenter import SParamAugmenter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_hdf5(h5_path: str, num_freqs: int):
    """Initializes the HDF5 storage with resizable datasets."""
    os.makedirs(os.path.dirname(h5_path), exist_ok=True)
    with h5py.File(h5_path, "a") as f:
        if "matrices" not in f:
            f.create_dataset("matrices", shape=(0, 15, 15), maxshape=(None, 15, 15), dtype="int8")
        if "s_parameters" not in f:
            f.create_dataset("s_parameters", shape=(0, 8, num_freqs, 2, 2), maxshape=(None, 8, num_freqs, 2, 2), dtype="complex64")
        if "dfs_status" not in f:
            f.create_dataset("dfs_status", shape=(0,), maxshape=(None,), dtype="bool")

def append_to_hdf5(h5_path: str, matrix: np.ndarray, variants: np.ndarray, dfs_status: bool):
    """Appends a single sample's augmented data to the HDF5 file dynamically."""
    with h5py.File(h5_path, "a") as f:
        dset_m = f["matrices"]
        dset_s = f["s_parameters"]
        dset_d = f["dfs_status"]

        curr_len = len(dset_m)
        dset_m.resize((curr_len + 1, 15, 15))
        dset_s.resize((curr_len + 1, 8, variants.shape[1], 2, 2))
        dset_d.resize((curr_len + 1,))

        dset_m[curr_len] = matrix.astype(np.int8)
        dset_s[curr_len] = variants.astype(np.complex64)
        dset_d[curr_len] = dfs_status

def run_pipeline(target_samples: int):
    """Orchestrates FDTD mesh looping, bounding strict 80/20 physical limits, and ML augmentation."""
    logging.info(f"Initializing Generator and FDTD Simulator for {target_samples} total target samples.")
    
    generator = PixelLayoutGenerator()
    simulator = PixelEMSimulator(config_path="configs/config.yaml")
    
    num_freqs = len(simulator.freq_points)
    h5_path = "data/processed/class_f_dataset.h5"
    initialize_hdf5(h5_path, num_freqs)
    
    target_conn = int(target_samples * 0.8)
    target_disconn = target_samples - target_conn
    
    saved_conn = 0
    saved_disconn = 0
    sim_dir = "data/processed/auto_orchestrator_sim"
    os.makedirs(sim_dir, exist_ok=True)
    
    samples_since_flush = 0

    while saved_conn < target_conn or saved_disconn < target_disconn:
        mat = generator.generate_raw_matrix()
        is_conn = generator.check_dfs_connectivity(mat)
        
        if is_conn and saved_conn >= target_conn:
            continue
        if not is_conn and saved_disconn >= target_disconn:
            continue
            
        logging.info(f"Starting FDTD Simulation for new matrix (DFS Connected: {is_conn})...")
        start_time = time.time()
        
        try:
            # Step B: Run OpenEMS
            s_matrix_4x4 = simulator.run_simulation(mat, sim_dir)
        except Exception as e:
            # Fault Tolerance: Catch meshing crashes or OpenEMS bounds failures cleanly.
            logging.warning(f"OpenEMS Simulation failed or mesh collided. Skipping matrix. Error: {e}")
            continue

        try:
            # Step C: Augmentation
            variants = SParamAugmenter.generate_8_variants(s_matrix_4x4, simulator.freq_points)
            variants_arr = np.array(variants, dtype=np.complex64) # Shape: (8, 21, 2, 2)
            
            # Step D: Append and Flush
            append_to_hdf5(h5_path, mat, variants_arr, is_conn)
        except Exception as e:
            logging.error(f"Augmentation or HDF5 storage failed: {e}")
            continue
        
        t_elapsed = time.time() - start_time
        
        if is_conn:
            saved_conn += 1
        else:
            saved_disconn += 1
            
        samples_since_flush += 1
        if samples_since_flush >= 10:
            with h5py.File(h5_path, "a") as f:
                f.flush()
            samples_since_flush = 0
            
        logging.info(f"Successfully processed and stored 8 dataset variants. Time: {t_elapsed:.2f}s | Progress -> Connected: {saved_conn}/{target_conn} | Disconnected: {saved_disconn}/{target_disconn}")

    logging.info("Master Dataset Orchestration Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Master Data Generation Pipeline for FDTD Pixels.")
    parser.add_argument("--samples", type=int, default=10, help="Target number of fully validated and expanded FDTD samples.")
    args = parser.parse_args()
    
    run_pipeline(args.samples)
