import json
import os
import logging
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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

    def gerar_graficos_plotly(self, dados_processados, nome_sprint):
        """
        Gera gráficos interativos Plotly para os dados da sprint.

        Parameters
        ----------
        dados_processados : list
            Lista de itens processados
        nome_sprint : str
            Nome da sprint

        Returns
        -------
        dict
            Dicionário com objetos de figura do Plotly
        """
        logger.info(f"Gerando gráficos interativos para sprint: {nome_sprint}")

        graficos = {}

        # Implementação dos gráficos interativos
        # Esta função será implementada posteriormente

        return graficos

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

        # Carrega dados processados para gerar gráficos Plotly
        dados_processados_path = pasta_saida / "dados_processados.json"
        if dados_processados_path.exists():
            with open(dados_processados_path, "r") as f:
                dados_processados = json.load(f)
            # Gera gráficos Plotly
            graficos_plotly = self.gerar_graficos_plotly(dados_processados, nome_sprint)
        else:
            logger.error(
                f"Arquivo de dados processados não encontrado: {dados_processados_path}"
            )
            graficos_plotly = {}

        # Gera HTML com os gráficos Plotly
        html_content = self._gerar_html_com_plotly(
            nome_sprint, insights, graficos_plotly
        )

        # Salva o relatório
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Relatório executivo gerado: {arquivo_saida}")

        return str(arquivo_saida)

    def _gerar_html_com_plotly(self, nome_sprint, insights, graficos_plotly):
        """
        Gera HTML com gráficos Plotly embutidos.

        Parameters
        ----------
        nome_sprint : str
            Nome da sprint
        insights : dict
            Insights da análise
        graficos_plotly : dict
            Dicionário com objetos de figura do Plotly

        Returns
        -------
        str
            HTML gerado
        """
        # Gera os gráficos como HTML
        graficos_html = {}

        # Só inclui o Plotly.js uma vez
        include_plotlyjs = "cdn"

        for nome, fig in graficos_plotly.items():
            try:
                graficos_html[nome] = fig.to_html(
                    include_plotlyjs=include_plotlyjs,
                    full_html=False,
                    config={"responsive": True},
                )
                # Depois do primeiro gráfico, não precisamos incluir o plotly.js novamente
                include_plotlyjs = False
            except Exception as e:
                logger.error(f"Erro ao converter gráfico Plotly para HTML: {str(e)}")
                graficos_html[nome] = f"<div>Erro ao gerar gráfico: {nome}</div>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Análise de Sprint - {nome_sprint}</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                h1, h2, h3 {{
                    color: #0078d4;
                    font-weight: 500;
                }}
                .dashboard {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 16px;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .card:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .metric {{
                    font-size: 28px;
                    font-weight: 600;
                    color: #0078d4;
                    margin-bottom: 8px;
                }}
                .metric-label {{
                    font-size: 14px;
                    color: #666;
                    font-weight: 500;
                }}
                .section-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 24px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    margin-bottom: 24px;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #0078d4;
                    margin-bottom: 16px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #f0f0f0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                th, td {{
                    padding: 12px 16px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f7fd;
                    color: #0078d4;
                    font-weight: 500;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f2f7fd;
                }}
                .warning {{
                    color: #e74c3c;
                }}
                .success {{
                    color: #27ae60;
                }}
                .image-container {{
                    margin: 20px 0;
                    max-width: 100%;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                }}
                .progress-container {{
                    width: 100%;
                    background-color: #f1f1f1;
                    border-radius: 20px;
                    margin: 10px 0;
                    overflow: hidden;
                }}
                .progress-bar {{
                    height: 12px;
                    border-radius: 20px;
                    background: linear-gradient(90deg, #0078d4, #00b7c3);
                }}
                .stats-container {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }}
                .stat {{
                    font-weight: 500;
                }}
                .two-columns {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 24px;
                }}
                @media print {{
                    .card, .section-card {{
                        break-inside: avoid;
                        box-shadow: none;
                        border: 1px solid #eee;
                    }}
                    .image-container {{
                        break-inside: avoid;
                        page-break-inside: avoid;
                        box-shadow: none;
                    }}
                }}
                @media (max-width: 768px) {{
                    .dashboard {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                    .two-columns {{
                        grid-template-columns: 1fr;
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
                    <div class="metric-label">Taxa de Conclusão (Tasks)</div>
                </div>
                <div class="card">
                    <div class="metric">{insights.get("percentual_esforco_concluido", 0):.1f}%</div>
                    <div class="metric-label">Taxa de Conclusão (Esforço)</div>
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
                {graficos_html.get('itens_por_tipo', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Distribuição de Estado Atual</h3>
            <div class="image-container">
                {graficos_html.get('itens_por_estado', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Carga de Trabalho da Equipe</h3>
            <div class="image-container">
                {graficos_html.get('itens_por_responsavel', '<div>Gráfico não disponível</div>')}
            </div>
            <div class="image-container">
                {graficos_html.get('esforco_por_responsavel', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Eficiência do Processo</h3>
            <div class="image-container">
                {graficos_html.get('tempo_medio_coluna', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Adições no Meio da Sprint</h3>
            <div class="image-container">
                {graficos_html.get('adicoes_meio_sprint', '<div>Gráfico não disponível</div>')}
            </div>
            
            {'<h3>Análise de Retornos</h3><p>' + str(insights["retornos_unicos"]) + ' itens experimentaram ' + str(insights["retornos"]) + ' transições de retorno. Isso pode indicar problemas com o processo de desenvolvimento ou controle de qualidade.</p><div class="image-container">' + graficos_html.get('retornos', '<div>Gráfico não disponível</div>') + '</div>' if 'retornos' in graficos_html else ''}
            
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

        return html

    def gerar_relatorio_consolidado(self, nomes_sprints, pasta_saida):
        """
        Gera relatório consolidado para múltiplas sprints.

        Parameters
        ----------
        nomes_sprints : list
            Lista de nomes das sprints
        pasta_saida : Path
            Caminho para a pasta de saída

        Returns
        -------
        str
            Caminho para o relatório gerado
        """
        logger.info(f"Gerando relatório consolidado para {len(nomes_sprints)} sprints")

        arquivo_saida = pasta_saida / "relatorio_consolidado.html"

        # Carrega os insights consolidados
        with open(pasta_saida / "insights_consolidados.json", "r") as f:
            insights_consolidados = json.load(f)

        # Gera gráficos de tendência com Plotly diretamente a partir dos insights consolidados
        graficos_tendencia = self._gerar_graficos_tendencia_plotly(
            insights_consolidados
        )

        # Gera o HTML com o conteúdo estático para as sprints individuais
        # Em vez de tentar carregar dados processados que não encontramos
        html_content = self._gerar_html_consolidado_simplificado(
            nomes_sprints, insights_consolidados, graficos_tendencia
        )

        # Salva o relatório
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Relatório consolidado gerado: {arquivo_saida}")

        return str(arquivo_saida)

    def _gerar_html_consolidado_simplificado(
        self, nomes_sprints, insights_consolidados, graficos_tendencia
    ):
        """
        Gera HTML consolidado com gráficos Plotly para tendências e tabelas para detalhes.

        Parameters
        ----------
        nomes_sprints : list
            Lista de nomes das sprints
        insights_consolidados : dict
            Insights consolidados
        graficos_tendencia : dict
            Gráficos de tendência Plotly

        Returns
        -------
        str
            HTML gerado
        """
        # Converte os gráficos de tendência para HTML
        include_plotlyjs = "cdn"

        graficos_tendencia_html = {}
        for nome, fig in graficos_tendencia.items():
            graficos_tendencia_html[nome] = fig.to_html(
                include_plotlyjs=include_plotlyjs,
                full_html=False,
                config={"responsive": True},
            )
            include_plotlyjs = False  # Depois do primeiro gráfico, não precisamos incluir o plotly.js novamente

        # Gera HTML para tabelas de sprint em vez de gráficos interativos
        sprint_sections_html = ""
        for sprint in nomes_sprints:
            if sprint in insights_consolidados["por_sprint"]:
                sprint_data = insights_consolidados["por_sprint"][sprint]

                # Cria tabela de dados para esta sprint
                sprint_table = f"""
                <table class="sprint-details-table">
                    <tr>
                        <th>Métrica</th>
                        <th>Valor</th>
                    </tr>
                    <tr>
                        <td>Total de Itens</td>
                        <td>{sprint_data.get('total_itens', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Esforço Total</td>
                        <td>{sprint_data.get('esforco_total', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Taxa de Conclusão</td>
                        <td>{sprint_data.get('percentual_concluido', 'N/A'):.1f}%</td>
                    </tr>
                    <tr>
                        <td>Adições no Meio da Sprint</td>
                        <td>{sprint_data.get('adicoes_meio_sprint', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Retornos</td>
                        <td>{sprint_data.get('retornos', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Chamados</td>
                        <td>{sprint_data.get('total_chamados', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Chamados Concluídos</td>
                        <td>{sprint_data.get('chamados_concluidos', 'N/A')}</td>
                    </tr>
                </table>
                """

                sprint_section = f"""
                <button class="collapsible">{sprint}</button>
                <div class="content">
                    <div class="sprint-section">
                        <div class="sprint-title">{sprint}</div>
                        <h4>Detalhes da Sprint</h4>
                        {sprint_table}
                        <p>Para visualizar gráficos detalhados, acesse o relatório individual desta sprint.</p>
                    </div>
                </div>
                """
                sprint_sections_html += sprint_section

        # Gera o HTML completo
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório Consolidado de Sprints</title>
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
                
                h1, h2, h3, h4 {{
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
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
                
                .sprint-section {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 25px 0;
                }}
                
                .sprint-title {{
                    background-color: #0078d4;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 5px;
                    display: inline-block;
                    margin-bottom: 15px;
                }}
                
                .sprint-details-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                .sprint-details-table th, .sprint-details-table td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                }}
                
                .sprint-details-table th {{
                    background-color: #f5f5f5;
                }}
                
                .collapsible {{
                    background-color: #f1f1f1;
                    color: #444;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    font-size: 16px;
                    border-radius: 5px;
                    margin-bottom: 5px;
                }}
                
                .active, .collapsible:hover {{
                    background-color: #ddd;
                }}
                
                .content {{
                    padding: 0 18px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                    background-color: #f9f9f9;
                    border-radius: 0 0 5px 5px;
                }}
                
                @media print {{
                    .card, .sprint-section {{
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
            <h1>Relatório Consolidado de Sprints</h1>
            <h2>Sprints: {', '.join(nomes_sprints)}</h2>
            
            <div class="dashboard">
                <div class="card">
                    <div class="metric">{insights_consolidados["total_sprints"]}</div>
                    <div class="metric-label">Total de Sprints Analisadas</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["total_itens"]}</div>
                    <div class="metric-label">Total de Itens de Trabalho</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["total_esforco"]}</div>
                    <div class="metric-label">Pontos de Esforço Total</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["media_percentual_concluido"]:.1f}%</div>
                    <div class="metric-label">Taxa Média de Conclusão</div>
                </div>
            </div>
            
            <!-- SEÇÃO: Análise de Chamados -->
            <h3>Análise de Chamados</h3>
            <div class="card">
                <div class="stats-container">
                    <div class="stat">Total de Chamados: {insights_consolidados.get("total_chamados", 0)}</div>
                    <div class="stat">Chamados Concluídos: {insights_consolidados.get("chamados_concluidos", 0)}</div>
                    <div class="stat">Percentual: {(insights_consolidados.get("chamados_concluidos", 0) / insights_consolidados.get("total_chamados", 1) * 100) if insights_consolidados.get("total_chamados", 0) > 0 else 0:.1f}%</div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {(insights_consolidados.get("chamados_concluidos", 0) / insights_consolidados.get("total_chamados", 1) * 100) if insights_consolidados.get("total_chamados", 0) > 0 else 0}%"></div>
                </div>
                <p>Ao longo das {insights_consolidados["total_sprints"]} sprints analisadas, foram registrados <strong>{insights_consolidados.get("total_chamados", 0)}</strong> chamados,
                dos quais <strong>{insights_consolidados.get("chamados_concluidos", 0)}</strong> foram concluídos.</p>
            </div>
            
            <h3>Resumo Consolidado</h3>
            <p>
                Este relatório analisa um total de {insights_consolidados["total_sprints"]} sprints, contendo {insights_consolidados["total_itens"]} itens de trabalho
                com um esforço total de {insights_consolidados["total_esforco"]} pontos.
            </p>
            <p>
                Em média, cada sprint contém {insights_consolidados["media_itens_sprint"]:.1f} itens de trabalho com {insights_consolidados["media_esforco_sprint"]:.1f} pontos de esforço.
                A taxa média de conclusão foi de {insights_consolidados["media_percentual_concluido"]:.1f}%.
            </p>
            <p>
                Ao longo dessas sprints, ocorreram em média {insights_consolidados["media_retornos_por_sprint"]:.1f} retornos por sprint,
                o que sugere um determinado nível de retrabalho no processo de desenvolvimento.
            </p>
            
            <h3>Tendências ao Longo das Sprints</h3>
            
            <h4>Tendência de Conclusão</h4>
            <div class="image-container">
                {graficos_tendencia_html.get('tendencia_conclusao', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h4>Tendência de Esforço</h4>
            <div class="image-container">
                {graficos_tendencia_html.get('tendencia_esforco', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Comparação Entre Sprints</h3>
            <table>
                <tr>
                    <th>Sprint</th>
                    <th>Itens</th>
                    <th>Esforço</th>
                    <th>Taxa de Conclusão</th>
                    <th>Chamados</th>
                    <th>Retornos</th>
                </tr>
                {self._gerar_linhas_tabela_sprints(nomes_sprints, insights_consolidados)}
            </table>
            
            <h3>Recomendações</h3>
            <ul>
                <li>Analisar tendências de conclusão para identificar melhorias ou regressões no processo ao longo do tempo</li>
                <li>Comparar o esforço estimado entre sprints para verificar consistência no planejamento</li>
                <li>Investigar sprints com taxas de conclusão significativamente abaixo da média ({insights_consolidados["media_percentual_concluido"]:.1f}%)</li>
                <li>Avaliar sprint com maior número de retornos para identificar causas de retrabalho</li>
                <li>Revisar a capacidade da equipe baseada na tendência de esforço total por sprint</li>
            </ul>
            
            <!-- NOVA SEÇÃO: Detalhes por Sprint -->
            <h3>Detalhes por Sprint</h3>
            <p>Clique em cada sprint para ver detalhes. Para visualizar gráficos detalhados, acesse o relatório individual de cada sprint.</p>
            
            {sprint_sections_html}
            
            <p><em>Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} pelo time de Payments 💙 | Sistema Boletinho Analytics</em></p>
            
            <script>
                // Script para os elementos colapsáveis
                var coll = document.getElementsByClassName("collapsible");
                for (var i = 0; i < coll.length; i++) {{
                    coll[i].addEventListener("click", function() {{
                        this.classList.toggle("active");
                        var content = this.nextElementSibling;
                        if (content.style.maxHeight) {{
                            content.style.maxHeight = null;
                        }} else {{
                            content.style.maxHeight = content.scrollHeight + "px";
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """

        return html

    def _gerar_graficos_tendencia_plotly(self, insights_consolidados):
        """
        Gera gráficos de tendência Plotly ao longo das sprints.

        Parameters
        ----------
        insights_consolidados : dict
            Dados consolidados das sprints

        Returns
        -------
        dict
            Dicionário com objetos Plotly
        """
        graficos = {}

        # Gráfico combinado de tendência de conclusão e esforço
        if (
            insights_consolidados["tendencia_conclusao"]
            and insights_consolidados["tendencia_esforco"]
        ):
            sprints_conclusao = [
                item["sprint"] for item in insights_consolidados["tendencia_conclusao"]
            ]
            percentuais = [
                item["percentual"]
                for item in insights_consolidados["tendencia_conclusao"]
            ]

            sprints_esforco = [
                item["sprint"] for item in insights_consolidados["tendencia_esforco"]
            ]
            esforcos = [
                item["esforco"] for item in insights_consolidados["tendencia_esforco"]
            ]

            # Verificar se as listas de sprints são iguais
            if sprints_conclusao == sprints_esforco:
                sprints = sprints_conclusao

                # Criar figura com dois eixos Y
                fig = go.Figure()

                # Adicionar taxa de conclusão (eixo Y primário)
                fig.add_trace(
                    go.Scatter(
                        x=sprints,
                        y=percentuais,
                        mode="lines+markers",
                        name="Taxa de Conclusão (%)",
                        marker=dict(color="#0078d4", size=10),
                        line=dict(color="#0078d4", width=2),
                    )
                )

                # Adicionar esforço total (eixo Y secundário)
                fig.add_trace(
                    go.Scatter(
                        x=sprints,
                        y=esforcos,
                        mode="lines+markers",
                        name="Esforço Total (pontos)",
                        marker=dict(color="#27ae60", size=10),
                        line=dict(color="#27ae60", width=2),
                        yaxis="y2",
                    )
                )

                # Configurar layout com dois eixos Y
                fig.update_layout(
                    title="Tendência de Conclusão e Esforço por Sprint",
                    xaxis=dict(
                        title=dict(text="Sprint", font=dict(color="#333333")),
                        tickfont=dict(color="#333333"),
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Taxa de Conclusão (%)", font=dict(color="#0078d4")
                        ),
                        tickfont=dict(color="#0078d4"),
                        side="left",
                    ),
                    yaxis2=dict(
                        title=dict(
                            text="Pontos de Esforço", font=dict(color="#27ae60")
                        ),
                        tickfont=dict(color="#27ae60"),
                        overlaying="y",
                        side="right",
                    ),
                    height=500,
                    template="plotly_white",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                    ),
                    margin=dict(l=60, r=60, t=80, b=60),
                )

                graficos["tendencia_combinada"] = fig
            else:
                # Se as listas de sprints não forem iguais, criar gráficos separados
                logger.warning(
                    "As listas de sprints para conclusão e esforço são diferentes. Criando gráficos separados."
                )

                # Gráfico de tendência de conclusão
                fig_conclusao = go.Figure()
                fig_conclusao.add_trace(
                    go.Scatter(
                        x=sprints_conclusao,
                        y=percentuais,
                        mode="lines+markers",
                        name="Taxa de Conclusão",
                        marker=dict(color="#0078d4", size=10),
                        line=dict(color="#0078d4", width=2),
                    )
                )
                fig_conclusao.update_layout(
                    title="Tendência de Conclusão por Sprint",
                    xaxis_title="Sprint",
                    yaxis_title="Percentual de Conclusão (%)",
                    height=500,
                    template="plotly_white",
                )
                graficos["tendencia_conclusao"] = fig_conclusao

                # Gráfico de tendência de esforço
                fig_esforco = go.Figure()
                fig_esforco.add_trace(
                    go.Scatter(
                        x=sprints_esforco,
                        y=esforcos,
                        mode="lines+markers",
                        name="Esforço Total",
                        marker=dict(color="#27ae60", size=10),
                        line=dict(color="#27ae60", width=2),
                    )
                )
                fig_esforco.update_layout(
                    title="Tendência de Esforço por Sprint",
                    xaxis_title="Sprint",
                    yaxis_title="Pontos de Esforço",
                    height=500,
                    template="plotly_white",
                )
                graficos["tendencia_esforco"] = fig_esforco

        return graficos

    def _gerar_html_consolidado_com_plotly(
        self,
        nomes_sprints,
        insights_consolidados,
        graficos_tendencia,
        graficos_por_sprint,
    ):
        """
        Gera HTML consolidado com gráficos Plotly embutidos.

        Parameters
        ----------
        nomes_sprints : list
            Lista de nomes das sprints
        insights_consolidados : dict
            Insights consolidados
        graficos_tendencia : dict
            Gráficos de tendência Plotly
        graficos_por_sprint : dict
            Dicionário com gráficos Plotly por sprint

        Returns
        -------
        str
            HTML gerado
        """
        # Gera os gráficos como HTML
        # Só inclui o Plotly.js uma vez
        include_plotlyjs = "cdn"

        # Converte os gráficos de tendência
        graficos_tendencia_html = {}
        for nome, fig in graficos_tendencia.items():
            graficos_tendencia_html[nome] = fig.to_html(
                include_plotlyjs=include_plotlyjs,
                full_html=False,
                config={"responsive": True},
            )
            include_plotlyjs = False

        # Converte os gráficos por sprint
        graficos_sprint_html = {}
        for sprint, graficos in graficos_por_sprint.items():
            graficos_sprint_html[sprint] = {}
            for nome, fig in graficos.items():
                try:
                    graficos_sprint_html[sprint][nome] = fig.to_html(
                        include_plotlyjs=False,  # Já incluído acima
                        full_html=False,
                        config={"responsive": True},
                    )
                except Exception as e:
                    logger.error(
                        f"Erro ao converter gráfico {nome} da sprint {sprint}: {str(e)}"
                    )
                    graficos_sprint_html[sprint][
                        nome
                    ] = f"<div>Erro ao gerar gráfico: {nome}</div>"

        # Cria HTML para o dropdown das sprints e seus gráficos
        sprint_sections_html = ""
        for sprint in nomes_sprints:
            graphs = graficos_sprint_html.get(sprint, {})

            sprint_section = f"""
            <button class="collapsible">{sprint}</button>
            <div class="content">
                <div class="sprint-section">
                    <div class="sprint-title">{sprint}</div>
                    
                    <h4>Itens de Trabalho por Tipo</h4>
                    <div class="image-container">
                        {graphs.get('itens_por_tipo', '<div>Gráfico não disponível</div>')}
                    </div>
                    
                    <h4>Distribuição de Estado Atual</h4>
                    <div class="image-container">
                        {graphs.get('itens_por_estado', '<div>Gráfico não disponível</div>')}
                    </div>
                    
                    <div class="sprint-grid">
                        <div>
                            <h4>Carga de Trabalho por Responsável</h4>
                            <div class="image-container">
                                {graphs.get('itens_por_responsavel', '<div>Gráfico não disponível</div>')}
                            </div>
                        </div>
                        <div>
                            <h4>Esforço por Responsável</h4>
                            <div class="image-container">
                                {graphs.get('esforco_por_responsavel', '<div>Gráfico não disponível</div>')}
                            </div>
                        </div>
                    </div>
                    
                    <h4>Tempo Médio em Coluna</h4>
                    <div class="image-container">
                        {graphs.get('tempo_medio_coluna', '<div>Gráfico não disponível</div>')}
                    </div>
                    
                    <div class="sprint-grid">
                        <div>
                            <h4>Adições no Meio da Sprint</h4>
                            <div class="image-container">
                                {graphs.get('adicoes_meio_sprint', '<div>Gráfico não disponível</div>')}
                            </div>
                        </div>
                        <div>
                            <h4>Retornos</h4>
                            <div class="image-container">
                                {graphs.get('retornos', '<div>Gráfico não disponível</div>')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
            sprint_sections_html += sprint_section

        # Gera o HTML completo
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório Consolidado de Sprints</title>
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
                
                h1, h2, h3, h4 {{
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
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
                
                .sprint-section {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 25px 0;
                }}
                
                .sprint-title {{
                    background-color: #0078d4;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 5px;
                    display: inline-block;
                    margin-bottom: 15px;
                }}
                
                .sprint-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                }}
                
                .collapsible {{
                    background-color: #f1f1f1;
                    color: #444;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    font-size: 16px;
                    border-radius: 5px;
                    margin-bottom: 5px;
                }}
                
                .active, .collapsible:hover {{
                    background-color: #ddd;
                }}
                
                .content {{
                    padding: 0 18px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                    background-color: #f9f9f9;
                    border-radius: 0 0 5px 5px;
                }}
                
                @media print {{
                    .card, .sprint-section {{
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
            <h1>Relatório Consolidado de Sprints</h1>
            <h2>Sprints: {', '.join(nomes_sprints)}</h2>
            
            <div class="dashboard">
                <div class="card">
                    <div class="metric">{insights_consolidados["total_sprints"]}</div>
                    <div class="metric-label">Total de Sprints Analisadas</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["total_itens"]}</div>
                    <div class="metric-label">Total de Itens de Trabalho</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["total_esforco"]}</div>
                    <div class="metric-label">Pontos de Esforço Total</div>
                </div>
                <div class="card">
                    <div class="metric">{insights_consolidados["media_percentual_concluido"]:.1f}%</div>
                    <div class="metric-label">Taxa Média de Conclusão</div>
                </div>
            </div>
            
            <!-- SEÇÃO: Análise de Chamados -->
            <h3>Análise de Chamados</h3>
            <div class="card">
                <div class="stats-container">
                    <div class="stat">Total de Chamados: {insights_consolidados.get("total_chamados", 0)}</div>
                    <div class="stat">Chamados Concluídos: {insights_consolidados.get("chamados_concluidos", 0)}</div>
                    <div class="stat">Percentual: {(insights_consolidados.get("chamados_concluidos", 0) / insights_consolidados.get("total_chamados", 1) * 100) if insights_consolidados.get("total_chamados", 0) > 0 else 0:.1f}%</div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {(insights_consolidados.get("chamados_concluidos", 0) / insights_consolidados.get("total_chamados", 1) * 100) if insights_consolidados.get("total_chamados", 0) > 0 else 0}%"></div>
                </div>
                <p>Ao longo das {insights_consolidados["total_sprints"]} sprints analisadas, foram registrados <strong>{insights_consolidados.get("total_chamados", 0)}</strong> chamados,
                dos quais <strong>{insights_consolidados.get("chamados_concluidos", 0)}</strong> foram concluídos.</p>
            </div>
            
            <h3>Resumo Consolidado</h3>
            <p>
                Este relatório analisa um total de {insights_consolidados["total_sprints"]} sprints, contendo {insights_consolidados["total_itens"]} itens de trabalho
                com um esforço total de {insights_consolidados["total_esforco"]} pontos.
            </p>
            <p>
                Em média, cada sprint contém {insights_consolidados["media_itens_sprint"]:.1f} itens de trabalho com {insights_consolidados["media_esforco_sprint"]:.1f} pontos de esforço.
                A taxa média de conclusão foi de {insights_consolidados["media_percentual_concluido"]:.1f}%.
            </p>
            <p>
                Ao longo dessas sprints, ocorreram em média {insights_consolidados["media_retornos_por_sprint"]:.1f} retornos por sprint,
                o que sugere um determinado nível de retrabalho no processo de desenvolvimento.
            </p>
            
            <h3>Tendências ao Longo das Sprints</h3>
            
            <h4>Tendência de Conclusão</h4>
            <div class="image-container">
                {graficos_tendencia_html.get('tendencia_conclusao', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h4>Tendência de Esforço</h4>
            <div class="image-container">
                {graficos_tendencia_html.get('tendencia_esforco', '<div>Gráfico não disponível</div>')}
            </div>
            
            <h3>Comparação Entre Sprints</h3>
            <table>
                <tr>
                    <th>Sprint</th>
                    <th>Itens</th>
                    <th>Esforço</th>
                    <th>Taxa de Conclusão</th>
                    <th>Chamados</th>
                    <th>Retornos</th>
                </tr>
                {self._gerar_linhas_tabela_sprints(nomes_sprints, insights_consolidados)}
            </table>
            
            <h3>Recomendações</h3>
            <ul>
                <li>Analisar tendências de conclusão para identificar melhorias ou regressões no processo ao longo do tempo</li>
                <li>Comparar o esforço estimado entre sprints para verificar consistência no planejamento</li>
                <li>Investigar sprints com taxas de conclusão significativamente abaixo da média ({insights_consolidados["media_percentual_concluido"]:.1f}%)</li>
                <li>Avaliar sprint com maior número de retornos para identificar causas de retrabalho</li>
                <li>Revisar a capacidade da equipe baseada na tendência de esforço total por sprint</li>
            </ul>
            
            <!-- NOVA SEÇÃO: Detalhes por Sprint -->
            <h3>Detalhes por Sprint</h3>
            <p>Clique em cada sprint para ver seus gráficos detalhados.</p>
            
            {sprint_sections_html}
            
            <p><em>Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} pelo time de Payments 💙 | Sistema Boletinho Analytics</em></p>
            
            <script>
                // Script para os elementos colapsáveis
                var coll = document.getElementsByClassName("collapsible");
                for (var i = 0; i < coll.length; i++) {{
                    coll[i].addEventListener("click", function() {{
                        this.classList.toggle("active");
                        var content = this.nextElementSibling;
                        if (content.style.maxHeight) {{
                            content.style.maxHeight = null;
                        }} else {{
                            content.style.maxHeight = content.scrollHeight + "px";
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """

        return html

    def _gerar_linhas_tabela_sprints(self, nomes_sprints, insights_consolidados):
        """
        Gera as linhas da tabela comparativa entre sprints.

        Parameters
        ----------
        nomes_sprints : list
            Lista de nomes das sprints
        insights_consolidados : dict
            Insights consolidados

        Returns
        -------
        str
            HTML com as linhas da tabela
        """
        linhas_html = ""

        for sprint in nomes_sprints:
            if sprint in insights_consolidados["por_sprint"]:
                dados_sprint = insights_consolidados["por_sprint"][sprint]

                linha = f"""
                <tr>
                    <td>{sprint}</td>
                    <td>{dados_sprint["total_itens"]}</td>
                    <td>{dados_sprint["esforco_total"]}</td>
                    <td>{dados_sprint["percentual_concluido"]:.1f}%</td>
                    <td>{dados_sprint.get("total_chamados", 0)}</td>
                    <td>{dados_sprint["retornos"]}</td>
                </tr>
                """
                linhas_html += linha

        return linhas_html

    # Métodos para gerar gráficos Plotly individuais
    def gerar_graficos_plotly(self, dados_processados, nome_sprint):
        """
        Gera gráficos interativos com Plotly para dados da sprint.

        Parameters
        ----------
        dados_processados : list
            Lista de itens processados
        nome_sprint : str
            Nome da sprint

        Returns
        -------
        dict
            Dicionário com objetos de figura do Plotly
        """
        graficos = {}

        # Gráfico de itens por tipo
        graficos["itens_por_tipo"] = self._gerar_grafico_plotly_itens_por_tipo(
            dados_processados, nome_sprint
        )

        # Gráfico de itens por estado
        graficos["itens_por_estado"] = self._gerar_grafico_plotly_itens_por_estado(
            dados_processados, nome_sprint
        )

        # Gráficos de carga de trabalho
        graficos["itens_por_responsavel"] = (
            self._gerar_grafico_plotly_itens_por_responsavel(
                dados_processados, nome_sprint
            )
        )

        graficos["esforco_por_responsavel"] = (
            self._gerar_grafico_plotly_esforco_por_responsavel(
                dados_processados, nome_sprint
            )
        )

        # Tempo médio em coluna
        graficos["tempo_medio_coluna"] = self._gerar_grafico_plotly_tempo_medio_coluna(
            dados_processados, nome_sprint
        )

        # Adições no meio da sprint
        graficos["adicoes_meio_sprint"] = self._gerar_grafico_plotly_adicoes_sprint(
            dados_processados, nome_sprint
        )

        # Retornos
        if any(item["retornos"] for item in dados_processados):
            graficos["retornos"] = self._gerar_grafico_plotly_retornos(
                dados_processados, nome_sprint
            )

        return graficos

    def _gerar_grafico_plotly_itens_por_tipo(self, dados_processados, nome_sprint):
        """Gera gráfico Plotly de itens por tipo."""
        try:
            # Calcula contagens
            contagens_tipo = {}
            for item in dados_processados:
                tipo_item = item["tipo"]
                if tipo_item not in contagens_tipo:
                    contagens_tipo[tipo_item] = 0
                contagens_tipo[tipo_item] += 1

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Tipo": list(contagens_tipo.keys()),
                    "Quantidade": list(contagens_tipo.values()),
                }
            )

            # Ordena por quantidade
            df = df.sort_values("Quantidade", ascending=False)

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Tipo",
                y="Quantidade",
                color="Tipo",
                title=f"Itens de Trabalho por Tipo - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Tipo de Item",
                yaxis_title="Quantidade",
                height=400,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de itens por tipo: {str(e)}")
            return go.Figure()

    def _gerar_grafico_plotly_itens_por_estado(self, dados_processados, nome_sprint):
        """Gera gráfico Plotly de itens por estado atual."""
        try:
            # Calcula contagens
            contagens_estado = {}
            for item in dados_processados:
                estado = item["estado"]
                if estado not in contagens_estado:
                    contagens_estado[estado] = 0
                contagens_estado[estado] += 1

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Estado": list(contagens_estado.keys()),
                    "Quantidade": list(contagens_estado.values()),
                }
            )

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Estado",
                y="Quantidade",
                color="Estado",
                title=f"Itens de Trabalho por Estado Atual - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Estado",
                yaxis_title="Quantidade",
                height=400,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de itens por estado: {str(e)}")
            return go.Figure()

    def _gerar_grafico_plotly_itens_por_responsavel(
        self, dados_processados, nome_sprint
    ):
        """Gera gráfico Plotly de itens por responsável."""
        try:
            # Calcula contagens
            contagens_responsavel = {}
            for item in dados_processados:
                responsavel = item["responsavel_atual"]
                if responsavel not in contagens_responsavel:
                    contagens_responsavel[responsavel] = 0
                contagens_responsavel[responsavel] += 1

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Responsável": list(contagens_responsavel.keys()),
                    "Quantidade": list(contagens_responsavel.values()),
                }
            )

            # Ordena por quantidade
            df = df.sort_values("Quantidade", ascending=False)

            # Limita para os top 10 responsáveis se houver muitos
            if len(df) > 10:
                outros_total = df.iloc[10:]["Quantidade"].sum()
                df = df.iloc[:10].copy()
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {"Responsável": ["Outros"], "Quantidade": [outros_total]}
                        ),
                    ]
                )

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Responsável",
                y="Quantidade",
                color="Responsável",
                title=f"Itens de Trabalho por Responsável - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Responsável",
                yaxis_title="Quantidade de Itens",
                height=400,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de itens por responsável: {str(e)}")
            return go.Figure()

    def _gerar_grafico_plotly_esforco_por_responsavel(
        self, dados_processados, nome_sprint
    ):
        """Gera gráfico Plotly de esforço por responsável."""
        try:
            # Calcula esforço
            esforco_responsavel = {}
            for item in dados_processados:
                responsavel = item["responsavel_atual"]
                if responsavel not in esforco_responsavel:
                    esforco_responsavel[responsavel] = 0
                esforco_responsavel[responsavel] += item["esforco"] or 0

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Responsável": list(esforco_responsavel.keys()),
                    "Esforço": list(esforco_responsavel.values()),
                }
            )

            # Ordena por esforço
            df = df.sort_values("Esforço", ascending=False)

            # Limita para os top 10 responsáveis se houver muitos
            if len(df) > 10:
                outros_total = df.iloc[10:]["Esforço"].sum()
                df = df.iloc[:10].copy()
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {"Responsável": ["Outros"], "Esforço": [outros_total]}
                        ),
                    ]
                )

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Responsável",
                y="Esforço",
                color="Responsável",
                title=f"Esforço por Responsável - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Responsável",
                yaxis_title="Pontos de Esforço",
                height=400,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de esforço por responsável: {str(e)}")
            return go.Figure()

    def _gerar_grafico_plotly_tempo_medio_coluna(self, dados_processados, nome_sprint):
        """Gera gráfico Plotly de tempo médio em cada coluna."""
        try:
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
                    tempos_medios_coluna[coluna] = sum(tempos_coluna) / len(
                        tempos_coluna
                    )
                else:
                    tempos_medios_coluna[coluna] = 0

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Coluna": list(tempos_medios_coluna.keys()),
                    "Horas": list(tempos_medios_coluna.values()),
                }
            )

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Coluna",
                y="Horas",
                color="Coluna",
                title=f"Tempo Médio em Coluna (Horas) - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Coluna",
                yaxis_title="Horas",
                height=400,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de tempo médio em coluna: {str(e)}")
            return go.Figure()

    def _gerar_grafico_plotly_adicoes_sprint(self, dados_processados, nome_sprint):
        """Gera gráfico Plotly de adições no meio da sprint."""
        try:
            # Calcula contagens
            contagem_meio_sprint = sum(
                1
                for item in dados_processados
                if item.get("adicionado_meio_sprint", False)
            )
            contagem_inicial = len(dados_processados) - contagem_meio_sprint

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Tipo": ["Itens Iniciais", "Adicionados no Meio da Sprint"],
                    "Quantidade": [contagem_inicial, contagem_meio_sprint],
                }
            )

            # Cria o gráfico
            fig = px.pie(
                df,
                values="Quantidade",
                names="Tipo",
                title=f"Itens Iniciais vs. Adições no Meio da Sprint - {nome_sprint}",
                color="Tipo",
                color_discrete_map={
                    "Itens Iniciais": "#0078d4",
                    "Adicionados no Meio da Sprint": "#ff8c00",
                },
            )

            # Personaliza o layout para melhorar a posição da legenda
            fig.update_layout(
                height=400,
                template="plotly_white",
                # Mover a legenda para dentro do gráfico
                legend=dict(
                    orientation="v",  # Legenda horizontal
                    yanchor="bottom",  # Ancorada na parte inferior
                    y=-0.2,  # Posicionada abaixo do gráfico
                    xanchor="center",  # Centralizada
                    x=0.5,  # No meio horizontalmente
                    font=dict(size=10),  # Texto menor para evitar corte
                ),
                margin=dict(
                    t=50, b=80, l=20, r=20
                ),  # Maior margem inferior para acomodar a legenda
            )

            # Ajustar o layout do gráfico em si
            fig.update_traces(
                textposition="inside",  # Texto dentro das fatias
                textinfo="percent+label",  # Mostra percentual e rótulo
                insidetextorientation="radial",  # Orientação do texto
            )

            return fig
        except Exception as e:
            logger.error(
                f"Erro ao gerar gráfico de adições no meio da sprint: {str(e)}"
            )
            return go.Figure()

    def _gerar_grafico_plotly_retornos(self, dados_processados, nome_sprint):
        """Gera gráfico Plotly de retornos entre estados."""
        try:
            # Calcula contagens de retornos por transição
            contagens_retorno = {}
            for item in dados_processados:
                for retorno in item.get("retornos", []):
                    transicao = f"{retorno['de']} -> {retorno['para']}"
                    if transicao not in contagens_retorno:
                        contagens_retorno[transicao] = 0
                    contagens_retorno[transicao] += 1

            # Se não há retornos, retornar uma figura vazia
            if not contagens_retorno:
                return go.Figure()

            # Prepara dados para Plotly
            df = pd.DataFrame(
                {
                    "Transição": list(contagens_retorno.keys()),
                    "Quantidade": list(contagens_retorno.values()),
                }
            )

            # Ordena por quantidade
            df = df.sort_values("Quantidade", ascending=False)

            # Cria o gráfico
            fig = px.bar(
                df,
                x="Transição",
                y="Quantidade",
                color="Transição",
                title=f"Retornos por Transição - {nome_sprint}",
            )

            # Personaliza o layout
            fig.update_layout(
                xaxis_title="Transição",
                yaxis_title="Quantidade",
                height=500,
                showlegend=False,
                template="plotly_white",
            )

            return fig
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de retornos: {str(e)}")
            return go.Figure()

    def gerar_cards_metricas(self, insights):
        """
        Gera HTML para os cards de métricas para uso no Streamlit.

        Parameters
        ----------
        insights : dict
            Dicionário com insights da sprint

        Returns
        -------
        str
            HTML dos cards formatados
        """
        # Formatar valores para exibição
        percentual_concluido = round(insights["percentual_concluido"], 1)

        cards_html = f"""
        <style>
            .card-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .card {{
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                flex: 1;
                min-width: 200px;
            }}
            .metric {{
                font-size: 28px;
                font-weight: bold;
                color: #0078d4;
                margin-bottom: 8px;
            }}
            .metric-label {{
                font-size: 14px;
                color: #666;
            }}
            .progress-container {{
                width: 100%;
                height: 8px;
                background-color: #f1f1f1;
                border-radius: 4px;
                margin-top: 10px;
                overflow: hidden;
            }}
            .progress-bar {{
                height: 100%;
                background-color: #4CAF50;
                border-radius: 4px;
            }}
        </style>
        <div class="card-container">
            <div class="card">
                <div class="metric">{insights["total_itens"]}</div>
                <div class="metric-label">Total de Itens de Trabalho</div>
            </div>
            <div class="card">
                <div class="metric">{insights["esforco_total"]}</div>
                <div class="metric-label">Pontos de Esforço Total</div>
            </div>
            <div class="card">
                <div class="metric">{percentual_concluido}%</div>
                <div class="metric-label">Taxa de Conclusão</div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {percentual_concluido}%;"></div>
                </div>
            </div>
            <div class="card">
                <div class="metric">{insights["adicoes_meio_sprint"]}</div>
                <div class="metric-label">Itens Adicionados no Meio da Sprint</div>
            </div>
        </div>
        """

        # Adiciona card de análise de chamados se disponível
        if "total_chamados" in insights and insights["total_chamados"] > 0:
            percentual_chamados = round(
                insights.get("percentual_chamados_concluidos", 0), 1
            )
            chamados_html = f"""
            <div class="card-container">
                <div class="card" style="width: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-weight: bold; font-size: 16px;">Análise de Chamados</div>
                        <div style="display: flex; gap: 20px;">
                            <span>Total: {insights.get("total_chamados", 0)}</span>
                            <span>Concluídos: {insights.get("chamados_concluidos", 0)}</span>
                            <span>Taxa: {percentual_chamados}%</span>
                        </div>
                    </div>
                    <div class="progress-container" style="margin-top: 15px;">
                        <div class="progress-bar" style="width: {percentual_chamados}%;"></div>
                    </div>
                </div>
            </div>
            """
            cards_html += chamados_html

        return cards_html
