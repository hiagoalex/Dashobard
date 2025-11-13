import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import locale
from datetime import datetime
import plotly.graph_objects as go 

# Configurar locale para formatação de números em português
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Atenção: Locale português não configurado. Os números serão formatados no padrão padrão.")

def formatar_numero(n):
    """Formata número inteiro com separador de milhar."""
    if pd.isna(n):
        return "N/A"
    try:
        # Usa o locale configurado para formatação
        return locale.format_string("%d", int(n), grouping=True)
    except Exception:
        # Fallback se o locale falhar
        return f"{int(n):,}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- 1. CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS ---
try:
    # ATENÇÃO: Se o seu arquivo for DADO.xlsx, troque 'data/dados.xlsx' para 'data/DADO.xlsx'
    df = pd.read_excel('data/dados.xlsx', sheet_name=0, header=0) 
    
    # Renomear colunas para corresponder ao modelo
    df.columns = [
        "nome", "qtd_convites", "meta_convites", "progresso_convites",
        "confirmados", "meta_confirmados", "media_confirmados",
        "ligacoes_efetuadas", "confirmacoes_ligacoes"
    ]

    # Ajustar tipos de dados e tratar valores ausentes como 0
    df['qtd_convites'] = pd.to_numeric(df['qtd_convites'], errors='coerce').fillna(0)
    df['meta_convites'] = pd.to_numeric(df['meta_convites'], errors='coerce').fillna(0)
    df['progresso_convites'] = pd.to_numeric(df['progresso_convites'], errors='coerce').fillna(0)
    df['confirmados'] = pd.to_numeric(df['confirmados'], errors='coerce').fillna(0)
    df['meta_confirmados'] = pd.to_numeric(df['meta_confirmados'], errors='coerce').fillna(0)
    df['media_confirmados'] = pd.to_numeric(df['media_confirmados'], errors='coerce').fillna(0)
    df['ligacoes_efetuadas'] = pd.to_numeric(df['ligacoes_efetuadas'], errors='coerce').fillna(0)
    df['confirmacoes_ligacoes'] = pd.to_numeric(df['confirmacoes_ligacoes'], errors='coerce').fillna(0)

except FileNotFoundError:
    print("\n🚨 ERRO: O arquivo 'dados.xlsx' não foi encontrado na pasta 'data/'.")
    print("Certifique-se de que a planilha está lá.")
    exit()
except Exception as e:
    print(f"\n🚨 ERRO ao carregar ou processar a planilha: {e}")
    exit()

# --- 2. CÁLCULO DE KPIS GLOBAIS ---
total_convites = df['qtd_convites'].sum()
meta_convites_global = df['meta_convites'].sum()
total_confirmados = df['confirmados'].sum()
meta_confirmados_global = df['meta_confirmados'].sum()
total_ligacoes = df['ligacoes_efetuadas'].sum() 

media_geral_progresso = (total_convites / meta_convites_global) if meta_convites_global > 0 else 0
media_geral_confirmacao = (total_confirmados / total_convites) if total_convites > 0 else 0

if not df.empty:
    loja_mais_confirmacoes = df.loc[df['confirmacoes_ligacoes'].idxmax()]
    nome_loja_mais_confirmacoes = loja_mais_confirmacoes['nome']
    valor_mais_confirmacoes = loja_mais_confirmacoes['confirmacoes_ligacoes']
else:
    nome_loja_mais_confirmacoes = "N/A"
    valor_mais_confirmacoes = 0


