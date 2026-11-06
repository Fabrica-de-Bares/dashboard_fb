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
from utils.functions.faturamento import *
from utils.functions.gazit import *
from utils.user import *
import math
from utils.queries_gazit import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Auditoria Externa - Gazit - Shopping Light",
	page_icon="🛍️",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	st.markdown(" <style>iframe{ height: 300px !important } ", unsafe_allow_html=True)

	config_sidebar()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_E_ADITIVOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

	df_eventos = df_eventos[
		(df_eventos['Valor Locação Aroo 1'] > 0) |
		(df_eventos['Valor Locação Aroo 2'] > 0) |
		(df_eventos['Valor Locação Aroo 3'] > 0) |
		(df_eventos['Valor Locação Anexo'] > 0)
	]
	# Formata tipos de dados do dataframe de eventos
	tipos_de_dados_eventos = {
		'Valor Locação Aroo 1': float,
		'Valor Locação Aroo 2': float,
		'Valor Locação Aroo 3': float,
		'Valor Locação Anexo': float,
		'Valor Locação Notie': float,
		'Valor Locação Bar': float,
		'Valor Locação Mirante': float,
		'Valor Imposto': float,
		'Valor AB': float,
		'Valor Total Evento': float,
		'Valor Total Locação': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')

	# Fillna em colunas de valores monetários
	df_eventos.fillna({
    'Valor Locação Aroo 1': 0,
    'Valor Locação Aroo 2': 0,
    'Valor Locação Aroo 3': 0,
    'Valor Locação Anexo': 0,
    'Valor Locação Notie': 0,
	'Valor Locação Bar': 0,
    'Valor Locação Mirante': 0,
    'Valor Imposto': 0,
    'Valor AB': 0,
    'Valor Total Evento': 0,
    'Valor Total Locação': 0
	}, inplace=True)

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor Parcela': float,
		'Categoria Parcela': str
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')

	# Adiciona coluna de concatenação de ID e Nome Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID Evento'].astype(str) + " - " + df_eventos['Nome Evento']

	# Calcula o valor de repasse para Gazit
	df_eventos = calcular_repasses_gazit(df_eventos)

	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title("🛍️ Auditoria Externa - Gazit - Shopping Light")
	with col2:
		st.button(label='Atualizar', key='atualizar_gazit', on_click=st.cache_data.clear)
	st.divider()

	# Seletor de ano
	col1, col2 = st.columns([1, 1])
	with col1:
		st.markdown('## Faturamento de Eventos')
	with col2:
		ano = seletor_ano(2024, 2026, key='ano_faturamento')
	st.divider()

	df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas, df_eventos)

	df_parcelas_vencimento = df_filtrar_ano(df_parcelas, 'Data Vencimento', ano)
	df_parcelas_recebimento = df_filtrar_ano(df_parcelas, 'Data Recebimento', ano)

	# Formata colunas de eventos
	df_eventos = df_format_date_columns_brazilian(df_eventos, ['Data Contratação', 'Data Evento'])

	# Repasses Gazit #
 
	tab1, tab2 = st.tabs(["Projeção por Vencimento", "Valor Realizado (R$)"])
	with tab1:
		# Gráfico de barras de Faturamento Bruto por mês, ver exemplo do faturamento por dia do dash da Luana
		st.markdown("### Projeção por Vencimento")

		mes_vencimento = grafico_barras_repasse_mensal_vencimento(df_parcelas_vencimento)

		if mes_vencimento != None:
			st.markdown("#### Parcelas")
				
			# Filtra parcelas pelo mês da Data Vencimento
			df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data Vencimento', mes_vencimento)

			# Drop colunas desnecessárias
			df_parcelas_vencimento.drop(columns=['Mes', 'Ano', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Total Locação', 'ID Casa', 'Casa'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_vencimento = df_formata_datas_sem_horario(df_parcelas_vencimento, ['Data Vencimento', 'Data Recebimento'])

			# Formatacao de colunas
			df_parcelas_vencimento = rename_colunas_parcelas(df_parcelas_vencimento)
			df_parcelas_vencimento = format_columns_brazilian(df_parcelas_vencimento, ['Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit'])
			df_eventos_vencimento = format_columns_brazilian(df_eventos, ['Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Locacao Total Aroos'])

			df_eventos_vencimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_vencimento['ID Evento'])]
			df_eventos_vencimento = df_eventos_vencimento[df_eventos_vencimento['Status Evento'].isin(['Em negociação', 'Confirmado'])]

			df_parcelas_vencimento = df_parcelas_vencimento[df_parcelas_vencimento['ID Evento'].isin(df_eventos_vencimento['ID Evento'])]

			# Ordem das colunas
			df_parcelas_vencimento = df_parcelas_vencimento[['ID Evento', 'Nome Evento', 'ID Parcela', 'Categoria Parcela', 'Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Data Vencimento', 'Data Recebimento', 'Status Pagamento', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit']]  # nova ordem
			st.dataframe(df_parcelas_vencimento, width='stretch', hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_vencimento = df_eventos_vencimento.drop(columns=['ID_Nome_Evento', 'Motivo Declínio', 'Observações', 'Status Evento'])
			df_eventos_vencimento = df_eventos_vencimento[['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo']]
			df_eventos_vencimento = format_columns_brazilian(df_eventos_vencimento, ['Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo'])
			st.dataframe(df_eventos_vencimento, width='stretch', hide_index=True)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")

	with tab2:
		st.markdown("### Valor Realizado (R$)")

		mes_recebimento = grafico_barras_repasse_mensal_recebimento(df_parcelas_recebimento)

		if mes_recebimento != None:
			st.markdown("#### Parcelas")

			# Filtra parcelas pelo mês da Data Recebimento
			df_parcelas_recebimento = df_filtrar_mes(df_parcelas_recebimento, 'Data Recebimento', mes_recebimento)
			# Drop colunas desnecessárias
			df_parcelas_recebimento.drop(columns=['Mes', 'Ano', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Total Locação', 'ID Casa'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data Vencimento', 'Data Recebimento'])

			# Formatacao de colunas
			df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)

			total_recebimento_aroo = df_parcelas_recebimento['Valor Parcela AROO'].sum()
			total_recebimento_anexo = df_parcelas_recebimento['Valor Parcela ANEXO'].sum()

			df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit'])

			df_parcelas_recebimento = df_parcelas_recebimento[['ID Evento', 'Nome Evento', 'ID Parcela', 'Categoria Parcela', 'Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Data Vencimento', 'Data Recebimento', 'Status Pagamento', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit']]  # nova ordem
			st.dataframe(df_parcelas_recebimento, width='stretch', hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_recebimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_recebimento['ID Evento'])]
			df_eventos_recebimento = df_eventos_recebimento.drop(columns=['ID_Nome_Evento', 'Motivo Declínio', 'Observações', 'Status Evento'])
			df_eventos_recebimento = df_eventos_recebimento[['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo']]
			df_eventos_recebimento = format_columns_brazilian(df_eventos_recebimento, ['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo'])
			st.dataframe(df_eventos_recebimento, width='stretch', hide_index=True)

			# Tabela Gazit
			st.markdown("#### Resumo de Vendas - Gazit")

			total_de_vendas = total_recebimento_anexo * 0.3 + total_recebimento_aroo * 0.7
			retencao_impostos = math.floor(total_de_vendas * 0.1453 * 100) / 100
			# retencao_impostos = total_de_vendas * 0.1453
			valor_liquido_a_pagar = total_de_vendas - retencao_impostos

			resumo_vendas_gazit(total_de_vendas, retencao_impostos, valor_liquido_a_pagar, total_recebimento_anexo, total_recebimento_aroo)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")
	st.divider()

	col1, col2 = st.columns(2)
	with col1:
		st.markdown('## Faturamento de Produtos Vendidos')
	with col2:
		data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
		date = st.date_input(
			'Selecione o período',
			value = (data_inicio_default, data_fim_default),
			key = 'periodo_datas',
			min_value = datetime.datetime(2022, 1, 1),
			max_value = 'today',
			format = 'DD/MM/YYYY'
		)
	st.divider()
	
	if len(date) == 2:
		data_inicio = date[0]
		data_fim = date[1]
		df_faturamento_notie = GET_FATURAMENTO_NOTIE(data_inicio, data_fim)
		
		cols_to_convert = ['Preço', 'Quantidade', 'Desconto', 'Valor Total']
		for col in cols_to_convert:
			df_faturamento_notie[col] = pd.to_numeric(df_faturamento_notie[col], errors='coerce')

		df_faturamento_notie_formatado = df_format_date_columns_brazilian(df_faturamento_notie, ['Data'])
		df_faturamento_notie_formatado = format_columns_brazilian(df_faturamento_notie, ['Preço', 'Quantidade', 'Desconto','Valor Total'])

		col1, col2 = st.columns([6, 1], vertical_alignment='bottom')
		with col1:
			valor_total = df_faturamento_notie['Valor Total'].sum()
			total_str = format_brazilian(valor_total)
			st.markdown(f'**Valor Total no período: R$ {total_str}**')
		with col2:
			button_download(df_faturamento_notie, 'faturamento_notie', f'{data_inicio}_{data_fim}')
		st.dataframe(df_faturamento_notie_formatado, hide_index=True)
	


if __name__ == '__main__':
    main()