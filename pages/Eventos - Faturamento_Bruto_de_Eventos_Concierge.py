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

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Faturamento Bruto de Eventos - Concierge",
	page_icon="💰",
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
		st.title("💰 Faturamento Bruto de Eventos - Concierge")
	with col2:
		st.button(label='Atualizar', key='atualizar_faturamento', on_click=st.cache_data.clear)
	st.divider()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_CONCIERGE()
	# Substitui nome e ID da casa Priceless
	df_eventos['Casa'] = df_eventos['Casa'].apply(lambda x: 'Terraço Notie' if x == 'Priceless' else x)
	df_eventos['ID Casa'] = df_eventos['ID Casa'].apply(lambda x: 162 if x == 149 else x)

	df_parcelas = GET_PARCELAS_EVENTOS_CONCIERGE()
	df_parcelas['ID Casa'] = df_parcelas['ID Casa'].apply(lambda x: 162 if x == 149 else x)
	df_parcelas['Casa'] = df_parcelas['Casa'].apply(lambda x: 'Terraço Notie' if x == 'Priceless' else x)
	df_orcamentos = GET_ORCAMENTOS_EVENTOS_CONCIERGE()

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
		'Valor Total Locação': float,
		'Valor Locação Gerador': float,
		'Valor Locação Mobiliário': float,
		'Valor Locação Utensílios': float,
		'Valor Taxa Serviço': float,
		'Valor Locação Espaço': float,
		'Valor Contratação Artístico': float,
		'Valor Contratação Técnico de Som': float,
		'Valor Contratação Bilheteria/Couvert Artístico': float,
		'Valor Mão de Obra Extra': float,
		'Valor Taxa Administrativa': float,
		'Valor Extras Gerais': float,
		'Valor Acréscimo Forma de Pagamento': float
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

	# Formata tipos de dados do dataframe de orcamentos
	tipos_de_dados_orcamentos = {
		'Valor': float
	}
	df_orcamentos = df_orcamentos.astype(tipos_de_dados_orcamentos, errors='ignore')

	# Calcula o valor de repasse para Gazit
	df_eventos = calcular_repasses_gazit(df_eventos)
	
	# Seletores
	col1, col2= st.columns([1, 1], gap="large")
	with col1:
		lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Blue Note SP (Sala 2)', 'Escritório Fabrica de Bares', 'The Cavern - Almoço', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'Girondino', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Priceless', 'Riviera Bar', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Ultra Evil Premium Ltda ']
		df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='faturamento_bruto')
		lista_ids_casa = df_casas_selecionadas['ID_Casa'].tolist()
	with col2:
		ano = seletor_ano(2024, 2026, key='ano_faturamento')
	st.divider()

	if lista_ids_casa == []:
		st.warning("Nenhuma casa selecionada")
	
	# Faturamento por Categoria
	with st.container(border=True):
		col1, col2, col3, col4 = st.columns([0.1, 2, 0.8, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento – Eventos Confirmados")
		with col3:
			filtro_data_categoria = "Competência"
			filtro_data_categoria = st.segmented_control(
				label="Por Data de:",
				options=["Competência", "Recebimento (Caixa)"],
				selection_mode="single",
				default="Competência",
			)
		st.write("")

		# Filtros parcelas
		df_parcelas_filtradas_por_status = filtrar_por_classe_selecionada(df_parcelas, 'Status Evento', ['Confirmado'])
		df_parcelas_filtradas_por_data = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, filtro_data_categoria, ano)

		# Filtros orcamentos
		df_orcamentos = filtrar_por_classe_selecionada(df_orcamentos, 'Ano', [ano])
		df_orcamentos = filtrar_por_classe_selecionada(df_orcamentos, 'ID Casa', lista_ids_casa)

		# Visualização do faturamento
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			if filtro_data_categoria is None:
				st.warning("Por favor, selecione um filtro de data.")
			df_parcelas_casa = df_parcelas_filtradas_por_data[df_parcelas_filtradas_por_data['ID Casa'].isin(lista_ids_casa)]
			if lista_ids_casa != [149]:
				montar_tabs_geral(
					df_parcelas_casa,
					'Todas as Casas Selecionadas',
					lista_ids_casa,
					filtro_data_categoria,
					df_orcamentos,
					exibir_painel_ano=True,
				)

			else:
				montar_tabs_priceless(
					df_parcelas_casa,
					149,
					df_eventos,
					filtro_data_categoria,
					df_orcamentos,
					exibir_painel_ano=True,
				)
	st.write("")

	df_eventos_filtrados_por_status = filtrar_por_classe_selecionada(df_eventos, 'Status Evento', ['Confirmado'])
	df_eventos_filtrados_por_status_e_ano = df_filtrar_ano(df_eventos_filtrados_por_status, 'Data Evento', ano)

	# Faturamento por tipo de evento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Tipo de Evento*")
			st.write("")
			grafico_linhas_faturamento_classificacoes_evento(df_eventos_filtrados_por_status_e_ano, lista_ids_casa, coluna_categoria='Tipo Evento')

			st.markdown("*Por mês de competência do evento.")
	st.write("")

	# Faturamento por modelo de evento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Modelo de Evento*")
			st.write("")
			grafico_linhas_faturamento_classificacoes_evento(df_eventos_filtrados_por_status_e_ano, lista_ids_casa, coluna_categoria='Modelo Evento')
			st.markdown("*Por mês de competência do evento.")
	st.write("")

	# Faturamento por segmento do evento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Segmento do Evento*")
			st.write("")
			grafico_linhas_faturamento_classificacoes_evento(df_eventos_filtrados_por_status_e_ano, lista_ids_casa, coluna_categoria='Segmento Evento')
			st.markdown("*Por mês de competência do evento.")
	st.write("")

	
if __name__ == '__main__':
  main()