# --- 3. INICIALIZAÇÃO DO DASHBOARD ---
# O Dash automaticamente procura e carrega o 'style.css' da pasta 'assets/'
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# --- 4. LAYOUT DO DASHBOARD (LOGO E DATA REMOVIDAS) ---
app.layout = html.Div(children=[
    html.Div(className='header-section', children=[
        html.Div(className='header-content-wrapper', children=[ 
            # LOGO REMOVIDA
            html.Div(className='header-text-container', children=[
                html.H1("🏆 Dashboard de Performance por Unidades - Grupo Sinal", className='dashboard-title grupo-sinal-header'),
                # LINHA DE ATUALIZAÇÃO REMOVIDA
            ])
        ])
    ]),

    html.Div(className='dash-app-content', children=[
        
        # 1. KPIs Globais (5 Cards)
        html.H2("Performance Agregada Geral", className='section-title'),
        html.Div(className='kpi-grid five-columns', children=[ 
            
            html.Div(className='kpi-card', children=[
                html.H3("Total Convites"),
                html.P(formatar_numero(total_convites), className='kpi-value'),
                html.Small(f"Meta Global: {formatar_numero(meta_convites_global)}")
            ]),
            
            html.Div(className='kpi-card', children=[
                html.H3("Total Confirmados"),
                html.P(formatar_numero(total_confirmados), className='kpi-value'),
                html.Small(f"Meta Global: {formatar_numero(meta_confirmados_global)}")
            ]),
            
            html.Div(className='kpi-card', children=[
                html.H3("Total Ligações"),
                html.P(formatar_numero(total_ligacoes), className='kpi-value'),
                html.Small("Ligações Efetuadas")
            ]),
            
            html.Div(className='kpi-card highlight', children=[
                html.H3("Média Geral de Progresso"),
                html.P(f"{media_geral_progresso:.2%}", className='kpi-value'),
                html.Small("Convites / Meta")
            ]),
            
            html.Div(className='kpi-card highlight', children=[
                html.H3("Taxa Geral de Confirmação"),
                html.P(f"{media_geral_confirmacao:.2%}", className='kpi-value'),
                html.Small("Confirmados / Convites")
            ]),
        ]),

        # 1.5 KPIs Dinâmicos (3 Cards/Listas)
        html.Div(className='kpi-grid three-columns', children=[ 
            html.Div(className='kpi-card success-card destaque-loja', children=[ 
                html.H3("🥇 Unidade: Maior Taxa de Conversão por Ligação"),
                html.P(f"{nome_loja_mais_confirmacoes}", className='kpi-value'),
                html.Small(f"Índice de Confirmações por Ligação: {formatar_numero(valor_mais_confirmacoes)}")
            ]),
            
            html.Div(className='kpi-card success-card', children=[
                html.H3("🏆 As 3 melhores lojas que tiveram confirmações"),
                html.Div(id='kpi-top-3-confirmadas', className="kpi-list")
            ]),
            
            html.Div(className='kpi-card warning-card', children=[
                html.H3("🐌 As 3 lojas que tiveram menos convites enviados"),
                html.Div(id='kpi-bottom-3-convites', className="kpi-list")
            ]),
        ]),

        # 2. Filtro e Detalhe da Unidade
        html.Div(className='unit-detail-section', children=[
            html.H2("Análise Detalhada de Performance", className='section-title'),
            dcc.Dropdown(
                id='select-unidade',
                options=[{'label': i, 'value': i} for i in df['nome'].unique()],
                placeholder="Selecione uma Unidade para ver detalhes...",
                style={'width': '100%', 'maxWidth': '600px', 'margin': '0 auto 20px auto'}
            ),
            html.Div(id='detalhe-unidade', className='kpi-grid', style={'display': 'none'})
        ]),
        
        # 3. TABELA DE DADOS
        html.H2("Performance Detalhada por Unidade", className='section-title'),
        html.Div(className='chart-container', children=[
            html.Div(id='tabela-geral-dados', style={'height': 'auto'}),
        ]),

        html.Div(id='placeholder-grafico-ranking', style={'display': 'none'}),
        html.Div(id='placeholder-grafico-ligacoes', style={'display': 'none'}),
        html.Div(id='grafico-performance-bolhas', style={'display': 'none'}),
    ])
])

# --- 5. CALLBACKS PARA INTERATIVIDADE (FILTRO DA UNIDADE) ---
@app.callback(
    Output('detalhe-unidade', 'children'),
    Output('detalhe-unidade', 'style'),
    Input('select-unidade', 'value')
)
def exibir_detalhe_unidade(selected_unidade):
    if not selected_unidade:
        return "", {'display': 'none'}

    unidade = df[df['nome'] == selected_unidade].iloc[0]

    children = [
        html.Div(className='kpi-card highlight', children=[
            html.H3(unidade['nome']),
            html.P(f"{unidade['progresso_convites']:.2%}", className='kpi-value'),
            html.Small("Progresso Convites / Meta")
        ]),
        html.Div(className='kpi-card', children=[
            html.H3("Volume Confirmações / Convites"), 
            html.P(formatar_numero(unidade['confirmados']), className='kpi-value'), 
            html.Small(f"Enviados: {formatar_numero(unidade['qtd_convites'])} | Eficiência: {unidade['media_confirmados']:.2%}")
        ]),
        html.Div(className='kpi-card', children=[
            html.H3("Meta Confirmados"),
            html.P(formatar_numero(unidade['meta_confirmados']), className='kpi-value'),
            html.Small("Volume Esperado de Confirmações")
        ]),
        html.Div(className='kpi-card', children=[
            html.H3("Ligações Efetuadas"),
            html.P(formatar_numero(unidade['ligacoes_efetuadas']), className='kpi-value'),
            html.Small(f"Confirmações: {formatar_numero(unidade['confirmacoes_ligacoes'])}")
        ]),
    ]
    return children, {'display': 'grid'}


