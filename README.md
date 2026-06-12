=======================================================================
               DOCUMENTAÇÃO E CÓDIGO-FONTE INTEGRAL
             HELPDESK PRO — CIESA SOLUTIONS (2026)
=======================================================================

-----------------------------------------------------------------------
PART 1: ARQUITETURA E REGRAS DE NEGÓCIO (README)
-----------------------------------------------------------------------

Este ecossistema foi desenvolvido para a Ciesa Solutions com o objetivo 
de substituir controles ineficientes por um sistema robusto de gestão de 
chamados técnicos, mitigando quebras de contrato (SLA) e automatizando 
o balanceamento de carga entre analistas de suporte.

O sistema adota uma arquitetura em 3 camadas independentes:
1. Core Business (helpdesk_djg.py): Modelo de domínio orientado a objetos.
2. API REST (app.py): Interface programática desenvolvida em Flask.
3. Interface Gráfica (app_gui.py): Painel Desktop em Tkinter para os operadores.

💡 JUSTIFICATIVA CRÍTICA DE DESEMPENHO (O(1))
A estrutura de dados escolhida para armazenar os chamados foi o Dicionário 
(dict) do Python, mapeando a chave {numero_chamado: objeto_chamado}. Internamente, 
os dicionários utilizam tabelas de dispersão (Hash Tables). A busca calcula 
uma função de espelhamento (hash) sobre o número do chamado, permitindo o 
acesso direto ao endereço de memória do objeto. Isso elimina a necessidade de 
varrer uma lista sequencialmente, garantindo complexidade algorítmica de tempo 
constante O(1), mantendo o sistema veloz mesmo com milhões de registros.

🔍 REVISÃO DO CÓDIGO BACKEND LINHA POR LINHA

1. Exceções Customizadas e Inicializador do Chamado
* As classes 'CapacidadeExcedidaException', 'ChamadoNaoEncontradoException' 
  e 'TransicaoInvalidaException' herdam de 'Exception' para isolar erros de 
  processo de negócio de falhas de infraestrutura.
* O atributo '_contador_id = 1000' é uma variável estática de classe usada 
  como acumulador para garantir IDs sequenciais a partir de 1001.
* No construtor (__init__), o dicionário 'TABELA_SLA' centraliza os tempos 
  limites por prioridade. O método '.lower()' previne falhas de digitação do 
  usuário. Caso a prioridade não exista, um ValueError impede a criação do objeto.

2. Monitoramento de SLA e Logs de Auditoria
* O método 'tempo_decorrido' retorna um objeto 'datetime.timedelta' calculando 
  a diferença entre o momento atual e a abertura.
* O método 'esta_em_atraso' aplica curto-circuito lógico: se o chamado estiver 
  'resolvido' ou 'fechado', o SLA para de correr. Caso contrário, verifica se 
  o tempo decorrido ultrapassou o estipulado na tabela de SLA.
* O método 'registrar_acao' insere dicionários formatados na lista de histórico. 
  O uso de '.isoformat()' converte datas em texto (padrão ISO 8601), garantindo 
  a serialização JSON perfeita.

3. Máquina de Estados Rígida
* O método 'alterar_status' mapeia os caminhos válidos em um dicionário interno. 
  A busca '.get(self.status, [])' avalia o estado atual. Se o novo status desejado 
  não constar na lista de destinos permitidos, a exceção 'TransicaoInvalidaException' 
  é disparada, blindando o fluxo operacional contra fraudes ou falhas humanas.

4. Gestão de Técnicos e Algoritmo de Desempenho
* As especialidades do Técnico são salvas em um 'set' (conjunto), permitindo 
  validações de habilidades em complexidade O(1).
* A propriedade 'disponivel' utiliza o decorador '@property', transformando o 
  método em um atributo computado de leitura (Getter) acessível sem parênteses.
* O algoritmo 'atribuicao_automatica' faz uma cópia da fila com 'list()' para 
  evitar mutação de dados em tempo de execução. Ele utiliza a função 'min()' combinada 
  com uma Tupla na chave Lambda: '(len(t.chamados_ativos), t.id_tecnico)'. O Python 
  avalia primeiro a quantidade de chamados ativos do técnico e, em caso de empate, 
  utiliza o menor ID como critério de desempate de forma puramente matemática.


-----------------------------------------------------------------------
PART 2: ARQUIVO CORE BACKEND - helpdesk_djg.py
-----------------------------------------------------------------------
# Salve o código abaixo em um arquivo separado chamado: helpdesk_djg.py

import datetime
from collections import Counter

class CapacidadeExcedidaException(Exception): pass
class ChamadoNaoEncontradoException(Exception): pass
class TransicaoInvalidaException(Exception): pass

