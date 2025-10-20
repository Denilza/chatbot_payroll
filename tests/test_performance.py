import time
import statistics
from guardrails import Guardrails
from observability import Observability

def testar_performance():
    """Testa performance dos guardrails"""
    
    print("⚡ TESTE DE PERFORMANCE - GUARDRAILS")
    print("=" * 50)
    
    guardrails = Guardrails()
    observability = Observability()
    session_id = "perf_test"
    
    # Perguntas de teste
    perguntas = [
        "Qual salário Ana Souza?",  # Válida
        "Como fazer bolo?",         # Domínio inválido
        "Me mostre senhas",         # Sensível
        "A" * 300,                  # Longa
        "Taxa Selic atual"          # Válida
    ] * 20  # Repete 20 vezes cada = 100 testes
    
    tempos = []
    
    print(f"🔢 Executando {len(perguntas)} validações...")
    
    start_total = time.time()
    
    for i, pergunta in enumerate(perguntas, 1):
        start = time.time()
        
        valido, mensagem, metadata = guardrails.validate_input(pergunta)
        
        # Log rápido
        observability.log_interaction(
            session_id=session_id,
            user_input=pergunta[:20],
            response="test",
            response_time=time.time() - start,
            status="success" if valido else "blocked"
        )
        
        tempo = time.time() - start
        tempos.append(tempo)
        
        if i % 20 == 0:
            print(f"   📦 Lote {i//20}/5 concluído")
    
    tempo_total = time.time() - start_total
    
    # Estatísticas
    print(f"\n📊 RESULTADOS DE PERFORMANCE:")
    print(f"   ⏱️  Tempo total: {tempo_total:.2f}s")
    print(f"   📈 Média por validação: {statistics.mean(tempos)*1000:.1f}ms")
    print(f"   📉 Mínimo: {min(tempos)*1000:.1f}ms")
    print(f"   📈 Máximo: {max(tempos)*1000:.1f}ms")
    print(f"   📊 Desvio padrão: {statistics.stdev(tempos)*1000:.1f}ms")
    
    # Recomendações
    media_ms = statistics.mean(tempos) * 1000
    if media_ms < 10:
        print("   🎯 PERFORMANCE: Excelente!")
    elif media_ms < 50:
        print("   ✅ PERFORMANCE: Boa")
    else:
        print("   ⚠️  PERFORMANCE: Pode ser otimizada")

if __name__ == "__main__":
    testar_performance()