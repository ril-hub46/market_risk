# Value-at-Risk - Graduation Project (PFE)

This project was developed as part of my **Graduation Internship (PFE)** at the **Banque Centrale Populaire (BCP)** in Morocco, towards obtaining my **Engineering Degree in Statistics, Economics, and Big Data**.

The application provides an industrial-grade solution for calculating and monitoring the **Value-at-Risk ** of various portfolio (options, stocks, ...) using an interactive **Streamlit** dashboard.

## 🚀 Key Features
* **Risk Engine**: Monte Carlo simulations for VaR calculation and interest rate curve interpolation.
* **Interactive Analytics**: Real-time risk visualization and portfolio return simulations using Plotly.
* **Software Quality**: Rigorous unit testing and static code analysis to meet banking software standards.

---

## 🛠 Tech Stack & Industrialization
To ensure the project meets professional production standards, I implemented the following workflow:

* **Package Management**: `uv` (modern, ultra-fast Python package manager).
* **Code Quality**: `Ruff` for strict PEP8 compliance and linting (addressing E501 and unused imports).
* **Testing Framework**: `Pytest` with market data mocking for robust financial validation.
* **CI/CD**: Automated GitLab CI pipeline (Linting + Testing) to ensure code integrity.
* **Containerization**: **DevContainers** and Docker for total environment portability and seamless deployment.

---

##  Installation & Execution

### 1. Prerequisites
Ensure you have [Git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/) installed on your machine.

### 2. Clone the Repository
First, clone the project to your local machine:
```bash
git clone [https://gitlab.com/Rilwanou/value_at_risk.git](https://gitlab.com/Rilwanou/value_at_risk.git)
cd value_at_risk
uv sync
uv run streamlit run src/var/interface.py

### Manual Launch via Docker## 🛠 Tech Stack & Industrialization

To build and run the dashboard without local Python installation:
```bash
# Build the Docker image
docker build -t var-app-dev -f .devcontainer/Dockerfile .

# Launch the Streamlit dashboard
docker run -p 8501:8501 var-app-dev uv run streamlit run src/var/interface.py