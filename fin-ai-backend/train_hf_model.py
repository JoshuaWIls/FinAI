import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from scipy.special import softmax
import warnings
warnings.filterwarnings('ignore')

class StockPredictor:
    """
    Advanced Stock Predictor using Hugging Face FinBERT and real-time data
    """
    
    def __init__(self):
        print("Initializing Stock Predictor with Hugging Face FinBERT...")
        
        # Load FinBERT for sentiment analysis
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.sentiment_model.eval()
        
        # Technical indicator model (to be trained)
        self.technical_model = None
        self.scaler = StandardScaler()
        
        print("FinBERT loaded successfully!")
    
    def get_sentiment_score(self, text):
        """
        Get sentiment score from text using FinBERT
        Returns: sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
        """
        if not text or len(text.strip()) == 0:
            return 0.0
        
        try:
            inputs = self.sentiment_tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                scores = outputs.logits[0].detach().numpy()
                probs = softmax(scores)
            
            # FinBERT outputs: [negative, neutral, positive]
            sentiment_score = probs[2] - probs[0]  # positive - negative
            
            return float(sentiment_score)
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return 0.0
    
    def calculate_technical_indicators(self, df):
        """
        Calculate technical indicators from price data
        """
        # Returns
        df['Returns'] = df['Close'].pct_change()
        
        # Moving averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        # Exponential moving averages
        df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # Volatility
        df['Volatility'] = df['Returns'].rolling(window=20).std()
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Price momentum
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        
        # Rate of Change
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        return df
    
    def fetch_and_prepare_data(self, symbols, period='2y'):
        """
        Fetch data for multiple symbols and prepare training dataset
        """
        all_data = []
        
        for symbol in symbols:
            print(f"Fetching data for {symbol}...")
            try:
                stock = yf.Ticker(symbol)
                df = stock.history(period=period)
                
                if df.empty:
                    continue
                
                # Calculate technical indicators
                df = self.calculate_technical_indicators(df)
                
                # Get recent news and sentiment
                try:
                    news = stock.news[:5]  # Last 5 news items
                    sentiments = []
                    
                    for item in news:
                        title = item.get('title', '')
                        summary = item.get('summary', '')
                        text = f"{title}. {summary}"
                        sentiment = self.get_sentiment_score(text)
                        sentiments.append(sentiment)
                    
                    avg_sentiment = np.mean(sentiments) if sentiments else 0.0
                    df['News_Sentiment'] = avg_sentiment
                    
                except:
                    df['News_Sentiment'] = 0.0
                
                # Create target: 1 if next 5 days average return > 0, 0 otherwise
                df['Future_Returns'] = df['Close'].shift(-5) / df['Close'] - 1
                df['Target'] = (df['Future_Returns'] > 0.01).astype(int)  # >1% gain
                
                df['Symbol'] = symbol
                all_data.append(df)
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
        
        combined_df = pd.concat(all_data, ignore_index=False)
        combined_df = combined_df.dropna()
        
        return combined_df
    
    def train_model(self, symbols=None):
        """
        Train the stock prediction model
        """
        if symbols is None:
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 
                      'NFLX', 'JPM', 'BAC', 'WMT', 'DIS', 'INTC', 'AMD']
        
        print("\n" + "="*60)
        print("TRAINING ADVANCED STOCK PREDICTOR")
        print("Using Hugging Face FinBERT + Technical Analysis")
        print("="*60)
        
        # Fetch and prepare data
        print("\n1. Fetching and preparing data...")
        df = self.fetch_and_prepare_data(symbols)
        
        print(f"Total samples: {len(df)}")
        
        # Select features
        feature_columns = [
            'Returns', 'SMA_5', 'SMA_10', 'SMA_20', 'EMA_5', 'EMA_20',
            'Volatility', 'RSI', 'MACD', 'Signal_Line', 'BB_Width',
            'Volume_Ratio', 'Momentum', 'ROC', 'News_Sentiment'
        ]
        
        X = df[feature_columns].values
        y = df['Target'].values
        
        print(f"\n2. Feature matrix shape: {X.shape}")
        print(f"   Positive samples: {np.sum(y)} ({np.mean(y)*100:.2f}%)")
        print(f"   Negative samples: {len(y) - np.sum(y)} ({(1-np.mean(y))*100:.2f}%)")
        
        # Split data
        print("\n3. Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        print("\n4. Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        print("\n5. Training Gradient Boosting model...")
        self.technical_model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=50,
            min_samples_leaf=20,
            subsample=0.8,
            random_state=42
        )
        
        self.technical_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        print("\n6. Evaluating model...")
        train_score = self.technical_model.score(X_train_scaled, y_train)
        test_score = self.technical_model.score(X_test_scaled, y_test)
        
        print(f"   Training accuracy: {train_score*100:.2f}%")
        print(f"   Testing accuracy: {test_score*100:.2f}%")
        
        # Feature importance
        print("\n7. Feature Importance:")
        importance = self.technical_model.feature_importances_
        feature_imp = sorted(zip(feature_columns, importance), key=lambda x: x[1], reverse=True)
        
        for name, imp in feature_imp[:10]:
            print(f"   {name:20s}: {imp:.4f}")
        
        return self.technical_model, self.scaler
    
    def save_model(self, path='./models/stock_predictor.joblib'):
        """
        Save the trained model and scaler
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'technical_model': self.technical_model,
            'scaler': self.scaler,
            'feature_columns': [
                'Returns', 'SMA_5', 'SMA_10', 'SMA_20', 'EMA_5', 'EMA_20',
                'Volatility', 'RSI', 'MACD', 'Signal_Line', 'BB_Width',
                'Volume_Ratio', 'Momentum', 'ROC', 'News_Sentiment'
            ]
        }
        
        joblib.dump(model_data, path)
        print(f"\n8. Model saved to: {path}")
        print(f"   File size: {os.path.getsize(path) / 1024:.2f} KB")
    
    def predict_realtime(self, symbol):
        """
        Make prediction using real-time data
        """
        print(f"\nMaking real-time prediction for {symbol}...")
        
        # Fetch recent data
        stock = yf.Ticker(symbol)
        df = stock.history(period='3mo')
        
        # Calculate indicators
        df = self.calculate_technical_indicators(df)
        
        # Get sentiment from recent news
        try:
            news = stock.news[:10]
            sentiments = []
            
            for item in news:
                title = item.get('title', '')
                summary = item.get('summary', '')
                text = f"{title}. {summary}"
                sentiment = self.get_sentiment_score(text)
                sentiments.append(sentiment)
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
        except:
            avg_sentiment = 0.0
        
        # Prepare features from latest data
        latest = df.iloc[-1]
        features = np.array([[
            latest['Returns'],
            latest['SMA_5'],
            latest['SMA_10'],
            latest['SMA_20'],
            latest['EMA_5'],
            latest['EMA_20'],
            latest['Volatility'],
            latest['RSI'],
            latest['MACD'],
            latest['Signal_Line'],
            latest['BB_Width'],
            latest['Volume_Ratio'],
            latest['Momentum'],
            latest['ROC'],
            avg_sentiment
        ]])
        
        # Scale and predict
        features_scaled = self.scaler.transform(features)
        prediction = self.technical_model.predict(features_scaled)[0]
        probability = self.technical_model.predict_proba(features_scaled)[0]
        
        print(f"Prediction: {'BUY' if prediction == 1 else 'SELL'}")
        print(f"Confidence: {max(probability)*100:.2f}%")
        print(f"News Sentiment: {avg_sentiment:.3f}")
        
        return prediction, probability, avg_sentiment


def main():
    """
    Main training function
    """
    try:
        # Initialize predictor
        predictor = StockPredictor()
        
        # Train model
        predictor.train_model()
        
        # Save model
        predictor.save_model()
        
        print("\n" + "="*60)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Test with real-time prediction
        print("\n" + "="*60)
        print("TESTING WITH REAL-TIME DATA")
        print("="*60)
        
        test_symbols = ['AAPL', 'TSLA', 'GOOGL']
        for symbol in test_symbols:
            try:
                predictor.predict_realtime(symbol)
            except Exception as e:
                print(f"Error predicting {symbol}: {e}")
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()