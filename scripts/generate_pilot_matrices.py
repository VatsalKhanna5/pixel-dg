#!/usr/bin/env python3
"""
Script to generate a pilot dataset of pixelated matrices.
"""

import sys
import os
import time
import logging
import numpy as np
from pathlib import Path

# Add the src/ directory to the path so we can import generators
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.generators.matrix_generator import PixelLayoutGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    logging.info("Starting pilot matrix generation...")
    
    start_time = time.time()
    
    # Instantiate the generator
    generator = PixelLayoutGenerator(config_path="configs/config.yaml")
    
    # Generate dataset
    total_samples = 100
    logging.info(f"Requested total samples: {total_samples}")
    
    dataset = generator.generate_dataset(total_samples=total_samples)
    
    # Re-verify the generated dataset
    connected_count = 0
    disconnected_count = 0
    for i in range(total_samples):
        if generator.check_dfs_connectivity(dataset[i]):
            connected_count += 1
        else:
            disconnected_count += 1
            
    logging.info(f"Generated {total_samples} matrices.")
    logging.info(f"Connected matrices: {connected_count}")
    logging.info(f"Disconnected matrices: {disconnected_count}")
    
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the dataset
    output_path = output_dir / "pilot_100_matrices.npy"
    np.save(output_path, dataset)
    logging.info(f"Saved dataset to {output_path}")
    
    elapsed_time = time.time() - start_time
    logging.info(f"Execution completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()
