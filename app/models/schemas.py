from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class Evidence(BaseModel):
    employee_id: str
    name: str
    competency: str
    net_pay: float
    payment_date: str
    base_salary: Optional[float] = None
    bonus: Optional[float] = None
    deductions_inss: Optional[float] = None
    deductions_irrf: Optional[float] = None

class ChatResponse(BaseModel):
    response: str
    evidence: List[Evidence]
    sources: List[str]
    conversation_id: Optional[str] = None

class PayrollQuery(BaseModel):
    employee_name: Optional[str] = None
    competency: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    query_type: str  # 'specific', 'aggregate', 'comparison'