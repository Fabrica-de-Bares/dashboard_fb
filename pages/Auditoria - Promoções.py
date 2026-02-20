import streamlit as st
import pandas as pd
import numpy as np
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download, seletor_mes, seletor_ano


# --- PATCH para ignorar cores inválidas no openpyxl ---
from openpyxl.styles.colors import WHITE, RGB
__old_rgb_set__ = RGB.__set__

def __rgb_set_fixed__(self, instance, value):
    try:
        __old_rgb_set__(self, instance, value)
    except ValueError as e:
        if e.args[0] == 'Colors must be aRGB hex values':
            __old_rgb_set__(self, instance, WHITE)  # substitui por branco

RGB.__set__ = __rgb_set_fixed__
# --- FIM DO PATCH ---


st.set_page_config(
    page_title="Formatar - Promoções",
    page_icon=":material/list:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/list: Formatar - Promoções")
st.write('Aba que formata a planilha de Promoções ZigPay para inserção automática no EPM.')
st.divider()

# Seletores de casa e data
df_casas = GET_CASAS()

col1, col2, col3 = st.columns(3)

with col1:
    # casas = df_casas['Casa'].tolist()
    casas = ['Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'BNSP', 'Edificio Rolim', 'Girondino', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Riviera Bar', 'Terraço Notiê', 'The Cavern']
    casa = st.selectbox("Selecione a casa correspondente ao arquivo de Promoções:", casas)
    
    # Recupera id da casa
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
    if casa != 'BNSP' and casa != 'Terraço Notiê':
        if casa == 'Edificio Rolim':
            id_casa = 145
        else:   
            id_casa = mapeamento_casas[casa]
    elif casa == 'Terraço Notiê':
        id_casa = 162
    elif casa == 'BNSP':
        id_casa = 131

with col2:
    mes = seletor_mes("Selecione o mês correspondente ao arquivo de Promoções:", key="seletor_mes_promocoes_zig")
    
with col3:
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano correspondente ao arquivo de Promoções:')

st.divider()

# Dar upload na planilha de descontos da zig
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if not uploaded_file:
    st.write("Adicione um arquivo .xlsx de Promoções para formatá-lo")

# Se arquivo adicionado, prossegue
else:
    # Lê o arquivo adicionado
    df = pd.read_excel(uploaded_file, skiprows=3)
    st.divider()
    st.subheader('Tabela original')
    st.dataframe(df, hide_index=True)
    st.divider()

    # Formata a tabela para inserção no banco
    df_formatado = df.copy()
    df_formatado['id_casa'] = id_casa

    # Cria coluna com primeiro dia do mês dos descontos
    df_formatado['Data'] = pd.Timestamp(
        year=int(ano),
        month=int(mes),
        day=1
    )

    # Renomeia colunas
    df_formatado = df_formatado.rename(columns={
       'Produto': 'PRODUTO',
       'Promoção': 'PROMOCAO',
       'Categoria': 'CATEGORIA_PRODUTO',
       'Quantidade de usos': 'QUANTIDADE_USOS',
       'Desconto total': 'DESCONTO_TOTAL',
       'id_casa': 'FK_CASA',
       'Data': 'DATA' 
    })

    # Cria coluna que de categoria 'Eventos' - Stand by
    # df_formatado["CATEGORIA"] = np.where(
    #     (~df_formatado["PROMOCAO"].isin([ # Para o que não está nessas categorias
    #         '30% ESHOWS - RG', '30% ESHOWS - CPF', 
    #         '30% DIVERTI - CPF', 
    #         '30% FÁBRICA DE BARES - CPF', '30% FÁBRICA DE BARES - RG', 
    #         'CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB', 'CARTÃO BLACK - FB', 
    #         'LUCIANO PERES - SÓCIO ',
    #         '10% CONVENIADOS - CPF'
    #     ])), 
    #     'Eventos',  # categoriza como 'Eventos'
    #     None        # senão, Null
    # )

    # Reordena colunas
    df_formatado = df_formatado[['FK_CASA', 'DATA', 'PRODUTO', 'PROMOCAO', 'CATEGORIA_PRODUTO', 'QUANTIDADE_USOS', 'DESCONTO_TOTAL']]
    df_download = df_formatado.copy()

    # Renomeia casas para formatar nome do arquivo excel
    if casa == 'Bar Brahma - Centro': nome_casa = 'BBC'
    elif casa == 'Bar Brahma - Granja': nome_casa = 'BBG'
    elif casa == 'Bar Léo - Centro': nome_casa = 'Bar Léo'
    elif casa == 'Blue Note - São Paulo': nome_casa = 'Blue Note SP'
    elif casa == 'Edificio Rolim': nome_casa = 'Rolim'
    elif casa == 'Girondino - CCBB': nome_casa = 'CCBB'
    elif casa == 'Love Cabaret': nome_casa = 'Love'
    elif casa == 'Riviera Bar': nome_casa = 'Riviera'
    else: nome_casa = casa

    # Mostra o resultado
    col1, col2 = st.columns(2, vertical_alignment='center')
    with col1:
        st.subheader('Tabela formatada')
        st.write('Tabela adequada para inputar os dados no EPM.')
    with col2:
        button_download(df_download, f"{nome_casa} - PROMO_{mes}{ano}", f"Promoções - {casa}")
    
    st.dataframe(df_download, hide_index=True)

