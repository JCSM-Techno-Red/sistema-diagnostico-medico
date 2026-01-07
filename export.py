"""
Sistema de exportação
"""
import os
from datetime import datetime
from typing import List, Dict
from tkinter import filedialog, messagebox

from config import ConfigManager
from models import Paciente, Diagnostico
from utils import setup_logging, formatar_data

logger = setup_logging()

class Exportador:
    """Classe base para exportação"""
    
    @staticmethod
    def sugerir_nome_arquivo(base_nome: str, extensao: str) -> str:
        """Sugere nome de arquivo"""
        data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = f"{base_nome}_{data_str}.{extensao}"
        return ConfigManager.get_export_path(nome)

def exportar_diagnostico(paciente_nome: str, sintomas: List[str], 
                         resultados: List[Dict]) -> bool:
    """Exporta diagnóstico para TXT"""
    try:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"diagnostico_{paciente_nome.replace(' ', '_')}.txt",
            initialdir=ConfigManager.get_path("exports")
        )
        
        if not filepath:
            return False
        
        lines = [
            "=" * 70,
            "RELATÓRIO DE DIAGNÓSTICO",
            "=" * 70,
            f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"Paciente: {paciente_nome}",
            f"Sintomas selecionados: {len(sintomas)}",
            "",
            "SINTOMAS:",
            "-" * 40,
            ", ".join(sintomas),
            "",
            "RESULTADOS:",
            "-" * 40
        ]
        
        for i, resultado in enumerate(resultados[:10], 1):
            lines.append(f"{i}. {resultado['doenca']} ({resultado['porcentagem']:.1f}%)")
            lines.append(f"   Tipo: {resultado['tipo']} | Severidade: {resultado['severidade']}")
            lines.append(f"   Sintomas correspondentes: {len(resultado['sintomas_correspondentes'])}")
            lines.append("")
        
        if resultados:
            top = resultados[0]
            lines.append("DIAGNÓSTICO PRINCIPAL:")
            lines.append("-" * 40)
            lines.append(f"Doença: {top['doenca']}")
            lines.append(f"Descrição: {top['descricao']}")
            lines.append("")
            lines.append("Tratamento sugerido:")
            lines.append(top['tratamento'])
        else:
            lines.append("Tratamento sugerido: Nenhum tratamento disponível.")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("Sistema de Diagnóstico Médico")
        lines.append("Documento para auxílio médico. Não substitui consulta especializada.")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Diagnóstico exportado: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exportar diagnóstico: {e}")
        messagebox.showerror("Erro", f"Falha na exportação: {str(e)}")
        return False

def exportar_historico(historico: List[Diagnostico]) -> bool:
    """Exporta histórico completo"""
    try:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"historico_diagnosticos.txt",
            initialdir=ConfigManager.get_path("exports")
        )
        
        if not filepath:
            return False
        
        lines = [
            "=" * 70,
            "HISTÓRICO COMPLETO DE DIAGNÓSTICOS",
            "=" * 70,
            f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"Total de registros: {len(historico)}",
            ""
        ]
        
        for i, diag in enumerate(historico, 1):
            lines.append(f"REGISTRO #{i}")
            lines.append("-" * 40)
            lines.append(f"Data: {formatar_data(diag.data_hora)}")
            lines.append(f"Paciente: {diag.paciente_nome}")
            lines.append(f"Sintomas: {len(diag.sintomas)}")
            lines.append(f"Diagnóstico principal: {diag.top_resultado} ({diag.top_porcentagem:.1f}%)")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append("FIM DO HISTÓRICO")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Histórico exportado: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exportar histórico: {e}")
        messagebox.showerror("Erro", f"Falha na exportação: {str(e)}")
        return False

def exportar_paciente(paciente: Paciente) -> bool:
    """Exporta ficha do paciente"""
    try:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"ficha_{paciente.nome.replace(' ', '_')}.txt",
            initialdir=ConfigManager.get_path("exports")
        )
        
        if not filepath:
            return False
        
        lines = [
            "=" * 70,
            "FICHA MÉDICA DO PACIENTE",
            "=" * 70,
            f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "INFORMAÇÕES PESSOAIS:",
            "-" * 40,
            f"Nome: {paciente.nome}",
            f"CPF: {paciente.cpf}",
            f"Data Nascimento: {paciente.data_nascimento}",
            f"Sexo: {paciente.sexo}",
            f"Telefone: {paciente.telefone}",
            f"Email: {paciente.email}",
            f"Endereço: {paciente.endereco}",
            f"Cidade/UF: {paciente.cidade}/{paciente.estado}",
            f"CEP: {paciente.cep}",
            "",
            "INFORMAÇÕES MÉDICAS:",
            "-" * 40
        ]
        
        if paciente.alergias:
            lines.append("Alergias:")
            for alergia in paciente.alergias:
                lines.append(f"  • {alergia}")
        else:
            lines.append("Alergias: Nenhuma registrada")
        
        lines.append("")
        
        if paciente.medicamentos_uso:
            lines.append("Medicamentos em uso:")
            for med in paciente.medicamentos_uso:
                lines.append(f"  • {med}")
        else:
            lines.append("Medicamentos em uso: Nenhum registrado")
        
        lines.append("")
        
        if paciente.doencas_cronicas:
            lines.append("Doenças crônicas:")
            for doenca in paciente.doencas_cronicas:
                lines.append(f"  • {doenca}")
        else:
            lines.append("Doenças crônicas: Nenhuma registrada")
        
        lines.append("")
        
        if paciente.observacoes:
            lines.append("Observações:")
            lines.append(paciente.observacoes)
        
        lines.append("")
        lines.append("METADADOS:")
        lines.append("-" * 40)
        lines.append(f"Data do cadastro: {formatar_data(paciente.data_cadastro)}")
        lines.append(f"Última atualização: {formatar_data(paciente.data_atualizacao)}")
        lines.append(f"Status: {'Ativo' if paciente.ativo else 'Inativo'}")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("FIM DA FICHA MÉDICA")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Ficha do paciente exportada: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao exportar ficha: {e}")
        messagebox.showerror("Erro", f"Falha na exportação: {str(e)}")
        return False