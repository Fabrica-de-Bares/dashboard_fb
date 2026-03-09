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
    st.write("Aba para visualizar despesas alteradas após as datas de fechamento de cada mês de DRE.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Dados - Logs despesas
df_log_despesas = GET_LOGS_DESPESAS()
df_datas_fechamento = GET_DATAS_FECHAMENTO()
st.write(df_datas_fechamento)

col1, col2, col3 = st.columns(3)

# Seletor de casa
with col1:
    lista_retirar_casas = ['Todas as Casas', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Terraço Notie', 'The Cavern - Almoço', 'Blue Note SP (Sala 2)']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='seletor_casas_despesas')		
    lista_ids_casas_selecionadas = df_casas_selecionadas['ID_Casa'].tolist()
with col2:
    mes_competencia_selecionado = int(seletor_mes("Selecione o mês da DRE", key="seletor_mes_despesas"))
with col3:
    ano_competencia_selecionado = seletor_ano(2025, 2026, 'ano', 'Selecione o ano da DRE')
st.divider()

# Seletores de class. cont.
col1, col2 = st.columns(2)
with col1:
    df_class_cont_1 = GET_CLASS_CONT_1()
    lista_class_cont_1 = df_class_cont_1['DESCRICAO'].tolist()
    lista_class_cont_1_selecionadas = st.multiselect(label='Selecione a Classificação Contábil 1', options=lista_class_cont_1, default=None)
with col2:
    df_class_cont_2 = GET_CLASS_CONT_2()
    if not lista_class_cont_1_selecionadas: lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
    else: 
        df_class_cont_2 = df_class_cont_2[df_class_cont_2['DESCRICAO_1'].isin(lista_class_cont_1_selecionadas)]
        lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
    lista_class_cont_2_selecionadas = st.multiselect(label='Selecione a Classificação Contábil 2', options=lista_class_cont_2, default=None)
st.divider()

if df_casas_selecionadas.empty:
    st.warning('Nenhuma casa selecionada')
    st.stop()


df_data_fechamento_mes_selecionado = df_datas_fechamento[(df_datas_fechamento['MES'] == mes_competencia_selecionado) & (df_datas_fechamento['ANO'] == ano_competencia_selecionado)]
if not df_data_fechamento_mes_selecionado.empty:
    data_fechamento_mes_selecionado = df_data_fechamento_mes_selecionado['DATA_FECHAMENTO'].iloc[0]
    st.write(f'**Data de fechamento:** {data_fechamento_mes_selecionado.date()}')
else:
    st.write("Não existe data de fechamento para esse mês.")

# Filtra pela casa selecionada e data > data de fechamento
df_log_despesas_filtrado = filtragem_inicial_despesas(df_log_despesas, lista_ids_casas_selecionadas, data_fechamento_mes_selecionado)

# Contabiliza a ocorrência de cada despesa
df_log_despesas_alteradas, df_log_despesas_criadas = ocorrencia_despesas(df_log_despesas_filtrado)

# Despesas criadas após data de fechamento
st.subheader('Despesas criadas após data de fechamento')
df_log_despesas_criadas = filtragem_classificacao_contabil(df_log_despesas_criadas, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
df_log_despesas_criadas = filtragem_mes_ano_competencia(df_log_despesas_criadas, mes_competencia_selecionado, ano_competencia_selecionado)
# Delimitar colunas exibidas #
st.dataframe(df_log_despesas_criadas, hide_index=True, width='stretch')
st.divider()


# Exibe alterações em data de competência
st.subheader('Alteração em Data de Competência')
df_alteracao_data_competencia = filtragem_classificacao_contabil(df_log_despesas_filtrado, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
df_alteracao_data_competencia = despesas_alteradas_por_campo(df_alteracao_data_competencia, ['Data Competência'])

if not df_alteracao_data_competencia.empty:
    df_alteracao_data_styled = format_columns_brazilian(df_alteracao_data_competencia, ['Valor Original', 'Valor Liquido'])
    df_alteracao_data_styled = destacar_alteracoes(df_alteracao_data_styled, ['Data Competência'])
    st.dataframe(df_alteracao_data_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_data_competencia)
st.divider()

# Exibe alterações em data de vencimento
st.subheader('Alteração em Data de Vencimento')
df_alteracao_data_vencimento = filtragem_classificacao_contabil(df_log_despesas_filtrado, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
df_alteracao_data_vencimento = despesas_alteradas_por_campo(df_alteracao_data_vencimento, ['Data Vencimento'])

if not df_alteracao_data_vencimento.empty:
    df_alteracao_data_styled = format_columns_brazilian(df_alteracao_data_vencimento, ['Valor Original', 'Valor Liquido'])
    df_alteracao_data_styled = destacar_alteracoes(df_alteracao_data_styled, ['Data Vencimento'])
    st.dataframe(df_alteracao_data_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_data_vencimento)
st.divider()


# Exibe alterações em campos de valor
st.subheader('Alteração em Valor')
df_alteracao_valor = filtragem_classificacao_contabil(df_log_despesas_filtrado, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
df_alteracao_valor = despesas_alteradas_por_campo(df_alteracao_valor, ['Valor Original', 'Valor Liquido'])

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

if lista_class_cont_1_selecionadas or lista_class_cont_2_selecionadas:
    df_alteracao_classif_selecionada = df_alteracao_classif[ # Despesas alteradas para a class. cont. selecionada
        (df_alteracao_classif['Class. Cont. 1'].isin(lista_class_cont_1_selecionadas)) |
        (df_alteracao_classif['Class. Cont. 2'].isin(lista_class_cont_2_selecionadas))
    ].copy()
    lista_ids_alteracao_classif_selecionada = df_alteracao_classif_selecionada['ID Despesa'].tolist()

    df_alteracao_classif_filtrado = df_alteracao_classif[df_alteracao_classif['ID Despesa'].isin(lista_ids_alteracao_classif_selecionada)]
else:
    df_alteracao_classif_filtrado = df_alteracao_classif

if not df_alteracao_classif_filtrado.empty:
    df_alteracao_classif_styled = format_columns_brazilian(df_alteracao_classif_filtrado, ['Valor Original', 'Valor Liquido'])
    df_alteracao_classif_styled = destacar_alteracoes(df_alteracao_classif_styled, ['Class. Cont. 1', 'Class. Cont. 2'])
    st.dataframe(df_alteracao_classif_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_alteracao_classif_filtrado)
st.divider()


# Despesas canceladas após data
st.subheader('Despesas Canceladas após data de fechamento')
df_despesas_canceladas = filtragem_classificacao_contabil(df_log_despesas_filtrado, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
df_despesas_canceladas = despesas_alteradas_por_campo(df_despesas_canceladas, ['Bit Cancelada'])

if not df_despesas_canceladas.empty:
    df_despesas_canceladas_styled = format_columns_brazilian(df_despesas_canceladas, ['Valor Original', 'Valor Liquido'])
    df_despesas_canceladas_styled = destacar_alteracoes(df_despesas_canceladas_styled, ['Bit Cancelada'])
    st.dataframe(df_despesas_canceladas_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_ids_alterados(df_despesas_canceladas)
st.divider()


# Exibe alterações em campos de provisão/real
# st.subheader('Alteração em Provisão/Real')
# df_alteracao_real_provisao = despesas_alteradas_por_campo(df_log_despesas_alteradas, ['Real/Provisão'])

# if not df_alteracao_real_provisao.empty:
#     df_alteracao_real_provisao_styled = format_columns_brazilian(df_alteracao_real_provisao, ['Valor Original', 'Valor Liquido'])
#     df_alteracao_real_provisao_styled = destacar_alteracoes(df_alteracao_real_provisao_styled, ['Real/Provisão'])
#     st.dataframe(df_alteracao_real_provisao_styled, hide_index=True, width='stretch')
#     exibe_legenda()

# exibe_contagem_ids_alterados(df_alteracao_real_provisao)


