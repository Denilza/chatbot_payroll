import pandas as pd
from typing import List, Optional
from pydantic import BaseModel

class PayrollRecord(BaseModel):
    employee_id: str
    name: str
    competency: str
    base_salary: float
    bonus: float
    benefits_vt_vr: float
    other_earnings: float
    deductions_inss: float
    deductions_irrf: float
    other_deductions: float
    net_pay: float
    payment_date: str

class PayrollData:
    def __init__(self, file_path: str):
        self.df = pd.read_csv(file_path)
        self._validate_data()
    
    def _validate_data(self):
        """Valida estrutura básica do dataset"""
        required_columns = [
            'employee_id', 'name', 'competency', 'base_salary', 'bonus',
            'benefits_vt_vr', 'other_earnings', 'deductions_inss', 
            'deductions_irrf', 'other_deductions', 'net_pay', 'payment_date'
        ]
        
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"Coluna obrigatória faltando: {col}")