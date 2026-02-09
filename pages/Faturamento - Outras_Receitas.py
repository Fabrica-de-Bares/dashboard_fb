import streamlit as st
import pandas as pd
from utils.queries_financeiro import *
from utils.functions.financeiro_faturamento_extraordinario import *
from utils.functions.general_functions import *
from utils.components import *
from utils.user import logout

st.set_page_config(
  layout = 'wide',
  page_title = 'Faturamento - Outras Receitas',  
  page_icon=':dollar:',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')

config_sidebar()
col, col2, col3 = st.columns([6, 1, 1])
with col:
  st.title(':dollar: Faturamento - Outras Receitas')
with col2:
  st.button(label="Atualizar", on_click = st.cache_data.clear)

st.divider()


data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
# Seletores
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    # Filtro de casa:
  lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless', 'Todas as Casas']
  id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='calendario')
  lojas_selecionadas = [casa]
with col2:
  data_inicio = st.date_input(
      'Data de Início',
      value=data_inicio_default,
      key='data_inicio_input',
      format="DD/MM/YYYY"
  )
with col3:
  data_fim = st.date_input(
      'Data de Fim',
      value=data_fim_default,
      key='data_fim_input',
      format="DD/MM/YYYY"
  )
st.divider()

ReceitExtraord = config_receit_extraord(lojas_selecionadas, data_inicio, data_fim)
FaturamReceitExtraord, Totais = faturam_receit_extraord(ReceitExtraord)
df_agrupado = ReceitExtraord.groupby('Data Evento').agg({'Valor Total': 'sum', 'ID': 'count'}).reset_index()
df_agrupado.rename(columns={'ID': 'Quantidade de Eventos'}, inplace=True)


with st.container(border=True):
  col0, col1, col2 = st.columns([1, 10, 1])
  with col1:
    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
    with col1:
      st.subheader("Faturamento Receitas Extraordinárias*:")
    with col2:
      st.write("*Receitas de Eventos até 09/2025")
    st.dataframe(FaturamReceitExtraord, width='stretch', hide_index=True)
    st.write("**Faturamento Extraordinário Total:**")
    st.dataframe(Totais, width='stretch', hide_index=True)


st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)

classificacoes = ['Eventos', 'Coleta de Óleo', 'Bilheteria', 'Patrocínio', 'Premium Corp']

with st.container(border=True):
  col0, col1, col2 = st.columns([1, 15, 1])
  with col1:
    col3, col4 = st.columns([2, 1])
    with col3:
      st.subheader("Detalhamento por Classificação:")
    with col4:
      classificacoes_selecionadas = st.multiselect(label='Selecione Classificações', options=classificacoes)
    DfFiltrado = filtrar_por_classe_selecionada(ReceitExtraord, 'Classificação', classificacoes_selecionadas)
    DfFiltrado = format_columns_brazilian(DfFiltrado, ['Valor Total', 'Categ. AB', 'Categ. Aluguel', 'Categ. Artista', 'Categ. Couvert', 'Categ. Locação', 'Categ. Patrocínio', 'Categ. Taxa de serviço'])
    st.dataframe(DfFiltrado, width='stretch', hide_index=True)

