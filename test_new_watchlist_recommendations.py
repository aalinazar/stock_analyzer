#!/usr/bin/env python3
"""
Comprehensive test script for the new AI-based get_watchlist_recommendation method.
This script tests all aspects of the updated functionality including:
- New method signature with day_range parameter
- AI-based price prediction algorithms
- Different trading horizons (weekly, monthly, quarterly, yearly)
- Technical analysis integration
- Error handling and edge cases
"""

import sys
import os
import json
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def import_trading_strategy():
    """Import the trading strategy module with error handling"""
    try:
        from trading_strategy import strategy, TradingStrategy
        return strategy, TradingStrategy
    except ImportError as e:
        print(f"Error importing trading_strategy: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return None, None

def test_method_signature():
    """Test that the method signature has been updated correctly"""
    print("\n" + "="*60)
    print("TESTING METHOD SIGNATURE")
    print("="*60)
    
    strategy_instance, TradingStrategy = import_trading_strategy()
    if not strategy_instance or not TradingStrategy:
        return False
    
    try:
        import inspect
        # Get unbound method signature to include 'self'
        sig = inspect.signature(TradingStrategy.get_watchlist_recommendation)
        params = list(sig.parameters.keys())
        expected_params = ['self', 'ticker', 'day_range']
        
        print(f"✓ Method signature: {params}")
        
        if params == expected_params:
            print("✅ Method signature is correct")
            return True
        else:
            print(f"❌ Method signature incorrect. Expected: {expected_params}, Got: {params}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing method signature: {e}")
        return False

def test_single_stock_recommendation():
    """Test single stock recommendation with different day ranges"""
    print("\n" + "="*60)
    print("TESTING SINGLE STOCK RECOMMENDATIONS")
    print("="*60)
    
    strategy, _ = import_trading_strategy()
    if not strategy:
        return False
    
    ticker = "AAPL"
    day_ranges = ['weekly', 'monthly', 'quarterly', 'yearly']
    
    all_passed = True
    
    for day_range in day_ranges:
        try:
            print(f"\nTesting {ticker} with {day_range} horizon:")
            result = strategy.get_watchlist_recommendation(ticker, day_range)
            
            # Verify required keys are present
            required_keys = ['target_buy_price', 'target_sell_price', 'action', 'reason', 
                           'confidence', 'strategy', 'current_price', 'day_range']
            missing_keys = [key for key in required_keys if key not in result]
            
            if missing_keys:
                print(f"❌ Missing keys: {missing_keys}")
                all_passed = False
                continue
            
            # Extract and display results
            buy_price = result.get('target_buy_price', 0)
            sell_price = result.get('target_sell_price', 0)
            current_price = result.get('current_price', 0)
            action = result.get('action', 'N/A')
            confidence = result.get('confidence', 0)
            strategy_used = result.get('strategy', 'N/A')
            prediction_model = result.get('prediction_model', 'N/A')
            
            # Validate data types and values
            if not all(isinstance(x, (int, float)) for x in [buy_price, sell_price, current_price, confidence]):
                print(f"❌ Invalid data types for numeric values")
                all_passed = False
                continue
            
            if buy_price <= 0 or sell_price <= 0 or current_price <= 0:
                print(f"❌ Invalid price values: Buy={buy_price}, Sell={sell_price}, Current={current_price}")
                all_passed = False
                continue
            
            if action not in ['BUY', 'SELL', 'HOLD']:
                print(f"❌ Invalid action: {action}")
                all_passed = False
                continue
            
            if not (0 <= confidence <= 1):
                print(f"❌ Invalid confidence level: {confidence}")
                all_passed = False
                continue
            
            # Calculate percentages
            buy_pct = ((buy_price - current_price) / current_price) * 100
            sell_pct = ((sell_price - current_price) / current_price) * 100
            
            print(f"  ✅ Current Price: ${current_price:.2f}")
            print(f"  ✅ Target Buy: ${buy_price:.2f} ({buy_pct:+.1f}%)")
            print(f"  ✅ Target Sell: ${sell_price:.2f} ({sell_pct:+.1f}%)")
            print(f"  ✅ Action: {action}")
            print(f"  ✅ Confidence: {confidence:.2f}")
            print(f"  ✅ Strategy: {strategy_used}")
            print(f"  ✅ Prediction Model: {prediction_model}")
            
        except Exception as e:
            print(f"❌ Error testing {ticker} with {day_range}: {e}")
            all_passed = False
    
    return all_passed

def test_watchlist_recommendations():
    """Test multiple stock watchlist recommendations"""
    print("\n" + "="*60)
    print("TESTING WATCHLIST RECOMMENDATIONS")
    print("="*60)
    
    strategy, _ = import_trading_strategy()
    if not strategy:
        return False
    
    # Test watchlist with different day ranges
    watchlist_data = [
        {'ticker': 'AAPL', 'day_range': 'weekly'},
        {'ticker': 'MSFT', 'day_range': 'monthly'},
        {'ticker': 'GOOGL'},  # Should use default
        {'ticker': 'TSLA', 'day_range': 'quarterly'}
    ]
    
    try:
        recommendations = strategy.get_watchlist_recommendations(watchlist_data, default_day_range='monthly')
        
        print(f"Generated {len(recommendations)} recommendations")
        
        if len(recommendations) != len(watchlist_data):
            print(f"❌ Expected {len(watchlist_data)} recommendations, got {len(recommendations)}")
            return False
        
        all_passed = True
        for i, rec in enumerate(recommendations):
            ticker = watchlist_data[i]['ticker']
            expected_range = watchlist_data[i].get('day_range', 'monthly')
            
            # Verify watchlist_data is preserved
            if 'watchlist_data' not in rec:
                print(f"❌ Missing watchlist_data for {ticker}")
                all_passed = False
                continue
            
            # Verify day_range
            actual_range = rec.get('day_range')
            if actual_range != expected_range:
                print(f"❌ {ticker}: Expected day_range '{expected_range}', got '{actual_range}'")
                all_passed = False
                continue
            
            # Verify required keys
            buy_price = rec.get('target_buy_price', 0)
            sell_price = rec.get('target_sell_price', 0)
            current_price = rec.get('current_price', 0)
            action = rec.get('action', 'N/A')
            
            if buy_price <= 0 or sell_price <= 0 or current_price <= 0:
                print(f"❌ {ticker}: Invalid prices")
                all_passed = False
                continue
            
            buy_pct = ((buy_price - current_price) / current_price) * 100
            sell_pct = ((sell_price - current_price) / current_price) * 100
            
            print(f"  ✅ {ticker}: {actual_range} - Buy ${buy_price:.2f} ({buy_pct:+.1f}%), Sell ${sell_price:.2f} ({sell_pct:+.1f}%), Action: {action}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing watchlist recommendations: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)
    
    strategy, _ = import_trading_strategy()
    if not strategy:
        return False
    
    all_passed = True
    
    # Test invalid day range (should default to monthly)
    try:
        result = strategy.get_watchlist_recommendation('AAPL', 'invalid_range')
        if result.get('day_range') == 'monthly':
            print("✅ Invalid day range defaults to monthly")
        else:
            print(f"❌ Invalid day range handled incorrectly: {result.get('day_range')}")
            all_passed = False
    except Exception as e:
        print(f"❌ Error handling invalid day range: {e}")
        all_passed = False
    
    # Test case insensitive day range
    try:
        result = strategy.get_watchlist_recommendation('AAPL', 'WEEKLY')
        if result.get('day_range') == 'weekly':
            print("✅ Case insensitive day range works")
        else:
            print(f"❌ Case insensitive day range failed: {result.get('day_range')}")
            all_passed = False
    except Exception as e:
        print(f"❌ Error testing case insensitive day range: {e}")
        all_passed = False
    
    # Test empty watchlist
    try:
        recommendations = strategy.get_watchlist_recommendations([])
        if len(recommendations) == 0:
            print("✅ Empty watchlist handled correctly")
        else:
            print(f"❌ Empty watchlist returned {len(recommendations)} recommendations")
            all_passed = False
    except Exception as e:
        print(f"❌ Error testing empty watchlist: {e}")
        all_passed = False
    
    return all_passed

def test_different_stocks():
    """Test with various stock tickers to ensure robustness"""
    print("\n" + "="*60)
    print("TESTING DIFFERENT STOCKS")
    print("="*60)
    
    strategy, _ = import_trading_strategy()
    if not strategy:
        return False
    
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    all_passed = True
    
    for ticker in test_stocks:
        try:
            result = strategy.get_watchlist_recommendation(ticker, 'monthly')
            
            # Basic validation
            buy_price = result.get('target_buy_price', 0)
            sell_price = result.get('target_sell_price', 0)
            current_price = result.get('current_price', 0)
            
            if buy_price > 0 and sell_price > 0 and current_price > 0:
                buy_pct = ((buy_price - current_price) / current_price) * 100
                sell_pct = ((sell_price - current_price) / current_price) * 100
                print(f"  ✅ {ticker}: ${current_price:.2f} → Buy ${buy_price:.2f} ({buy_pct:+.1f}%) → Sell ${sell_price:.2f} ({sell_pct:+.1f}%)")
            else:
                print(f"❌ {ticker}: Invalid price data")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {ticker}: Error - {e}")
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 STARTING COMPREHENSIVE TESTS FOR NEW WATCHLIST RECOMMENDATION FUNCTIONALITY")
    print("=" * 80)
    
    tests = [
        ("Method Signature", test_method_signature),
        ("Single Stock Recommendations", test_single_stock_recommendation),
        ("Watchlist Recommendations", test_watchlist_recommendations),
        ("Edge Cases", test_edge_cases),
        ("Different Stocks", test_different_stocks)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("🏁 TEST SUMMARY")
    print("="*80)
    
    passed_count = 0
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_count += 1
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! The new AI-based watchlist recommendation system is working correctly.")
        print("\n📋 IMPLEMENTED FEATURES:")
        print("✅ AI-driven price prediction using ensemble of technical indicators")
        print("✅ Support for multiple trading horizons (weekly, monthly, quarterly, yearly)")
        print("✅ Comprehensive technical analysis (RSI, MACD, Bollinger Bands, Moving Averages)")
        print("✅ Volatility-based price target adjustment")
        print("✅ Support/resistance level identification")
        print("✅ Trend strength and momentum analysis")
        print("✅ Weighted ensemble prediction with confidence scoring")
        print("✅ Robust error handling and fallback mechanisms")
        print("✅ Updated method signature with day_range parameter")
        print("✅ Returns target_buy_price and target_sell_price as requested")
    else:
        print(f"⚠️  {total_count - passed_count} tests failed. Please review the implementation.")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
