from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from bson import ObjectId
from enum import Enum
import datetime

class PyObjectId(str):
    """Custom Pydantic-compatible ObjectId that works with Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
        raise ValueError("Invalid ObjectId")


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRegister(UserCreate):
    dateOfBirth: datetime.date
    occupation: str
    currentSalary: float
    
    model_config = ConfigDict(populate_by_name=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    name: Optional[str] = None
    hashed_password: str
    dateOfBirth: Optional[datetime.date] = None
    occupation: Optional[str] = None
    currentSalary: Optional[float] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class SentimentResult(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"


class NewsItemOut(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    link: Optional[str] = None
    sentiment: str
    timestamp: str


class SentimentResponse(BaseModel):
    symbol: Optional[str] = None
    text: str
    sentiment: str 
    score: Optional[float] = None


class SuggestedStock(BaseModel):
    ticker: str
    name: Optional[str] = None
    price: Optional[float] = None
    beta: Optional[float] = None


class RiskProfile(BaseModel):
    ticker: str
    price: Optional[float] = None
    volatility: float
    beta: Optional[float] = None
    user_salary: float
    risk_score: float
    risk_level: str
    suggestion_message: str
    suggested_stocks: List[SuggestedStock] = []