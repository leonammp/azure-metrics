import matplotlib.pyplot as plt
import seaborn as sns
import base64
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from jinja2 import Template

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Classe para geração de relatórios e visualizações dos dados de sprint."""

    def __init__(self, sprint_analyzer):
        """
        Inicializa o gerador de relatórios.

        Parameters
        ----------
        sprint_analyzer : SprintAnalyzer
            Analisador de sprint para acesso a dados e configurações
        """
        self.sprint_analyzer = sprint_analyzer

        # Configura o estilo para visualizações
        sns.set_style("whitegrid")
        plt.rcParams["figure.figsize"] = (14, 8)
        plt.rcParams["font.family"] = "DejaVu Sans"

    def gerar_visualizacoes(self, dados_processados, nome_sprint, pasta_saida):
        """
        Gera visualizações para os dados da sprint.

        Parameters
        ----------
        dados_processados : list
            Lista de itens processados
        nome_sprint : str
            Nome da sprint
        pasta_saida : Path
            Caminho para salvar as visualizações
        """
        logger.info(f"Gerando visualizações para sprint: {nome_sprint}")

        # Gera gráficos de análise
        self._visualizar_itens_por_tipo(dados_processados, nome_sprint, pasta_saida)
        self._visualizar_itens_por_estado(dados_processados, nome_sprint, pasta_saida)
        self._visualizar_carga_trabalho(dados_processados, nome_sprint, pasta_saida)
        self._visualizar_adicoes_sprint(dados_processados, nome_sprint, pasta_saida)
        self._visualizar_tempo_colunas(dados_processados, nome_sprint, pasta_saida)
        self._visualizar_retornos(dados_processados, nome_sprint, pasta_saida)

    def gerar_relatorio_executivo(self, nome_sprint, pasta_saida):
        """
        Gera relatório executivo HTML com insights e visualizações.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint
        pasta_saida : Path
            Caminho com dados e visualizações

        Returns
        -------
        str
            Caminho para o relatório HTML gerado
        """
        logger.info(f"Gerando relatório executivo para sprint: {nome_sprint}")

        arquivo_saida = pasta_saida / "relatorio_executivo.html"

        # Verifica se temos os dados necessários
        if not (pasta_saida / "insights.json").exists():
            logger.error(f"Arquivo de insights não encontrado em {pasta_saida}")
            return None

        # Carrega os insights
        with open(pasta_saida / "insights.json", "r") as f:
            insights = json.load(f)

        # Converte imagens para base64
        imagens_base64 = self._converter_imagens_para_base64(pasta_saida)

        # Carrega o template HTML
        template_path = (
            Path(__file__).parent.parent.parent / "templates" / "relatorio.html"
        )

        if not template_path.exists():
            # Se o template não existir, usa o template embutido
            html = self._gerar_html_relatorio(insights, imagens_base64, nome_sprint)
        else:
            # Usa o template do arquivo
            with open(template_path, "r", encoding="utf-8") as f:
                template = Template(f.read())

            html = template.render(
                insights=insights,
                imagens=imagens_base64,
                nome_sprint=nome_sprint,
                data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            )

        # Salva o relatório
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Relatório executivo gerado: {arquivo_saida}")

        return str(arquivo_saida)

    def _visualizar_itens_por_tipo(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráfico de itens por tipo."""
        # Calcula contagens
        contagens_tipo = {}
        for item in dados_processados:
            tipo_item = item["tipo"]
            if tipo_item not in contagens_tipo:
                contagens_tipo[tipo_item] = 0
            contagens_tipo[tipo_item] += 1

        # Gera o gráfico
        plt.figure()
        sns.barplot(x=list(contagens_tipo.keys()), y=list(contagens_tipo.values()))
        plt.title(f"Itens de Trabalho por Tipo - {nome_sprint}")
        plt.xlabel("Tipo de Item")
        plt.ylabel("Quantidade")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "itens_por_tipo.png")
        plt.close()

    def _visualizar_itens_por_estado(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráfico de itens por estado atual."""
        # Calcula contagens
        contagens_estado = {}
        for item in dados_processados:
            estado = item["estado"]
            if estado not in contagens_estado:
                contagens_estado[estado] = 0
            contagens_estado[estado] += 1

        # Gera o gráfico
        plt.figure()
        sns.barplot(x=list(contagens_estado.keys()), y=list(contagens_estado.values()))
        plt.title(f"Itens de Trabalho por Estado Atual - {nome_sprint}")
        plt.xlabel("Estado")
        plt.ylabel("Quantidade")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "itens_por_estado.png")
        plt.close()

    def _visualizar_carga_trabalho(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráficos de carga de trabalho por responsável."""
        # Calcula contagens e esforço
        contagens_responsavel = {}
        esforco_responsavel = {}

        for item in dados_processados:
            responsavel = item["responsavel_atual"]
            if responsavel not in contagens_responsavel:
                contagens_responsavel[responsavel] = 0
                esforco_responsavel[responsavel] = 0

            contagens_responsavel[responsavel] += 1
            esforco_responsavel[responsavel] += item["esforco"] or 0

        # Gráfico de quantidade de itens
        plt.figure()
        sns.barplot(
            x=list(contagens_responsavel.keys()), y=list(contagens_responsavel.values())
        )
        plt.title(f"Itens de Trabalho por Responsável - {nome_sprint}")
        plt.xlabel("Responsável")
        plt.ylabel("Número de Itens")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "itens_por_responsavel.png")
        plt.close()

        # Gráfico de esforço total
        plt.figure()
        sns.barplot(
            x=list(esforco_responsavel.keys()), y=list(esforco_responsavel.values())
        )
        plt.title(f"Esforço por Responsável - {nome_sprint}")
        plt.xlabel("Responsável")
        plt.ylabel("Pontos de Esforço Total")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "esforco_por_responsavel.png")
        plt.close()

    def _visualizar_adicoes_sprint(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráfico de adições no meio da sprint."""
        # Calcula contagens
        contagem_meio_sprint = sum(
            1 for item in dados_processados if item["adicionado_meio_sprint"]
        )
        contagem_inicial = len(dados_processados) - contagem_meio_sprint

        # Gera o gráfico
        plt.figure()
        sns.barplot(
            x=["Itens Iniciais", "Adicionados no Meio da Sprint"],
            y=[contagem_inicial, contagem_meio_sprint],
        )
        plt.title(f"Itens Iniciais vs. Adições no Meio da Sprint - {nome_sprint}")
        plt.ylabel("Quantidade")
        plt.tight_layout()
        plt.savefig(pasta_saida / "adicoes_meio_sprint.png")
        plt.close()

    def _visualizar_tempo_colunas(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráfico de tempo médio em cada coluna."""
        # Calcula tempo médio por coluna
        tempos_medios_coluna = {}
        for coluna in self.sprint_analyzer.colunas_estados.keys():
            tempos_coluna = []

            for item in dados_processados:
                transicoes = item.get("transicoes_coluna", {}).get(coluna, [])
                if len(transicoes) >= 2:
                    primeira = datetime.fromisoformat(
                        transicoes[0].replace("Z", "+00:00")
                    )
                    ultima = datetime.fromisoformat(
                        transicoes[-1].replace("Z", "+00:00")
                    )
                    horas = (ultima - primeira).total_seconds() / 3600
                    tempos_coluna.append(horas)

            if tempos_coluna:
                tempos_medios_coluna[coluna] = sum(tempos_coluna) / len(tempos_coluna)
            else:
                tempos_medios_coluna[coluna] = 0

        # Gera o gráfico
        plt.figure()
        sns.barplot(
            x=list(tempos_medios_coluna.keys()), y=list(tempos_medios_coluna.values())
        )
        plt.title(f"Tempo Médio em Coluna (Horas) - {nome_sprint}")
        plt.xlabel("Coluna")
        plt.ylabel("Horas")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "tempo_medio_coluna.png")
        plt.close()

    def _visualizar_retornos(self, dados_processados, nome_sprint, pasta_saida):
        """Gera gráfico de retornos entre estados."""
        # Verifica se temos retornos para visualizar
        if not any(item["retornos"] for item in dados_processados):
            return

        # Calcula contagens de retornos por transição
        contagens_retorno = {}
        for item in dados_processados:
            for retorno in item["retornos"]:
                transicao = f"{retorno['de']} -> {retorno['para']}"
                if transicao not in contagens_retorno:
                    contagens_retorno[transicao] = 0
                contagens_retorno[transicao] += 1

        # Gera o gráfico
        plt.figure()
        sns.barplot(
            x=list(contagens_retorno.keys()), y=list(contagens_retorno.values())
        )
        plt.title(f"Retornos por Transição - {nome_sprint}")
        plt.xlabel("Transição")
        plt.ylabel("Quantidade")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(pasta_saida / "retornos.png")
        plt.close()

    def _converter_imagens_para_base64(self, pasta_saida):
        """Converte imagens para strings base64 para inclusão no HTML."""
        # Lista de arquivos de imagem para converter
        arquivos_imagem = [
            "itens_por_tipo.png",
            "itens_por_estado.png",
            "itens_por_responsavel.png",
            "esforco_por_responsavel.png",
            "tempo_medio_coluna.png",
            "adicoes_meio_sprint.png",
            "retornos.png",
        ]

        # Função para converter uma imagem para base64
        def img_to_base64(img_path):
            if not os.path.exists(img_path):
                return ""
            with open(img_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")

        # Converte todas as imagens
        imagens_base64 = {}
        for arquivo in arquivos_imagem:
            chave = arquivo.replace(".png", "")
            imagens_base64[chave] = img_to_base64(pasta_saida / arquivo)

        return imagens_base64

    def _gerar_html_relatorio(self, insights, imagens_base64, nome_sprint):
        """Gera HTML para o relatório executivo."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Análise de Sprint - {nome_sprint}</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #0078d4;
                }}
                .dashboard {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: #f9f9f9;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #0078d4;
                    margin-bottom: 8px;
                }}
                .metric-label {{
                    font-size: 14px;
                    color: #666;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .warning {{
                    color: #e74c3c;
                }}
                .success {{
                    color: #27ae60;
                }}
                .image-container {{
                    margin: 20px 0;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 4px;
                }}
                .progress-container {{
                    width: 100%;
                    background-color: #f1f1f1;
                    border-radius: 4px;
                    margin: 10px 0;
                }}
                .progress-bar {{
                    height: 20px;
                    border-radius: 4px;
                    background-color: #4CAF50;
                }}
                .stats-container {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }}
                .stat {{
                    font-weight: bold;
                }}
                @media print {{
                    .card {{
                        break-inside: avoid;
                    }}
                    .image-container {{
                        break-inside: avoid;
                        page-break-inside: avoid;
                    }}
                }}
            </style>
        </head>
        <body>
            <h1>Relatório de Análise de Sprint</h1>
            <h2>{nome_sprint}</h2>
            
            <div class="dashboard">
                <div class="card">
                    <div class="metric">{insights["total_itens"]}</div>
                    <div class="metric-label">Total de Itens de Trabalho</div>
                </div>
                <div class="card">
                    <div class="metric">{insights["esforco_total"]}</div>
                    <div class="metric-label">Pontos de Esforço Total</div>
                </div>
                <div class="card">
                    <div class="metric">{insights["percentual_concluido"]:.1f}%</div>
                    <div class="metric-label">Taxa de Conclusão</div>
                </div>
                <div class="card">
                    <div class="metric">{insights["adicoes_meio_sprint"]}</div>
                    <div class="metric-label">Itens Adicionados no Meio da Sprint</div>
                </div>
            </div>
            
            <!-- SEÇÃO: Análise de Chamados -->
            <h3>Análise de Chamados</h3>
            <div class="card">
                <div class="stats-container">
                    <div class="stat">Total de Chamados: {insights.get("total_chamados", 0)}</div>
                    <div class="stat">Chamados Concluídos: {insights.get("chamados_concluidos", 0)}</div>
                    <div class="stat">Percentual: {insights.get("percentual_chamados_concluidos", 0):.1f}%</div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {insights.get("percentual_chamados_concluidos", 0)}%"></div>
                </div>
                <p>Esta sprint continha <strong>{insights.get("total_chamados", 0)}</strong> chamados, dos quais <strong>{insights.get("chamados_concluidos", 0)}</strong> foram concluídos,
                representando uma taxa de conclusão de <strong>{insights.get("percentual_chamados_concluidos", 0):.1f}%</strong>.</p>
            </div>
            
            <h3>Resumo da Sprint</h3>
            <p>
                Esta sprint continha {insights["total_itens"]} itens de trabalho com um esforço total de 
                {insights["esforco_total"]} pontos. {insights["percentual_concluido"]:.1f}% dos itens 
                foram concluídos até o final da sprint.
            </p>
            <p>
                {insights["adicoes_meio_sprint"]} itens foram adicionados após o início da sprint, 
                representando {(insights["adicoes_meio_sprint"] / insights["total_itens"] * 100 if insights["total_itens"] > 0 else 0):.1f}% do trabalho total.
            </p>
            <p>
                Houve {insights["retornos_unicos"]} itens que experimentaram retornos 
                (movendo-se para trás no fluxo de trabalho), com um total de {insights["retornos"]} transições de retorno.
            </p>
            
            <h3>Itens de Trabalho por Tipo</h3>
            <div class="image-container">
                <img src="data:image/png;base64,{imagens_base64['itens_por_tipo']}" alt="Itens por Tipo">
            </div>
            
            <h3>Distribuição de Estado Atual</h3>
            <div class="image-container">
                <img src="data:image/png;base64,{imagens_base64['itens_por_estado']}" alt="Itens por Estado">
            </div>
            
            <h3>Carga de Trabalho da Equipe</h3>
            <div class="image-container">
                <img src="data:image/png;base64,{imagens_base64['itens_por_responsavel']}" alt="Itens por Responsável">
            </div>
            <div class="image-container">
                <img src="data:image/png;base64,{imagens_base64['esforco_por_responsavel']}" alt="Esforço por Responsável">
            </div>
            
            <h3>Eficiência do Processo</h3>
            <div class="image-container">
                <img src="data:image/png;base64,{imagens_base64['tempo_medio_coluna']}" alt="Tempo Médio em Coluna">
            </div>
            
            {'<h3>Análise de Retornos</h3><p>' + str(insights["retornos_unicos"]) + ' itens experimentaram ' + str(insights["retornos"]) + ' transições de retorno. Isso pode indicar problemas com o processo de desenvolvimento ou controle de qualidade.</p><div class="image-container"><img src="data:image/png;base64,' + imagens_base64['retornos'] + '" alt="Análise de Retornos"></div>' if imagens_base64.get('retornos') else ''}
            
            <h3>Recomendações</h3>
            <ul>
                <li>Revisar o processo para itens com longos tempos de ciclo para identificar gargalos</li>
                <li>Analisar retornos para melhorar a qualidade e reduzir o retrabalho</li>
                <li>Avaliar a capacidade da equipe com base no trabalho concluído versus planejado</li>
                <li>Considerar o balanceamento da carga de trabalho dos membros da equipe com base nos dados de responsáveis</li>
                <li>Revisar adições no meio da sprint para melhorar o planejamento da sprint</li>
            </ul>
            
            <p><em>Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} pelo time de Payments 💙 | Sistema Boletinho Analytics</em></p>
        </body>
        </html>
        """
