import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.user import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_icon=":receipt:",
	page_title="Auditoria de Eventos - Preenchimento dos Lançamentos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')
 
def main():
	config_sidebar()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_AUDITORIA()
	df_parcelas = GET_PARCELAS_EVENTOS_AUDITORIA()
	
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
		'Valor Locação Gerador': float,
		'Valor Locação Mobiliário': float,
		'Valor Locação Utensílios': float,
		'Valor Mão de Obra Extra': float,
		'Valor Taxa Administrativa': float,
		'Valor Comissão BV': float,
		'Valor Extras Gerais': float,
		'Valor Taxa Serviço': float,
		'Valor Acréscimo Forma de Pagamento': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')
	df_eventos['Data Contratação'] = pd.to_datetime(df_eventos['Data Contratação'], errors='coerce')
	df_eventos['Data Evento'] = pd.to_datetime(df_eventos['Data Evento'], errors='coerce')
	df_eventos['Data Envio Proposta'] = pd.to_datetime(df_eventos['Data Envio Proposta'], errors='coerce')
	df_eventos['Data Recebimento Lead'] = pd.to_datetime(df_eventos['Data Recebimento Lead'], errors='coerce')

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor Parcela': float
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
	df_parcelas['Data Vencimento'] = pd.to_datetime(df_parcelas['Data Vencimento'], errors='coerce')
	df_parcelas['Data Recebimento'] = pd.to_datetime(df_parcelas['Data Recebimento'], errors='coerce')

	# Lista de eventos para o filtro
	eventos_unicos = df_eventos['ID Evento'].unique().tolist()
	eventos_id_options = ['Todos os Eventos'] + sorted(eventos_unicos)

	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.header(":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
	with col2:
		st.button(label='Atualizar', key='atualizar_informacoes_eventos', on_click=st.cache_data.clear)
	st.divider()

	# Filtro de casa:
	lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Terraço Notie', 'Blue Note SP (Sala 2)', 'Escritório Fabrica de Bares', 'The Cavern - Almoço']
	df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='seletor_casas_auditoria')
	lista_ids_casas = df_casas_selecionadas['ID_Casa'].unique().tolist()
	df_eventos = df_eventos[df_eventos['ID Casa'].isin(lista_ids_casas)]
	df_parcelas = df_parcelas[df_parcelas['ID Casa'].isin(lista_ids_casas)]

	# Filtro Confirmados, Em Negociação e Declinados
	df_eventos_confirmados = df_eventos[df_eventos['Status'] == 'Confirmado']
	df_parcelas_eventos_confirmados = df_parcelas[df_parcelas['Status Evento'] == 'Confirmado']

	df_eventos_declinados = df_eventos[df_eventos['Status'] == 'Declinado']

	df_eventos_em_negociacao = df_eventos[df_eventos['Status'] == 'Em negociação']
	
	lista_ids_eventos_confirmados = df_eventos_confirmados['ID Evento'].unique().tolist()
	lista_ids_eventos_com_parcelas = df_parcelas_eventos_confirmados['ID Evento'].unique().tolist()
	lista_ids_eventos_sem_parcelas = list(set(lista_ids_eventos_confirmados) - set(lista_ids_eventos_com_parcelas))

	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("### Farol - Eventos Confirmados sem Parcelas Lançadas")
			df_eventos_sem_parcelas = df_eventos_confirmados[df_eventos_confirmados['ID Evento'].isin(lista_ids_eventos_sem_parcelas)]
			df_eventos_sem_parcelas_download = df_eventos_sem_parcelas.copy()
			df_eventos_sem_parcelas = df_formata_datas_sem_horario(df_eventos_sem_parcelas, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			df_eventos_sem_parcelas = format_columns_brazilian(df_eventos_sem_parcelas, ['Valor Total Evento', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Valor Imposto', 'Valor AB', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Taxa Serviço', 'Valor Acréscimo Forma de Pagamento'])
			if df_eventos_sem_parcelas.empty:
				st.success("Nenhum evento sem parcelas lançadas.")
			else:
				st.dataframe(df_eventos_sem_parcelas, width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_sem_parcelas_download, f"sem_parcelas", f"sem_parcelas")

			st.markdown("### Farol - Eventos Confirmados sem Data de Envio da Proposta")
			df_eventos_sem_data_envio_proposta = df_eventos_confirmados[df_eventos_confirmados['Data Envio Proposta'].isna()]
			df_eventos_sem_data_envio_proposta_download = df_eventos_sem_data_envio_proposta.copy()
			df_eventos_sem_data_envio_proposta = df_formata_datas_sem_horario(df_eventos_sem_data_envio_proposta, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			if df_eventos_sem_data_envio_proposta.empty:
				st.success("Nenhum evento sem data de envio da proposta.")
			else:
				st.dataframe(df_eventos_sem_data_envio_proposta[['ID Evento', 'Nome Evento', 'Casa', 'Status', 'Cliente', 'Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_sem_data_envio_proposta_download, f"sem_data_envio_proposta", f"sem_data_envio_proposta")

			st.markdown("### Farol - Eventos Confirmados sem Data de Recebimento do Lead")
			df_eventos_sem_data_recebimento_lead = df_eventos_confirmados[df_eventos_confirmados['Data Recebimento Lead'].isna()]
			df_eventos_sem_data_recebimento_lead_download = df_eventos_sem_data_recebimento_lead.copy()
			df_eventos_sem_data_recebimento_lead = df_formata_datas_sem_horario(df_eventos_sem_data_recebimento_lead, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			if df_eventos_sem_data_recebimento_lead.empty:
				st.success("Nenhum evento sem data de recebimento do lead.")
			else:
				st.dataframe(df_eventos_sem_data_recebimento_lead[['ID Evento', 'Nome Evento', 'Casa', 'Status', 'Cliente', 'Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_sem_data_recebimento_lead_download, f"sem_data_recebimento_lead", f"sem_data_recebimento_lead")

			st.markdown("### Farol - Eventos Confirmados sem Data de Contratação")
			df_eventos_sem_data_contratacao = df_eventos_confirmados[df_eventos_confirmados['Data Contratação'].isna()]
			df_eventos_sem_data_contratacao_download = df_eventos_sem_data_contratacao.copy()
			df_eventos_sem_data_contratacao = df_formata_datas_sem_horario(df_eventos_sem_data_contratacao, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			if df_eventos_sem_data_contratacao.empty:
				st.success("Nenhum evento sem data de contratação.")
			else:
				st.dataframe(df_eventos_sem_data_contratacao[['ID Evento', 'Nome Evento', 'Casa', 'Status', 'Cliente', 'Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_sem_data_contratacao_download, f"sem_data_contratacao", f"sem_data_contratacao")

			st.markdown("### Farol - Eventos Declinados sem Motivo de Declínio")
			df_eventos_sem_motivo_declinio = df_eventos_declinados[df_eventos_declinados['Motivo Declínio'].isna()]
			if df_eventos_sem_motivo_declinio.empty:
				st.success("Nenhum evento sem motivo de declínio.")
			else:
				st.dataframe(df_eventos_sem_motivo_declinio[['ID Evento', 'Nome Evento', 'Casa', 'Cliente', 'Status', 'Motivo Declínio']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_sem_motivo_declinio, f"sem_motivo_declinio", f"sem_motivo_declinio")
					
			st.markdown("### Farol - Eventos Em negociação com Data do Evento passado")
			df_eventos_em_negociacao_passados = df_eventos_em_negociacao[df_eventos_em_negociacao['Data Evento'] < datetime.datetime.today()]
			df_eventos_em_negociacao_passados_download = df_eventos_em_negociacao_passados.copy()
			df_eventos_em_negociacao_passados = df_formata_datas_sem_horario(df_eventos_em_negociacao_passados, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			if df_eventos_em_negociacao_passados.empty:
				st.success("Nenhum evento em negociação com data do evento passada.")
			else:
				st.dataframe(df_eventos_em_negociacao_passados[['ID Evento', 'Nome Evento', 'Casa', 'Status', 'Cliente', 'Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_em_negociacao_passados_download, f"em_negociacao_passados", f"em_negociacao_passados")

			st.markdown("### Farol - Eventos Em negociação com Data de Contratação")
			df_eventos_em_negociacao_com_data_contratacao = df_eventos_em_negociacao[df_eventos_em_negociacao['Data Contratação'].notna()]
			df_eventos_em_negociacao_com_data_contratacao_download = df_eventos_em_negociacao_com_data_contratacao.copy()
			df_eventos_em_negociacao_com_data_contratacao = df_formata_datas_sem_horario(df_eventos_em_negociacao_com_data_contratacao, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
			if df_eventos_em_negociacao_com_data_contratacao.empty:
				st.success("Nenhum evento em negociação com data de contratação.")
			else:
				st.dataframe(df_eventos_em_negociacao_com_data_contratacao[['ID Evento', 'Nome Evento', 'Casa', 'Status', 'Cliente', 'Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação']], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_eventos_em_negociacao_com_data_contratacao_download, f"em_negoc_data_contratacao", f"em_negoc_data_contratacao")
			
			st.markdown("### Farol - Valor Total do Evento x Valor Total das Parcelas")
			df_valor_total_parcelas = df_parcelas_eventos_confirmados.groupby('ID Evento')['Valor Parcela'].sum().reset_index().rename(columns={'Valor Parcela': 'Valor Total Parcelas'})
			df_comparacao = df_eventos_confirmados[['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'Data Evento', 'Observações', 'Valor Total Evento']].merge(df_valor_total_parcelas, on='ID Evento', how='left')
			df_comparacao['Diferença'] = df_comparacao['Valor Total Evento'] - df_comparacao['Valor Total Parcelas']
			df_comparacao = df_comparacao[df_comparacao['Diferença'] != 0]
			df_comparacao_download = df_comparacao.copy()
			df_comparacao = format_columns_brazilian(df_comparacao, ['Valor Total Evento', 'Valor Total Parcelas', 'Diferença'])
			df_comparacao = df_format_date_columns_brazilian(df_comparacao, ['Data Evento'])
			df_comparacao.sort_values(by=['Casa'], inplace=True)
			if df_comparacao.empty:
				st.success("Nenhuma diferença entre o valor total do evento e o valor total das parcelas.")
			else:
				st.dataframe(df_comparacao, width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_comparacao_download, f"comparacao", f"comparacao")

			st.markdown("### Farol - Valor Total x Valor Total das Categorias")
			df_valor_total_categorias = df_eventos.copy()
			# Colunas que começam com "Valor"
			colunas_valor = [col for col in df_valor_total_categorias.columns if col.startswith("Valor") and col != "Valor Total Evento"]
			df_valor_total_categorias[colunas_valor] = df_valor_total_categorias[colunas_valor].fillna(0)
			df_valor_total_categorias['Valor Total Categorias'] = df_valor_total_categorias[colunas_valor].sum(axis=1)
			df_valor_total_categorias['Diferença'] = df_valor_total_categorias['Valor Total Evento'] - df_valor_total_categorias['Valor Total Categorias']
			df_valor_total_categorias = df_valor_total_categorias[df_valor_total_categorias['Diferença'] != 0]
			df_valor_total_categorias = df_valor_total_categorias[df_valor_total_categorias['Status'] == 'Confirmado']
			colunas = ['ID Evento', 'Nome Evento', 'ID Casa', 'Casa', 'Data Evento', 'Valor Total Evento', 'Valor Total Categorias', 'Diferença', 'Status']
			df_valor_total_categorias_download = df_valor_total_categorias[colunas].copy()
			df_valor_total_categorias = format_columns_brazilian(df_valor_total_categorias, ['Valor Total Evento', 'Valor Total Categorias', 'Diferença'])
			df_valor_total_categorias = df_format_date_columns_brazilian(df_valor_total_categorias, ['Data Evento'])
			if df_valor_total_categorias.empty:
				st.success("Nenhum evento com diferença de Valor Total Eventos e Valor Total de categorias.")
			else:
				st.dataframe(df_valor_total_categorias[colunas], width='stretch', hide_index=True)
				col1, col2 = st.columns([4, 1])
				with col2:
					button_download(df_valor_total_categorias_download, f"valor_total_categorias", f"valor_total_categorias")

	st.markdown("")
if __name__ == '__main__':
  main()