"""
Motor de diagnóstico
"""
from typing import List, Dict, Tuple
import hashlib

from config import CONFIG
from models import Doenca
from utils import setup_logging

logger = setup_logging()

class ResultadoDiagnostico:
    """Resultado de diagnóstico"""
    
    def __init__(self, doenca: Doenca, sintomas_selecionados: List[str]):
        self.doenca = doenca
        self.sintomas_selecionados = sintomas_selecionados
        self.sintomas_correspondentes = []
        self.sintomas_faltantes = []
        self.pontuacao_bruta = 0.0
        self.pontuacao_maxima = 0.0
        self.porcentagem = 0.0
        self._calcular()
    
    def _calcular(self):
        """Calcula compatibilidade"""
        # Extrair sintomas da doença com pesos
        sintomas_doenca = {}
        for sintoma in self.doenca.sintomas:
            if isinstance(sintoma, dict):
                nome = sintoma["s"]
                peso = float(sintoma.get("peso", 1.0))
            else:
                nome = str(sintoma)
                peso = 1.0
            sintomas_doenca[nome] = peso
            self.pontuacao_maxima += peso
        
        # Verificar correspondência
        for nome_sintoma, peso in sintomas_doenca.items():
            if nome_sintoma in self.sintomas_selecionados:
                self.pontuacao_bruta += peso
                self.sintomas_correspondentes.append(nome_sintoma)
            else:
                self.sintomas_faltantes.append(nome_sintoma)
        
        # Calcular porcentagem
        if self.pontuacao_maxima > 0:
            self.porcentagem = round((self.pontuacao_bruta / self.pontuacao_maxima) * 100, 1)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "doenca": self.doenca.nome,
            "tipo": self.doenca.tipo,
            "categoria": self.doenca.categoria,
            "descricao": self.doenca.descricao,
            "tratamento": self.doenca.tratamento,
            "severidade": self.doenca.severidade,
            "porcentagem": self.porcentagem,
            "sintomas_correspondentes": self.sintomas_correspondentes,
            "sintomas_faltantes": self.sintomas_faltantes,
            "pontuacao_bruta": round(self.pontuacao_bruta, 2),
            "pontuacao_maxima": round(self.pontuacao_maxima, 2)
        }

class DiagnosticoEngine:
    """Motor de diagnóstico"""
    
    def __init__(self, database):
        self.db = database
        self.cache = {}
        logger.info(f"Engine inicializado com {len(self.db.doencas)} doenças")
    
    def avaliar(self, sintomas: List[str], paciente_id: str = None) -> List[Dict]:
        """Avalia sintomas e retorna diagnósticos"""
        if not sintomas:
            return []
        
        # Verificar cache
        cache_key = self._gerar_cache_key(sintomas)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        resultados = []
        
        for doenca in self.db.doencas:
            # Verificar condições
            if not self._verificar_condicoes(doenca, sintomas):
                continue
            
            # Calcular compatibilidade
            resultado = ResultadoDiagnostico(doenca, sintomas)
            
            # Filtrar por porcentagem mínima
            if resultado.porcentagem >= CONFIG["PORCENTAGEM_MINIMA"]:
                resultados.append(resultado.to_dict())
        
        # Ordenar por porcentagem
        resultados.sort(key=lambda x: x["porcentagem"], reverse=True)
        
        # Limitar resultados
        resultados = resultados[:CONFIG["LIMITE_RESULTADOS"]]
        
        # Salvar no cache
        self.cache[cache_key] = resultados
        
        return resultados
    
    def _verificar_condicoes(self, doenca: Doenca, sintomas: List[str]) -> bool:
        """Verifica condições da doença"""
        condicoes = doenca.condicoes
        
        # Verificar sintomas obrigatórios
        obrigatorios = condicoes.get("sintomas_obrigatorios", [])
        if obrigatorios:
            for obrig in obrigatorios:
                if obrig not in sintomas:
                    return False
        
        # Verificar mínimo de sintomas
        min_sintomas = condicoes.get("min_sintomas", 0)
        if min_sintomas > 0:
            sintomas_doenca = [
                s["s"] if isinstance(s, dict) else str(s)
                for s in doenca.sintomas
            ]
            
            comuns = [s for s in sintomas_doenca if s in sintomas]
            if len(comuns) < min_sintomas:
                return False
        
        return True
    
    def _gerar_cache_key(self, sintomas: List[str]) -> str:
        """Gera chave de cache"""
        sintomas_sorted = sorted(sintomas)
        sintomas_str = ','.join(sintomas_sorted)
        return hashlib.md5(sintomas_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Limpa cache"""
        self.cache.clear()
        logger.info("Cache do engine limpo")