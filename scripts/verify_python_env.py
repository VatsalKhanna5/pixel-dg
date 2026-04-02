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

log_and_print("=" * 70)
log_and_print("Python Environment Verification")
log_and_print("=" * 70)
log_and_print(f"Python Version: {sys.version}")
log_and_print(f"Executable: {sys.executable}")
log_and_print("")
log_and_print("Library Status:")
log_and_print("-" * 70)

# Check critical: openEMS
try:
    from openEMS import openEMS
    import openEMS as openems_module
    version = getattr(openems_module, '__version__', 'unknown')
    log_and_print(f"[OK]   {'openEMS':<40} v{version}")
except ImportError as e:
    log_and_print(f"[FAIL] {'openEMS':<40} IMPORT ERROR")
    critical_failed = True

# Check critical: CSXCAD
try:
    from CSXCAD import ContinuousStructure
    import CSXCAD as csxcad_module
    version = getattr(csxcad_module, '__version__', 'unknown')
    log_and_print(f"[OK]   {'CSXCAD':<40} v{version}")
except ImportError as e:
    log_and_print(f"[FAIL] {'CSXCAD':<40} IMPORT ERROR")
    critical_failed = True

# Check supporting: numpy
try:
    import numpy
    log_and_print(f"[OK]   {'numpy':<40} v{numpy.__version__}")
except ImportError:
    log_and_print(f"[WARN] {'numpy':<40} NOT INSTALLED")

# Check supporting: scipy
try:
    import scipy
    log_and_print(f"[OK]   {'scipy':<40} v{scipy.__version__}")
except ImportError:
    log_and_print(f"[WARN] {'scipy':<40} NOT INSTALLED")

# Check supporting: matplotlib
try:
    import matplotlib
    log_and_print(f"[OK]   {'matplotlib':<40} v{matplotlib.__version__}")
except ImportError:
    log_and_print(f"[WARN] {'matplotlib':<40} NOT INSTALLED")

# Check supporting: pytest
try:
    import pytest
    log_and_print(f"[OK]   {'pytest':<40} v{pytest.__version__}")
except ImportError:
    log_and_print(f"[WARN] {'pytest':<40} NOT INSTALLED")

# Print special warnings for OpenEMS/CSXCAD if they failed
if critical_failed:
    log_and_print("")
    log_and_print("=" * 70)
    log_and_print("⚠️  CRITICAL WARNING: OpenEMS/CSXCAD Import Failed")
    log_and_print("=" * 70)
    log_and_print("")
    log_and_print("OpenEMS and CSXCAD are NOT pip-installable.")
    log_and_print("They require manual compilation from source.")
    log_and_print("")
    log_and_print("To fix this:")
    log_and_print("1. Clone and compile OpenEMS: https://github.com/thliebig/openEMS")
    log_and_print("2. Clone and compile CSXCAD: https://github.com/thliebig/CSXCAD")
    log_and_print("3. Ensure PYTHONPATH includes: /usr/local/lib/python3/dist-packages")
    log_and_print("")

log_and_print("-" * 70)
log_and_print(f"Exit Code: {1 if critical_failed else 0}")
log_and_print("=" * 70)

log_output.close()

sys.exit(1 if critical_failed else 0)
