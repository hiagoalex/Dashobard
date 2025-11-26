import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import locale
from datetime import datetime
import os
import pytz

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
        return locale.format_string("%d", int(n), grouping=True)
    except Exception:
        return f"{int(n):,}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================
# LINK CSV DO GOOGLE SHEETS
# ==========================
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRRoTZ50By6BN1ThLry1WykGR57GTaH5pmvBZUxLqU2gnBV3qUZGlBFk4FkMaSAUw/pub?gid=1684851949&single=true&output=csv"

# ==========================
# FUNÇÃO PARA CARREGAR DADOS
# ==========================
def carregar_dados():
    try:
        df_temp = pd.read_csv(URL_SHEETS, header=0)
    except Exception as e:
        print(f"Erro ao ler Google Sheets: {e}")
        return pd.DataFrame(columns=[
            "nome","qtd_convites","meta_convites","progresso_convites",
            "confirmados","meta_confirmados","media_confirmados",
            "ligacoes_efetuadas","confirmacoes_ligacoes"
        ])

    cols_lower = [c.strip().upper() for c in df_temp.columns]
    header_map = {}
    if "NOME" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("NOME")]] = "nome"
    if "QUANTIDADE DE CONVITES" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("QUANTIDADE DE CONVITES")]] = "qtd_convites"
    if "META" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("META")]] = "meta_convites"
    if "PROGRESSO DE CONVITES" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("PROGRESSO DE CONVITES")]] = "progresso_convites"
    if "CONFIRMADOS" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("CONFIRMADOS")]] = "confirmados"
    if "META DE CONFIRMADOS" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("META DE CONFIRMADOS")]] = "meta_confirmados"
    if "MÉDIA DE CONFIRMADOS" in cols_lower or "MEDIA DE CONFIRMADOS" in cols_lower:
        header_map[list(df_temp.columns)[cols_lower.index("MÉDIA DE CONFIRMADOS" if "MÉDIA DE CONFIRMADOS" in cols_lower else "MEDIA DE CONFIRMADOS")]] = "media_confirmados"
    if "LIGAÇÕES EFETUADAS" in cols_lower or "LIGACOES EFETUADAS" in cols_lower:
        idx = cols_lower.index("LIGAÇÕES EFETUADAS") if "LIGAÇÕES EFETUADAS" in cols_lower else cols_lower.index("LIGACOES EFETUADAS")
        header_map[list(df_temp.columns)[idx]] = "ligacoes_efetuadas"
    if "CONFIRMAÇÕES" in cols_lower or "CONFIRMACOES" in cols_lower:
        idx = cols_lower.index("CONFIRMAÇÕES") if "CONFIRMAÇÕES" in cols_lower else cols_lower.index("CONFIRMACOES")
        header_map[list(df_temp.columns)[idx]] = "confirmacoes_ligacoes"

    if header_map:
        df_temp = df_temp.rename(columns=header_map)

    expected_cols = [
        "nome","qtd_convites","meta_convites","progresso_convites",
        "confirmados","meta_confirmados","media_confirmados",
        "ligacoes_efetuadas","confirmacoes_ligacoes"
    ]

    if not all(c in df_temp.columns for c in expected_cols):
        if len(df_temp.columns) >= 9:
            df_temp = df_temp.iloc[:, :9]
            df_temp.columns = expected_cols
        else:
            return pd.DataFrame(columns=expected_cols)

    df_temp = df_temp[expected_cols].copy()
    df_temp.dropna(subset=['nome'], inplace=True)
    for col in ["qtd_convites","meta_convites","progresso_convites","confirmados",
                "meta_confirmados","media_confirmados","ligacoes_efetuadas",
                "confirmacoes_ligacoes"]:
        df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce').fillna(0)

    return df_temp

