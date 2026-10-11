# Value-at-Risk - Graduation Project (PFE)

This project was developed as part of my **Graduation Internship (PFE)** at the **Banque Centrale Populaire (BCP)** in Morocco, towards obtaining my **Engineering Degree in Statistics, Economics, and Big Data**.

The application provides an industrial-grade solution for calculating and monitoring the **Value-at-Risk ** of various portfolio (options, stocks, ...) using an interactive **Streamlit** dashboard.

##  Key Features
* **Risk Engine**: Monte Carlo simulations for VaR calculation and interest rate curve interpolation.
* **Interactive Analytics**: Real-time risk visualization and portfolio return simulations using Plotly.
* **Software Quality**: Rigorous unit testing and static code analysis to meet banking software standards.

---

##  Tech Stack
To ensure the project meets professional production standards, I implemented the following workflow:

* **Package Management**: `uv` (modern, ultra-fast Python package manager).
* **Code Quality**: `Ruff` for strict PEP8 compliance and linting (addressing E501 and unused imports).
* **Testing Framework**: `Pytest` with market data mocking for robust financial validation.
* **CI/CD**: Automated GitLab CI pipeline (Linting + Testing) to ensure code integrity.
* **Containerization**: **DevContainers** and Docker for total environment portability and seamless deployment.

---

##  Project Structure

The project is split into three independent layers:

```
value_at_risk/
├── api/            # FastAPI backend — receives raw Excel uploads, parses them
│   ├── main.py     #   (via pkg.data_processing) and runs the VaR engine (pkg.model)
│   ├── routers/    # /var/options, /var/stocks, /var/historical endpoints
│   └── schemas.py  # Pydantic response models
│
├── pkg/            # Pure calculation logic — no UI/web framework dependency
│   ├── model.py            # Monte Carlo, Cornish-Fisher, GBM, historical VaR
│   ├── data_processing.py  # Excel parsing/cleaning (options, prices, curves, quantities)
│   └── data/
│       ├── raw/
│       └── processed/
│
├── web/            # Streamlit frontend — UI only, talks to the API over HTTP
│   ├── main.py
│   ├── interface.py
│   └── api_client.py
│
└── tests/
    ├── pkg/
    └── api/
```

##  Installation & Execution

### 1. Prerequisites
Ensure you have [Git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/) installed on your machine.

### 2. Clone the Repository
First, clone the project to your local machine:
```bash
git clone https://gitlab.com/Rilwanou/value_at_risk.git
cd value_at_risk
uv sync
```

### 3. Run the app
Two processes are needed: the API (backend) and the Streamlit dashboard (frontend).

```bash
# Terminal 1 — backend
uv run uvicorn api.main:app --reload

# Terminal 2 — frontend (talks to the API on http://localhost:8000 by default,
# override with the API_BASE_URL env var)
uv run streamlit run web/main.py
```

### 4. Run via Docker
The devcontainer image ships the environment only (no default command). Run both
processes inside it:
```bash
docker build -t var-app-dev -f .devcontainer/Dockerfile .
docker run -p 8501:8501 -p 8000:8000 var-app-dev \
  bash -c "uv run uvicorn api.main:app --host 0.0.0.0 & uv run streamlit run web/main.py --server.address 0.0.0.0"
```