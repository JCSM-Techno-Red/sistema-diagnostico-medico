"""
Sistema de gerenciamento de pacientes
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from config import CONFIG, ConfigManager
from utils import setup_logging, Validator, formatar_data

logger = setup_logging()

@dataclass
class Paciente:
    """Modelo de paciente"""
    id: str
    nome: str
    data_nascimento: str
    sexo: str
    telefone: str
    email: str
    cpf: str
    endereco: str
    cidade: str
    estado: str
    cep: str
    
    # Informações médicas
    alergias: List[str]
    medicamentos_uso: List[str]
    doencas_cronicas: List[str]
    cirurgias_previas: List[str]
    historico_familiar: Dict[str, str]
    observacoes: str
    
    # Metadados
    data_cadastro: str
    data_atualizacao: str
    ativo: bool
    
    @classmethod
    def criar_novo(cls, **kwargs):
        """Cria novo paciente com valores padrão"""
        now = datetime.now().isoformat()
        
        defaults = {
            'id': str(uuid.uuid4()),
            'alergias': [],
            'medicamentos_uso': [],
            'doencas_cronicas': [],
            'cirurgias_previas': [],
            'historico_familiar': {},
            'observacoes': '',
            'data_cadastro': now,
            'data_atualizacao': now,
            'ativo': True
        }
        
        defaults.update(kwargs)
        return cls(**defaults)

class PacienteManager:
    """Gerenciador de pacientes"""
    
    def __init__(self):
        self.pacientes_file = ConfigManager.get_path("pacientes.json")
        self.pacientes: Dict[str, Paciente] = {}
        self._carregar_pacientes()
    
    def _carregar_pacientes(self):
        """Carrega pacientes do arquivo"""
        try:
            if os.path.exists(self.pacientes_file):
                with open(self.pacientes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.pacientes = {
                    pid: Paciente(**paciente_data)
                    for pid, paciente_data in data.items()
                }
                logger.info(f"Pacientes carregados: {len(self.pacientes)}")
            else:
                self.pacientes = {}
                logger.info("Arquivo de pacientes não encontrado. Criando novo.")
                
        except Exception as e:
            logger.error(f"Erro ao carregar pacientes: {e}")
            self.pacientes = {}
    
    def _salvar_pacientes(self):
        """Salva pacientes no arquivo"""
        try:
            # Criar backup antes de salvar
            from utils import BackupManager
            backup_dir = ConfigManager.get_path("backups")
            backup_manager = BackupManager(backup_dir, CONFIG["BACKUP_DAYS_TO_KEEP"])
            backup_manager.create_backup(self.pacientes_file, "pre_salvamento_pacientes")
            
            # Converter para dicionário
            data = {
                pid: asdict(paciente)
                for pid, paciente in self.pacientes.items()
            }
            
            # Salvar
            with open(self.pacientes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Pacientes salvos: {len(self.pacientes)}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar pacientes: {e}")
            return False
    
    def cadastrar_paciente(self, **dados) -> Optional[Paciente]:
        """Cadastra novo paciente"""
        try:
            # Validar dados obrigatórios
            obrigatorios = ['nome', 'data_nascimento', 'sexo', 'cpf']
            for campo in obrigatorios:
                if not dados.get(campo):
                    raise ValueError(f"Campo obrigatório: {campo}")
            
            # Verificar se CPF já existe
            cpf = dados['cpf']
            for paciente in self.pacientes.values():
                if paciente.cpf == cpf and paciente.ativo:
                    raise ValueError(f"Paciente com CPF {cpf} já cadastrado")
            
            # Criar paciente
            paciente = Paciente.criar_novo(**dados)
            self.pacientes[paciente.id] = paciente
            
            # Salvar
            if self._salvar_pacientes():
                logger.info(f"Paciente cadastrado: {paciente.nome} ({paciente.id})")
                return paciente
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar paciente: {e}")
            raise
    
    def buscar_paciente(self, **filtros) -> List[Paciente]:
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
                raise ValueError(f"Paciente {paciente_id} não encontrado")
            
            paciente = self.pacientes[paciente_id]
            
            # Atualizar campos
            for campo, valor in atualizacoes.items():
                if hasattr(paciente, campo):
                    setattr(paciente, campo, valor)
            
            # Atualizar data de modificação
            paciente.data_atualizacao = datetime.now().isoformat()
            
            # Salvar
            return self._salvar_pacientes()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar paciente: {e}")
            return False
    
    def inativar_paciente(self, paciente_id: str) -> bool:
        """Inativa paciente (exclusão lógica)"""
        try:
            if paciente_id in self.pacientes:
                self.pacientes[paciente_id].ativo = False
                self.pacientes[paciente_id].data_atualizacao = datetime.now().isoformat()
                return self._salvar_pacientes()
            return False
        except Exception as e:
            logger.error(f"Erro ao inativar paciente: {e}")
            return False
    
    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas dos pacientes"""
        total = len(self.pacientes)
        ativos = sum(1 for p in self.pacientes.values() if p.ativo)
        homens = sum(1 for p in self.pacientes.values() if p.sexo.lower() in ['m', 'masculino'])
        mulheres = ativos - homens
        
        return {
            'total_pacientes': total,
            'ativos': ativos,
            'inativos': total - ativos,
            'homens': homens,
            'mulheres': mulheres,
            'com_alergias': sum(1 for p in self.pacientes.values() if p.alergias and p.ativo),
            'com_medicamentos': sum(1 for p in self.pacientes.values() if p.medicamentos_uso and p.ativo)
        }