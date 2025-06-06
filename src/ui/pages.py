import streamlit as st
import tempfile
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import json
import base64
from io import BytesIO

from src.ui.components import get_download_link, render_category_cards


def render_sprint_analysis_page(
    selected_sprints,
    analyzer,
    report_generator,
    column_buttons=None,
    dados_processados=None,
    mostrar_dados=True,
):
    """
    Renderiza a página de análise de sprint concluída.

    Parameters
    ----------
    selected_sprints : list
        Lista de sprints selecionadas
    analyzer : SprintAnalyzer
        Analisador de sprint
    report_generator : ReportGenerator
        Gerador de relatórios
    column_buttons : st.column, optional
        Coluna para posicionar botões (não usado no novo fluxo unificado)
    dados_processados : dict, optional
        Dados já processados da sessão (usado no novo fluxo unificado)
    mostrar_dados : bool, optional
        Se True, exibe a planilha de dados. Se False, omite a planilha.
    """
    # Se estamos usando o fluxo unificado com dados já processados
    if dados_processados is not None:
        # Usar diretamente os dados processados
        insights = dados_processados["insights"]
        pasta_saida = dados_processados["pasta_saida"]
        selected_sprints = dados_processados["selected_sprints"]
        is_consolidado = dados_processados["is_consolidado"]

        # Exibir título da seção
        if is_consolidado:
            st.markdown(f"## Relatório Consolidado: {len(selected_sprints)} Sprints")
        else:
            st.markdown(f"## Relatório da Sprint: {selected_sprints[0]}")

        # Continuar com a exibição do relatório
        exibir_relatorio_com_dados_processados(
            selected_sprints, insights, pasta_saida, report_generator, mostrar_dados
        )
        return

    # Fluxo antigo (mantido para compatibilidade)
    # Inicializa o estado da sessão para armazenar os relatórios analisados
    if "relatorios_analisados" not in st.session_state:
        st.session_state.relatorios_analisados = {}

    if column_buttons:
        with column_buttons:
            # Espaço vertical para alinhar com o select
            st.markdown(
                '<div style="padding-top: 27px;"></div>', unsafe_allow_html=True
            )
            # Botão para gerar relatório
            generate_button = st.button(
                f"Gerar Relatório {'Consolidado' if len(selected_sprints) > 1 else ''}",
                type="primary",
                use_container_width=False,
                disabled=len(selected_sprints) == 0,
            )

    if len(selected_sprints) == 0:
        st.info("Selecione pelo menos uma sprint para análise.")
        return

    # Chave única para identificar este conjunto de sprints
    if len(selected_sprints) == 1:
        relatorio_key = selected_sprints[0]
    else:
        relatorio_key = "consolidado_" + "_".join(sorted(selected_sprints))

    # Verifica se já temos este relatório em cache
    if relatorio_key in st.session_state.relatorios_analisados and not generate_button:
        # Usa os dados já analisados
        dados_relatorio = st.session_state.relatorios_analisados[relatorio_key]

        # Exibe o relatório a partir dos dados em cache
        exibir_relatorio(
            dados_relatorio["sprints"],
            dados_relatorio["insights"],
            dados_relatorio["graficos_plotly"],
            dados_relatorio["html_content"],
            dados_relatorio["pasta_saida"],
            dados_relatorio["detalhes_csv"],
            mostrar_dados,
        )
        return

    # Se o botão foi clicado ou não temos o relatório em cache
    if generate_button or relatorio_key not in st.session_state.relatorios_analisados:
        with st.spinner(
            f"Analisando {len(selected_sprints)} sprint(s). Isso pode levar alguns minutos..."
        ):
            # Usar um diretório temporário para evitar conflitos
            with tempfile.TemporaryDirectory() as temp_dir:
                # Configurar a pasta de saída
                temp_path = Path(temp_dir)
                analyzer.pasta_base_saida = temp_path

                if len(selected_sprints) == 1:
                    # Processamento de sprint única
                    insights, pasta_saida = analyzer.analisar_sprint(
                        selected_sprints[0]
                    )

                    # Carregar dados processados para gráficos interativos
                    dados_processados_path = pasta_saida / "dados_processados.json"
                    if dados_processados_path.exists():
                        with open(dados_processados_path, "r") as f:
                            dados_processados = json.load(f)
                        # Gera gráficos interativos
                        graficos_plotly = report_generator.gerar_graficos_plotly(
                            dados_processados, selected_sprints[0]
                        )
                    else:
                        graficos_plotly = None

                    # Gerar relatório HTML para download
                    relatorio_path = report_generator.gerar_relatorio_executivo(
                        selected_sprints[0], pasta_saida
                    )

                    # Ler o relatório HTML
                    with open(relatorio_path, "r", encoding="utf-8") as f:
                        html_content = f.read()

                    # Para verificar existência do CSV
                    detalhes_csv = pasta_saida / "detalhes_completos.csv"

                    # Ler dados do CSV para armazenar na sessão
                    if detalhes_csv.exists():
                        df_csv = pd.read_csv(detalhes_csv)
                        csv_content = df_csv.to_dict()
                    else:
                        csv_content = None

                else:
                    # Processamento de múltiplas sprints
                    insights_consolidados, pasta_saida = (
                        analyzer.analisar_multiplas_sprints(selected_sprints)
                    )
                    relatorio_path = report_generator.gerar_relatorio_consolidado(
                        selected_sprints, pasta_saida
                    )

                    # Ler o relatório HTML
                    with open(relatorio_path, "r", encoding="utf-8") as f:
                        html_content = f.read()

                    # Para verificar existência do CSV
                    detalhes_csv = pasta_saida / "detalhes_consolidados.csv"

                    # Ler dados do CSV para armazenar na sessão
                    if detalhes_csv.exists():
                        df_csv = pd.read_csv(detalhes_csv)
                        csv_content = df_csv.to_dict()
                    else:
                        csv_content = None

                    insights = insights_consolidados
                    graficos_plotly = None  # Não implementamos gráficos interativos para múltiplas sprints

                # Salvar na sessão
                st.session_state.relatorios_analisados[relatorio_key] = {
                    "sprints": selected_sprints,
                    "insights": insights,
                    "graficos_plotly": graficos_plotly,
                    "html_content": html_content,
                    "pasta_saida": str(pasta_saida),
                    "detalhes_csv": (
                        str(detalhes_csv) if detalhes_csv.exists() else None
                    ),
                    "csv_content": csv_content,
                }

                # Exibir o relatório
                exibir_relatorio(
                    selected_sprints,
                    insights,
                    graficos_plotly,
                    html_content,
                    pasta_saida,
                    detalhes_csv,
                    mostrar_dados,
                )