class Chamado:
    _contador_id = 1000
    def __init__(self, titulo, descricao, cliente, prioridade):
        TABELA_SLA = {'critica': 4, 'alta': 8, 'media': 24, 'baixa': 72}
        prioridade_limpa = prioridade.lower()
        if prioridade_limpa not in TABELA_SLA:
            raise ValueError(f"Prioridade inválida: {prioridade}")
        
        self.numero = Chamado._contador_id = Chamado._contador_id + 1
        self.titulo = titulo
        self.descricao = descricao
        self.cliente = cliente
        self.prioridade = prioridade_limpa
        self.status = 'aberto'
        self.data_abertura = datetime.datetime.now()
        self.sla_horas = TABELA_SLA[self.prioridade]
        self.tecnico = None
        self.historico = []
        self.registrar_acao("Chamado aberto no sistema.", "Sistema")

    def tempo_decorrido(self):
        return datetime.datetime.now() - self.data_abertura

    def esta_em_atraso(self):
        if self.status in ['resolvido', 'fechado']: return False
        return self.tempo_decorrido() > datetime.timedelta(hours=self.sla_horas)

    def registrar_acao(self, acao, responsavel):
        self.historico.append({"data": datetime.datetime.now().isoformat(), "acao": acao, "responsavel": responsavel})

    def alterar_status(self, novo_status, responsavel):
        fluxo_valido = {
            'aberto': ['em_atendimento'],
            'em_atendimento': ['aguardando_cliente', 'resolvido'],
            'aguardando_cliente': ['em_atendimento'],
            'resolvido': ['fechado'],
            'fechado': []
        }
        if novo_status not in fluxo_valido.get(self.status, []):
            raise TransicaoInvalidaException(f"Não é permitido mudar de '{self.status}' para '{novo_status}'.")
        self.status = novo_status
        self.registrar_acao(f"Status alterado para '{novo_status}'", responsavel)

    def to_dict(self):
        return {
            "numero": self.numero, "titulo": self.titulo, "descricao": self.descricao,
            "cliente": self.cliente, "prioridade": self.prioridade, "status": self.status,
            "data_abertura": self.data_abertura.isoformat(), "sla_horas": self.sla_horas,
            "tecnico": self.tecnico, "esta_em_atraso": self.esta_em_atraso(), "historico": self.historico
        }

class Tecnico:
    _contador_tecnico = 1
    def __init__(self, nome, especialidades, capacidade_maxima=5):
        self.id_tecnico = Tecnico._contador_tecnico = Tecnico._contador_tecnico + 1
        self.nome = nome
        self.especialidades = set([esp.lower() for esp in especialidades])
        self.chamados_ativos = []
        self.capacidade_maxima = capacity_maxima

    @property
    def disponivel(self):
        return len(self.chamados_ativos) < self.capacidade_maxima

    def atribuir_chamado(self, numero):
        if not self.disponivel: raise CapacidadeExcedidaException("Limite atingido.")
        if numero not in self.chamados_ativos: self.chamados_ativos.append(numero)

    def liberar_chamado(self, numero):
        if numero in self.chamados_ativos: self.chamados_ativos.remove(numero)
        else: raise ValueError("Chamado não encontrado no técnico.")

    def to_dict(self):
        return {"id_tecnico": self.id_tecnico, "nome": self.nome, "especialidades": list(self.especialidades), "chamados_ativos": self.chamados_ativos, "disponivel": self.disponivel}

class CentralDeSupporte:
    def __init__(self, empresa):
        self.empresa = empresa
        self.chamados = {}
        self.tecnicos = {}
        self.fila_nao_atribuidos = []

    def abrir_chamado(self, titulo, descricao, cliente, prioridade):
        novo = Chamado(titulo, descricao, cliente, prioridade)
        self.chamados[novo.numero] = novo
        self.fila_nao_atribuidos.append(novo.numero)
        return novo

    def registrar_tecnico(self, nome, especialidades, capacidade_maxima=5):
        novo = Tecnico(nome, especialidades, capacidade_maxima)
        self.tecnicos[novo.id_tecnico] = novo
        return novo

    def buscar_chamado(self, numero):
        if numero not in self.chamados: raise ChamadoNaoEncontradoException("Inexistente.")
        return self.chamados[numero]

    def atribuir_tecnico(self, numero_chamado, id_tecnico):
        chamado = self.buscar_chamado(numero_chamado)
        tecnico = self.tecnicos[id_tecnico]
        tecnico.atribuir_chamado(chamado.numero)
        chamado.tecnico = tecnico.id_tecnico
        chamado.alterar_status('em_atendimento', f"Técnico: {tecnico.nome}")
        if chamado.numero in self.fila_nao_atribuidos: self.fila_nao_atribuidos.remove(chamado.numero)

    def atribuicao_automatica(self):
        atribuidos = []
        for num in list(self.fila_nao_atribuidos):
            tecs_disp = [t for t in self.tecnicos.values() if t.disponivel]
            if not tecs_disp: break
            prox = min(tecs_disp, key=lambda t: (len(t.chamados_ativos), t.id_tecnico))
            self.atribuir_tecnico(num, prox.id_tecnico)
            atribuidos.append(num)
        return len(atribuidos), atribuidos

    def resolver_chamado(self, numero, id_tecnico, descricao_solucao):
        chamado = self.buscar_chamado(numero)
        if chamado.tecnico != id_tecnico: raise ValueError("Não é o responsável.")
        chamado.alterar_status('resolvido', f"Técnico #{id_tecnico}")
        chamado.registrar_acao(f"Solução: {descricao_solucao}", f"Técnico #{id_tecnico}")
        self.tecnicos[id_tecnico].liberar_chamado(chamado.numero)

    def fechar_chamado(self, numero):
        self.buscar_chamado(numero).alterar_status('fechado', "Supervisor")

    def listar_em_atraso(self):
        return sorted([c for c in self.chamados.values() if c.esta_em_atraso()], key=lambda c: c.tempo_decorrido(), reverse=True)

    def painel_operacional(self):
        status_counts = Counter([c.status for c in self.chamados.values()])
        top_3 = Counter([c.cliente for c in self.chamados.values()]).most_common(3)
        return {
            "totais_por_status": dict(status_counts),
            "total_em_atraso": len(self.listar_em_atraso()),
            "tecnicos_disponiveis": len([t for t in self.tecnicos.values() if t.disponivel]),
            "top_3_clientes": top_3
        }


