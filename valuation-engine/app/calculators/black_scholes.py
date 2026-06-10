import numpy as np
from scipy.stats import norm
from app.models.valuation import BlackScholesInput, BlackScholesOutput
from app.core.logging import logger

def calculate_black_scholes(inputs: BlackScholesInput) -> BlackScholesOutput:
    """Calculate Black-Scholes option pricing model."""
    S = inputs.stock_price
    K = inputs.strike_price
    T = inputs.time_to_expiry
    r = inputs.risk_free_rate
    sigma = inputs.volatility
    q = inputs.dividend_yield

    logger.info("calculating_black_scholes", S=S, K=K, T=T, r=r, sigma=sigma)

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)
    n_neg_d1 = norm.cdf(-d1)
    n_neg_d2 = norm.cdf(-d2)

    call_price = S * np.exp(-q * T) * nd1 - K * np.exp(-r * T) * nd2
    put_price = K * np.exp(-r * T) * n_neg_d2 - S * np.exp(-q * T) * n_neg_d1

    delta_call = np.exp(-q * T) * nd1
    delta_put = -np.exp(-q * T) * n_neg_d1
    gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta_call = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                  - r * K * np.exp(-r * T) * nd2 + q * S * np.exp(-q * T) * nd1)
    theta_put = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * n_neg_d2 - q * S * np.exp(-q * T) * n_neg_d1)
    vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)
    rho_call = K * T * np.exp(-r * T) * nd2
    rho_put = -K * T * np.exp(-r * T) * n_neg_d2

    result = BlackScholesOutput(
        call_price=round(float(call_price), 4),
        put_price=round(float(put_price), 4),
        delta_call=round(float(delta_call), 6),
        delta_put=round(float(delta_put), 6),
        gamma=round(float(gamma), 6),
        theta_call=round(float(theta_call), 4),
        theta_put=round(float(theta_put), 4),
        vega=round(float(vega), 4),
        rho_call=round(float(rho_call), 4),
        rho_put=round(float(rho_put), 4),
    )

    logger.info("black_scholes_complete", call_price=result.call_price, put_price=result.put_price)
    return result
