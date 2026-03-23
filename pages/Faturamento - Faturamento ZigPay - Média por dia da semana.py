import streamlit as st
from utils.components import seletor_ano, input_multiselecao_casas, button_download
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import GET_ITENS_VENDIDOS_DIA_DA_SEMANA
from utils.functions.faturamento_dia_semana import *
from utils.functions.forecast import *
from utils.user import logout


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
    - Para uma casa e ano selecionados, exibe a média de faturamento desse período incluindo Alimentos, Bebidas, Couvert e Serviço por dia da semana
    - Para meses futuros, calcula uma projeção baseada nas duas semanas anteriores
    """)
with col2:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
st.divider()

# Seletores
col1, col2 = st.columns(2, vertical_alignment='center')

with col1:
    lista_retirar_casas = ['Todas as Casas']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='faturamento_bruto', adicionar_delivery=True)
    lista_casas_selecionadas = df_casas_selecionadas['Casa'].tolist()
    lista_ids_casas_selecionadas = df_casas_selecionadas['ID_Casa'].tolist()
with col2: 
    ano = seletor_ano(2025, 2026, 'ano_faturamento_zig', 'Selecione um ano:')
st.divider()

if lista_casas_selecionadas == []:
  st.warning('Nenhuma casa selecionada.')
  st.stop()

# Query com todos os faturamentos da Zig
df_faturamento_diario = GET_ITENS_VENDIDOS_DIA_DA_SEMANA()

# Filtrando por casa e gerando coluna com dia da semana
df_faturamento_diario_casa = prepara_dados_faturamento_casa(df_faturamento_diario, lista_casas_selecionadas)

# Gera projeção para prox dias do mês corrente/seguinte por dia da semana
df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(
    datas['ano_atual'], 
    datas['mes_atual'], 
    df_faturamento_diario_casa
)

df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_diario_casa, df_dias_futuros_com_categorias)
df_dias_futuros_mes['Mes_Ano'] = df_dias_futuros_mes['Mes_Ano'].fillna(df_dias_futuros_mes['Data Evento'].dt.strftime('%m-%Y'))

# Une meses já concluídos com mês corrente
if len(lista_casas_selecionadas) == 1:
    id_casa = lista_ids_casas_selecionadas[0]
    casa = lista_casas_selecionadas[0]
else:
    id_casa = 'Agrupamento'
    casa = 'Agrupamento'
df_faturamento_todos_meses = concatena_meses_reais_projetados(df_dias_futuros_mes, df_faturamento_diario_casa, id_casa, casa, ano)

# Calcula faturamento geral por dia da semana para cada mês
pivot_faturamento_geral = calcula_faturamento_medio(df_faturamento_todos_meses, ano)

# Formata e estiliza exibição
pivot_faturamento_geral_formatado = formata_df(pivot_faturamento_geral)
pivot_faturamento_geral_formatado = pivot_faturamento_geral_formatado.rename(columns={'Mes_Ano':'Mês-Ano'})
if ano == datas['ano_atual']:
    df_estilizado = pivot_faturamento_geral_formatado.style.apply(destaca_mes_atual_seguintes, axis=1) # Pinta mês corrente (ainda não concluído)
    legenda = f"""
        <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
            <span style="font-size: 14px">Média de faturamento projetado (não real). Mês ainda não está concluído.</span>
        </div>
        """
elif ano > datas['ano_atual']:
    df_estilizado = pivot_faturamento_geral_formatado
    legenda = f"""
        <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <span style="font-size: 14px"><b>Observação:</b> Esses valores são a média de faturamento projetado (não real).</span>
        </div>
        """
elif ano < datas['ano_atual']:
    df_estilizado = pivot_faturamento_geral_formatado
    legenda = ""

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.subheader(f"Média de faturamento geral por dia da semana - {casa} - {ano}")
with col2:
    button_download(pivot_faturamento_geral, f"Faturamento Dia da Semana", f"Faturamento Dia da Semana")
st.dataframe(df_estilizado, hide_index=True, height=458)
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
pivot_faturamento_categoria_dia_semana = calcula_faturamento_medio(df_faturamento_todos_meses, ano, detalhamento_categoria=True, categoria_selecionada=categoria_selecionada)

with col2:
    button_download(pivot_faturamento_categoria_dia_semana, f"Faturamento por Categoria", f"Faturamento por Categoria")

# Formata e estiliza exibição
pivot_faturamento_categoria_dia_semana_formatado = formata_df(pivot_faturamento_categoria_dia_semana)
pivot_faturamento_categoria_dia_semana_formatado = pivot_faturamento_categoria_dia_semana_formatado.rename(columns={'Mes_Ano':'Mês-Ano'})

if ano == datas['ano_atual']:
    df_estilizado = pivot_faturamento_categoria_dia_semana_formatado.style.apply(destaca_mes_atual_seguintes, axis=1) # Pinta mês corrente (ainda não concluído)
    legenda = f"""
        <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
            <span style="font-size: 14px">Média de faturamento projetado (não real). Mês ainda não está concluído.</span>
        </div>
        """
elif ano > datas['ano_atual']:
    df_estilizado = pivot_faturamento_categoria_dia_semana_formatado
    legenda = f"""
        <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <span style="font-size: 14px"><b>Observação:</b> Esses valores são a média de faturamento projetado (não real).</span>
        </div>
        """
elif ano < datas['ano_atual']:
    df_estilizado = pivot_faturamento_categoria_dia_semana_formatado
    legenda = ""

st.dataframe(df_estilizado, hide_index=True, height=458)
st.markdown(legenda, unsafe_allow_html=True) # Exibe legenda

