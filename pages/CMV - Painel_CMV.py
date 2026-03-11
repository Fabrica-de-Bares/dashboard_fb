import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico import *
from utils.functions.cmv import *
from utils.functions.cmv_painel import *
from utils.queries_cmv import *
from datetime import timedelta
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed


st.set_page_config(
    page_icon="📊",
    page_title="Painel de CMV",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

# Constantes
CASAS_EXCLUIDAS = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas', 'Escritório Fabrica de Bares']


def main():
    # Sidebar
    config_sidebar()

    # Header
    col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment="center")
    with col1:
        st.title("📊 Painel de CMV")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    st.divider()
 
    col1, col2 = st.columns([1, 1])
    with col1:
        id_casa, casa, id_zigpay = input_selecao_casas(CASAS_EXCLUIDAS, 'selecao_casa')
    with col2:
        ano = seletor_ano(2024, int(get_last_year(today=datetime.datetime.now()) + 2), 'ano', label='Selecione o ano')
    st.divider()
    
    ### Dados
    with ThreadPoolExecutor() as executor:
        futures = {
            'GET_CMV_ORCADO_AB': executor.submit(GET_CMV_ORCADO_AB),
            'GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE': executor.submit(GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE),
            'GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO': executor.submit(GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO),
            'GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE': executor.submit(GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE),
            'GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO': executor.submit(GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO),
            'GET_FATURAMENTO_ITENS_VENDIDOS_DIA': executor.submit(GET_FATURAMENTO_ITENS_VENDIDOS_DIA)
        }

    # Espera todas terminarem
    concurrent.futures.wait(futures.values())
    
    # Dataframes com dados
    df_cmv_orcado = futures['GET_CMV_ORCADO_AB'].result()
    # dataframe com as quantidades de insumos de estoque para cada ITEM VENDIDO
    df_fichas_itens_vendidos_insumos_estoque = futures['GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE'].result()
    # dataframe com as quantidades de insumos de produção para cada ITEM VENDIDO
    df_fichas_itens_vendidos_itens_producao = futures['GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO'].result()
    df_precos_insumos = futures['GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE'].result()
    # dataframe com as quantidades de insumos de estoque e de produção para cada ITEM DE PRODUÇÃO
    df_fichas_itens_producao = futures['GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO'].result()
    # Tabela de faturamento
    df_itens_vendidos_dia = futures['GET_FATURAMENTO_ITENS_VENDIDOS_DIA'].result()

    df_cmv_orcado = df_cmv_orcado[df_cmv_orcado['Casa'] == casa]
    df_cmv_orcado = df_cmv_orcado[df_cmv_orcado['Ano'] == ano]
    
    # dataframe com as quantidades de insumos de produção e de estoque para cada VENDIDO
    df_fichas_itens_vendidos = pd.merge(df_fichas_itens_vendidos_insumos_estoque, df_fichas_itens_vendidos_itens_producao, how='outer')

    df_precos_insumos_de_estoque = df_precos_insumos.groupby(['ID Casa', 'ID Insumo Estoque', 'Mês Compra', 'Ano Compra']).agg({
        'Valor N5': 'sum',
        'Quantidade Insumo Estoque': 'sum',
        'Casa': 'first',
        'Insumo Estoque': 'first',
        'U.M. Insumo Estoque': 'first'
    }).reset_index()
    col_ordem = [
        'ID Casa', 'Casa', 'Mês Compra', 'Ano Compra',
        'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque',
        'Valor N5', 'Quantidade Insumo Estoque'
    ]
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[col_ordem]
    # Calcula o preço da unidade (preço de 1 unidade de medida) do insumo de estoque
    df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] = df_precos_insumos_de_estoque['Valor N5'] / df_precos_insumos_de_estoque['Quantidade Insumo Estoque']

    # Remover NaN
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque.dropna(subset=['Preço Médio Insumo Estoque'])
    # Remover inf e -inf
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        ~np.isinf(df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'])
    ]
    # Remover valores negativos
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] > 0
    ]

    # Formatação de dados
    df_itens_vendidos_dia['Data Venda'] = pd.to_datetime(df_itens_vendidos_dia['Data Venda'], errors='coerce')

    # Obtem os insumos de estoque para cada casa para calcular o preço posteriormente
    insumos_necessarios_estoque_casa = df_fichas_itens_vendidos_insumos_estoque.loc[
        df_fichas_itens_vendidos_insumos_estoque['ID Casa'] == id_casa,
        ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
    ].drop_duplicates()

    df_fichas_itens_vendidos = df_fichas_itens_vendidos[df_fichas_itens_vendidos['ID Casa'] == id_casa]

    # Mês atual
    mes_atual = datetime.datetime.now().month

    # CMV Téorico
    df_cmv_teorico = calcular_cmv_teorico_ano(ano, mes_atual, id_casa, df_fichas_itens_vendidos, df_fichas_itens_producao, df_precos_insumos_de_estoque, df_itens_vendidos_dia, insumos_necessarios_estoque_casa)

    # CMV Real
    df_cmv_real = calcula_cmv_real_ano_paralelo(ano, mes_atual, casa)

    grafico_cmv_teorico(df_cmv_teorico)
    st.divider()

    grafico_cmv_real(df_cmv_real)
    st.divider()

    grafico_cmv_orcado(df_cmv_orcado)
    st.divider()
    
        
if __name__ == '__main__':
    main()