import os
import yaml
import numpy as np
from pathlib import Path
from typing import Tuple

from openEMS import openEMS
from CSXCAD import ContinuousStructure

class PixelEMSimulator:
    """
    Executes a 4-port 15x15 physical FDTD layout mapping in openEMS.
    Provides standard geometric rendering mapping 1s to perfectly overlapping metal trace pads
    embedded securely inside an extended physical bounded simulation domain with proper edge lumped ports.
    """

    def __init__(self, config_path: str = "configs/config.yaml"):
        """Initialize simulator definitions and frequency specifications."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.grid_size = self.config['geometry']['grid_size']
        self.pixel_size = self.config['geometry']['pixel_size_mm']
        self.overlap_ratio = self.config['geometry']['overlap_ratio']
        self.sub_size = self.config['geometry']['substrate_size_mm']
        
        self.sub_er = self.config['substrate']['dk']
        self.sub_h = self.config['substrate']['thickness_mm']
        self.sub_loss = self.config['substrate']['loss_tangent']
        
        self.f_start = self.config['simulation']['freq_start_ghz'] * 1e9
        self.f_stop = self.config['simulation']['freq_stop_ghz'] * 1e9
        
        # Build frequency points precisely from predefined lists
        self.freq_points = []
        for band in self.config['simulation']['freq_bands_ghz']:
            pts = np.linspace(band[0] * 1e9, band[1] * 1e9, self.config['simulation']['points_per_band'])
            self.freq_points.extend(pts)
        self.freq_points = np.array(sorted(list(set(self.freq_points))))
        
        self.unit = 1e-3  # Native unit mm
        self.port_impedance = 50.0

    def run_simulation(self, matrix: np.ndarray, sim_dir: str) -> np.ndarray:
        """
        Builds the 15x15 layout XML with overlap extensions, runs FDTD,
        extracts S-parameters dynamically at exact frequency locations, and returns.
        
        Returns: 
           np.ndarray: Complex matrix [Freq Points, 4 Ports, 4 Ports]
        """
        sim_path = Path(sim_dir)
        sim_path.mkdir(parents=True, exist_ok=True)
        
        csx = ContinuousStructure()
        
        z_bot = 0.0
        z_top = self.sub_h
        
        # Rogers Substrate Definition
        kappa = self.sub_loss * 2 * np.pi * 5e9 * self.sub_er * 8.854e-12
        substrate = csx.AddMaterial('substrate', epsilon=self.sub_er, kappa=kappa)
        substrate.AddBox(priority=0, 
                         start=[-self.sub_size/2, -self.sub_size/2, z_bot],
                         stop=[self.sub_size/2, self.sub_size/2, z_top])
                         
        # Complete bottom ground plane reflection pad
        gnd = csx.AddMetal('gnd')
        gnd.AddBox(priority=5, 
                   start=[-self.sub_size/2, -self.sub_size/2, z_bot],
                   stop=[self.sub_size/2, self.sub_size/2, z_bot])
                   
        trace = csx.AddMetal('trace')
        
        # Evaluate overlapping traces correctly: Add 0.12mm to each side. Total box size: 1.44 x 1.44 mm
        # as requested where 1.2 * 10% = 0.12 extension on EACH side
        overlap_ext = 0.12
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if matrix[i, j] == 1:
                    # x = (i - 7) * 1.2 and y = (j - 7) * 1.2
                    cx = (i - 7) * self.pixel_size
                    cy = (j - 7) * self.pixel_size
                    
                    x_start = cx - (self.pixel_size/2 + overlap_ext)
                    x_stop  = cx + (self.pixel_size/2 + overlap_ext)
                    y_start = cy - (self.pixel_size/2 + overlap_ext)
                    y_stop  = cy + (self.pixel_size/2 + overlap_ext)
                    
                    trace.AddBox(priority=10, 
                                 start=[x_start, y_start, z_top],
                                 stop=[x_stop, y_stop, z_top])
                                 
        mesh = csx.GetGrid()
        mesh.SetDeltaUnit(self.unit)
        
        fine_res = 0.3
        coarse_res = 2.0
        Z_AIR_PADDING = 15.0
        
        layout_max = 7 * self.pixel_size + self.pixel_size/2 + overlap_ext
        xy_mesh = np.unique(np.concatenate([
            np.linspace(-self.sub_size/2 - 10, -layout_max, int((self.sub_size/2 - layout_max + 10)/coarse_res)+1),
            np.linspace(-layout_max, layout_max, int(2*layout_max/fine_res)+1),
            np.linspace(layout_max, self.sub_size/2 + 10, int((self.sub_size/2 - layout_max + 10)/coarse_res)+1)
        ]))

        z_mesh = np.unique(np.concatenate([
            np.linspace(-Z_AIR_PADDING, z_bot, int(Z_AIR_PADDING/coarse_res) + 5),
            np.linspace(z_bot, z_top, int(self.sub_h/fine_res) + 2),
            np.linspace(z_top, z_top + Z_AIR_PADDING, int(Z_AIR_PADDING/coarse_res) + 5)
        ]))
        
        mesh.AddLine('x', xy_mesh)
        mesh.AddLine('y', xy_mesh)
        mesh.AddLine('z', z_mesh)
        
        # Instantiate execution bounds
        FDTD = openEMS(NrTS=50000, EndCriteria=1e-5)
        FDTD.SetCSX(csx)
        FDTD.SetBoundaryCond(['PML_8'] * 6)
        
        f0 = 0.5 * (self.f_start + self.f_stop)
        fc = 0.5 * (self.f_stop - self.f_start)
        FDTD.SetGaussExcite(f0, fc)
        
        pw = self.pixel_size / 2
        port_objs = []
        
        # P1: Left (X = -7 * 1.2, Y = 0)
        p1_x = -7 * self.pixel_size
        port1 = FDTD.AddLumpedPort(1, self.port_impedance, 
                                   [p1_x - pw, -pw, z_bot], 
                                   [p1_x + pw, pw, z_top], 'z', excite=1)
        port_objs.append(port1)
        
        # P2: Right (X = 7 * 1.2, Y = 0)
        p2_x = 7 * self.pixel_size
        port2 = FDTD.AddLumpedPort(2, self.port_impedance, 
                                   [p2_x - pw, -pw, z_bot], 
                                   [p2_x + pw, pw, z_top], 'z', excite=0)
        port_objs.append(port2)

        # P3: Bottom (X = 0, Y = -7 * 1.2)
        p3_y = -7 * self.pixel_size
        port3 = FDTD.AddLumpedPort(3, self.port_impedance, 
                                   [-pw, p3_y - pw, z_bot], 
                                   [pw, p3_y + pw, z_top], 'z', excite=0)
        port_objs.append(port3)

        # P4: Top (X = 0, Y = 7 * 1.2)
        p4_y = 7 * self.pixel_size
        port4 = FDTD.AddLumpedPort(4, self.port_impedance, 
                                   [-pw, p4_y - pw, z_bot], 
                                   [pw, p4_y + pw, z_top], 'z', excite=0)
        port_objs.append(port4)
        
        # Core execution
        orig_cwd = os.getcwd()
        try:
            xml_file = str((sim_path / "sim.xml").absolute())
            FDTD.Write2XML(xml_file)
            FDTD.Run(str(sim_path.absolute()), verbose=0)
        finally:
            os.chdir(orig_cwd)
            
        # Post Calculate S-parameters
        ret_s_matrix = np.zeros((len(self.freq_points), 4, 4), dtype=complex)
        
        for p in port_objs:
            p.CalcPort(str(sim_path.absolute()), self.freq_points)
            
        incident = port_objs[0].uf_inc
        ret_s_matrix[:, 0, 0] = port_objs[0].uf_ref / incident
        ret_s_matrix[:, 1, 0] = port_objs[1].uf_ref / incident
        ret_s_matrix[:, 2, 0] = port_objs[2].uf_ref / incident
        ret_s_matrix[:, 3, 0] = port_objs[3].uf_ref / incident
        
        return ret_s_matrix
