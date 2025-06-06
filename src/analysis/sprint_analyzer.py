import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SprintAnalyzer:
    """Classe para análise e processamento de dados de sprints do Azure DevOps."""

    def __init__(self, azure_client):
        """
        Inicializa o analisador com um cliente Azure DevOps.

        Parameters
        ----------
        azure_client : AzureDevOpsClient
            Cliente configurado para acessar o Azure DevOps
        """
        self.azure_client = azure_client

        # Define o mapeamento de estados para colunas do quadro
        self.colunas_estados = {
            "Planejado": "Planned",
            "Em desenvolvimento": "InProgress",
            "Em revisão de código": "InReview",
            "Pronto para homologação": "ReadyForTest",
            "Em homologação": "Testing",
            "Validado pelo negócio": "Validated",
            "Concluído": "Done",
        }

        # Metas padrão para a distribuição de trabalho
        self.metas_padrao = {"Negócio": 70, "Técnico": 20, "Incidentes": 10}

        # Pasta base para saída de arquivos
        self.pasta_base_saida = Path("analises_sprint")
        self.pasta_base_saida.mkdir(exist_ok=True)

    def analisar_sprint(self, nome_sprint, forcar_atualizacao=False):
        """
        Analisa uma sprint completa, gerando insights e dados processados.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint a ser analisada
        forcar_atualizacao : bool, optional
            Se True, força a reanálise mesmo se já houver dados processados

        Returns
        -------
        tuple
            (insights, pasta_saida) contendo os insights gerados e o caminho
            para a pasta com os resultados
        """
        # Extrai dados da sprint
        dados_brutos, pasta_saida = self.azure_client.extract_sprint_data(
            nome_sprint, True
        )
        arquivo_saida = pasta_saida / "dados_processados.json"

        # Verifica se já temos dados processados
        if not forcar_atualizacao and arquivo_saida.exists():
            with open(arquivo_saida, "r") as f:
                dados_processados = json.load(f)
        else:
            # Transforma os dados brutos
            dados_processados = self._transformar_dados(dados_brutos)

            # Salva os dados processados
            with open(arquivo_saida, "w") as f:
                json.dump(dados_processados, f)

        # Gera insights
        insights = self._gerar_insights(dados_processados, nome_sprint, pasta_saida)

        # Exporta para CSV para análises adicionais
        self._exportar_para_csv(dados_processados, pasta_saida)
        self._exportar_dados_completos(nome_sprint, pasta_saida)

        return insights, pasta_saida

    def analisar_multiplas_sprints(self, nomes_sprints):
        """
        Analisa múltiplas sprints e gera relatório consolidado.

        Parameters
        ----------
        nomes_sprints : list
            Lista de nomes das sprints a serem analisadas

        Returns
        -------
        tuple
            (insights_consolidados, pasta_saida)
        """
        logger.info(
            f"Analisando {len(nomes_sprints)} sprints: {', '.join(nomes_sprints)}"
        )

        # Cria pasta para o relatório consolidado
        pasta_saida = self.pasta_base_saida / "consolidado"
        pasta_saida.mkdir(exist_ok=True, parents=True)

        # Armazena insights de cada sprint
        todos_insights = []

        # Dados brutos consolidados
        df_consolidado = None

        # Analisa cada sprint individualmente
        for nome_sprint in nomes_sprints:
            insights, pasta_sprint = self.analisar_sprint(nome_sprint)
            todos_insights.append(insights)

            # Copia os gráficos gerados para a pasta consolidada
            self._copiar_graficos_sprint(pasta_sprint, pasta_saida, nome_sprint)

            # Acumula dados brutos
            csv_path = pasta_sprint / "detalhes_completos.csv"
            if csv_path.exists():
                df_sprint = pd.read_csv(csv_path)
                # Adiciona coluna com nome da sprint
                df_sprint["Sprint"] = nome_sprint

                if df_consolidado is None:
                    df_consolidado = df_sprint
                else:
                    df_consolidado = pd.concat(
                        [df_consolidado, df_sprint], ignore_index=True
                    )

        # Salva dados brutos consolidados
        if df_consolidado is not None:
            df_consolidado.to_csv(
                pasta_saida / "detalhes_consolidados.csv",
                index=False,
                encoding="utf-8-sig",
            )

        # Consolida métricas
        insights_consolidados = self._consolidar_insights(todos_insights, nomes_sprints)

        # Salva os insights consolidados
        with open(pasta_saida / "insights_consolidados.json", "w") as f:
            json.dump(insights_consolidados, f)

        return insights_consolidados, pasta_saida

    def _copiar_graficos_sprint(self, pasta_origem, pasta_destino, nome_sprint):
        """
        Copia os gráficos de uma sprint para a pasta consolidada, renomeando-os com prefixo.

        Parameters
        ----------
        pasta_origem : Path
            Pasta com os gráficos da sprint
        pasta_destino : Path
            Pasta de destino (consolidado)
        nome_sprint : str
            Nome da sprint para usar como prefixo
        """
        # Nomes de arquivos a copiar
        arquivos_graficos = [
            "itens_por_tipo.png",
            "itens_por_estado.png",
            "itens_por_responsavel.png",
            "esforco_por_responsavel.png",
            "tempo_medio_coluna.png",
            "adicoes_meio_sprint.png",
            "retornos.png",
        ]

        import shutil

        for arquivo in arquivos_graficos:
            caminho_origem = pasta_origem / arquivo
            if caminho_origem.exists():
                # Substitui espaços e caracteres especiais no nome da sprint para evitar problemas no nome do arquivo
                nome_safe = (
                    nome_sprint.replace(" ", "_").replace("/", "_").replace("\\", "_")
                )
                caminho_destino = pasta_destino / f"{nome_safe}_{arquivo}"
                shutil.copy2(caminho_origem, caminho_destino)

    def _consolidar_insights(self, lista_insights, nomes_sprints):
        """
        Consolida insights de múltiplas sprints em um único conjunto.

        Parameters
        ----------
        lista_insights : list
            Lista de dicionários de insights
        nomes_sprints : list
            Nomes das sprints correspondentes

        Returns
        -------
        dict
            Insights consolidados
        """
        consolidado = {
            "sprints": nomes_sprints,
            "total_sprints": len(nomes_sprints),
            "por_sprint": {},
            "total_itens": 0,
            "media_itens_sprint": 0,
            "total_esforco": 0,
            "esforco_total": 0,  # Adicionando chave alternativa para compatibilidade
            "media_esforco_sprint": 0,
            "media_percentual_concluido": 0,
            "percentual_concluido": 0,  # Adicionando chave alternativa para compatibilidade
            "total_chamados": 0,
            "chamados_concluidos": 0,
            "media_retornos_por_sprint": 0,
            "tendencia_conclusao": [],
            "tendencia_esforco": [],
        }

        # Armazena dados por sprint e calcula totais
        for i, insights in enumerate(lista_insights):
            nome_sprint = nomes_sprints[i]
            consolidado["por_sprint"][nome_sprint] = insights

            # Acumula métricas
            consolidado["total_itens"] += insights["total_itens"]
            consolidado["total_esforco"] += insights["esforco_total"]
            consolidado["media_percentual_concluido"] += insights[
                "percentual_concluido"
            ]
            consolidado["total_chamados"] += insights.get("total_chamados", 0)
            consolidado["chamados_concluidos"] += insights.get("chamados_concluidos", 0)
            consolidado["media_retornos_por_sprint"] += insights["retornos"]

            # Dados para tendências
            consolidado["tendencia_conclusao"].append(
                {"sprint": nome_sprint, "percentual": insights["percentual_concluido"]}
            )
            consolidado["tendencia_esforco"].append(
                {"sprint": nome_sprint, "esforco": insights["esforco_total"]}
            )

        # Calcula médias
        n_sprints = len(lista_insights)
        if n_sprints > 0:
            consolidado["media_itens_sprint"] = consolidado["total_itens"] / n_sprints
            consolidado["media_esforco_sprint"] = (
                consolidado["total_esforco"] / n_sprints
            )
            consolidado["media_percentual_concluido"] /= n_sprints
            consolidado["media_retornos_por_sprint"] /= n_sprints

        # Ordena tendências por nome da sprint
        consolidado["tendencia_conclusao"].sort(key=lambda x: x["sprint"])
        consolidado["tendencia_esforco"].sort(key=lambda x: x["sprint"])

        return consolidado

    def analisar_distribuicao_tasks(self, nome_sprint):
        """
        Analisa a distribuição atual das tasks da sprint por categoria.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint a ser analisada

        Returns
        -------
        tuple
            (distribuicao_por_esforco, distribuicao_por_quantidade, df_items)
        """
        logger.info(f"Analisando distribuição de tasks para sprint: {nome_sprint}")

        # Extrai dados da sprint
        dados_brutos, pasta_saida = self.azure_client.extract_sprint_data(nome_sprint)

        # Processa os itens
        itens_processados = []

        for item in dados_brutos:
            categoria = self._determinar_categoria_item(item)

            item_processado = {
                "ID": item["id"],
                "Título": item["fields"].get("System.Title", ""),
                "Tipo": item["fields"].get("System.WorkItemType", ""),
                "Estado": item["fields"].get("System.State", ""),
                "Esforço": item["fields"].get("Microsoft.VSTS.Scheduling.Effort", 0)
                or 0,
                "Categoria": categoria,
            }

            itens_processados.append(item_processado)

        # Cria DataFrame
        df_items = pd.DataFrame(itens_processados)

        # Calcula distribuição por esforço
        total_esforco = df_items["Esforço"].sum()
        distribuicao_por_esforco = {}

        if total_esforco > 0:
            esforco_por_categoria = df_items.groupby("Categoria")["Esforço"].sum()

            for categoria, esforco_categoria in esforco_por_categoria.items():
                distribuicao_por_esforco[categoria] = (
                    esforco_categoria / total_esforco
                ) * 100

        # Calcula distribuição por quantidade
        total_tasks = len(df_items)
        distribuicao_por_quantidade = {}

        if total_tasks > 0:
            quantidade_por_categoria = df_items["Categoria"].value_counts()

            for categoria, qtd_categoria in quantidade_por_categoria.items():
                distribuicao_por_quantidade[categoria] = (
                    qtd_categoria / total_tasks
                ) * 100

        # Garante que todas as categorias estejam presentes
        for categoria in ["Negócio", "Técnico", "Incidentes"]:
            if categoria not in distribuicao_por_esforco:
                distribuicao_por_esforco[categoria] = 0
            if categoria not in distribuicao_por_quantidade:
                distribuicao_por_quantidade[categoria] = 0

        logger.info(f"Distribuição por esforço: {distribuicao_por_esforco}")
        logger.info(f"Distribuição por quantidade: {distribuicao_por_quantidade}")

        return distribuicao_por_esforco, distribuicao_por_quantidade, df_items

    def gerar_recomendacoes_distribuicao(
        self,
        distribuicao_esforco,
        distribuicao_quantidade,
        df_items,
        avg_points,
        metas=None,
    ):
        """
        Gera recomendações para ajustar a distribuição de tasks com base nas metas.

        Parameters
        ----------
        distribuicao_esforco : dict
            Distribuição percentual por esforço
        distribuicao_quantidade : dict
            Distribuição percentual por quantidade
        df_items : DataFrame
            DataFrame com os itens da sprint
        avg_points : float
            Média histórica de pontos por sprint
        metas : dict, optional
            Metas percentuais por categoria (usa padrão se None)

        Returns
        -------
        dict
            Dicionário com análises e recomendações
        """
        # Usa metas padrão se não especificadas
        if metas is None:
            metas = self.metas_padrao

        # Ponto total atual
        pontos_atuais = df_items["Esforço"].sum()

        # Quantidade total de tasks
        quantidade_total = len(df_items)

        # Diferença entre pontos atuais e média histórica
        diferenca_pontos = pontos_atuais - avg_points

        # Cálculos para recomendações
        pontos_ideais = {
            categoria: (meta / 100) * avg_points for categoria, meta in metas.items()
        }

        tasks_ideais = {
            categoria: (meta / 100) * quantidade_total
            for categoria, meta in metas.items()
        }

        # Pontos e tasks atuais por categoria
        pontos_atuais_por_categoria = (
            df_items.groupby("Categoria")["Esforço"].sum().to_dict()
        )
        qtd_tasks_por_categoria = df_items["Categoria"].value_counts().to_dict()

        # Garante que todas as categorias estejam no dicionário
        for cat in metas.keys():
            if cat not in pontos_atuais_por_categoria:
                pontos_atuais_por_categoria[cat] = 0
            if cat not in qtd_tasks_por_categoria:
                qtd_tasks_por_categoria[cat] = 0

        # Calcula diferenças entre atual e ideal
        diferencas_pontos = {
            cat: pontos_atuais_por_categoria.get(cat, 0) - pontos_ideais[cat]
            for cat in metas.keys()
        }

        diferencas_qtd = {
            cat: qtd_tasks_por_categoria.get(cat, 0) - tasks_ideais[cat]
            for cat in metas.keys()
        }

        # Determina categorias com maior déficit e excesso
        cat_mais_deficit = min(diferencas_pontos.items(), key=lambda x: x[1])
        cat_mais_excesso = max(diferencas_pontos.items(), key=lambda x: x[1])

        # Itens candidatos para movimentação
        itens_candidatos = None
        if cat_mais_deficit[1] < -5 and cat_mais_excesso[1] > 5:
            if cat_mais_excesso[0] in df_items["Categoria"].values:
                itens_candidatos = (
                    df_items[df_items["Categoria"] == cat_mais_excesso[0]]
                    .sort_values("Esforço")
                    .head(3)
                )

        # Resultado final
        return {
            "metas": metas,
            "distribuicao_por_esforco": distribuicao_esforco,
            "distribuicao_por_quantidade": distribuicao_quantidade,
            "pontos_atuais": pontos_atuais,
            "quantidade_total": quantidade_total,
            "avg_points": avg_points,
            "diferenca_pontos": diferenca_pontos,
            "pontos_ideais": pontos_ideais,
            "tasks_ideais": tasks_ideais,
            "pontos_atuais_por_categoria": pontos_atuais_por_categoria,
            "qtd_tasks_por_categoria": qtd_tasks_por_categoria,
            "diferencas_pontos": diferencas_pontos,
            "diferencas_qtd": diferencas_qtd,
            "cat_mais_deficit": cat_mais_deficit,
            "cat_mais_excesso": cat_mais_excesso,
            "itens_candidatos": itens_candidatos,
        }

    def _determinar_categoria_item(self, item):
        """
        Determina a categoria de um item baseado em critérios definidos.

        Parameters
        ----------
        item : dict
            Item de trabalho do Azure DevOps

        Returns
        -------
        str
            Categoria do item (Negócio, Técnico ou Incidentes)
        """
        # Mapeamento de categorias
        mapeamento_categoria = {"Business": "Negócio", "Architectural": "Técnico"}

        # Extrai informações relevantes
        tipo = item["fields"].get("System.WorkItemType", "")
        value_area = item["fields"].get("Microsoft.VSTS.Common.ValueArea", "")
        tags = item["fields"].get("System.Tags", "").lower()

        # Determina categoria
        if "chamado" in tags:
            return "Incidentes"

        categoria = mapeamento_categoria.get(value_area, "")
        if not categoria:
            return "Negócio"  # Padrão

        return categoria

    def _transformar_dados(self, dados_brutos):
        """
        Transforma dados brutos em formato estruturado para análise.

        Parameters
        ----------
        dados_brutos : list
            Lista de itens de trabalho com seus detalhes

        Returns
        -------
        list
            Dados processados em formato padronizado
        """
        itens_processados = []

        for item in dados_brutos:
            id_item = item["id"]
            tipo_item = item["fields"]["System.WorkItemType"]
            titulo = item["fields"]["System.Title"]
            estado = item["fields"]["System.State"]

            # Extrai pontos de esforço
            esforco = item["fields"].get("Microsoft.VSTS.Scheduling.Effort", 0) or 0

            # Extrai histórico de responsáveis
            historico_responsaveis = []
            responsavel_atual = (
                item["fields"]
                .get("System.AssignedTo", {})
                .get("displayName", "Não atribuído")
                if isinstance(item["fields"].get("System.AssignedTo"), dict)
                else "Não atribuído"
            )

            # Processa revisões para transições e responsáveis
            transicoes_coluna, retornos = self._processar_revisoes(item)

            # Verifica se adicionado no meio da sprint
            data_criacao = item["fields"]["System.CreatedDate"]
            inicio_sprint = item["fields"].get("System.IterationStartDate")
            adicionado_meio_sprint = False

            if inicio_sprint and data_criacao > inicio_sprint:
                adicionado_meio_sprint = True

            # Cria item processado
            item_processado = {
                "id": id_item,
                "tipo": tipo_item,
                "titulo": titulo,
                "estado": estado,
                "esforco": esforco,
                "historico_responsaveis": historico_responsaveis,
                "responsavel_atual": responsavel_atual,
                "transicoes_coluna": transicoes_coluna,
                "retornos": retornos,
                "data_criacao": data_criacao,
                "adicionado_meio_sprint": adicionado_meio_sprint,
            }

            # Processa histórico de responsáveis
            for rev in item.get("revisoes", []):
                if "System.AssignedTo" in rev.get("fields", {}):
                    resp = rev["fields"]["System.AssignedTo"]
                    nome_resp = (
                        resp.get("displayName", "Não atribuído")
                        if isinstance(resp, dict)
                        else "Não atribuído"
                    )
                    data = rev["fields"]["System.ChangedDate"]
                    historico_responsaveis.append(
                        {"responsavel": nome_resp, "data": data}
                    )

            item_processado["historico_responsaveis"] = historico_responsaveis
            itens_processados.append(item_processado)

        return itens_processados

    def _processar_revisoes(self, item):
        """
        Processa as revisões de um item para extrair transições de estado e retornos.

        Parameters
        ----------
        item : dict
            Item de trabalho com revisões

        Returns
        -------
        tuple
            (transicoes_coluna, retornos)
        """
        transicoes_coluna = {}
        retornos = []

        # Processa revisões para extrair transições
        revisoes = sorted(item.get("revisoes", []), key=lambda x: x["rev"])

        # Rastreia a ordem máxima de colunas para detectar retornos
        ordem_colunas = list(self.colunas_estados.keys())
        ultimo_indice_coluna_maior = -1

        for rev in revisoes:
            if "System.State" in rev.get("fields", {}):
                estado = rev["fields"]["System.State"]
                data_alteracao = rev["fields"]["System.ChangedDate"]

                # Mapeia o estado para coluna
                coluna = next(
                    (k for k, v in self.colunas_estados.items() if v == estado),
                    estado,
                )

                if coluna not in transicoes_coluna:
                    transicoes_coluna[coluna] = []

                transicoes_coluna[coluna].append(data_alteracao)

                # Detecta retornos
                if coluna in ordem_colunas:
                    indice_atual = ordem_colunas.index(coluna)

                    if indice_atual < ultimo_indice_coluna_maior:
                        # Encontrou um retorno
                        retornos.append(
                            {
                                "de": ordem_colunas[ultimo_indice_coluna_maior],
                                "para": coluna,
                                "data": data_alteracao,
                            }
                        )

                    ultimo_indice_coluna_maior = max(
                        ultimo_indice_coluna_maior, indice_atual
                    )

        return transicoes_coluna, retornos

    def _gerar_insights(self, dados_processados, nome_sprint, pasta_saida):
        """
        Gera insights a partir dos dados processados.

        Parameters
        ----------
        dados_processados : list
            Lista de itens processados
        nome_sprint : str
            Nome da sprint
        pasta_saida : Path
            Caminho para salvar resultados

        Returns
        -------
        dict
            Insights gerados
        """
        # Inicializa estrutura de insights
        insights = self._inicializar_insights(nome_sprint)

        # Calcula métricas básicas
        insights = self._analisar_metricas_basicas(insights, dados_processados)

        # Analisa retornos
        insights = self._analisar_retornos(insights, dados_processados)

        # Analisa tempo em colunas
        insights = self._analisar_tempo_colunas(insights, dados_processados)

        # Analisa chamados
        insights = self._analisar_chamados(insights, dados_processados, pasta_saida)

        # Salva insights
        with open(pasta_saida / "insights.json", "w") as f:
            json.dump(insights, f)

        return insights

    def _inicializar_insights(self, nome_sprint):
        """Inicializa a estrutura base de insights."""
        return {
            "nome_sprint": nome_sprint,
            "total_itens": 0,
            "por_tipo": {},
            "por_estado": {},
            "adicoes_meio_sprint": 0,
            "retornos": 0,
            "retornos_unicos": 0,
            "detalhes_retornos": [],
            "carga_trabalho_responsaveis": {},
            "esforco_total": 0,
            "tempo_medio_colunas": {},
            "percentual_concluido": 0,
            "total_chamados": 0,
            "chamados_concluidos": 0,
        }

    def _analisar_metricas_basicas(self, insights, dados_processados):
        """Analisa métricas básicas dos itens."""
        insights["total_itens"] = len(dados_processados)
        itens_concluidos = 0
        esforco_concluido = 0
        esforco_total = 0

        for item in dados_processados:
            # Conta por tipo
            tipo_item = item["tipo"]
            if tipo_item not in insights["por_tipo"]:
                insights["por_tipo"][tipo_item] = 0
            insights["por_tipo"][tipo_item] += 1

            # Conta por estado
            estado = item["estado"]
            if estado not in insights["por_estado"]:
                insights["por_estado"][estado] = 0
            insights["por_estado"][estado] += 1

            # Verifica se concluído
            concluido = estado == "Done" or estado == self.colunas_estados["Concluído"]
            if concluido:
                itens_concluidos += 1
                esforco_concluido += item["esforco"] or 0

            # Conta adições no meio da sprint
            if item["adicionado_meio_sprint"]:
                insights["adicoes_meio_sprint"] += 1

            # Soma esforço
            item_esforco = item["esforco"] or 0
            esforco_total += item_esforco
            insights["esforco_total"] = esforco_total

            # Rastreia carga de trabalho por responsável
            responsavel = item["responsavel_atual"]
            if responsavel not in insights["carga_trabalho_responsaveis"]:
                insights["carga_trabalho_responsaveis"][responsavel] = {
                    "contagem": 0,
                    "esforco": 0,
                }

            insights["carga_trabalho_responsaveis"][responsavel]["contagem"] += 1
            insights["carga_trabalho_responsaveis"][responsavel][
                "esforco"
            ] += item_esforco

        # Calcula percentual de conclusão baseado em quantidade de itens
        if insights["total_itens"] > 0:
            insights["percentual_concluido"] = (
                itens_concluidos / insights["total_itens"]
            ) * 100
        else:
            insights["percentual_concluido"] = 0

        # Calcula percentual de conclusão baseado em esforço
        if esforco_total > 0:
            insights["percentual_esforco_concluido"] = (
                esforco_concluido / esforco_total
            ) * 100
        else:
            insights["percentual_esforco_concluido"] = 0

        # Armazena os valores absolutos para referência
        insights["itens_concluidos"] = itens_concluidos
        insights["esforco_concluido"] = esforco_concluido

        return insights

    def _analisar_retornos(self, insights, dados_processados):
        """Analisa retornos de itens no fluxo de trabalho."""
        itens_retorno = set()

        for item in dados_processados:
            if item["retornos"]:
                insights["retornos"] += len(item["retornos"])
                itens_retorno.add(item["id"])

                for retorno in item["retornos"]:
                    insights["detalhes_retornos"].append(
                        {
                            "id_item": item["id"],
                            "titulo": item["titulo"],
                            "de": retorno["de"],
                            "para": retorno["para"],
                            "data": retorno["data"],
                        }
                    )

        insights["retornos_unicos"] = len(itens_retorno)
        return insights

    def _analisar_tempo_colunas(self, insights, dados_processados):
        """Analisa tempo médio em cada coluna."""
        tempos_coluna = {coluna: [] for coluna in self.colunas_estados.keys()}

        for item in dados_processados:
            for coluna, datas in item["transicoes_coluna"].items():
                if len(datas) >= 2:
                    # Calcula diferença entre primeira e última entrada
                    primeira_data = datetime.fromisoformat(
                        datas[0].replace("Z", "+00:00")
                    )
                    ultima_data = datetime.fromisoformat(
                        datas[-1].replace("Z", "+00:00")
                    )

                    diferenca_horas = (
                        ultima_data - primeira_data
                    ).total_seconds() / 3600

                    if coluna in tempos_coluna:
                        tempos_coluna[coluna].append(diferenca_horas)

        # Calcula médias
        for coluna, tempos in tempos_coluna.items():
            if tempos:
                insights["tempo_medio_colunas"][coluna] = sum(tempos) / len(tempos)
            else:
                insights["tempo_medio_colunas"][coluna] = 0

        return insights

    def _analisar_chamados(self, insights, dados_processados, pasta_saida):
        """Analisa métricas relacionadas a chamados."""
        # Carrega dados brutos para verificar tags
        try:
            with open(pasta_saida / "dados_brutos.json", "r") as f:
                dados_brutos = json.load(f)
        except FileNotFoundError:
            logger.error(f"Arquivo de dados brutos não encontrado em {pasta_saida}")
            return insights

        # Mapeia IDs para facilitar busca
        mapa_itens = {str(item["id"]): item for item in dados_brutos}

        # Conta chamados
        chamados_total = 0
        chamados_concluidos = 0

        for item in dados_processados:
            item_bruto = mapa_itens.get(str(item["id"]))

            if not item_bruto:
                continue

            tags = item_bruto["fields"].get("System.Tags", "").lower()

            if "chamado" in tags:
                chamados_total += 1

                # Verifica se está concluído
                concluido = (
                    item["estado"] == "Done"
                    or item["estado"] == self.colunas_estados["Concluído"]
                )
                if concluido:
                    chamados_concluidos += 1

        insights["total_chamados"] = chamados_total
        insights["chamados_concluidos"] = chamados_concluidos

        # Calcula percentual de conclusão
        if chamados_total > 0:
            insights["percentual_chamados_concluidos"] = (
                chamados_concluidos / chamados_total
            ) * 100
        else:
            insights["percentual_chamados_concluidos"] = 0

        return insights

    def _exportar_para_csv(self, dados_processados, pasta_saida):
        """
        Exporta dados processados para CSVs para análise adicional.

        Parameters
        ----------
        dados_processados : list
            Lista de itens processados
        pasta_saida : Path
            Caminho para salvar os arquivos CSV
        """
        # Dados principais dos itens
        dados_itens = []
        for item in dados_processados:
            item_base = {
                "id": item["id"],
                "titulo": item["titulo"],
                "tipo": item["tipo"],
                "estado": item["estado"],
                "esforco": item["esforco"],
                "responsavel_atual": item["responsavel_atual"],
                "data_criacao": item["data_criacao"],
                "adicionado_meio_sprint": item["adicionado_meio_sprint"],
            }
            dados_itens.append(item_base)

        itens_df = pd.DataFrame(dados_itens)
        itens_df.to_csv(pasta_saida / "itens.csv", index=False)

        # Dados de transições
        dados_transicoes = []
        for item in dados_processados:
            for coluna, datas in item["transicoes_coluna"].items():
                for data in datas:
                    dados_transicoes.append(
                        {
                            "id_item": item["id"],
                            "coluna": coluna,
                            "data_transicao": data,
                        }
                    )

        transicoes_df = pd.DataFrame(dados_transicoes)
        if not transicoes_df.empty:
            transicoes_df.to_csv(pasta_saida / "transicoes.csv", index=False)

        # Dados de retornos
        dados_retornos = []
        for item in dados_processados:
            for retorno in item["retornos"]:
                dados_retornos.append(
                    {
                        "id_item": item["id"],
                        "coluna_origem": retorno["de"],
                        "coluna_destino": retorno["para"],
                        "data_retorno": retorno["data"],
                    }
                )

        retornos_df = pd.DataFrame(dados_retornos)
        if not retornos_df.empty:
            retornos_df.to_csv(pasta_saida / "retornos.csv", index=False)

        # Dados de histórico de responsáveis
        dados_responsaveis = []
        for item in dados_processados:
            for atribuicao in item["historico_responsaveis"]:
                dados_responsaveis.append(
                    {
                        "id_item": item["id"],
                        "responsavel": atribuicao["responsavel"],
                        "data_atribuicao": atribuicao["data"],
                    }
                )

        responsaveis_df = pd.DataFrame(dados_responsaveis)
        if not responsaveis_df.empty:
            responsaveis_df.to_csv(pasta_saida / "responsaveis.csv", index=False)

    def _exportar_dados_completos(self, nome_sprint, pasta_saida):
        """
        Exporta dados detalhados dos work items para CSV.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint
        pasta_saida : Path
            Caminho para salvar o CSV

        Returns
        -------
        str
            Caminho do arquivo CSV gerado
        """
        logger.info("Exportando dados completos dos work items")

        try:
            # Lê os dados brutos
            with open(pasta_saida / "dados_brutos.json", "r") as f:
                dados_brutos = json.load(f)
        except FileNotFoundError:
            logger.error(f"Arquivo de dados brutos não encontrado em {pasta_saida}")
            return None

        # Processa cada item
        itens_completos = []

        for item in dados_brutos:
            campos = {}

            # Informações básicas
            campos["ID"] = item["id"]
            campos["Tipo"] = item["fields"].get("System.WorkItemType", "")
            campos["Titulo"] = item["fields"].get("System.Title", "")
            campos["Estado"] = item["fields"].get("System.State", "")
            campos["Criado_Em"] = item["fields"].get("System.CreatedDate", "")
            campos["Alterado_Em"] = item["fields"].get("System.ChangedDate", "")

            # Data de entrada para cada estado
            for nome_coluna, estado_azure in self.colunas_estados.items():
                data_entrada = ""
                for rev in item.get("revisoes", []):
                    if rev.get("fields", {}).get("System.State") == estado_azure:
                        data_entrada = rev.get("fields", {}).get(
                            "System.ChangedDate", ""
                        )
                        break

                campos[f"Data_Entrada_{nome_coluna}"] = data_entrada

            # Informações detalhadas
            campos["Prioridade"] = item["fields"].get(
                "Microsoft.VSTS.Common.Priority", ""
            )
            campos["Esforco"] = item["fields"].get(
                "Microsoft.VSTS.Scheduling.Effort", ""
            )
            campos["Area_Path"] = item["fields"].get("System.AreaPath", "")
            campos["Iteration_Path"] = item["fields"].get("System.IterationPath", "")

            # Datas da sprint
            campos["Sprint_Inicio"] = item["fields"].get(
                "System.IterationStartDate", ""
            )
            campos["Sprint_Fim"] = item["fields"].get("System.IterationEndDate", "")

            # Pessoas envolvidas
            campos["Criado_Por"] = self._extrair_nome_pessoa(
                item["fields"].get("System.CreatedBy")
            )
            campos["Responsavel"] = self._extrair_nome_pessoa(
                item["fields"].get("System.AssignedTo")
            )
            campos["Alterado_Por"] = self._extrair_nome_pessoa(
                item["fields"].get("System.ChangedBy")
            )

            # Tags
            campos["Tags"] = item["fields"].get("System.Tags", "")

            # Campos adicionais
            campos["Razao"] = item["fields"].get("System.Reason", "")

            # Verifica se adicionado no meio da sprint
            if campos["Sprint_Inicio"] and campos["Criado_Em"]:
                try:
                    inicio_sprint = datetime.fromisoformat(
                        campos["Sprint_Inicio"].replace("Z", "+00:00")
                    )
                    data_criacao = datetime.fromisoformat(
                        campos["Criado_Em"].replace("Z", "+00:00")
                    )
                    campos["Adicionado_Meio_Sprint"] = data_criacao > inicio_sprint
                except:
                    campos["Adicionado_Meio_Sprint"] = False
            else:
                campos["Adicionado_Meio_Sprint"] = False

            # Análise de retornos
            campos["Possui_Retornos"], campos["Maior_Estado_Atingido"] = (
                self._analisar_retornos_item(item)
            )

            # Tempo total
            if campos["Criado_Em"] and campos["Alterado_Em"]:
                try:
                    data_criacao = datetime.fromisoformat(
                        campos["Criado_Em"].replace("Z", "+00:00")
                    )
                    data_alteracao = datetime.fromisoformat(
                        campos["Alterado_Em"].replace("Z", "+00:00")
                    )
                    tempo_total = (data_alteracao - data_criacao).total_seconds() / 3600
                    campos["Tempo_Total_Horas"] = round(tempo_total, 2)
                except:
                    campos["Tempo_Total_Horas"] = 0
            else:
                campos["Tempo_Total_Horas"] = 0

            itens_completos.append(campos)

        # Cria DataFrame
        df_completo = pd.DataFrame(itens_completos)

        # Melhora nomes de colunas
        renomeacoes = {
            "Titulo": "Título",
            "Criado_Em": "Criado Em",
            "Alterado_Em": "Alterado Em",
            "Area_Path": "Caminho da Área",
            "Iteration_Path": "Caminho da Iteração",
            "Sprint_Inicio": "Início da Sprint",
            "Sprint_Fim": "Fim da Sprint",
            "Criado_Por": "Criado Por",
            "Alterado_Por": "Alterado Por",
            "Razao": "Razão",
            "Adicionado_Meio_Sprint": "Adicionado no Meio da Sprint",
            "Possui_Retornos": "Possui Retornos",
            "Maior_Estado_Atingido": "Maior Estado Atingido",
            "Tempo_Total_Horas": "Tempo Total (Horas)",
        }

        df_completo = df_completo.rename(columns=renomeacoes)

        # Melhora nomes de colunas de data
        for coluna in df_completo.columns:
            if coluna.startswith("Data_Entrada_"):
                nova_coluna = coluna.replace("Data_Entrada_", "Data Entrada ")
                df_completo = df_completo.rename(columns={coluna: nova_coluna})

        # Salva CSV
        nome_arquivo = pasta_saida / "detalhes_completos.csv"
        df_completo.to_csv(nome_arquivo, index=False, encoding="utf-8-sig")

        logger.info(f"Dados completos exportados para {nome_arquivo}")

        return str(nome_arquivo)

    def _extrair_nome_pessoa(self, campo):
        """Extrai nome de pessoa de campo do Azure DevOps."""
        if isinstance(campo, dict) and "displayName" in campo:
            return campo["displayName"]
        return ""

    def _analisar_retornos_item(self, item):
        """Analisa retornos de um item para verificar se houve movimentação para trás."""
        possui_retornos = False
        maior_estado_atingido = ""

        # Ordem das colunas do fluxo
        ordem_colunas = list(self.colunas_estados.keys())
        ultimo_indice_coluna_maior = -1

        # Processa revisões
        for rev in item.get("revisoes", []):
            if "System.State" in rev.get("fields", {}):
                estado = rev["fields"]["System.State"]

                # Mapeia para coluna
                coluna = next(
                    (k for k, v in self.colunas_estados.items() if v == estado),
                    estado,
                )

                if coluna in ordem_colunas:
                    indice_atual = ordem_colunas.index(coluna)

                    # Verifica se é um retorno
                    if indice_atual < ultimo_indice_coluna_maior:
                        possui_retornos = True

                    # Atualiza maior estado
                    if indice_atual > ultimo_indice_coluna_maior:
                        ultimo_indice_coluna_maior = indice_atual
                        if (
                            ultimo_indice_coluna_maior >= 0
                            and ultimo_indice_coluna_maior < len(ordem_colunas)
                        ):
                            maior_estado_atingido = ordem_colunas[
                                ultimo_indice_coluna_maior
                            ]

        return possui_retornos, maior_estado_atingido
