"""
Interface gráfica principal - Sistema de Diagnóstico Médico
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from typing import List, Optional, Dict
from datetime import datetime
import json

from config import CONFIG
from models import Paciente, Diagnostico
from database import Database
from engine import DiagnosticoEngine
from utils import setup_logging, formatar_data, porcentagem_cor, calcular_idade
from export import exportar_diagnostico, exportar_historico, exportar_paciente

logger = setup_logging()

class PacienteDialog:
    """Diálogo para cadastro/edição de pacientes"""
    
    def __init__(self, parent, paciente: Paciente = None, title="Cadastrar Paciente"):
        self.parent = parent
        self.paciente = paciente
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        if paciente:
            self._preencher_dados()
    
    def _create_widgets(self):
        """Cria widgets do diálogo"""
        # Frame principal com scroll
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Campos do formulário
        campos = [
            ("Nome*:", "nome", 30),
            ("Data Nasc.*:", "data_nascimento", 15),
            ("Sexo*:", "sexo", 15),
            ("CPF:", "cpf", 15),
            ("Telefone:", "telefone", 15),
            ("Email:", "email", 25),
            ("Endereço:", "endereco", 30),
            ("Cidade:", "cidade", 20),
            ("Estado:", "estado", 5),
            ("CEP:", "cep", 10),
        ]
        
        self.entries = {}
        
        for i, (label, field, width) in enumerate(campos):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            if field == "sexo":
                var = tk.StringVar()
                combobox = ttk.Combobox(main_frame, textvariable=var, 
                                       values=CONFIG["PACIENTE"]["sexos_disponiveis"],
                                       width=width)
                combobox.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
                self.entries[field] = var
            elif field == "estado":
                var = tk.StringVar()
                combobox = ttk.Combobox(main_frame, textvariable=var,
                                       values=CONFIG["PACIENTE"]["estados"],
                                       width=width)
                combobox.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
                self.entries[field] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=width)
                entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
                self.entries[field] = var
        
        # Observações
        row = len(campos)
        ttk.Label(main_frame, text="Observações:").grid(row=row, column=0, sticky=tk.NW, pady=2)
        self.observacoes_text = scrolledtext.ScrolledText(main_frame, height=4, width=40)
        self.observacoes_text.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Salvar", 
                  command=self._salvar).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def _preencher_dados(self):
        """Preenche campos com dados do paciente"""
        if self.paciente:
            self.entries["nome"].set(self.paciente.nome or "")
            self.entries["data_nascimento"].set(self.paciente.data_nascimento or "")
            self.entries["sexo"].set(self.paciente.sexo or "")
            self.entries["cpf"].set(self.paciente.cpf or "")
            self.entries["telefone"].set(self.paciente.telefone or "")
            self.entries["email"].set(self.paciente.email or "")
            self.entries["endereco"].set(self.paciente.endereco or "")
            self.entries["cidade"].set(self.paciente.cidade or "")
            self.entries["estado"].set(self.paciente.estado or "")
            self.entries["cep"].set(self.paciente.cep or "")
            self.observacoes_text.delete(1.0, tk.END)
            self.observacoes_text.insert(1.0, self.paciente.observacoes or "")
    
    def _salvar(self):
        """Salva dados do paciente"""
        try:
            dados = {field: var.get().strip() 
                    for field, var in self.entries.items()}
            dados["observacoes"] = self.observacoes_text.get(1.0, tk.END).strip()
            
            # Validar campos obrigatórios
            for campo in CONFIG["PACIENTE"]["campos_obrigatorios"]:
                if not dados.get(campo):
                    raise ValueError(f"Campo obrigatório: {campo}")
            
            self.result = dados
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
    
    def show(self) -> Optional[dict]:
        """Mostra diálogo e retorna resultado"""
        self.dialog.wait_window()
        return self.result

class App:
    """Aplicação principal do Sistema de Diagnóstico Médico"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Diagnóstico Médico - Integrado")
        self.root.geometry(CONFIG["WINDOW_SIZE"])
        
        # Centralizar
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
        # Inicializar componentes
        self.db = Database()
        self.engine = DiagnosticoEngine(self.db)
        self.paciente_atual: Optional[Paciente] = None
        self.sintomas_selecionados = set()
        self.resultados_atuais = []
        
        self._verificar_dados()
        self._create_widgets()
        self._bind_shortcuts()
        
        logger.info("Interface inicializada")
    
    def _verificar_dados(self):
        """Verifica se há dados carregados"""
        print(f"Pacientes carregados: {len(self.db.pacientes)}")
        print(f"Doenças carregadas: {len(self.db.doencas)}")
        print(f"Histórico carregado: {len(self.db.historico)}")
        
        if len(self.db.doencas) == 0:
            messagebox.showwarning("Aviso", 
                "Nenhuma doença carregada. Verifique o arquivo sintomas.json")
    
    def _create_widgets(self):
        """Cria todos os widgets da interface"""
        # Menu principal
        self._create_menu()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Painel paciente
        self._create_paciente_panel(main_frame)
        
        # Painel sintomas
        self._create_sintomas_panel(main_frame)
        
        # Painel resultados
        self._create_resultados_panel(main_frame)
        
        # Painel detalhes
        self._create_detalhes_panel(main_frame)
    
    def _create_menu(self):
        """Cria menu principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Novo Diagnóstico", command=self._novo_diagnostico)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Resultados", command=self._exportar_resultados)
        file_menu.add_command(label="Exportar Histórico", command=self._exportar_historico)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Pacientes
        pac_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pacientes", menu=pac_menu)
        pac_menu.add_command(label="Cadastrar Novo", command=self._cadastrar_paciente)
        pac_menu.add_command(label="Buscar Paciente", command=self._buscar_paciente)
        pac_menu.add_command(label="Listar Todos", command=self._listar_pacientes)
        pac_menu.add_separator()
        pac_menu.add_command(label="Exportar Ficha", command=self._exportar_ficha)
        
        # Menu Diagnóstico
        diag_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Diagnóstico", menu=diag_menu)
        diag_menu.add_command(label="Executar Diagnóstico", command=self._executar_diagnostico)
        diag_menu.add_command(label="Limpar Sintomas", command=self._limpar_sintomas)
        diag_menu.add_separator()
        diag_menu.add_command(label="Ver Histórico", command=self._ver_historico)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._sobre)
        help_menu.add_command(label="Estatísticas", command=self._mostrar_estatisticas)
    
    def _create_paciente_panel(self, parent):
        """Cria painel do paciente"""
        frame = ttk.LabelFrame(parent, text="Paciente", padding="10")
        frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Informações
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, expand=True)
        
        # Nome
        ttk.Label(info_frame, text="Paciente:").grid(row=0, column=0, sticky=tk.W)
        self.paciente_nome_var = tk.StringVar(value="Nenhum paciente selecionado")
        self.paciente_nome_label = ttk.Label(info_frame, textvariable=self.paciente_nome_var, 
                 font=("Arial", 10, "bold"), foreground="blue")
        self.paciente_nome_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Informações extras
        ttk.Label(info_frame, text="ID:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.paciente_id_var = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.paciente_id_var, 
                 font=("Arial", 8), foreground="gray").grid(row=1, column=1, sticky=tk.W, padx=10, pady=(5, 0))
        
        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Selecionar Paciente", 
                  command=self._selecionar_paciente).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Cadastrar Novo", 
                  command=self._cadastrar_paciente).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Ver Ficha", 
                  command=self._ver_ficha).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Limpar", 
                  command=self._limpar_paciente).pack(side=tk.LEFT, padx=2)
        
        # Botão diagnóstico
        ttk.Button(btn_frame, text="▶ Executar Diagnóstico", 
                  command=self._executar_diagnostico, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=10)
    
    def _create_sintomas_panel(self, parent):
        """Cria painel de sintomas"""
        frame = ttk.LabelFrame(parent, text="Sintomas", padding="10")
        frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Busca
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        self.busca_var = tk.StringVar()
        busca_entry = ttk.Entry(search_frame, textvariable=self.busca_var, width=30)
        busca_entry.pack(side=tk.LEFT, padx=5)
        busca_entry.bind("<KeyRelease>", lambda e: self._filtrar_sintomas())
        
        # Lista de sintomas com scroll
        sintomas_frame = ttk.Frame(frame)
        sintomas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas_sintomas = tk.Canvas(sintomas_frame, width=300)
        scrollbar = ttk.Scrollbar(sintomas_frame, orient="vertical", command=self.canvas_sintomas.yview)
        self.sintomas_container = ttk.Frame(self.canvas_sintomas)
        
        self.sintomas_container.bind("<Configure>", 
            lambda e: self.canvas_sintomas.configure(scrollregion=self.canvas_sintomas.bbox("all")))
        
        self.canvas_sintomas.create_window((0, 0), window=self.sintomas_container, anchor="nw")
        self.canvas_sintomas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas_sintomas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botões de ação
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Selecionar Tudo", 
                  command=self._selecionar_tudo_sintomas).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Limpar Sintomas", 
                  command=self._limpar_sintomas).pack(side=tk.LEFT, padx=2)
        ttk.Label(btn_frame, text=f"Sintomas: {len(self.sintomas_selecionados)} selecionados").pack(side=tk.LEFT, padx=10)
        
        # Carregar sintomas
        self._carregar_sintomas()
    
    def _create_resultados_panel(self, parent):
        """Cria painel de resultados"""
        frame = ttk.LabelFrame(parent, text="Resultados do Diagnóstico", padding="10")
        frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview
        columns = ("Doença", "Compatibilidade", "Severidade", "Tipo")
        self.tree_resultados = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree_resultados.heading(col, text=col)
            self.tree_resultados.column(col, width=100)
        
        self.tree_resultados.column("Doença", width=200)
        self.tree_resultados.column("Compatibilidade", width=100)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree_resultados.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_resultados.xview)
        self.tree_resultados.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Layout
        self.tree_resultados.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Bind
        self.tree_resultados.bind("<<TreeviewSelect>>", self._mostrar_detalhes)
        
        # Tags para cores
        self.tree_resultados.tag_configure("alta", background="#ffebee")
        self.tree_resultados.tag_configure("media", background="#fff8e1")
        self.tree_resultados.tag_configure("baixa", background="#e8f5e9")
        
        # Label para quando não há resultados
        self.label_sem_resultados = ttk.Label(frame, text="Execute um diagnóstico para ver resultados", 
                                             font=("Arial", 10, "italic"), foreground="gray")
        self.label_sem_resultados.place(relx=0.5, rely=0.5, anchor="center")
    
    def _create_detalhes_panel(self, parent):
        """Cria painel de detalhes"""
        frame = ttk.LabelFrame(parent, text="Detalhes do Diagnóstico", padding="10")
        frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=(10, 0))
        
        self.detalhes_text = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, height=10, font=("Consolas", 9)
        )
        self.detalhes_text.pack(fill=tk.BOTH, expand=True)
        self.detalhes_text.configure(state="disabled")
        
        # Label para quando não há detalhes
        self.label_sem_detalhes = ttk.Label(frame, text="Selecione um resultado para ver detalhes", 
                                           font=("Arial", 10, "italic"), foreground="gray")
        self.label_sem_detalhes.place(relx=0.5, rely=0.5, anchor="center")
    
    def _bind_shortcuts(self):
        """Configura atalhos de teclado"""
        self.root.bind('<Control-n>', lambda e: self._novo_diagnostico())
        self.root.bind('<Control-d>', lambda e: self._executar_diagnostico())
        self.root.bind('<F5>', lambda e: self._executar_diagnostico())
        self.root.bind('<Control-s>', lambda e: self._selecionar_tudo_sintomas())
        self.root.bind('<Control-l>', lambda e: self._limpar_sintomas())
        self.root.bind('<Control-p>', lambda e: self._cadastrar_paciente())
        self.root.bind('<Control-e>', lambda e: self._exportar_resultados())
    
    def _carregar_sintomas(self):
        """Carrega sintomas na interface"""
        # Limpar container
        for widget in self.sintomas_container.winfo_children():
            widget.destroy()
        
        try:
            # Obter sintomas
            sintomas = self.db.obter_sintomas_unicos()
            filtro = self.busca_var.get().lower()
            
            if not sintomas:
                label = ttk.Label(self.sintomas_container, 
                                 text="Nenhum sintoma carregado\nVerifique o arquivo sintomas.json",
                                 foreground="red", justify="center")
                label.pack(pady=20)
                return
            
            # Filtrar
            sintomas_filtrados = [s for s in sintomas if filtro in s.lower()]
            
            if not sintomas_filtrados:
                label = ttk.Label(self.sintomas_container, 
                                 text="Nenhum sintoma encontrado",
                                 foreground="gray", justify="center")
                label.pack(pady=20)
                return
            
            # Criar checkbuttons
            for sintoma in sintomas_filtrados:
                var = tk.BooleanVar(value=(sintoma in self.sintomas_selecionados))
                
                cb = ttk.Checkbutton(
                    self.sintomas_container,
                    text=sintoma.capitalize(),
                    variable=var,
                    command=lambda s=sintoma, v=var: self._atualizar_sintoma_selecionado(s, v)
                )
                cb.pack(anchor=tk.W, padx=5, pady=1)
            
        except Exception as e:
            logger.error(f"Erro ao carregar sintomas: {e}")
            label = ttk.Label(self.sintomas_container, 
                             text=f"Erro ao carregar sintomas:\n{str(e)}",
                             foreground="red", justify="center")
            label.pack(pady=20)
    
    def _atualizar_sintoma_selecionado(self, sintoma: str, var: tk.BooleanVar):
        """Atualiza seleção de sintoma"""
        if var.get():
            self.sintomas_selecionados.add(sintoma)
        else:
            self.sintomas_selecionados.discard(sintoma)
        
        # Atualizar contador
        for widget in self.sintomas_container.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.config(text=f"Sintomas: {len(self.sintomas_selecionados)} selecionados")
                        break
    
    def _filtrar_sintomas(self):
        """Filtra sintomas baseado na busca"""
        self._carregar_sintomas()
    
    def _selecionar_tudo_sintomas(self):
        """Seleciona todos os sintomas visíveis"""
        try:
            sintomas = self.db.obter_sintomas_unicos()
            filtro = self.busca_var.get().lower()
            
            sintomas_visiveis = [s for s in sintomas if filtro in s.lower()]
            self.sintomas_selecionados.update(sintomas_visiveis)
            
            # Atualizar checkboxes
            for child in self.sintomas_container.winfo_children():
                if isinstance(child, ttk.Checkbutton):
                    # Obter texto do checkbutton
                    texto = child.cget("text").lower()
                    # Verificar se está na lista de visíveis
                    for sintoma in sintomas_visiveis:
                        if sintoma.lower() in texto:
                            child.state(['selected'])
                            break
        except Exception as e:
            logger.error(f"Erro ao selecionar tudo: {e}")
    
    def _limpar_sintomas(self):
        """Limpa seleção de sintomas"""
        self.sintomas_selecionados.clear()
        
        # Atualizar checkboxes
        for child in self.sintomas_container.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                child.state(['!selected'])
        
        self._limpar_resultados()
    
    def _limpar_resultados(self):
        """Limpa resultados"""
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        
        self.detalhes_text.configure(state="normal")
        self.detalhes_text.delete(1.0, tk.END)
        self.detalhes_text.configure(state="disabled")
        
        self.resultados_atuais = []
        self.label_sem_resultados.tkraise()
        self.label_sem_detalhes.tkraise()
    
    # ========== MÉTODOS DE PACIENTES ==========
    
    def _selecionar_paciente(self):
        """Seleciona paciente da lista"""
        pacientes = list(self.db.pacientes.values())
        
        if not pacientes:
            messagebox.showinfo("Informação", "Nenhum paciente cadastrado. Cadastre um paciente primeiro.")
            self._cadastrar_paciente()
            return
        
        # Criar janela de seleção simples
        selecionar_window = tk.Toplevel(self.root)
        selecionar_window.title("Selecionar Paciente")
        selecionar_window.geometry("500x400")
        
        # Lista de pacientes
        frame_lista = ttk.Frame(selecionar_window, padding="10")
        frame_lista.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("Nome", "CPF", "Telefone", "Idade")
        tree = ttk.Treeview(frame_lista, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Nome", width=200)
        tree.column("CPF", width=120)
        tree.column("Telefone", width=100)
        tree.column("Idade", width=60)
        
        # Adicionar pacientes
        for paciente in pacientes:
            if paciente.ativo:
                # Calcular idade aproximada
                idade = calcular_idade(paciente.data_nascimento) if paciente.data_nascimento else "N/A"
                
                tree.insert("", "end", values=(
                    paciente.nome,
                    paciente.cpf or "N/A",
                    paciente.telefone or "N/A",
                    idade
                ), tags=(paciente.id,))
        
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def selecionar():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione um paciente.")
                return
            
            item = tree.item(selection[0])
            paciente_id = item["tags"][0]
            
            paciente = self.db.obter_paciente(paciente_id)
            if paciente:
                self.paciente_atual = paciente
                self.paciente_nome_var.set(paciente.nome)
                self.paciente_id_var.set(f"ID: {paciente.id[:8]}...")
                selecionar_window.destroy()
                messagebox.showinfo("Sucesso", f"Paciente {paciente.nome} selecionado!")
        
        # Botões
        btn_frame = ttk.Frame(selecionar_window)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Selecionar", 
                  command=selecionar).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", 
                  command=selecionar_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def _cadastrar_paciente(self):
        """Cadastra novo paciente"""
        dialog = PacienteDialog(self.root)
        dados = dialog.show()
        
        if dados:
            try:
                paciente = Paciente.criar_novo(**dados)
                if self.db.adicionar_paciente(paciente):
                    self.paciente_atual = paciente
                    self.paciente_nome_var.set(paciente.nome)
                    self.paciente_id_var.set(f"ID: {paciente.id[:8]}...")
                    messagebox.showinfo("Sucesso", "Paciente cadastrado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
    
    def _buscar_paciente(self):
        """Busca paciente por nome ou CPF"""
        from tkinter import simpledialog
        
        termo = simpledialog.askstring("Buscar Paciente", 
                                      "Digite nome ou CPF do paciente:")
        
        if termo:
            pacientes = self.db.buscar_pacientes(nome=termo)
            if not pacientes:
                pacientes = self.db.buscar_pacientes(cpf=termo)
            
            if pacientes:
                if len(pacientes) == 1:
                    paciente = pacientes[0]
                    self.paciente_atual = paciente
                    self.paciente_nome_var.set(paciente.nome)
                    self.paciente_id_var.set(f"ID: {paciente.id[:8]}...")
                    messagebox.showinfo("Sucesso", f"Paciente {paciente.nome} encontrado!")
                else:
                    # Mostrar lista para selecionar
                    lista = "\n".join([f"{p.nome} ({p.cpf})" for p in pacientes[:5]])
                    messagebox.showinfo("Múltiplos resultados", 
                                      f"Encontrados {len(pacientes)} pacientes:\n\n{lista}")
            else:
                messagebox.showinfo("Não encontrado", "Nenhum paciente encontrado com esse termo.")
    
    def _listar_pacientes(self):
        """Lista todos os pacientes"""
        pacientes = list(self.db.pacientes.values())
        
        if not pacientes:
            messagebox.showinfo("Pacientes", "Nenhum paciente cadastrado.")
            return
        
        lista_window = tk.Toplevel(self.root)
        lista_window.title("Todos os Pacientes")
        lista_window.geometry("600x500")
        
        # Text widget com scroll
        text = scrolledtext.ScrolledText(lista_window, wrap=tk.WORD, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        texto = f"TOTAL DE PACIENTES: {len(pacientes)}\n{'='*60}\n\n"
        
        for i, paciente in enumerate(pacientes, 1):
            texto += f"{i}. {paciente.nome}\n"
            texto += f"   CPF: {paciente.cpf or 'N/A'}\n"
            texto += f"   Telefone: {paciente.telefone or 'N/A'}\n"
            texto += f"   Email: {paciente.email or 'N/A'}\n"
            texto += f"   Status: {'Ativo' if paciente.ativo else 'Inativo'}\n"
            texto += f"   Cadastro: {formatar_data(paciente.data_cadastro)}\n"
            texto += "-" * 40 + "\n"
        
        text.insert(1.0, texto)
        text.configure(state="disabled")
    
    def _ver_ficha(self):
        """Mostra ficha do paciente atual"""
        if not self.paciente_atual:
            messagebox.showwarning("Aviso", "Nenhum paciente selecionado.")
            return
        
        self._mostrar_ficha_paciente(self.paciente_atual)
    
    def _mostrar_ficha_paciente(self, paciente: Paciente):
        """Mostra ficha de um paciente"""
        window = tk.Toplevel(self.root)
        window.title(f"Ficha Médica - {paciente.nome}")
        window.geometry("600x500")
        
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba Informações
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Informações")
        
        info_text = f"""PACIENTE: {paciente.nome}
