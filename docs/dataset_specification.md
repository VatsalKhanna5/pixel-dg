# Dataset Specification

## Overview

Pixel writes simulation products to HDF5 so that generated layouts, reduced-port responses, and connectivity labels can be consumed efficiently from Python-based analysis and machine-learning workflows.

## Primary Sequential Output

Default path:

`data/processed/class_f_dataset.h5`

Datasets created by [`scripts/generate_dataset_orchestrator.py`](/home/dr-robin-kalyan/Desktop/pixel/scripts/generate_dataset_orchestrator.py):

| Dataset | Shape | Type | Description |
| --- | --- | --- | --- |
| `matrices` | `(N, 15, 15)` | `int8` | Binary conductive layout. `1` indicates metal and `0` indicates absence of conductor. |
| `s_parameters` | `(N, 8, F, 2, 2)` | `complex64` | Eight augmented two-port variants for each accepted layout. |
| `dfs_status` | `(N,)` | `bool` | Connectivity label produced by DFS screening. |

Where:

- `N` is the number of accepted layouts stored
- `F` is the number of retained frequency points, currently 21 from the configured three-band plan

## Bulk Output

Default path:

`data/processed/final_dataset.h5`

Datasets created by [`scripts/generate_bulk_dataset.py`](/home/dr-robin-kalyan/Desktop/pixel/scripts/generate_bulk_dataset.py):

| Dataset | Shape | Type | Description |
| --- | --- | --- | --- |
| `matrices` | `(N, 15, 15)` | `int8` | Binary conductive layout |
| `s_parameters` | `(N, 8, F, 2, 2)` | `complex64` | Augmented two-port variants |
| `s_parameters_raw_4x4` | `(N, F, 4, 4)` | `complex64` | Raw solver-shaped response tensor prior to augmentation |
| `dfs_status` | `(N,)` | `bool` | DFS connectivity status |

## Frequency Definition

The current configuration file [`configs/config.yaml`](/home/dr-robin-kalyan/Desktop/pixel/configs/config.yaml) defines:

- `freq_start_ghz: 2.0`
- `freq_stop_ghz: 10.0`
- `freq_bands_ghz: [[2.4, 3.0], [4.8, 6.0], [7.2, 9.0]]`
- `points_per_band: 7`

This produces 21 analysis points across the three target bands.

## Semantic Notes

- Layout tensors encode geometry in matrix form, not mesh form.
- `dfs_status` is a graph-theoretic label, not a direct EM metric.
- `s_parameters` represent reduced-port variants derived from the solver output through the augmentation logic in [`src/utils/data_augmenter.py`](/home/dr-robin-kalyan/Desktop/pixel/src/utils/data_augmenter.py).
- Bulk generation preserves a raw `4 x 4`-shaped tensor for future analysis or alternative reduction methods.

## Provenance Recommendations

For publication-grade datasets, the following metadata would be valuable to persist alongside each run:

- exact configuration snapshot
- code commit identifier
- solver version
- random seed strategy
- baseline verification status
- timestamped generation manifest

These recommendations are not fully materialized in the current HDF5 schema, but they are useful next steps for stronger reproducibility.