# ==================================
# 🟨 FUNÇÃO ATUALIZADA: GERAR TABELA COM CORES
# ==================================
def gerar_tabela_formatada(df):
    if df.empty:
        return html.Div("Nenhum dado encontrado.")

    # --- Função de cor (apenas fundo) ---
    def cor_linha(row):
        try:
            taxa = row['confirmados'] / row['meta_confirmados'] if row['meta_confirmados'] > 0 else 0
        except Exception:
            taxa = 0

        if taxa >= 0.90:
            return "#c4f4d4"  # Verde
        elif taxa >= 0.60:
            return "#fff8b3"  # Amarelo
        else:
            return "#fceb00"  # Vermelho (não rosa forte)

    # --- Tabela formatada ---
    tabela = html.Table([
        html.Thead(
            html.Tr([
                html.Th(
                    col,
                    style={
                        'backgroundColor': '#1f2937',
                        'color': 'white',
                        'padding': '8px',
                        'fontWeight': 'bold',
                        'border': '2px solid #fff'
                    }
                )
                for col in df.columns
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(
                    formatar_numero(cell) if isinstance(cell, (int, float)) else cell,
                    style={
                        'padding': '6px',
                        'textAlign': 'center',
                        'border': '2px solid white',
                        'color': 'black',
                        'fontSize': '13px',
                        'fontWeight': '600'
                    }
                )
                for cell in row
            ],
            style={'backgroundColor': cor_linha(df.iloc[i])})
            for i, row in enumerate(df.values)
        ])
    ],
    style={
        'width': '100%',
        'borderCollapse': 'collapse',
        'fontFamily': 'Arial, sans-serif'
    })

    return tabela

