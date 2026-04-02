#!/bin/bash
# Electromagnetic simulation pipeline - system verification
# Validates system-level dependencies critical for EM simulation

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure logs directory exists
mkdir -p data/logs

# Log file
LOG_FILE="data/logs/system_check.log"

# Initialize exit code
EXIT_CODE=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "OK")
            echo -e "${GREEN}[OK]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "FAIL")
            echo -e "${RED}[FAIL]${NC} $message" | tee -a "$LOG_FILE"
            EXIT_CODE=1
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Clear log file
> "$LOG_FILE"
echo "=== System Verification Check ===" >> "$LOG_FILE"
echo "Timestamp: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 1. Check openEMS binary (case-sensitive)
if command -v openEMS &> /dev/null; then
    OPENEMS_PATH=$(command -v openEMS)
    print_status "OK" "openEMS binary found at: $OPENEMS_PATH"
else
    print_status "FAIL" "openEMS binary not found in PATH"
fi

# 2. Check python executable
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    PYTHON_PATH=$(command -v python)
    print_status "OK" "python executable found: $PYTHON_VERSION (at $PYTHON_PATH)"
else
    print_status "FAIL" "python executable not found in PATH"
fi

# 3. Check pip executable
if command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version 2>&1)
    PIP_PATH=$(command -v pip)
    print_status "OK" "pip executable found: $PIP_VERSION (at $PIP_PATH)"
else
    print_status "FAIL" "pip executable not found in PATH"
fi

# 4. Verify python and pip are from same environment
if command -v python &> /dev/null && command -v pip &> /dev/null; then
    PYTHON_PATH=$(command -v python)
    PIP_PATH=$(command -v pip)
    PYTHON_DIR=$(dirname "$PYTHON_PATH")
    PIP_DIR=$(dirname "$PIP_PATH")
    
    if [ "$PYTHON_DIR" = "$PIP_DIR" ]; then
        print_status "OK" "python and pip resolve to same environment"
    else
        print_status "WARN" "python and pip from different locations (may cause issues)"
    fi
fi

# 5. Check LD_LIBRARY_PATH
if [[ "$LD_LIBRARY_PATH" == *"/usr/local/lib"* ]]; then
    print_status "OK" "LD_LIBRARY_PATH includes /usr/local/lib"
else
    if [ -d "/usr/local/lib" ]; then
        print_status "WARN" "LD_LIBRARY_PATH does not include /usr/local/lib (may cause runtime failures)"
    else
        print_status "WARN" "/usr/local/lib does not exist on system"
    fi
fi

echo "" >> "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"

exit $EXIT_CODE
