import streamlit as st
from utils.components import seletor_ano, input_multiselecao_casas, button_download
from utils.functions.general_functions import config_sidebar
from utils.queries_forecast import GET_ITENS_VENDIDOS_DIA_DA_SEMANA
from utils.functions.faturamento_dia_semana import *
from utils.functions.forecast import *


st.set_page_config(
    page_title="Faturamento ZigPay - Média por dia da semana",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title("💰 Faturamento ZigPay - Dias da Semana")
    st.markdown("""
    - Para uma casa selecionada, é exibida a média de faturamento (incluindo Alimentos, Bebidas, Couvert, Gifts e Serviço) por dia da semana de cada mês, do ano anterior e do atual, com cálculo da variação.
    - Para meses futuros, é calculada uma projeção baseada nas duas semanas anteriores.
    """)
with col2:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
st.divider()

# Seletores
# col1, col2 = st.columns(2, vertical_alignment='center')

# with col1:
lista_retirar_casas = ['Todas as Casas', 'Blue Note SP (Sala 2)', 'Edificio Rolim', 'Terraço Notie']
df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='faturamento_bruto', adicionar_delivery=True)
lista_casas_selecionadas = df_casas_selecionadas['Casa'].tolist()
lista_ids_casas_selecionadas = df_casas_selecionadas['ID_Casa'].tolist()
qtd_casas_selecionadas = len(lista_casas_selecionadas)
# with col2: 
#     ano = seletor_ano(2025, 2026, 'ano_faturamento_zig', 'Selecione um ano:')
st.divider()

if lista_casas_selecionadas == []:
  st.warning('Nenhuma casa selecionada.')
  st.stop()

if 'Arcos' in lista_casas_selecionadas: st.info('Observação: Arcos sem operação às segundas-feiras.')

# Query com todos os faturamentos da Zig
df_faturamento_diario = GET_ITENS_VENDIDOS_DIA_DA_SEMANA()

# Filtrando por casa e gerando coluna com dia da semana
df_faturamento_diario_casa = prepara_dados_faturamento_casa(df_faturamento_diario, lista_casas_selecionadas)
if df_faturamento_diario_casa.empty:
    st.warning(f'Sem dados de faturamento para a(s) casa(s) selecionada(s).')
    st.stop()

# Gera projeção para prox dias do mês corrente/seguinte por dia da semana
df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(datas['ano_atual'], df_faturamento_diario_casa)

df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_diario_casa, df_dias_futuros_com_categorias)
df_dias_futuros_mes['Mes_Ano'] = df_dias_futuros_mes['Mes_Ano'].fillna(df_dias_futuros_mes['Data Evento'].dt.strftime('%m/%Y'))

# Une meses já concluídos com mês corrente
if len(lista_casas_selecionadas) == 1:
    id_casa = lista_ids_casas_selecionadas[0]
    casa = lista_casas_selecionadas[0]
else:
    id_casa = 'Casas agrupadas'
    casa = 'Casas agrupadas'
df_faturamento_todos_meses = concatena_meses_reais_projetados(df_dias_futuros_mes, df_faturamento_diario_casa)

# Calcula faturamento geral por dia da semana para cada mês
pivot_faturamento_geral = calcula_faturamento_medio(df_faturamento_todos_meses, qtd_casas_selecionadas)

