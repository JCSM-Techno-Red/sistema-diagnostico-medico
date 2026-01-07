"""
Utilitários do sistema
"""
import json
import logging
import shutil
import hashlib
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Any
from collections import OrderedDict
from functools import lru_cache
from copy import deepcopy
from threading import RLock
from time import time

def setup_logging(log_file: str = None, level=logging.INFO):
    """Configura sistema de logging"""
    logger = logging.getLogger('diagnostico')
    
    if logger.hasHandlers():
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Erro ao configurar log em arquivo: {e}")
    
    logger.setLevel(level)
    return logger

class BackupManager:
    """Gerenciador de backups"""
    
    def __init__(self, backup_dir: str, days_to_keep: int = 30):
        self.backup_dir = Path(backup_dir)
        self.days_to_keep = days_to_keep
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, source_file: str, description: str = "") -> str:
        """Cria backup de um arquivo"""
        try:
            source = Path(source_file)
            if not source.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.stem}_{timestamp}{source.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(source, backup_path)
            self.clean_old_backups()
            
            return str(backup_path)
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return None
    
    def clean_old_backups(self):
        """Remove backups antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.days_to_keep)
            
            for backup_file in self.backup_dir.glob("*"):
                if backup_file.is_file():
                    try:
                        match = re.search(r"_(\d{8})_", backup_file.name)
                        if match:
                            file_date = datetime.strptime(match.group(1), "%Y%m%d")
                            if file_date < cutoff_date:
                                backup_file.unlink()
                    except Exception:
                        pass
        except Exception as e:
            print(f"Erro ao limpar backups: {e}")

class Validator:
    """Validador de dados"""
    
    @staticmethod
    def validate_json_structure(data: Dict) -> Tuple[bool, List[str]]:
        """Valida estrutura do JSON"""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("JSON deve ser um objeto")
            return False, errors
        
        if "doencas" not in data:
            errors.append("JSON deve conter chave 'doencas'")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 100) -> str:
        """Sanitiza entrada de texto"""
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF"""
        cpf = re.sub(r'[^\d]', '', cpf)
        
        if len(cpf) != 11:
            return False
        
        # Verificar dígitos repetidos
        if cpf == cpf[0] * 11:
            return False
        
        # Validar primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cpf[9]):
            return False
        
        # Validar segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return digito2 == int(cpf[10])

def formatar_data(data_str: str, formato: str = "%d/%m/%Y %H:%M") -> str:
    """Formata data para exibição"""
    try:
        if "T" in data_str:
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        else:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(data_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return data_str
        return dt.strftime(formato)
    except Exception:
        return data_str

def porcentagem_cor(pct: float) -> str:
    """Determina cor baseada na porcentagem"""
    if pct >= 75:
        return "alta"
    elif pct >= 40:
        return "media"
    else:
        return "baixa"

def calcular_idade(data_nascimento: str) -> int:
    """Calcula idade a partir da data de nascimento"""
    try:
        nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y")
        hoje = datetime.now()
        
        idade = hoje.year - nascimento.year
        
        # Ajustar se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
            idade -= 1
        
        return idade
    except:
        return 0