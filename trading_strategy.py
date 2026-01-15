import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from database import db

class TradingStrategy:
    def __init__(self):
        self.strategies = {
            'simple': self.simple_strategy,
            'moving_average': self.moving_average_strategy,
            'rsi': self.rsi_strategy,
            'bollinger_bands': self.bollinger_bands_strategy,
            'macd': self.macd_strategy
        }
    
    def get_recommendation(self, ticker: str, shares: float, purchase_price: float, 
                          current_price: float) -> Dict:
        """Get trading recommendation for a stock"""
        
        # Get strategy settings for this ticker
        settings = db.get_strategy_settings(ticker)
        if not settings:
            settings = {
                'strategy_type': 'simple',
                'parameters': {
                    'profit_target': 0.20,  # 20% profit target
                    'stop_loss': 0.10,      # 10% stop loss
                    'hold_threshold': 0.05  # 5% hold threshold
                }
            }
        
        # Get historical data for technical analysis
        hist_data = self.get_historical_data(ticker)
        
        # Apply the selected strategy
        strategy_func = self.strategies.get(settings['strategy_type'], self.simple_strategy)
        recommendation = strategy_func(ticker, shares, purchase_price, current_price, 
                                      settings['parameters'], hist_data)
        
        # Log the recommendation
        db.log_recommendation(
            ticker=ticker,
            action=recommendation['action'],
            reason=recommendation['reason'],
            confidence=recommendation['confidence'],
            price=current_price
        )
        
        return recommendation
    
    def get_historical_data(self, ticker: str, period: str = "6mo") -> pd.DataFrame:
        """Get historical stock data for technical analysis"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def simple_strategy(self, ticker: str, shares: float, purchase_price: float, 
                       current_price: float, parameters: Dict, hist_data: pd.DataFrame) -> Dict:
        """Simple profit/loss based strategy"""
        profit_loss_pct = ((current_price - purchase_price) / purchase_price) * 100
        
        profit_target = parameters.get('profit_target', 0.20) * 100
        stop_loss = parameters.get('stop_loss', 0.10) * 100
        hold_threshold = parameters.get('hold_threshold', 0.05) * 100
        
        if profit_loss_pct >= profit_target:
            return {
                'action': 'SELL',
                'reason': f'Target profit reached: {profit_loss_pct:.2f}% (Target: {profit_target:.1f}%)',
                'confidence': 0.85,
                'strategy': 'simple'
            }
        elif profit_loss_pct <= -stop_loss:
            return {
                'action': 'SELL',
                'reason': f'Stop loss triggered: {profit_loss_pct:.2f}% (Max loss: {-stop_loss:.1f}%)',
                'confidence': 0.90,
                'strategy': 'simple'
            }
        elif abs(profit_loss_pct) <= hold_threshold:
            return {
                'action': 'HOLD',
                'reason': f'Within hold threshold: {profit_loss_pct:.2f}% (Threshold: ±{hold_threshold:.1f}%)',
                'confidence': 0.70,
                'strategy': 'simple'
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'Monitoring position: {profit_loss_pct:.2f}% P/L',
                'confidence': 0.60,
                'strategy': 'simple'
            }
    
    def moving_average_strategy(self, ticker: str, shares: float, purchase_price: float, 
                              current_price: float, parameters: Dict, hist_data: pd.DataFrame) -> Dict:
        """Moving average crossover strategy"""
        if hist_data.empty:
            return self.simple_strategy(ticker, shares, purchase_price, current_price, parameters, hist_data)
        
        short_period = parameters.get('short_ma', 20)
        long_period = parameters.get('long_ma', 50)
        
        hist_data['MA_short'] = hist_data['Close'].rolling(window=short_period).mean()
        hist_data['MA_long'] = hist_data['Close'].rolling(window=long_period).mean()
        
        latest_short = hist_data['MA_short'].iloc[-1]
        latest_long = hist_data['MA_long'].iloc[-1]
        prev_short = hist_data['MA_short'].iloc[-2] if len(hist_data) > 1 else latest_short
        prev_long = hist_data['MA_long'].iloc[-2] if len(hist_data) > 1 else latest_long
        
        # Golden cross (short MA crosses above long MA) - Buy signal
        if prev_short <= prev_long and latest_short > latest_long:
            return {
                'action': 'BUY',
                'reason': f'Golden cross detected: {short_period}-day MA ({latest_short:.2f}) crossed above {long_period}-day MA ({latest_long:.2f})',
                'confidence': 0.75,
                'strategy': 'moving_average'
            }
        
        # Death cross (short MA crosses below long MA) - Sell signal
        elif prev_short >= prev_long and latest_short < latest_long:
            return {
                'action': 'SELL',
                'reason': f'Death cross detected: {short_period}-day MA ({latest_short:.2f}) crossed below {long_period}-day MA ({latest_long:.2f})',
                'confidence': 0.80,
                'strategy': 'moving_average'
            }
        
        # Current position relative to MAs
        elif current_price > latest_short > latest_long:
            return {
                'action': 'HOLD',
                'reason': f'Bullish trend: Price (${current_price:.2f}) > Short MA ({latest_short:.2f}) > Long MA ({latest_long:.2f})',
                'confidence': 0.65,
                'strategy': 'moving_average'
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'Neutral/Bearish: Price (${current_price:.2f}) below moving averages',
                'confidence': 0.60,
                'strategy': 'moving_average'
            }
    
    def rsi_strategy(self, ticker: str, shares: float, purchase_price: float, 
                    current_price: float, parameters: Dict, hist_data: pd.DataFrame) -> Dict:
        """RSI (Relative Strength Index) strategy"""
        if hist_data.empty or len(hist_data) < 14:
            return self.simple_strategy(ticker, shares, purchase_price, current_price, parameters, hist_data)
        
        period = parameters.get('rsi_period', 14)
        oversold = parameters.get('oversold_level', 30)
        overbought = parameters.get('overbought_level', 70)
        
        # Calculate RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi <= oversold:
            return {
                'action': 'BUY',
                'reason': f'RSI oversold: {current_rsi:.1f} (Buy signal below {oversold})',
                'confidence': 0.70,
                'strategy': 'rsi'
            }
        elif current_rsi >= overbought:
            return {
                'action': 'SELL',
                'reason': f'RSI overbought: {current_rsi:.1f} (Sell signal above {overbought})',
                'confidence': 0.70,
                'strategy': 'rsi'
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'RSI neutral: {current_rsi:.1f} (Between {oversold} and {overbought})',
                'confidence': 0.50,
                'strategy': 'rsi'
            }
    
    def bollinger_bands_strategy(self, ticker: str, shares: float, purchase_price: float, 
                                current_price: float, parameters: Dict, hist_data: pd.DataFrame) -> Dict:
        """Bollinger Bands strategy"""
        if hist_data.empty or len(hist_data) < 20:
            return self.simple_strategy(ticker, shares, purchase_price, current_price, parameters, hist_data)
        
        period = parameters.get('bb_period', 20)
        std_dev = parameters.get('bb_std', 2)
        
        # Calculate Bollinger Bands
        ma = hist_data['Close'].rolling(window=period).mean()
        std = hist_data['Close'].rolling(window=period).std()
        upper_band = ma + (std * std_dev)
        lower_band = ma - (std * std_dev)
        
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_ma = ma.iloc[-1]
        
        # Price above upper band = overbought (sell signal)
        if current_price > current_upper:
            return {
                'action': 'SELL',
                'reason': f'Price above Bollinger Band: ${current_price:.2f} > Upper band ${current_upper:.2f}',
                'confidence': 0.65,
                'strategy': 'bollinger_bands'
            }
        
        # Price below lower band = oversold (buy signal)
        elif current_price < current_lower:
            return {
                'action': 'BUY',
                'reason': f'Price below Bollinger Band: ${current_price:.2f} < Lower band ${current_lower:.2f}',
                'confidence': 0.65,
                'strategy': 'bollinger_bands'
            }
        
        else:
            return {
                'action': 'HOLD',
                'reason': f'Price within Bollinger Bands: ${current_lower:.2f} < ${current_price:.2f} < ${current_upper:.2f}',
                'confidence': 0.50,
                'strategy': 'bollinger_bands'
            }
    
    def macd_strategy(self, ticker: str, shares: float, purchase_price: float, 
                     current_price: float, parameters: Dict, hist_data: pd.DataFrame) -> Dict:
        """MACD (Moving Average Convergence Divergence) strategy"""
        if hist_data.empty or len(hist_data) < 26:
            return self.simple_strategy(ticker, shares, purchase_price, current_price, parameters, hist_data)
        
        fast_period = parameters.get('macd_fast', 12)
        slow_period = parameters.get('macd_slow', 26)
        signal_period = parameters.get('macd_signal', 9)
        
        # Calculate MACD
        exp1 = hist_data['Close'].ewm(span=fast_period).mean()
        exp2 = hist_data['Close'].ewm(span=slow_period).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period).mean()
        histogram = macd - signal
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2] if len(histogram) > 1 else current_hist
        
        # MACD crossover above signal line = buy signal
        if prev_hist <= 0 and current_hist > 0:
            return {
                'action': 'BUY',
                'reason': f'MACD bullish crossover: MACD ({current_macd:.4f}) crossed above Signal ({current_signal:.4f})',
                'confidence': 0.70,
                'strategy': 'macd'
            }
        
        # MACD crossover below signal line = sell signal
        elif prev_hist >= 0 and current_hist < 0:
            return {
                'action': 'SELL',
                'reason': f'MACD bearish crossover: MACD ({current_macd:.4f}) crossed below Signal ({current_signal:.4f})',
                'confidence': 0.70,
                'strategy': 'macd'
            }
        
        # Current MACD position
        elif current_macd > current_signal:
            return {
                'action': 'HOLD',
                'reason': f'MACD bullish: MACD ({current_macd:.4f}) above Signal ({current_signal:.4f})',
                'confidence': 0.60,
                'strategy': 'macd'
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'MACD bearish: MACD ({current_macd:.4f}) below Signal ({current_signal:.4f})',
                'confidence': 0.60,
                'strategy': 'macd'
            }
    
    def get_all_portfolio_recommendations(self, portfolio_data: List[Dict]) -> List[Dict]:
        """Get trading recommendations for all stocks in portfolio"""
        recommendations = []
        
        for stock in portfolio_data:
            try:
                # Get current price
                stock_ticker = yf.Ticker(stock['ticker'])
                info = stock_ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if current_price is None:
                    hist = stock_ticker.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        continue
                
                recommendation = self.get_recommendation(
                    stock['ticker'], 
                    stock['shares'], 
                    stock['purchase_price'],
                    current_price
                )
                
                recommendation['stock_data'] = stock
                recommendation['current_price'] = current_price
                recommendations.append(recommendation)
                
            except Exception as e:
                print(f"Error getting recommendation for {stock['ticker']}: {e}")
                continue
        
        return recommendations

# Global strategy instance
strategy = TradingStrategy()
