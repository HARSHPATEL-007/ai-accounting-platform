from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal

class BlackScholesInput(BaseModel):
    stock_price: float = Field(..., gt=0, description="Current stock price (S)")
    strike_price: float = Field(..., gt=0, description="Exercise price (K)")
    time_to_expiry: float = Field(..., gt=0, description="Time to expiry in years (T)")
    risk_free_rate: float = Field(..., ge=0, le=1, description="Risk-free rate (r)")
    volatility: float = Field(..., gt=0, le=2, description="Annualized volatility (sigma)")
    dividend_yield: float = Field(default=0.0, ge=0, le=1, description="Dividend yield (q)")

class BlackScholesOutput(BaseModel):
    call_price: float
    put_price: float
    delta_call: float
    delta_put: float
    gamma: float
    theta_call: float
    theta_put: float
    vega: float
    rho_call: float
    rho_put: float

class ESOPValuationInput(BaseModel):
    grant_date: str
    number_of_options: int = Field(..., gt=0)
    exercise_price: float = Field(..., gt=0)
    fair_market_value: float = Field(..., gt=0)
    volatility: float = Field(..., gt=0, le=2)
    time_to_expiry_years: float = Field(..., gt=0)
    risk_free_rate: float = Field(default=0.07, ge=0, le=1)
    vesting_schedule: list = Field(default_factory=list)

class ESOPValuationOutput(BaseModel):
    total_value: float
    per_option_value: float
    black_scholes_inputs: BlackScholesInput
    black_scholes_outputs: BlackScholesOutput
    dilution_impact_percent: Optional[float] = None

class TransferPricingInput(BaseModel):
    method: Literal["cup", "tnmm", "rpm", "cps", "profit_split"]
    tested_party: str
    comparable_companies: list
    financial_data: dict
    adjustment_factors: Optional[dict] = None

class TransferPricingOutput(BaseModel):
    arm_length_range: tuple
    median: float
    method_used: str
    comparables_count: int
    adjustment_applied: bool
