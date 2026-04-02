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

# 1. Check openEMS binary
if command -v openEMS &> /dev/null; then
    OPENEMS_PATH=$(command -v openEMS)
    print_status "OK" "openEMS found at: $OPENEMS_PATH"
else
    print_status "FAIL" "openEMS binary not found in PATH"
fi

# 2. Check Python 3
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_status "OK" "Python 3 installed: $PYTHON_VERSION"
else
    print_status "FAIL" "python3 not found in PATH"
fi

# 3. Check pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1)
    print_status "OK" "pip available: $PIP_VERSION"
elif command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version 2>&1)
    print_status "OK" "pip available: $PIP_VERSION"
else
    print_status "FAIL" "pip not found in PATH"
fi

# 4. Check LD_LIBRARY_PATH
if [[ "$LD_LIBRARY_PATH" == *"/usr/local/lib"* ]]; then
    print_status "OK" "LD_LIBRARY_PATH includes /usr/local/lib"
else
    print_status "WARN" "LD_LIBRARY_PATH does not include /usr/local/lib (may cause runtime failures)"
fi

echo "" >> "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"

exit $EXIT_CODE
