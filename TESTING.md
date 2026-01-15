# Testing Guide

This document explains how to run and work with the tests for the trading strategy module.

## Prerequisites

Make sure you have the virtual environment activated and dependencies installed:

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

### Method 1: Using the run_tests.py script (Recommended)
```bash
python run_tests.py
```

### Method 2: Using pytest directly (with activated venv)
```bash
python -m pytest tests/ -v
```

### Method 3: Using VS Code
- Open the project in VS Code
- Go to the "Run and Debug" panel (Ctrl+Shift+D)
- Select "Run All Tests" and press F5

### Method 4: Using pytest with virtual environment path
```bash
./venv/bin/pytest tests/ -v
```

## Test Configuration

The test suite is configured with:

- **pytest.ini**: Main pytest configuration
- **.vscode/settings.json**: VS Code Python settings
- **.vscode/launch.json**: VS Code launch configurations

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_trading_strategy.py    # Main test file (41 tests)
└── README.md                   # Test documentation
```

## Test Coverage

The test suite includes:

### Trading Strategies (5 strategies tested)
- Simple Strategy
- Moving Average Strategy
- RSI Strategy
- Bollinger Bands Strategy
- MACD Strategy

### Core Functionality
- Historical data retrieval
- Recommendation engine
- Portfolio recommendations
- Watchlist recommendations

### Edge Cases & Error Handling
- Network failures
- Invalid inputs
- Strategy fallbacks

### Integration Tests
- Full workflow testing
- Database integration

## Running Specific Tests

### Run a specific test class:
```bash
python -m pytest tests/test_trading_strategy.py::TestSimpleStrategy -v
```

### Run a specific test method:
```bash
python -m pytest tests/test_trading_strategy.py::TestSimpleStrategy::test_simple_strategy_profit_target_reached -v
```

### Run with coverage report:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=trading_strategy --cov-report=html
```

## Debugging Tests

### Run with verbose output and short traceback:
```bash
python -m pytest tests/ -v --tb=short
```

### Run a specific test with debugging:
```bash
python -m pytest tests/ -v -s --tb=long -k "test_simple_strategy_profit_target_reached"
```

## VS Code Integration

VS Code is configured to:

1. **Use the correct Python interpreter**: `./venv/bin/python`
2. **Enable pytest testing**: Built-in test discovery
3. **Provide launch configurations**: Easy debugging from VS Code

### Using VS Code Test Explorer:
1. Open VS Code
2. Go to the Testing tab (flask icon in sidebar)
3. Tests should be automatically discovered
4. Click on test names to run individual tests
5. Use the "Run Test" button at the top to run all tests

## Common Issues

### "ModuleNotFoundError: No module named 'yfinance'"
**Solution**: Make sure the virtual environment is activated:
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

### Tests running with wrong Python version
**Solution**: VS Code should automatically use the virtual environment. If not, check:
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose `./venv/bin/python`

### Tests not discovered in VS Code
**Solution**: 
1. Ensure you're in the correct workspace folder
2. Check that `.vscode/settings.json` exists and is properly configured
3. Reload the VS Code window

## Adding New Tests

1. Follow the naming convention: `test_*.py` for files, `test_*` for functions
2. Use the existing fixtures and patterns in `test_trading_strategy.py`
3. Add appropriate assertions with descriptive messages
4. Mock external dependencies
5. Update this documentation if adding new test categories

## Test Data

The tests use:
- **Sample historical data**: 100 days of realistic price data
- **Sample portfolio/watchlist data**: Multiple stocks with different scenarios
- **Deterministic random seeds**: For reproducible test results

## Continuous Integration

All tests pass consistently (41/41) and provide comprehensive coverage of the trading strategy functionality.
