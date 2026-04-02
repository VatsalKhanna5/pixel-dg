#!/usr/bin/env python3
"""
Phase 1: Verified EM Simulation (Baseline)

2-port passive transmission network (Microstrip transmission line).
Generates real EM simulation data using openEMS with proper mesh and ports.
"""

from openEMS import openEMS
from CSXCAD import ContinuousStructure
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import shutil

# ============================================================================
# CONFIGURATION
# ============================================================================

# Unit: mm
unit = 1e-3

# Frequency range
FREQ_START = 2e9      # 2 GHz
FREQ_STOP = 10e9      # 10 GHz

# Substrate (Rogers 4350B equivalent)
SUBSTRATE_ER = 3.48
SUBSTRATE_THICKNESS = 0.508  # 20 mil in mm
SUBSTRATE_LOSS = 0.004

# Geometry (in mm)
TRACE_WIDTH = 1.15    # approx 50 Ohm line width for 20mil RO4350B
SUBSTRATE_LENGTH_X = 50.0   # length of the microstrip routing
SUBSTRATE_WIDTH_Y = 20.0

PORT_IN_X = -SUBSTRATE_LENGTH_X / 2
PORT_OUT_X = SUBSTRATE_LENGTH_X / 2

# Port impedance
PORT_IMPEDANCE = 50   # Ohms

# Mesh resolution
FINE_RESOLUTION = 0.3     # mm
COARSE_RESOLUTION = 2.0   # mm

# ============================================================================
# SETUP OUTPUT DIRECTORIES
# ============================================================================

output_base = Path("simulations/results/test_case")
output_base.mkdir(parents=True, exist_ok=True)

sim_dir = output_base / "sim_tmp"
if sim_dir.exists():
    shutil.rmtree(sim_dir)
sim_dir.mkdir(exist_ok=True)

sim_xml = str(sim_dir / "transmission_line.xml")

# ============================================================================
# BUILD GEOMETRY
# ============================================================================

print("[SETUP] Creating geometry...")

csx = ContinuousStructure()

# Define coordinate system
z_substrate_bottom = 0
z_substrate_top = z_substrate_bottom + SUBSTRATE_THICKNESS
z_trace = z_substrate_top

# Substrate material (Rogers 4350B)
substrate_kappa = SUBSTRATE_LOSS * 2 * np.pi * 5e9 * SUBSTRATE_ER
substrate = csx.AddMaterial('substrate', epsilon=SUBSTRATE_ER, )

# EXTEND materials past the mesh limits so PML can match their impedance without reflections!
EXT_X = 20.0 # 20mm extra material outside simulation space for clean PML matching

sub_start = [-SUBSTRATE_LENGTH_X/2 - EXT_X, -SUBSTRATE_WIDTH_Y/2, z_substrate_bottom]
sub_stop = [SUBSTRATE_LENGTH_X/2 + EXT_X, SUBSTRATE_WIDTH_Y/2, z_substrate_top]
substrate.AddBox(priority=0, start=sub_start, stop=sub_stop)

# Ground plane (PEC)
gnd = csx.AddMetal('gnd')
gnd_start = [-SUBSTRATE_LENGTH_X/2 - EXT_X, -SUBSTRATE_WIDTH_Y/2, z_substrate_bottom]
gnd_stop = [SUBSTRATE_LENGTH_X/2 + EXT_X, SUBSTRATE_WIDTH_Y/2, z_substrate_bottom]
gnd.AddBox(priority=5, start=gnd_start, stop=gnd_stop)

# Conductive Trace (PEC) -> Continuous path between ends of substrate
trace = csx.AddMetal('trace')
trace_start = [-SUBSTRATE_LENGTH_X/2 - EXT_X, -TRACE_WIDTH/2, z_trace]
trace_stop = [SUBSTRATE_LENGTH_X/2 + EXT_X, TRACE_WIDTH/2, z_trace]
trace.AddBox(priority=10, start=trace_start, stop=trace_stop)

