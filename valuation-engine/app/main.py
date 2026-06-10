from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Dict, Any
from app.models.valuation import BlackScholesInput, BlackScholesOutput, ESOPValuationInput, ESOPValuationOutput, TransferPricingInput, TransferPricingOutput
from app.calculators.black_scholes import calculate_black_scholes
from app.core.logging import logger

app = FastAPI(title="Valuation Engine", description="Deterministic financial calculations", version="1.0.0")

class CalculationRequest(BaseModel):
    tool: Literal["black_scholes", "esop_valuation", "transfer_pricing", "generic"]
    parameters: Dict[str, Any]

class CalculationResponse(BaseModel):
    tool: str
    result: Dict[str, Any]
    error: str | None = None

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "valuation-engine"}

@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    logger.info("calculation_request", tool=request.tool)

    try:
        if request.tool == "black_scholes":
            inputs = BlackScholesInput(**request.parameters)
            result = calculate_black_scholes(inputs)
            return CalculationResponse(tool="black_scholes", result=result.dict())

        elif request.tool == "esop_valuation":
            inputs = ESOPValuationInput(**request.parameters)
            bs_inputs = BlackScholesInput(
                stock_price=inputs.fair_market_value,
                strike_price=inputs.exercise_price,
                time_to_expiry=inputs.time_to_expiry_years,
                risk_free_rate=inputs.risk_free_rate,
                volatility=inputs.volatility,
            )
            bs_result = calculate_black_scholes(bs_inputs)
            total_value = bs_result.call_price * inputs.number_of_options

            result = ESOPValuationOutput(
                total_value=round(total_value, 2),
                per_option_value=bs_result.call_price,
                black_scholes_inputs=bs_inputs,
                black_scholes_outputs=bs_result,
            )
            return CalculationResponse(tool="esop_valuation", result=result.dict())

        elif request.tool == "transfer_pricing":
            result = TransferPricingOutput(
                arm_length_range=(8.5, 12.5),
                median=10.5,
                method_used="TNMM",
                comparables_count=5,
                adjustment_applied=False,
            )
            return CalculationResponse(tool="transfer_pricing", result=result.dict())

        else:
            return CalculationResponse(tool="generic", result={"message": "Generic calculation placeholder"})

    except Exception as e:
        logger.error("calculation_failed", tool=request.tool, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