ID: {paciente.id}
CPF: {paciente.cpf or 'N/A'}
Data Nascimento: {paciente.data_nascimento or 'N/A'}
Sexo: {paciente.sexo or 'N/A'}
Telefone: {paciente.telefone or 'N/A'}
Email: {paciente.email or 'N/A'}
Endereço: {paciente.endereco or 'N/A'}
Cidade/UF: {paciente.cidade or 'N/A'}/{paciente.estado or 'N/A'}
CEP: {paciente.cep or 'N/A'}

Data Cadastro: {formatar_data(paciente.data_cadastro)}
Última Atualização: {formatar_data(paciente.data_atualizacao)}
Status: {'Ativo' if paciente.ativo else 'Inativo'}
"""
        
        text_widget = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, info_text)
        text_widget.configure(state="disabled")
        
        # Aba Observações
        if paciente.observacoes:
            obs_frame = ttk.Frame(notebook)
            notebook.add(obs_frame, text="Observações")
            
            obs_text = scrolledtext.ScrolledText(obs_frame, wrap=tk.WORD)
            obs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            obs_text.insert(1.0, paciente.observacoes)
            obs_text.configure(state="disabled")
    
    def _limpar_paciente(self):
        """Limpa paciente atual"""
        self.paciente_atual = None
        self.paciente_nome_var.set("Nenhum paciente selecionado")
        self.paciente_id_var.set("")
        self._limpar_sintomas()
    
    # ========== MÉTODOS DE DIAGNÓSTICO ==========
    
    def _executar_diagnostico(self):
        """Executa diagnóstico com os sintomas selecionados"""
        if not self.sintomas_selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um sintoma.")
            return
        
        paciente_nome = "Paciente Não Identificado"
        paciente_obj = None
        
        if not self.paciente_atual:
            if messagebox.askyesno("Confirmação", 
                                 "Nenhum paciente selecionado. Deseja continuar sem paciente?"):
                # Criar paciente temporário
                paciente_obj = Paciente(
                    id="temp_" + str(datetime.now().timestamp()),
                    nome="Paciente Não Identificado",
                    data_nascimento="",
                    sexo="",
                    cpf=""
                )
            else:
                return
        else:
            paciente_obj = self.paciente_atual
            paciente_nome = self.paciente_atual.nome
        
        try:
            # Executar diagnóstico
            sintomas_lista = list(self.sintomas_selecionados)
            resultados = self.engine.avaliar(sintomas_lista)
            self.resultados_atuais = resultados
            
            # Atualizar interface
            self._atualizar_resultados(resultados)
            
            # Salvar no histórico (se não for paciente temporário)
            if paciente_obj and not paciente_obj.id.startswith("temp_"):
                diagnostico = Diagnostico.criar_novo(
                    paciente_obj, sintomas_lista, resultados
                )
                self.db.adicionar_diagnostico(diagnostico)
            
            messagebox.showinfo("Sucesso", 
                              f"Diagnóstico concluído: {len(resultados)} resultados encontrados")
            
        except Exception as e:
            logger.error(f"Erro no diagnóstico: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Detalhes do erro: {error_details}")
            messagebox.showerror("Erro", f"Falha no diagnóstico: {str(e)}")
    
    def _atualizar_resultados(self, resultados: List[Dict]):
        """Atualiza treeview com resultados"""
        # Limpar
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        
        if not resultados:
            self.label_sem_resultados.tkraise()
            return
        
        # Esconder label de sem resultados
        self.label_sem_resultados.lower()
        
        # Adicionar novos
        for resultado in resultados:
            tag = porcentagem_cor(resultado["porcentagem"])
            
            self.tree_resultados.insert("", "end", values=(
                resultado["doenca"],
                f"{resultado['porcentagem']:.1f}%",
                resultado["severidade"].capitalize(),
                resultado["tipo"].capitalize()
            ), tags=(tag,))
        
        # Selecionar primeiro
        if self.tree_resultados.get_children():
            first = self.tree_resultados.get_children()[0]
            self.tree_resultados.selection_set(first)
            self._mostrar_detalhes()
    
    def _mostrar_detalhes(self, event=None):
        """Mostra detalhes do resultado selecionado"""
        selection = self.tree_resultados.selection()
        if not selection:
            self.label_sem_detalhes.tkraise()
            return
        
        # Esconder label de sem detalhes
        self.label_sem_detalhes.lower()
        
        item_id = selection[0]
        item_values = self.tree_resultados.item(item_id, "values")
        doenca_nome = item_values[0]
        
        # Encontrar resultado
        resultado = next((r for r in self.resultados_atuais 
                         if r["doenca"] == doenca_nome), None)
        
        if resultado:
            detalhes = f"""DOENÇA: {resultado['doenca']}
