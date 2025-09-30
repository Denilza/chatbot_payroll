import os
import pandas as pd

def create_payroll_data():
    """Cria o dataset de folha de pagamento"""
    
    data = {
        'employee_id': ['E001', 'E001', 'E001', 'E001', 'E001', 'E001',
                       'E002', 'E002', 'E002', 'E002', 'E002', 'E002'],
        'name': ['Ana Souza', 'Ana Souza', 'Ana Souza', 'Ana Souza', 'Ana Souza', 'Ana Souza',
                'Bruno Lima', 'Bruno Lima', 'Bruno Lima', 'Bruno Lima', 'Bruno Lima', 'Bruno Lima'],
        'competency': ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06',
                      '2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06'],
        'base_salary': [8000, 8000, 8000, 8000, 8000, 8000,
                       6000, 6000, 6000, 6000, 6000, 6000],
        'bonus': [500, 0, 800, 0, 1200, 300,
                 500, 0, 800, 0, 1200, 300],
        'benefits_vt_vr': [600, 600, 650, 650, 650, 650,
                          600, 600, 650, 650, 650, 650],
        'other_earnings': [0, 200, 0, 300, 0, 0,
                         0, 200, 0, 300, 0, 0],
        'deductions_inss': [880.0, 880.0, 880.0, 880.0, 880.0, 880.0,
                          660.0, 660.0, 660.0, 660.0, 660.0, 660.0],
        'deductions_irrf': [495.0, 472.5, 521.25, 483.75, 551.25, 483.75,
                          345.0, 322.5, 371.25, 333.75, 401.25, 333.75],
        'other_deductions': [0, 0, 0, 0, 0, 0,
                           0, 0, 0, 200, 0, 0],
        'net_pay': [7725.0, 7447.5, 8048.75, 7586.25, 8418.75, 7586.25,
                   6095.0, 5817.5, 6418.75, 5756.25, 6788.75, 5956.25],
        'payment_date': ['2025-01-28', '2025-02-28', '2025-03-28', '2025-04-28', '2025-05-28', '2025-06-28',
                        '2025-01-28', '2025-02-28', '2025-03-28', '2025-04-28', '2025-05-28', '2025-06-28']
    }
    
    df = pd.DataFrame(data)
    
    # Cria diretório se não existir
    os.makedirs('data', exist_ok=True)
    
    # Salva arquivo
    df.to_csv('data/payroll.csv', index=False)
    print("Dataset criado com sucesso em data/payroll.csv")
    print(f"Total de registros: {len(df)}")

if __name__ == "__main__":
    create_payroll_data()