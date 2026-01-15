import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class PortfolioDatabase:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Portfolio stocks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    shares REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    purchase_price REAL NOT NULL,
                    company_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Trading strategy settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT UNIQUE NOT NULL,
                    strategy_type TEXT NOT NULL DEFAULT 'simple',
                    parameters TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Trading recommendations log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD'
                    reason TEXT NOT NULL,
                    confidence REAL NOT NULL, -- 0-1 scale
                    price_at_recommendation REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sales transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_stock_id INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    shares_sold REAL NOT NULL,
                    sell_price REAL NOT NULL,
                    sell_date TEXT NOT NULL,
                    purchase_price REAL NOT NULL,
                    tax_fee REAL DEFAULT 0.0,
                    real_profit REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_stock_id) REFERENCES portfolio_stocks (id)
                )
            ''')
            
            conn.commit()
    
    def add_stock(self, ticker: str, shares: float, purchase_date: str, 
                  purchase_price: float, company_name: str = None) -> int:
        """Add a stock to the portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_stocks 
                (ticker, shares, purchase_date, purchase_price, company_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticker.upper(), shares, purchase_date, purchase_price, company_name))
            
            stock_id = cursor.lastrowid
            conn.commit()
            return stock_id
    
    def get_portfolio(self) -> List[Dict]:
        """Get all stocks from portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolio_stocks ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_stock(self, stock_id: int) -> bool:
        """Delete a stock from portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM portfolio_stocks WHERE id = ?', (stock_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def clear_portfolio(self) -> bool:
        """Clear all stocks from portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM portfolio_stocks')
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def update_stock(self, stock_id: int, shares: float = None, 
                    purchase_price: float = None) -> bool:
        """Update stock shares or purchase price"""
        updates = []
        params = []
        
        if shares is not None:
            updates.append('shares = ?')
            params.append(shares)
        
        if purchase_price is not None:
            updates.append('purchase_price = ?')
            params.append(purchase_price)
        
        if not updates:
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(stock_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE portfolio_stocks 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    # Trading strategy methods
    def save_strategy_settings(self, ticker: str, strategy_type: str, 
                              parameters: Dict) -> bool:
        """Save trading strategy settings for a ticker"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO strategy_settings 
                (ticker, strategy_type, parameters, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ticker.upper(), strategy_type, json.dumps(parameters)))
            conn.commit()
            return True
    
    def get_strategy_settings(self, ticker: str) -> Optional[Dict]:
        """Get trading strategy settings for a ticker"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strategy_type, parameters 
                FROM strategy_settings 
                WHERE ticker = ?
            ''', (ticker.upper(),))
            
            row = cursor.fetchone()
            if row:
                return {
                    'strategy_type': row['strategy_type'],
                    'parameters': json.loads(row['parameters'])
                }
            return None
    
    def log_recommendation(self, ticker: str, action: str, reason: str, 
                          confidence: float, price: float) -> int:
        """Log a trading recommendation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trading_recommendations 
                (ticker, action, reason, confidence, price_at_recommendation)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticker.upper(), action, reason, confidence, price))
            
            rec_id = cursor.lastrowid
            conn.commit()
            return rec_id
    
    def get_recent_recommendations(self, limit: int = 10) -> List[Dict]:
        """Get recent trading recommendations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trading_recommendations 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def export_portfolio_to_csv(self) -> str:
        """Export portfolio data to CSV format"""
        portfolio = self.get_portfolio()
        if not portfolio:
            return ""
        
        lines = ["ID,Ticker,Shares,Purchase Date,Purchase Price,Company Name,Created At"]
        for stock in portfolio:
            lines.append(f"{stock['id']},{stock['ticker']},{stock['shares']},"
                        f"{stock['purchase_date']},{stock['purchase_price']},"
                        f"{stock['company_name'] or ''},{stock['created_at']}")
        
        return "\n".join(lines)

# Global database instance
db = PortfolioDatabase()
