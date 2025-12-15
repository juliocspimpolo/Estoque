import customtkinter as ctk
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import tkinter.messagebox as messagebox
import sys
from tkinter import filedialog
from tkinter import Toplevel
from pathlib import Path

# Definir o tema do aplicativo
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Conexão com a Planilha do Google Sheets ---
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    credentials_file = 'credenciais.json'
    if not Path(credentials_file).is_file():
        raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {credentials_file}")

    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    
    spreadsheet_name = 'Controle_Estoque_iMotion'
    spreadsheet = client.open(spreadsheet_name)
    
    planilha = spreadsheet.sheet1
    historico = spreadsheet.worksheet('Historico')
    usuarios_sheet = spreadsheet.worksheet('Usuarios')
    logistica_sheet = spreadsheet.worksheet('Logistica')
    fornecedores_sheet = spreadsheet.worksheet('Fornecedores')
    montagem_sheet = spreadsheet.worksheet('Montagem Esteira')
    visits_sheet = spreadsheet.worksheet('Visitas') 

except gspread.exceptions.SpreadsheetNotFound:
    print(f"Erro: Planilha '{spreadsheet_name}' não encontrada.")
    sys.exit()
except FileNotFoundError as e:
    print(f"Erro: {e}.")
    sys.exit()
except Exception as e:
    print(f"Erro de conexão: {e}")
    sys.exit()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # As instâncias das planilhas
        self.planilha = planilha
        self.historico = historico
        self.usuarios_sheet = usuarios_sheet
        self.logistica_sheet = logistica_sheet
        self.fornecedores_sheet = fornecedores_sheet
        self.montagem_sheet = montagem_sheet
        self.visits_sheet = visits_sheet
        
        self.edit_row_number = None
        self.user_role = None
        self.current_user = None
        self.checklist_data = {}
        self.assembly_frame_scroll = None
        self.checklist_headers_map = {}
        self.fullscreen_state = False

        # Configurações da janela principal
        self.title("Controle de Estoque I-Motion")
        self.geometry("1100x750")
        self.resizable(True, True)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- 1. CRIAÇÃO DOS FRAMES (LIMPEZA TOTAL) ---
        self.login_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.home_frame = ctk.CTkFrame(self, corner_radius=0)
        
        # Frames Funcionais
        self.list_stock_frame = ctk.CTkFrame(self, corner_radius=0) # Painel Principal
        # (Search frame removido pois foi integrado)
        self.logistics_frame = ctk.CTkFrame(self, corner_radius=0)
        self.suppliers_frame = ctk.CTkFrame(self, corner_radius=0) 
        self.export_frame = ctk.CTkFrame(self, corner_radius=0)
        self.assembly_frame = ctk.CTkFrame(self, corner_radius=0)
        self.visits_frame = ctk.CTkFrame(self, corner_radius=0) 
        self.user_management_frame = ctk.CTkFrame(self, corner_radius=0)
        
        # Frames LEGADOS removidos da criação para limpar memória e código
        # (add_frame, search_frame, remove_frame, edit_frame, withdraw_frame foram deletados)

        # --- 2. CONFIGURAÇÃO DE TODOS OS WIDGETS ---
        
        # --- Layout do Dashboard (Início) ---
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_rowconfigure(0, weight=1)
        self.dashboard_label = ctk.CTkLabel(self.home_frame, text="Dashboard de Resumo", font=ctk.CTkFont(size=22, weight="bold"))
        self.dashboard_label.grid(row=0, column=0, padx=20, pady=20, sticky="n")

        self.total_stock_value_label = ctk.CTkLabel(self.home_frame, text="Valor Total: R$ 0.00", font=ctk.CTkFont(size=16))
        self.total_stock_value_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        self.low_stock_count_label = ctk.CTkLabel(self.home_frame, text="Estoque Baixo: 0", font=ctk.CTkFont(size=16))
        self.low_stock_count_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        self.total_items_count_label = ctk.CTkLabel(self.home_frame, text="Total Itens: 0", font=ctk.CTkFont(size=16))
        self.total_items_count_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.low_stock_list_label = ctk.CTkLabel(self.home_frame, text="5 Itens com Menor Estoque:", font=ctk.CTkFont(size=16, weight="bold"))
        self.low_stock_list_label.grid(row=4, column=0, padx=20, pady=(30, 10), sticky="w")
        self.low_stock_list_text = ctk.CTkTextbox(self.home_frame, height=150)
        self.low_stock_list_text.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")

        # --- Layout da Tela de Login ---
        self.login_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.login_frame, text="Login", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(150, 10))
        self.user_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Usuário", width=250)
        self.user_entry.grid(row=1, column=0, padx=20, pady=10)
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Senha", show="*", width=250)
        self.password_entry.grid(row=2, column=0, padx=20, pady=10)
        ctk.CTkButton(self.login_frame, text="Entrar", command=self.login, width=250).grid(row=3, column=0, padx=20, pady=(20, 150))
        
        # --- Menu de Navegação (LIMPO) ---
        self.navigation_frame.grid_remove()
        ctk.CTkLabel(self.navigation_frame, text="Menu", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Início", command=lambda: self.select_frame_by_name("Início"))
        self.home_button.grid(row=1, column=0, sticky="ew")

        # Botão Principal de Estoque
        self.list_stock_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="📦 Gerenciar Estoque", command=lambda: self.select_frame_by_name("Listar Estoque"))
        self.list_stock_button.grid(row=2, column=0, sticky="ew")

        # (Botão "Buscar Item" REMOVIDO DAQUI - Agora está integrado no painel de estoque)
        
        self.logistics_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Logística", command=lambda: self.select_frame_by_name("Logística"))
        self.logistics_button.grid(row=4, column=0, sticky="ew")
        
        self.suppliers_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Gerenciar Fornecedores", command=lambda: self.select_frame_by_name("Fornecedores"))
        self.suppliers_button.grid(row=5, column=0, sticky="ew")
        
        self.assembly_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Checklist de Montagem", command=lambda: self.select_frame_by_name("Montagem"))
        self.assembly_button.grid(row=6, column=0, sticky="ew")

        self.visits_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Visitas Técnicas", command=lambda: self.select_frame_by_name("Visitas"))
        self.visits_button.grid(row=7, column=0, sticky="ew") 
        
        self.export_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Exportar Dados", command=lambda: self.select_frame_by_name("Exportar"))
        self.export_button.grid(row=8, column=0, sticky="ew")
        
        self.user_management_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Gerenciar Usuários", command=lambda: self.select_frame_by_name("Gerenciar Usuários"))
        self.user_management_button.grid(row=9, column=0, sticky="ew")

        self.spacer = ctk.CTkLabel(self.navigation_frame, text="")
        self.spacer.grid(row=10, column=0, sticky="ew", pady=50)

        self.exit_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, text="Sair", command=self.logout)
        self.exit_button.grid(row=11, column=0, sticky="ew")
        
        # --- 3. PAINEL DE ESTOQUE INTERATIVO COM BUSCA INTEGRADA ---
        self.list_stock_frame.grid_columnconfigure(0, weight=1)
        self.list_stock_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.list_stock_frame, text="Gerenciamento de Estoque", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w", columnspan=2)

        # Barra de Ferramentas Superior (Busca + Ações)
        self.toolbar_frame = ctk.CTkFrame(self.list_stock_frame, fg_color="transparent")
        self.toolbar_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        
        # Grid da Toolbar: 0=Busca Entry, 1=Btn Busca, 2=Btn Refresh, 3=Btn Novo
        self.toolbar_frame.grid_columnconfigure(0, weight=3) # A barra de busca ocupa mais espaço
        self.toolbar_frame.grid_columnconfigure(1, weight=0)
        self.toolbar_frame.grid_columnconfigure(2, weight=0)
        self.toolbar_frame.grid_columnconfigure(3, weight=0)

        # 💡 Campo de Busca Integrado
        self.stock_search_entry = ctk.CTkEntry(self.toolbar_frame, placeholder_text="🔍 Buscar item por Nome ou Código...")
        self.stock_search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Botão de Lupa (Buscar)
        self.btn_search_stock = ctk.CTkButton(self.toolbar_frame, text="Buscar", width=80, command=lambda: self.refresh_stock_list(self.stock_search_entry.get()))
        self.btn_search_stock.grid(row=0, column=1, padx=(0, 10))

        # Botão Atualizar (Limpa busca)
        self.btn_refresh = ctk.CTkButton(self.toolbar_frame, text="🔄 Todos", width=80, command=lambda: [self.stock_search_entry.delete(0, 'end'), self.refresh_stock_list()])
        self.btn_refresh.grid(row=0, column=2, padx=(0, 10))

        # Botão Adicionar (Pop-up)
        self.btn_add_new = ctk.CTkButton(self.toolbar_frame, text="➕ Novo Item", fg_color="green", width=120, command=self.open_add_item_window)
        self.btn_add_new.grid(row=0, column=3, sticky="e")
        
        # Lista Interativa (Scrollable Frame)
        self.stock_scroll_frame = ctk.CTkScrollableFrame(self.list_stock_frame, label_text="Itens Cadastrados")
        self.stock_scroll_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")
        self.stock_scroll_frame.grid_columnconfigure(0, weight=1); self.stock_scroll_frame.grid_columnconfigure(1, weight=0)
        self.stock_scroll_frame.grid_columnconfigure(2, weight=0); self.stock_scroll_frame.grid_columnconfigure(3, weight=0)
