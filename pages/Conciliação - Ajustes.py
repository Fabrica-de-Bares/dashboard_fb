import streamlit as st
from utils.components import seletor_ano, input_selecao_casas
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import casas_validas
from utils.functions.general_functions import config_sidebar
from utils.functions.ajustes import *
from utils.queries_conciliacao import *


st.set_page_config(
  page_title="Conciliação FB - Ajustes",
  page_icon="🛠️",
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
  st.title("🛠️ Ajustes")
with col2:
  st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Filtrando por casa e ano
datas = calcular_datas()
col1, col2 = st.columns(2)

# Seletor de casa
with col1: 
  lista_retirar_casas = ['Todas as Casas', 'Bar Léo - Vila Madalena', 'Blue Note SP (Sala 2)', 'The Cavern - Almoço', 'Brahminha']
  id_casa, nome_casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
  
# Seletor de ano
with col2:
  ano = seletor_ano(2024, 2026, 'ano_ajustes')

st.divider()

# Define df usados nos gráficos individuais de casa (de acordo com casa e data dos seletores)
df_ajustes_filtrado = define_df_ajustes(id_casa, ano)
lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt = total_ajustes_mes(df_ajustes_filtrado)
lista_qtd_ajustes_mes = qtd_ajustes_mes(df_ajustes_filtrado)


# Cria a lista da qtd de ajustes por mês de cada casa usando list comprehension
lista_ajustes_casas = [lista_ajustes_casa(casa, ano) for casa in casas_validas]

# Exibe gráfico de todos os meses e todas as casas
if nome_casa == 'Todas as casas':
  with st.container(border=True):
    col1, col2, col3 = st.columns([0.05, 4, 0.05], vertical_alignment="center")
    with col2:
      st.subheader("Contagem de ajustes por mês e por casa")
      grafico_ajustes_todas_casas(casas_validas, nomes_meses, lista_ajustes_casas)


with st.container(border=True):
  if (len(lista_ajustes_pos_mes_fmt) == 0 and len(lista_ajustes_neg_mes_fmt) == 0) and all(v == 0 for v in lista_qtd_ajustes_mes):
    st.warning(f"Não há ajustes a serem exibidos para {nome_casa}")
  else: 
    col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment="center")
    with col2:
      # Exibe gráfico da contagem de ajustes por mês
      st.subheader(f"Contagem total de ajustes por mês - {nome_casa}")
      grafico_qtd_ajustes_mes(lista_qtd_ajustes_mes)
      st.divider()

      # Exibe gráfico de valor total de ajustes por mês
      st.subheader(f"Valor total de ajustes por mês - {nome_casa}")
      grafico_total_ajustes_mes(df_ajustes_filtrado, lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt)
      
  

