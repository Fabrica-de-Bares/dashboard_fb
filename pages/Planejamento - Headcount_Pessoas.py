import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_planejamento_anual import *
from utils.functions.controladoria_quarterday import formatar_moeda_br
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


# # Para Nº Colaboradores
# df_num_colaboradores = df_download[(df_download['ANO'] == ano) & (df_download['TIPO_DADO'] == 'Nº COLABORADORES')].copy()
# df_num_colaboradores = df_num_colaboradores.pivot_table(
#     index='CARGO',
#     columns='MES',
#     values='VALOR',
#     sort=False
# ).reset_index()

# nomes_meses = {
#     1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
#     5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
#     9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
# }
# df_num_colaboradores = df_num_colaboradores.rename(columns=nomes_meses)
# colunas_meses = df_num_colaboradores.select_dtypes(include='number').columns

# df_final_num_colaboradores = prepara_secoes_headcount(df_num_colaboradores, colunas_meses)
# df_styled = df_final_num_colaboradores.style.apply(highlight_secoes_headcount, axis=1).format({col: "{:.0f}" for col in colunas_meses})

# st.dataframe(df_styled, hide_index=True, width='stretch')

# # Para Remuneração
# df_remuneracao = df_download[(df_download['ANO'] == ano) & (df_download['TIPO_DADO'] == 'REMUNERAÇÃO')].copy()
# df_remuneracao = df_remuneracao.pivot_table(
#     index='CARGO',
#     columns='MES',
#     values='VALOR',
#     sort=False
# ).reset_index()

# nomes_meses = {
#     1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
#     5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
#     9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
# }
# df_remuneracao = df_remuneracao.rename(columns=nomes_meses)
# colunas_meses = df_remuneracao.select_dtypes(include='number').columns

# df_final_remuneracao = prepara_secoes_headcount(df_remuneracao, colunas_meses)
# df_styled = df_final_remuneracao.style.apply(highlight_secoes_headcount, axis=1).format(formatar_moeda_br, subset=colunas_meses)

# st.dataframe(df_styled, hide_index=True, width='stretch')


        
        
