#!/usr/bin/env python3
"""
Python environment verification for OpenEMS and CSXCAD.
Validates critical EM library bindings and supporting packages.
"""

import sys
from pathlib import Path

# Ensure logs directory exists
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

LOG_FILE = log_dir / "python_env_check.log"

# Open log file for writing
log_output = open(LOG_FILE, 'w')

def log_and_print(message):
    """Print to both stdout and log file."""
    print(message)
    log_output.write(message + '\n')
    log_output.flush()

# Status tracking
critical_failed = False

log_and_print("=" * 75)
log_and_print("Python Environment Verification")
log_and_print("=" * 75)
log_and_print(f"Python Version: {sys.version}")
log_and_print(f"Executable: {sys.executable}")
log_and_print("")
log_and_print("Library Status:")
log_and_print("-" * 75)

# Table format: [Status] Library Name                              Version
status_results = []

# Check critical: openEMS
try:
    from openEMS import openEMS
    import openEMS as openems_module
    version = getattr(openems_module, '__version__', 'unknown')
    status_results.append(("[OK]", "openEMS", version))
except ImportError as e:
    status_results.append(("[FAIL]", "openEMS", "IMPORT ERROR"))
    critical_failed = True

# Check critical: CSXCAD
try:
    from CSXCAD import ContinuousStructure
    import CSXCAD as csxcad_module
    version = getattr(csxcad_module, '__version__', 'unknown')
    status_results.append(("[OK]", "CSXCAD", version))
except ImportError as e:
    status_results.append(("[FAIL]", "CSXCAD", "IMPORT ERROR"))
    critical_failed = True

# Check supporting: numpy
try:
    import numpy
    status_results.append(("[OK]", "numpy", numpy.__version__))
except ImportError:
    status_results.append(("[WARN]", "numpy", "NOT INSTALLED"))

# Check supporting: scipy
try:
    import scipy
    status_results.append(("[OK]", "scipy", scipy.__version__))
except ImportError:
    status_results.append(("[WARN]", "scipy", "NOT INSTALLED"))

# Check supporting: matplotlib
try:
    import matplotlib
    status_results.append(("[OK]", "matplotlib", matplotlib.__version__))
except ImportError:
    status_results.append(("[WARN]", "matplotlib", "NOT INSTALLED"))

# Check supporting: pytest
try:
    import pytest
    status_results.append(("[OK]", "pytest", pytest.__version__))
except ImportError:
    status_results.append(("[WARN]", "pytest", "NOT INSTALLED"))

# Print formatted results
for status, library, version in status_results:
    log_and_print(f"{status:<8} {library:<35} {version}")

# Print special warnings for OpenEMS/CSXCAD if they failed
if critical_failed:
    log_and_print("")
    log_and_print("=" * 75)
    log_and_print("⚠️  CRITICAL WARNING: OpenEMS/CSXCAD Import Failed")
    log_and_print("=" * 75)
    log_and_print("")
    log_and_print("OpenEMS and CSXCAD are NOT pip-installable.")
    log_and_print("They require manual compilation from source code.")
    log_and_print("")
    log_and_print("To resolve:")
    log_and_print("  1. Clone OpenEMS: https://github.com/thliebig/openEMS")
    log_and_print("  2. Clone CSXCAD: https://github.com/thliebig/CSXCAD")
    log_and_print("  3. Compile both using their build instructions")
    log_and_print("  4. Python bindings generated via setup.py must be installed")
    log_and_print("  5. Ensure PYTHONPATH includes compiled module paths")
    log_and_print("")

log_and_print("-" * 75)
log_and_print(f"Exit Code: {1 if critical_failed else 0}")
log_and_print("=" * 75)

log_output.close()

sys.exit(1 if critical_failed else 0)
