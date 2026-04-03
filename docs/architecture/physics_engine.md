# Physics Engine

## Overview

The simulation core is implemented in [`src/simulators/openems_simulator.py`](/home/dr-robin-kalyan/Desktop/pixel/src/simulators/openems_simulator.py) and uses openEMS together with CSXCAD to build and solve a three-dimensional FDTD problem for each accepted layout.

## Material And Geometry Parameters

From [`configs/config.yaml`](/home/dr-robin-kalyan/Desktop/pixel/configs/config.yaml):

- substrate material: `Rogers 4350B`
- substrate thickness: `0.508 mm`
- relative permittivity: `3.66`
- loss tangent: `0.004`
- substrate size: `40.0 mm`

## Conductive Pixel Construction

Each active pixel is created as a top-metal box. The implementation intentionally extends pixel boundaries beyond the nominal `1.2 mm` width to prevent artificial discontinuities between neighboring cells.

- nominal pixel width: `1.2 mm`
- overlap extension per side: `0.12 mm`
- effective box width: `1.44 mm`

This overlap is a practical meshing decision that helps logical adjacency behave like physical continuity.

## Mesh Strategy

The simulator uses a mixed-resolution grid:

- fine region near the active geometry: `0.3 mm`
- coarse region in extended padding zones: `2.0 mm`
- air padding above and below the board: `15.0 mm`

This is a compromise between simulation cost and fidelity. Fine spacing is concentrated where fields and geometry change rapidly, while coarser cells are used in less critical regions.

## Boundary Conditions

The solver applies `PML_8` on all six sides of the simulation domain. The purpose is to absorb outgoing waves and reduce artificial reflections from the finite simulation box.

## Excitation And Frequency Plan

The simulator constructs frequency points from the configured bands:

- `2.4 to 3.0 GHz`
- `4.8 to 6.0 GHz`
- `7.2 to 9.0 GHz`

with `7` points per band, for `21` retained analysis frequencies.

The solver is driven with a Gaussian excitation spanning the configured `2.0 to 10.0 GHz` envelope while post-processing retains the discrete points above.

## Port Arrangement

The model uses four lumped ports located at the midpoints of each side of the active layout region:

- left
- right
- bottom
- top

This makes it possible to interpret the structure as a multi-port network and later reduce it to the two-port views used in the dataset.

## Operational Implication

The simulation setup is deliberately more conservative than a toy example. Substrate padding, air volume, and explicit boundary conditions all exist to avoid pathological solver behavior that would contaminate the dataset with non-physical artifacts.