def exibir_relatorio_com_dados_processados(
    selected_sprints, insights, pasta_saida, report_generator, mostrar_dados=True
):
    """
    Exibe o relatório usando dados já processados da sessão.

    Parameters
    ----------
    selected_sprints : list
        Lista de sprints selecionadas
    insights : dict
        Insights da análise
    pasta_saida : str
        Caminho para a pasta com resultados
    report_generator : ReportGenerator
        Gerador de relatórios
    mostrar_dados : bool, optional
        Se True, exibe a planilha de dados. Se False, omite a planilha.
    """
    pasta_saida = Path(pasta_saida)
    is_consolidado = len(selected_sprints) > 1

    # Exibir cards de métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Itens na Sprint", insights["total_itens"])

    with col2:
        st.metric("Pontos de Esforço Planejados", insights["esforco_total"])

    with col3:
        st.metric(
            "Taxa de Conclusão (Tasks)", f"{insights['percentual_concluido']:.1f}%"
        )

    with col4:
        if "percentual_esforco_concluido" in insights:
            st.metric(
                "Taxa de Conclusão (Esforço)",
                f"{insights['percentual_esforco_concluido']:.1f}%",
            )
        else:
            st.metric("Itens Adicionados", insights.get("adicoes_meio_sprint", 0))

    # Chamados (se houver)
    if "total_chamados" in insights and insights["total_chamados"] > 0:
        st.markdown("### Análise de Chamados")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Chamados", insights.get("total_chamados", 0))

        with col2:
            st.metric("Chamados Concluídos", insights.get("chamados_concluidos", 0))

        with col3:
            st.metric(
                "Taxa de Conclusão",
                f"{insights.get('percentual_chamados_concluidos', 0):.1f}%",
            )

    # Resumo da Sprint
    st.markdown("### Resumo")

    if is_consolidado:
        # Resumo para relatório consolidado
        st.markdown(
            f"""
            Este relatório analisa um total de {len(selected_sprints)} sprints, contendo {insights["total_itens"]} itens de trabalho
            com um esforço total de {insights["esforco_total"]} pontos.
            
            Em média, cada sprint contém {insights.get("media_itens_sprint", 0):.1f} itens de trabalho com {insights.get("media_esforco_sprint", 0):.1f} pontos de esforço.
            A taxa média de conclusão foi de {insights.get("media_percentual_concluido", 0):.1f}%.
            """
        )

        # Gráfico de tendência combinado
        st.markdown("### Tendências ao Longo das Sprints")

        # Gerar gráfico de tendência combinado
        graficos_tendencia = report_generator._gerar_graficos_tendencia_plotly(insights)

        if "tendencia_combinada" in graficos_tendencia:
            st.plotly_chart(
                graficos_tendencia["tendencia_combinada"],
                use_container_width=True,
            )
    else:
        # Resumo para sprint única
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                Esta sprint contém **{insights['total_itens']}** itens de trabalho com um 
                esforço total de **{insights['esforco_total']}** pontos. 
                
                **{insights['percentual_concluido']:.1f}%** dos itens foram concluídos 
                até o final da sprint.
                """
            )

        with col2:
            percentual_adicoes = (
                (insights["adicoes_meio_sprint"] / insights["total_itens"] * 100)
                if insights["total_itens"] > 0
                else 0
            )
            st.markdown(
                f"""
                **{insights['adicoes_meio_sprint']}** itens foram adicionados após o início 
                da sprint, representando **{percentual_adicoes:.1f}%** 
                do trabalho total.
                
                Houve **{insights['retornos_unicos']}** itens que experimentaram 
                retornos, com um total de **{insights['retornos']}** transições de retorno.
                """
            )

        # Carregar dados processados para gráficos interativos
        dados_processados_path = pasta_saida / "dados_processados.json"
        if dados_processados_path.exists():
            with open(dados_processados_path, "r") as f:
                dados_processados = json.load(f)
            # Gera gráficos interativos
            graficos_plotly = report_generator.gerar_graficos_plotly(
                dados_processados, selected_sprints[0]
            )

            if graficos_plotly:
                st.markdown("### Análise Detalhada")

                # Itens por tipo
                st.subheader("Itens de Trabalho por Tipo")
                st.plotly_chart(
                    graficos_plotly["itens_por_tipo"],
                    use_container_width=True,
                )

                # Estado atual
                st.subheader("Distribuição de Estado Atual")
                st.plotly_chart(
                    graficos_plotly["itens_por_estado"],
                    use_container_width=True,
                )

                # Carga de trabalho
                st.subheader("Carga de Trabalho da Equipe")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Por Quantidade de Itens")
                    st.plotly_chart(
                        graficos_plotly["itens_por_responsavel"],
                        use_container_width=True,
                    )

                with col2:
                    st.markdown("#### Por Pontos de Esforço")
                    st.plotly_chart(
                        graficos_plotly["esforco_por_responsavel"],
                        use_container_width=True,
                    )

                # Tempo médio em coluna
                st.subheader("Eficiência do Processo")
                st.plotly_chart(
                    graficos_plotly["tempo_medio_coluna"],
                    use_container_width=True,
                )

                # Adições no meio da sprint e Retornos
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Adições no Meio da Sprint")
                    st.plotly_chart(
                        graficos_plotly["adicoes_meio_sprint"],
                        use_container_width=True,
                    )

                # Retornos (se existirem)
                if "retornos" in graficos_plotly:
                    with col2:
                        st.markdown("#### Retornos")
                        st.plotly_chart(
                            graficos_plotly["retornos"],
                            use_container_width=True,
                        )


def exibir_relatorio(
    selected_sprints,
    insights,
    graficos_plotly,
    html_content,
    pasta_saida,
    detalhes_csv,
    mostrar_dados=True,
):
    """
    Exibe o relatório gerado no Streamlit.

    Parameters
    ----------
    selected_sprints : list
        Lista de sprints selecionadas
    insights : dict
        Insights da análise
    graficos_plotly : dict
        Dicionário com objetos de figura do Plotly
    html_content : str
        Conteúdo HTML do relatório
    pasta_saida : Path
        Caminho para a pasta com resultados
    detalhes_csv : Path
        Caminho para o CSV com detalhes
    mostrar_dados : bool, optional
        Se True, exibe a planilha de dados. Se False, omite a planilha.
    """
    from src.ui.components import gerar_card_categoria

    # Exibir sucesso
    sprint_texto = (
        f"Sprint '{selected_sprints[0]}'"
        if len(selected_sprints) == 1
        else f"{len(selected_sprints)} Sprints"
    )
    st.success(f"🎉 Relatório para {sprint_texto} gerado com sucesso!")

    # Aba de dashboard para todos os tipos de relatório
    # Conteúdo específico para relatório consolidado
    if len(selected_sprints) > 1:
        st.markdown(f"## Dashboard Consolidado: {len(selected_sprints)} Sprints")

        # Exibir o HTML para relatório consolidado
        st.components.v1.html(html_content, height=800, scrolling=True)

        # Botão para download do HTML
        sprint_name_safe = "consolidado"
        file_name = f"relatorio_{sprint_name_safe}.html"
        st.download_button(
            label="📥 Baixar Relatório HTML",
            data=html_content,
            file_name=file_name,
            mime="text/html",
        )

    # Aba de dashboard interativo (apenas para sprint única)
    elif len(selected_sprints) == 1:
        # Exibir título
        st.markdown(f"## Dashboard da Sprint: {selected_sprints[0]}")

        try:
            # Exibir cards de métricas usando componentes nativos do Streamlit
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Itens", insights["total_itens"])

            with col2:
                st.metric("Pontos de Esforço", insights["esforco_total"])

            with col3:
                st.metric(
                    "Taxa de Conclusão (Tasks)",
                    f"{insights['percentual_concluido']:.1f}%",
                )

            with col4:
                if "percentual_esforco_concluido" in insights:
                    st.metric(
                        "Taxa de Conclusão (Esforço)",
                        f"{insights['percentual_esforco_concluido']:.1f}%",
                    )
                else:
                    st.metric("Itens Adicionados", insights["adicoes_meio_sprint"])

            # Chamados (se houver)
            if "total_chamados" in insights and insights["total_chamados"] > 0:
                st.markdown("### Análise de Chamados")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total de Chamados", insights.get("total_chamados", 0))

                with col2:
                    st.metric(
                        "Chamados Concluídos",
                        insights.get("chamados_concluidos", 0),
                    )

                with col3:
                    st.metric(
                        "Taxa de Conclusão",
                        f"{insights.get('percentual_chamados_concluidos', 0):.1f}%",
                    )

            # Resumo da Sprint
            st.markdown("### Resumo da Sprint")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"""
                Esta sprint contém **{insights['total_itens']}** itens de trabalho com um 
                esforço total de **{insights['esforco_total']}** pontos. 
                
                **{insights['percentual_concluido']:.1f}%** dos itens foram concluídos 
                até o final da sprint.
                """
                )

            with col2:
                percentual_adicoes = (
                    (insights["adicoes_meio_sprint"] / insights["total_itens"] * 100)
                    if insights["total_itens"] > 0
                    else 0
                )
                st.markdown(
                    f"""
                **{insights['adicoes_meio_sprint']}** itens foram adicionados após o início 
                da sprint, representando **{percentual_adicoes:.1f}%** 
                do trabalho total.
                
                Houve **{insights['retornos_unicos']}** itens que experimentaram 
                retornos, com um total de **{insights['retornos']}** transições de retorno.
                """
                )

            # Download do relatório HTML
            file_name = f"relatorio_{selected_sprints[0].replace(' ', '_')}.html"

            st.download_button(
                label="📥 Baixar Relatório HTML",
                data=html_content,
                file_name=file_name,
                mime="text/html",
                help="Baixe o relatório HTML para compartilhar com sua equipe",
            )

            # Gráficos interativos
            if graficos_plotly:
                st.markdown("### Análise Detalhada")

                # Itens por tipo
                st.subheader("Itens de Trabalho por Tipo")
                st.plotly_chart(
                    graficos_plotly["itens_por_tipo"],
                    use_container_width=True,
                )

                # Estado atual
                st.subheader("Distribuição de Estado Atual")
                st.plotly_chart(
                    graficos_plotly["itens_por_estado"],
                    use_container_width=True,
                )

                # Carga de trabalho
                st.subheader("Carga de Trabalho da Equipe")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Por Quantidade de Itens")
                    st.plotly_chart(
                        graficos_plotly["itens_por_responsavel"],
                        use_container_width=True,
                    )

                with col2:
                    st.markdown("#### Por Pontos de Esforço")
                    st.plotly_chart(
                        graficos_plotly["esforco_por_responsavel"],
                        use_container_width=True,
                    )

                # Tempo médio em coluna
                st.subheader("Eficiência do Processo")
                st.plotly_chart(
                    graficos_plotly["tempo_medio_coluna"],
                    use_container_width=True,
                )

                # Adições no meio da sprint e Retornos
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Adições no Meio da Sprint")
                    st.plotly_chart(
                        graficos_plotly["adicoes_meio_sprint"],
                        use_container_width=True,
                    )

                # Retornos (se existirem)
                if "retornos" in graficos_plotly:
                    with col2:
                        st.markdown("#### Retornos")
                        st.plotly_chart(
                            graficos_plotly["retornos"],
                            use_container_width=True,
                        )

        except Exception as e:
            st.error(f"Erro ao gerar dashboard: {str(e)}")


def render_distribution_analysis_page(
    selected_sprints,
    analyzer,
    column_input=None,
    column_button=None,
    dados_processados=None,
    mostrar_dados=True,
):
    """
    Renderiza a página de análise de distribuição de tasks.

    Parameters
    ----------
    selected_sprints : list ou str
        Lista de sprints selecionadas ou nome de uma única sprint
    analyzer : SprintAnalyzer
        Analisador de sprint
    column_input : st.column, optional
        Coluna para posicionar inputs (não usado no novo fluxo unificado)
    column_button : st.column, optional
        Coluna para posicionar botões (não usado no novo fluxo unificado)
    dados_processados : dict, optional
        Dados já processados da sessão (usado no novo fluxo unificado)
    mostrar_dados : bool, optional
        Se True, exibe a planilha de dados. Se False, omite a planilha.
    """
    # Se estamos usando o fluxo unificado com dados já processados
    if dados_processados is not None:
        # Usar diretamente os dados processados
        insights = dados_processados["insights"]
        pasta_saida = dados_processados["pasta_saida"]
        selected_sprints = dados_processados["selected_sprints"]
        is_consolidado = dados_processados["is_consolidado"]

        # Exibir título da seção
        if is_consolidado:
            st.markdown(f"## Distribuição de Tasks: {len(selected_sprints)} Sprints")
            current_sprint = (
                selected_sprints  # Usar todas as sprints para análise acumulada
            )
        else:
            st.markdown(f"## Distribuição de Tasks: {selected_sprints[0]}")
            current_sprint = selected_sprints[0]

        # Continuar com a análise de distribuição
        analisar_distribuicao_com_dados_processados(
            current_sprint, analyzer, insights, mostrar_dados
        )
        return

    # Fluxo antigo (mantido para compatibilidade)
    # Verifica se temos uma sprint selecionada
    if not selected_sprints:
        st.info("Selecione uma sprint para análise de distribuição de tasks.")
        return

    # Converte para string se for lista com um elemento
    if isinstance(selected_sprints, list) and len(selected_sprints) == 1:
        current_sprint = selected_sprints[0]
    else:
        current_sprint = selected_sprints

    # Inicializa o estado da sessão
    if "distribuicao_analisada" not in st.session_state:
        st.session_state.distribuicao_analisada = False
        st.session_state.distribuicao_por_esforco = None
        st.session_state.distribuicao_por_quantidade = None
        st.session_state.df_items = None
        st.session_state.sprint_analisada = None
        st.session_state.recomendacoes = None

    # Formulário para análise
    with column_input:
        st.markdown("### Configurações")
        st.markdown("Defina as metas de distribuição de tasks por categoria:")

        # Metas por categoria
        col1, col2, col3 = st.columns(3)

        with col1:
            meta_negocio = st.number_input(
                "Meta Negócio (%)",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                key="meta_negocio",
            )

        with col2:
            meta_tecnico = st.number_input(
                "Meta Técnico (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="meta_tecnico",
            )

        with col3:
            meta_incidentes = st.number_input(
                "Meta Incidentes (%)",
                min_value=0,
                max_value=100,
                value=10,
                step=5,
                key="meta_incidentes",
            )

        # Validação de soma = 100%
        total_metas = meta_negocio + meta_tecnico + meta_incidentes
        if total_metas != 100:
            st.warning(f"A soma das metas deve ser 100%. Atualmente: {total_metas}%")

    # Botão para analisar
    with column_button:
        # Espaço vertical para alinhar com o select
        st.markdown('<div style="padding-top: 27px;"></div>', unsafe_allow_html=True)
        analyze_button = st.button(
            "Analisar Distribuição",
            type="primary",
            use_container_width=False,
            disabled=current_sprint is None,
        )

    # Verifica se o botão foi clicado ou se já temos uma análise para esta sprint
    if analyze_button or (
        st.session_state.distribuicao_analisada
        and st.session_state.sprint_analisada == current_sprint
    ):
        # Se o botão foi clicado ou mudamos de sprint, refaz a análise
        if analyze_button or st.session_state.sprint_analisada != current_sprint:
            with st.spinner("Analisando distribuição de tasks..."):
                # Coleta as metas em um dicionário
                metas = {
                    "Negócio": meta_negocio,
                    "Técnico": meta_tecnico,
                    "Incidentes": meta_incidentes,
                }

                # Analisa a distribuição atual
                (
                    distribuicao_por_esforco,
                    distribuicao_por_quantidade,
                    df_items,
                ) = analyzer.analisar_distribuicao_tasks(current_sprint)

                # Removida a geração de recomendações para simplificar a interface

                # Atualiza o estado da sessão
                st.session_state.distribuicao_analisada = True
                st.session_state.distribuicao_por_esforco = distribuicao_por_esforco
                st.session_state.distribuicao_por_quantidade = (
                    distribuicao_por_quantidade
                )
                st.session_state.df_items = df_items
                st.session_state.sprint_analisada = current_sprint

        # Exibe os resultados da análise
        st.markdown(f"## Análise de Distribuição: {current_sprint}")

        # Exibe cards de categoria
        render_category_cards(
            st.session_state.distribuicao_por_esforco,
            st.session_state.distribuicao_por_quantidade,
            {
                "Negócio": meta_negocio,
                "Técnico": meta_tecnico,
                "Incidentes": meta_incidentes,
            },
        )

        # Exibe todos os itens da sprint
        if mostrar_dados and st.session_state.df_items is not None:
            st.markdown("### Todos os Itens da Sprint")
            st.dataframe(st.session_state.df_items, use_container_width=True)


def analisar_distribuicao_com_dados_processados(
    selected_sprints, analyzer, insights, mostrar_dados=True
):
    """
    Analisa a distribuição de tasks usando dados já processados.

    Parameters
    ----------
    selected_sprints : list ou str
        Lista de sprints selecionadas ou nome de uma única sprint
    analyzer : SprintAnalyzer
        Analisador de sprint
    insights : dict
        Insights da análise
    mostrar_dados : bool, optional
        Se True, exibe a planilha de dados. Se False, omite a planilha.
    """
    # Configurações de metas
    st.markdown("### Configurações")
    st.markdown("Defina as metas de distribuição de tasks por categoria:")

    # Metas por categoria
    col1, col2, col3 = st.columns(3)

    with col1:
        meta_negocio = st.number_input(
            "Meta Negócio (%)",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="meta_negocio_unificado",
        )

    with col2:
        meta_tecnico = st.number_input(
            "Meta Técnico (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            key="meta_tecnico_unificado",
        )

    with col3:
        meta_incidentes = st.number_input(
            "Meta Incidentes (%)",
            min_value=0,
            max_value=100,
            value=10,
            step=5,
            key="meta_incidentes_unificado",
        )

    # Validação de soma = 100%
    total_metas = meta_negocio + meta_tecnico + meta_incidentes
    if total_metas != 100:
        st.warning(f"A soma das metas deve ser 100%. Atualmente: {total_metas}%")

    # Executa a análise automaticamente
    with st.spinner("Analisando distribuição de tasks..."):
        # Coleta as metas em um dicionário
        metas = {
            "Negócio": meta_negocio,
            "Técnico": meta_tecnico,
            "Incidentes": meta_incidentes,
        }

        # Analisa a distribuição atual
        if isinstance(selected_sprints, list) and len(selected_sprints) > 1:
            # Para múltiplas sprints, acumular dados
            distribuicao_por_esforco = {"Negócio": 0, "Técnico": 0, "Incidentes": 0}
            distribuicao_por_quantidade = {"Negócio": 0, "Técnico": 0, "Incidentes": 0}
            df_items_list = []

            for sprint in selected_sprints:
                # Analisa cada sprint individualmente
                dist_esforco, dist_qtd, df = analyzer.analisar_distribuicao_tasks(
                    sprint
                )

                # Acumula os dados brutos para análise consolidada
                df_items_list.append(df)

            # Concatena os DataFrames
            if df_items_list:
                df_items = pd.concat(df_items_list, ignore_index=True)

                # Recalcula distribuição consolidada
                total_esforco = df_items["Esforço"].sum()
                total_items = len(df_items)

                if total_esforco > 0:
                    for categoria in ["Negócio", "Técnico", "Incidentes"]:
                        esforco_categoria = df_items[
                            df_items["Categoria"] == categoria
                        ]["Esforço"].sum()
                        distribuicao_por_esforco[categoria] = (
                            esforco_categoria / total_esforco
                        ) * 100

                if total_items > 0:
                    for categoria in ["Negócio", "Técnico", "Incidentes"]:
                        qtd_categoria = len(
                            df_items[df_items["Categoria"] == categoria]
                        )
                        distribuicao_por_quantidade[categoria] = (
                            qtd_categoria / total_items
                        ) * 100
            else:
                st.error("Não foi possível obter dados das sprints selecionadas.")
                return
        else:
            # Para sprint única
            if isinstance(selected_sprints, list):
                sprint_name = selected_sprints[0]
            else:
                sprint_name = selected_sprints

            distribuicao_por_esforco, distribuicao_por_quantidade, df_items = (
                analyzer.analisar_distribuicao_tasks(sprint_name)
            )

        # Exibe os resultados da análise
        if isinstance(selected_sprints, list) and len(selected_sprints) > 1:
            st.markdown(
                f"## Análise de Distribuição Consolidada: {len(selected_sprints)} Sprints"
            )
        else:
            sprint_name = (
                selected_sprints[0]
                if isinstance(selected_sprints, list)
                else selected_sprints
            )
            st.markdown(f"## Análise de Distribuição: {sprint_name}")

        # Exibe cards de categoria
        render_category_cards(
            distribuicao_por_esforco,
            distribuicao_por_quantidade,
            metas,
        )

        # Exibe todos os itens da sprint (apenas se mostrar_dados for True)
        if mostrar_dados:
            st.markdown("### Todos os Itens da Sprint")
            st.dataframe(df_items, use_container_width=True)


def render_dados_brutos_page(selected_sprints, analyzer, dados_processados=None):
    """
    Renderiza a página de dados brutos.

    Parameters
    ----------
    selected_sprints : list
        Lista de sprints selecionadas
    analyzer : SprintAnalyzer
        Analisador de sprint
    dados_processados : dict, optional
        Dados já processados da sessão
    """
    if dados_processados is None:
        st.info("Não há dados processados disponíveis.")
        return

    # Usar diretamente os dados processados
    selected_sprints = dados_processados["selected_sprints"]
    is_consolidado = dados_processados["is_consolidado"]

    st.markdown("## Dados Brutos")

    # Obter dados unificados com categoria
    df_items = obter_dados_unificados(selected_sprints, analyzer, dados_processados)

    if df_items is not None and not df_items.empty:
        # Para relatório consolidado, adiciona filtro por sprint
        if is_consolidado and "Sprint" in df_items.columns:
            sprint_filter = st.selectbox(
                "Filtrar por Sprint:",
                ["Todas"] + sorted(df_items["Sprint"].unique().tolist()),
            )

            if sprint_filter != "Todas":
                df_items_filtrado = df_items[df_items["Sprint"] == sprint_filter]
            else:
                df_items_filtrado = df_items
        else:
            df_items_filtrado = df_items

        # Adicionar filtro por categoria
        if "Categoria" in df_items.columns:
            categoria_options = ["Todas"] + sorted(
                df_items["Categoria"].unique().tolist()
            )
            categoria_filter = st.selectbox(
                "Filtrar por Categoria:",
                categoria_options,
            )

            if categoria_filter != "Todas":
                df_items_filtrado = df_items_filtrado[
                    df_items_filtrado["Categoria"] == categoria_filter
                ]

        # Exibir dataframe unificado
        st.dataframe(df_items_filtrado, use_container_width=True)

        # Download do CSV
        if is_consolidado:
            file_name = "dados_consolidados.csv"
        else:
            file_name = f"dados_{selected_sprints[0].replace(' ', '_')}.csv"

        csv_data = df_items_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar CSV Completo",
            data=csv_data,
            file_name=file_name,
            mime="text/csv",
        )

        # Exibir resumo de distribuição por categoria
        st.markdown("### Resumo por Categoria")

        # Criar dataframe de resumo
        resumo = []

        # Por quantidade
        qtd_total = len(df_items)
        for categoria in ["Negócio", "Técnico", "Incidentes"]:
            qtd_categoria = len(df_items[df_items["Categoria"] == categoria])
            pct_qtd = (qtd_categoria / qtd_total * 100) if qtd_total > 0 else 0

            # Por esforço
            esforco_total = df_items["Esforço"].sum()
            esforco_categoria = df_items[df_items["Categoria"] == categoria][
                "Esforço"
            ].sum()
            pct_esforco = (
                (esforco_categoria / esforco_total * 100) if esforco_total > 0 else 0
            )

            resumo.append(
                {
                    "Categoria": categoria,
                    "Quantidade": qtd_categoria,
                    "% Quantidade": f"{pct_qtd:.1f}%",
                    "Esforço": esforco_categoria,
                    "% Esforço": f"{pct_esforco:.1f}%",
                }
            )

        # Adicionar total
        resumo.append(
            {
                "Categoria": "Total",
                "Quantidade": qtd_total,
                "% Quantidade": "100.0%",
                "Esforço": esforco_total,
                "% Esforço": "100.0%",
            }
        )

        # Exibir resumo
        st.dataframe(pd.DataFrame(resumo), use_container_width=True)
    else:
        st.warning("Não foi possível obter dados para exibição.")


def obter_dados_unificados(selected_sprints, analyzer, dados_processados=None):
    """
    Obtém dados unificados com coluna de categoria para todas as sprints selecionadas.

    Parameters
    ----------
    selected_sprints : list
        Lista de sprints selecionadas
    analyzer : SprintAnalyzer
        Analisador de sprint
    dados_processados : dict, optional
        Dados já processados da sessão

    Returns
    -------
    pandas.DataFrame
        DataFrame unificado com dados de todas as sprints selecionadas
    """
    # Verificar se já temos os dados na sessão para evitar busca duplicada
    if "df_items_unificado" in st.session_state:
        return st.session_state.df_items_unificado

    is_consolidado = isinstance(selected_sprints, list) and len(selected_sprints) > 1

    if is_consolidado:
        # Para múltiplas sprints, acumular dados
        df_items_list = []

        for sprint in selected_sprints:
            try:
                # Analisa cada sprint individualmente
                _, _, df = analyzer.analisar_distribuicao_tasks(sprint)

                # Adicionar coluna de sprint se não existir
                if "Sprint" not in df.columns:
                    df["Sprint"] = sprint

                df_items_list.append(df)
            except Exception as e:
                st.error(f"Erro ao analisar sprint {sprint}: {str(e)}")

        # Concatena os DataFrames
        if df_items_list:
            df_items = pd.concat(df_items_list, ignore_index=True)

            # Garantir que a coluna Categoria existe
            if "Categoria" not in df_items.columns:
                df_items["Categoria"] = "Não categorizado"

            # Armazenar na sessão para reutilização
            st.session_state.df_items_unificado = df_items
            return df_items
        else:
            return None
    else:
        # Para sprint única
        try:
            sprint_name = (
                selected_sprints[0]
                if isinstance(selected_sprints, list)
                else selected_sprints
            )
            _, _, df_items = analyzer.analisar_distribuicao_tasks(sprint_name)

            # Adicionar coluna de sprint se não existir
            if "Sprint" not in df_items.columns:
                df_items["Sprint"] = sprint_name

            # Garantir que a coluna Categoria existe
            if "Categoria" not in df_items.columns:
                df_items["Categoria"] = "Não categorizado"

            # Armazenar na sessão para reutilização
            st.session_state.df_items_unificado = df_items
            return df_items
        except Exception as e:
            st.error(f"Erro ao analisar sprint: {str(e)}")
            return None
