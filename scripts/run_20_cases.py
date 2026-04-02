import sys
import os
import numpy as np

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.generators.matrix_generator import PixelLayoutGenerator
from src.simulators.openems_simulator import PixelEMSimulator

def main():
    print("=== Initializing Generator and Simulator ===")
    os.makedirs("data/processed", exist_ok=True)
    
    generator = PixelLayoutGenerator()
    simulator = PixelEMSimulator(config_path="/home/dr-robin-kalyan/Desktop/pixel/configs/config.yaml")
    
    # We will generate and simulate 20 matrices
    total_cases = 20
    print(f"Generating dataset of {total_cases} samples (80% Connected, 20% Disconnected)...")
    dataset = list(generator.generate_dataset(total_cases))
    
    results = []
    for i, (matrix, is_connected) in enumerate(dataset):
        print(f"\n--- Running Case {i+1}/{total_cases} (Graph Connected: {is_connected}) ---")
        sim_dir = f"data/processed/sim_case_{(i+1):02d}"
        
        # Run FDTD
        s_parameters = simulator.run_simulation(matrix, sim_dir)
        
        # Calculate Peak S11 (Reflection) and S21 (Transmission) Magnitude in dB
        # ret_s_matrix dims: (Freq, Port, Port)
        # Port 1 is the forced excitation port (index 0). 
        # Port 1 Reflection (S11) -> index 0, 0
        # Port 2 Transmission (S21) -> index 1, 0
        freqs = simulator.freq_points
        s11_mag = 20 * np.log10(np.abs(s_parameters[:, 0, 0]) + 1e-12)
        s21_mag = 20 * np.log10(np.abs(s_parameters[:, 1, 0]) + 1e-12)
        
        max_s11 = np.max(s11_mag)
        max_s21 = np.max(s21_mag)
        
        print(f"Max |S11| (Reflection): {max_s11:>7.2f} dB")
        print(f"Max |S21| (Transmission): {max_s21:>7.2f} dB")
        
        if is_connected and max_s21 > -30:
            status = "PASS (Signal propagated)"
        elif not is_connected and max_s21 < -10:
            status = "PASS (Signal blocked/open circuit)"
        else:
            status = "REVIEW"
            
        print(f"Validation Status: {status}")
        results.append((is_connected, max_s11, max_s21, status))
        
    print("\n\n=== Final Report Summary ===")
    print(f"{'Case':<6} | {'Topology':<15} | {'Max S11(dB)':<12} | {'Max S21(dB)':<12} | {'Status'}")
    print("-" * 65)
    for i, (conn, s11, s21, status) in enumerate(results):
        conn_str = "Connected" if conn else "Disconnected"
        print(f"{(i+1):02d}     | {conn_str:<15} | {s11:>11.2f} | {s21:>11.2f} | {status}")

if __name__ == "__main__":
    main()
