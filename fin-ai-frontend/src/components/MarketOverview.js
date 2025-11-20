'use client';

import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const POPULAR_STOCKS = [
  { symbol: 'AAPL', name: 'Apple Inc.', color: '#3b82f6' },
  { symbol: 'MSFT', name: 'Microsoft', color: '#10b981' },
  { symbol: 'GOOGL', name: 'Alphabet', color: '#f59e0b' },
  { symbol: 'AMZN', name: 'Amazon', color: '#8b5cf6' },
  { symbol: 'TSLA', name: 'Tesla', color: '#ef4444' },
  { symbol: 'NVDA', name: 'NVIDIA', color: '#06b6d4' },
  { symbol: 'META', name: 'Meta', color: '#ec4899' },
  { symbol: 'NFLX', name: 'Netflix', color: '#f43f5e' },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000';

export default function MarketOverview() {
  const [selectedStock, setSelectedStock] = useState(POPULAR_STOCKS[0]);
  const [customSymbol, setCustomSymbol] = useState('');
  const [stockData, setStockData] = useState([]);
  const [marketIndices, setMarketIndices] = useState([]);
  const [safeStocks] = useState(POPULAR_STOCKS);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('1M');
  const [error, setError] = useState(null);

  const fetchStockData = async (ticker) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Fetching data for ${ticker}...`);
      
      const periodMap = { 
        '1W': '5d', 
        '1M': '1mo', 
        '3M': '3mo', 
        '1Y': '1y' 
      };
      
      const intervalMap = { 
        '1W': '1h',    // hourly for 1 week
        '1M': '1d',    // daily for 1 month
        '3M': '1d',    // daily for 3 months
        '1Y': '1wk'    // weekly for 1 year
      };

      const response = await axios.get(
        `${API_BASE_URL}/api/stock/${ticker}`,
        {
          params: {
            period: periodMap[timeRange],
            interval: intervalMap[timeRange],
          },
          timeout: 10000
        }
      );

      const stockDataFromBackend = response.data.data;
      
      if (!stockDataFromBackend || stockDataFromBackend.length === 0) {
        throw new Error('No data received from server');
      }
      
      const data = stockDataFromBackend.map((item) => ({
        date: new Date(item.timestamp * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        fullDate: new Date(item.timestamp * 1000).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
        price: parseFloat(item.close?.toFixed(2) || 0),
        volume: item.volume || 0,
      }));

      console.log(`✅ Fetched ${data.length} data points for ${ticker}`);
      setStockData(data);
      
    } catch (err) {
      console.error('Error fetching stock history:', err);
      
      let errorMessage = `Failed to load data for ${ticker}.`;
      
      if (err.code === 'ECONNABORTED') {
        errorMessage += ' Request timed out. Please try again.';
      } else if (err.response) {
        errorMessage += ` ${err.response.data?.detail || 'Server error.'}`;
      } else if (err.request) {
        errorMessage += ' Cannot connect to server. Make sure the backend is running on http://localhost:8000';
      } else {
        errorMessage += ' Please try again.';
      }
      
      setError(errorMessage);
      setStockData([]);
    }
    
    setLoading(false);
  };

  const fetchMarketIndices = async () => {
    try {
      const indices = [
        { symbol: '^GSPC', name: 'S&P 500' },
        { symbol: '^DJI', name: 'Dow Jones' },
        { symbol: '^IXIC', name: 'NASDAQ' },
        { symbol: '^RUT', name: 'Russell 2000' },
      ];

      const promises = indices.map(async (index) => {
        try {
          const response = await axios.get(
            `${API_BASE_URL}/api/stock/${index.symbol}`,
            { 
              params: { period: '5d', interval: '1d' },
              timeout: 10000
            }
          );

          const data = response.data.data;
          if (!data || data.length < 2) return null;
          
          const currentPrice = data[data.length - 1].close;
          const previousClose = data[data.length - 2].close;
          const change = currentPrice - previousClose;
          const changePercent = (change / previousClose) * 100;

          return {
            name: index.name,
            value: currentPrice,
            change: change,
            changePercent: changePercent,
          };
        } catch (err) {
          console.error(`Error fetching ${index.name}:`, err);
          return null;
        }
      });

      const results = (await Promise.all(promises)).filter(Boolean);
      
      if (results.length > 0) {
        setMarketIndices(results);
      } else {
        console.warn('Using fallback data for market indices');
        setMarketIndices([
          { name: 'S&P 500', value: 6052.85, change: 23.45, changePercent: 0.389 },
          { name: 'Dow Jones', value: 43870.35, change: -55.39, changePercent: -0.126 },
          { name: 'NASDAQ', value: 19268.89, change: 111.69, changePercent: 0.583 },
          { name: 'Russell 2000', value: 2304.22, change: 18.76, changePercent: 0.820 },
        ]);
      }
    } catch (err) {
      console.error('Error fetching market indices:', err);
      setMarketIndices([
        { name: 'S&P 500', value: 6052.85, change: 23.45, changePercent: 0.389 },
        { name: 'Dow Jones', value: 43870.35, change: -55.39, changePercent: -0.126 },
        { name: 'NASDAQ', value: 19268.89, change: 111.69, changePercent: 0.583 },
        { name: 'Russell 2000', value: 2304.22, change: 18.76, changePercent: 0.820 },
      ]);
    }
  };

  useEffect(() => {
    fetchMarketIndices();
  }, []);

  useEffect(() => {
    if (selectedStock?.symbol) {
      fetchStockData(selectedStock.symbol);
    }
  }, [selectedStock, timeRange]);

  const handleCustomSearch = (e) => {
    e.preventDefault();
    if (!customSymbol.trim()) return;
    
    const symbol = customSymbol.trim().toUpperCase();
    const existing = safeStocks.find((s) => s.symbol === symbol);
    
    setSelectedStock(existing || { symbol, name: symbol, color: '#6366f1' });
    setCustomSymbol('');
  };

  const currentPrice = stockData.length > 0 ? stockData[stockData.length - 1].price : 0;
  const previousPrice = stockData.length > 1 ? stockData[0].price : 0;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent = previousPrice !== 0 ? ((priceChange / previousPrice) * 100).toFixed(2) : 0;
  const isPositive = priceChange >= 0;

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: 12, color: 'white' }}>
        <p style={{ fontSize: 13, marginBottom: 4 }}>{payload[0].payload.fullDate}</p>
        <p style={{ fontSize: 18, fontWeight: 600 }}>${payload[0].value.toFixed(2)}</p>
      </div>
    );
  };

  const VolumeTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    return (
      <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: 12, color: 'white' }}>
        <p style={{ fontSize: 13, marginBottom: 4 }}>{payload[0].payload.fullDate}</p>
        <p style={{ fontSize: 18, fontWeight: 600 }}>{(payload[0].value / 1000000).toFixed(2)}M shares</p>
      </div>
    );
  };

  return (
    <>
      <style jsx>{`
        .container { max-width: 1400px; margin: 0 auto; padding: 32px 24px; font-family: 'Inter', sans-serif; }
        .section-title { font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
        .title-accent { width: 4px; height: 32px; background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%); border-radius: 4px; }
        .indices-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .index-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; transition: all 0.3s ease; position: relative; overflow: hidden; }
        .index-card::before { content: ''; position: absolute; top:0; left:0; width:100%; height:3px; background: linear-gradient(90deg,#3b82f6 0%,#2563eb 100%); transform: scaleX(0); transition: transform 0.3s ease; }
        .index-card:hover { box-shadow: 0 10px 25px rgba(0,0,0,0.12); transform: translateY(-2px); }
        .index-card:hover::before { transform: scaleX(1); }
        .index-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
        .index-name { font-size:13px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; }
        .status-dot { width:8px; height:8px; border-radius:50%; }
        .status-dot.positive { background:#10b981; box-shadow:0 0 8px rgba(16,185,129,0.5); }
        .status-dot.negative { background:#ef4444; box-shadow:0 0 8px rgba(239,68,68,0.5); }
        .index-value { font-size:32px; font-weight:700; color:#0f172a; margin-bottom:12px; line-height:1; }
        .index-change { display:flex; align-items:center; gap:8px; }
        .change-badge { font-size:13px; font-weight:600; padding:6px 12px; border-radius:6px; display:inline-flex; align-items:center; gap:4px; }
        .change-badge.positive { background:#dcfce7; color:#15803d; }
        .change-badge.negative { background:#fee2e2; color:#b91c1c; }
        .change-percent { font-size:13px; font-weight:600; }
        .change-percent.positive { color:#10b981; }
        .change-percent.negative { color:#ef4444; }
        .stock-selection-card { background:white; border-radius:16px; padding:32px; box-shadow:0 1px 3px rgba(0,0,0,0.08); border:1px solid #e2e8f0; margin-bottom:32px; }
        .search-form { margin-bottom:32px; }
        .search-wrapper { display:flex; gap:12px; }
        .search-input { flex:1; padding:16px 20px; font-size:15px; border:2px solid #e2e8f0; border-radius:12px; background:#f8fafc; color:#0f172a; transition: all 0.2s ease; }
        .search-input:focus { outline:none; border-color:#3b82f6; background:white; box-shadow:0 0 0 4px rgba(59,130,246,0.1); }
        .search-input::placeholder { color:#94a3b8; }
        .search-button { padding:16px 32px; background:linear-gradient(135deg,#3b82f6 0%,#2563eb 100%); color:white; border:none; border-radius:12px; font-size:15px; font-weight:600; cursor:pointer; display:flex; align-items:center; gap:8px; transition: all 0.2s ease; }
        .search-button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(59,130,246,0.3); }
        .popular-stocks-label { font-size:14px; font-weight:600; color:#64748b; margin-bottom:16px; }
        .stocks-buttons { display:flex; flex-wrap:wrap; gap:12px; }
        .stock-button { padding:12px 24px; border:2px solid #e2e8f0; background:white; border-radius:10px; font-size:14px; font-weight:600; color:#475569; cursor:pointer; transition: all 0.2s ease; }
        .stock-button:hover { border-color:#3b82f6; color:#3b82f6; transform: translateY(-2px); }
        .stock-button.active { background:linear-gradient(135deg,#3b82f6 0%,#2563eb 100%); color:white; border-color:transparent; transform: translateY(-2px); }
        .chart-card { background:white; border-radius:16px; box-shadow:0 1px 3px rgba(0,0,0,0.08); border:1px solid #e2e8f0; overflow:hidden; margin-bottom:32px; }
        .chart-header { padding:32px; border-bottom:1px solid #e2e8f0; background:linear-gradient(180deg,#f8fafc 0%,white 100%); }
        .chart-header-content { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:24px; }
        .stock-info { flex:1; min-width:300px; }
        .stock-title { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
        .stock-symbol { font-size:36px; font-weight:700; color:#0f172a; }
        .stock-name { font-size:18px; color:#64748b; font-weight:500; }
        .price-info { display:flex; align-items:baseline; gap:16px; }
        .current-price { font-size:48px; font-weight:700; color:#0f172a; line-height:1; }
        .price-change { font-size:20px; font-weight:600; display:flex; align-items:center; gap:4px; }
        .price-change.positive { color:#10b981; }
        .price-change.negative { color:#ef4444; }
        .time-selector { display:flex; gap:8px; background:#f1f5f9; padding:6px; border-radius:12px; }
        .time-button { padding:10px 20px; border:none; background:transparent; border-radius:8px; font-size:14px; font-weight:600; color:#64748b; cursor:pointer; transition: all 0.2s ease; }
        .time-button:hover { color:#3b82f6; }
        .time-button.active { background:white; color:#3b82f6; box-shadow:0 2px 8px rgba(0,0,0,0.08); }
        .chart-content { padding:32px; }
        .loading-container { height:400px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px; }
        .spinner { width:48px; height:48px; border:4px solid #e2e8f0; border-top-color:#3b82f6; border-radius:50%; animation:spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { color:#64748b; font-size:14px; }
        .error-message { color:#ef4444; background:#fee2e2; padding:16px; border-radius:8px; margin:16px 0; text-align:center; font-size:14px; }
        .volume-card { background:white; border-radius:16px; box-shadow:0 1px 3px rgba(0,0,0,0.08); border:1px solid #e2e8f0; padding:32px; margin-bottom:32px; }
        .volume-title { font-size:20px; font-weight:700; color:#0f172a; margin-bottom:24px; display:flex; align-items:center; gap:12px; }
        .volume-accent { width:4px; height:24px; background:linear-gradient(180deg,#8b5cf6 0%,#7c3aed 100%); border-radius:4px; }
        @media (max-width:768px) {
          .container { padding:20px 16px; }
          .indices-grid { grid-template-columns:1fr; }
          .search-wrapper { flex-direction:column; }
          .search-button { width:100%; justify-content:center; }
          .stock-button { flex:1; min-width:calc(50% - 6px); }
          .chart-header-content { flex-direction:column; align-items:flex-start; }
          .stock-symbol { font-size:28px; }
          .current-price { font-size:36px; }
          .time-selector { width:100%; }
          .time-button { flex:1; }
        }
      `}</style>

      <div className="container">
        <br></br>
        <br></br>
        <br></br>
        <h2 className="section-title"><span className="title-accent"></span>Market Overview</h2>
        <div className="indices-grid">
          {marketIndices.map((index, i) => (
            <div key={i} className="index-card">
              <div className="index-header">
                <h3 className="index-name">{index.name}</h3>
                <span className={`status-dot ${index.change >= 0 ? 'positive' : 'negative'}`}></span>
              </div>
              <p className="index-value">{index.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
              <div className="index-change">
                <span className={`change-badge ${index.change >= 0 ? 'positive' : 'negative'}`}>
                  {index.change >= 0 ? '↑' : '↓'} {Math.abs(index.change).toFixed(2)}
                </span>
                <span className={`change-percent ${index.change >= 0 ? 'positive' : 'negative'}`}>
                  ({Math.abs(index.changePercent).toFixed(2)}%)
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="stock-selection-card">
          <form onSubmit={handleCustomSearch} className="search-form">
            <div className="search-wrapper">
              <input 
                type="text" 
                value={customSymbol} 
                onChange={(e) => setCustomSymbol(e.target.value)} 
                placeholder="Enter stock symbol (e.g., AAPL)" 
                className="search-input" 
              />
              <button type="submit" className="search-button">
                🔍 Search
              </button>
            </div>
          </form>
          <p className="popular-stocks-label">Popular Stocks</p>
          <div className="stocks-buttons">
            {safeStocks.map((s) => (
              <button
                key={s.symbol}
                onClick={() => setSelectedStock(s)}
                className={`stock-button ${selectedStock?.symbol === s.symbol ? 'active' : ''}`}
                style={{ 
                  borderColor: selectedStock?.symbol === s.symbol ? 'transparent' : s.color, 
                  color: selectedStock?.symbol === s.symbol ? 'white' : s.color, 
                  background: selectedStock?.symbol === s.symbol ? s.color : 'white' 
                }}
              >
                {s.symbol}
              </button>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-header">
            <div className="chart-header-content">
              <div className="stock-info">
                <div className="stock-title">
                  <h1 className="stock-symbol">{selectedStock?.symbol}</h1>
                  <h2 className="stock-name">{selectedStock?.name}</h2>
                </div>
                <div className="price-info">
                  <span className="current-price">${currentPrice.toFixed(2)}</span>
                  <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? '↑' : '↓'} ${Math.abs(priceChange).toFixed(2)} ({priceChangePercent}%)
                  </span>
                </div>
              </div>
              <div className="time-selector">
                {['1H','1W','3M','1Y'].map((range) => (
                  <button 
                    key={range} 
                    onClick={() => setTimeRange(range)} 
                    className={`time-button ${timeRange === range ? 'active' : ''}`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="chart-content">
            {error && <div className="error-message">{error}</div>}
            {loading ? (
              <div className="loading-container">
                <div className="spinner"></div>
                <p className="loading-text">Loading chart data...</p>
              </div>
            ) : stockData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={stockData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={selectedStock?.color || '#3b82f6'} stopOpacity={0.4}/>
                      <stop offset="95%" stopColor={selectedStock?.color || '#3b82f6'} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} domain={['auto','auto']} />
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="price" stroke={selectedStock?.color || '#3b82f6'} strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="loading-container">
                <p className="loading-text">No data available</p>
              </div>
            )}
          </div>
        </div>

        {stockData.length > 0 && (
          <div className="volume-card">
            <div className="volume-title">
              <span className="volume-accent"></span> Trading Volume
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={stockData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} domain={['auto','auto']} />
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <Tooltip content={<VolumeTooltip />} />
                <Area type="monotone" dataKey="volume" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </>
  );
}