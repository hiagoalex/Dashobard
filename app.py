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
# FUNÇÃO PARA CARREGAR DADOS (VERSÃO ROBUSTA)
# ==========================
def carregar_dados():
    try:
        df_temp = pd.read_csv(URL_SHEETS, header=0)
    except Exception as e:
        print(f"Erro ao ler Google Sheets: {e}")
        # Retorna DataFrame vazio com as colunas padronizadas esperadas
        return pd.DataFrame(columns=[
            "nome","qtd_convites","confirmados","meta_convites","progresso_convites",
            "meta_confirmados","media_confirmados","ligacoes_efetuadas","confirmacoes_ligacoes",
            "vendedor_top_convites","unidade_top_convites","qtd_top_convites",
            "vendedor_confirmado","unidade_confirmados","convites_confirmados"
        ])

    # lista de cabeçalhos normalizados (maiúsculos, sem espaços laterais)
    cols_clean = [c.strip() for c in df_temp.columns]
    cols_upper = [c.upper() for c in cols_clean]

    header_map = {}

    # helper para mapear por nome (se existir)
    def map_if_exists(name_upper, target):
        if name_upper in cols_upper:
            header_map[cols_clean[cols_upper.index(name_upper)]] = target
            return True
        return False

    # Mapeamentos diretos (variants comuns)
    map_if_exists("NOME", "nome")
    map_if_exists("QUANTIDADE DE CONVITES", "qtd_convites")
    # 'CONFIRMADOS' aparece na sua planilha (maiusculo)
    map_if_exists("CONFIRMADOS", "confirmados")
    map_if_exists("META", "meta_convites")
    map_if_exists("PROGRESSO DE CONVITES", "progresso_convites")
    map_if_exists("META DE CONFIRMADOS", "meta_confirmados")
    # média de confirmados pode vir com acento ou sem
    if "MÉDIA DE CONFIRMADOS" in cols_upper:
        header_map[cols_clean[cols_upper.index("MÉDIA DE CONFIRMADOS")]] = "media_confirmados"
    elif "MEDIA DE CONFIRMADOS" in cols_upper:
        header_map[cols_clean[cols_upper.index("MEDIA DE CONFIRMADOS")]] = "media_confirmados"
    # ligações efetuadas variantes
    if "LIGAÇÕES EFETUADAS" in cols_upper:
        header_map[cols_clean[cols_upper.index("LIGAÇÕES EFETUADAS")]] = "ligacoes_efetuadas"
    elif "LIGACOES EFETUADAS" in cols_upper:
        header_map[cols_clean[cols_upper.index("LIGACOES EFETUADAS")]] = "ligacoes_efetuadas"
    # confirmações gerais (se existir)
    if "CONFIRMAÇÕES" in cols_upper:
        header_map[cols_clean[cols_upper.index("CONFIRMAÇÕES")]] = "confirmacoes_ligacoes"
    elif "CONFIRMACOES" in cols_upper:
        header_map[cols_clean[cols_upper.index("CONFIRMACOES")]] = "confirmacoes_ligacoes"

    # ---------------------------
    # TOP VENDEDORES (convites)
    # ---------------------------
    # vendedor_top_convites (coluna "VENDEDORES QUE ENVIARAM MAIS CONVITES")
    if "VENDEDORES QUE ENVIARAM MAIS CONVITES" in cols_upper:
        idx_vtop = cols_upper.index("VENDEDORES QUE ENVIARAM MAIS CONVITES")
        header_map[cols_clean[idx_vtop]] = "vendedor_top_convites"

        # busca a primeira UNIDADES que aparece *após* esse índice
        unidades_indices = [i for i, c in enumerate(cols_upper) if c == "UNIDADES"]
        unidade_idx = None
        for ui in unidades_indices:
            if ui > idx_vtop:
                unidade_idx = ui
                break
        if unidade_idx is not None:
            header_map[cols_clean[unidade_idx]] = "unidade_top_convites"
        else:
            # fallback: se existir qualquer 'UNIDADES', pega a primeira
            if unidades_indices:
                header_map[cols_clean[unidades_indices[0]]] = "unidade_top_convites"

        # busca o CONVITES relacionado (procura 'CONVITES' após idx_vtop)
        conv_indices = [i for i, c in enumerate(cols_upper) if c == "CONVITES"]
        conv_idx = None
        for ci in conv_indices:
            if ci > idx_vtop:
                conv_idx = ci
                break
        if conv_idx is not None:
            header_map[cols_clean[conv_idx]] = "qtd_top_convites"
        else:
            # fallback: se existir 'CONVITES' em qualquer lugar, pega a primeira
            if conv_indices:
                header_map[cols_clean[conv_indices[0]]] = "qtd_top_convites"

    # ---------------------------
    # TOP VENDEDORES (confirmados)
    # ---------------------------
    # vendedor_confirmado pode aparecer como 'vendedor_confirmado' (minúscula) ou como 'VENDEDORES QUE TIVERAM MAIS CONFIRMAÇÕES'
    # tenta mapear vários formatos:
    if "VENDEDORES QUE TIVERAM MAIS CONFIRMAÇÕES" in cols_upper:
        idx_vconf = cols_upper.index("VENDEDORES QUE TIVERAM MAIS CONFIRMAÇÕES")
        header_map[cols_clean[idx_vconf]] = "vendedor_confirmado"
    elif "VENDEDORES" in cols_upper and "CONFIRMAÇÕES" in cols_upper:
        # fallback genérico (não esperado, mas seguro)
        try:
            idx_vconf = cols_upper.index("VENDEDORES")
            header_map[cols_clean[idx_vconf]] = "vendedor_confirmado"
        except Exception:
            pass
    # também mapeia se a coluna vier exatamente como 'vendedor_confirmado' (minúscula)
    for i, c in enumerate(cols_clean):
        if c.strip().lower() == "vendedor_confirmado":
            header_map[c] = "vendedor_confirmado"
            idx_vconf = i
            break

    # agora localizar a UNIDADE que pertence a esse vendedor_confirmado
    if 'idx_vconf' in locals():
        unidades_indices = [i for i, c in enumerate(cols_upper) if c == "UNIDADES"]
        unidade_conf_idx = None
        for ui in unidades_indices:
            if ui > idx_vconf:
                unidade_conf_idx = ui
                break
        if unidade_conf_idx is not None:
            header_map[cols_clean[unidade_conf_idx]] = "unidade_confirmados"
        else:
            # fallback: se houver mais de uma UNIDADES, pega a segunda ocorrência
            if len(unidades_indices) > 1:
                header_map[cols_clean[unidades_indices[1]]] = "unidade_confirmados"

    # convites_confirmados: busca coluna 'CONVITES CONFIRMADOS' ou 'convites_confirmados'
    if "CONVITES CONFIRMADOS" in cols_upper:
        idx_cc = cols_upper.index("CONVITES CONFIRMADOS")
        header_map[cols_clean[idx_cc]] = "convites_confirmados"
    else:
        # tenta por nome exato minúsculo
        for i, c in enumerate(cols_clean):
            if c.strip().lower() == "convites_confirmados":
                header_map[c] = "convites_confirmados"
                break

    # ---------------------------
    # Renomeia conforme o mapeamento (se houver)
    # ---------------------------
    if header_map:
        df_temp = df_temp.rename(columns=header_map)

    # ---------------------------
    # Colunas esperadas padrão no retorno
    # ---------------------------
    expected_cols = [
        "nome","qtd_convites","confirmados","meta_convites","progresso_convites",
        "meta_confirmados","media_confirmados","ligacoes_efetuadas","confirmacoes_ligacoes",
        "vendedor_top_convites","unidade_top_convites","qtd_top_convites",
        "vendedor_confirmado","unidade_confirmados","convites_confirmados"
    ]

    # se alguma coluna esperada estiver faltando, cria com 0 ou string vazia (para textos)
    for col in expected_cols:
        if col not in df_temp.columns:
            # para colunas textuais, colocar string vazia; numéricas -> 0
            if col in ["nome","vendedor_top_convites","unidade_top_convites","vendedor_confirmado","unidade_confirmados"]:
                df_temp[col] = ""
            else:
                df_temp[col] = 0

    # Reordena e retorna somente as expected_cols
    df_temp = df_temp[expected_cols].copy()

    # Remove linhas sem nome (se aplicável)
    if 'nome' in df_temp.columns:
        df_temp.dropna(subset=['nome'], inplace=True)

    # Converte colunas que devem ser numéricas
    numeric_cols = [
        "qtd_convites","confirmados","meta_convites","progresso_convites",
        "meta_confirmados","media_confirmados","ligacoes_efetuadas",
        "confirmacoes_ligacoes","qtd_top_convites","convites_confirmados"
    ]
    for col in numeric_cols:
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

    # Build layout
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

            # 1.5 KPIs Dinâmicos (6 Cards) - 3 em cima e 3 embaixo reorganizados
            # Linha 1
            html.Div(className='kpi-grid three-columns', children=[
                html.Div(className='kpi-card success-card destaque-loja', children=[
                    html.H3("🥇 Top 10 vendedores que enviaram mais convites"),
                    html.Div(id='kpi-top-10-convites', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
                ]),
                html.Div(className='kpi-card success-card', children=[
                    html.H3("🚀 Top 5 lojas que mais enviaram convites"),
                    html.Div(id='kpi-top-5-convites', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
                ]),
                html.Div(className='kpi-card success-card', children=[
                    html.H3("🥇🥈🥉 Top 5 lojas com mais confirmações"),
                    html.Div(id='kpi-top-3-confirmadas', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
                ]),
            ]),

            # Linha 2
            html.Div(className='kpi-grid three-columns', children=[
                html.Div(className='kpi-card success-card destaque-loja', children=[
                    html.H3("🥇 Top 10 vendedores com convites confirmados"),
                    html.Div(id='kpi-top-10-confirmados', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
                ]),
                html.Div(className='kpi-card warning-card', children=[
                    html.H3("🐌 Top 5 lojas com menos confirmações"),
                    html.Div(id='kpi-bottom-5-confirmados', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
                ]),
                html.Div(className='kpi-card warning-card', children=[
                    html.H3("🐢 Top 5 lojas que menos enviaram convites"),
                    html.Div(id='kpi-bottom-3-convites', className="kpi-list", style={
                        'overflowX': 'auto', 'whiteSpace': 'nowrap', 'maxWidth': '100%', 'padding': '5px'
                    })
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

@app.callback(
    Output('kpi-top-3-confirmadas', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_top5_confirmacoes(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []
    top5 = df_local.sort_values(by='confirmacoes_ligacoes', ascending=False).head(5).reset_index(drop=True)
    lista = []
    for i, row in top5.iterrows():
        texto = f"{i+1}º {row['nome']}: {int(row['confirmacoes_ligacoes'])} confirmações"
        lista.append(html.Div(texto, style={"color": "#006600", "fontWeight": "600", "marginBottom": "6px"}))
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
    for i, row in bottom5.iterrows():
        texto = f"🐢 {row['nome']}: {int(row['qtd_convites'])} convites"
        lista.append(html.Div(texto, style={"color": "#cc6600", "fontWeight": "600", "marginBottom": "6px"}))
    return lista

# =============================
# ALTERAÇÃO 1
# TOP 10 VENDEDORES QUE ENVIOU CONVITES (AGORA COM LOJA)
# =============================
@app.callback(
    Output('kpi-top-10-convites', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_top10_convites(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []

    top10 = df_local.sort_values(by='qtd_top_convites', ascending=False).head(10).reset_index(drop=True)
    
    lista = []
    for i, row in top10.iterrows():
        texto = f"{i+1}º {row['vendedor_top_convites']} ({row['unidade_top_convites']}): {formatar_numero(row['qtd_top_convites'])} convites"
        lista.append(html.Div(
            texto,
            style={"color": "#0066cc", "fontWeight": "600", "marginBottom": "6px"}
        ))
    return lista

@app.callback(
    Output('kpi-bottom-5-confirmados', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_bottom5_confirmados(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []
    bottom5 = df_local.sort_values(by='confirmados', ascending=True).head(5).reset_index(drop=True)
    lista = []
    for _, row in bottom5.iterrows():
        texto = f"🐌 {row['nome']}: {int(row['confirmados'])} confirmações"
        lista.append(html.Div(texto, style={"color": "#cc0000", "fontWeight": "600", "marginBottom": "6px"}))
    return lista

@app.callback(
    Output('kpi-top-5-convites', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_top5_envios_convites(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []
    top5 = df_local.sort_values(by='qtd_convites', ascending=False).head(5).reset_index(drop=True)
    lista = []
    for i, row in top5.iterrows():
        texto = f"🚀 {row['nome']}: {int(row['qtd_convites'])} convites"
        lista.append(html.Div(texto, style={"color": "#009933", "fontWeight": "600", "marginBottom": "6px"}))
    return lista

# =============================
# ALTERAÇÃO 2
# TOP 10 VENDEDORES COM CONVITES CONFIRMADOS (AGORA COM LOJA)
# =============================
@app.callback(
    Output('kpi-top-10-confirmados', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_top10_confirmados(n):
    df_local = carregar_dados()
    if df_local.empty:
        return []

    top10_confirmados = df_local.sort_values(by='convites_confirmados', ascending=False).head(10).reset_index(drop=True)
    
    lista = []
    for i, row in top10_confirmados.iterrows():
        texto = f"{i+1}º {row['vendedor_confirmado']} ({row['unidade_confirmados']}): {int(row['convites_confirmados'])} confirmados"
        
        lista.append(html.Div(
            texto,
            style={"color": "#006600", "fontWeight": "600", "marginBottom": "6px"}
        ))
    return lista


# ==========================
# CALLBACK: Tabela Geral
# ==========================
@app.callback(
    Output('tabela-geral-dados', 'children'),
    Input('interval-update-data', 'n_intervals')
)
def atualizar_tabela(n):
    df_local = carregar_dados()
    return gerar_tabela_formatada(df_local)

# ==========================
# RODAR APP
# ==========================
if __name__ == '__main__':
    app.run(debug=True)