# ============================================================================
# SETUP MESH
# ============================================================================

print("[SETUP] Configuring mesh...")

mesh = csx.GetGrid()
mesh.SetDeltaUnit(unit)

# X direction: MESH STOPS EXACTLY ON PORTS, the PML layer naturally handles waves moving outward
x_mesh = np.linspace(-SUBSTRATE_LENGTH_X/2, SUBSTRATE_LENGTH_X/2, int(SUBSTRATE_LENGTH_X/FINE_RESOLUTION)+1)
mesh.AddLine('x', x_mesh)

# Y direction: Expand outwards for width pad
y_mesh = np.linspace(-SUBSTRATE_WIDTH_Y/2 - 10, SUBSTRATE_WIDTH_Y/2 + 10, int((SUBSTRATE_WIDTH_Y+20)/FINE_RESOLUTION)+1)
mesh.AddLine('y', y_mesh)

# Z direction: fine in substrate
z_mesh = np.unique(np.concatenate([
    np.linspace(-15, z_substrate_bottom, 7),
    np.linspace(z_substrate_bottom, z_substrate_top, 3),
    np.linspace(z_substrate_top, 15, 7)
]))
mesh.AddLine('z', z_mesh)

# ============================================================================
# SETUP FDTD
# ============================================================================

print("[SETUP] Initializing openEMS FDTD...")

# Create openEMS instance
FDTD = openEMS(NrTS=50000, EndCriteria=1e-5)
FDTD.SetCSX(csx)
FDTD.SetGaussExcite(0.5*(FREQ_START + FREQ_STOP), 0.5*(FREQ_STOP - FREQ_START))

# Use standard PML boundary conditions on all sides as we expanded the mesh to accommodate it
BC = ['PML_8', 'PML_8', 'PML_8', 'PML_8', 'MUR', 'MUR']
FDTD.SetBoundaryCond(BC)

# ============================================================================
# ADD PORTS (2-Port Transmission Structure)
# ============================================================================

print("[SETUP] Defining 2-port excitation...")

# Port 1 - Input (Excited)
p1_start = [PORT_IN_X, -TRACE_WIDTH/2, z_substrate_bottom]
p1_stop  = [PORT_IN_X, TRACE_WIDTH/2, z_substrate_top]
port1 = FDTD.AddLumpedPort(1, PORT_IMPEDANCE, p1_start, p1_stop, 'z', excite=1)

# Port 2 - Output (Passive)
p2_start = [PORT_OUT_X, -TRACE_WIDTH/2, z_substrate_bottom]
p2_stop  = [PORT_OUT_X, TRACE_WIDTH/2, z_substrate_top]
port2 = FDTD.AddLumpedPort(2, PORT_IMPEDANCE, p2_start, p2_stop, 'z', excite=0)

# ============================================================================
# RUN SIMULATION
# ============================================================================

print(f"\n{'='*70}")
print(f"[SIMULATION] Starting FDTD...")
print(f"{'='*70}")
print(f"  Mesh points x: {len(x_mesh)}")
print(f"  Mesh points y: {len(y_mesh)}")
print(f"  Mesh points z: {len(z_mesh)}")
print(f"  Frequency: [{FREQ_START/1e9:.1f}, {FREQ_STOP/1e9:.1f}] GHz")
print(f"  Timesteps: 50000")
print(f"  Simulation folder: {sim_dir}")
print(f"{'='*70}\n")

orig_cwd = os.getcwd()

try:
    FDTD.Write2XML(sim_xml)
    FDTD.Run(str(sim_dir.absolute()), verbose=0)
    print(f"\n{'='*70}")
    print(f"[SUCCESS] Simulation completed")
    print(f"{'='*70}\n")
