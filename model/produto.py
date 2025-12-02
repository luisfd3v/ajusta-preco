class Produto:
    def __init__(
        self,
        codigo,
        descricao,
        custo_reposicao,
        preco_venda_min,
        preco_venda_max,
        tipo_margem=1,
        custo_total=0.0,
        ag_pen=0,
        ar_pen=0.0,
    ):
        self.sequencia = ""
        self.codigo = codigo
        self.descricao = descricao
        self.custo_reposicao = custo_reposicao
        self.custo_total = custo_total
        self.preco_venda_min = preco_venda_min
        self.preco_venda_max = preco_venda_max
        self.preco_venda_novo = preco_venda_min
        self.margem_venda = 0.0
        self.porcentagem_custo = 0.0
        self.tipo_margem = tipo_margem
        self.ag_pen = ag_pen
        self.ar_pen = ar_pen
        self.usar_custo_total = False

    def calcular_preco_por_margem_venda(self, margem_percentual):
        self.margem_venda = margem_percentual
        custo_base = self.custo_total if self.usar_custo_total else self.custo_reposicao
        if custo_base > 0:
            self.preco_venda_novo = custo_base / (1 - margem_percentual / 100)
            self.porcentagem_custo = ((self.preco_venda_novo - custo_base) / custo_base) * 100
        return self.preco_venda_novo

    def calcular_preco_por_porcentagem_custo(self, porcentagem):
        self.porcentagem_custo = porcentagem
        custo_base = self.custo_total if self.usar_custo_total else self.custo_reposicao
        if custo_base > 0:
            self.preco_venda_novo = custo_base * (1 + porcentagem / 100)
            self.margem_venda = (1 - custo_base / self.preco_venda_novo) * 100
        return self.preco_venda_novo

    def set_preco_venda_novo(self, preco):
        self.preco_venda_novo = preco
        custo_base = self.custo_total if self.usar_custo_total else self.custo_reposicao
        if custo_base > 0 and preco > 0:
            self.margem_venda = (1 - custo_base / preco) * 100
            self.porcentagem_custo = ((preco - custo_base) / custo_base) * 100
        else:
            self.margem_venda = 0.0
            self.porcentagem_custo = 0.0

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "descricao": self.descricao,
            "custo_reposicao": self.custo_reposicao,
            "custo_total": self.custo_total,
            "preco_venda_min": self.preco_venda_min,
            "preco_venda_max": self.preco_venda_max,
            "preco_venda_novo": self.preco_venda_novo,
            "margem_venda": self.margem_venda,
            "porcentagem_custo": self.porcentagem_custo,
        }
