import pytest
from stock import Stock

def test_invalid_ticker():
    """Ensure fake tickers raise a ConnectionError or ValueError."""
    with pytest.raises((ValueError, ConnectionError)):
        Stock("FAKE_TICKER_123")

def test_quantity_integrity():
    """Ensure quantity cannot be negative or manipulated illegally."""
    s = Stock("AAPL", 10)
    with pytest.raises(ValueError):
        s.decrease_quantity(20)  # Selling more than owned
    with pytest.raises(ValueError):
        s.increase_quantity(-5)  # Adding negative amount

def test_missing_data_fallbacks():
    """Ensure metrics default to N/A or 0 rather than crashing if API is patchy."""
    s = Stock("AAPL")
    # Even if data is missing, these attributes should exist
    assert hasattr(s.valuation, 'pe')
    assert hasattr(s.risk_metrics, 'get_sharpe_ratio')

def test_zero_beta_handling():
    """Test the Treynor ratio doesn't crash with zero beta (division by zero)."""
    s = Stock("AAPL")
    s.valuation.beta = 0
    # This should return 0.0 because of our error handling, not crash
    assert s.risk_metrics.get_treynor_ratio() == 0.0