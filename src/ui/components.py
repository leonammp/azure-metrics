import streamlit as st
import base64
import os


def init_session_state():
    """Inicializa o estado da sessão para a aplicação."""
    if "distribuicao_analisada" not in st.session_state:
        st.session_state.distribuicao_analisada = False
        st.session_state.distribuicao_por_esforco = None
        st.session_state.distribuicao_por_quantidade = None
        st.session_state.df_items = None
        st.session_state.sprint_analisada = None
        st.session_state.recomendacoes = None


def render_sidebar():
    """
    Renderiza a sidebar com configurações e informações.

    Returns
    -------
    dict
        Dicionário com credenciais fornecidas
    """
    with st.sidebar:
        st.header("Configurações")
        st.write(
            "Insira as credenciais do Azure DevOps para acessar os dados da sprint."
        )

        org = st.text_input(
            "Organização", key="org", help="Nome da sua organização no Azure DevOps"
        )

        project = st.text_input(
            "Projeto", key="project", help="Nome do projeto no Azure DevOps"
        )

        team = st.text_input("Equipe", key="team", help="Nome da equipe (opcional)")

        pat = st.text_input(
            "Personal Access Token (PAT)",
            type="password",
            key="pat",
            help="Token de acesso pessoal do Azure DevOps. Estas credenciais não são armazenadas permanentemente.",
        )

        st.markdown("---")
        st.markdown("### Sobre")
        st.info(
            """
            Esta ferramenta analisa dados de sprints do Azure DevOps.
            
            Desenvolvida para facilitar o acesso a métricas importantes.
            
            💙 BU Payments | v1.0
            """
        )

        return {"org": org, "project": project, "team": team, "pat": pat}


def get_download_link(file_path, link_text):
    """
    Cria um link HTML para download de arquivo.

    Parameters
    ----------
    file_path : str
        Caminho para o arquivo
    link_text : str
        Texto a ser exibido no link

    Returns
    -------
    str
        HTML do link de download
    """
    with open(file_path, "rb") as f:
        data = f.read()

    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{os.path.basename(file_path)}" target="_blank">{link_text}</a>'

    return href


def gerar_card_categoria(titulo, valor_esforco, valor_quantidade, meta):
    """
    Gera HTML para um card de categoria com métricas.

    Parameters
    ----------
    titulo : str
        Título do card
    valor_esforco : float
        Percentual por esforço
    valor_quantidade : float
        Percentual por quantidade
    meta : float
        Meta percentual para a categoria

    Returns
    -------
    str
        HTML do card formatado
    """

    def get_status_color(atual, meta, tolerancia=5):
        if abs(atual - meta) <= tolerancia:
            return "#27ae60"  # Verde
        elif abs(atual - meta) <= tolerancia * 2:
            return "#f39c12"  # Amarelo
        else:
            return "#e74c3c"  # Vermelho

    # Calcular diferenças
    diferenca_esforco = valor_esforco - meta
    diferenca_quantidade = valor_quantidade - meta

    # Determinar cores
    color_esforco = get_status_color(valor_esforco, meta)
    color_quantidade = get_status_color(valor_quantidade, meta)

    return f"""
    <div style="padding: 20px; border-radius: 10px; background-color: #f8f9fa; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="color: #0078d4; margin: 0; font-size: 24px;">{titulo}</h3>
            <div style="background-color: #0078d4; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold;">
                Meta: {meta}%
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 15px;">
            <!-- Coluna de Esforço -->
            <div style="flex: 1; padding: 15px; background-color: #f2f2f2; border-radius: 8px; margin-right: 10px;">
                <div style="font-size: 16px; font-weight: bold; color: #444; margin-bottom: 8px;">POR ESFORÇO</div>
                <div style="font-size: 32px; font-weight: bold; color: {color_esforco};">{valor_esforco:.1f}%</div>
                <div style="font-size: 14px; color: {color_esforco}; margin-top: 8px; display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 4px;">{'+' if diferenca_esforco > 0 else ''}
                    {diferenca_esforco:.1f}%</span>
                    <span>da meta</span>
                </div>
            </div>
            <!-- Coluna de Quantidade -->
            <div style="flex: 1; padding: 15px; background-color: #f2f2f2; border-radius: 8px;">
                <div style="font-size: 16px; font-weight: bold; color: #444; margin-bottom: 8px;">POR QUANTIDADE</div>
                <div style="font-size: 32px; font-weight: bold; color: {color_quantidade};">{valor_quantidade:.1f}%</div>
                <div style="font-size: 14px; color: {color_quantidade}; margin-top: 8px; display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 4px;">{'+' if diferenca_quantidade > 0 else ''}
                    {diferenca_quantidade:.1f}%</span>
                    <span>da meta</span>
                </div>
            </div>
        </div>
    </div>
    """


def render_category_cards(distribuicao_esforco, distribuicao_qtd, metas):
    """
    Renderiza cards de categoria em colunas.

    Parameters
    ----------
    distribuicao_esforco : dict
        Distribuição percentual por esforço
    distribuicao_qtd : dict
        Distribuição percentual por quantidade
    metas : dict
        Metas por categoria
    """
    col1, col2, col3 = st.columns(3)

    categorias = [("Negócio", col1), ("Técnico", col2), ("Incidentes", col3)]

    for categoria, coluna in categorias:
        with coluna:
            esforco = distribuicao_esforco.get(categoria, 0)
            quantidade = distribuicao_qtd.get(categoria, 0)
            meta = metas.get(categoria, 0)

            st.markdown(
                gerar_card_categoria(categoria, esforco, quantidade, meta),
                unsafe_allow_html=True,
            )