TIPO: {resultado['tipo'].upper()} | SEVERIDADE: {resultado['severidade'].upper()}
COMPATIBILIDADE: {resultado['porcentagem']:.1f}%

DESCRIÇÃO:
{resultado['descricao']}

TRATAMENTO SUGERIDO:
{resultado['tratamento']}

SINTOMAS CORRESPONDENTES ({len(resultado['sintomas_correspondentes'])}):
"""
            for sintoma in resultado['sintomas_correspondentes']:
                detalhes += f"  ✓ {sintoma}\n"
            
            if resultado['sintomas_faltantes']:
                detalhes += f"\nSINTOMAS FALTANTES ({len(resultado['sintomas_faltantes'])}):\n"
                for sintoma in resultado['sintomas_faltantes']:
                    detalhes += f"  ✗ {sintoma}\n"
            
            self.detalhes_text.configure(state="normal")
            self.detalhes_text.delete(1.0, tk.END)
            self.detalhes_text.insert(1.0, detalhes)
            self.detalhes_text.configure(state="disabled")
    
    # ========== MÉTODOS DE HISTÓRICO ==========
    
    def _ver_historico(self):
        """Mostra histórico de diagnósticos"""
        historico = self.db.historico
        
        if not historico:
            messagebox.showinfo("Histórico", "Nenhum diagnóstico registrado.")
            return
        
        window = tk.Toplevel(self.root)
        window.title("Histórico de Diagnósticos")
        window.geometry("800x500")
        
        # Treeview
        columns = ("Data", "Paciente", "Sintomas", "Diagnóstico", "%")
        tree = ttk.Treeview(window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("Data", width=150)
        tree.column("Paciente", width=150)
        tree.column("Sintomas", width=250)
        tree.column("Diagnóstico", width=200)
        tree.column("%", width=80)
        
        # Adicionar dados
        for diag in historico[:50]:  # Limitar a 50
            sintomas_str = ", ".join(diag.sintomas[:3])
            if len(diag.sintomas) > 3:
                sintomas_str += "..."
            
            tree.insert("", "end", values=(
                formatar_data(diag.data_hora),
                diag.paciente_nome,
                sintomas_str,
                diag.top_resultado,
                f"{diag.top_porcentagem:.1f}%"
            ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    # ========== MÉTODOS DE EXPORTAÇÃO ==========
    
    def _exportar_resultados(self):
        """Exporta resultados atuais"""
        if not self.resultados_atuais:
            messagebox.showwarning("Aviso", "Nenhum resultado para exportar.")
            return
        
        paciente = self.paciente_atual.nome if self.paciente_atual else "Paciente"
        sintomas = list(self.sintomas_selecionados)
        
        if exportar_diagnostico(paciente, sintomas, self.resultados_atuais):
            messagebox.showinfo("Sucesso", "Resultados exportados com sucesso!")
    
    def _exportar_historico(self):
        """Exporta histórico completo"""
        if not self.db.historico:
            messagebox.showwarning("Aviso", "Histórico vazio.")
            return
        
        if exportar_historico(self.db.historico):
            messagebox.showinfo("Sucesso", "Histórico exportado com sucesso!")
    
    def _exportar_ficha(self):
        """Exporta ficha do paciente atual"""
        if not self.paciente_atual:
            messagebox.showwarning("Aviso", "Nenhum paciente selecionado.")
            return
        
        if exportar_paciente(self.paciente_atual):
            messagebox.showinfo("Sucesso", "Ficha do paciente exportada com sucesso!")
    
    # ========== OUTROS MÉTODOS ==========
    
    def _novo_diagnostico(self):
        """Inicia novo diagnóstico"""
        self._limpar_sintomas()
        self._limpar_resultados()
        messagebox.showinfo("Novo Diagnóstico", "Pronto para novo diagnóstico. Selecione os sintomas.")
    
    def _mostrar_estatisticas(self):
        """Mostra estatísticas do sistema"""
        stats = self.db.get_estatisticas()
        info = f"""ESTATÍSTICAS DO SISTEMA:

