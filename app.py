import streamlit as st
import os

from src.data.azure_client import AzureDevOpsClient
from src.analysis.sprint_analyzer import SprintAnalyzer
from src.analysis.report_generator import ReportGenerator
from src.ui.components import init_session_state, render_sidebar
from src.ui.pages import render_sprint_analysis_page, render_distribution_analysis_page

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
    st.markdown("### ")

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

            # Opções de análise
            st.markdown("## Escolha o tipo de análise")
            analysis_type = st.radio(
                "Selecione o tipo de análise:",
                ["Análise de Sprint Concluída", "Meta de Distribuição de Tasks"],
                horizontal=True,
            )

            # Seleção de sprint comum para ambos os tipos
            col1, col2, col3 = st.columns([1, 1, 3])

            with col1:
                selected_sprint = st.selectbox("Selecione a Sprint:", sprint_names)

            # Renderiza a interface baseada no tipo de análise
            if analysis_type == "Análise de Sprint Concluída":
                render_sprint_analysis_page(
                    selected_sprint, analyzer, report_generator, col2
                )
            else:
                render_distribution_analysis_page(selected_sprint, analyzer, col2, col3)

        except Exception as e:
            st.error(f"Erro ao conectar ou processar dados: {str(e)}")
            st.write("⚠️ Verifique suas credenciais e tente novamente.")
            logger.error(f"Erro: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