except Exception as e:
    print(f"\n{'='*70}")
    print(f"[ERROR] Simulation failed: {e}")
    print(f"{'='*70}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    os.chdir(orig_cwd)

# ============================================================================
# EXTRACT S-PARAMETERS
# ============================================================================

print("[POST-PROCESSING] Extracting S-parameters...")

try:
    freq = np.linspace(FREQ_START, FREQ_STOP, 501)
    
    port1.CalcPort(str(sim_dir.absolute()), freq)
    port2.CalcPort(str(sim_dir.absolute()), freq)
    
    # Extract S11 (Reflection at Port 1)
    s11 = port1.uf_ref / port1.uf_inc
    s11_mag = np.abs(s11)
    
    # Extract S21 (Transmission from Port 1 to Port 2)
    s21 = port2.uf_ref / port1.uf_inc
    s21_mag = np.abs(s21)
    
    print(f"  Extracted {len(freq)} S11/S21 points from simulation")
    
except Exception as e:
    print(f"[ERROR] Failed to process simulation data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# VALIDATION
# ============================================================================

print("\n[VALIDATION]")

nan_count = np.sum(np.isnan(s11_mag)) + np.sum(np.isnan(s21_mag))
inf_count = np.sum(np.isinf(s11_mag)) + np.sum(np.isinf(s21_mag))
if nan_count > 0 or inf_count > 0:
    print(f"  ✗ FAILED: NaN/Inf detected in S-parameters")
    sys.exit(1)
print(f"  ✓ No NaN/Inf values")

s11_max = np.max(s11_mag)
if s11_max > 1.05:
    print(f"  ✗ FAILED: |S11| exceeds physics bound: {s11_max:.6f}")
    sys.exit(1)
print(f"  ✓ |S11| bounded: Max = {s11_max:.6f}")

s21_mean = np.mean(s21_mag)
if s21_mean < 0.05:
    print(f"  ✗ FAILED: |S21| is practically zero (mean={s21_mean:.6f}). Structure is an open circuit.")
    sys.exit(1)
print(f"  ✓ |S21| confirms passive transmission: Mean = {s21_mean:.6f}")

s11_std = np.std(s11_mag)
if s11_std < 0.001:
    print(f"  ⚠ Response is very flat (std={s11_std:.8f})")
else:
    print(f"  ✓ Response characteristic is dynamic (std={s11_std:.6f})")

print(f"\n[RESULTS]")
print(f"  S11 max:        {s11_max:.6f}")
print(f"  S21 mean:       {s21_mean:.6f}")
print(f"  S21 max:        {np.max(s21_mag):.6f}")

# ============================================================================
# PLOT S-PARAMETERS
# ============================================================================

print(f"\n[PLOTTING] Generating S-parameter response...")

fig, ax = plt.subplots(figsize=(12, 7))

freq_ghz = freq / 1e9
s11_db = 20 * np.log10(np.maximum(s11_mag, 1e-12))
s21_db = 20 * np.log10(np.maximum(s21_mag, 1e-12))

ax.plot(freq_ghz, s11_db, 'b-', linewidth=2.5, label='|S11| (Reflection)')
ax.plot(freq_ghz, s21_db, 'r-', linewidth=2.5, label='|S21| (Transmission)')
ax.set_xlabel('Frequency (GHz)', fontsize=12, fontweight='bold')
ax.set_ylabel('Magnitude (dB)', fontsize=12, fontweight='bold')
ax.set_title('2-Port Passive Transmission Line: S-Parameters', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.4, linestyle='--')
ax.legend(fontsize=11, loc='best')
ax.set_xlim([FREQ_START/1e9, FREQ_STOP/1e9])

plt.tight_layout()

plot_path = output_base / "s_parameters.png"
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"  Plot saved: {plot_path}")
plt.close()

data_path = output_base / "s_parameters_data.npy"
np.save(data_path, np.column_stack([freq, s11_mag, s21_mag]))
print(f"  Data saved: {data_path}")

print(f"\n{'='*70}")
print(f"✓ PHASE 1 COMPLETE: 2-Port Transmission Network Validated (Real Data)")
print(f"{'='*70}\n")

sys.exit(0)
