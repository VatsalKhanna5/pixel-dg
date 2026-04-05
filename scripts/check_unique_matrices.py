import h5py
import numpy as np
import argparse
import os

def check_unique_matrices(h5_path):
    if not os.path.exists(h5_path):
        print(f"File not found: {h5_path}")
        return

    with h5py.File(h5_path, 'r') as f:
        if 'matrices' not in f:
            print(f"No 'matrices' dataset found in {h5_path}")
            return
            
        matrices = f['matrices'][:]
        total_matrices = len(matrices)
        
        if total_matrices == 0:
            print("The dataset is empty.")
            return

        # Flatten the matrices to 1D arrays to easily find unique rows
        # shape is (N, 15, 15), flatten to (N, 225)
        flattened_matrices = matrices.reshape(total_matrices, -1)
        
        # Find unique matrices
        unique_matrices = np.unique(flattened_matrices, axis=0)
        num_unique = len(unique_matrices)
        
        print(f"Total matrices in dataset: {total_matrices}")
        print(f"Unique matrices:           {num_unique}")
        print(f"Duplicate matrices:        {total_matrices - num_unique}")
        print(f"Percentage unique:         {(num_unique / total_matrices) * 100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check number of unique matrices in the HDF5 dataset.")
    parser.add_argument('--dataset', type=str, default='data/processed/final_dataset.h5',
                        help='Path to the HDF5 dataset file.')
    args = parser.parse_args()
    
    check_unique_matrices(args.dataset)
