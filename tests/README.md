# Trading Strategy Tests

This directory contains comprehensive unit tests for the `trading_strategy.py` module.

## Test Coverage

The test suite covers:

### Trading Strategies
- **Simple Strategy**: Tests profit/loss based trading decisions
- **Moving Average Strategy**: Tests golden cross, death cross, and trend detection
- **RSI Strategy**: Tests overbought/oversold conditions and neutral signals
- **Bollinger Bands Strategy**: Tests price relative to upper/lower bands
- **MACD Strategy**: Tests bullish/bearish crossovers and trend analysis

### Core Functionality
- **Historical Data Retrieval**: Tests data fetching from yfinance
- **Recommendation Engine**: Tests the main recommendation logic
- **Portfolio Recommendations**: Tests batch portfolio analysis
- **Watchlist Recommendations**: Tests target-based and AI-powered recommendations

### Edge Cases
- **Error Handling**: Tests network failures and data issues
- **Invalid Inputs**: Tests zero shares, negative prices, empty parameters
- **Strategy Fallbacks**: Tests behavior when strategies fail or aren't found

### Integration Tests
- **Full Workflow**: Tests complete recommendation flow with mocked dependencies
- **Database Integration**: Tests interaction with the database module

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with verbose output:
```bash
pytest -v
```

### Run specific test class:
```bash
pytest tests/test_trading_strategy.py::TestSimpleStrategy -v
```

### Run specific test method:
```bash
pytest tests/test_trading_strategy.py::TestSimpleStrategy::test_simple_strategy_profit_target_reached -v
```

### Run with coverage:
```bash
pip install pytest-cov
pytest --cov=trading_strategy --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_trading_strategy.py    # Main test file
└── README.md                   # This file
```

## Mocking

The tests use extensive mocking to avoid external dependencies:
- **yfinance**: Stock data fetching is mocked
- **Database**: Database operations are mocked
- **Historical Data**: Sample data is generated for consistent testing

## Test Data

### Sample Historical Data
- 100 days of realistic price data
- Deterministic random seed for reproducible results
- Includes Open, High, Low, Close, Volume columns

### Sample Portfolio/Watchlist Data
- Multiple stocks with different scenarios
- Various price points and target prices
- Realistic ticker symbols and data

## Test Categories

- **Unit Tests**: Individual method and function testing
- **Integration Tests**: End-to-end workflow testing
- **Edge Case Tests**: Error handling and boundary conditions

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on others
2. **Reproducibility**: Fixed random seeds ensure consistent results
3. **Comprehensive Coverage**: All major code paths are tested
4. **Clear Assertions**: Tests have descriptive failure messages
5. **Mocking**: External dependencies are properly mocked

## Adding New Tests

When adding new functionality:

1. Create test methods following the `test_` naming convention
2. Use descriptive test method names
3. Add appropriate fixtures for shared test data
4. Mock external dependencies
5. Test both success and failure scenarios
6. Update this README if adding new test categories

## Dependencies

Test dependencies are included in `requirements.txt`:
- `pytest`: Test framework
- `pandas`: Data manipulation for test data
- `numpy`: Numerical operations
- Additional test dependencies as needed
