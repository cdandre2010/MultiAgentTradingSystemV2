# TA-Lib Installation Guide

This guide provides instructions for installing TA-Lib, a technical analysis library that is used in the MultiAgentTradingSystemV2 project for indicator calculations.

## Why TA-Lib?

We've chosen TA-Lib for our indicator calculations for several reasons:

1. **Reliability**: TA-Lib is a battle-tested library used extensively in the industry
2. **Performance**: TA-Lib's core is written in C, making calculations significantly faster
3. **Maintenance**: Using an established library reduces our maintenance burden
4. **Coverage**: TA-Lib includes 150+ technical indicators out of the box
5. **Accuracy**: Well-tested implementations ensure calculation correctness

## Installation Instructions

### Ubuntu/Debian Linux

```bash
# Install TA-Lib dependencies
sudo apt-get update
sudo apt-get install -y build-essential python3-dev wget

# Download and install TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# Install Python wrapper
pip install ta-lib
```

### macOS (Homebrew)

```bash
# Install TA-Lib
brew install ta-lib

# Install Python wrapper
pip install ta-lib
```

### Windows

On Windows, installing TA-Lib can be more complex, so we recommend using a pre-built wheel:

1. Download a pre-built wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
   - Select the appropriate version for your Python installation (matching Python version and architecture)
   - For example: `TA_Lib‑0.4.24‑cp312‑cp312‑win_amd64.whl` for Python 3.12 on 64-bit Windows

2. Install the downloaded wheel
   ```bash
   pip install C:/path/to/downloaded/TA_Lib‑0.4.24‑cp312‑cp312‑win_amd64.whl
   ```

### Docker

If you're using Docker, add the following to your Dockerfile:

```dockerfile
# Install TA-Lib
RUN apt-get update && apt-get install -y build-essential wget
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install
    
# Install Python wrapper
RUN pip install ta-lib
```

## Verifying Installation

To verify your TA-Lib installation:

```python
import talib
import numpy as np

# Generate some random data
data = np.random.random(100)

# Calculate a simple moving average
sma = talib.SMA(data, timeperiod=10)

print("Installation successful!")
```

## Troubleshooting

### Common Issues on Linux

If you encounter the error `talib/common.c:242:28: fatal error: ta-lib/ta_defs.h: No such file or directory`:
- Ensure you've properly installed the TA-Lib C library before installing the Python wrapper
- You may need to set the library path: `export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH`

### Common Issues on Windows

If you encounter a "DLL load failed" error:
- Ensure you've installed the correct wheel for your Python version
- Restart your Python environment after installation

## Resources

- [TA-Lib GitHub Repository](https://github.com/mrjbq7/ta-lib)
- [TA-Lib Documentation](https://mrjbq7.github.io/ta-lib/)
- [TA-Lib Function Documentation](https://mrjbq7.github.io/ta-lib/func.html)