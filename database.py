"""
Gerenciamento de dados do sistema
"""
import json
import os
import threading
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from config import CONFIG, ConfigManager
from models import Paciente, Diagnostico, Doenca
from utils import setup_logging, BackupManager, Validator

logger = setup_logging(CONFIG["LOG_FILE"])

class Database:
    """Gerenciador de banco de dados"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Verificar se já foi inicializado
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        with self._lock:
            if hasattr(self, '_initialized') and self._initialized:
                return
            
            self.pacientes_file = ConfigManager.get_path(CONFIG["PACIENTES_FILE"])
            self.historico_file = ConfigManager.get_path(CONFIG["HIST_FILE"])
            self.sintomas_file = ConfigManager.get_path(CONFIG["JSON_FILE"])
            
            self.pacientes: Dict[str, Paciente] = {}
            self.historico: List[Diagnostico] = []
            self.doencas: List[Doenca] = []
            
            self.backup_manager = BackupManager(
                ConfigManager.get_path("backups"),
                CONFIG["BACKUP_DAYS_TO_KEEP"]
            )
            
            self._carregar_dados()
            self._initialized = True
    
    def _carregar_dados(self):
        """Carrega todos os dados do sistema"""
        self._carregar_pacientes()
        self._carregar_historico()
        self._carregar_doencas()
    
    def _carregar_pacientes(self):
        """Carrega pacientes do arquivo"""
        try:
            if os.path.exists(self.pacientes_file):
                with open(self.pacientes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.pacientes = {
                    pid: Paciente.from_dict(paciente_data)
                    for pid, paciente_data in data.items()
                }
                logger.info(f"Pacientes carregados: {len(self.pacientes)}")
            else:
                self.pacientes = {}
                logger.info("Arquivo de pacientes não encontrado. Criando novo.")
        except Exception as e:
            logger.error(f"Erro ao carregar pacientes: {e}")
            self.pacientes = {}
    
    def _carregar_historico(self):
        """Carrega histórico de diagnósticos"""
        try:
            if os.path.exists(self.historico_file):
                with open(self.historico_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.historico = []
                for d in data:
                    try:
                        diagnostico = Diagnostico(
                            id=d.get('id', str(uuid.uuid4())),
                            paciente_id=d.get('paciente_id', ''),
                            paciente_nome=d.get('paciente_nome', ''),
                            sintomas=d.get('sintomas', []),
                            data_hora=d.get('data_hora', ''),
                            resultados=d.get('resultados', []),
                            top_resultado=d.get('top_resultado', ''),
                            top_porcentagem=d.get('top_porcentagem', 0.0)
                        )
                        self.historico.append(diagnostico)
                    except Exception as e:
                        logger.error(f"Erro ao carregar diagnóstico: {e}")
                
                logger.info(f"Histórico carregado: {len(self.historico)} registros")
            else:
                self.historico = []
                logger.info("Arquivo de histórico não encontrado. Criando novo.")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            self.historico = []
    
    def _carregar_doencas(self):
        """Carrega doenças do arquivo JSON"""
        try:
            if not os.path.exists(self.sintomas_file):
                logger.error(f"Arquivo {self.sintomas_file} não encontrado")
                return
            
            with open(self.sintomas_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.doencas = []
            
            # Processar doenças físicas
            if "doencas" in data and "fisicas" in data["doencas"]:
                for doenca_data in data["doencas"]["fisicas"]:
                    try:
                        doenca_data["tipo"] = "físico"
                        doenca_data["categoria"] = "fisica"
                        self.doencas.append(Doenca.from_dict(doenca_data))
                    except Exception as e:
                        logger.error(f"Erro ao carregar doença física: {e}")
            
            # Processar doenças mentais
            if "doencas" in data and "mentais" in data["doencas"]:
                for doenca_data in data["doencas"]["mentais"]:
                    try:
                        doenca_data["tipo"] = "psicológico"
                        doenca_data["categoria"] = "mental"
                        self.doencas.append(Doenca.from_dict(doenca_data))
                    except Exception as e:
                        logger.error(f"Erro ao carregar doença mental: {e}")
            
            logger.info(f"Doenças carregadas: {len(self.doencas)}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar doenças: {e}")
            self.doencas = []
    
    # Métodos para pacientes
    def salvar_pacientes(self) -> bool:
        """Salva pacientes no arquivo"""
        try:
            self.backup_manager.create_backup(self.pacientes_file, "pacientes")
            
            data = {
                pid: paciente.to_dict()
                for pid, paciente in self.pacientes.items()
            }
            
            with open(self.pacientes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar pacientes: {e}")
            return False
    
    def adicionar_paciente(self, paciente: Paciente) -> bool:
        """Adiciona novo paciente"""
        try:
            # Verificar se CPF já existe (se CPF não estiver vazio)
            if paciente.cpf:
                for existing in self.pacientes.values():
                    if existing.cpf == paciente.cpf and existing.ativo:
                        raise ValueError(f"Paciente com CPF {paciente.cpf} já cadastrado")
            
            self.pacientes[paciente.id] = paciente
            return self.salvar_pacientes()
        except Exception as e:
            logger.error(f"Erro ao adicionar paciente: {e}")
            raise
    
    def buscar_pacientes(self, **filtros) -> List[Paciente]:
        """Busca pacientes por filtros"""
        resultados = []
        
        for paciente in self.pacientes.values():
            if not paciente.ativo:
                continue
            
            match = True
            for campo, valor in filtros.items():
                if hasattr(paciente, campo):
                    attr_valor = getattr(paciente, campo)
                    if valor.lower() not in str(attr_valor).lower():
                        match = False
                        break
            
            if match:
                resultados.append(paciente)
        
        return resultados
    
    def obter_paciente(self, paciente_id: str) -> Optional[Paciente]:
        """Obtém paciente pelo ID"""
        return self.pacientes.get(paciente_id)
    
    def atualizar_paciente(self, paciente_id: str, **atualizacoes) -> bool:
        """Atualiza dados do paciente"""
        try:
            if paciente_id not in self.pacientes:
                return False
            
            paciente = self.pacientes[paciente_id]
            
            for campo, valor in atualizacoes.items():
                if hasattr(paciente, campo):
                    setattr(paciente, campo, valor)
            
            paciente.data_atualizacao = datetime.now().isoformat()
            return self.salvar_pacientes()
        except Exception as e:
            logger.error(f"Erro ao atualizar paciente: {e}")
            return False
    
    # Métodos para histórico
    def salvar_historico(self) -> bool:
        """Salva histórico no arquivo"""
        try:
            self.backup_manager.create_backup(self.historico_file, "historico")
            
            data = [
                {
                    'id': d.id,
                    'paciente_id': d.paciente_id,
                    'paciente_nome': d.paciente_nome,
                    'sintomas': d.sintomas,
                    'data_hora': d.data_hora,
                    'resultados': d.resultados,
                    'top_resultado': d.top_resultado,
                    'top_porcentagem': d.top_porcentagem
                } for d in self.historico
            ]
            
            with open(self.historico_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            return False
    
    def adicionar_diagnostico(self, diagnostico: Diagnostico) -> bool:
        """Adiciona novo diagnóstico ao histórico"""
        try:
            self.historico.insert(0, diagnostico)
            
            # Limitar tamanho
            if len(self.historico) > CONFIG["MAX_HIST_ITENS"]:
                self.historico = self.historico[:CONFIG["MAX_HIST_ITENS"]]
            
            return self.salvar_historico()
        except Exception as e:
            logger.error(f"Erro ao adicionar diagnóstico: {e}")
            return False
    
    def obter_historico_paciente(self, paciente_id: str) -> List[Diagnostico]:
        """Obtém histórico de um paciente"""
        return [
            d for d in self.historico
            if d.paciente_id == paciente_id
        ]
    
    # Métodos para doenças
    def obter_doencas(self) -> List[Doenca]:
        """Retorna todas as doenças"""
        return self.doencas
    
    def obter_sintomas_unicos(self) -> List[str]:
        """Retorna todos os sintomas únicos"""
        sintomas_set = set()
        
        for doenca in self.doencas:
            for sintoma in doenca.sintomas:
                if isinstance(sintoma, dict):
                    sintomas_set.add(sintoma["s"])
                else:
                    sintomas_set.add(str(sintoma))
        
        return sorted(sintomas_set)
    
    def get_estatisticas(self) -> Dict:
        """Retorna estatísticas do sistema"""
        total_pacientes = len(self.pacientes)
        pacientes_ativos = sum(1 for p in self.pacientes.values() if p.ativo)
        pacientes_homens = sum(1 for p in self.pacientes.values() 
                              if p.ativo and p.sexo.lower() in ['m', 'masculino', 'homem'])
        
        return {
            'pacientes': {
                'total': total_pacientes,
                'ativos': pacientes_ativos,
                'inativos': total_pacientes - pacientes_ativos,
                'homens': pacientes_homens,
                'mulheres': pacientes_ativos - pacientes_homens
            },
            'diagnosticos': {
                'total': len(self.historico),
                'ultimo_mes': len([
                    d for d in self.historico
                    if self._dentro_do_ultimo_mes(d.data_hora)
                ])
            },
            'doencas': {
                'total': len(self.doencas),
                'fisicas': sum(1 for d in self.doencas if d.tipo == 'físico'),
                'psicologicas': sum(1 for d in self.doencas if d.tipo == 'psicológico')
            }
        }
    
    def _dentro_do_ultimo_mes(self, data_str: str) -> bool:
        """Verifica se data está dentro do último mês"""
        try:
            if "T" in data_str:
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            else:
                # Tentar diferentes formatos
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%Y"]:
                    try:
                        data = datetime.strptime(data_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False
            
            um_mes_atras = datetime.now() - timedelta(days=30)
            return data >= um_mes_atras
        except Exception:
            return False