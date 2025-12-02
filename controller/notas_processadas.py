import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class NotasProcessadasManager:
    """
    Gerencia o rastreamento de notas fiscais que já tiveram seus preços ajustados.
    Utiliza arquivo JSON para persistência sem modificar o banco de dados original.
    """

    def __init__(self, arquivo_json: str = "notas_processadas.json"):
        """
        Inicializa o gerenciador de notas processadas.
        
        Args:
            arquivo_json: Caminho do arquivo JSON para armazenamento
        """
        self.arquivo_json = arquivo_json
        self.notas: Dict[str, dict] = {}
        self._carregar()

    def _gerar_chave(self, codigo_fornecedor: str, numero_nota: str, serie: str) -> str:
        """
        Gera chave única para identificar uma nota.
        
        Args:
            codigo_fornecedor: Código do fornecedor (5 dígitos)
            numero_nota: Número da nota fiscal (6 dígitos)
            serie: Série da nota
            
        Returns:
            Chave no formato "fornecedor_nota_serie"
        """
        # Normalizar para garantir consistência
        fornecedor = str(codigo_fornecedor).zfill(5)
        nota = str(numero_nota).zfill(6)
        return f"{fornecedor}_{nota}_{serie}"

    def _carregar(self) -> None:
        """
        Carrega as notas processadas do arquivo JSON.
        Se o arquivo não existir, inicializa com dicionário vazio.
        """
        if os.path.exists(self.arquivo_json):
            try:
                with open(self.arquivo_json, "r", encoding="utf-8") as f:
                    self.notas = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Aviso: Erro ao carregar {self.arquivo_json}: {e}")
                print("Criando novo arquivo de rastreamento...")
                self.notas = {}
        else:
            self.notas = {}

    def _salvar(self) -> None:
        """
        Salva as notas processadas no arquivo JSON.
        """
        try:
            with open(self.arquivo_json, "w", encoding="utf-8") as f:
                json.dump(self.notas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar {self.arquivo_json}: {e}")
            raise

    def verificar_nota(
        self, codigo_fornecedor: str, numero_nota: str, serie: str = "1"
    ) -> bool:
        """
        Verifica se uma nota já foi processada.
        
        Args:
            codigo_fornecedor: Código do fornecedor
            numero_nota: Número da nota fiscal
            serie: Série da nota (padrão "1")
            
        Returns:
            True se a nota já foi processada, False caso contrário
        """
        chave = self._gerar_chave(codigo_fornecedor, numero_nota, serie)
        return chave in self.notas

    def adicionar_nota(
        self,
        codigo_fornecedor: str,
        numero_nota: str,
        serie: str,
        usuario: str,
        produtos_editados: int,
        codigos_produtos: List[str] = None,
    ) -> None:
        """
        Registra uma nota como processada.
        
        Args:
            codigo_fornecedor: Código do fornecedor
            numero_nota: Número da nota fiscal
            serie: Série da nota
            usuario: Código do usuário que processou
            produtos_editados: Quantidade de produtos que tiveram preço alterado
            codigos_produtos: Lista com códigos dos produtos editados (opcional)
        """
        chave = self._gerar_chave(codigo_fornecedor, numero_nota, serie)
        
        agora = datetime.now()
        
        self.notas[chave] = {
            "fornecedor": str(codigo_fornecedor).zfill(5),
            "nota": str(numero_nota).zfill(6),
            "serie": serie,
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M:%S"),
            "usuario": usuario,
            "produtos_editados": produtos_editados,
            "codigos_produtos": codigos_produtos or [],
        }
        
        self._salvar()

    def obter_informacoes(
        self, codigo_fornecedor: str, numero_nota: str, serie: str = "1"
    ) -> Optional[dict]:
        """
        Obtém informações detalhadas sobre uma nota processada.
        
        Args:
            codigo_fornecedor: Código do fornecedor
            numero_nota: Número da nota fiscal
            serie: Série da nota (padrão "1")
            
        Returns:
            Dicionário com informações da nota ou None se não foi processada
        """
        chave = self._gerar_chave(codigo_fornecedor, numero_nota, serie)
        return self.notas.get(chave)

    def listar_todas(self) -> List[dict]:
        """
        Lista todas as notas processadas.
        
        Returns:
            Lista de dicionários com informações de todas as notas processadas
        """
        return list(self.notas.values())

    def total_notas_processadas(self) -> int:
        """
        Retorna o total de notas processadas.
        
        Returns:
            Quantidade de notas processadas
        """
        return len(self.notas)

    def limpar_notas_antigas(self, dias: int = 365) -> int:
        """
        Remove notas processadas com mais de X dias (opcional, para manutenção).
        
        Args:
            dias: Número de dias para considerar nota como antiga
            
        Returns:
            Quantidade de notas removidas
        """
        from datetime import timedelta
        
        limite = datetime.now() - timedelta(days=dias)
        chaves_remover = []
        
        for chave, info in self.notas.items():
            try:
                data_processamento = datetime.strptime(info["data"], "%Y-%m-%d")
                if data_processamento < limite:
                    chaves_remover.append(chave)
            except (ValueError, KeyError):
                continue
        
        for chave in chaves_remover:
            del self.notas[chave]
        
        if chaves_remover:
            self._salvar()
        
        return len(chaves_remover)
