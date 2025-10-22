import pandas as pd
import re
from typing import List, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.schemas import Evidence
from logger import logger
from app.services.formatter import format_currency_brl, parse_date_variations


class PayrollService:
    def __init__(self, payroll_data):
        self.data = payroll_data.df

    def search_employee(self, name: str) -> pd.DataFrame:
        """Busca funcionário por nome (case insensitive, parcial)"""
        if not name:
            return pd.DataFrame()

        name_clean = name.lower().strip()
        return self.data[self.data['name'].str.lower().str.contains(name_clean, na=False)]

    def search_by_competency(self, competency: str, employee_name: Optional[str] = None) -> pd.DataFrame:
        """Busca por competência com suporte a variações de formato"""
        df = self.data

        if employee_name:
            df = self.search_employee(employee_name)
            if df.empty:
                return df

        # Parse de variações de data
        parsed_date = parse_date_variations(competency)
        if parsed_date:
            year_month = parsed_date.strftime("%Y-%m")
            return df[df['competency'] == year_month]

        # Tenta diretamente
        if competency in df['competency'].values:
            return df[df['competency'] == competency]

        return pd.DataFrame()

    def get_employee_records(self, employee_name: str) -> pd.DataFrame:
        """Retorna todos os registros de um funcionário"""
        return self.search_employee(employee_name)

    def get_quarter_records(self, employee_name: str, year: int, quarter: int) -> pd.DataFrame:
        """Retorna registros de um trimestre específico"""
        df = self.search_employee(employee_name)
        if df.empty:
            return df

        # Define os meses do trimestre
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3

        quarters = [f"{year}-{str(month).zfill(2)}" for month in range(start_month, end_month + 1)]
        return df[df['competency'].isin(quarters)]

    def get_year_records(self, employee_name: str, year: int) -> pd.DataFrame:
        """Retorna registros de um ano específico"""
        df = self.search_employee(employee_name)
        return df[df['competency'].str.startswith(str(year))]

    def find_max_bonus(self, employee_name: str) -> pd.DataFrame:
        """Encontra o maior bônus de um funcionário"""
        df = self.search_employee(employee_name)
        if df.empty:
            return df

        max_bonus = df['bonus'].max()
        return df[df['bonus'] == max_bonus]

    def to_evidence(self, df: pd.DataFrame) -> List[Evidence]:
        """Converte DataFrame para lista de Evidence"""
        evidence_list = []

        for _, row in df.iterrows():
            evidence = Evidence(
                employee_id=row['employee_id'],
                name=row['name'],
                competency=row['competency'],
                net_pay=row['net_pay'],
                payment_date=row['payment_date'],
                base_salary=row['base_salary'],
                bonus=row['bonus'],
                deductions_inss=row['deductions_inss'],
                deductions_irrf=row['deductions_irrf']
            )
            evidence_list.append(evidence)

        return evidence_list