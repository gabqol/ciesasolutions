import tkinter as tk
from tkinter import ttk, messagebox
from helpdesk_djg import CentralDeSupporte, TransicaoInvalidaException

class HelpDeskGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ciesa Solutions - HelpDesk Pro Panel")
        self.root.geometry("850x600")
        self.root.configure(bg="#f4f6f9")

        self.central = CentralDeSupporte("Ciesa Solutions")
        self.configurar_dados_iniciais()

        self.estilo = ttk.Style()
        self.estilo.theme_use("clam")
        self.estilo.configure("TLabel", background="#f4f6f9", font=("Arial", 10))
        self.estilo.configure("Header.TLabel", font=("Arial", 14, "bold"), background="#f4f6f9", foreground="#2c3e50")
        self.estilo.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        
        self.criar_widgets()
        self.atualizar_tela()

    def configurar_dados_iniciais(self):
        self.central.registrar_tecnico("Julianne Diniz", ["Redes", "Windows"], capacidade_maxima=3)
        self.central.registrar_tecnico("Dymitre", ["Banco de Dados", "Linux"])
        self.central.registrar_tecnico("Carla Costa", ["Cloud"])
        
        self.central.abrir_chamado("Servidor instável", "Quedas constantes no banco", "Empresa Alfa", "critica")
        self.central.abrir_chamado("Impressora travada", "Papel preso no rolo", "Empresa Beta", "baixa")
        self.central.abrir_chamado("Erro de login no ERP", "Usuários sem acesso externo", "Empresa Gama", "alta")

    def criar_widgets(self):
        lbl_titulo = ttk.Label(self.root, text=f"Sistema de Gestão de Chamados - {self.central.empresa}", style="Header.TLabel")
        lbl_titulo.pack(pady=15)

        frame_cards = ttk.Frame(self.root, padding=10)
        frame_cards.pack(fill="x", padx=20)

        self.card_total = ttk.Frame(frame_cards, style="Card.TFrame", width=180, height=80)
        self.card_total.pack_propagate(False)
        self.card_total.pack(side="left", padx=10, expand=True)
        self.lbl_num_total = tk.Label(self.card_total, text="0", font=("Arial", 20, "bold"), bg="#ffffff", fg="#2980b9")
        self.lbl_num_total.pack(pady=(10,0))
        tk.Label(self.card_total, text="Total Ativos", bg="#ffffff", font=("Arial", 9)).pack()

        self.card_atraso = ttk.Frame(frame_cards, style="Card.TFrame", width=180, height=80)
        self.card_atraso.pack_propagate(False)
        self.card_atraso.pack(side="left", padx=10, expand=True)
        self.lbl_num_atraso = tk.Label(self.card_atraso, text="0", font=("Arial", 20, "bold"), bg="#ffffff", fg="#c0392b")
        self.lbl_num_atraso.pack(pady=(10,0))
        tk.Label(self.card_atraso, text="Em Atraso (SLA)", bg="#ffffff", font=("Arial", 9)).pack()

        self.card_tecs = ttk.Frame(frame_cards, style="Card.TFrame", width=180, height=80)
        self.card_tecs.pack_propagate(False)
        self.card_tecs.pack(side="left", padx=10, expand=True)
        self.lbl_num_tecs = tk.Label(self.card_tecs, text="0", font=("Arial", 20, "bold"), bg="#ffffff", fg="#27ae60")
        self.lbl_num_tecs.pack(pady=(10,0))
        tk.Label(self.card_tecs, text="Técnicos Livres", bg="#ffffff", font=("Arial", 9)).pack()

        frame_tabela = ttk.Frame(self.root, padding=10)
        frame_tabela.pack(fill="both", expand=True, padx=20, pady=15)

        colunas = ("numero", "titulo", "cliente", "prioridade", "status", "tecnico")
        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=10)
        
        self.tabela.heading("numero", text="Nº")
        self.tabela.heading("titulo", text="Título")
        self.tabela.heading("cliente", text="Cliente")
        self.tabela.heading("prioridade", text="Prioridade")
        self.tabela.heading("status", text="Status")
        self.tabela.heading("tecnico", text="Técnico ID")

        self.tabela.column("numero", width=60, anchor="center")
        self.tabela.column("titulo", width=220)
        self.tabela.column("cliente", width=130)
        self.tabela.column("prioridade", width=90, anchor="center")
        self.tabela.column("status", width=110, anchor="center")
        self.tabela.column("tecnico", width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame_acoes = ttk.LabelFrame(self.root, text=" Ações e Abertura Rápida ", padding=15)
        frame_acoes.pack(fill="x", padx=20, pady=(0, 20))

        ttk.Label(frame_acoes, text="Título:").grid(row=0, column=0, sticky="w", padx=5)
        self.ent_titulo = ttk.Entry(frame_acoes, width=20)
        self.ent_titulo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_acoes, text="Cliente:").grid(row=0, column=2, sticky="w", padx=5)
        self.ent_cliente = ttk.Entry(frame_acoes, width=15)
        self.ent_cliente.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_acoes, text="Prioridade:").grid(row=0, column=4, sticky="w", padx=5)
        self.cb_prioridade = ttk.Combobox(frame_acoes, values=["baixa", "media", "alta", "critica"], width=10, state="readonly")
        self.cb_prioridade.set("media")
        self.cb_prioridade.grid(row=0, column=5, padx=5, pady=5)

        btn_abrir = tk.Button(frame_acoes, text="+ Abrir Chamado", bg="#2980b9", fg="white", font=("Arial", 9, "bold"), command=self.evento_abrir_chamado)
        btn_abrir.grid(row=0, column=6, padx=15, pady=5)

        ttk.Separator(frame_acoes, orient="horizontal").grid(row=1, column=0, columnspan=7, sticky="ew", pady=10)

        btn_auto = tk.Button(frame_acoes, text="⚙ Rodar Atribuição Automática", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=self.evento_atribuicao_automatica)
        btn_auto.grid(row=2, column=0, columnspan=3, sticky="w", padx=5)

        btn_fechar = tk.Button(frame_acoes, text="✓ Finalizar/Fechar Selecionado", bg="#7f8c8d", fg="white", font=("Arial", 10, "bold"), command=self.evento_fechar_selecionado)
        btn_fechar.grid(row=2, column=4, columnspan=3, sticky="e", padx=5)

    def atualizar_tela(self):
        for item in self.tabela.get_children(): self.tabela.delete(item)
        for chamado in self.central.chamados.values():
            self.tabela.insert("", "end", values=(
                chamado.numero, chamado.titulo, chamado.cliente, chamado.prioridade.upper(),
                chamado.status.replace("_", " "), chamado.tecnico if chamado.tecnico else "Nenhum"
            ))
        dados_painel = self.central.painel_operacional()
        ativos = sum(v for k, v in dados_painel["totais_por_status"].items() if k not in ['resolvido', 'fechado'])
        self.lbl_num_total.config(text=str(ativos))
        self.lbl_num_atraso.config(text=str(dados_painel["total_em_atraso"]))
        self.lbl_num_tecs.config(text=str(dados_painel["tecnicos_disponiveis"]))

    def evento_abrir_chamado(self):
        t, c, p = self.ent_titulo.get().strip(), self.ent_cliente.get().strip(), self.cb_prioridade.get()
        if not t or not c:
            messagebox.showwarning("Campos Vazios", "Preencha o Título e o Cliente.")
            return
        novo = self.central.abrir_chamado(t, "Tkinter GUI", c, p)
        messagebox.showinfo("Sucesso", f"Chamado #{novo.numero} aberto!")
        self.ent_titulo.delete(0, tk.END)
        self.ent_cliente.delete(0, tk.END)
        self.atualizar_tela()

    def evento_atribuicao_automatica(self):
        qtd, atribuidos = self.central.atribuicao_automatica()
        messagebox.showinfo("Resultado", f"{qtd} chamados atribuídos. IDs: {atribuidos}")
        self.atualizar_tela()

    def evento_fechar_selecionado(self):
        item = self.tabela.selection()
        if not item: return
        num = int(self.tabela.item(item)['values'][0])
        try:
            chamado = self.central.buscar_chamado(num)
            if chamado.status in ['aberto', 'aguardando_cliente']: chamado.status = 'em_atendimento'
            if chamado.status == 'em_atendimento': chamado.status = 'resolvido'
            self.central.fechar_chamado(num)
            self.atualizar_tela()
        except TransicaoInvalidaException as ex:
            messagebox.showerror("Erro", str(ex))

if __name__ == "__main__":
    root_window = tk.Tk()
    app = HelpDeskGUI(root_window)
    root_window.mainloop()
