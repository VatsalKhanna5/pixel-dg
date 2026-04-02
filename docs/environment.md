# Environment Setup (openEMS + CSXCAD)

## Purpose
This project depends on openEMS and CSXCAD for electromagnetic simulation.

---

## Installation Summary

Both libraries are built from source and installed system-wide:

- openEMS → /usr/local
- CSXCAD → /usr/local

Python bindings are installed inside the project virtual environment using:

- openEMS/python/setup.py
- CSXCAD/python/setup.py

---

## Verification Command

Run the following:

```bash
python -c "from openEMS import openEMS; from CSXCAD import ContinuousStructure; print('openEMS + CSXCAD OK')"