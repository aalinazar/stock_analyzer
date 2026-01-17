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
            
            # Watchlist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT UNIQUE NOT NULL,
                    target_buy_price REAL,
                    target_sell_price REAL,
                    notes TEXT,
                    status TEXT DEFAULT 'watching',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    purchase_price: float = None, purchase_date: str = None,
                    ticker: str = None, company_name: str = None) -> bool:
        """Update stock details"""
        updates = []
        params = []
        
        if shares is not None:
            updates.append('shares = ?')
            params.append(shares)
        
        if purchase_price is not None:
            updates.append('purchase_price = ?')
            params.append(purchase_price)
        
        if purchase_date is not None:
            updates.append('purchase_date = ?')
            params.append(purchase_date)
        
        if ticker is not None:
            updates.append('ticker = ?')
            params.append(ticker.upper())
        
        if company_name is not None:
            updates.append('company_name = ?')
            params.append(company_name)
        
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
    
    def sell_stock(self, portfolio_stock_id: int, shares_sold: float, sell_price: float, 
                   sell_date: str, tax_fee: float = 0.0) -> Tuple[bool, str]:
        """Sell shares from a stock in portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the stock details
            cursor.execute('SELECT * FROM portfolio_stocks WHERE id = ?', (portfolio_stock_id,))
            stock = cursor.fetchone()
            
            if not stock:
                return False, "Stock not found in portfolio"
            
            stock_dict = dict(stock)
            
            if shares_sold > stock_dict['shares']:
                return False, f"Cannot sell {shares_sold} shares. Only {stock_dict['shares']} shares available"
            
            # Calculate real profit
            purchase_cost = shares_sold * stock_dict['purchase_price']
            sell_revenue = shares_sold * sell_price
            real_profit = sell_revenue - purchase_cost - tax_fee
            
            # Record the sale transaction
            cursor.execute('''
                INSERT INTO sales_transactions 
                (portfolio_stock_id, ticker, shares_sold, sell_price, sell_date, 
                 purchase_price, tax_fee, real_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (portfolio_stock_id, stock_dict['ticker'], shares_sold, sell_price, 
                  sell_date, stock_dict['purchase_price'], tax_fee, real_profit))
            
            # Update the remaining shares
            remaining_shares = stock_dict['shares'] - shares_sold
            
            if remaining_shares > 0:
                cursor.execute('''
                    UPDATE portfolio_stocks 
                    SET shares = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (remaining_shares, portfolio_stock_id))
            else:
                # Remove the stock if all shares are sold
                cursor.execute('DELETE FROM portfolio_stocks WHERE id = ?', (portfolio_stock_id,))
            
            conn.commit()
            return True, f"Successfully sold {shares_sold} shares of {stock_dict['ticker']}. Real profit: {real_profit:.2f}"
    
    def get_sales_history(self) -> List[Dict]:
        """Get all sales transactions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT st.*, ps.company_name 
                FROM sales_transactions st
                LEFT JOIN portfolio_stocks ps ON st.portfolio_stock_id = ps.id
                ORDER BY st.sell_date DESC, st.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sales_for_stock(self, portfolio_stock_id: int) -> List[Dict]:
        """Get sales transactions for a specific stock"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sales_transactions 
                WHERE portfolio_stock_id = ?
                ORDER BY sell_date DESC, created_at DESC
            ''', (portfolio_stock_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_realized_profits(self) -> float:
        """Calculate total realized profits from all sales"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(real_profit) FROM sales_transactions')
            result = cursor.fetchone()
            return result[0] if result[0] else 0.0
    
    def update_sales_transaction(self, sale_id: int, shares_sold: float = None, 
                                sell_price: float = None, sell_date: str = None,
                                tax_fee: float = None) -> Tuple[bool, str]:
        """Update a sales transaction"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the original sale transaction
            cursor.execute('SELECT * FROM sales_transactions WHERE id = ?', (sale_id,))
            sale = cursor.fetchone()
            
            if not sale:
                return False, "Sales transaction not found"
            
            sale_dict = dict(sale)
            
            # Use original values if new ones not provided
            new_shares_sold = shares_sold if shares_sold is not None else sale_dict['shares_sold']
            new_sell_price = sell_price if sell_price is not None else sale_dict['sell_price']
            new_sell_date = sell_date if sell_date is not None else sale_dict['sell_date']
            new_tax_fee = tax_fee if tax_fee is not None else sale_dict['tax_fee']
            
            # Calculate new real profit
            purchase_cost = new_shares_sold * sale_dict['purchase_price']
            sell_revenue = new_shares_sold * new_sell_price
            new_real_profit = sell_revenue - purchase_cost - new_tax_fee
            
            # Update the sales transaction
            cursor.execute('''
                UPDATE sales_transactions 
                SET shares_sold = ?, sell_price = ?, sell_date = ?, 
                    tax_fee = ?, real_profit = ?
                WHERE id = ?
            ''', (new_shares_sold, new_sell_price, new_sell_date, 
                  new_tax_fee, new_real_profit, sale_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            
            if updated:
                return True, f"Sales transaction updated successfully. New real profit: {new_real_profit:.2f}"
            else:
                return False, "Failed to update sales transaction"
    
    def delete_sales_transaction(self, sale_id: int) -> Tuple[bool, str]:
        """Delete a sales transaction"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sales_transactions WHERE id = ?', (sale_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                return True, "Sales transaction deleted successfully"
            else:
                return False, "Sales transaction not found or already deleted"
    
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
    
    # Watchlist methods
    def add_to_watchlist(self, ticker: str, target_buy_price: float = None, 
                        target_sell_price: float = None, notes: str = None) -> int:
        """Add a stock to the watchlist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO watchlist 
                (ticker, target_buy_price, target_sell_price, notes, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ticker.upper(), target_buy_price, target_sell_price, notes))
            
            watchlist_id = cursor.lastrowid
            conn.commit()
            return watchlist_id
    
    def get_watchlist(self) -> List[Dict]:
        """Get all stocks from watchlist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM watchlist ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_watchlist_stock(self, ticker: str) -> Optional[Dict]:
        """Get a specific stock from watchlist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM watchlist WHERE ticker = ?', (ticker.upper(),))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_watchlist_stock(self, ticker: str, target_buy_price: float = None, 
                              target_sell_price: float = None, notes: str = None, 
                              status: str = None) -> bool:
        """Update watchlist stock details"""
        updates = []
        params = []
        
        if target_buy_price is not None:
            updates.append('target_buy_price = ?')
            params.append(target_buy_price)
        
        if target_sell_price is not None:
            updates.append('target_sell_price = ?')
            params.append(target_sell_price)
        
        if notes is not None:
            updates.append('notes = ?')
            params.append(notes)
        
        if status is not None:
            updates.append('status = ?')
            params.append(status)
        
        if not updates:
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(ticker.upper())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE watchlist 
                SET {', '.join(updates)}
                WHERE ticker = ?
            ''', params)
            
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    def remove_from_watchlist(self, ticker: str) -> bool:
        """Remove a stock from watchlist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker.upper(),))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def clear_watchlist(self) -> bool:
        """Clear all stocks from watchlist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist')
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def export_watchlist_to_csv(self) -> str:
        """Export watchlist data to CSV format"""
        watchlist = self.get_watchlist()
        if not watchlist:
            return ""
        
        lines = ["ID,Ticker,Target Buy Price,Target Sell Price,Status,Notes,Created At"]
        for stock in watchlist:
            lines.append(f"{stock['id']},{stock['ticker']},{stock['target_buy_price'] or ''},"
                        f"{stock['target_sell_price'] or ''},{stock['status']},"
                        f"{stock['notes'] or ''},{stock['created_at']}")
        
        return "\n".join(lines)
    
    def import_watchlist_from_csv(self, csv_data, handle_duplicates='skip', validate_tickers=True):
        """
        Import watchlist data from CSV
        
        Args:
            csv_data: CSV file object or string
            handle_duplicates: How to handle existing tickers ('skip', 'update', 'replace')
            validate_tickers: Whether to validate ticker symbols with yfinance
            
        Returns:
            dict: Import results with success count, error count, and details
        """
        import io
        import pandas as pd
        
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'warnings': [],
            'imported_stocks': [],
            'skipped_stocks': [],
            'updated_stocks': []
        }
        
        try:
            # Read CSV data
            if hasattr(csv_data, 'read'):
                df = pd.read_csv(csv_data)
            else:
                df = pd.read_csv(io.StringIO(csv_data))
            
            # Standardize column names (case-insensitive)
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Check required columns
            if 'ticker' not in df.columns:
                results['errors'].append("CSV must contain a 'ticker' column")
                results['error_count'] += 1
                return results
            
            # Get existing watchlist to check for duplicates
            existing_watchlist = self.get_watchlist()
            existing_tickers = {stock['ticker'] for stock in existing_watchlist}
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Extract and validate ticker
                    ticker = str(row['ticker']).strip().upper()
                    if not ticker or ticker == 'NAN':
                        results['errors'].append(f"Row {index + 1}: Missing or invalid ticker")
                        results['error_count'] += 1
                        continue
                    
                    # Check for duplicates
                    if ticker in existing_tickers:
                        if handle_duplicates == 'skip':
                            results['skipped_stocks'].append(ticker)
                            results['warnings'].append(f"Row {index + 1}: {ticker} already exists in watchlist (skipped)")
                            continue
                        elif handle_duplicates == 'replace':
                            # Remove existing entry before adding new one
                            self.remove_from_watchlist(ticker)
                            existing_tickers.remove(ticker)
                    
                    # Validate ticker symbol if requested
                    if validate_tickers:
                        try:
                            import yfinance as yf
                            stock = yf.Ticker(ticker)
                            info = stock.info
                            # Check if we got valid data
                            if not info or info.get('regularMarketPrice') is None and info.get('currentPrice') is None:
                                # Try history as fallback
                                hist = stock.history(period="1d")
                                if hist.empty:
                                    results['warnings'].append(f"Row {index + 1}: Could not validate ticker {ticker} (adding anyway)")
                        except Exception as e:
                            results['warnings'].append(f"Row {index + 1}: Could not validate ticker {ticker}: {str(e)} (adding anyway)")
                    
                    # Extract optional fields
                    target_buy_price = None
                    target_sell_price = None
                    notes = None
                    status = 'watching'
                    
                    # Handle target buy price
                    if 'target_buy_price' in df.columns and pd.notna(row['target_buy_price']):
                        try:
                            target_buy_price = float(row['target_buy_price'])
                            if target_buy_price <= 0:
                                target_buy_price = None
                        except (ValueError, TypeError):
                            results['warnings'].append(f"Row {index + 1}: Invalid target_buy_price for {ticker}")
                    
                    # Handle target sell price
                    if 'target_sell_price' in df.columns and pd.notna(row['target_sell_price']):
                        try:
                            target_sell_price = float(row['target_sell_price'])
                            if target_sell_price <= 0:
                                target_sell_price = None
                        except (ValueError, TypeError):
                            results['warnings'].append(f"Row {index + 1}: Invalid target_sell_price for {ticker}")
                    
                    # Handle notes
                    if 'notes' in df.columns and pd.notna(row['notes']):
                        notes = str(row['notes']).strip()
                        if notes == 'NAN':
                            notes = None
                    
                    # Handle status
                    if 'status' in df.columns and pd.notna(row['status']):
                        status = str(row['status']).strip().lower()
                        valid_statuses = ['watching', 'ready_to_buy', 'ready_to_sell', 'paused']
                        if status not in valid_statuses:
                            status = 'watching'
                            results['warnings'].append(f"Row {index + 1}: Invalid status for {ticker}, using 'watching'")
                    
                    # Add to watchlist
                    if handle_duplicates == 'update' and ticker in existing_tickers:
                        # Update existing entry
                        success = self.update_watchlist_stock(
                            ticker=ticker,
                            target_buy_price=target_buy_price,
                            target_sell_price=target_sell_price,
                            notes=notes,
                            status=status
                        )
                        if success:
                            results['updated_stocks'].append(ticker)
                            results['success_count'] += 1
                        else:
                            results['errors'].append(f"Row {index + 1}: Failed to update {ticker}")
                            results['error_count'] += 1
                    else:
                        # Add new entry
                        watchlist_id = self.add_to_watchlist(
                            ticker=ticker,
                            target_buy_price=target_buy_price,
                            target_sell_price=target_sell_price,
                            notes=notes
                        )
                        results['imported_stocks'].append(ticker)
                        results['success_count'] += 1
                
                except Exception as e:
                    results['errors'].append(f"Row {index + 1}: Error processing {row.get('ticker', 'unknown')}: {str(e)}")
                    results['error_count'] += 1
            
        except Exception as e:
            results['errors'].append(f"Error reading CSV file: {str(e)}")
            results['error_count'] += 1
        
        return results

# Global database instance
db = PortfolioDatabase()
