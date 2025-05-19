import requests
import base64
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Cliente para acessar dados do Azure DevOps API."""

    def __init__(self, organizacao, projeto, equipe, pat):
        """
        Inicializa o cliente com credenciais do Azure DevOps.

        Parameters
        ----------
        organizacao : str
            Nome da organização no Azure DevOps
        projeto : str
            Nome do projeto
        equipe : str, optional
            Nome da equipe
        pat : str
            Personal Access Token para autenticação
        """
        self.organizacao = organizacao
        self.projeto = projeto
        self.equipe = equipe

        # Configura a autenticação
        token_autenticacao = base64.b64encode(f":{pat}".encode()).decode()
        self.cabecalho_autenticacao = {"Authorization": f"Basic {token_autenticacao}"}

        # URL base para chamadas de API
        self.url_base = f"https://dev.azure.com/{organizacao}/{projeto}"

    def get_sprints(self):
        """
        Obtém todas as sprints disponíveis para a equipe atual.

        Returns
        -------
        list
            Lista de sprints disponíveis

        Raises
        ------
        requests.RequestException
            Se houver erro na comunicação com a API
        """
        param_equipe = f"&team={self.equipe}" if self.equipe else ""
        url = f"{self.url_base}/_apis/work/teamsettings/iterations?api-version=7.0{param_equipe}"

        logger.info(f"Obtendo sprints de: {url}")

        try:
            resposta = requests.get(url, headers=self.cabecalho_autenticacao)
            resposta.raise_for_status()

            json_resposta = resposta.json()
            logger.info(f"Obtidas {len(json_resposta.get('value', []))} sprints")

            return json_resposta["value"]

        except requests.RequestException as e:
            logger.error(f"Erro na requisição: {str(e)}")
            logger.error(f"URL: {url}")
            if hasattr(e.response, "text"):
                logger.error(f"Resposta: {e.response.text[:200]}")
            raise

    def get_sprint_by_name(self, nome_sprint):
        """
        Obtém uma sprint específica pelo nome.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint a ser encontrada

        Returns
        -------
        dict or None
            Dados da sprint ou None se não encontrada
        """
        sprints = self.get_sprints()
        for sprint in sprints:
            if sprint["name"] == nome_sprint:
                return sprint
        return None

    def get_work_items_from_sprint(self, sprint_id):
        """
        Obtém todos os itens de trabalho para uma sprint específica.

        Parameters
        ----------
        sprint_id : str
            ID da sprint

        Returns
        -------
        list
            Lista de IDs dos itens de trabalho
        """
        param_equipe = f"&teamId={self.equipe}" if self.equipe else ""
        url = f"{self.url_base}/_apis/work/teamsettings/iterations/{sprint_id}/workitems?api-version=7.0{param_equipe}"

        logger.info(f"Obtendo itens de trabalho da sprint {sprint_id}")

        resposta = requests.get(url, headers=self.cabecalho_autenticacao)
        resposta.raise_for_status()

        itens_trabalho = resposta.json()["workItemRelations"]
        ids_itens_trabalho = [
            item["target"]["id"] for item in itens_trabalho if "target" in item
        ]

        logger.info(f"Encontrados {len(ids_itens_trabalho)} itens de trabalho")
        return ids_itens_trabalho

    def get_work_item_details(self, item_id):
        """
        Obtém informações detalhadas de um item de trabalho, incluindo revisões.

        Parameters
        ----------
        item_id : int
            ID do item de trabalho

        Returns
        -------
        dict
            Dados completos do item com histórico de revisões
        """
        # Obtém os detalhes atuais do item
        url = (
            f"{self.url_base}/_apis/wit/workitems/{item_id}?$expand=all&api-version=7.0"
        )

        logger.info(f"Obtendo detalhes do item {item_id}")

        resposta = requests.get(url, headers=self.cabecalho_autenticacao)
        resposta.raise_for_status()

        item_trabalho = resposta.json()

        # Obtém o histórico de revisões
        url_revisoes = (
            f"{self.url_base}/_apis/wit/workitems/{item_id}/revisions?api-version=7.0"
        )

        logger.info(f"Obtendo revisões do item {item_id}")

        resposta_revisoes = requests.get(
            url_revisoes, headers=self.cabecalho_autenticacao
        )
        resposta_revisoes.raise_for_status()

        revisoes = resposta_revisoes.json()["value"]

        # Combina as informações
        item_trabalho["revisoes"] = revisoes

        return item_trabalho

    def extract_sprint_data(self, nome_sprint, forcar_update=False):
        """
        Extrai todos os dados de uma sprint, incluindo itens de trabalho e revisões.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint

        Returns
        -------
        tuple
            Tupla contendo (dados_itens_trabalho, pasta_saida)

        Raises
        ------
        ValueError
            Se a sprint não for encontrada
        """
        logger.info(f"Extraindo dados para a sprint: {nome_sprint}")

        # Define o diretório de saída, se fornecido
        pasta_saida = Path("analises_sprint") / nome_sprint
        pasta_saida.mkdir(exist_ok=True, parents=True)

        # Verifica se o arquivo já existe
        arquivo_saida = pasta_saida / "dados_brutos.json"
        if arquivo_saida.exists() and not forcar_update:
            logger.info(f"Arquivo de saída já existe: {arquivo_saida}")
            with open(arquivo_saida, "r") as f:
                dados_itens_trabalho = json.load(f)
            return dados_itens_trabalho, pasta_saida

        # Obtém a sprint
        sprint = self.get_sprint_by_name(nome_sprint)
        if not sprint:
            raise ValueError(f"Sprint '{nome_sprint}' não encontrada")

        # Obtém os IDs dos itens de trabalho
        ids_itens_trabalho = self.get_work_items_from_sprint(sprint["id"])
        logger.info(
            f"Encontrados {len(ids_itens_trabalho)} itens de trabalho na sprint"
        )

        # Obtém detalhes de cada item
        dados_itens_trabalho = []
        for id_item in ids_itens_trabalho:
            logger.info(f"Processando item de trabalho {id_item}")
            item_trabalho = self.get_work_item_details(id_item)
            dados_itens_trabalho.append(item_trabalho)

        # Salva os dados brutos
        with open(pasta_saida / "dados_brutos.json", "w") as f:
            json.dump(dados_itens_trabalho, f)

        return dados_itens_trabalho, pasta_saida
