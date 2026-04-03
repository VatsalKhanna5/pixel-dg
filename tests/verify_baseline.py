import numpy as np
import matplotlib.pyplot as plt
from src.simulators.openems_simulator import PixelEMSimulator
from src.utils.data_augmenter import SParamAugmenter
import os

print("--- Initializing Baseline 50-Ohm Transmission Line Verification ---")
# 1. Create a 15x15 matrix
matrix = np.zeros((15, 15), dtype=np.int8)

# 2. Add continuous 50-ohm trace from Left (Port 1) to Right (Port 2)
# Left is i=0, j=7. Right is i=14, j=7.
for i in range(15):
    matrix[i, 7] = 1

# Save visual representation
plt.figure(figsize=(6,6))
plt.imshow(matrix.T, cmap='Blues', origin='lower', extent=[-7.5*1.2, 7.5*1.2, -7.5*1.2, 7.5*1.2])
plt.title("Baseline 50-Ohm Transmission Line\nLeft: Port 1, Right: Port 2, Bottom: Port 3, Top: Port 4")
plt.xlabel("X (mm)")
plt.ylabel("Y (mm)")
plt.grid(True, color='gray', linestyle='--', linewidth=0.5)
plt.colorbar(label='Metal presence')
plt.savefig("baseline_layout.png", dpi=300)
print("Saved baseline layout 2D plot to baseline_layout.png")

# 3. Setup Simulator
sim = PixelEMSimulator(config_path="configs/config.yaml")

print("Beginning openEMS simulation... (This may take a minute). The 3D layout .xml is dumped in the temp_baseline folder.")
# Run simulation
s_params_4port = sim.run_simulation(matrix, sim_dir="temp_baseline")

freqs = sim.freq_points / 1e9  # GHz

# Because it's a completely symmetric 50-ohm straight line, S11 should be very low (ideally < -10 dB or lower), S21 near 0 dB
s11_mag = 20 * np.log10(np.abs(s_params_4port[:, 0, 0]) + 1e-12)
s21_mag = 20 * np.log10(np.abs(s_params_4port[:, 1, 0]) + 1e-12)

plt.figure(figsize=(10,6))
plt.plot(freqs, s11_mag, label='|S11| (Reflection)', color='red', linewidth=2)
plt.plot(freqs, s21_mag, label='|S21| (Transmission)', color='blue', linewidth=2)
plt.axhline(-10, color='gray', linestyle='--', alpha=0.7, label='-10 dB Threshold')
plt.title("Baseline Transmission Line S-Parameters\nTheoretical 50-ohm match expectation")
plt.xlabel("Frequency (GHz)")
plt.ylabel("Magnitude (dB)")
plt.legend()
plt.grid(True)
plt.savefig("baseline_S_params.png", dpi=300)
print("Saved S-parameter results to baseline_S_params.png")
print("Baseline Verification Complete. You can visualize the 3D structure by inspecting temp_baseline/pixel_structure.xml with AppCSXCAD.")
