"""
Configurações do sistema
"""
import os
from datetime import datetime

# Configurações gerais
CONFIG = {
    # Arquivos
    "JSON_FILE": "sintomas.json",
    "HIST_FILE": "historico_diagnosticos.json",
    "PACIENTES_FILE": "pacientes.json",
    "LOG_FILE": "diagnostico.log",
    
    # Limites
    "LIMITE_RESULTADOS": 50,
    "PORCENTAGEM_MINIMA": 5.0,
    "MAX_HIST_ITENS": 500,
    "MAX_PACIENTES": 1000,
    
    # Cache
    "CACHE_TTL": 300,  # 5 minutos
    "CACHE_MAX_SIZE": 1000,
    
    # Exportação
    "EXPORT_AUTOR": "Sistema de Diagnóstico Médico",
    "EXPORT_TITULO": "Relatório de Diagnóstico",
    
    # Interface
    "WINDOW_SIZE": "1400x900",
    "SINTOMAS_PER_PAGE": 100,
    
    # Segurança
    "BACKUP_DAYS_TO_KEEP": 30,
    "MAX_FILE_SIZE_MB": 10,
    
    # Idioma
    "IDIOMA": "pt_BR",
    
    # Temas
    "TEMA": {
        "cores": {
            "alta": "#ff6b6b",
            "media": "#ffd166",
            "baixa": "#06d6a0",
            "fisico": "#4cc9f0",
            "psicologico": "#f72585",
            "selecionado": "#caf0f8",
            "background": "#f8f9fa"
        }
    },
    
    # Pacientes
    "PACIENTE": {
        "campos_obrigatorios": ["nome", "data_nascimento", "sexo", "cpf"],
        "sexos_disponiveis": ["Masculino", "Feminino", "Outro"],
        "estados": [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
            "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", 
            "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]
    }
}

class ConfigManager:
    """Gerenciador de configurações"""
    
    @staticmethod
    def get_path(*args):
        """Retorna caminho absoluto"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, *args)
    
    @staticmethod
    def ensure_directories():
        """Cria diretórios necessários"""
        dirs = ["backups", "logs", "exports"]
        for dir_name in dirs:
            path = ConfigManager.get_path(dir_name)
            os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def get_export_path(filename: str) -> str:
        """Retorna caminho para exportação"""
        export_dir = ConfigManager.get_path("exports")
        os.makedirs(export_dir, exist_ok=True)
        return os.path.join(export_dir, filename)