# Environment Setup

## Solver Dependencies

Pixel depends on the following non-Python components for electromagnetic simulation:

- `openEMS`
- `CSXCAD`

These must be installed and available to the Python environment used for the project.

## Expected Installation Pattern

The repository context indicates a source-based installation pattern in which:

- `openEMS` is installed system-wide
- `CSXCAD` is installed system-wide
- Python bindings are installed into the active project environment

## Python Dependencies

Install the Python requirements with:

```bash
pip install -r requirements.txt
```

## Minimal Verification

Run:

```bash
python -c "from openEMS import openEMS; from CSXCAD import ContinuousStructure; print('openEMS + CSXCAD OK')"
```

If the command succeeds, the core solver bindings are visible to Python.

## Practical Validation Sequence

After import verification:

1. run [`tests/verify_baseline.py`](/home/dr-robin-kalyan/Desktop/pixel/tests/verify_baseline.py)
2. run a small dataset job with [`scripts/generate_dataset_orchestrator.py`](/home/dr-robin-kalyan/Desktop/pixel/scripts/generate_dataset_orchestrator.py)
3. review the generated outputs before scaling further

## Environment Risks To Watch

- mismatched Python environments for solver bindings and project packages
- missing shared libraries for source-built openEMS or CSXCAD installs
- local path assumptions when running scripts from unexpected working directories
