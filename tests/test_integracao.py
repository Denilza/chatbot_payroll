
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.getcwd())

def testar_importacoes():
    """Testa se todas as importações funcionam"""
    
    print("🔍 TESTANDO IMPORTAÇÕES DO SISTEMA")
    print("=" * 50)
    
    modulos = [
        ("guardrails.Guardrails", "from guardrails import Guardrails"),
        ("observability.Observability", "from observability import Observability"), 
        ("logger", "from logger import logger"),
        ("streamlit", "import streamlit as st")
    ]
    
    for modulo_name, import_code in modulos:
        try:
            exec(import_code)
            print(f"✅ {modulo_name:30} - OK")
        except Exception as e:
            print(f"❌ {modulo_name:30} - ERRO: {e}")
    
    print("\n🎯 TESTANDO FUNCIONALIDADES:")
    
    # Testar guardrails
    try:
        from guardrails import Guardrails
        guardrails = Guardrails()
        print("✅ Guardrails - Instância criada")
        
        # Teste rápido
        valido, msg, meta = guardrails.validate_input("Qual salário da Ana?")
        print(f"✅ Guardrails - Validação: {valido}")
        
    except Exception as e:
        print(f"❌ Guardrails - Erro: {e}")
    
    # Testar observability
    try:
        from observability import Observability
        observability = Observability()
        print("✅ Observability - Instância criada")
        
        # Teste rápido
        id = observability.log_interaction(
            session_id="test",
            user_input="teste",
            response="teste", 
            response_time=0.1,
            status="success"
        )
        print(f"✅ Observability - Log criado: {id}")
        
    except Exception as e:
        print(f"❌ Observability - Erro: {e}")

if __name__ == "__main__":
    testar_importacoes()