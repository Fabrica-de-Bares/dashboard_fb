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

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title("🔎 Alteração de Despesas")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Dados - Logs despesas
df_log_despesas = GET_LOGS_DESPESAS()
df_teste = GET_IDS_APROVACAO_OPERACAO_ALTERADOS()
df_teste = pd.merge(
     df_teste,
     df_log_despesas,
     how='left',
     on=['ID Despesa']
)

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

# Seletores de class. cont.
col1, col2 = st.columns(2)
with col1:
    df_class_cont_1 = GET_CLASS_CONT_1()
    lista_class_cont_1 = df_class_cont_1['DESCRICAO'].tolist()
    class_cont_1_selecionada = st.multiselect(label='Selecione a Classificação Contábil 1:', options=lista_class_cont_1, default=None)
with col2:
    df_class_cont_2 = GET_CLASS_CONT_2()
    if not class_cont_1_selecionada: lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
    else: 
        df_class_cont_2 = df_class_cont_2[df_class_cont_2['DESCRICAO_1'].isin(class_cont_1_selecionada)]
        lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
    class_cont_2_selecionada = st.multiselect(label='Selecione a Classificação Contábil 2:', options=lista_class_cont_2, default=None)
st.divider()

if df_casas_selecionadas.empty:
    st.warning('Nenhuma casa selecionada')
    st.stop()


data_limite = pd.Timestamp(
	year=2026,
	month=1,
	day=20
)

# Filtra pela data de referência e ordena
df_log_despesas.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

# Contabiliza a ocorrência de cada despesa
df_log_despesas_contagem = df_log_despesas.copy()
df_contador = df_log_despesas_contagem.groupby('ID Despesa').size().reset_index(name='Contagem')
df_log_despesas_contagem = pd.merge(df_log_despesas_contagem, df_contador, how='left', on='ID Despesa') 

# Cria df com despesas alteradas depois da data limite
df_log_despesas_alteradas = df_log_despesas_contagem[df_log_despesas_contagem['Contagem'] > 1] 
df_log_despesas_alteradas = df_log_despesas_alteradas[df_log_despesas_alteradas['Data Alteração'] > data_limite]
df_log_despesas_alteradas.drop(columns=['Contagem'], inplace=True)

# Cria df com despesas criadas depois da data limite
df_log_despesas_criadas = df_log_despesas_contagem[df_log_despesas_contagem['Contagem'] == 1] 
df_log_despesas_criadas = df_log_despesas_criadas[df_log_despesas_criadas['Data Alteração'] > data_limite]
df_log_despesas_criadas.drop(columns=['Contagem'], inplace=True)

st.subheader('Despesas criadas após data determinada')
st.dataframe(df_log_despesas_criadas, hide_index=True, width='stretch')
st.divider()


# Define tipos de dados do dataframe de log de despesas alteradas
tipos_de_dados_despesas = {
    'ID Casa': int,
    'Valor Original': float,
    'Valor Liquido': float,  
}
df_log_despesas_alteradas = df_log_despesas_alteradas.astype(tipos_de_dados_despesas, errors='ignore')
df_log_despesas_alteradas['Data Competência'] = pd.to_datetime(df_log_despesas_alteradas['Data Competência'], errors='coerce')
df_log_despesas_alteradas['Data Vencimento'] = pd.to_datetime(df_log_despesas_alteradas['Data Vencimento'], errors='coerce')


# Exibe alterações em data de competência
st.subheader('Alteração em Data de Competência')
df_alteracao_data_competencia = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Data Competência'])

if not df_alteracao_data_competencia.empty:
    df_alteracao_data_styled = format_columns_brazilian(df_alteracao_data_competencia, ['Valor Original', 'Valor Liquido'])
    df_alteracao_data_styled = destacar_alteracoes(df_alteracao_data_styled, ['Data Competência'])
    st.dataframe(df_alteracao_data_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_data_competencia)
st.divider()

# Exibe alterações em data de vencimento
st.subheader('Alteração em Data de Vencimento')
df_alteracao_data_vencimento = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Data Vencimento'])

if not df_alteracao_data_vencimento.empty:
    df_alteracao_data_styled = format_columns_brazilian(df_alteracao_data_vencimento, ['Valor Original', 'Valor Liquido'])
    df_alteracao_data_styled = destacar_alteracoes(df_alteracao_data_styled, ['Data Vencimento'])
    st.dataframe(df_alteracao_data_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_data_vencimento)
st.divider()


# Exibe alterações em campos de valor
st.subheader('Alteração em Valor')
df_alteracao_valor = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Valor Original', 'Valor Liquido'])

if not df_alteracao_valor.empty:
    df_alteracao_valor_styled = format_columns_brazilian(df_alteracao_valor, ['Valor Original', 'Valor Liquido'])
    df_alteracao_valor_styled = destacar_alteracoes(df_alteracao_valor_styled, ['Valor Original', 'Valor Liquido'])
    st.dataframe(df_alteracao_valor_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_valor)
st.divider()


# Exibe alterações em campos de classificação cont.
st.subheader('Alteração em Classificação Contábil')
df_alteracao_classif = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Class. Cont. 1', 'Class. Cont. 2'])

if not df_alteracao_classif.empty:
    df_alteracao_classif_styled = format_columns_brazilian(df_alteracao_classif, ['Valor Original', 'Valor Liquido'])
    df_alteracao_classif_styled = destacar_alteracoes(df_alteracao_classif_styled, ['Class. Cont. 1', 'Class. Cont. 2'])
    st.dataframe(df_alteracao_classif_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_classif)
st.divider()


# Exibe alterações em campos de aprovação operação - stand-by
# st.subheader('Alteração em Status Aprovação Operação')
# df_teste = df_teste[df_teste['ID Casa'].isin(lista_ids_casas_selecionadas)]

# df_alteracao_aprov_operacao = despesas_alteradas_por_campo(df_teste, ['Status Aprovação Operação'])
# st.write(df_alteracao_aprov_operacao)

# if not df_alteracao_aprov_operacao.empty:
#     df_alteracao_aprov_operacao_styled = format_columns_brazilian(df_alteracao_aprov_operacao, ['Valor Original', 'Valor Liquido'])
#     df_alteracao_aprov_operacao_styled = destacar_alteracoes(df_alteracao_aprov_operacao_styled, ['Status Aprovação Operação'])
#     st.dataframe(df_alteracao_aprov_operacao_styled, hide_index=True, width='stretch')
#     exibe_legenda()
# st.divider()


# Exibe alterações em campos de provisão/real
# st.subheader('Alteração em Provisão/Real')
# df_alteracao_real_provisao = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Real/Provisão'])

# if not df_alteracao_real_provisao.empty:
#     df_alteracao_real_provisao_styled = format_columns_brazilian(df_alteracao_real_provisao, ['Valor Original', 'Valor Liquido'])
#     df_alteracao_real_provisao_styled = destacar_alteracoes(df_alteracao_real_provisao_styled, ['Real/Provisão'])
#     st.dataframe(df_alteracao_real_provisao_styled, hide_index=True, width='stretch')
#     exibe_legenda()

# exibe_contagem_ids_alterados(df_alteracao_real_provisao)