# --- Layout do Novo Frame de Logística com Abas (RESTAURADO) ---
        self.logistics_frame.grid_columnconfigure(0, weight=1)
        self.logistics_frame.grid_rowconfigure(0, weight=1)

        self.logistics_tabview = ctk.CTkTabview(self.logistics_frame)
        self.logistics_tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.log_register_tab = self.logistics_tabview.add("Registro de Movimentação")
        self.log_history_tab = self.logistics_tabview.add("Histórico de Logística")

        self.log_register_tab.grid_columnconfigure((0, 1), weight=1)
        
        self.shipment_frame = ctk.CTkFrame(self.log_register_tab)
        self.shipment_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.shipment_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.shipment_frame, text="REGISTRO DE ENVIO", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=10)
        
        self.shipment_item_entry = ctk.CTkEntry(self.shipment_frame, placeholder_text="Tipo Item/Descrição (Ex: Notebook)")
        self.shipment_item_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.shipment_qty_entry = ctk.CTkEntry(self.shipment_frame, placeholder_text="Quantidade")
        self.shipment_qty_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.shipment_date_entry = ctk.CTkEntry(self.shipment_frame, placeholder_text="Data (DD/MM/AAAA)")
        self.shipment_date_entry.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.shipment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        self.shipment_responsible_entry = ctk.CTkEntry(self.shipment_frame, placeholder_text="Responsável pelo Envio")
        self.shipment_responsible_entry.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        self.shipment_details_entry = ctk.CTkTextbox(self.shipment_frame, height=100)
        self.shipment_details_entry.insert("0.0", "Detalhes do Pacote/Destinatário...")
        self.shipment_details_entry.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(self.shipment_frame, text="Registrar ENVIO", command=self.log_shipment).grid(row=6, column=0, padx=20, pady=10)

        self.receipt_frame = ctk.CTkFrame(self.log_register_tab)
        self.receipt_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.receipt_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.receipt_frame, text="REGISTRO DE RECEBIMENTO", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=10)

        self.receipt_item_entry = ctk.CTkEntry(self.receipt_frame, placeholder_text="Tipo Item/Descrição (Ex: Caixa de Cabos)")
        self.receipt_item_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.receipt_date_entry = ctk.CTkEntry(self.receipt_frame, placeholder_text="Data (DD/MM/AAAA)")
        self.receipt_date_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.receipt_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        self.receipt_responsible_entry = ctk.CTkEntry(self.receipt_frame, placeholder_text="Responsável pelo Recebimento")
        self.receipt_responsible_entry.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        self.receipt_details_entry = ctk.CTkTextbox(self.receipt_frame, height=150)
        self.receipt_details_entry.insert("0.0", "Detalhes do Pacote/Remetente...")
        self.receipt_details_entry.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(self.receipt_frame, text="Registrar RECEBIMENTO", command=self.log_receipt).grid(row=5, column=0, padx=20, pady=10)

        self.log_history_tab.grid_columnconfigure(0, weight=1)
        
        self.log_history_filter_frame = ctk.CTkFrame(self.log_history_tab)
        self.log_history_filter_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        self.log_history_filter_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.log_search_entry = ctk.CTkEntry(self.log_history_filter_frame, placeholder_text="Buscar Item/Responsável/Detalhes")
        self.log_search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.log_type_combobox = ctk.CTkComboBox(self.log_history_filter_frame, values=["Todos", "Envio", "Recebimento"])
        self.log_type_combobox.set("Todos")
        self.log_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.log_date_from = ctk.CTkEntry(self.log_history_filter_frame, placeholder_text="Data De (DD/MM/AAAA)")
        self.log_date_from.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.log_date_to = ctk.CTkEntry(self.log_history_filter_frame, placeholder_text="Data Até (DD/MM/AAAA)")
        self.log_date_to.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(self.log_history_filter_frame, text="Buscar Histórico", command=self.list_logistics_history).grid(row=0, column=4, padx=5, pady=5)

        self.log_history_result_text = ctk.CTkTextbox(self.log_history_tab, height=500, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_history_result_text.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # --- Layout do Gerenciamento de Usuários (RESTAURADO) ---
        self.user_management_frame.grid_columnconfigure(0, weight=1)
        self.user_management_label = ctk.CTkLabel(self.user_management_frame, text="Gerenciar Usuários", font=ctk.CTkFont(size=18, weight="bold"))
        self.user_management_label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.new_user_entry = ctk.CTkEntry(self.user_management_frame, placeholder_text="Novo Usuário")
        self.new_user_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.new_password_entry = ctk.CTkEntry(self.user_management_frame, placeholder_text="Senha")
        self.new_password_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.new_role_combobox = ctk.CTkComboBox(self.user_management_frame, values=["editor", "visualizador", "admin"])
        self.new_role_combobox.set("editor")
        self.new_role_combobox.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.add_user_button = ctk.CTkButton(self.user_management_frame, text="Adicionar Usuário", command=self.add_user)
        self.add_user_button.grid(row=4, column=0, padx=20, pady=10)

        self.user_list_text = ctk.CTkTextbox(self.user_management_frame, height=200)
        self.user_list_text.grid(row=5, column=0, padx=20, pady=(10, 5), sticky="nsew")

        self.remove_user_entry = ctk.CTkEntry(self.user_management_frame, placeholder_text="Usuário para Remover")
        self.remove_user_entry.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        self.remove_user_button = ctk.CTkButton(self.user_management_frame, text="Remover Usuário", command=self.remove_user)
        self.remove_user_button.grid(row=7, column=0, padx=20, pady=10)

        # --- Layout do Gerenciamento de Fornecedores (RESTAURADO) ---
        self.suppliers_frame.grid_columnconfigure(0, weight=1)
        self.suppliers_frame.grid_rowconfigure(0, weight=1)

        self.suppliers_tabview = ctk.CTkTabview(self.suppliers_frame, command=self.supplier_tab_changed)
        self.suppliers_tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.sup_item_tab = self.suppliers_tabview.add("Gerenciar por Item")
        self.sup_general_tab = self.suppliers_tabview.add("Lista Geral de Fornecedores")

        self.sup_item_tab.grid_columnconfigure(0, weight=1)
        self.sup_item_tab.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sup_item_tab, text="Gerenciamento de Fornecedores por Item", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.supplier_search_entry = ctk.CTkEntry(self.sup_item_tab, placeholder_text="Digite o Código do Item (Ex: BORRACHA)")
        self.supplier_search_entry.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        ctk.CTkButton(self.sup_item_tab, text="Buscar Item e Fornecedores", command=self.find_item_for_supplier).grid(row=2, column=0, padx=20, pady=5)

        self.supplier_details_frame = ctk.CTkFrame(self.sup_item_tab)
        self.supplier_details_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.supplier_details_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.supplier_details_frame, text="Cadastrar Novo Fornecedor", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5))
        self.supplier_item_code = ctk.CTkLabel(self.supplier_details_frame, text="Item: N/A", font=ctk.CTkFont(size=14, weight="bold"))
        self.supplier_item_code.grid(row=1, column=0, padx=20, pady=(0, 10))

        self.supplier_name_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Nome do Fornecedor")
        self.supplier_name_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.supplier_phone_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Telefone")
        self.supplier_phone_entry.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.supplier_address_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Endereço")
        self.supplier_address_entry.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        self.supplier_website_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Site/E-mail")
        self.supplier_website_entry.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.supplier_price_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Preço de Compra (R$)")
        self.supplier_price_entry.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        self.supplier_date_entry = ctk.CTkEntry(self.supplier_details_frame, placeholder_text="Data da Compra (DD/MM/AAAA)")
        self.supplier_date_entry.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        self.supplier_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

        ctk.CTkButton(self.supplier_details_frame, text="Adicionar Fornecedor e Preço", command=self.add_supplier_to_item).grid(row=8, column=0, padx=20, pady=10)

        ctk.CTkLabel(self.sup_item_tab, text="Histórico de Fornecedores e Preços:", font=ctk.CTkFont(size=16)).grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.supplier_history_scroll = ctk.CTkScrollableFrame(self.sup_item_tab, label_text="Clique em EDITAR para alterar um fornecedor.", height=150)
        self.supplier_history_scroll.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.supplier_history_scroll.grid_columnconfigure((0, 1), weight=1)
        
        self.sup_general_tab.grid_columnconfigure(0, weight=1)
        self.sup_general_tab.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sup_general_tab, text="Lista Geral de Fornecedores Cadastrados", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.all_suppliers_scroll = ctk.CTkScrollableFrame(self.sup_general_tab, label_text="Fornecedores (Nome Único)", label_font=ctk.CTkFont(size=14, weight="bold"))
        self.all_suppliers_scroll.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.all_suppliers_scroll.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(self.sup_general_tab, text="ATUALIZAR LISTA GERAL", command=self.list_all_suppliers).grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # --- Layout do Exportar Dados (RESTAURADO) ---
        self.export_frame.grid_columnconfigure(0, weight=1)
        self.export_label = ctk.CTkLabel(self.export_frame, text="Exportar Dados do Estoque (CSV)", font=ctk.CTkFont(size=20, weight="bold"))
        self.export_label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.export_button_stock = ctk.CTkButton(self.export_frame, text="EXPORTAR ESTOQUE PRINCIPAL (CSV)", command=self.export_stock_to_csv)
        self.export_button_stock.grid(row=1, column=0, padx=20, pady=10)
        
        self.export_button_logistics = ctk.CTkButton(self.export_frame, text="EXPORTAR LOGÍSTICA (CSV)", command=lambda: self.export_sheet_to_csv('Logistica'))
        self.export_button_logistics.grid(row=2, column=0, padx=20, pady=10)
        
        self.export_button_history = ctk.CTkButton(self.export_frame, text="EXPORTAR HISTÓRICO DE MOV. (CSV)", command=lambda: self.export_sheet_to_csv('Historico'))
        self.export_button_history.grid(row=3, column=0, padx=20, pady=10)
        
        # --- Layout do Frame de Montagem da Esteira (RESTAURADO) ---
        self.assembly_frame.grid_columnconfigure(0, weight=1)
        self.assembly_frame.grid_rowconfigure(0, weight=1)

        self.assembly_tabview = ctk.CTkTabview(self.assembly_frame)
        self.assembly_tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.asm_register_tab = self.assembly_tabview.add("Registro de Montagem")
        self.asm_history_tab = self.assembly_tabview.add("Acompanhamento e Histórico")

        self.asm_register_tab.grid_columnconfigure(0, weight=1)
        self.asm_register_tab.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.asm_register_tab, text="Checklist de Montagem de Equipamento", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.assembly_info_frame = ctk.CTkFrame(self.asm_register_tab)
        self.assembly_info_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.assembly_info_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.asm_cliente_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Nome Cliente")
        self.asm_cliente_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.asm_localizacao_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Localização Cliente")
        self.asm_localizacao_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.asm_tecnico_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Técnico Responsável")
        self.asm_tecnico_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.asm_item_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Item a ser Montado (Ex: Esteira X)")
        self.asm_item_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.asm_data_inicio_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Data Início Montagem")
        self.asm_data_inicio_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.asm_entrega_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Previsão Entrega")
        self.asm_entrega_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.asm_finalizacao_entry = ctk.CTkEntry(self.assembly_info_frame, placeholder_text="Data Finalização")
        self.asm_finalizacao_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.asm_finalizacao_entry.configure(state="disabled")

        ctk.CTkButton(self.assembly_info_frame, text="Carregar Checklist", command=self.load_assembly_checklist).grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        self.assembly_checklist_scroll = ctk.CTkScrollableFrame(self.asm_register_tab, label_text="Checklist (Aguardando Carregamento)", label_font=ctk.CTkFont(size=14, weight="bold"))
        self.assembly_checklist_scroll.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.assembly_checklist_scroll.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(self.asm_register_tab, text="SALVAR ANDAMENTO DA MONTAGEM", command=self.save_assembly_progress, fg_color="green").grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.asm_history_tab.grid_columnconfigure(0, weight=1)
        self.asm_history_tab.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.asm_history_tab, text="Projetos em Andamento / Histórico", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.assembly_progress_scroll = ctk.CTkScrollableFrame(self.asm_history_tab, label_text="Clique em um item para ver o detalhe", label_font=ctk.CTkFont(size=14, weight="bold"))
        self.assembly_progress_scroll.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.assembly_progress_scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(self.asm_history_tab, text="ATUALIZAR LISTA DE PROJETOS", command=self.list_assembly_progress).grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # --- Layout do Novo Frame de Visitas Técnicas (RESTAURADO) ---
        self.visits_frame.grid_columnconfigure(0, weight=1)
        self.visits_frame.grid_rowconfigure(9, weight=1) 

        ctk.CTkLabel(self.visits_frame, text="Agendar Nova Visita Técnica", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # Linha 1: Nome e Endereço
        visits_info_frame = ctk.CTkFrame(self.visits_frame)
        visits_info_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        visits_info_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.visits_client_name_entry = ctk.CTkEntry(visits_info_frame, placeholder_text="Nome Cliente/Empresa", width=250)
        self.visits_client_name_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.visits_street_entry = ctk.CTkEntry(visits_info_frame, placeholder_text="Rua/Avenida")
        self.visits_street_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.visits_number_entry = ctk.CTkEntry(visits_info_frame, placeholder_text="Número")
        self.visits_number_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Linha 2: Cidade/UF e CEP
        visits_address_frame = ctk.CTkFrame(self.visits_frame)
        visits_address_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        visits_address_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.visits_city_entry = ctk.CTkEntry(visits_address_frame, placeholder_text="Cidade")
        self.visits_city_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.visits_uf_entry = ctk.CTkEntry(visits_address_frame, placeholder_text="UF (Ex: SP)")
        self.visits_uf_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.visits_cep_entry = ctk.CTkEntry(visits_address_frame, placeholder_text="CEP (Ex: 00000-000)")
        self.visits_cep_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Linha 3: Equipamentos e Responsável
        visits_equip_frame = ctk.CTkFrame(self.visits_frame)
        visits_equip_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        visits_equip_frame.grid_columnconfigure((0, 1), weight=1)

        self.visits_equip_entry = ctk.CTkEntry(visits_equip_frame, placeholder_text="Equipamentos a serem reparados (Ex: Esteira X, Vácuo Y)")
        self.visits_equip_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.visits_responsible_combobox = ctk.CTkComboBox(visits_equip_frame, values=["Carregando Usuários..."])
        self.visits_responsible_combobox.set("Selecionar Técnico")
        self.visits_responsible_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Linha 4: Descrição do Problema
        ctk.CTkLabel(self.visits_frame, text="Descrição do Problema:", anchor="w").grid(row=4, column=0, padx=20, pady=(0, 5), sticky="w")
        self.visits_problem_text = ctk.CTkTextbox(self.visits_frame, height=100)
        self.visits_problem_text.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Linha 5: Data da Visita
        visits_date_frame = ctk.CTkFrame(self.visits_frame)
        visits_date_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        visits_date_frame.grid_columnconfigure(0, weight=1)
        
        self.visits_date_entry = ctk.CTkEntry(visits_date_frame, placeholder_text="Data da Visita (DD/MM/AAAA)")
        self.visits_date_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.visits_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Botão de Agendar
        ctk.CTkButton(self.visits_frame, text="AGENDAR VISITA TÉCNICA", command=self.schedule_visit, fg_color="#3498DB", hover_color="#2980B9").grid(row=7, column=0, padx=20, pady=(10, 20), sticky="ew")

        # Linha 8: Área de Histórico/Acompanhamento (ScrollableFrame)
        ctk.CTkLabel(self.visits_frame, text="Visitas Agendadas e Concluídas:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=8, column=0, padx=20, pady=(0, 5), sticky="w")
        self.visits_history_scroll = ctk.CTkScrollableFrame(self.visits_frame, label_text="Histórico de Agendamentos", label_font=ctk.CTkFont(size=14))
        self.visits_history_scroll.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.visits_history_scroll.grid_columnconfigure((0, 1, 2), weight=1) 

        self.select_frame_by_name("Login")
# ====================================================================
    # 💡 MÉTODOS DE TELA E NAVEGAÇÃO
    # ====================================================================
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen_state = not self.fullscreen_state
        self.attributes("-fullscreen", self.fullscreen_state)
        return "break"

    def end_fullscreen(self, event=None):
        self.fullscreen_state = False
        self.attributes("-fullscreen", False)
        return "break"

    # --- MÉTODOS UTILITÁRIOS (COLOCADOS AQUI PARA EVITAR ERRO DE INICIALIZAÇÃO) ---
    
    def supplier_tab_changed(self, tab_name):
        """Método chamado ao mudar de aba na visualização de fornecedores."""
        if tab_name == "Lista Geral de Fornecedores":
            self.list_all_suppliers()

    def get_users_list(self):
        """Busca a lista de usuários para preencher ComboBoxes."""
        try:
            users_data = self.usuarios_sheet.col_values(1)[1:] 
            return users_data
        except Exception:
            return ["Erro ao carregar usuários"]

    # --- NAVEGAÇÃO (LIMPA - SEM ABAS ANTIGAS) ---

    def select_frame_by_name(self, frame_name):
        # Esconde todos os frames ativos (Sem os antigos)
        for frame in [self.login_frame, self.navigation_frame, self.home_frame, 
                      self.user_management_frame, self.list_stock_frame, self.logistics_frame, 
                      self.suppliers_frame, self.export_frame, self.assembly_frame, self.visits_frame]:
            frame.grid_forget()

        if frame_name == "Login": self.login_frame.grid(row=0, column=0, columnspan=2, sticky="nsew"); return
        
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        
        if frame_name == "Início": 
            self.home_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.update_dashboard()
        
        # 💡 LISTA INTERATIVA
        elif frame_name == "Listar Estoque": 
            self.list_stock_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.refresh_stock_list() 
            
        # (Aba Buscar removida da seleção visual, mas mantida no código por segurança)

        elif frame_name == "Logística": 
            self.logistics_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            if self.logistics_tabview.get() == "Histórico de Logística": self.list_logistics_history()
        
        elif frame_name == "Fornecedores":
            self.suppliers_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.supplier_search_entry.delete(0, 'end')
            self.supplier_item_code.configure(text="Item: N/A")
            for widget in self.supplier_history_scroll.winfo_children(): widget.destroy()
            if self.suppliers_tabview.get() == "Lista Geral de Fornecedores": self.list_all_suppliers()
        
        elif frame_name == "Montagem": 
            self.assembly_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.asm_tecnico_entry.delete(0, 'end')
            self.asm_tecnico_entry.insert(0, self.current_user if self.current_user else "")
            self.asm_data_inicio_entry.delete(0, 'end')
            self.asm_data_inicio_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
            if self.assembly_tabview.get() == "Acompanhamento e Histórico": self.list_assembly_progress()
            
        elif frame_name == "Visitas": 
            self.visits_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            try: self.visits_responsible_combobox.configure(values=self.get_users_list())
            except: pass
            self.list_visits_history()
            
        elif frame_name == "Exportar": 
            self.export_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        elif frame_name == "Gerenciar Usuários": 
            self.user_management_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.update_user_list()

    # --- LOGIN E USUÁRIOS ---
    def login(self):
        try:
            u = self.user_entry.get().strip(); p = self.password_entry.get().strip()
            users = self.usuarios_sheet.get_all_records(); found = False
            for user in users:
                if user['Usuario'] == u and str(user['Senha']) == p:
                    self.user_role = user['Cargo']; self.current_user = u; found = True; break
            if found:
                messagebox.showinfo("Sucesso", f"Bem-vindo, {self.current_user}!")
                self.configure_ui_for_role()
                self.select_frame_by_name("Início")
            else: messagebox.showerror("Erro", "Login inválido.")
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def logout(self):
        self.user_role = None; self.current_user = None; self.select_frame_by_name("Login")
        self.user_entry.delete(0, 'end'); self.password_entry.delete(0, 'end')

    def configure_ui_for_role(self):
        is_auth = self.user_role in ['admin', 'editor']
        self.btn_add_new.configure(state="normal" if is_auth else "disabled") 
        if self.user_role == 'admin': self.user_management_button.grid()
        else: self.user_management_button.grid_remove()

    def update_user_list(self):
        self.user_list_text.delete("0.0", "end")
        try:
            for u in self.usuarios_sheet.get_all_records(): self.user_list_text.insert("end", f"{u['Usuario']} ({u['Cargo']})\n")
        except: pass

    def add_user(self):
        if self.user_role != 'admin': return
        try:
            self.usuarios_sheet.append_row([self.new_user_entry.get(), self.new_password_entry.get(), self.new_role_combobox.get()])
            messagebox.showinfo("Sucesso", "Usuário adicionado."); self.update_user_list()
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def remove_user(self):
        if self.user_role != 'admin': return
        u = self.remove_user_entry.get()
        try:
            cell = self.usuarios_sheet.find(u, in_column=1)
            if cell: self.usuarios_sheet.delete_rows(cell.row); self.update_user_list(); messagebox.showinfo("Sucesso", "Removido.")
        except: messagebox.showerror("Erro", "Não encontrado.")

    # --- DASHBOARD & GERAL ---
    def update_dashboard(self):
        try:
            df = pd.DataFrame(self.planilha.get_all_records())
            if not df.empty:
                df['Valor Total'] = pd.to_numeric(df['Valor Total'].astype(str).str.replace('R$','').str.replace(',','.'), errors='coerce').fillna(0)
                df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
                self.total_stock_value_label.configure(text=f"Valor Total: R$ {df['Valor Total'].sum():,.2f}")
                self.low_stock_count_label.configure(text=f"Estoque Baixo: {df[df['Quantidade'] < 5].shape[0]}")
                self.total_items_count_label.configure(text=f"Total Itens: {df.shape[0]}")
                self.low_stock_list_text.delete("0.0", "end")
                for _, r in df.sort_values('Quantidade').head(5).iterrows(): self.low_stock_list_text.insert("end", f"{r['Nome do Item']}: {r['Quantidade']}\n")
        except: pass

    def log_movimentacao(self, codigo, nome, tipo, quantidade):
        try: self.historico.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), codigo, nome, tipo, quantidade, self.current_user])
        except: pass

    # ====================================================================
    # 🔥 NOVO PAINEL DE ESTOQUE (COM BUSCA INTEGRADA)
    # ====================================================================

    def refresh_stock_list(self, search_query=""):
        """Reconstroi a lista com filtro de busca opcional."""
        for widget in self.stock_scroll_frame.winfo_children(): widget.destroy()
        try:
            data = self.planilha.get_all_records()
            if not data: 
                ctk.CTkLabel(self.stock_scroll_frame, text="Nenhum item em estoque.").grid(row=0, column=0, padx=10, pady=10)
                return

            df = pd.DataFrame(data)
            
            # 🔥 Lógica de Filtro
            if search_query:
                term = search_query.lower()
                # Filtra se o termo está no Nome OU no Código
                df = df[df['Nome do Item'].astype(str).str.lower().str.contains(term) | 
                        df['Código do Item'].astype(str).str.lower().str.contains(term)]
                if df.empty:
                    ctk.CTkLabel(self.stock_scroll_frame, text="Nenhum item encontrado.").grid(row=0, column=0)
                    return

            is_auth = self.user_role in ['admin', 'editor']
            
            # Cabeçalho
            ctk.CTkLabel(self.stock_scroll_frame, text="ITEM / CÓDIGO", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10)
            ctk.CTkLabel(self.stock_scroll_frame, text="QTD", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10)
            ctk.CTkLabel(self.stock_scroll_frame, text="AÇÕES", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, columnspan=2, sticky="w", padx=10)
            
            r = 1
            for idx, row in df.iterrows():
                info = f"{row['Nome do Item']}\n({row['Código do Item']})"
                qty = row['Quantidade']
                # Pega o índice original na planilha para edição (índice do DF não é confiável após filtro)
                # Como get_all_records devolve lista, assumimos que a ordem inicial é preservada. 
                # Melhor estratégia: buscar o índice pelo código único para segurança absoluta.
                try:
                    cell = self.planilha.find(row['Código do Item'], in_column=1)
                    sheet_row = cell.row
                except:
                    continue # Se não achar (estranho), pula
                
                ctk.CTkLabel(self.stock_scroll_frame, text=info, anchor="w", justify="left").grid(row=r, column=0, sticky="ew", padx=10, pady=5)
                
                try: min_stock = int(row['Estoque Mínimo']); qty_val = int(qty); color = "#E74C3C" if qty_val < min_stock else "white" 
                except: color = "white"

                ctk.CTkLabel(self.stock_scroll_frame, text=str(qty), text_color=color, font=ctk.CTkFont(weight="bold")).grid(row=r, column=1, padx=10)
                
                if is_auth:
                    ctk.CTkButton(self.stock_scroll_frame, text="✏️", width=40, fg_color="#2980B9", 
                                  command=lambda d=row.to_dict(), sr=sheet_row: self.open_quick_edit_window(d, sr)).grid(row=r, column=2, padx=5, pady=2)
                    ctk.CTkButton(self.stock_scroll_frame, text="🗑️", width=40, fg_color="#C0392B", 
                                  command=lambda sr=sheet_row, c=row['Código do Item']: self.delete_item_from_list(sr, c)).grid(row=r, column=3, padx=5, pady=2)
                
                ctk.CTkFrame(self.stock_scroll_frame, height=1, fg_color="gray").grid(row=r+1, column=0, columnspan=4, sticky="ew", pady=5)
                r += 2
        except Exception as e: messagebox.showerror("Erro Lista", f"Falha ao carregar lista: {e}")

    def open_add_item_window(self):
        if self.user_role not in ['admin', 'editor']: return
        win = ctk.CTkToplevel(self); win.geometry("400x600"); win.grab_set(); win.title("Novo Item")
        entries = {}; fields = ["Código", "Nome", "Fornecedor", "Data (DD/MM/AAAA)", "Quantidade", "Preço Unit.", "Estoque Mín.", "Localização"]
        ctk.CTkLabel(win, text="NOVO ITEM", font=ctk.CTkFont(weight="bold", size=18)).pack(pady=15)
        content = ctk.CTkScrollableFrame(win); content.pack(fill="both", expand=True, padx=10, pady=10)

        for f in fields:
            ctk.CTkLabel(content, text=f + ":", anchor="w").pack(padx=10, fill="x")
            e = ctk.CTkEntry(content); e.pack(padx=10, fill="x", pady=(0, 10)); entries[f] = e
            if "Data" in f: e.insert(0, datetime.now().strftime("%d/%m/%Y"))
            
        def save_new():
            try:
                if not entries["Código"].get() or not entries["Nome"].get(): raise ValueError("Código e Nome obrigatórios.")
                qtd = int(entries["Quantidade"].get() or 0); prc = float(entries["Preço Unit."].get().replace(',', '.') or 0.0)
                row = [entries["Código"].get().upper(), entries["Nome"].get(), entries["Fornecedor"].get(), entries["Data (DD/MM/AAAA)"].get(),
                       qtd, prc, int(entries["Estoque Mín."].get() or 0), qtd * prc, entries["Localização"].get(), datetime.now().strftime("%d/%m/%Y %H:%M")]
                self.planilha.append_row(row)
                self.log_movimentacao(row[0], row[1], "Entrada Inicial", qtd)
                messagebox.showinfo("Sucesso", "Item criado!"); win.destroy(); self.refresh_stock_list(); self.update_dashboard()
            except Exception as err: messagebox.showerror("Erro", f"{err}")
        ctk.CTkButton(win, text="SALVAR NOVO ITEM", fg_color="green", command=save_new).pack(pady=20)

    def open_quick_edit_window(self, data, sheet_row):
        win = ctk.CTkToplevel(self); win.geometry("400x500"); win.grab_set(); win.title(f"Editar: {data['Nome do Item']}")
        ctk.CTkLabel(win, text=f"Editando: {data['Código do Item']}", font=ctk.CTkFont(weight="bold", size=16)).pack(pady=10)
        ctk.CTkLabel(win, text=f"Estoque Atual: {data['Quantidade']}", text_color="cyan").pack(pady=5)
        
        ctk.CTkLabel(win, text="MUDANÇA DE QUANTIDADE (+/-):").pack(pady=(10,0))
        qty_change = ctk.CTkEntry(win, placeholder_text="Ex: 10 (entrada) ou -5 (saída)"); qty_change.pack(padx=20, fill="x")
        ctk.CTkLabel(win, text="PREÇO UNITÁRIO:").pack(pady=(5,0))
        price_entry = ctk.CTkEntry(win); price_entry.insert(0, str(data['Preço Unitário'])); price_entry.pack(padx=20, fill="x")
        ctk.CTkLabel(win, text="LOCALIZAÇÃO:").pack(pady=(5,0))
        location_entry = ctk.CTkEntry(win); location_entry.insert(0, str(data['Localização'])); location_entry.pack(padx=20, fill="x")

        def apply_change():
            try:
                chg = int(qty_change.get()) if qty_change.get() else 0
                prc = float(price_entry.get().strip().replace(',', '.')); new_q = int(data['Quantidade']) + chg
                if new_q < 0: messagebox.showerror("Erro", "Estoque negativo"); return
                self.planilha.update_cell(sheet_row, 5, new_q); self.planilha.update_cell(sheet_row, 6, prc)
                self.planilha.update_cell(sheet_row, 8, new_q * prc); self.planilha.update_cell(sheet_row, 9, location_entry.get())
                self.planilha.update_cell(sheet_row, 10, datetime.now().strftime("%d/%m/%Y %H:%M"))
                if chg != 0: self.log_movimentacao(data['Código do Item'], data['Nome do Item'], "Ajuste Rápido", abs(chg))
                messagebox.showinfo("Sucesso", "Atualizado!"); win.destroy(); self.refresh_stock_list(self.stock_search_entry.get()); self.update_dashboard()
            except Exception as e: messagebox.showerror("Erro", f"{e}")
        ctk.CTkButton(win, text="SALVAR ALTERAÇÕES", command=apply_change).pack(pady=30)

    def delete_item_from_list(self, sheet_row, code):
        if messagebox.askyesno("Confirmar", f"Apagar {code}?"):
            try: self.planilha.delete_rows(sheet_row); self.log_movimentacao(code, "ITEM EXCLUÍDO", "Exclusão", 0); self.refresh_stock_list(); self.update_dashboard()
            except Exception as e: messagebox.showerror("Erro", f"{e}")

    # --- MÉTODOS DE LOGÍSTICA (COMPLETO) ---
    def log_logistics(self, tipo, item, quantidade, data, responsavel, detalhes):
        try:
            qty = quantidade if quantidade is not None else 0
            self.logistica_sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tipo, item, qty, data, responsavel, detalhes.strip(), self.current_user])
            return True
        except Exception as e: messagebox.showerror("Erro", f"{e}"); return False

    def log_shipment(self):
        try:
            q = int(self.shipment_qty_entry.get()); 
            if q <= 0: raise ValueError
            if self.log_logistics("Envio", self.shipment_item_entry.get(), q, self.shipment_date_entry.get(), self.shipment_responsible_entry.get(), self.shipment_details_entry.get("0.0", "end")):
                messagebox.showinfo("Sucesso", "Envio registrado.")
                self.shipment_item_entry.delete(0, 'end'); self.shipment_qty_entry.delete(0, 'end')
        except: messagebox.showerror("Erro", "Verifique os dados.")

    def log_receipt(self):
        if self.log_logistics("Recebimento", self.receipt_item_entry.get(), 0, self.receipt_date_entry.get(), self.receipt_responsible_entry.get(), self.receipt_details_entry.get("0.0", "end")):
            messagebox.showinfo("Sucesso", "Recebimento registrado.")
            self.receipt_item_entry.delete(0, 'end')

    def list_logistics_history(self):
        self.log_history_result_text.delete("0.0", "end")
        try:
            df = pd.DataFrame(self.logistica_sheet.get_all_records())
            if df.empty: self.log_history_result_text.insert("end", "Vazio."); return
            self.log_history_result_text.insert("end", df.to_string())
        except: pass

    # --- MÉTODOS DE FORNECEDORES (COMPLETO) ---
    def find_item_for_supplier(self):
        if self.user_role not in ['editor', 'admin']: return
        codigo = self.supplier_search_entry.get().strip().upper()
        for widget in self.supplier_history_scroll.winfo_children(): widget.destroy()
        self.supplier_item_code.configure(text="Item: N/A")
        if not codigo: return
        try:
            cell = self.planilha.find(codigo, in_column=1)
            if not cell: messagebox.showwarning("Aviso", "Item não encontrado."); return
            item_info = self.planilha.row_values(cell.row)
            self.supplier_item_code.configure(text=f"Item: {item_info[1]} (Cód: {codigo})")
            all_suppliers = self.fornecedores_sheet.get_all_records()
            if not all_suppliers: return
            df = pd.DataFrame(all_suppliers)
            history = df[df['Código do Item'].astype(str).str.upper() == codigo]
            if not history.empty:
                row_num = 0
                for index, row in history.iterrows():
                    s_data = row.to_dict(); s_data['Sheet Row'] = index + 2 
                    txt = f"{row['Nome do Fornecedor']} | R$ {float(row['Preço']):.2f} ({row['Data da Compra']})"
                    ctk.CTkLabel(self.supplier_history_scroll, text=txt).grid(row=row_num, column=0, padx=10, sticky="w")
                    ctk.CTkButton(self.supplier_history_scroll, text="EDITAR", width=60, command=lambda d=s_data: self.show_supplier_edit_window(d)).grid(row=row_num, column=1, padx=5)
                    row_num += 1
            else: ctk.CTkLabel(self.supplier_history_scroll, text="Nenhum fornecedor.").pack()
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def show_supplier_edit_window(self, data):
        win = ctk.CTkToplevel(self); win.geometry("400x500"); win.grab_set()
        win.title("Editar Fornecedor")
        ctk.CTkLabel(win, text="Editar Fornecedor", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(win, text="Nome:").pack(); name = ctk.CTkEntry(win); name.insert(0, data.get('Nome do Fornecedor', '')); name.pack()
        ctk.CTkLabel(win, text="Telefone:").pack(); phone = ctk.CTkEntry(win); phone.insert(0, data.get('Telefone', '')); phone.pack()
        ctk.CTkLabel(win, text="Preço:").pack(); price = ctk.CTkEntry(win); price.insert(0, str(data.get('Preço', ''))); price.pack()
        def save():
            try:
                r = data['Sheet Row']
                self.fornecedores_sheet.update_cell(r, 2, name.get()) 
                self.fornecedores_sheet.update_cell(r, 3, phone.get()) 
                self.fornecedores_sheet.update_cell(r, 6, float(price.get().replace(',', '.'))) 
                messagebox.showinfo("Sucesso", "Atualizado!")
                win.destroy(); self.find_item_for_supplier()
            except Exception as e: messagebox.showerror("Erro", f"{e}")
        ctk.CTkButton(win, text="Salvar", command=save).pack(pady=20)

    def add_supplier_to_item(self):
        if self.user_role not in ['editor', 'admin']: return
        cod = self.supplier_search_entry.get().upper()
        if not cod or "N/A" in self.supplier_item_code.cget("text"): messagebox.showerror("Erro", "Busque um item."); return
        try:
            prc = float(self.supplier_price_entry.get().replace(',', '.'))
            row = [cod, self.supplier_name_entry.get(), self.supplier_phone_entry.get(), self.supplier_address_entry.get(),
                   self.supplier_website_entry.get(), prc, self.supplier_date_entry.get(), self.current_user, datetime.now().strftime("%d/%m/%Y")]
            self.fornecedores_sheet.append_row(row)
            messagebox.showinfo("Sucesso", "Adicionado."); self.find_item_for_supplier()
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def list_all_suppliers(self):
        for w in self.all_suppliers_scroll.winfo_children(): w.destroy()
        try:
            data = self.fornecedores_sheet.get_all_records()
            if not data: return
            df = pd.DataFrame(data).drop_duplicates(subset=['Nome do Fornecedor'])
            for _, row in df.iterrows():
                ctk.CTkLabel(self.all_suppliers_scroll, text=f"{row['Nome do Fornecedor']} - {row['Telefone']}").pack(anchor="w", padx=10)
        except: pass

    # --- VISITAS TÉCNICAS ---
    def schedule_visit(self):
        if self.user_role == 'visualizador': return
        try:
            row = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), self.visits_client_name_entry.get(), 
                   f"{self.visits_street_entry.get()}, {self.visits_number_entry.get()}",
                   self.visits_date_entry.get(), self.visits_responsible_combobox.get(),
                   self.visits_problem_text.get("0.0", "end").strip(), self.visits_equip_entry.get(),
                   "AGENDADA", self.current_user]
            self.visits_sheet.append_row(row)
            messagebox.showinfo("Sucesso", "Visita Agendada.")
            self.list_visits_history()
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def list_visits_history(self):
        for w in self.visits_history_scroll.winfo_children(): w.destroy()
        try:
            data = self.visits_sheet.get_all_records()
            if not data: 
                ctk.CTkLabel(self.visits_history_scroll, text="Nenhuma visita agendada.").pack()
                return
            
            df = pd.DataFrame(data)
            try: df = df.sort_values(by='Data Visita', ascending=False)
            except: pass

            self.visits_history_scroll.grid_columnconfigure(0, weight=1)
            r = 0
            for idx, row in df.iterrows():
                sheet_row = idx + 2
                status = row.get('Status', 'N/D')
                color = "green" if status == "CONCLUÍDA" else "#E67E22" if status == "AGENDADA" else "red"
                txt = f"[{status}] {row.get('Data Visita','')} - {row.get('Cliente','N/A')}"
                ctk.CTkLabel(self.visits_history_scroll, text=txt, text_color=color, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=r, column=0, sticky="ew", padx=10, pady=5)
                ctk.CTkButton(self.visits_history_scroll, text="Opções", width=70, height=25, fg_color="#2980B9",
                              command=lambda d=row.to_dict(), sr=sheet_row: self.show_visit_action_window(d, sr, 'AÇÃO')).grid(row=r, column=1, padx=10, pady=5)
                ctk.CTkFrame(self.visits_history_scroll, height=1, fg_color="gray").grid(row=r+1, column=0, columnspan=2, sticky="ew", pady=2)
                r += 2
        except Exception as e: print(f"Erro ao listar visitas: {e}")

    def show_visit_action_window(self, data, sheet_row, action):
        win = ctk.CTkToplevel(self); win.geometry("400x400"); win.grab_set()
        win.title(f"Gerenciar Visita")
        ctk.CTkLabel(win, text=f"Cliente: {data.get('Cliente')}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        status_var = ctk.StringVar(value=data.get('Status', 'AGENDADA'))
        ctk.CTkOptionMenu(win, variable=status_var, values=["AGENDADA", "CONCLUÍDA", "CANCELADA"]).pack(pady=10)
        def save():
            try:
                self.visits_sheet.update_cell(sheet_row, 8, status_var.get()) 
                messagebox.showinfo("Sucesso", "Status atualizado.")
                win.destroy(); self.list_visits_history()
            except Exception as e: messagebox.showerror("Erro", f"{e}")
        ctk.CTkButton(win, text="Salvar", command=save).pack(pady=20)
    
    def update_visit_data(self): pass 

    # --- EXPORTAÇÃO ---
    def export_sheet_to_csv(self, sheet_name):
        try:
            if sheet_name == 'Logistica': s = self.logistica_sheet
            elif sheet_name == 'Historico': s = self.historico
            else: s = self.planilha
            data = s.get_all_records()
            if not data: return
            df = pd.DataFrame(data)
            f = filedialog.asksaveasfilename(defaultextension=".csv")
            if f: df.to_csv(f, index=False, sep=';')
            messagebox.showinfo("Sucesso", "Exportado.")
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def export_stock_to_csv(self): self.export_sheet_to_csv('Controle_Estoque_iMotion')

    # --- MONTAGEM ---
    def ensure_assembly_headers(self, checklist_steps):
        base = ['Nome Cliente', 'Localização Cliente', 'Técnico Responsável', 'Item a ser Montado', 'Data Início', 'Entrega Prevista', 'Finalização Real', 'Status', 'Usuário Registro', 'Data/Hora Registro']
        check = [unique_id for _, _, unique_id in checklist_steps]
        full = base + check
        try:
            curr = self.montagem_sheet.row_values(1)
            if not curr: self.montagem_sheet.append_row(full)
        except: pass

    def load_assembly_checklist(self):
        if self.user_role != 'editor' and self.user_role != 'admin': return
        cliente = self.asm_cliente_entry.get().strip(); item = self.asm_item_entry.get().strip()
        if not cliente or not item: messagebox.showwarning("Atenção", "Preencha Cliente e Item."); return
        for w in self.assembly_checklist_scroll.winfo_children(): widget.destroy()
        self.checklist_data.clear()
        checklist_steps = [
            ("Componentes Básicos", "Fita LED Instalada e Funcionando", "BAS_01"),
            ("Componentes Básicos", "Fixação da Esteira na Carcaça (Cantoneira em L)", "BAS_02"),
            ("Componentes Básicos", "Borrachas (Porta)", "BAS_03"),
            ("Vácuo/Vedação", "Funcionamento do Vácuo (Teste de Pressão)", "VAC_01"),
            ("Vácuo/Vedação", "Filtro Vácuo Instalado", "VAC_02"),
            ("Vácuo/Vedação", "Grelha do Vácuo", "VAC_03"),
            ("Vácuo/Vedação", "Vedação (Geral)", "VAC_04"),
            ("Vácuo/Vedação", "Saia de vedação S", "VAC_05"),
            ("Vácuo/Vedação", "Saia de vedação M", "VAC_06"),
            ("Vácuo/Vedação", "Saia de vedação L", "VAC_07"),
            ("Acabamento/Estrutura", "Fixação do Ventilador (Esteira)", "ESTR_01"),
            ("Acabamento/Estrutura", "Grelhas Laterais", "ESTR_02"),
            ("Acabamento/Estrutura", "Braços (Fixação)", "ESTR_03"),
            ("Acabamento/Estrutura", "Trava de Engate Rápido (Interno Carcaça", "ESTR_04"),
            ("Acabamento/Estrutura", "Lâmpada Infravermelho", "ESTR_05"),
            ("Acabamento/Estrutura", "Lâmpada Colágeno", "ESTR_06"),
            ("Acabamento/Estrutura", "Chave de Segurança", "ESTR_07"),
            ("Acabamento/Estrutura", "Suporte Tela Mini Pc", "ESTR_08"),
            ("Acabamento/Estrutura", "Pintura (Acabamento e Limpeza)", "ESTR_09"),
            ("Acabamento/Estrutura", "Adesivos (Geral)", "ESTR_10"),
            ("Acabamento/Estrutura", "Tapete de Borracha (Porta)", "ESTR_11"),
            ("Fixação (Parafusos)", "Parafusos Janela Esquerda", "FIX_01"),
            ("Fixação (Parafusos)", "Parafusos Janela Direita", "FIX_02"),
            ("Fixação (Parafusos)", "Parafusos Degrau", "FIX_04"),
            ("Eletrônica / Controles", "Carregador USB-C", "ELEC_01"),
            ("Eletrônica / Controles", "Cabo padrão Brasil", "ELEC_02"),
            ("Eletrônica / Controles", "Caixa (Quadro de Energia)", "ELEC_03"),
            ("Eletrônica / Controles", "Mini Pc (Instalado e Config.)", "ELEC_04"),
            ("Eletrônica / Controles", "Tela Mini Pc (Conexão)", "ELEC_05"),
            ("Eletrônica / Controles", "Placa de Controle e Antena", "ELEC_06"),
            ("Eletrônica / Controles", "Kit Cabo Completo ShapeSpace", "ELEC_07"),
            ("Eletrônica / Controles", "Montagem Cabo Eletro Estimulação", "ELEC_08"),
            ("Eletrônica / Controles", "Montagem Cabo Manga (Conexão Esteira/Placa de controle)", "ELEC_09"),
            ("Eletrônica / Controles", "Placa V4 atualizada (MCI)", "ELEC_10"),
            ("Eletrônica / Controles", "IDR 16 A (sistema de segurança de corrente)", "ELEC_11"),
            ("Eletrônica / Controles", "Disjuntos Bipolar 16 A", "ELEC_12"),
            ("Eletrônica / Controles", "Fonte Energia EDR 120 - 12", "ELEC_13"),
            ("Eletrônica / Controles", "Conector Energia (Frontal)", "ELEC_14"),
            ("Acessórios (Inclusos)", "Pulsômetro", "ACESS_01"),
            ("Acessórios (Inclusos)", "Óculos (2)", "ACESS_02"),
            ("Acessórios (Inclusos)", "Óleo de Silicone", "ACESS_03"),
            ("Acessórios (Inclusos)", "Borrifador I-motion", "ACESS_04"),
            ("Aromaterapia", "Aromaterapia (ON/OFF))", "AROMA_01"),
            ("Aromaterapia", "Compressor Aromaterapia (ON/OFF)", "AROMA_02"),
            ("Bioshape (Trajes)", "Traje Bioshape S", "BIOS_01"),
            ("Bioshape (Trajes)", "Traje Bioshape M", "BIOS_02"),
            ("Bioshape (Trajes)", "Traje Bioshape L", "BIOS_03")
        ]
        self.checklist_headers_map = {unique_id: f"[{category}] - {description}" for category, description, unique_id in checklist_steps}
        found_progress = None
        try:
            dados = self.montagem_sheet.get_all_records()
            if dados:
                df = pd.DataFrame(dados)
                filtered = df[(df['Nome Cliente'] == cliente) & (df['Item a ser Montado'] == item)]
                if not filtered.empty:
                    found_progress = filtered.iloc[-1].to_dict()
                    self.asm_localizacao_entry.delete(0, 'end'); self.asm_localizacao_entry.insert(0, found_progress.get('Localização Cliente', ''))
                    self.asm_tecnico_entry.delete(0, 'end'); self.asm_tecnico_entry.insert(0, found_progress.get('Técnico Responsável', ''))
                    self.asm_data_inicio_entry.delete(0, 'end'); self.asm_data_inicio_entry.insert(0, found_progress.get('Data Início', ''))
                    self.asm_entrega_entry.delete(0, 'end'); self.asm_entrega_entry.insert(0, found_progress.get('Entrega Prevista', ''))
                    if found_progress.get('Finalização Real'): 
                        self.asm_finalizacao_entry.configure(state="normal")
                        self.asm_finalizacao_entry.delete(0, 'end')
                        self.asm_finalizacao_entry.insert(0, found_progress['Finalização Real'])
                        self.asm_finalizacao_entry.configure(state="disabled")
        except: pass
        row_num = 0
        for category, description, unique_id in checklist_steps:
            val = 1 if found_progress and str(found_progress.get(unique_id, '')).upper() == 'CONCLUÍDO' else 0
            var = ctk.IntVar(value=val)
            self.checklist_data[unique_id] = var
            ctk.CTkCheckBox(self.assembly_checklist_scroll, text=f"[{category}] - {description}", variable=var).grid(row=row_num, column=0, padx=10, pady=5, sticky="w")
            row_num += 1
        self.ensure_assembly_headers(checklist_steps)
        messagebox.showinfo("Carregado", "Checklist carregado.")

    def save_assembly_progress(self):
        if not self.checklist_data: return
        cliente = self.asm_cliente_entry.get().strip(); item = self.asm_item_entry.get().strip()
        info = [cliente, self.asm_localizacao_entry.get(), self.asm_tecnico_entry.get(), item, self.asm_data_inicio_entry.get(), self.asm_entrega_entry.get()]
        if not all(info): messagebox.showerror("Erro", "Preencha os dados do projeto."); return
        progress = ["CONCLUÍDO" if var.get() == 1 else "PENDENTE" for var in self.checklist_data.values()]
        all_done = all(var.get() == 1 for var in self.checklist_data.values())
        status = "FINALIZADO" if all_done else "EM ANDAMENTO"
        final_date = datetime.now().strftime("%d/%m/%Y") if all_done else ""
        row = info + [final_date, status, self.current_user, datetime.now().strftime("%d/%m/%Y %H:%M:%S")] + progress
        try:
            self.montagem_sheet.append_row(row)
            messagebox.showinfo("Sucesso", f"Salvo! Status: {status}")
        except Exception as e: messagebox.showerror("Erro", f"{e}")

    def list_assembly_progress(self):
        for w in self.assembly_progress_scroll.winfo_children(): w.destroy()
        try:
            data = self.montagem_sheet.get_all_records()
            if not data: return
            df = pd.DataFrame(data)
            r = 0
            for idx, row in df.iterrows():
                ctk.CTkLabel(self.assembly_progress_scroll, text=f"{row['Item a ser Montado']} ({row['Nome Cliente']}) - {row['Status']}").grid(row=r, column=0, padx=10, pady=2, sticky="w")
                ctk.CTkButton(self.assembly_progress_scroll, text="Ver Detalhes", command=lambda d=row.to_dict(): self.show_assembly_details(d)).grid(row=r, column=1)
                r += 1
        except: pass

    def show_assembly_details(self, data):
        win = ctk.CTkToplevel(self); win.geometry("600x600")
        scroll = ctk.CTkScrollableFrame(win); scroll.pack(fill="both", expand=True)
        for k, v in data.items():
            if k in self.checklist_headers_map or k in ['Nome Cliente', 'Status']:
                lbl = self.checklist_headers_map.get(k, k)
                color = "green" if str(v) == "CONCLUÍDO" else "white"
                ctk.CTkLabel(scroll, text=f"{lbl}: {v}", text_color=color).pack(anchor="w")

    # --- MÉTODOS LEGADOS ---
    def add_item(self): pass
    def search_item(self): 
        t = self.search_entry.get(); self.search_result_text.delete("0.0", "end")
        try:
            df = pd.DataFrame(self.planilha.get_all_records())
            res = df[df['Nome do Item'].str.contains(t, case=False, na=False)]
            self.search_result_text.insert("end", res.to_string())
        except: pass
    def remove_item(self): pass
    def find_item_for_edit(self): pass
    def update_item(self): pass
    def withdraw_item(self): pass
    def list_all_items(self): pass

if __name__ == "__main__":
    app = App()
    app.mainloop()