import streamlit as st
import pandas as pd
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.functions.faturamento import *
from utils.user import *
from utils.functions.concilicacao_eventos_vencimento_recebimento import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_icon="↔️",
	page_title="Contas a Receber - Conciliação de Parcelas de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():

	st.markdown(" <style>iframe{ height: 320px !important } ", unsafe_allow_html=True)
	config_sidebar()

	# Header
	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title("↔️ Contas a Receber - Conciliação de Parcelas de Eventos")
	with col2:
		st.button(label='Atualizar', key='atualizar_conciliacao_vencimento_recebimento_eventos', on_click=st.cache_data.clear)
	st.divider()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_E_ADITIVOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()
	
    # Formata tipos de dados do dataframe de eventos
	tipos_de_dados_eventos = {
		'Valor Locação Aroo 1': float,
		'Valor Locação Aroo 2': float,
		'Valor Locação Aroo 3': float,
		'Valor Locação Anexo': float,
		'Valor Locação Notie': float,
		'Valor Locação Mirante': float,
		'Valor Imposto': float,
		'Valor AB': float,
		'Valor Total Evento': float,
		'Valor Total Locação': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')
	df_eventos['Data Contratação'] = pd.to_datetime(df_eventos['Data Contratação'], errors='coerce')
	df_eventos['Data Evento'] = pd.to_datetime(df_eventos['Data Evento'], errors='coerce')

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor Parcela': float,
		'Categoria Parcela': str
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
	df_parcelas['Data Vencimento'] = pd.to_datetime(df_parcelas['Data Vencimento'], errors='coerce')
	df_parcelas['Data Recebimento'] = pd.to_datetime(df_parcelas['Data Recebimento'], errors='coerce')
	
	# Adiciona coluna de concatenação de ID e Nome Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID Evento'].astype(str) + " - " + df_eventos['Nome Evento']
	
	# Seletores
	col1, col2= st.columns([1, 1], gap="large")
	with col1:
		lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Terraço Notie', 'Blue Note SP (Sala 2)', 'Escritório Fabrica de Bares', 'The Cavern - Almoço']
		df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='faturamento_bruto')
		lista_ids_casas = df_casas_selecionadas['ID_Casa'].tolist()
	with col2:
		ano = seletor_ano(2024, 2026, key='ano_faturamento')
	st.divider()

	# Filtros parcelas
	df_parcelas_casa = filtrar_por_classe_selecionada(df_parcelas, 'ID Casa', lista_ids_casas)
	df_parcelas_filtradas_por_status = filtrar_por_classe_selecionada(df_parcelas_casa, 'Status Evento', ['Confirmado'])

	# Vencimento x Recebimento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Vencimento x Recebimento")
			st.write("")
			df_parcelas_vencimento = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, "Vencimento", ano)
			df_parcelas_recebimento = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, "Recebimento (Caixa)", ano)
			grafico_barras_vencimento_x_recebimento(df_parcelas_recebimento, df_parcelas_vencimento, lista_ids_casas)
	
	# Farol de Parcelas Atrasadas
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		df_farol = filtra_parcelas_atrasadas(df_parcelas_filtradas_por_status)
		df_farol = df_format_date_columns_brazilian(df_farol, ['Data Vencimento', 'Data Recebimento'])
		df_farol_download = df_farol.copy()
		df_farol = format_columns_brazilian(df_farol, ['Valor Parcela'])
		df_farol = rename_colunas_parcelas(df_farol)
		if df_farol is not None:
			df_farol = df_farol.drop(columns=['ID Casa'], errors='ignore')
		
			with col2:
				col1, col2 = st.columns([4, 1], gap="large", vertical_alignment="center")
				with col1:
					st.markdown(f"## Farol de Parcelas Atrasadas")
				with col2:
					button_download(df_farol_download, 'Parcelas_Atrasadas', 'parcelas_atrasadas')
				
				st.dataframe(df_farol, width='stretch', hide_index=True)
				st.markdown("Todas as parcelas ainda sem pagamento após a Data de Vencimento.")
		else:
			with col2:
				col1, col2 = st.columns([4, 1], gap="large", vertical_alignment="center")
				with col1:
					st.markdown(f"## Farol de Parcelas Atrasadas")
					st.warning("Nenhuma parcela atrasada encontrada.")
					st.stop()


if __name__ == '__main__':
  main()