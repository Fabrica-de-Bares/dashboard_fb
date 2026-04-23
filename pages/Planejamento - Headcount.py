import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.planejamento_anual import *
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.functions.general_functions_conciliacao import calcular_datas
from utils.components import button_download, seletor_ano, input_selecao_casas
from utils.queries_controladoria import *


pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Headcount de Pessoas",
    page_icon="👥",
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
    st.title("👥 Headcount de Pessoas")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa') 
with col2:
    ano = seletor_ano(2026, 2026, 'ano')
st.divider()

local = st.secrets['local_headcount']
local = local['local']
df_headcount = pd.read_excel(local + f'\{casa}.xlsx')
st.write(df_headcount)

