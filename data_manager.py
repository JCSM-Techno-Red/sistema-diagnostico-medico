"""
Gerenciador de dados com cache e validação
"""
import json
import os
import time
import threading
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from config import CONFIG, ConfigManager
from utils import setup_logging, Validator, BackupManager

logger = setup_logging(CONFIG["LOG_FILE"])

@dataclass
class CacheEntry:
    """Entrada de cache"""
    data: Any
    timestamp: float
    hits: int = 0

class DataManager:
    """Gerenciador de dados com cache LRU"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self._load_config()
        
        # Inicializar backup manager
        backup_dir = ConfigManager.get_path("backups")
        self.backup_manager = BackupManager(backup_dir, CONFIG["BACKUP_DAYS_TO_KEEP"])
    
    def _load_config(self):
        """Carrega configurações"""
        self.cache_ttl = CONFIG.get("CACHE_TTL", 300)
        self.cache_max_size = CONFIG.get("CACHE_MAX_SIZE", 1000)
        self.json_file = CONFIG["JSON_FILE"]
        self.hist_file = CONFIG["HIST_FILE"]
    
    def carregar_banco(self, force_reload: bool = False) -> Tuple[bool, List[Dict], List[str]]:
        """Carrega banco de dados com cache e validação"""
        cache_key = "banco_dados"
        
        # Verificar cache
        if not force_reload:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                logger.info("Usando dados do cache")
                return True, cached, []
        
        try:
            # Verificar se arquivo existe
            if not os.path.exists(self.json_file):
                error_msg = f"Arquivo {self.json_file} não encontrado"
                logger.error(error_msg)
                return False, [], [error_msg]
            
            # Criar backup antes de carregar
            backup_path = self.backup_manager.create_backup(
                self.json_file, 
                "pre_carregamento"
            )
            
            if backup_path:
                logger.info(f"Backup criado: {backup_path}")
            
            # Carregar e validar JSON
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar estrutura
            is_valid, errors = Validator.validate_json_structure(data)
            
            if not is_valid:
                logger.error(f"Erros na validação: {errors}")
                return False, [], errors
            
            # Processar dados
            doencas_processadas = self._processar_dados(data)
            
            # Salvar no cache
            self._save_to_cache(cache_key, doencas_processadas)
            
            logger.info(f"Banco carregado: {len(doencas_processadas)} doenças")
            return True, doencas_processadas, []
            
        except FileNotFoundError:
            error_msg = f"Arquivo {self.json_file} não encontrado"
            logger.error(error_msg)
            return False, [], [error_msg]
        except json.JSONDecodeError as e:
            error_msg = f"Erro na formatação JSON: {str(e)}"
            logger.error(error_msg)
            return False, [], [error_msg]
        except Exception as e:
            error_msg = f"Erro ao carregar banco: {str(e)}"
            logger.error(error_msg)
            return False, [], [error_msg]
    
    def _processar_dados(self, data: Dict) -> List[Dict]:
        """Processa dados do JSON para formato interno"""
        doencas = []
        
        # Processar doenças físicas
        if "doencas" in data and "fisicas" in data["doencas"]:
            for doenca in data["doencas"]["fisicas"]:
                if isinstance(doenca, dict):
                    doenca["tipo"] = "físico"
                    doenca["categoria"] = "fisica"
                    self._normalizar_doenca(doenca)
                    doencas.append(doenca)
        
        # Processar doenças mentais
        if "doencas" in data and "mentais" in data["doencas"]:
            for doenca in data["doencas"]["mentais"]:
                if isinstance(doenca, dict):
                    doenca["tipo"] = "psicológico"
                    doenca["categoria"] = "mental"
                    self._normalizar_doenca(doenca)
                    doencas.append(doenca)
        
        return doencas
    
    def _normalizar_doenca(self, doenca: Dict):
        """Normaliza estrutura de uma doença"""
        # Garantir campos obrigatórios
        doenca.setdefault("descricao", "")
        doenca.setdefault("tratamento", "")
        doenca.setdefault("severidade", "moderada")
        doenca.setdefault("condicoes", {})
        doenca.setdefault("sintomas", [])
        
        # Normalizar sintomas
        sintomas_normalizados = []
        for sintoma in doenca["sintomas"]:
            if isinstance(sintoma, dict):
                sintoma.setdefault("peso", 1.0)
                sintoma.setdefault("tipo", doenca["tipo"])
                sintomas_normalizados.append(sintoma)
            else:
                sintomas_normalizados.append({
                    "s": str(sintoma),
                    "peso": 1.0,
                    "tipo": doenca["tipo"]
                })
        
        doenca["sintomas"] = sintomas_normalizados
        
        # Normalizar condições
        condicoes = doenca["condicoes"]
        condicoes.setdefault("min_sintomas", 0)
        condicoes.setdefault("sintomas_obrigatorios", [])
    
    def carregar_historico(self, limit: int = 100) -> List[Dict]:
        """Carrega histórico de diagnósticos"""
        try:
            if not os.path.exists(self.hist_file):
                return []
            
            with open(self.hist_file, 'r', encoding='utf-8') as f:
                historico = json.load(f)
            
            # Ordenar por data (mais recente primeiro)
            historico.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return historico[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            return []
    
    def salvar_historico(self, entrada: Dict) -> bool:
        """Salva entrada no histórico"""
        try:
            # Carregar histórico existente
            historico = self.carregar_historico(CONFIG["MAX_HIST_ITENS"] * 2)
            
            # Adicionar nova entrada
            entrada.setdefault("id", str(int(time.time())))
            
            historico.insert(0, entrada)
            
            # Limitar tamanho
            if len(historico) > CONFIG["MAX_HIST_ITENS"]:
                historico = historico[:CONFIG["MAX_HIST_ITENS"]]
            
            # Criar backup antes de salvar
            self.backup_manager.create_backup(self.hist_file, "pre_salvamento")
            
            # Salvar
            with open(self.hist_file, 'w', encoding='utf-8') as f:
                json.dump(historico, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Histórico salvo: {entrada.get('paciente', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            return False
    
    def _get_from_cache(self, key: str) -> Any:
        """Obtém dado do cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Verificar expiração
                if time.time() - entry.timestamp < self.cache_ttl:
                    entry.hits += 1
                    return entry.data
                else:
                    # Remover entrada expirada
                    del self.cache[key]
            
            return None
    
    def _save_to_cache(self, key: str, data: Any):
        """Salva dado no cache"""
        with self.lock:
            # Limitar tamanho do cache (LRU)
            if len(self.cache) >= self.cache_max_size:
                # Remover entrada menos usada
                lru_key = min(
                    self.cache.keys(), 
                    key=lambda k: self.cache[k].hits
                )
                del self.cache[lru_key]
            
            self.cache[key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                hits=1
            )
    
    def clear_cache(self):
        """Limpa cache"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache limpo")
    
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        with self.lock:
            total_size = len(self.cache)
            total_hits = sum(entry.hits for entry in self.cache.values())
            avg_hits = total_hits / total_size if total_size > 0 else 0
            
            return {
                "total_entradas": total_size,
                "total_hits": total_hits,
                "avg_hits": round(avg_hits, 2),
                "ttl": self.cache_ttl
            }