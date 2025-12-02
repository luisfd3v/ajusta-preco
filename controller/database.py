import pyodbc
import configparser
import os
from model.produto import Produto
from controller.notas_processadas import NotasProcessadasManager


class Database:
    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.connection = None
        self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding="utf-8")

        self.server = config.get("Database", "server")
        self.database = config.get("Database", "database")
        self.username = config.get("Database", "username")
        self.password = config.get("Database", "password")
        self.driver = config.get("Database", "driver")
        self.usuario_evolucao = config.get("Database", "usuario_evolucao", fallback="2")
        self.tipo_margem = int(config.get("Database", "tipo_margem", fallback="1"))

    def connect(self):
        try:
            connection_string = (
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
            self.connection = pyodbc.connect(connection_string)
            return True
        except Exception as e:
            raise Exception(f"Erro ao conectar ao banco de dados: {str(e)}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def buscar_produtos_por_nota(
        self, numero_nota, serie_nota="1", codigo_fornecedor=""
    ):
        if not self.connection:
            self.connect()

        nota_formatada = str(numero_nota).zfill(6)
        fornecedor_formatado = (
            str(codigo_fornecedor).zfill(5) if codigo_fornecedor else ""
        )

        query = """
            SELECT
                a.AH_PEN as Sequencia,
                a.AE_PEN as CodigoProduto,
                cp.AB_ITE as DescricaoProduto,
                a.AJ_PEN as CustoTotal,
                a.AG_PEN as TipoCalculo,
                a.AI_PEN as Quantidade,
                a.AO_PEN as ValorAO,
                a.AR_PEN as ValorAR,
                CASE
                    WHEN a.AG_PEN = 2 AND a.AI_PEN > 0 THEN (a.AO_PEN + ISNULL(a.AR_PEN, 0)) / a.AI_PEN
                    WHEN a.AG_PEN = 3 AND a.AI_PEN > 0 THEN a.AO_PEN / a.AI_PEN
                    WHEN a.AI_PEN > 0 THEN (a.AO_PEN + ISNULL(a.AR_PEN, 0)) / a.AI_PEN
                    ELSE 0
                END as CustoReposicao,
                pa.PrecoVendaMin as PrecoMinimo,
                pa.PrecoVendaMax as PrecoMaximo
            FROM APECENCE a
            LEFT JOIN CE_PRODUTO cp ON a.AE_PEN = cp.AU_ITE
            LEFT JOIN ce_produtos_adicionais pa ON a.AE_PEN = pa.CodReduzido
            WHERE a.AB_PEN = ? AND a.AC_PEN = ? AND a.AA_PEN = ?
            ORDER BY a.AH_PEN
        """

        produtos = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (nota_formatada, serie_nota, fornecedor_formatado))

            for row in cursor.fetchall():
                produto = Produto(
                    codigo=row.CodigoProduto or "",
                    descricao=(row.DescricaoProduto or "").strip(),
                    custo_reposicao=float(row.CustoReposicao or 0),
                    preco_venda_min=float(row.PrecoMinimo or 0),
                    preco_venda_max=float(row.PrecoMaximo or 0),
                    tipo_margem=self.tipo_margem,
                    custo_total=float(row.CustoTotal or 0),
                    ag_pen=int(row.TipoCalculo or 0),
                    ar_pen=float(row.ValorAR or 0),
                )
                produto.sequencia = row.Sequencia or ""
                produtos.append(produto)

            cursor.close()
            return produtos

        except Exception as e:
            raise Exception(f"Erro ao buscar produtos: {str(e)}")

    def atualizar_precos(self, produtos, codigo_fornecedor=None, numero_nota=None, serie=None):
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()

            query_update = """
                UPDATE ce_produtos_adicionais
                SET PrecoVendaMin = ?, PrecoVendaMax = ?
                WHERE CodReduzido = ?
            """

            query_evolucao = """
                INSERT INTO GE_VARIACAO_PRECOSVENDA (
                    DATA_VPV,
                    HORA_VPV,
                    USUARIO_VPV,
                    PRODUTO_VPV,
                    VLR_MINIMO_VPV,
                    VLR_MAXIMO_VPV,
                    VLR_PROMOCIONAL_VPV,
                    VLR_TABELADO_VPV,
                    ORIGEMPRECO_VPV,
                    CODIGOORIGEM_VPV,
                    EMPRESA_VPV,
                    OPERACAO_VPV
                ) VALUES (
                    CONVERT(DATE, GETDATE()),
                    CONVERT(TIME, GETDATE()),
                    ?,
                    ?,
                    ?,
                    ?,
                    0,
                    0,
                    '0',
                    ?,
                    '02',
                    'ALTERACAO'
                )
            """

            for produto in produtos:
                cursor.execute(
                    query_update,
                    (
                        produto.preco_venda_novo,
                        produto.preco_venda_novo,
                        produto.codigo,
                    ),
                )

                cursor.execute(
                    query_evolucao,
                    (
                        self.usuario_evolucao,
                        produto.codigo,
                        produto.preco_venda_novo,
                        produto.preco_venda_novo,
                        produto.codigo,
                    ),
                )

            self.connection.commit()
            cursor.close()
            
            # Registrar nota como processada no JSON
            if codigo_fornecedor and numero_nota and serie:
                try:
                    notas_manager = NotasProcessadasManager()
                    codigos_produtos = [produto.codigo for produto in produtos]
                    notas_manager.adicionar_nota(
                        codigo_fornecedor=codigo_fornecedor,
                        numero_nota=numero_nota,
                        serie=serie,
                        usuario=self.usuario_evolucao,
                        produtos_editados=len(produtos),
                        codigos_produtos=codigos_produtos
                    )
                except Exception as e:
                    print(f"Aviso: Erro ao registrar nota no JSON: {e}")
            
            return True

        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Erro ao atualizar preços: {str(e)}")

    def verificar_nota_existe(self, numero_nota):
        if not self.connection:
            self.connect()

        nota_formatada = str(numero_nota).zfill(6)

        query = "SELECT COUNT(*) FROM APECENCE WHERE ab_pen = ?"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (nota_formatada,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0

        except Exception as e:
            raise Exception(f"Erro ao verificar nota: {str(e)}")

    def buscar_nome_empresa(self):
        if not self.connection:
            self.connect()

        query = "SELECT BC_EMP FROM AEMPREGE"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result and result[0]:
                return result[0].strip()
            else:
                return "Empresa"

        except Exception as e:
            print(f"Aviso: Não foi possível buscar nome da empresa: {str(e)}")
            return "Empresa"

    def buscar_regime_tributario(self):
        """Busca o código do regime tributário da empresa.
        Retorna:
            int: Código do regime tributário (3 = Regime Normal, outros = Simples Nacional)
        """
        if not self.connection:
            self.connect()

        query = "SELECT CODRGT_EMP FROM AEMPREGE"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            if result and result[0] is not None:
                return int(result[0])
            else:
                return 0

        except Exception as e:
            print(f"Aviso: Não foi possível buscar regime tributário: {str(e)}")
            return 0

    def buscar_informacoes_fornecedor(self, codigo_fornecedor):
        if not self.connection:
            self.connect()

        fornecedor_formatado = str(codigo_fornecedor).zfill(5)

        query = """
            SELECT
                codigo_for as Codigo,
                nome_for as Nome,
                cgccpf_for as CNPJ,
                estado_for as Estado,
                classi_for as Classificacao
            FROM AFORNEGE
            WHERE codigo_for = ?
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (fornecedor_formatado,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "codigo": (result.Codigo or "").strip(),
                    "nome": (result.Nome or "").strip(),
                    "cnpj": (result.CNPJ or "").strip(),
                    "estado": (result.Estado or "").strip(),
                    "classificacao": (result.Classificacao or "").strip(),
                }
            else:
                return None

        except Exception as e:
            raise Exception(f"Erro ao buscar fornecedor: {str(e)}")

    def buscar_todas_notas(self, limite=1000):
        if not self.connection:
            self.connect()

        query = f"""
            SELECT TOP {limite}
                AD_NEN AS EMISSAO, 
                AB_NEN AS NOTA, 
                AC_NEN AS SERIE, 
                AA_NEN AS CODIGO, 
                AB_TIP AS TIPOENTRADA, 
                CGCCPF_FOR AS CNPJ, 
                NOME_FOR AS FORNECEDOR, 
                AE_NEN AS ENTRADA, 
                AF_NEN AS VALOR, 
                CASE BE_NEN
                    WHEN '1' THEN 'Nota Digitada'
                    WHEN '2' THEN 'Nota Com Erro de Cálculo'
                    WHEN '3' THEN 'Nota Cálculo Ok'
                    WHEN '4' THEN 'Nota Impressa Ok'
                    WHEN '5' THEN 'Nota Com Atualização Iniciada'
                    WHEN '6' THEN 'Nota Atualizada Ok'
                    WHEN '7' THEN 'Nota Emitida Pelo Sistema'
                    WHEN '9' THEN 'Nota Cancelada'
                END AS STATUS,
                CASE BR_NEN 
                    WHEN 'P' THEN 'Próprio'
                    WHEN 'T' THEN 'Terceiros'
                END AS EMITENTE, 
                CHVNFE_NEN AS CHACENFE 
            FROM ANOTENCE 
            LEFT JOIN AFORNEGE ON CODIGO_FOR = AA_NEN 
            INNER JOIN ATIPNFCE ON AA_TIP = BD_NEN
            WHERE AA_TIP = '01'
            ORDER BY AD_NEN DESC, AB_NEN DESC
        """

        try:
            # Carregar notas processadas uma única vez
            notas_manager = NotasProcessadasManager()
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            notas = []
            for row in cursor.fetchall():
                codigo_fornecedor = (row.CODIGO or "").strip()
                numero_nota = (row.NOTA or "").strip()
                serie = (row.SERIE or "").strip()
                
                # Verificar se nota foi processada (operação O(1) no dicionário)
                processada = notas_manager.verificar_nota(
                    codigo_fornecedor, 
                    numero_nota, 
                    serie
                )
                
                nota = {
                    "emissao": row.EMISSAO,
                    "nota": numero_nota,
                    "serie": serie,
                    "codigo_fornecedor": codigo_fornecedor,
                    "tipo_entrada": (row.TIPOENTRADA or "").strip(),
                    "cnpj": (row.CNPJ or "").strip(),
                    "fornecedor": (row.FORNECEDOR or "").strip(),
                    "entrada": row.ENTRADA,
                    "valor": float(row.VALOR or 0),
                    "status": (row.STATUS or "").strip(),
                    "emitente": (row.EMITENTE or "").strip(),
                    "chave_nfe": (row.CHACENFE or "").strip() if hasattr(row, 'CHACENFE') else "",
                    "processada": processada,  # Nova coluna
                }
                notas.append(nota)
            
            cursor.close()
            return notas

        except Exception as e:
            raise Exception(f"Erro ao buscar notas: {str(e)}")
