# Analisador de Sprint Azure DevOps

Ferramenta para análise de dados de sprints no Azure DevOps, fornecendo métricas, visualizações e recomendações para equipes ágeis.

## Funcionalidades

- **Análise de Sprint Concluída**: Geração de relatório executivo com métricas, gráficos e insights
- **Análise de Distribuição de Tasks**: Avaliação da distribuição por categoria (Negócio, Técnico, Incidentes)
- **Identificação de Retornos**: Detecção de itens que retornaram no fluxo de trabalho
- **Análise de Chamados**: Métricas específicas para chamados e incidentes
- **Recomendações**: Sugestões para melhorar o planejamento e execução da sprint

## Estrutura do Projeto
```
projeto/
├── src/
│   ├── data/
│   │   └── azure_client.py     # Comunicação com API do Azure DevOps
│   ├── analysis/
│   │   ├── sprint_analyzer.py  # Análise de dados da sprint
│   │   └── report_generator.py # Geração de relatórios e visualizações
│   └── ui/
│       ├── components.py       # Componentes UI reutilizáveis
│       └── pages.py            # Páginas da aplicação
├── templates/
│   └── relatorio.html          # Template HTML para relatório
├── app.py                      # Ponto de entrada do Streamlit
├── requirements.txt            # Dependências do projeto
└── README.md                   # Documentação
```

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/analisador-sprint.git
cd analisador-sprint
```
2. Instale as dependências:
```bash
poetry install
```
3. Execute a aplicação:
```bash
streamlit run app.py
```

## Configuração

Para usar a aplicação, você precisa fornecer:

- **Organização**: Nome da sua organização no Azure DevOps
- **Projeto**: Nome do projeto
- **Equipe** (opcional): Nome da equipe
- **Personal Access Token (PAT)**: Token de acesso com permissões para leitura de itens de trabalho

## Uso

1. Acesse a aplicação em http://localhost:8501
2. Insira suas credenciais do Azure DevOps no menu lateral
3. Selecione o tipo de análise desejada
4. Escolha a sprint que deseja analisar
5. Execute a análise e explore os resultados