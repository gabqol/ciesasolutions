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
        self.capacidade_maxima = capacidade_maxima

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
