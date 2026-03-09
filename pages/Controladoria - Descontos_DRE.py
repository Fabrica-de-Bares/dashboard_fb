import streamlit as st
import pandas as pd
import numpy as np
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria import *
from utils.queries_descontos_dre import *
from utils.components import button_download, seletor_ano, seletor_mes

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Descontos - DRE",
    page_icon=":material/percent_discount:",
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
    st.title(":material/percent_discount: Descontos - DRE")
    st.write("Aba que replica a aba de 'Descontos' da planilha de DRE para inserção automática no EPM.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Recupera dados
df_casas = GET_CASAS_SIMPLES()
df_descontos = GET_DESCONTOS()
df_promocoes = GET_PROMOCOES()

# Define variáveis importantes
id_casa = None
nome_casa = None
CMV = 0.29 # Valor estimado
DEDUCAO_FAT_ALIM = 0.43
DEDUCAO_FAT_BEB = 0.57

# Seletor de casa e ano
col1, col2, col3 = st.columns(3)

with col1:
    # casas = df_casas['Casa'].tolist()
    casas = ['Todas as casas', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'BNSP', 'Edificio Rolim', 'Girondino', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Riviera Bar', 'Terraço Notiê', 'The Cavern']
    casa = st.selectbox("Selecione uma casa:", casas)
    if casa == 'Todas as casas':
        nome_casa = None
        id_casa = None
    else:
        if casa == 'BNSP':
            nome_casa = 'Blue Note SP (Novo)'
        elif casa == 'Terraço Notiê':
            nome_casa = 'Terraço Notie'
        else:
            nome_casa = casa

        # Recupera id da casa
        mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
        id_casa = mapeamento_casas[nome_casa]

with col2:
    mes = seletor_mes("Selecione o mês:", key="seletor_mes_descontos_dre")
    
with col3:
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano:')

st.divider()

# Filtra pelo mês, ano e casa selecionados
df_descontos_filtrado, df_promocoes_filtrado = filtra_df(df_descontos, df_promocoes, mes, ano, id_casa)

# Concatena descontos e promoções 
df_descontos_mes, df_promocoes_mes, df_concatenado = prepara_consolidado(df_descontos_filtrado, df_promocoes_filtrado)

df_categorias_mes = df_concatenado.copy()
df_categorias_mes['CMV'] = CMV # Cria coluna com valor de CMV

# Calcula 'Aloca no Centro de Custo' par todas as categorias (menos EVENTOS)
df_categorias_mes['DESCONTO'] = df_categorias_mes['DESCONTO'].astype(float)
df_categorias_mes['CMV'] = df_categorias_mes['CMV'].astype(float)

condicao = ~df_categorias_mes['CATEGORIA'].isin(['EVENTO', 'EVENTOS'])
df_categorias_mes.loc[condicao, 'Aloca no Centro de Custo'] = df_categorias_mes['DESCONTO'] * df_categorias_mes['CMV']


if not df_categorias_mes.empty:
    # Mapeamento - Centro de Custo
    df_categorias_mes_centro_custo = mapeamento_centro_custo(df_categorias_mes)

    # Calcula 'Permanece no Desconto' de acordo com 'Centro de Custo'
    df_categorias_mes_centro_custo["Permanece no Desconto"] = np.where(
        (df_categorias_mes_centro_custo["Centro de Custo"].isna()), # se é NULO
        df_categorias_mes_centro_custo["DESCONTO"], # usa o valor total do desconto
        df_categorias_mes_centro_custo["DESCONTO"] - df_categorias_mes_centro_custo["Aloca no Centro de Custo"]  # senão faz desconto menos 'Aloca no Centro de Custo'
    )   

    # Calcula Dedução de A&B para EVENTOS
    if casa == 'Orfeu': # Mudança para caso do Orfeu
        DEDUCAO_FAT_ALIM = 0.57
        DEDUCAO_FAT_BEB = 0.43
    
    condicao = df_categorias_mes_centro_custo['CATEGORIA'].isin(['EVENTO', 'EVENTOS'])
    df_categorias_mes_centro_custo.loc[condicao, 'Dedução Faturamento - Alimento'] = df_categorias_mes_centro_custo['DESCONTO'] * DEDUCAO_FAT_ALIM
    df_categorias_mes_centro_custo.loc[condicao, 'Dedução Faturamento - Bebida'] = df_categorias_mes_centro_custo['DESCONTO'] * DEDUCAO_FAT_BEB

    # Mapeamento - Descontos - DRE
    df_categorias_mes_descontos_dre = mapeamento_descontos_dre(df_categorias_mes_centro_custo)
    df_descontos_dre_editavel = df_categorias_mes_descontos_dre.copy()

    # Exibe tebela resultante editável
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Tabela formatada')
    # with col2:
        # button_download(df_download, f"{casa} - {mes}{ano}", f"Descontos - {casa}")
    
    # Organiza colunas para exibição
    df_descontos_dre_editavel.sort_values(by=['Descontos - DRE'], ascending=True, na_position='first', inplace=True) # None ficam no início do df
    df_descontos_dre_editavel = df_descontos_dre_editavel.rename(columns={
        'FK_CASA': 'ID Casa',
        'CATEGORIA': 'Categoria',
        'DESCONTO': 'Total Desconto',
        'DATA': 'Data'
    })
    df_descontos_dre_editavel = df_descontos_dre_editavel[['ID Casa', 'Data', 'Categoria', 'Total Desconto', 'CMV', 'Aloca no Centro de Custo', 'Centro de Custo', 'Permanece no Desconto', 'Dedução Faturamento - Alimento', 'Dedução Faturamento - Bebida', 'Descontos - DRE']]

    # Exibe df com coluna editável
    df_descontos_dre_editavel = st.data_editor(
        df_descontos_dre_editavel,
        # column_config={
        #     "Descontos - DRE": st.column_config.NumberColumn(
        #         "Your rating",
        #         help="How much do you like this command (1-5)?",
        #         min_value=1,
        #         max_value=5,
        #         step=1,
        #         format="%d ⭐",
        #     ),
        # },
        disabled=[col for col in df_descontos_dre_editavel if col != 'Descontos - DRE'],
        hide_index=True,
    )
    
    # Contabiliza registros sem classificação
    df_descontos_dre_vazios = df_descontos_dre_editavel[(df_descontos_dre_editavel['Descontos - DRE'].isna()) | (df_descontos_dre_editavel['Descontos - DRE'] == '')]
    contagem_descontos_dre_vazios = df_descontos_dre_vazios['Data'].count()

    # Formata df para download
    df_download = df_descontos_dre_editavel.copy()
    df_download = df_download.rename(columns={
        'ID Casa': 'FK_CASA',
        'Categoria': 'CATEGORIA',
        'Total Desconto': 'TOTAL_DESCONTO',
        'Data': 'DATA',
        'Aloca no Centro de Custo': 'ALOCA_CENTRO_CUSTO',
        'Centro de Custo': 'CENTRO_CUSTO',
        'Permanece no Desconto': 'PERMANECE_DESCONTO',
        'Dedução Faturamento - Alimento': 'DEDUCAO_FATURAMENTO_ALIM',
        'Dedução Faturamento - Bebida': 'DEDUCAO_FATURAMENTO_BEB',
        'Descontos - DRE': 'DESCONTOS_DRE'
    })
    df_download = df_download[['FK_CASA', 'DATA', 'CATEGORIA', 'TOTAL_DESCONTO', 'CMV', 'ALOCA_CENTRO_CUSTO', 'CENTRO_CUSTO', 'PERMANECE_DESCONTO', 'DEDUCAO_FATURAMENTO_ALIM', 'DEDUCAO_FATURAMENTO_BEB', 'DESCONTOS_DRE']]
    df_download = df_download.sort_values(by=['FK_CASA'])

    col1, col2 = st.columns([5, 1], vertical_alignment='center')
    if contagem_descontos_dre_vazios == 0: 
        with col1: st.success('Todos registros classificados na coluna "Descontos - DRE"!')
        with col2: button_download(df_download, f"{casa} - {mes}{ano}", f"Descontos - {casa}")
        
    else: 
        with col1: st.warning(f'Atenção: há {contagem_descontos_dre_vazios} registros sem classificação na coluna "Descontos - DRE"')
        with col2: button_download(df_download, f"{casa} - {mes}{ano}", f"Descontos - {casa}")
        
        st.markdown("""
            **Preencha os registros vazios com uma das opções abaixo, sem erros de digitação.**

            - Desconto - Alimentação Escritório
            - Descontos - Marketing
            - Descontos - Operação
            - Faturamento de Eventos - Promoções Utilizadas
        """)

else: # Quando não há dados de Descontos e Promoções para o mês selecionado
    st.info('Nada a ser exibido para a data selecionada.')
    
