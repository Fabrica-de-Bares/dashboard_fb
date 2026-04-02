import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_alteracao_despesas import *
from utils.functions.general_functions import *
from utils.queries_controladoria import *
from utils.components import seletor_mes, seletor_ano, input_selecao_casas

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Auditoria - Alteração de Despesas em Sistema",
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
    st.title("🔎 Auditoria - Alteração de Despesas em Sistema")
    st.write("Aba para visualizar despesas alteradas após as datas de fechamento de cada mês de DRE.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Dados - Logs despesas
df_log_despesas_inicial = GET_LOGS_DESPESAS()
df_datas_fechamento = GET_DATAS_FECHAMENTO()


col1, col2, col3 = st.columns(3)

# Seletor de casa
with col1:
    lista_retirar_casas = ['Todas as Casas', 'Bar Brahma Paulista', 'Brahminha', 'Bar Léo - Vila Madalena', 'Blue Note SP (Sala 2)', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Terraço Notie', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='seletor_casas_despesas')		
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
        df_class_cont_2 = df_class_cont_2[df_class_cont_2['DESCRICAO_1'].isin(lista_class_cont_1_selecionadas)].copy()
        lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
    lista_class_cont_2_selecionadas = st.multiselect(label='Selecione a Classificação Contábil 2', options=lista_class_cont_2, default=None)
st.divider()

if not id_casa:
    st.warning('Nenhuma casa selecionada')
    st.stop()


df_data_fechamento_mes_selecionado = df_datas_fechamento[
    (df_datas_fechamento['MES'] == mes_competencia_selecionado) & 
    (df_datas_fechamento['ANO'] == ano_competencia_selecionado) &
    (df_datas_fechamento['ID Casa'] == id_casa)
].copy()
if not df_data_fechamento_mes_selecionado.empty:
    data_fechamento_mes_selecionado = df_data_fechamento_mes_selecionado['DATA_FECHAMENTO'].iloc[0]
    st.write(f'**Data de fechamento da DRE:** {data_fechamento_mes_selecionado.date()}')
else:
    st.warning("Não existe data de fechamento para esse mês.")
    st.stop()

# Lista de dataframes para excel
dfs_exportar = {}

# Filtra pela casa selecionada
df_log_despesas_filtrado = filtragem_inicial_despesas(df_log_despesas_inicial, id_casa, data_fechamento_mes_selecionado)
df_log_despesas_filtrado = filtragem_classificacao_contabil(df_log_despesas_filtrado, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)

# Despesas criadas após data de fechamento
st.subheader('Despesas criadas após data de fechamento')
df_log_despesas_criadas = ocorrencia_despesas(df_log_despesas_inicial, id_casa, data_fechamento_mes_selecionado)
df_log_despesas_criadas = filtragem_classificacao_contabil(df_log_despesas_criadas, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas, 'Criadas')
df_log_despesas_criadas = filtragem_mes_ano_competencia(df_log_despesas_criadas, mes_competencia_selecionado, ano_competencia_selecionado, 'Criadas', data_fechamento_mes_selecionado)
df_log_despesas_criadas.rename(columns={'Data Alteração': 'Data Criação'}, inplace=True)

if not df_log_despesas_criadas.empty:
    df_log_despesas_criadas_styled = format_columns_brazilian(df_log_despesas_criadas, ['Valor Original', 'Valor Liquido'])
    st.dataframe(df_log_despesas_criadas_styled, hide_index=True, width='stretch')

exibe_contagem_despesas(df_log_despesas_criadas)
dfs_exportar["Despesas Criadas"] = df_log_despesas_criadas # adiciona para exportação
st.divider()


tipos_alteracao = [
    {
        "titulo": "Alteração em Data de Competência",
        "campo_filtro": "Data Competência",
        "colunas_comparar": ["Data Competência"],
        "titulo_excel": "Data de Competência"
    },
    {
        "titulo": "Alteração em Data de Vencimento",
        "campo_filtro": "Data Vencimento",
        "colunas_comparar": ["Data Vencimento"],
        "titulo_excel": "Data de Vencimento"
    },
    {
        "titulo": "Alteração em Valor",
        "campo_filtro": "Valor",
        "colunas_comparar": ["Valor Original", "Valor Liquido"],
        "titulo_excel": "Valor"
    },
    {
        "titulo": "Alteração em Classificação Contábil",
        "campo_filtro": "Class. Cont.",
        "colunas_comparar": ["Class. Cont. 1", "Class. Cont. 2"],
        "titulo_excel": "Classificação Contábil"
    },
    {
        "titulo": "Despesas Canceladas",
        "campo_filtro": "Canceladas",
        "colunas_comparar": ["Bit Cancelada"],
        "titulo_excel": "Despesas Canceladas"
    }
]

for tipo in tipos_alteracao:
    st.subheader(tipo["titulo"])

    df = despesas_alteradas_por_campo(df_log_despesas_filtrado, tipo["colunas_comparar"])
    df = filtragem_classificacao_contabil(df, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas, tipo["campo_filtro"])
    df = filtragem_mes_ano_competencia(df, mes_competencia_selecionado, ano_competencia_selecionado, tipo["campo_filtro"], data_fechamento_mes_selecionado)

    if not df.empty:
        df_styled = format_columns_brazilian(df, ['Valor Original', 'Valor Liquido'])
        df_styled = destacar_alteracoes(df_styled, tipo["colunas_comparar"])
        st.dataframe(df_styled, hide_index=True, width="stretch")
        exibe_legenda()

    exibe_contagem_despesas(df)
    dfs_exportar[tipo["titulo_excel"]] = df
    st.divider()


# Antes - Exemplo #
# # Exibe alterações em campos de valor
# st.subheader('Alteração em Valor')
# df_alteracao_valor = despesas_alteradas_por_campo(df_log_despesas_filtrado, ['Valor Original', 'Valor Liquido'])
# df_alteracao_valor = filtragem_classificacao_contabil(df_alteracao_valor, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas, 'Valor')
# df_alteracao_valor = filtragem_mes_ano_competencia(df_alteracao_valor, mes_competencia_selecionado, ano_competencia_selecionado, 'Valor', data_fechamento_mes_selecionado)

# # df_despesas_alteracao = df_alteracao_valor[ # Despesas alteradas para a mes/ano selecionados
# #     (df_alteracao_valor['Casa'] == casa) &
# #     (df_alteracao_valor['Data Alteração'] >= data_fechamento_mes_selecionado)
# # ].copy()
# # lista_ids_alteracao_mes_selecionado = df_despesas_alteracao['ID Despesa'].tolist()
# # df_alteracao_valor = df_alteracao_valor[df_alteracao_valor['ID Despesa'].isin(lista_ids_alteracao_mes_selecionado)]
# # df_alteracao_valor.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

# if not df_alteracao_valor.empty:
#     df_alteracao_valor_styled = format_columns_brazilian(df_alteracao_valor, ['Valor Original', 'Valor Liquido'])
#     df_alteracao_valor_styled = destacar_alteracoes(df_alteracao_valor_styled, ['Valor Original', 'Valor Liquido'])
#     st.dataframe(df_alteracao_valor_styled, hide_index=True, width='stretch')
#     exibe_legenda()

# exibe_contagem_despesas(df_alteracao_valor)
# st.divider()


# Despesas com casa alterada
st.subheader('Despesas com casa alterada')
df_despesas_alteracao_casa = despesas_alteradas_por_campo(df_log_despesas_inicial, ['Casa'])
df_despesas_alteracao_casa = filtragem_classificacao_contabil(df_despesas_alteracao_casa, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas, 'Casa')
df_despesas_alteracao_casa = filtragem_mes_ano_competencia(df_despesas_alteracao_casa, mes_competencia_selecionado, ano_competencia_selecionado, 'Casa', data_fechamento_mes_selecionado)

df_despesas_alteracao = df_despesas_alteracao_casa[ # Despesas alteradas para a mes/ano selecionados
    (df_despesas_alteracao_casa['ID Casa'] == id_casa) &
    (df_despesas_alteracao_casa['Data Alteração'] >= data_fechamento_mes_selecionado)
].copy()
lista_ids_alteracao_mes_selecionado = df_despesas_alteracao['ID Despesa'].tolist()
df_despesas_alteracao_casa = df_despesas_alteracao_casa[df_despesas_alteracao_casa['ID Despesa'].isin(lista_ids_alteracao_mes_selecionado)].copy()
df_despesas_alteracao_casa['ID Casa'] = pd.to_numeric(df_despesas_alteracao_casa['ID Casa'], errors='coerce').astype('Int64')
df_despesas_alteracao_casa.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

if not df_despesas_alteracao_casa.empty:
    df_despesas_alteracao_casa_styled = format_columns_brazilian(df_despesas_alteracao_casa, ['Valor Original', 'Valor Liquido'])
    df_despesas_alteracao_casa_styled = destacar_alteracoes(df_despesas_alteracao_casa_styled, ['Casa'])
    st.dataframe(df_despesas_alteracao_casa_styled, hide_index=True, width='stretch')
    exibe_legenda()

exibe_contagem_despesas(df_despesas_alteracao_casa)
dfs_exportar["Despesas Casa Alterada"] = df_despesas_alteracao_casa
st.divider()


# Botão para exportar Excel
col1, col2, col3 = st.columns([3, 1, 3])
with col2:
    button_download(dfs_exportar)


