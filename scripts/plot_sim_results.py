import sys
import os
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import yaml

def load_port_data(sim_dir, port_number):
    u = np.loadtxt(os.path.join(sim_dir, f'port_ut_{port_number}'))
    i = np.loadtxt(os.path.join(sim_dir, f'port_it_{port_number}'))
    return u, i

def main():
    matrices_path = Path("data/raw/pilot_100_matrices.npy")
    if not matrices_path.exists():
        print("Matrices not found!")
        return
        
    data = np.load(matrices_path, allow_pickle=True)
    
    with open("configs/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
        
    freq_start = min([band[0] for band in config['simulation']['freq_bands_ghz']]) * 1e9
    freq_stop = max([band[1] for band in config['simulation']['freq_bands_ghz']]) * 1e9
    freq = np.linspace(freq_start, freq_stop, 201)
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    for idx in range(2):
        sim_dir = Path(f"data/processed/sim_{idx}")
        if not sim_dir.exists():
            continue
            
        matrix = data[idx]
        
        u1, i1 = load_port_data(sim_dir, 1)
        u2, i2 = load_port_data(sim_dir, 2)
        
        dt = u1[1, 0] - u1[0, 0]
        
        uf1 = np.sum(u1[:,1:] * np.exp(-1j * 2 * np.pi * freq * u1[:,0:1]), axis=0) * dt
        if1 = np.sum(i1[:,1:] * np.exp(-1j * 2 * np.pi * freq * i1[:,0:1]), axis=0) * dt
        
        uf2 = np.sum(u2[:,1:] * np.exp(-1j * 2 * np.pi * freq * u2[:,0:1]), axis=0) * dt
        if2 = np.sum(i2[:,1:] * np.exp(-1j * 2 * np.pi * freq * i2[:,0:1]), axis=0) * dt
        
        z0 = 50.0 
        
        a1 = 0.5 * (uf1 + if1 * z0) / np.sqrt(z0)
        b1 = 0.5 * (uf1 - if1 * z0) / np.sqrt(z0)
        
        b2 = 0.5 * (uf2 - if2 * z0) / np.sqrt(z0)
        
        s11 = b1 / a1
        s21 = b2 / a1
        
        s11_db = 20 * np.log10(np.abs(s11.flatten()) + 1e-12)
        s21_db = 20 * np.log10(np.abs(s21.flatten()) + 1e-12)
        
        axes[idx].plot(freq / 1e9, s11_db, label='S11 (dB)', color='red')
        axes[idx].plot(freq / 1e9, s21_db, label='S21 (dB)', color='blue')
        axes[idx].set_title(f"Simulation {idx} S-Parameters")
        axes[idx].set_xlabel("Frequency (GHz)")
        axes[idx].set_ylabel("Magnitude (dB)")
        axes[idx].legend()
        axes[idx].grid(True)
        axes[idx].set_ylim([-60, 0])
        
    plt.tight_layout()
    plt.savefig('data/processed/s_parameters_sim0_1.png')
    print("Plot saved to data/processed/s_parameters_sim0_1.png")

if __name__ == '__main__':
    main()
