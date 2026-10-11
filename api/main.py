from fastapi import FastAPI

from api.routers import historical, options, stocks

app = FastAPI(title="Value-at-Risk API")

app.include_router(options.router)
app.include_router(stocks.router)
app.include_router(historical.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