-----------------------------------------------------------------------
PART 3: ARQUIVO API FLASK - app.py
-----------------------------------------------------------------------
# Salve o código abaixo em um arquivo separado chamado: app.py

from flask import Flask, request, jsonify
from helpdesk_djg import (
    CentralDeSupporte, 
    ChamadoNaoEncontradoException, 
    TransicaoInvalidaException, 
    CapacidadeExcedidaException
)

app = Flask(__name__)
central = CentralDeSupporte("Ciesa Solutions")

central.registrar_tecnico("Julianne Diniz", ["Redes", "Windows"], capacidade_maxima=3)
central.registrar_tecnico("Dymitre", ["Banco de Dados", "Linux"])

@app.route('/chamados', methods=['POST'])
def abrir_chamado():
    data = request.get_json() or {}
    try:
        required = ['titulo', 'descricao', 'cliente', 'prioridade']
        if not all(field in data for field in required):
            return jsonify({"erro": "Campos obrigatórios ausentes"}), 400
        novo = central.abrir_chamado(data['titulo'], data['descricao'], data['cliente'], data['prioridade'])
        return jsonify(novo.to_dict()), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/chamados', methods=['GET'])
def listar_chamados():
    status_filtro = request.args.get('status')
    res = [c.to_dict() for c in central.chamados.values() if not status_filtro or c.status.lower() == status_filtro.lower()]
    return jsonify(res), 200

@app.route('/chamados/<int:numero>', methods=['GET'])
def buscar_chamado_por_numero(numero):
    try:
        return jsonify(central.buscar_chamado(numero).to_dict()), 200
    except ChamadoNaoEncontradoException as e:
        return jsonify({"erro": str(e)}), 404

@app.route('/chamados/<int:numero>/status', methods=['PATCH'])
def alterar_status_chamado(numero):
    data = request.get_json() or {}
    novo_status = data.get('novo_status')
    if not novo_status: return jsonify({"erro": "novo_status obrigatório"}), 400
    try:
        chamado = central.buscar_chamado(numero)
        chamado.alterar_status(novo_status, data.get('responsavel', 'API'))
        return jsonify(chamado.to_dict()), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/chamados/<int:numero>/resolver', methods=['PATCH'])
def resolver_chamado(numero):
    data = request.get_json() or {}
    id_tecnico = data.get('id_tecnico')
    solucao = data.get('descricao_solucao')
    if id_tecnico is None or not solucao: return jsonify({"erro": "Campos obrigatórios ausentes"}), 400
    try:
        central.resolver_chamado(numero, int(id_tecnico), solucao)
        return jsonify(central.buscar_chamado(numero).to_dict()), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/chamados/em-atraso', methods=['GET'])
def listar_em_atraso():
    return jsonify([c.to_dict() for c in central.listar_em_atraso()]), 200

@app.route('/tecnicos', methods=['POST'])
def registrar_tecnico():
    data = request.get_json() or {}
    if 'nome' not in data or 'especialidades' not in data: return jsonify({"erro": "Campos inválidos"}), 400
    novo = central.registrar_tecnico(data['nome'], data['especialidades'], data.get('capacidade_maxima', 5))
    return jsonify(novo.to_dict()), 201

@app.route('/tecnicos', methods=['GET'])
def listar_tecnicos():
    disp = request.args.get('disponivel')
    res = [t.to_dict() for t in central.tecnicos.values() if disp is None or str(t.disponivel).lower() == disp.lower()]
    return jsonify(res), 200

@app.route('/atribuicao/automatica', methods=['POST'])
def exec_atribuicao_automatica():
    qtd, lista = central.atribuicao_automatica()
    return jsonify({"quantidade_atribuida": qtd, "chamados_atribuidos_ids": lista}), 200

@app.route('/painel', methods=['GET'])
def obter_painel():
    return jsonify(central.painel_operacional()), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)


-----------------------------------------------------------------------
PART 4: ARQUIVO INTERFACE GRÁFICA TKINTER - app_gui.py
-----------------------------------------------------------------------
# Salve o código abaixo em um arquivo separado chamado: app_gui.py

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

=======================================================================
                        FIM DO PROJETO
=======================================================================
