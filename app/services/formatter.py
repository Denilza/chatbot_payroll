import re
from datetime import datetime
from typing import Optional


def format_currency_brl(value: float) -> str:
    """Formata valor em moeda brasileira"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_date_variations(date_str: str) -> Optional[datetime]:
    """Parse de variações de datas em português"""
    if not date_str:
        return None

    date_str = date_str.lower().strip()

    # Mapeamento de meses
    month_map = {
        'jan': 1, 'janeiro': 1,
        'fev': 2, 'fevereiro': 2,
        'mar': 3, 'março': 3,
        'abr': 4, 'abril': 4,
        'mai': 5, 'maio': 5,
        'jun': 6, 'junho': 6,
        'jul': 7, 'julho': 7,
        'ago': 8, 'agosto': 8,
        'set': 9, 'setembro': 9,
        'out': 10, 'outubro': 10,
        'nov': 11, 'novembro': 11,
        'dez': 12, 'dezembro': 12
    }

    try:
        # Formato YYYY-MM
        if re.match(r'^\d{4}-\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m')

        # Formato mes/ano ou mes-ano
        match = re.match(r'(\w+)[/\-](\d{2,4})', date_str)
        if match:
            month_str, year_str = match.groups()
            month = month_map.get(month_str)
            year = int(year_str) if len(year_str) == 4 else 2000 + int(year_str)

            if month and year:
                return datetime(year, month, 1)

        # Nome do mês por extenso
        for month_name, month_num in month_map.items():
            if month_name in date_str and any(char.isdigit() for char in date_str):
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = int(year_match.group())
                    return datetime(year, month_num, 1)

    except Exception:
        return None

    return None


def format_payment_date(date_str: str) -> str:
    """Formata data de pagamento para dd/mm/aaaa"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str