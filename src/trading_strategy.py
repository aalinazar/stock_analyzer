import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from src.database import db

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
            price=current_price,
            strategy=recommendation['strategy']
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
                recommendation['source'] = 'portfolio'
                recommendations.append(recommendation)
                
            except Exception as e:
                print(f"Error getting recommendation for {stock['ticker']}: {e}")
                continue
        
        return recommendations
    
    def get_watchlist_recommendations(self, watchlist_data: List[Dict], default_day_range: str = 'monthly') -> List[Dict]:
        """
        Get AI-predicted trading recommendations for watchlist stocks.
        
        Args:
            watchlist_data: List of watchlist stock dictionaries
            default_day_range: Default trading horizon for predictions ('weekly', 'monthly', 'quarterly', 'yearly')
        
        Returns:
            List of recommendation dictionaries with predicted target prices
        """
        recommendations = []
        
        for watchlist_stock in watchlist_data:
            try:
                # Use day_range from watchlist data if available, otherwise use default
                day_range = watchlist_stock.get('day_range', default_day_range)
                
                recommendation = self.get_watchlist_recommendation(
                    watchlist_stock['ticker'],
                    day_range
                )
                
                recommendation['watchlist_data'] = watchlist_stock
                recommendation['source'] = 'watchlist'
                recommendations.append(recommendation)
                
            except Exception as e:
                print(f"Error getting watchlist recommendation for {watchlist_stock['ticker']}: {e}")
                continue
        
        return recommendations
    
    def get_watchlist_recommendation(self, ticker: str, day_range: str) -> Dict:
        """
        Get AI-predicted target buy/sell prices for a watchlist stock based on day range.
        
        Args:
            ticker: Stock ticker symbol
            day_range: Trading horizon ('weekly', 'monthly', 'quarterly', 'yearly')
        
        Returns:
            Dict containing target_buy_price, target_sell_price, action, reason, confidence, and strategy
        """
        
        # Map day ranges to analysis periods and data requirements
        range_config = {
            'weekly': {'period': '3mo', 'min_days': 20, 'volatility_factor': 1.2, 'profit_target': 0.03},
            'monthly': {'period': '6mo', 'min_days': 50, 'volatility_factor': 1.5, 'profit_target': 0.08},
            'quarterly': {'period': '1y', 'min_days': 100, 'volatility_factor': 2.0, 'profit_target': 0.15},
            'yearly': {'period': '2y', 'min_days': 200, 'volatility_factor': 2.5, 'profit_target': 0.25}
        }
        
        config = range_config.get(day_range.lower(), range_config['monthly'])
        
        # Store the actual day_range being used (handle invalid inputs)
        actual_day_range = day_range.lower() if day_range.lower() in range_config else 'monthly'
        
        try:
            # Get current price
            stock_ticker = yf.Ticker(ticker)
            info = stock_ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                hist = stock_ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    raise ValueError(f"Unable to fetch current price for {ticker}")
            
            # Get historical data for analysis
            hist_data = self.get_historical_data(ticker, config['period'])
            
            if hist_data.empty or len(hist_data) < config['min_days']:
                # Fallback to simple prediction if insufficient data
                return self._simple_price_prediction(ticker, current_price, day_range)
            
            # AI-based price prediction using multiple algorithms
            target_buy, target_sell, action, reason, confidence = self._ai_price_prediction(
                ticker, current_price, hist_data, config, day_range
            )
            
            return {
                'target_buy_price': target_buy,
                'target_sell_price': target_sell,
                'action': action,
                'reason': reason,
                'confidence': confidence,
                'strategy': f'ai_prediction_{actual_day_range}',
                'current_price': current_price,
                'day_range': actual_day_range,
                'prediction_model': 'ensemble_technical_analysis'
            }
            
        except Exception as e:
            print(f"Error in AI price prediction for {ticker}: {e}")
            # Fallback to simple prediction
            return self._simple_price_prediction(ticker, current_price, day_range)
    
    def _simple_price_prediction(self, ticker: str, current_price: float, day_range: str) -> Dict:
        """Simple fallback price prediction based on day range"""
        
        range_multipliers = {
            'weekly': {'buy': 0.97, 'sell': 1.05},
            'monthly': {'buy': 0.95, 'sell': 1.10},
            'quarterly': {'buy': 0.90, 'sell': 1.20},
            'yearly': {'buy': 0.85, 'sell': 1.30}
        }
        
        multipliers = range_multipliers.get(day_range.lower(), range_multipliers['monthly'])
        
        target_buy = current_price * multipliers['buy']
        target_sell = current_price * multipliers['sell']
        
        return {
            'target_buy_price': target_buy,
            'target_sell_price': target_sell,
            'action': 'BUY',
            'reason': f'Simple {day_range} prediction: Buy at ${target_buy:.2f}, Sell at ${target_sell:.2f} for {((target_sell/current_price - 1) * 100):.1f}% profit',
            'confidence': 0.50,
            'strategy': f'simple_prediction_{day_range}',
            'current_price': current_price,
            'day_range': day_range,
            'prediction_model': 'simple_percentage'
        }
    
    def _ai_price_prediction(self, ticker: str, current_price: float, hist_data: pd.DataFrame, 
                           config: Dict, day_range: str) -> Tuple[float, float, str, str, float]:
        """
        AI-based price prediction using ensemble of technical indicators
        
        Returns: (target_buy_price, target_sell_price, action, reason, confidence)
        """
        
        # Calculate multiple technical indicators
        indicators = self._calculate_technical_indicators(hist_data)
        
        # Calculate volatility and price ranges
        volatility = self._calculate_volatility(hist_data)
        support_resistance = self._find_support_resistance_levels(hist_data)
        trend_analysis = self._analyze_trend_strength(hist_data)
        
        # Get company fundamentals for additional context
        fundamentals = self._get_fundamental_context(ticker)
        
        # Ensemble prediction combining all signals
        prediction = self._ensemble_prediction(
            current_price, indicators, volatility, support_resistance, 
            trend_analysis, fundamentals, config, day_range
        )
        
        return prediction
    
    def _calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        
        indicators = {}
        
        # Moving Averages
        hist_data['MA_20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA_50'] = hist_data['Close'].rolling(window=50).mean()
        hist_data['MA_200'] = hist_data['Close'].rolling(window=200).mean()
        
        # RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_data['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        ma_20 = hist_data['MA_20']
        std_20 = hist_data['Close'].rolling(window=20).std()
        hist_data['BB_Upper'] = ma_20 + (std_20 * 2)
        hist_data['BB_Lower'] = ma_20 - (std_20 * 2)
        
        # MACD
        exp12 = hist_data['Close'].ewm(span=12).mean()
        exp26 = hist_data['Close'].ewm(span=26).mean()
        hist_data['MACD'] = exp12 - exp26
        hist_data['MACD_Signal'] = hist_data['MACD'].ewm(span=9).mean()
        
        # Price momentum
        hist_data['Momentum_5'] = hist_data['Close'].pct_change(5)
        hist_data['Momentum_10'] = hist_data['Close'].pct_change(10)
        hist_data['Momentum_20'] = hist_data['Close'].pct_change(20)
        
        # Store latest values
        if len(hist_data) > 0:
            latest = hist_data.iloc[-1]
            indicators = {
                'price': latest['Close'],
                'ma_20': latest['MA_20'],
                'ma_50': latest['MA_50'],
                'ma_200': latest['MA_200'],
                'rsi': latest['RSI'],
                'bb_upper': latest['BB_Upper'],
                'bb_lower': latest['BB_Lower'],
                'macd': latest['MACD'],
                'macd_signal': latest['MACD_Signal'],
                'momentum_5': latest['Momentum_5'],
                'momentum_10': latest['Momentum_10'],
                'momentum_20': latest['Momentum_20']
            }
        
        return indicators
    
    def _calculate_volatility(self, hist_data: pd.DataFrame) -> Dict:
        """Calculate volatility metrics"""
        
        if len(hist_data) < 20:
            return {'daily_vol': 0.02, 'atr': 0, 'volatility_regime': 'normal'}
        
        # Daily volatility (standard deviation of daily returns)
        daily_returns = hist_data['Close'].pct_change().dropna()
        daily_vol = daily_returns.std()
        
        # Average True Range (ATR)
        high_low = hist_data['High'] - hist_data['Low']
        high_close = abs(hist_data['High'] - hist_data['Close'].shift())
        low_close = abs(hist_data['Low'] - hist_data['Close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        # Volatility regime
        historical_vol = daily_returns.rolling(window=50).std().iloc[-1] if len(daily_returns) >= 50 else daily_vol
        if daily_vol > historical_vol * 1.5:
            volatility_regime = 'high'
        elif daily_vol < historical_vol * 0.7:
            volatility_regime = 'low'
        else:
            volatility_regime = 'normal'
        
        return {
            'daily_vol': daily_vol,
            'atr': atr,
            'volatility_regime': volatility_regime,
            'historical_vol': historical_vol
        }
    
    def _find_support_resistance_levels(self, hist_data: pd.DataFrame) -> Dict:
        """Find key support and resistance levels"""
        
        if len(hist_data) < 50:
            recent_data = hist_data
        else:
            recent_data = hist_data.tail(50)
        
        # Find local maxima and minima for support/resistance
        highs = recent_data['High']
        lows = recent_data['Low']
        
        # Simple support/resistance based on recent price action
        resistance_levels = []
        support_levels = []
        
        # Find resistance levels (local maxima)
        for i in range(2, len(highs) - 2):
            if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                resistance_levels.append(highs.iloc[i])
        
        # Find support levels (local minima)
        for i in range(2, len(lows) - 2):
            if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
                lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
                support_levels.append(lows.iloc[i])
        
        # Get most recent and strongest levels
        current_price = hist_data['Close'].iloc[-1]
        
        # Find nearest resistance above current price
        valid_resistance = [r for r in resistance_levels if r > current_price]
        nearest_resistance = min(valid_resistance) if valid_resistance else current_price * 1.10
        
        # Find nearest support below current price
        valid_support = [s for s in support_levels if s < current_price]
        nearest_support = max(valid_support) if valid_support else current_price * 0.90
        
        return {
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'all_resistance': sorted(resistance_levels),
            'all_support': sorted(support_levels)
        }
    
    def _analyze_trend_strength(self, hist_data: pd.DataFrame) -> Dict:
        """Analyze trend direction and strength"""
        
        if len(hist_data) < 50:
            return {'trend': 'neutral', 'strength': 0.5, 'direction': 'sideways'}
        
        # Calculate trend using linear regression on recent prices
        recent_prices = hist_data['Close'].tail(50)
        x = np.arange(len(recent_prices))
        y = recent_prices.values
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        # Moving average trend analysis
        ma_20 = hist_data['Close'].rolling(window=20).mean().iloc[-1]
        ma_50 = hist_data['Close'].rolling(window=50).mean().iloc[-1]
        current_price = hist_data['Close'].iloc[-1]
        
        # Determine trend direction
        if slope > 0 and current_price > ma_20 > ma_50:
            trend = 'bullish'
            direction = 'up'
        elif slope < 0 and current_price < ma_20 < ma_50:
            trend = 'bearish'
            direction = 'down'
        else:
            trend = 'neutral'
            direction = 'sideways'
        
        # Calculate trend strength (normalized slope)
        price_range = recent_prices.max() - recent_prices.min()
        strength = abs(slope * 50) / price_range if price_range > 0 else 0.5
        strength = min(max(strength, 0), 1)  # Normalize between 0 and 1
        
        return {
            'trend': trend,
            'strength': strength,
            'direction': direction,
            'slope': slope
        }
    
    def _get_fundamental_context(self, ticker: str) -> Dict:
        """Get fundamental data for additional context"""
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'pe_ratio': info.get('forwardPE'),
                'beta': info.get('beta'),
                'market_cap': info.get('marketCap'),
                'dividend_yield': info.get('dividendYield'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth')
            }
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return {}
    
    def _ensemble_prediction(self, current_price: float, indicators: Dict, volatility: Dict,
                           support_resistance: Dict, trend_analysis: Dict, fundamentals: Dict,
                           config: Dict, day_range: str) -> Tuple[float, float, str, str, float]:
        """
        Ensemble prediction combining all technical and fundamental signals
        
        Returns: (target_buy_price, target_sell_price, action, reason, confidence)
        """
        
        # Base predictions from different models
        predictions = []
        
        # 1. Support/Resistance based prediction
        sr_buy = support_resistance['nearest_support'] * 0.98  # 2% below support
        sr_sell = support_resistance['nearest_resistance'] * 0.98  # 2% below resistance
        predictions.append(('support_resistance', sr_buy, sr_sell, 0.7))
        
        # 2. Moving average based prediction
        if indicators.get('ma_20') and indicators.get('ma_50'):
            ma_trend_signal = 1 if indicators['ma_20'] > indicators['ma_50'] else -1
            volatility_adj = volatility['daily_vol'] * config['volatility_factor']
            
            if ma_trend_signal > 0:  # Bullish
                ma_buy = max(indicators['ma_20'] * 0.98, current_price * (1 - volatility_adj))
                ma_sell = current_price * (1 + config['profit_target'])
            else:  # Bearish
                ma_buy = current_price * (1 - volatility_adj * 1.5)
                ma_sell = min(indicators['ma_20'] * 0.98, current_price * (1 + config['profit_target'] * 0.5))
            
            predictions.append(('moving_average', ma_buy, ma_sell, 0.6))
        
        # 3. Volatility-based prediction
        vol_factor = config['volatility_factor'] * (2 if volatility['volatility_regime'] == 'high' else 1)
        vol_buy = current_price * (1 - volatility['daily_vol'] * vol_factor)
        vol_sell = current_price * (1 + volatility['daily_vol'] * vol_factor)
        predictions.append(('volatility', vol_buy, vol_sell, 0.5))
        
        # 4. RSI-based prediction
        if indicators.get('rsi'):
            rsi = indicators['rsi']
            if rsi < 30:  # Oversold
                rsi_buy = current_price * 0.97
                rsi_sell = current_price * 1.15
            elif rsi > 70:  # Overbought
                rsi_buy = current_price * 0.92
                rsi_sell = current_price * 1.05
            else:  # Neutral
                rsi_buy = current_price * 0.95
                rsi_sell = current_price * 1.10
            
            predictions.append(('rsi', rsi_buy, rsi_sell, 0.4))
        
        # 5. Bollinger Bands prediction
        if indicators.get('bb_upper') and indicators.get('bb_lower'):
            bb_buy = indicators['bb_lower'] * 0.98
            bb_sell = indicators['bb_upper'] * 0.95
            predictions.append(('bollinger', bb_buy, bb_sell, 0.5))
        
        # 6. Momentum-based prediction
        momentum_score = 0
        if indicators.get('momentum_5') and indicators.get('momentum_10'):
            if indicators['momentum_5'] > 0.02 and indicators['momentum_10'] > 0:  # Strong momentum
                momentum_score = 1
            elif indicators['momentum_5'] < -0.02 and indicators['momentum_10'] < 0:  # Negative momentum
                momentum_score = -1
        
        # Weighted ensemble prediction
        total_weight = sum(pred[3] for pred in predictions)
        weighted_buy = sum(pred[1] * pred[3] for pred in predictions) / total_weight
        weighted_sell = sum(pred[2] * pred[3] for pred in predictions) / total_weight
        
        # Adjust based on trend strength
        trend_boost = 1 + (trend_analysis['strength'] * 0.2)
        if trend_analysis['trend'] == 'bullish':
            weighted_sell *= trend_boost
        elif trend_analysis['trend'] == 'bearish':
            weighted_buy *= (2 - trend_boost)  # Lower buy price in bearish trend
        
        # Momentum adjustment
        if momentum_score > 0:
            weighted_sell *= 1.1
        elif momentum_score < 0:
            weighted_buy *= 0.95
        
        # Ensure reasonable bounds
        weighted_buy = max(weighted_buy, current_price * 0.7)
        weighted_sell = min(weighted_sell, current_price * 1.5)
        
        # Determine action based on current price relative to targets
        if current_price <= weighted_buy:
            action = 'BUY'
            confidence = 0.8
        elif current_price >= weighted_sell:
            action = 'SELL'
            confidence = 0.8
        else:
            action = 'HOLD'
            confidence = 0.6
        
        # Add momentum consideration for action
        if momentum_score > 0.5 and action == 'HOLD':
            action = 'BUY'
            confidence = 0.7
        elif momentum_score < -0.5 and action == 'HOLD':
            action = 'SELL'
            confidence = 0.7
        
        # Generate reasoning
        reason_parts = [f"AI ensemble prediction for {day_range} horizon:"]
        reason_parts.append(f"Target buy: ${weighted_buy:.2f}, Target sell: ${weighted_sell:.2f}")
        
        if trend_analysis['trend'] == 'bullish':
            reason_parts.append(f"Strong {trend_analysis['trend']} trend detected")
        elif trend_analysis['trend'] == 'bearish':
            reason_parts.append(f"Downtrend with {trend_analysis['strength']*100:.0f}% strength")
        
        if momentum_score > 0:
            reason_parts.append("Positive momentum supports upward movement")
        elif momentum_score < 0:
            reason_parts.append("Negative momentum suggests caution")
        
        if volatility['volatility_regime'] == 'high':
            reason_parts.append("High volatility - wider price targets set")
        elif volatility['volatility_regime'] == 'low':
            reason_parts.append("Low volatility - conservative targets set")
        
        reason = " | ".join(reason_parts)
        
        # Calculate overall confidence based on signal consistency
        signal_strength = abs(momentum_score) + trend_analysis['strength']
        confidence = min(0.5 + (signal_strength * 0.25), 0.9)
        
        return (weighted_buy, weighted_sell, action, reason, confidence)

# Global strategy instance
strategy = TradingStrategy()
