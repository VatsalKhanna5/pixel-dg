import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
from src.simulators.openems_runner import OpenEMSRunner

def main():
    matrices_path = Path("data/raw/pilot_100_matrices.npy")
    if not matrices_path.exists():
        return
        
    data = np.load(matrices_path, allow_pickle=True)
    runner = OpenEMSRunner()
    
    for i in range(2):
        matrix = data[i]
        
        print("Matrix footprint:")
        for row in matrix:
            print("".join(["██" if val == 1 else "  " for val in row]))
            
        success = runner.simulate_matrix(matrix, i)
        if success:
            print(f"Simulation {i} successfully finished!")
            
if __name__ == '__main__':
    main()
