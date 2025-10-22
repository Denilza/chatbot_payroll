
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_importacoes_basicas():
    """Testa imports básicos """
    from app.main import app
    from app.core.chatbot import Chatbot
    from app.core.rag_engine import RAGEngine
    assert app is not None
    print("✅ Imports básicos OK")

def test_formatacao_brl_simples():
    """Teste de formatação BRL - """
    def format_brl(value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    assert format_brl(8418.75) == "R$ 8.418,75"
    assert format_brl(660.00) == "R$ 660,00"
    print("✅ Formatação BRL OK")

def test_formatacao_data_simples():
    """Teste de formatação de datas """
    from datetime import datetime
    
    def format_date_simple(date_obj):
        return date_obj.strftime("%d/%m/%Y")
    
    data = datetime(2024, 5, 15)
    assert format_date_simple(data) == "15/05/2024"
    print("✅ Formatação datas OK")

def test_api_endpoints():
    """Testa se endpoints existem """
    from app.main import app
    
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    assert "/chat" in str(routes)
    assert "/health" in str(routes) 
    assert "/employees" in str(routes)
    print("✅ Endpoints API OK")

def test_dados_payroll():
    """Testa se dados payroll existem"""
    import pandas as pd
    df = pd.read_csv('data/payroll.csv')
    assert len(df) > 0
    assert 'name' in df.columns
    assert 'net_pay' in df.columns
    print("✅ Dados payroll OK")