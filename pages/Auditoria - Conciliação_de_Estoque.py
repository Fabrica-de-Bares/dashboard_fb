import streamlit as st
import pandas as pd
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.functions.cmv_teorico import *
from utils.queries_estoque import *
from utils.functions.estoque import login_zigpay, id_casa_para_ids_zigpay, request_getProductsSoldAtEventInPeriodV2_zigpay, request_getEvents_zigpay

st.set_page_config(
    page_icon="📋",
    page_title="Auditoria - Conciliação de Estoque",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')


def main():
    #Sidebar
    config_sidebar()

    #Header
    col1, col2 = st.columns([6,2], vertical_alignment="center")
    with col1:
        st.title("📋 Auditoria - Conciliação de Estoque")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear, icon='🔄', width='stretch')
        
    #Seletores
    col_casa, col_dia  = st.columns([1, 1])
    with col_casa:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas', 'Priceless', 'Escritório Fabrica de Bares']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, 'selecao_casa', adicionar_delivery=True)
        lista_ids_zigpay = id_casa_para_ids_zigpay(id_casa, id_zigpay)
    with col_dia:
        data = st.date_input("Selecione o dia")
        dia =data.day
        mes_numero = data.month
        ano = data.year
    

    st.divider()

    #ZIGPAY #
    #Realiza login na Zigpay
    login_zigpay()

    # Obtem Serviço Zigpay da casa agregada
    df_eventos_zigpay = pd.DataFrame()
    for id_place in lista_ids_zigpay:
        df_eventos_place = request_getEvents_zigpay(id_place, mes_numero, ano)
        df_eventos_zigpay = pd.concat([df_eventos_zigpay, df_eventos_place])
    
    print(df_eventos_zigpay.columns)
    print(df_eventos_zigpay[['begin','end']].head(2))


    # Tratamento de dados
    df_eventos_zigpay['CASA'] = casa
    df_eventos_zigpay['begin'] = pd.to_datetime(df_eventos_zigpay['begin']).dt.date
    df_eventos_zigpay.sort_values(by='begin', inplace=True)
    df_eventos_zigpay.drop(columns=['end', 'name', 'openedBy', 'openedAt', 'checkedAt', 'checkedBy', 'sales', 'tags', 'image', 'hasOpenedTables', 'lastSyncAfterClosed', 'closingConferenceStatus'], inplace=True)
    df_eventos_zigpay.dropna(subset=['income', 'totalPublic', 'averageTicket'], inplace=True)

    # Renomeia colunas
    df_eventos_zigpay.rename(columns={
      'begin': 'DATA VENDA',
    }, inplace=True)


    # Pegar DataFrame e extrair a data corretamente
    data_contagem = GET_ULTIMA_DATA_CONTAGEM(data, id_casa)

    data_escolhida = pd.to_datetime(data)
    data_anterior = data_escolhida - pd.Timedelta(days=1)
    data_inicio_str = data_anterior.strftime('%Y-%m-%dT00:00:00')
    data_fim_str = data_escolhida.strftime('%Y-%m-%dT23:59:59')
    
    
    print(f"dia_inicio={data_inicio_str}, dia_fim={data_fim_str}")

    # Requisição para getProductsSoldAtEventInPeriodV2: obtem da API os produtos vendidos de cada evento
    df_produtos_eventos_zig = pd.DataFrame()
    for evento in df_eventos_zigpay['id'].unique().tolist():
        df_produtos_evento_zig = request_getProductsSoldAtEventInPeriodV2_zigpay(
            evento,
            place_id=None,
            since=data_inicio_str,
            until=data_fim_str,
            sources=None
        )
        df_produtos_eventos_zig = pd.concat([df_produtos_eventos_zig, df_produtos_evento_zig])
        
    
    # df_produtos_eventos_zig.drop(columns=['evento'])

    st.markdown("### Produtos vendidos por evento - Zigpay")
    st.dataframe(df_produtos_eventos_zig, width='stretch', hide_index=True)
    st.markdown("### Eventos Zigpay")
    st.dataframe(df_eventos_zigpay, width='stretch', hide_index=True)



    df_eventos_zigpay = df_eventos_zigpay.merge(df_produtos_eventos_zig, how='inner', left_on='id', right_on='evento')

    # df_eventos_zigpay = df_eventos_zigpay.groupby(['DATA EVENTO']).agg({
    #     'DATA EVENTO': 'first',
    # })  

    st.markdown("### Eventos e Produtos Vendidos - Zigpay")
    st.dataframe(df_eventos_zigpay, width='stretch', hide_index=True)  
    # Faturamento T_ITENS_VENDIDOS
    df_itens_vendidos = GET_QUANTIDADE_ITENS_VENDIDOS_COMPLETO(lista_ids_zigpay, data_contagem, data, id_casa)
    
    

  
    df_eventos_zigpay.rename(columns={'id_produto': 'PRODUCT ID', 'categoria': 'CATEGORIA', 'quantidade': 'QUANTIDADE'}, inplace=True)
        

    st.markdown("### Itens Vendidos - Banco de Dados")
    st.dataframe(df_itens_vendidos, width='stretch', hide_index=True)
    # Merge final: Zigpay e T_ITENS_VENDIDOS
    df_merged_zig_bd = (
        df_eventos_zigpay.reset_index(drop=True)
        .merge(df_itens_vendidos.reset_index(drop=True), on=['DATA VENDA'], how='left')
    )

    df_merged_zig_bd.drop(columns=['income','unfinishedPdvs',
       'totalPublic', 'averageTicket', 'tipo_produto', 'categoria_mestre',
       'evento'], inplace=True)
    
    #Ainda nao sei se sera usado
    #Dataframe com as quantidades de insumos de estoque para cada ITEM VENDIDO
    

    # st.dataframe(df_merged_zig_bd, width='stretch', hide_index=True)

    ultima_data_validada = GET_DATA_VALIDACAO(data)

    #COMPRAS
    df_itens_comprados = GET_INSUMOS_BLUE_ME_COM_PEDIDO(data, ultima_data_validada, id_casa)
    
    # st.dataframe(df_itens_comprados, width='stretch', hide_index=True)
    

    # df_itens_diferenca_compra_venda = pd.merge(df_merged_zig_bd, df_itens_comprados, on=['PRODUCT ID'], how='outer', suffixes=('_VENDA', '_COMPRA'))
    # print(df_itens_diferenca_compra_venda.columns)

    # st.dataframe(df_itens_diferenca_compra_venda, width='stretch', hide_index=True)
 
    # Cards
    col1, col2 = st.columns([1, 1])

if __name__ == '__main__':
    main() 