# ==========================
# FUNÇÃO PARA GERAR LAYOUT (mantendo seu layout original)
# ==========================
def gerar_layout(df):
    # Renomear colunas para nomes legíveis no layout
    df = df.rename(columns={
        'qtd_convites': 'Quantidade de convites',
        'meta_convites': 'Meta de convites',
        'confirmados': 'Confirmados',
        'meta_confirmados': 'Meta_confirmados',
        'ligacoes_efetuadas': 'Ligacoes_efetuadas',
        'confirmacoes_ligacoes': 'Ligações confirmadas',
        'nome': 'Nome'
    })

    # calcula KPIs globais
    total_convites = df['Quantidade de convites'].sum()
    meta_convites_global = df['Meta de convites'].sum()
    total_confirmados = df['Confirmados'].sum()
    meta_confirmados_global = df['Meta_confirmados'].sum()
    total_ligacoes = df['Ligacoes_efetuadas'].sum()
    media_geral_progresso = (total_convites / meta_convites_global) if meta_convites_global > 0 else 0
    media_geral_confirmacao = (total_confirmados / total_convites) if total_convites > 0 else 0

    if not df.empty:
        # loja com maior confirmações por ligação (mantendo seu campo)
        try:
            loja_mais_confirmacoes = df.loc[df['Ligações confirmadas'].idxmax()]
            nome_loja_mais_confirmacoes = loja_mais_confirmacoes['Nome']
            valor_mais_confirmacoes = loja_mais_confirmacoes['Ligações confirmadas']
        except Exception:
            nome_loja_mais_confirmacoes = "N/A"
            valor_mais_confirmacoes = 0
    else:
        nome_loja_mais_confirmacoes = "N/A"
        valor_mais_confirmacoes = 0

    # Data de atualização (horário de Brasília)
    data_modificacao = datetime.now(pytz.timezone("America/Sao_Paulo"))
    ultima_atualizacao = data_modificacao.strftime("%d/%m/%Y %H:%M")

    # Top 5 confirmações
    top5 = df.sort_values(by='Confirmados', ascending=False).head(5) if not df.empty else pd.DataFrame()
    # Bottom 5 convites
    bottom5 = df.sort_values(by='Quantidade de convites', ascending=True).head(5) if not df.empty else pd.DataFrame()

    # Build layout (idêntico ao seu)
    return html.Div(children=[

        # CABEÇALHO COM LOGO + TÍTULO + DATA
        html.Div(className='header-section', children=[
            html.Div(className='header-content-wrapper', children=[
                html.Div(className='header-text-container', style={'display': 'flex', 'align-items': 'center'}, children=[
                    html.Img(
                        src='/assets/logo.png',
                        style={'height': '180px', 'width': 'auto', 'margin-right': '15px'}
                    ),
                    html.Div(children=[
                        html.H1(
                            "🏆 Dashboard de Performance por Unidades - Grupo Primavia",
                            className='dashboard-title grupo-Primavia-header'
                        ),
                        html.Div(
                            f"📅 Última atualização dos dados: {ultima_atualizacao}",
                            style={
                                'fontSize': '16px',
                                'color': '#374151',
                                'fontWeight': '600',
                                'marginTop': '5px'
                            }
                        )
                    ])
                ])
            ])
        ]),

        html.Div(className='dash-app-content', children=[

            # 1. KPIs Globais (5 Cards)
            html.H2("Performance Agregada Geral", className='section-title'),
            html.Div(className='kpi-grid five-columns', children=[

                html.Div(className='kpi-card', children=[
                    html.H3("Total Convites Enviados"),
                    html.P(formatar_numero(total_convites), className='kpi-value'),
                    html.Small("Total de convites já enviados")
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

            # 1.5 KPIs Dinâmicos (Top 5 / Bottom 5)
            html.Div(className='kpi-grid three-columns', children=[
                html.Div(className='kpi-card success-card destaque-loja', children=[
                    html.H3("🥇 Unidade: Maior Taxa de Conversão por Ligação"),
                    html.P(f"{nome_loja_mais_confirmacoes}", className='kpi-value'),
                    html.Small(f"Índice de Confirmações por Ligação: {formatar_numero(valor_mais_confirmacoes)}")
                ]),
                html.Div(className='kpi-card success-card', children=[
                    html.H3("🥇🥈🥉 Top 5 lojas com mais confirmações"),
                    html.Div(id='kpi-top-3-confirmadas', className="kpi-list")
                ]),
                html.Div(className='kpi-card warning-card', children=[
                    html.H3("🐢 Top 5 lojas que menos enviaram convites"),
                    html.Div(id='kpi-bottom-3-convites', className="kpi-list")
                ]),
            ]),

            # 2. Filtro e Detalhe da Unidade
            html.Div(className='unit-detail-section', children=[
                html.H2("Análise Detalhada de Performance", className='section-title'),
                dcc.Dropdown(
                    id='select-unidade',
                    options=[{'label': i, 'value': i} for i in df['Nome'].unique()],
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

# ==========================
# INICIALIZAÇÃO DO DASH
# ==========================
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Mantemos um layout externo que será reconstruído a cada intervalo
app.layout = html.Div([
    dcc.Interval(id='interval-update-data', interval=5 * 60 * 1000, n_intervals=0),
    html.Div(id='layout-div')
])

# Callback para reconstruir layout a cada intervalo (5 minutos)
@app.callback(
    Output('layout-div', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def rebuild_layout(n):
    df_local = carregar_dados()
    return gerar_layout(df_local)

# Callback para detalhe por unidade (mantém comportamento original)
@app.callback(
    Output('detalhe-unidade', 'children'),
    Output('detalhe-unidade', 'style'),
    Input('select-unidade', 'value')
)
def exibir_detalhe_unidade(selected_unidade):
    if not selected_unidade:
        return "", {'display': 'none'}

    df_current = carregar_dados().copy()
    unidade = df_current[df_current['nome'] == selected_unidade].iloc[0]

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

# Callbacks que preenchem as listas Top5 e Bottom5 (com cores e medalhas)
@app.callback(
    Output('kpi-top-3-confirmadas', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_top5_confirmacoes(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []
    top5 = df_local.sort_values(by='confirmados', ascending=False).head(5).reset_index(drop=True)
    medalhas = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    lista = []
    for i, row in top5.iterrows():
        texto = f"{medalhas[i]} {row['nome']}: {int(row['confirmados'])} confirmações"
        lista.append(html.Div(texto, style={"color": "#009933", "fontWeight": "600", "marginBottom": "6px"}))
    return lista

@app.callback(
    Output('kpi-bottom-3-convites', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_bottom5_convites(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []
    bottom5 = df_local.sort_values(by='qtd_convites', ascending=True).head(5).reset_index(drop=True)
    lista = []
    for _, row in bottom5.iterrows():
        texto = f"🐢 {row['nome']}: {int(row['qtd_convites'])} convites"
        lista.append(html.Div(texto, style={"color": "#cc0000", "fontWeight": "600", "marginBottom": "6px"}))
    return lista

# Callback para preencher tabela de dados (mantendo seu gerador de tabela)
@app.callback(
    Output('tabela-geral-dados', 'children'),
    Input('select-unidade', 'value')
)
def update_tabela_dados(value):
    df_local = carregar_dados()
    return gerar_tabela_formatada(df_local)

# Placeholders callbacks (mantidos)
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
    # Use app.run(debug=True) para compatibilidade com versões recentes do Dash
    app.run(debug=True)
