"""
Modelos de dados do sistema
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid

@dataclass
class Paciente:
    """Modelo de paciente"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nome: str = ""
    data_nascimento: str = ""
    sexo: str = ""
    telefone: str = ""
    email: str = ""
    cpf: str = ""
    endereco: str = ""
    cidade: str = ""
    estado: str = ""
    cep: str = ""
    
    # Informações médicas
    alergias: List[str] = field(default_factory=list)
    medicamentos_uso: List[str] = field(default_factory=list)
    doencas_cronicas: List[str] = field(default_factory=list)
    cirurgias_previas: List[str] = field(default_factory=list)
    historico_familiar: Dict[str, str] = field(default_factory=dict)
    observacoes: str = ""
    
    # Metadados
    data_cadastro: str = field(default_factory=lambda: datetime.now().isoformat())
    data_atualizacao: str = field(default_factory=lambda: datetime.now().isoformat())
    ativo: bool = True
    
    @classmethod
    def criar_novo(cls, **kwargs) -> 'Paciente':
        """Cria novo paciente"""
        # Remover campos vazios para usar valores padrão
        campos_validos = {}
        for key, value in kwargs.items():
            if value is not None and value != "":
                campos_validos[key] = value
        
        return cls(**campos_validos)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário usando asdict do dataclass"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Paciente':
        """Cria paciente a partir de dicionário"""
        return cls(**data)

@dataclass
class Diagnostico:
    """Modelo de diagnóstico"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    paciente_id: str = ""
    paciente_nome: str = ""
    sintomas: List[str] = field(default_factory=list)
    data_hora: str = field(default_factory=lambda: datetime.now().isoformat())
    resultados: List[Dict] = field(default_factory=list)
    top_resultado: str = ""
    top_porcentagem: float = 0.0
    
    @classmethod
    def criar_novo(cls, paciente: 'Paciente', sintomas: List[str], 
                   resultados: List[Dict]) -> 'Diagnostico':
        """Cria novo diagnóstico"""
        # Verificar se há resultados
        if resultados:
            top_resultado = resultados[0].get('doenca', 'N/A')
            top_porcentagem = resultados[0].get('porcentagem', 0.0)
        else:
            top_resultado = "Nenhum resultado"
            top_porcentagem = 0.0
        
        return cls(
            paciente_id=paciente.id,
            paciente_nome=paciente.nome,
            sintomas=sintomas,
            resultados=resultados[:10],  # Top 10 resultados
            top_resultado=top_resultado,
            top_porcentagem=top_porcentagem
        )

@dataclass
class Doenca:
    """Modelo de doença"""
    nome: str = ""
    tipo: str = "físico"  # "físico" ou "psicológico"
    categoria: str = "fisica"  # "fisica" ou "mental"
    descricao: str = ""
    tratamento: str = ""
    severidade: str = "moderada"  # "baixa", "moderada", "alta"
    sintomas: List[Dict] = field(default_factory=list)  # Lista de {s: nome, peso: float}
    condicoes: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Doenca':
        """Cria doença a partir de dicionário"""
        return cls(
            nome=data.get('doenca', ''),
            tipo=data.get('tipo', 'físico'),
            categoria=data.get('categoria', 'fisica'),
            descricao=data.get('descricao', ''),
            tratamento=data.get('tratamento', ''),
            severidade=data.get('severidade', 'moderada'),
            sintomas=data.get('sintomas', []),
            condicoes=data.get('condicoes', {})
        )