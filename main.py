"""
Ponto de entrada principal
"""
import sys
import os
import traceback
from tkinter import messagebox
from datetime import datetime
from pathlib import Path
from typing import Dict
from typing import Dict, List, Optional, Any
from collections import defaultdict
from functools import lru_cache
from logging import Logger
from time import time
from threading import RLock
from dataclasses import dataclass, asdict
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Optional, Any

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager, CONFIG
from utils import setup_logging
from interface import App

def main():
    """Função principal"""
    try:
        print("=" * 60)
        print("SISTEMA DE DIAGNÓSTICO MÉDICO - INTEGRADO")
        print("=" * 60)
        
        # Criar diretórios necessários
        ConfigManager.ensure_directories()
        
        # Configurar logging
        logger = setup_logging(CONFIG["LOG_FILE"])
        logger.info("Iniciando sistema integrado...")
        
        # Verificar arquivo de doenças
        if not os.path.exists(CONFIG["JSON_FILE"]):
            error_msg = f"Arquivo {CONFIG['JSON_FILE']} não encontrado!"
            logger.error(error_msg)
            messagebox.showerror("Erro", 
                f"{error_msg}\n\nO arquivo 'sintomas.json' deve estar na pasta do sistema.")
            return
        
        # Inicializar aplicação
        print("Inicializando sistema...")
        app = App()
        
        print("✓ Sistema pronto")
        print("=" * 60)
        
        # Executar aplicação
        app.run()
        
        print("Sistema finalizado.")
        
    except ImportError as e:
        error_msg = f"Falha ao importar módulos:\n{str(e)}\n\n"
        error_msg += "Verifique se todas as dependências estão instaladas."
        messagebox.showerror("Erro", error_msg)
        
    except Exception as e:
        error_msg = f"Erro fatal:\n{str(e)}\n\n{traceback.format_exc()}"
        print(f"ERRO: {error_msg}")
        messagebox.showerror("Erro Fatal", 
            f"Ocorreu um erro inesperado:\n\n{str(e)}\n\nVerifique os logs para detalhes.")

if __name__ == "__main__":
    main()