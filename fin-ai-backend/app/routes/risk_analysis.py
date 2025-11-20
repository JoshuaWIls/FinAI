from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.risk_service import generate_risk_profile
from app.models import RiskProfile
from app.services.auth_service import get_current_user
from app.services.mongo_service import get_user_by_id_str

router = APIRouter(tags=["risk"])

@router.get("/{ticker}", response_model=RiskProfile)
async def get_risk(ticker: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Get risk profile for a ticker for the authenticated user.
    """
    try:
        user = await get_user_by_id_str(str(current_user["_id"]))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        salary = user.get("currentSalary")
        if salary is None:
            raise HTTPException(status_code=400, detail="User salary (CTC) not set. Please update profile.")
        
        result = await generate_risk_profile(ticker, float(salary))
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] /risk/{ticker}: {e}")
        raise HTTPException(status_code=500, detail="Risk analysis failed")
