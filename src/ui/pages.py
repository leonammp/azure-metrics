import streamlit as st
import tempfile
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd

from src.ui.components import get_download_link, render_category_cards


def render_sprint_analysis_page(
    selected_sprint, analyzer, report_generator, column_buttons
):
    """
    Renderiza a página de análise de sprint concluída.

    Parameters
    ----------
    selected_sprint : str
        Nome da sprint selecionada
    analyzer : SprintAnalyzer
        Analisador de sprint
    report_generator : ReportGenerator
        Gerador de relatórios
    column_buttons : st.column
        Coluna para posicionar botões
    """
    with column_buttons:
        # Espaço vertical para alinhar com o select
        st.markdown('<div style="padding-top: 27px;"></div>', unsafe_allow_html=True)
        # Botão para gerar relatório
        generate_button = st.button(
            "Gerar Relatório", type="primary", use_container_width=False
        )

    # Se o botão foi clicado
    if generate_button:
        with st.spinner(
            f"Analisando '{selected_sprint}'. Isso pode levar alguns minutos..."
        ):
            # Usar um diretório temporário para evitar conflitos
            with tempfile.TemporaryDirectory() as temp_dir:
                # Configurar a pasta de saída
                temp_path = Path(temp_dir)
                analyzer.pasta_base_saida = temp_path

                # Analisar a sprint e gerar o relatório
                insights, pasta_saida = analyzer.analisar_sprint(selected_sprint)
                relatorio_path = report_generator.gerar_relatorio_executivo(
                    selected_sprint, pasta_saida
                )

                # Ler o relatório HTML
                with open(relatorio_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Exibir sucesso
                st.success(
                    f"🎉 Relatório para Sprint '{selected_sprint}' gerado com sucesso!"
                )

                # Opções para visualizar e baixar
                tab1, tab2, tab3 = st.tabs(
                    ["Visualizar Relatório", "Baixar Relatório", "Dados Brutos"]
                )

                with tab1:
                    # Exibir o HTML
                    st.components.v1.html(html_content, height=800, scrolling=True)

                with tab2:
                    # Link para download do relatório
                    st.markdown(
                        get_download_link(relatorio_path, "📥 Baixar Relatório HTML"),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        "Você pode baixar o relatório e compartilhá-lo com sua equipe."
                    )

                with tab3:
                    # Mostrar os dados em formato tabular
                    detalhes_csv = pasta_saida / "detalhes_completos.csv"
                    if detalhes_csv.exists():
                        df = pd.read_csv(detalhes_csv)
                        st.dataframe(df, use_container_width=True)
                        st.markdown(
                            get_download_link(detalhes_csv, "📥 Baixar CSV Completo"),
                            unsafe_allow_html=True,
                        )

                        # Estatísticas sobre chamados
                        if "Tags" in df.columns:
                            chamados = df[
                                df["Tags"].str.contains("chamado", case=False, na=False)
                            ]
                            st.metric("Total de Chamados", len(chamados))
                    else:
                        st.warning("Arquivo de detalhes não encontrado.")


def render_distribution_analysis_page(
    selected_sprint, analyzer, column_input, column_button
):
    """
    Renderiza a página de análise de distribuição de tasks.

    Parameters
    ----------
    selected_sprint : str
        Nome da sprint selecionada
    analyzer : SprintAnalyzer
        Analisador de sprint
    column_input : st.column
        Coluna para inputs
    column_button : st.column
        Coluna para botões
    """
    # Constantes para metas padrão
    DEFAULT_AVG_POINTS = 80

    # Campo para média de pontos
    with column_input:
        avg_points = st.number_input(
            "Média entregue",
            min_value=1,
            value=DEFAULT_AVG_POINTS,
            step=5,
            help="Informe a média histórica de pontos que sua equipe consegue entregar em uma sprint",
            key="avg_points",
        )

    with column_button:
        # Espaço vertical para alinhar com o select
        st.markdown('<div style="padding-top: 27px;"></div>', unsafe_allow_html=True)
        # Botão para analisar distribuição
        distribution_button = st.button(
            "Analisar Distribuição", type="primary", use_container_width=False
        )

    # Função para analisar distribuição
    def analisar_distribuicao(nome_sprint, avg_points):
        distribuicao_por_esforco, distribuicao_por_quantidade, df_items = (
            analyzer.analisar_distribuicao_tasks(nome_sprint)
        )
        recomendacoes = analyzer.gerar_recomendacoes_distribuicao(
            distribuicao_por_esforco, distribuicao_por_quantidade, df_items, avg_points
        )

        # Salvar resultados no session_state
        st.session_state.distribuicao_analisada = True
        st.session_state.distribuicao_por_esforco = distribuicao_por_esforco
        st.session_state.distribuicao_por_quantidade = distribuicao_por_quantidade
        st.session_state.df_items = df_items
        st.session_state.sprint_analisada = nome_sprint
        st.session_state.recomendacoes = recomendacoes

    # Se o botão foi clicado
    if distribution_button:
        with st.spinner(
            f"Analisando distribuição de tasks para '{selected_sprint}'..."
        ):
            analisar_distribuicao(selected_sprint, avg_points)

    # Exibe resultados se já analisados
    if st.session_state.distribuicao_analisada:
        # Se a sprint selecionada é diferente da analisada, reanalisamos
        if selected_sprint != st.session_state.sprint_analisada:
            with st.spinner(f"Atualizando distribuição para '{selected_sprint}'..."):
                analisar_distribuicao(selected_sprint, avg_points)

        # Agora exibimos os resultados
        st.success(
            f"✅ Análise de distribuição para Sprint '{st.session_state.sprint_analisada}' concluída!"
        )

        st.markdown("## Distribuição Atual vs. Meta")

        # Obtém dados do session state
        metas = st.session_state.recomendacoes["metas"]
        distribuicao_por_esforco = st.session_state.distribuicao_por_esforco
        distribuicao_por_quantidade = st.session_state.distribuicao_por_quantidade

        # Renderiza cards de categoria
        render_category_cards(
            distribuicao_por_esforco, distribuicao_por_quantidade, metas
        )

        # Gráfico de comparação
        render_distribution_chart(
            distribuicao_por_esforco, distribuicao_por_quantidade, metas
        )

        # Tabela de itens
        render_items_table(st.session_state.df_items, metas)

        # Análise e sugestões
        render_recommendations(st.session_state.recomendacoes)


def render_distribution_chart(distribuicao_esforco, distribuicao_quantidade, metas):
    """Renderiza gráfico de comparação da distribuição."""
    st.markdown("### Comparação Visual")

    # Dados para o gráfico
    categories = list(metas.keys())
    esforco_values = [distribuicao_esforco.get(cat, 0) for cat in categories]
    quantidade_values = [distribuicao_quantidade.get(cat, 0) for cat in categories]
    target_values = list(metas.values())

    # Cria o gráfico
    fig = go.Figure()

    # Barras de distribuição por esforço
    fig.add_trace(
        go.Bar(
            x=categories,
            y=esforco_values,
            name="Distribuição por Esforço",
            marker_color="#0078d4",
        )
    )

    # Barras de distribuição por quantidade
    fig.add_trace(
        go.Bar(
            x=categories,
            y=quantidade_values,
            name="Distribuição por Quantidade",
            marker_color="#9c59b6",
        )
    )

    # Barras de meta
    fig.add_trace(
        go.Bar(
            x=categories,
            y=target_values,
            name="Meta",
            marker_color="#27ae60",
        )
    )

    # Layout do gráfico
    fig.update_layout(
        title="Distribuição Atual vs. Meta",
        xaxis_title="Categoria",
        yaxis_title="Percentual (%)",
        barmode="group",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_items_table(df_items, metas):
    """Renderiza tabela de itens com filtro por categoria."""
    st.markdown("### Itens por Categoria")

    # Cria filtro por categoria
    categorias = ["Todos"] + list(metas.keys())
    categoria_selecionada = st.selectbox("Filtrar por categoria:", categorias)

    # Filtra os dados
    if categoria_selecionada == "Todos":
        filtered_df = df_items
    else:
        filtered_df = df_items[df_items["Categoria"] == categoria_selecionada]

    # Exibe a tabela
    st.dataframe(filtered_df, use_container_width=True)


def render_recommendations(recomendacoes):
    """Renderiza análise e recomendações."""
    st.markdown("## Análise e Sugestões")

    # Exibe análise de pontos totais
    st.write(f"**Pontos totais na sprint atual:** {recomendacoes['pontos_atuais']:.1f}")
    st.write(f"**Média histórica de pontos:** {recomendacoes['avg_points']:.1f}")

    # Alerta de capacidade
    if recomendacoes["diferenca_pontos"] > 10:
        st.warning(
            f"⚠️ A sprint atual tem {recomendacoes['diferenca_pontos']:.1f} pontos a mais que a média histórica, "
            "o que pode levar a sobrecarga da equipe."
        )
    elif recomendacoes["diferenca_pontos"] < -10:
        st.warning(
            f"⚠️ A sprint atual tem {abs(recomendacoes['diferenca_pontos']):.1f} pontos a menos que a média histórica, "
            "o que pode indicar subutilização da capacidade da equipe."
        )
    else:
        st.success(
            "✅ A carga total de pontos está próxima da média histórica da equipe."
        )

    # Sugestões de remanejamento
    st.markdown("### Sugestões de Remanejamento")

    # Radio para escolher entre visão por esforço ou por quantidade
    visao_analise = st.radio(
        "Visualizar recomendações baseadas em:",
        ["Esforço (pontos)", "Quantidade de tasks"],
        horizontal=True,
    )

    # Escolhe as diferenças baseadas na visão selecionada
    if visao_analise == "Esforço (pontos)":
        diferencas = recomendacoes["diferencas_pontos"]
        valor_atual = recomendacoes["pontos_atuais"]
        valor_ideal = recomendacoes["avg_points"]
        unidade = "pontos"
    else:
        diferencas = recomendacoes["diferencas_qtd"]
        valor_atual = recomendacoes["quantidade_total"]
        valor_ideal = recomendacoes[
            "quantidade_total"
        ]  # O ideal é o próprio total aqui
        unidade = "tasks"

    # Formatar as sugestões baseadas nas diferenças
    for cat, diff in diferencas.items():
        if diff > 1:  # Mais unidades do que o ideal
            st.info(
                f"📉 **{cat}**: Reduzir em aproximadamente {abs(diff):.1f} {unidade} para atingir a meta de {recomendacoes['metas'][cat]}%."
            )
        elif diff < -1:  # Menos unidades do que o ideal
            st.info(
                f"📈 **{cat}**: Adicionar aproximadamente {abs(diff):.1f} {unidade} para atingir a meta de {recomendacoes['metas'][cat]}%."
            )
        else:
            st.success(
                f"✅ **{cat}**: Distribuição adequada, próxima da meta de {recomendacoes['metas'][cat]}%."
            )

    # Sugestões específicas
    st.markdown("### Recomendações Específicas")

    cat_mais_deficit = recomendacoes["cat_mais_deficit"]
    cat_mais_excesso = recomendacoes["cat_mais_excesso"]

    if visao_analise == "Esforço (pontos)":
        if cat_mais_deficit[1] < -5 and cat_mais_excesso[1] > 5:
            st.write(
                f"**Recomendação principal:** Considere mover alguns itens da categoria '{cat_mais_excesso[0]}' para "
                f"'{cat_mais_deficit[0]}' para equilibrar a distribuição."
            )

            # Itens candidatos para movimentação
            if (
                recomendacoes["itens_candidatos"] is not None
                and not recomendacoes["itens_candidatos"].empty
            ):
                st.write("**Itens candidatos para remanejamento:**")
                st.dataframe(
                    recomendacoes["itens_candidatos"][
                        ["ID", "Título", "Esforço", "Categoria"]
                    ],
                    use_container_width=True,
                )

    # Conclusão
    st.markdown("### Conclusão")
    st.write(
        """
        Este é um guia para ajudar no planejamento da sprint. As sugestões são baseadas nas metas
        estabelecidas (70% Negócio, 20% Técnico, 10% Incidentes) e na média histórica de pontos
        entregues pela equipe. Lembre-se que cada sprint tem suas particularidades e que esses
        valores são apenas diretrizes.
        """
    )
