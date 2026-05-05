import streamlit as st
import pandas as pd
import uuid
import http.client
import json
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.functions.api_zigpay import login_zigpay, request_getEvents_zigpay, request_getProductsSoldAtEventInPeriodV2_zigpay
from utils.queries_controladoria import GET_FATURAMENTO_ZIGPAY_VALIDACAO, GET_ITENS_SEM_CADASTRO, GET_ITENS_COM_CADASTRO_DUPLICADO

st.set_page_config(
	page_icon="✅",
	page_title="Validação de Faturamento Zigpay",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')


def main():
    config_sidebar()

    # Header
    col1, col2 = st.columns([5, 1], vertical_alignment='center')
    with col1:
        st.title("✅ Validação de Faturamento Zigpay")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    st.divider()

    # Seletores
    col_casa, col_datas = st.columns([1, 1])
    with col_casa:
        lista_retirar_casas = ['Priceless', 'Bar Léo - Vila Madalena', 'Todas as Casas', 'Escritório Fabrica de Bares', 'Casa Teste 2', 'Brahminha', 'Bar Brahma Paulista', 'Blue Note SP (Sala 2)', 'Tempus Fugit  Ltda ', 'Sanduiche comunicação LTDA ', 'Edificio Rolim']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, 'selecao_casa', adicionar_delivery=True)
    with col_datas:
        col1, col2 = st.columns([1, 1])
        with col1:
            mes_nome, mes_numero = seletor_mes_produtos('seletor_mes')
        with col2:
            ano = seletor_ano(2025, 2026, 'ano', 'Ano')

    st.divider()

    # ZIGPAY #
    # Realiza login na Zigpay
    login_zigpay()

    # Obtém Serviço Zigpay da casa agregada
    df_eventos_zigpay = request_getEvents_zigpay(id_zigpay, mes_numero, ano)

    # Tratamento de dados
    df_eventos_zigpay['Casa'] = casa
    df_eventos_zigpay['begin'] = pd.to_datetime(df_eventos_zigpay['begin']).dt.date
    df_eventos_zigpay.sort_values(by='begin', inplace=True)
    df_eventos_zigpay.drop(columns=['end', 'name', 'openedBy', 'openedAt', 'checkedAt', 'checkedBy', 'sales', 'tags', 'image', 'hasOpenedTables', 'lastSyncAfterClosed', 'closingConferenceStatus'], inplace=True)
    df_eventos_zigpay.dropna(subset=['income', 'totalPublic', 'averageTicket'], inplace=True)

    # Renomeia colunas
    df_eventos_zigpay.rename(columns={
        'begin': 'Data Evento',
        'income': 'Faturamento',
    }, inplace=True)

    # Requisição para getProductsSoldAtEventInPeriodV2: obtem da API os produtos vendidos de cada evento
    df_produtos_eventos_zig = pd.DataFrame()
    for evento in df_eventos_zigpay['id'].unique().tolist():
        df_produtos_evento_zig = request_getProductsSoldAtEventInPeriodV2_zigpay(
            evento, 
            place_id=None,
            since=None,
            until=None,
            sources=None
        )
        df_produtos_eventos_zig = pd.concat([df_produtos_eventos_zig, df_produtos_evento_zig])
    
    # Agrupa faturamento por evento zig
    df_produtos_eventos_zig = df_produtos_eventos_zig.groupby(['evento']).agg({
        'valor_total': 'sum',
        'valor_liquido': 'sum',
        'desconto': 'sum'
    }).reset_index()
    
    # Merge faturamentos bruto e liquido dos eventos com os eventos do mês
    df_eventos_zigpay = df_eventos_zigpay.merge(df_produtos_eventos_zig, how='left', left_on='id', right_on='evento')

    # Agrupa por dia de evento se houver mais de um evento no mesmo dia
    df_eventos_zigpay = df_eventos_zigpay.groupby(['Data Evento']).agg({
        'Data Evento': 'first',
        'totalPublic': 'sum',        
        'valor_total': 'sum',
        'valor_liquido': 'sum',
        'desconto': 'sum'
    })

    # Faturamento T_ITENS_VENDIDOS  
    df_itens_vendidos = GET_FATURAMENTO_ZIGPAY_VALIDACAO(id_zigpay, mes_numero, ano)

    # Renomeia colunas
    df_itens_vendidos.rename(columns={
        'Soma_Valor_Transacao_Bruto': 'Faturamento Itens Bruto',
        'Soma_Desconto': 'Desconto',
        'Soma_Valor_Transacao_Liquido': 'Faturamento Itens Líquido',
    }, inplace=True)

    # Se a casa selecionada for o Arcos, remove as linhas de faturamento de Couvert
    if id_casa == 122:
        df_itens_vendidos.drop(df_itens_vendidos[df_itens_vendidos['Categoria'] == 'Couvert'].index, inplace=True)

    # Agrupa por dia se houver mais de um evento no mesmo dia
    df_itens_vendidos = df_itens_vendidos.groupby(['Data Evento']).agg({
        'Faturamento Itens Bruto': 'sum',
        'Faturamento Itens Líquido': 'sum',
        'Desconto': 'sum'
    }).reset_index()

    # Merge final: Zigpay e T_ITENS_VENDIDOS
    df_merged_zig_bd = (
        df_eventos_zigpay.reset_index(drop=True)
        .merge(df_itens_vendidos.reset_index(drop=True), on='Data Evento', how='left')
    )
    
    # Padroniza tipos de dados
    df_merged_zig_bd['Faturamento Itens Bruto'] = df_merged_zig_bd['Faturamento Itens Bruto'].astype(float).round(2)
    df_merged_zig_bd['valor_total'] = df_merged_zig_bd['valor_total'].astype(float).round(2)
    df_merged_zig_bd['Faturamento Itens Líquido'] = df_merged_zig_bd['Faturamento Itens Líquido'].astype(float).round(2)
    df_merged_zig_bd['valor_liquido'] = df_merged_zig_bd['valor_liquido'].astype(float).round(2)
    df_merged_zig_bd['Desconto'] = df_merged_zig_bd['Desconto'].astype(float).round(2)
    df_merged_zig_bd['desconto'] = df_merged_zig_bd['desconto'].astype(float).round(2)

    df_merged_zig_bd['Validação'] = df_merged_zig_bd['Faturamento Itens Líquido'] == df_merged_zig_bd['valor_liquido']

    df_merged_zig_bd.rename(columns={
        "valor_total": "Faturamento Bruto Zigpay",
        "desconto": "Desconto Zigpay",
        "valor_liquido": "Faturamento Líquido Zigpay",
        "Faturamento Itens Bruto": "Faturamento Bruto T_ITENS_VENDIDOS",
        "Desconto": "Desconto T_ITENS_VENDIDOS",
        "Faturamento Itens Líquido": "Faturamento Líquido T_ITENS_VENDIDOS"
    }, inplace=True)
    df_merged_zig_bd.drop(columns=['totalPublic'], inplace=True)

    # Formatação
    df_merged_zig_bd.dropna(inplace=True)
    df_merged_zig_bd = format_columns_brazilian(df_merged_zig_bd, ['Faturamento Bruto Zigpay', 'Faturamento Líquido Zigpay', 'Faturamento Bruto T_ITENS_VENDIDOS', 'Faturamento Líquido T_ITENS_VENDIDOS', 'Desconto Zigpay', 'Desconto T_ITENS_VENDIDOS'])
    
    st.markdown('## Faturamento Zigpay e T_ITENS_VENDIDOS')
    st.dataframe(df_merged_zig_bd, width='stretch', hide_index=True)

    df_itens_sem_cadastro = GET_ITENS_SEM_CADASTRO()
    df_itens_sem_cadastro = df_itens_sem_cadastro[df_itens_sem_cadastro['ID Zigpay'] == id_zigpay]
    st.markdown('## Itens sem cadastro')
    st.dataframe(df_itens_sem_cadastro, width='stretch', hide_index=True)

    df_itens_cadastro_duplicado = GET_ITENS_COM_CADASTRO_DUPLICADO()
    st.markdown('## Itens com cadastro duplicado')
    st.dataframe(df_itens_cadastro_duplicado)

    # Cards
    col1, col2, col3 = st.columns([1, 1, 1])
    

if __name__ == "__main__":
    main()

    