# --- 5.5 CALLBACKS PARA OS KPIS DINÂMICOS ---
@app.callback(
    Output('kpi-top-3-confirmadas', 'children'),
    Input('select-unidade', 'value') 
)
def update_kpi_top_3_confirmadas(value):
    # Lógica: Maiores Confirmações
    df_temp = df.copy().sort_values(by='confirmados', ascending=False).head(3)
    
    list_items = []
    for index, row in df_temp.iterrows():
        text = f"🥇 {row['nome']}: {formatar_numero(row['confirmados'])} Confirmações"
        list_items.append(html.Li(html.B(text), style={'fontSize': '1.1em'}, className="mb-1"))

    return html.Ul(list_items, className="list-unstyled p-2")

@app.callback(
    Output('kpi-bottom-3-convites', 'children'),
    Input('select-unidade', 'value')
)
def update_kpi_bottom_3_convites(value):
    # Lógica: Menos Convites Enviados (qtd_convites)
    df_temp = df.copy().sort_values(by='qtd_convites', ascending=True).head(3) 
    
    list_items = []
    for index, row in df_temp.iterrows():
        # Texto atualizado para mostrar a métrica de "Convites Enviados"
        text = f"❌ {row['nome']}: {formatar_numero(row['qtd_convites'])} Convites Enviados" 
        list_items.append(html.Li(html.B(text), style={'fontSize': '1.1em'}, className="mb-1"))

    return html.Ul(list_items, className="list-unstyled p-2")


# --- 6. GERAÇÃO DA TABELA DE DADOS NO FORMATO DE COLUNAS ---

def gerar_tabela_formatada(df_input):
    """Cria a tabela de dados formatada (similar a Excel) com a nomenclatura solicitada."""
    
    df_tabela = df_input.copy()
    
    df_tabela['Foco_Diretoria'] = df_tabela['media_confirmados'].apply(
        lambda x: 'baixa-eficiencia' if x < 0.05 else ('alta-performance' if x > 0.15 else 'monitorar')
    )
    
    # Colunas da tabela no formato literal (mantidas)
    columns = [
        {'id': 'nome', 'name': 'UNIDADE'},
        {'id': 'qtd_convites', 'name': 'QUANTIDADE DE CONVITES', 'format': formatar_numero},
        {'id': 'meta_convites', 'name': 'META (CONVITES)', 'format': formatar_numero}, 
        {'id': 'progresso_convites', 'name': 'PROGRESSO DE CONVITES', 'format': lambda x: f"{x:.2%}"}, 
        {'id': 'confirmados', 'name': 'CONFIRMADOS (ENVIOS)', 'format': formatar_numero},
        {'id': 'meta_confirmados', 'name': 'META DE CONFIRMADOS', 'format': formatar_numero}, 
        {'id': 'media_confirmados', 'name': 'MÉDIA DE CONFIRMADOS', 'format': lambda x: f"{x:.2%}"}, 
        {'id': 'ligacoes_efetuadas', 'name': 'LIGAÇÕES EFETUADAS', 'format': formatar_numero},
        {'id': 'confirmacoes_ligacoes', 'name': 'CONFIRMAÇÕES (LIG.)', 'format': formatar_numero},
    ]

    rows = []
    df_tabela = df_tabela.sort_values(by='media_confirmados', ascending=False)
    
    for index, row in df_tabela.iterrows():
        row_class = row['Foco_Diretoria']
        cells = []
        for col in columns:
            value = row[col['id']]
            display_value = col.get('format', lambda x: x)(value) 
            cells.append(html.Td(display_value, className='data-cell'))
        rows.append(html.Tr(cells, className=f'data-row {row_class}'))

    header = html.Thead(html.Tr([html.Th(col['name'], className='header-cell') for col in columns]))
    return html.Table([header, html.Tbody(rows)], className='data-table')

@app.callback(
    Output('tabela-geral-dados', 'children'),
    Input('select-unidade', 'value')
)
def update_tabela_dados(value):
    return gerar_tabela_formatada(df)
    
@app.callback(Output('placeholder-grafico-ranking', 'children'), [Input('select-unidade', 'value')])
def remove_grafico_ranking(value):
    return None 

@app.callback(Output('placeholder-grafico-ligacoes', 'children'), [Input('select-unidade', 'value')])
def remove_grafico_ligacoes(value):
    return None

@app.callback(Output('grafico-performance-bolhas', 'children'), [Input('select-unidade', 'value')])
def remove_grafico_bolhas(value):
    return None

# --- 7. EXECUTAR O DASHBOARD ---
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)