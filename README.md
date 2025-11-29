<div align="center">
  <h1>FinAI 💸</h1>
  <p><strong>Your AI-powered companion for navigating the financial markets.</strong></p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Getting Started</a> •
    <a href="#-contributing">Contributing</a>
  </p>
</div>

---

FinAI is a project born out of a passion for finance and technology. It's built to provide traders and investors with the tools they need for smart decision-making, all in one place. We're leveraging the power of AI to make financial analysis accessible to everyone.

## ✨ Features

-   **🤖 AI Chatbot:** Ask anything from "What is a P/E ratio?" to complex market queries.
-   **📈 Stock Prediction:** A machine learning model to forecast stock price movements.
-   **⚠️ Risk Analyser:** Evaluate the risk associated with different stocks.
-   **📰 News Feed & Sentiment:** Get the latest financial news and understand the market's mood using Ollam instruct.
-   **📊 Live Stock Data:** Real-time and historical data at your fingertips.
-   **🔐 Secure User Accounts:** Your personal data and portfolio are safe with us.

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)

-   **Backend:** Python, FastAPI, MongoDB, JWT, Hugging Face Transformers, yfinance
-   **Frontend:** Next.js, React, CSS Modules

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18.x+
- A running MongoDB instance.

### 1. Backend (`/fin-ai-backend`)
```bash
# Go to backend folder
cd fin-ai-backend

# Set up and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file from the example
cp .env.example .env 

# Edit the .env file with your own credentials
# nano .env (or use your favorite editor)

# Run the server
uvicorn main:app --reload
# Now running on http://127.0.0.1:8000
```

### 2. Frontend (`/fin-ai-frontend`)
```bash
# Go to frontend folder from root
cd fin-ai-frontend

# Install dependencies
npm install

# Run the development server
npm run dev
# Now running on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser and you're ready to go!

## 🤝 Contributing

We're just getting started! Contributions are welcome. Whether it's a bug fix, a new feature, or documentation improvements, feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---
