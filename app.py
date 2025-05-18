import streamlit as st
import os

from src.data.azure_client import AzureDevOpsClient
from src.analysis.sprint_analyzer import SprintAnalyzer
from src.analysis.report_generator import ReportGenerator
from src.ui.components import init_session_state, render_sidebar, sprint_selector
from src.ui.pages import (
    render_sprint_analysis_page,
    render_distribution_analysis_page,
    render_dados_brutos_page,
)

# Configuração do logger
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Função principal da aplicação de análise de Sprint do Azure DevOps"""
    # Configuração da página
    st.set_page_config(page_title="Análise de Sprint", page_icon="📊", layout="wide")

    # Inicialização do estado da aplicação
    init_session_state()

    # Interface do usuário
    st.title("📊 Análise de Sprint")

    # Renderizar sidebar e obter credenciais
    credenciais = render_sidebar()

    # Container principal
    with st.container():
        # Verificar credenciais
        if not all([credenciais["org"], credenciais["project"], credenciais["pat"]]):
            st.warning(
                "👈 Primeiro, insira as credenciais no menu lateral para continuar."
            )
            st.stop()

        try:
            # Configura variáveis de ambiente temporárias (apenas para esta sessão)
            os.environ["AZURE_DEVOPS_ORG"] = credenciais["org"]
            os.environ["AZURE_DEVOPS_PROJECT"] = credenciais["project"]
            if credenciais["team"]:
                os.environ["AZURE_DEVOPS_TEAM"] = credenciais["team"]
            os.environ["AZURE_DEVOPS_PAT"] = credenciais["pat"]

            # Inicializa o cliente e analisador
            client = AzureDevOpsClient(
                credenciais["org"],
                credenciais["project"],
                credenciais["team"],
                credenciais["pat"],
            )

            analyzer = SprintAnalyzer(client)
            report_generator = ReportGenerator(analyzer)

            # Obtém a lista de sprints
            with st.spinner("Conectando ao Azure DevOps..."):
                sprints = client.get_sprints()
                sprint_names = [sprint["name"] for sprint in sprints]

            # Seleção de sprints unificada
            selected_sprints = sprint_selector(sprint_names, key_prefix="analysis")

            # Inicializa a chave para armazenar dados processados na sessão
            if "dados_processados" not in st.session_state:
                st.session_state.dados_processados = {}

            # Chave única para identificar este conjunto de sprints
            if len(selected_sprints) > 0:
                sprints_key = "_".join(sorted(selected_sprints))

                # Botão para processar dados
                col1, col2 = st.columns([1, 3])

                with col1:
                    # Espaço vertical para alinhar com o select
                    st.markdown(
                        '<div style="padding-top: 27px;"></div>', unsafe_allow_html=True
                    )
                    process_button = st.button(
                        "Processar Dados",
                        type="primary",
                        use_container_width=False,
                        disabled=len(selected_sprints) == 0,
                    )

                # Processa os dados se o botão for clicado ou se já temos dados em cache
                if process_button or (
                    sprints_key in st.session_state.dados_processados
                ):
                    if process_button or not st.session_state.dados_processados.get(
                        sprints_key
                    ):
                        with st.spinner(
                            f"Processando dados de {len(selected_sprints)} sprint(s). Isso pode levar alguns minutos..."
                        ):
                            # Processa os dados das sprints selecionadas
                            if len(selected_sprints) == 1:
                                insights, pasta_saida = analyzer.analisar_sprint(
                                    selected_sprints[0]
                                )
                                is_consolidado = False
                            else:
                                insights, pasta_saida = (
                                    analyzer.analisar_multiplas_sprints(
                                        selected_sprints
                                    )
                                )
                                is_consolidado = True

                            # Armazena os dados processados na sessão
                            st.session_state.dados_processados[sprints_key] = {
                                "insights": insights,
                                "pasta_saida": str(pasta_saida),
                                "selected_sprints": selected_sprints,
                                "is_consolidado": is_consolidado,
                            }

                            # Limpar cache de dados unificados para forçar recálculo
                            if "df_items_unificado" in st.session_state:
                                del st.session_state.df_items_unificado

                    # Exibe as abas de análise
                    tabs = st.tabs(
                        ["Relatório de Sprint", "Distribuição de Tasks", "Dados Brutos"]
                    )
                    tab_relatorio, tab_distribuicao, tab_dados_brutos = tabs

                    # Dados da sessão
                    dados_sessao = st.session_state.dados_processados[sprints_key]

                    # Aba de relatório de sprint
                    with tab_relatorio:
                        render_sprint_analysis_page(
                            dados_sessao["selected_sprints"],
                            analyzer,
                            report_generator,
                            None,  # Não precisa de coluna de botões, já processamos os dados
                            dados_processados=dados_sessao,
                            mostrar_dados=False,  # Não mostrar planilha de dados nesta aba
                        )

                    # Aba de distribuição de tasks
                    with tab_distribuicao:
                        # Para análise de distribuição com múltiplas sprints
                        render_distribution_analysis_page(
                            dados_sessao["selected_sprints"],
                            analyzer,
                            None,  # Não precisa de coluna de input
                            None,  # Não precisa de coluna de botão
                            dados_processados=dados_sessao,
                            mostrar_dados=False,  # Não mostrar planilha de dados nesta aba
                        )

                    # Aba de dados brutos
                    with tab_dados_brutos:
                        render_dados_brutos_page(
                            dados_sessao["selected_sprints"],
                            analyzer,
                            dados_processados=dados_sessao,
                        )
                else:
                    st.info(
                        "Selecione pelo menos uma sprint e clique em 'Processar Dados' para iniciar a análise."
                    )

        except Exception as e:
            st.error(f"Erro ao conectar ou processar dados: {str(e)}")
            st.write("⚠️ Verifique suas credenciais e tente novamente.")
            logger.error(f"Erro: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
