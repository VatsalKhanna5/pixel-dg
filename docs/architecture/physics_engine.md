# Physics Engine Limits & Meshing Constraints

The physics system heavily leverages **openEMS**, a flexible open-source FDTD solver. To guarantee correct un-guided electromagnetic propagation without artificial mesh resonance, several hard geometric physics rules have been implemented inside `PixelEMSimulator`.

## 1. Pixel Overlap Mechanics

Standard theoretical mathematical blocks map perfectly edge-to-edge. However, in discretized 3D physics solvers, finite floating-point gaps and non-aligned FDTD meshing elements act as high-frequency capacitors, causing adjacent mathematical pixels to reflect signals as if they were disconnected.

**Solution:** Every $1.2\text{mm} \times 1.2\text{mm}$ trace element undergoes a spatial overlap augmentation.
* $10\%$ spatial bleed is added to every boundary.
* Each pixel physically expands by $+0.12\text{mm}$ radially. 
* The ultimate physical bounding box of a logical $1.2\text{mm}$ pixel becomes $1.44 \times 1.44\text{mm}$, ensuring contiguous metal overlaps perfectly merge into unified macro-polygons when processed by the `CSXCAD` engine.

## 2. Substrate Domain Padding & PML Constraints

Electromagnetic fields propagate infinitely outwards through space. openEMS requires numerical boundaries—specifically Perfectly Matched Layers (`PML_8`)—to consume outbound waves and prevent them from reflecting back into the circuit.

**The PML Collapse Factor:** `PML` boundaries *must* be kept physically distant from active electromagnetic components and specifically from lumped excitation ports. If a lumped port intersects a PML, the injected wave immediately dissipates into the matched absorber, simulating a total functional blackout ($S_{21} = -\infty$).

**Padding Deployments:**
1. **X-Y Plane (Substrate Padding):** Although the 15x15 core layout occupies exactly a $18\text{mm} \times 18\text{mm}$ geometric area, the bounding `Rogers` substrate block natively spans **$40\text{mm} \times 40\text{mm}$**. This leaves an active empty runway on both lengths. The $50\Omega$ internal routing ports occupy the edges of the 18mm bounds, allowing waves sufficient unhindered clearance before boundary intersection.
2. **Z-Axis (Air Bounding):** Natively, FDTD grids resting flush to the Substrate ($+Z$) and Ground Plane ($-Z$) collapse the PML parameters and trigger openEMS to default to Perfect Electrical Conductor (`PEC`) bounds—essentially encasing the simulation inside a solid metal cavity. A parameter `Z_AIR_PADDING = 15.0 mm` explicitly models a robust free-space gradient above and below the board geometry mapped to a coarse gradient mesh, ensuring standard radiation patterns hold true limits.

## 3. Discretization Grid

The solver allocates two FDTD meshing constants to preserve CPU efficiency without sacrificing microwave fidelity:
* `FINE_RES = 0.3mm`: Exclusively deployed tightly encapsulating the specific structural geometry bounds covering the microstrip traces and substrate volume.
* `COARSE_RES = 2.0mm`: Mapped across the extended padding thresholds and upper air constraints.
