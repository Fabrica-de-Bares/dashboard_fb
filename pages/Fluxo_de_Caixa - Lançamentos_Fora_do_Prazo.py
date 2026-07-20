import streamlit as st
from utils.functions.general_functions import *
from utils.components import *
from utils.queries_fluxo_de_caixa import GET_DESPESAS_FORA_PRAZO

st.set_page_config(
    page_title="Lançamentos Fora do Prazo",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

config_sidebar()

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment='center')
with col1:
    st.title("⚠️ Lançamentos Fora do Prazo")
with col3:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
st.divider()

data_inicio_default, data_fim_default = get_first_and_last_day_of_month()

# Seletores
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    # Filtro de casa:
    lista_retirar_casas = ['Bar Léo - Vila Madalena']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='calendario', adicionar_delivery=True)
    lojas_selecionadas = df_casas_selecionadas['Casa'].tolist()
with col2:
    data_inicio = st.date_input(
        'Data de Início (Vencimento)',
        value=data_inicio_default,
        key='data_inicio_input',
        format="DD/MM/YYYY"
    )
with col3:
    data_fim = st.date_input(
        'Data de Fim (Vencimento)',
        value=data_fim_default,
        key='data_fim_input',
        format="DD/MM/YYYY"
    )

    # Converte as datas selecionadas para o formato Timestamp
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

st.divider()

if lojas_selecionadas == []:
    st.warning("Nenhuma casa selecionada.")
    st.stop()

st.warning("Despesas devem ser lançadas antes do prazo de 15 dias do vencimento.")
df_despesas_fora_prazo = GET_DESPESAS_FORA_PRAZO()
df_despesas_fora_prazo = df_despesas_fora_prazo[df_despesas_fora_prazo['Casa'].isin(lojas_selecionadas)]
df_despesas_fora_prazo['Data Lançamento'] = pd.to_datetime(df_despesas_fora_prazo['Data Lançamento'], errors='coerce')

df_despesas_fora_prazo = df_despesas_fora_prazo[(df_despesas_fora_prazo['Data Lançamento'] >= data_inicio) & (df_despesas_fora_prazo['Data Lançamento'] <= data_fim)]
num_despesas_fora_prazo = len(df_despesas_fora_prazo)
media_prazo = df_despesas_fora_prazo['Dias de Antecedência'].mean()

col0, col1, col2, col4 = st.columns(4)
with col1:
    st.metric(label='Nro. Despesas Fora do Prazo', value=num_despesas_fora_prazo, border=True)
with col2:
    st.metric(label='Antecedência média das despesas', value=f'{media_prazo:.1f} dias' if pd.notna(media_prazo) else '—', border=True)

df_despesas_fora_prazo = df_format_date_columns_brazilian(df_despesas_fora_prazo, ['Data Competência', 'Data Lançamento', 'Data Vencimento'])

col1, col2 = st.columns([4, 1], vertical_alignment='center')
with col2:
    button_download(df_despesas_fora_prazo, 'despesas_fora_prazo', 'despesas_fora_prazo')
df_despesas_fora_prazo_styled = df_despesas_fora_prazo.style.map(lambda x: 'font-weight: bold', subset=['Dias de Antecedência'])
st.dataframe(df_despesas_fora_prazo_styled, hide_index=True, height=35 * 15 + 38)





