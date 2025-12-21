import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.stats import kurtosis, norm, skew


def find_nearest_date(date, data):
    if not isinstance(date, pd.Timestamp):
        date = pd.to_datetime(date, dayfirst=True)
    if date in data["Date"].values:
        return data.loc[data["Date"] == date].iloc[0].iloc[1:]
    else:
        idx = (data["Date"] - date).abs().idxmin()
        return data.iloc[idx].iloc[1:]


def get_rates(date, T, currency, dic):
    T = T / 365
    if currency == "EURMAD":
        r_f_curve = find_nearest_date(date, dic["EUR"])
    elif currency == "USDMAD":
        r_f_curve = find_nearest_date(date, dic["USD"])
    else:
        raise ValueError("Devise non reconnue")

    r_d_curve = find_nearest_date(date, dic["MAD"])
    ASE_mat = dic["MAD"].columns.drop("Date").astype(float)
    r_f = interp1d(ASE_mat, r_f_curve, kind="linear", fill_value="extrapolate")(T)
    r_d = interp1d(ASE_mat, r_d_curve, kind="linear", fill_value="extrapolate")(T)

    return float(r_d), float(r_f)


def compute_var(data, date, var_confidence, n_simulations, dic):
    np.random.seed(5)
    delta_t = 1 / 365

    S0 = data["Spot"].values[:, np.newaxis]
    sigma = data["Vol"].values[:, np.newaxis]
    K = data["Strike"].values[:, np.newaxis]
    T = (data["Maturity"].values / 365)[:, np.newaxis]
    pos = data["Position Units"].values[:, np.newaxis]
    types = data["Type"].values
    currs = data["Currency"].values

    n_options = len(data)

    rds = np.zeros((n_options, 1))
    rfs = np.zeros((n_options, 1))
    for i in range(n_options):
        rds[i], rfs[i] = get_rates(date, T[i, 0], currs[i], dic)

    Z = np.random.normal(0, 1, (1, n_simulations))

    S_future = S0 * np.exp(
        (rds - rfs - 0.5 * sigma**2) * delta_t + sigma * np.sqrt(delta_t) * Z
    )

    d1_init = (np.log(S0 / K) + (rds - rfs + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2_init = d1_init - sigma * np.sqrt(T)

    d1_future = (np.log(S_future / K) + (rds - rfs + 0.5 * sigma**2) * T) / (
        sigma * np.sqrt(T)
    )
    d2_future = d1_future - sigma * np.sqrt(T)

    call_mask = (types == "Call")[:, np.newaxis]

    price_init = np.where(
        call_mask,
        S0 * np.exp(-rfs * T) * norm.cdf(d1_init)
        - K * np.exp(-rds * T) * norm.cdf(d2_init),
        K * np.exp(-rds * T) * norm.cdf(-d2_init)
        - S0 * np.exp(-rfs * T) * norm.cdf(-d1_init),
    )

    price_future = np.where(
        call_mask,
        S_future * np.exp(-rfs * T) * norm.cdf(d1_future)
        - K * np.exp(-rds * T) * norm.cdf(d2_future),
        K * np.exp(-rds * T) * norm.cdf(-d2_future)
        - S_future * np.exp(-rfs * T) * norm.cdf(-d1_future),
    )
    pnl = pos * (price_future - price_init)

    pnl_total = np.sum(pnl, axis=0)

    var_value = -np.percentile(pnl_total, 100 * (1 - var_confidence))
    return var_value, pnl_total.tolist()


def CF_var(returns, var_confidence, weights):
    port_returns = returns.dot(weights)
    z = norm.ppf(var_confidence / 100)
    s = skew(port_returns)
    k = kurtosis(port_returns)
    z_mod = (
        z
        + (z**2 - 1) * s / 6
        + (z**3 - 3 * z) * (k - 3) / 24
        - (2 * z**3 - 5 * z) * (s**2) / 36
    )
    return -(port_returns.mean() + z_mod * port_returns.std(ddof=0))


def GBM(n_sims, returns, weights, var_confidence):
    n_assets = returns.shape[1]
    mu = returns.mean().values
    sigma = returns.std().values
    dt = 1
    np.random.seed(44)
    Z = np.random.normal(size=(n_sims, n_assets))
    sim_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    sim_portofolio = sim_returns @ weights
    return -np.percentile(sim_portofolio, 100 - var_confidence), sim_portofolio


def compute_historical_var(df_prices, df_quantities, confidence_level, nb_returns):
    df_prices = df_prices.sort_index(ascending=False)
    df_prices = df_prices.apply(pd.to_numeric, errors="coerce")

    returns = (df_prices - df_prices.shift(-1)) / df_prices.shift(-1)
    returns = returns.dropna()

    latest_prices = df_prices.iloc[0]
    weighted_returns = returns.multiply(latest_prices, axis=1).multiply(
        df_quantities, axis=1
    )
    portfolio_returns = weighted_returns.sum(axis=1).iloc[:nb_returns]

    var = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)

    return var, portfolio_returns
