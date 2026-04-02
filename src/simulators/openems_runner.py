import sys
import os
import numpy as np
from pathlib import Path
import shutil
import yaml

from openEMS import openEMS
from CSXCAD import ContinuousStructure

class OpenEMSRunner:
    def __init__(self, config_path: str = "configs/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.unit = 1e-3
        self.freq_start = min([band[0] for band in self.config['simulation']['freq_bands_ghz']]) * 1e9
        self.freq_stop = max([band[1] for band in self.config['simulation']['freq_bands_ghz']]) * 1e9
        
        self.sub_er = self.config['substrate']['dk']
        self.sub_h = self.config['substrate']['thickness_mm']
        self.px_size = self.config['geometry']['pixel_size_mm']
        self.grid_size = self.config['geometry']['grid_size']
        self.overlap = self.config['geometry']['overlap_ratio']
        
        self.port_imp = 50.0  # Ohms
    
    def setup_geometry(self, matrix: np.ndarray, sim_dir: Path):
        """ Maps the geometry and setups openEMS for a 15x15 pixel matrix. """
        csx = ContinuousStructure()
        
        # Dimensions
        board_w = self.px_size * self.grid_size
        board_l = self.px_size * self.grid_size
        
        z_sub_bot = 0
        z_sub_top = self.sub_h
        z_trace = z_sub_top
        
        # Substrate & Ground
        substrate = csx.AddMaterial('substrate', epsilon=self.sub_er)
        substrate.AddBox(priority=0, start=[-board_w/2, -board_l/2, z_sub_bot],
                         stop=[board_w/2, board_l/2, z_sub_top])
                         
        gnd = csx.AddMetal('gnd')
        gnd.AddBox(priority=5, start=[-board_w/2, -board_l/2, z_sub_bot],
                   stop=[board_w/2, board_l/2, z_sub_bot])
                   
        trace = csx.AddMetal('trace')
        
        px_eff = self.px_size * (1.0 + self.overlap)
        
        # Maps the 15x15 matrix (row=y, col=x for visual map, or vice versa)
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if matrix[r, c] == 1:
                    # Map (r, c) to coordinates. Centered at 0,0
                    # c goes along x, r goes along y
                    cx = (c - self.grid_size/2 + 0.5) * self.px_size
                    cy = (self.grid_size/2 - 0.5 - r) * self.px_size
                    
                    trace.AddBox(priority=10, 
                                 start=[cx - px_eff/2, cy - px_eff/2, z_trace],
                                 stop=[cx + px_eff/2, cy + px_eff/2, z_trace])
                                 
        # Build Mesh
        mesh = csx.GetGrid()
        mesh.SetDeltaUnit(self.unit)
        fine_res = 0.3
        coarse_res = 2.0
        
        # Simple regular mesh over the board
        mx = np.linspace(-board_w/2, board_w/2, int(board_w/fine_res))
        my = np.linspace(-board_l/2, board_l/2, int(board_l/fine_res))
        mz = np.array([-15, z_sub_bot, z_sub_top, 15])
        
        # Expand out
        mx = np.concatenate([[-board_w/2 - 5], mx, [board_w/2 + 5]])
        my = np.concatenate([[-board_l/2 - 5], my, [board_l/2 + 5]])
        
        mesh.AddLine('x', np.unique(mx))
        mesh.AddLine('y', np.unique(my))
        mesh.AddLine('z', np.unique(mz))
        
        FDTD = openEMS(NrTS=30000, EndCriteria=1e-4) # faster for test
        FDTD.SetCSX(csx)
        FDTD.SetGaussExcite(0.5*(self.freq_start + self.freq_stop), 0.5*(self.freq_stop - self.freq_start))
        
        BC = ['PML_8'] * 6
        FDTD.SetBoundaryCond(BC)
        
        # Add 4 Ports at exact edges
        # Port 1: Left (-x), excited
        p1_x = -board_w/2
        p1_start = [p1_x, -self.px_size/2, z_sub_bot]
        p1_stop  = [p1_x, self.px_size/2, z_sub_top]
        FDTD.AddLumpedPort(1, self.port_imp, p1_start, p1_stop, 'z', excite=1)
        
        # Port 2: Right (+x)
        p2_x = board_w/2
        p2_start = [p2_x, -self.px_size/2, z_sub_bot]
        p2_stop  = [p2_x, self.px_size/2, z_sub_top]
        FDTD.AddLumpedPort(2, self.port_imp, p2_start, p2_stop, 'z', excite=0)
        
        # Port 3: Top (+y)
        p3_y = board_l/2
        p3_start = [-self.px_size/2, p3_y, z_sub_bot]
        p3_stop  = [self.px_size/2, p3_y, z_sub_top]
        FDTD.AddLumpedPort(3, self.port_imp, p3_start, p3_stop, 'z', excite=0)
        
        # Port 4: Bottom (-y)
        p4_y = -board_l/2
        p4_start = [-self.px_size/2, p4_y, z_sub_bot]
        p4_stop  = [self.px_size/2, p4_y, z_sub_top]
        FDTD.AddLumpedPort(4, self.port_imp, p4_start, p4_stop, 'z', excite=0)
        
        return FDTD, str((sim_dir / "sim.xml").absolute())

    def simulate_matrix(self, matrix: np.ndarray, index: int):
        sim_dir = Path(f"data/processed/sim_{index}")
        if sim_dir.exists():
            shutil.rmtree(sim_dir)
        sim_dir.mkdir(parents=True, exist_ok=True)
        
        FDTD, xml_path = self.setup_geometry(matrix, sim_dir)
        
        orig_cwd = os.getcwd()
        try:
            FDTD.Write2XML(xml_path)
            FDTD.Run(str(sim_dir.absolute()), verbose=1)
            print(f"Successfully ran simulation {index}")
            return True
        except Exception as e:
            print(f"Simulation {index} failed: {e}")
            return False
        finally:
            os.chdir(orig_cwd)

