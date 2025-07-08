# 🚚 Pegazzo Drivers Monolith API

This is the repository for the Pegazzo Monolith with **FastAPI** and **SQLAlchemy**, designed to manage drivers.

---

## 📦 Features

- ⚡️ FastAPI framework for high-performance APIs
- 🧱 SQLAlchemy for ORM and database handling

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/pegazzo-drivers-api.git
cd pegazzo-drivers-api
```

### 2. Install dependencies using Pipenv

```bash
pipenv install
```

### 3. Set up environment variables

First, activate your virtual environment:

```bash
pipenv shell
```

Create a `.env` file in the root directory and add the following variables:

```bash
ENV=development
DEBUG=true
DATABASE_URL=sqlite:///./dev.db
```

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

### 5. Access the API

Open your browser and navigate to `http://localhost:8000` to access the API.
