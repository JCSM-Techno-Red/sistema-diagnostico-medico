import json
import os
from config import ConfigManager

# Verificar arquivo de pacientes
pacientes_file = ConfigManager.get_path("pacientes.json")

print(f"Arquivo de pacientes: {pacientes_file}")
print(f"Existe: {os.path.exists(pacientes_file)}")

if os.path.exists(pacientes_file):
    with open(pacientes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\nTotal de pacientes no arquivo: {len(data)}")
    print("\nLista de pacientes:")
    for i, (pid, paciente) in enumerate(data.items(), 1):
        print(f"{i}. {paciente.get('nome', 'Sem nome')} (ID: {pid[:8]}...)")
        print(f"   CPF: {paciente.get('cpf', 'N/A')}")
        print(f"   Ativo: {paciente.get('ativo', True)}")
        print()
else:
    print("Arquivo de pacientes não encontrado.")