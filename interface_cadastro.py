# [file name]: interface_cadastro.py
[file content begin]
"""
Interface de cadastro de pacientes
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Optional, List, Callable
import re

from paciente import Paciente, PacienteManager, Sexo, TipoSanguineo, Endereco, Contato, HistoricoMedico

class CadastroPacienteWindow(tk.Toplevel):
    """Janela de cadastro/edição de pacientes"""
    
    def __init__(self, parent, paciente_manager: PacienteManager, 
                 paciente_id: Optional[str] = None, 
                 on_save_callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.paciente_manager = paciente_manager
        self.paciente_id = paciente_id
        self.on_save_callback = on_save_callback
        
        if paciente_id:
            self.title("Editar Paciente")
            self.paciente = paciente_manager.get_paciente_por_id(paciente_id)
        else:
            self.title("Cadastrar Novo Paciente")
            self.paciente = Paciente()
        
        self._setup_window()
        self._create_widgets()
        self._load_paciente_data()
    
    def _setup_window(self):
        """Configura janela"""
        self.geometry("1000x700")
        self.resizable(True, True)
        
        # Centralizar
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configurar pesos
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Cria widgets da interface"""
        # Notebook (abas)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba 1: Dados Pessoais
        aba_dados = ttk.Frame(notebook)
        notebook.add(aba_dados, text="Dados Pessoais")
        self._create_aba_dados(aba_dados)
        
        # Aba 2: Endereço e Contato
        aba_contato = ttk.Frame(notebook)
        notebook.add(aba_contato, text="Endereço e Contato")
        self._create_aba_contato(aba_contato)
        
        # Aba 3: Histórico Médico
        aba_historico = ttk.Frame(notebook)
        notebook.add(aba_historico, text="Histórico Médico")
        self._create_aba_historico(aba_historico)
        
        # Painel de botões
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Salvar", 
                  command=self._salvar, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Estilo para botão destacado
        style = ttk.Style()
        style.configure("Accent.TButton", background="#4CAF50", foreground="white")
    
    def _create_aba_dados(self, parent):
        """Cria aba de dados pessoais"""
        # Frame com scroll
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        container = ttk.Frame(canvas)
        
        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Conteúdo
        row = 0
        
        # Código
        ttk.Label(container, text="Código:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.codigo_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.codigo_var, state="readonly", width=20).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        row += 1
        
        # Nome Completo (obrigatório)
        ttk.Label(container, text="Nome Completo *:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.nome_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.nome_var, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        row += 1
        
        # Nome Social
        ttk.Label(container, text="Nome Social:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.nome_social_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.nome_social_var, width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        row += 1
        
        # CPF
        ttk.Label(container, text="CPF:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.cpf_var = tk.StringVar()
        cpf_entry = ttk.Entry(container, textvariable=self.cpf_var, width=20)
        cpf_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        cpf_entry.bind("<KeyRelease>", self._formatar_cpf)
        row += 1
        
        # RG
        ttk.Label(container, text="RG:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rg_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.rg_var, width=20).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        
        # Data de Nascimento
        ttk.Label(container, text="Data de Nascimento:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.data_nascimento_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.data_nascimento_var, width=15).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        ttk.Label(container, text="(DD/MM/AAAA)").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Sexo
        ttk.Label(container, text="Sexo:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.sexo_var = tk.StringVar(value=Sexo.OUTRO.value)
        sexo_combo = ttk.Combobox(container, textvariable=self.sexo_var, 
                                 values=[s.value for s in Sexo], state="readonly", width=15)
        sexo_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Tipo Sanguíneo
        ttk.Label(container, text="Tipo Sanguíneo:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tipo_sanguineo_var = tk.StringVar()
        tipo_combo = ttk.Combobox(container, textvariable=self.tipo_sanguineo_var,
                                 values=[t.value for t in TipoSanguineo], state="readonly", width=10)
        tipo_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Altura e Peso
        altura_frame = ttk.Frame(container)
        altura_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(altura_frame, text="Altura:").pack(side=tk.LEFT)
        self.altura_var = tk.StringVar()
        ttk.Entry(altura_frame, textvariable=self.altura_var, width=8).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(altura_frame, text="cm").pack(side=tk.LEFT)
        
        ttk.Label(altura_frame, text="Peso:").pack(side=tk.LEFT, padx=(10, 0))
        self.peso_var = tk.StringVar()
        ttk.Entry(altura_frame, textvariable=self.peso_var, width=8).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(altura_frame, text="kg").pack(side=tk.LEFT)
        
        # Botão calcular IMC
        ttk.Button(altura_frame, text="Calcular IMC", 
                  command=self._calcular_imc, width=12).pack(side=tk.LEFT, padx=(10, 0))
        row += 1
        
        # Resultado IMC
        self.imc_label = ttk.Label(container, text="IMC: -- (--)")
        self.imc_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Observações
        ttk.Label(container, text="Observações:").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=5)
        self.observacoes_text = scrolledtext.ScrolledText(container, width=50, height=8, wrap=tk.WORD)
        self.observacoes_text.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        row += 1
        
        # Configurar pesos das colunas
        container.columnconfigure(1, weight=1)
    
    def _create_aba_contato(self, parent):
        """Cria aba de endereço e contato"""
        # Frame com scroll
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        container = ttk.Frame(canvas)
        
        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Conteúdo
        row = 0
        
        # Endereço
        ttk.Label(container, text="Endereço", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5)
        )
        row += 1
        
        # Logradouro e Número
        ttk.Label(container, text="Logradouro:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.logradouro_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.logradouro_var, width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        row += 1
        
        ttk.Label(container, text="Número:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.numero_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.numero_var, width=15).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        
        ttk.Label(container, text="Complemento:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.complemento_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.complemento_var, width=40).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        
        ttk.Label(container, text="Bairro:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.bairro_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.bairro_var, width=40).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        
        ttk.Label(container, text="Cidade:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.cidade_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.cidade_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(container, text="Estado:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        self.estado_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.estado_var, width=5).grid(
            row=row, column=3, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        
        ttk.Label(container, text="CEP:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.cep_var = tk.StringVar()
        cep_entry = ttk.Entry(container, textvariable=self.cep_var, width=15)
        cep_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        cep_entry.bind("<KeyRelease>", self._formatar_cep)
        row += 2
        
        # Contato
        ttk.Label(container, text="Contato", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5)
        )
        row += 1
        
        # Telefones
        ttk.Label(container, text="Telefone:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.telefone_var = tk.StringVar()
        telefone_entry = ttk.Entry(container, textvariable=self.telefone_var, width=20)
        telefone_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        telefone_entry.bind("<KeyRelease>", lambda e: self._formatar_telefone(self.telefone_var))
        row += 1
        
        ttk.Label(container, text="Celular *:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.celular_var = tk.StringVar()
        celular_entry = ttk.Entry(container, textvariable=self.celular_var, width=20)
        celular_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        celular_entry.bind("<KeyRelease>", lambda e: self._formatar_telefone(self.celular_var))
        row += 1
        
        # Email
        ttk.Label(container, text="Email:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.email_var, width=40).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 2
        
        # Contato de Emergência
        ttk.Label(container, text="Contato de Emergência", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5)
        )
        row += 1
        
        ttk.Label(container, text="Nome:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.contato_emergencia_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.contato_emergencia_var, width=40).grid(
            row=row, column=1, sticky=tk.W, padx=5, pady=5
        )
        row += 1
        ttk.Label(container, text="Telefone:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.telefone_emergencia_var = tk.StringVar()
        telefone_emergencia_entry = ttk.Entry(container, textvariable=self.telefone_emergencia_var, width=20)
        telefone_emergencia_entry.grid(row=row, column=1, sticky=tk.W, padx
, pady=5)
        telefone_emergencia_entry.bind("<KeyRelease>", lambda e: self._formatar_telefone(self.telefone_emergencia_var))
        row += 1