# Calcula variação entre ano anterior e atual
pivot_faturamento_geral = pivot_faturamento_geral.rename(columns={'Mes_Ano':'Mês/Ano'})
pivot_faturamento_geral['Mês'] = pivot_faturamento_geral['Mês/Ano'].str.split("/").str[0].astype(int)
pivot_faturamento_geral['Ano'] = pivot_faturamento_geral['Mês/Ano'].str.split("/").str[1].astype(int)
pivot_faturamento_geral = pivot_faturamento_geral[['Mês', 'Ano', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']]
pivot_faturamento_geral_variacao = calcula_variacao_ano_anterior(pivot_faturamento_geral)

# Aplica estilos e formatação
dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
mask = pivot_faturamento_geral_variacao['Ano'] == 'Variação'

for col in dias_semana: # Concatena variação (diferença) e variação (porcentagem)
    pivot_faturamento_geral_variacao.loc[mask, col] = (
        pivot_faturamento_geral_variacao.loc[mask, col]
        .map(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        + " ("
        + pivot_faturamento_geral_variacao.loc[mask, f'{col}_pct']
            .map(lambda x: f"{x:.1%}")
        + ")"
    )

colunas_pct = [c for c in pivot_faturamento_geral_variacao.columns if c.endswith('_pct')]
df_exibicao = pivot_faturamento_geral_variacao.drop(columns=colunas_pct)
# height = (len(pivot_faturamento_geral_variacao) + 1) * 35

for col in dias_semana: # Formatação numérica
    df_exibicao.loc[df_exibicao['Ano'] != 'Variação', col] = (
        df_exibicao.loc[df_exibicao['Ano'] != 'Variação', col]
        .apply(formato_br)
    )

# Aplica estilos (cores)
df_estilizado = df_exibicao.style.apply(lambda row: aplica_estilos(row, pivot_faturamento_geral_variacao), axis=1)

# if ano == datas['ano_atual']:
legenda = f"""
    <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
        <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
        <span style="font-size: 14px">Média de faturamento projetado (não real) para meses futuros do ano atual.</span>
    </div>
    """
# elif ano > datas['ano_atual']:
#     df_estilizado = pivot_faturamento_geral_formatado
#     legenda = f"""
#         <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
#             <span style="font-size: 14px"><b>Observação:</b> Esses valores são a média de faturamento projetado (não real).</span>
#         </div>
#         """
# elif ano < datas['ano_atual']:
#     df_estilizado = pivot_faturamento_geral_formatado
#     legenda = ""

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.subheader(f"Média de faturamento geral por dia da semana - {casa}")
with col2:
    button_download(pivot_faturamento_geral, f"Faturamento Dia da Semana", f"Faturamento Dia da Semana")
st.dataframe(df_estilizado, hide_index=True)
st.markdown(legenda, unsafe_allow_html=True) # Exibe legenda

st.divider()

# Detalhamento
st.subheader('Faturamento por categoria')
df_faturamento_categorias_todos_meses = df_faturamento_todos_meses[~df_faturamento_todos_meses['Categoria'].isna()].copy()

# Cria seletor
col1, col2 = st.columns([4, 1], vertical_alignment='bottom')
with col1:
    categorias_faturamento = df_faturamento_categorias_todos_meses['Categoria'].unique().tolist()
    categoria_selecionada = st.selectbox("Selecione uma categoria:", categorias_faturamento)

# Calcula a média de faturamento de cada categoria por dia da semana
pivot_faturamento_categoria_dia_semana = calcula_faturamento_medio(df_faturamento_todos_meses, qtd_casas_selecionadas, detalhamento_categoria=True, categoria_selecionada=categoria_selecionada)

with col2:
    button_download(pivot_faturamento_categoria_dia_semana, f"Faturamento por Categoria", f"Faturamento por Categoria")

# Calcula variação entre ano anterior e atual
pivot_faturamento_categoria_dia_semana = pivot_faturamento_categoria_dia_semana.rename(columns={'Mes_Ano':'Mês/Ano'})
pivot_faturamento_categoria_dia_semana['Mês'] = pivot_faturamento_categoria_dia_semana['Mês/Ano'].str.split("/").str[0].astype(int)
pivot_faturamento_categoria_dia_semana['Ano'] = pivot_faturamento_categoria_dia_semana['Mês/Ano'].str.split("/").str[1].astype(int)
pivot_faturamento_categoria_dia_semana = pivot_faturamento_categoria_dia_semana[['Mês', 'Ano', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']]
pivot_faturamento_categoria_dia_semana = calcula_variacao_ano_anterior(pivot_faturamento_categoria_dia_semana)

# Aplica estilos e formatação
mask = pivot_faturamento_categoria_dia_semana['Ano'] == 'Variação'

for col in dias_semana: # Concatena variação (diferença) e variação (porcentagem)
    pivot_faturamento_categoria_dia_semana.loc[mask, col] = (
        pivot_faturamento_categoria_dia_semana.loc[mask, col]
        .map(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        + " ("
        + pivot_faturamento_categoria_dia_semana.loc[mask, f'{col}_pct']
            .map(lambda x: f"{x:.1%}")
        + ")"
    )

colunas_pct = [c for c in pivot_faturamento_categoria_dia_semana.columns if c.endswith('_pct')]
df_exibicao = pivot_faturamento_categoria_dia_semana.drop(columns=colunas_pct)
# height = (len(pivot_faturamento_categoria_dia_semana) + 1) * 35

for col in dias_semana: # Formatação numérica
    df_exibicao.loc[df_exibicao['Ano'] != 'Variação', col] = (
        df_exibicao.loc[df_exibicao['Ano'] != 'Variação', col]
        .apply(formato_br)
    )

# Aplica estilos (cores)
df_estilizado = df_exibicao.style.apply(lambda row: aplica_estilos(row, pivot_faturamento_categoria_dia_semana), axis=1)

# if ano == datas['ano_atual']:
legenda = f"""
    <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
        <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
        <span style="font-size: 14px">Média de faturamento projetado (não real) para meses futuros do ano atual.</span>
    </div>
    """
# elif ano > datas['ano_atual']:
#     df_estilizado = pivot_faturamento_categoria_dia_semana_formatado
#     legenda = f"""
#         <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
#             <span style="font-size: 14px"><b>Observação:</b> Esses valores são a média de faturamento projetado (não real).</span>
#         </div>
#         """
# elif ano < datas['ano_atual']:
#     df_estilizado = pivot_faturamento_categoria_dia_semana_formatado
#     legenda = ""

st.dataframe(df_estilizado, hide_index=True)
st.markdown(legenda, unsafe_allow_html=True) # Exibe legenda

