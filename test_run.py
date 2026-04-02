import os
from pathlib import Path
from openEMS import openEMS
from CSXCAD import ContinuousStructure
import numpy as np

csx = ContinuousStructure()
SUBSTRATE_LENGTH_X = 50.0
SUBSTRATE_WIDTH_Y = 20.0
TRACE_WIDTH = 1.15
z_sub_bot = 0
z_sub_top = 0.508
SUBSTRATE_ER = 3.48

substrate = csx.AddMaterial('substrate', epsilon=SUBSTRATE_ER)
substrate.AddBox(priority=0, start=[-SUBSTRATE_LENGTH_X, -SUBSTRATE_WIDTH_Y, z_sub_bot],
                 stop=[SUBSTRATE_LENGTH_X, SUBSTRATE_WIDTH_Y, z_sub_top])

gnd = csx.AddMetal('gnd')
gnd.AddBox(priority=5, start=[-SUBSTRATE_LENGTH_X, -SUBSTRATE_WIDTH_Y, z_sub_bot],
           stop=[SUBSTRATE_LENGTH_X, SUBSTRATE_WIDTH_Y, z_sub_bot])

trace = csx.AddMetal('trace')
trace.AddBox(priority=10, start=[-SUBSTRATE_LENGTH_X, -TRACE_WIDTH/2, z_sub_top],
             stop=[SUBSTRATE_LENGTH_X, TRACE_WIDTH/2, z_sub_top])

mesh = csx.GetGrid()
mesh.SetDeltaUnit(1e-3)
x_mesh = np.linspace(-SUBSTRATE_LENGTH_X/2, SUBSTRATE_LENGTH_X/2, int(SUBSTRATE_LENGTH_X/0.5)+1)
mesh.AddLine('x', x_mesh)
y_mesh = np.linspace(-SUBSTRATE_WIDTH_Y/2-5, SUBSTRATE_WIDTH_Y/2+5, int((SUBSTRATE_WIDTH_Y+10)/0.5)+1)
mesh.AddLine('y', y_mesh)
z_mesh = np.array([-15, 0, 0.508, 15])
mesh.AddLine('z', z_mesh)

FDTD = openEMS(NrTS=5000, EndCriteria=1e-4) # faster test
FDTD.SetCSX(csx)
FDTD.SetBoundaryCond(['PML_8']*6)
FDTD.SetGaussExcite(6e9, 4e9)

port1 = FDTD.AddLumpedPort(1, 50, [-SUBSTRATE_LENGTH_X/2, -TRACE_WIDTH/2, z_sub_bot], 
                           [-SUBSTRATE_LENGTH_X/2, TRACE_WIDTH/2, z_sub_top], 'z', excite=1)
port2 = FDTD.AddLumpedPort(2, 50, [SUBSTRATE_LENGTH_X/2, -TRACE_WIDTH/2, z_sub_bot], 
                           [SUBSTRATE_LENGTH_X/2, TRACE_WIDTH/2, z_sub_top], 'z', excite=0)

sim_dir = Path("sim_test")
sim_dir.mkdir(exist_ok=True)
orig_cwd = os.getcwd()
FDTD.Write2XML(str(sim_dir / "sim.xml"))
FDTD.Run(str(sim_dir.absolute()), verbose=0)
os.chdir(orig_cwd)

freq = np.linspace(2e9, 10e9, 101)
port1.CalcPort(str(sim_dir.absolute()), freq)
port2.CalcPort(str(sim_dir.absolute()), freq)
print("S21 mean:", np.mean(np.abs(port2.uf_ref / port1.uf_inc)))
