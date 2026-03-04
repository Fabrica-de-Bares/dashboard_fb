import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_alteracao_despesas import *
from utils.functions.general_functions import *
from utils.queries_controladoria import *
from utils.components import button_download, seletor_mes, seletor_ano, input_multiselecao_casas

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Alteração de Despesas",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("🔎 Alteração de Despesas")
st.divider()

df_log_despesas = GET_LOGS_DESPESAS()

col1, col2, col3 = st.columns(3)

# Seletor de casa
with col1:
    lista_retirar_casas = ['Todas as Casas', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Terraço Notie', 'The Cavern - Almoço', 'Blue Note SP (Sala 2)']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='seletor_casas_despesas')		
    lista_ids_casas_selecionadas = df_casas_selecionadas['ID_Casa'].tolist()
    df_log_despesas = df_log_despesas[df_log_despesas['ID Casa'].isin(lista_ids_casas_selecionadas)]

with col2:
    mes = seletor_mes("Selecione o mês:", key="seletor_mes_despesas")
    
with col3:
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano:')
st.divider()


data_limite = pd.Timestamp(
	year=2026,
	month=1,
	day=20
)

# Filtra pela data de referência e ordena
df_log_despesas = df_log_despesas[df_log_despesas['Data Alteração'] > data_limite]
df_log_despesas.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

# Remove logs em que não houve alteração (apenas despesa criada)
df_log_despesas_filtrado = df_log_despesas.copy()
df_contador = df_log_despesas_filtrado.groupby('ID Despesa').size().reset_index(name='Contagem')
df_log_despesas_filtrado = pd.merge(df_log_despesas_filtrado, df_contador, how='left', on='ID Despesa')
df_log_despesas_filtrado = df_log_despesas_filtrado[df_log_despesas_filtrado['Contagem'] > 1] 
df_log_despesas_filtrado.drop(columns=['Contagem'], inplace=True)

# Define tipos de dados do dataframe de log de despesas
tipos_de_dados_despesas = {
    'ID Casa': int,
    'Valor Original': float,
    'Valor Liquido': float,  
}
df_log_despesas_filtrado = df_log_despesas_filtrado.astype(tipos_de_dados_despesas, errors='ignore')
df_log_despesas_filtrado['Data Competência'] = pd.to_datetime(df_log_despesas_filtrado['Data Competência'], errors='coerce')
df_log_despesas_filtrado['Data Vencimento'] = pd.to_datetime(df_log_despesas_filtrado['Data Vencimento'], errors='coerce')


# Exibe alterações em campos de data
st.subheader('Alteração em Data de Competência ou Vencimento')
df_alteracao_data = despesas_alteradas_por_campo(df_log_despesas_filtrado, ['Data Vencimento', 'Data Competência'])

if not df_alteracao_data.empty:
    df_alteracao_data_styled = format_columns_brazilian(df_alteracao_data, ['Valor Original', 'Valor Liquido'])
    df_alteracao_data_styled = destacar_alteracoes(df_alteracao_data_styled, ['Data Vencimento', 'Data Competência'])
    st.dataframe(df_alteracao_data_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_data)
st.divider()

# Exibe alterações em campos de valor
st.subheader('Alteração em Valor')
df_alteracao_valor = despesas_alteradas_por_campo(df_log_despesas_filtrado, ['Valor Original', 'Valor Liquido'])

if not df_alteracao_valor.empty:
    df_alteracao_valor_styled = format_columns_brazilian(df_alteracao_valor, ['Valor Original', 'Valor Liquido'])
    df_alteracao_valor_styled = destacar_alteracoes(df_alteracao_valor_styled, ['Valor Original', 'Valor Liquido'])
    st.dataframe(df_alteracao_valor_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_valor)
st.divider()

# Exibe alterações em campos de classificação cont.
st.subheader('Alteração em Classificação Contábil')
df_alteracao_classif = despesas_alteradas_por_campo(df_log_despesas_filtrado, ['Class. Cont. 1', 'Class. Cont. 2'])

if not df_alteracao_classif.empty:
    df_alteracao_classif_styled = format_columns_brazilian(df_alteracao_classif, ['Valor Original', 'Valor Liquido'])
    df_alteracao_classif_styled = destacar_alteracoes(df_alteracao_classif_styled, ['Class. Cont. 1', 'Class. Cont. 2'])
    st.dataframe(df_alteracao_classif_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_classif)
st.divider()