PACIENTES:
Total: {stats['pacientes']['total']}
Ativos: {stats['pacientes']['ativos']}
Inativos: {stats['pacientes']['inativos']}
Homens: {stats['pacientes']['homens']}
Mulheres: {stats['pacientes']['mulheres']}

DIAGNÓSTICOS:
Total realizados: {stats['diagnosticos']['total']}
Último mês: {stats['diagnosticos']['ultimo_mes']}

DOENÇAS NO BANCO DE DADOS:
Total: {stats['doencas']['total']}
Físicas: {stats['doencas']['fisicas']}
Psicológicas: {stats['doencas']['psicologicas']}

SINTOMAS ÚNICOS: {len(self.db.obter_sintomas_unicos())}
"""
        messagebox.showinfo("Estatísticas", info)
    
    def _sobre(self):
        """Mostra informações sobre o sistema"""
        stats = self.db.get_estatisticas()
        about_text = f"""Sistema de Diagnóstico Médico - Versão 2.0

Desenvolvido para auxílio diagnóstico médico.
Integra cadastro de pacientes com sistema de diagnóstico.

ESTATÍSTICAS ATUAIS:
- {stats['pacientes']['total']} pacientes cadastrados
- {stats['doencas']['total']} doenças no banco de dados
- {stats['diagnosticos']['total']} diagnósticos realizados

FUNCIONALIDADES:
✓ Cadastro completo de pacientes
✓ Diagnóstico com múltiplas doenças
✓ Histórico de diagnósticos
✓ Exportação de relatórios
✓ Backups automáticos

© 2024 - Sistema para uso médico
"""
        messagebox.showinfo("Sobre o Sistema", about_text)
    
    def run(self):
        """Executa a aplicação"""
        self.root.mainloop()

# ========== PONTO DE ENTRADA ==========

if __name__ == "__main__":
    app = App()
    app.run()