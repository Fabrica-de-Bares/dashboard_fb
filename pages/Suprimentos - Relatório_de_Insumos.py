import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico_fichas_tecnicas import *
from utils.queries_compras import *
from datetime import date, datetime, timedelta
from utils.functions.suprimentos_relatorio_insumos import *

st.set_page_config(
	page_icon="📦",
	page_title="Relatório de Insumos - Suprimentos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	
	# Sidebar
	config_sidebar()
	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title("📦 Relatório de Insumos - Suprimentos")
	with col2:
		st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
	st.divider()
	
	inputs_expenses_base = inputs_expenses()

	# Seletores
	col1, col2 = st.columns(2)
	# Periodo
	with col1:
		# periodo = input_periodo_datas(key='data_inicio')
		today = get_today()
		first_day_this_month_this_year = get_first_day_this_month_this_year(today)
		last_day_this_month_this_year = get_last_day_this_month_this_year(today)
		periodo = st.date_input('Período',
					value=(first_day_this_month_this_year, last_day_this_month_this_year),
					min_value=get_jan_last_year(get_last_year(today)), # Janeiro do ano anterior
					format="DD/MM/YYYY",
					key='data_inicio'
                )
	
	if not periodo or len(periodo) < 2 or not periodo[0] or not periodo[1]:
		st.warning("Selecione um período válido antes de continuar.")
		st.stop()
	data_inicio = periodo[0]
	data_fim = periodo[1]
	
	# Validação de data
	if data_inicio > data_fim:
		st.warning('📅 Data Inicio deve ser menor que Data Final')
	else:
		inputsExpenses = inputs_expenses_base.copy()
		inputsExpenses = inputsExpenses[inputsExpenses['Data Competencia'].between(data_inicio, data_fim)]
		# Casas
		with col2:
			lista_casas_retirar = []
			df_companies_filtered = input_multiselecao_casas(lista_casas_retirar, 'casas_suprimentos')
			companies_filtered = df_companies_filtered['Casa'].to_list()
		st.divider()

		if len(companies_filtered) == 0:
				st.warning('Nenhuma loja selecionada')
				st.stop()

		inputsExpenses_filtered = inputsExpenses[inputsExpenses['Casa'].isin(companies_filtered)]
		inputs_expenses_base_casa = inputs_expenses_base[inputs_expenses_base['Casa'].isin(companies_filtered)]

		# Agrupa por Casa e Categoria
		inputsExpenses_n2 = (
			inputsExpenses_filtered.groupby(['Casa', 'Nivel 2'])[['Valor Insumo']]
			.sum().reset_index().sort_values(by=['Casa', 'Valor Insumo'], ascending=[True, False])
		)
		
		input_total_value = function_format_number_columns(valor=inputsExpenses_n2['Valor Insumo'].sum())  # valor total antes de formatar
		inputsExpenses_n2 = function_format_number_columns(inputsExpenses_n2, columns_money=['Valor Insumo'])

		# Agrupa por Categoria
		categoryN2_grafic = (
			inputsExpenses_filtered.groupby('Nivel 2')[['Valor Insumo']]
			.sum().reset_index().sort_values(by='Valor Insumo', ascending=False)
		)
		categoryN2_grafic['Percentual'] = (categoryN2_grafic['Valor Insumo'] / categoryN2_grafic['Valor Insumo'].sum() * 100).round(1)
		categoryN2_grafic['Label'] = categoryN2_grafic.apply(lambda x: f"{x['Nivel 2']} ({x['Percentual']}%)", axis=1)
			
		col2, col3 = st.columns([2, 3], vertical_alignment='top')
		with col2:
			with st.container(border=True, height=578):
				col21, col22, col23 = st.columns([1, 5, 1])
				with col22:
					st.markdown('#### Compra de Insumos - Categoria')
				dataframe_aggrid(inputsExpenses_n2, 'Insumos por Casa e Categoria', height=500)
		with col3:
			kpi_card_cmv_teorico('💰 Valor Total dos Insumos', input_total_value, background_color="#FFFFFF", title_color="#333", value_color="#000")
			st.write('')
			with st.container(border=True):
				col31, col32, col33 = st.columns([1, 5, 1])
				with col32:
					st.markdown(f'#### Gastos por Categoria - {data_inicio} a {data_fim}')
				component_plotPizzaChart(categoryN2_grafic['Label'], categoryN2_grafic['Valor Insumo'], 'Gastos por Categoria', 19)
		

		inputs_expenses_base_casa = (
			inputs_expenses_base_casa.groupby(['Casa', 'Nivel 2', 'Mês', 'Ano'])[['Valor Insumo']]
			.sum().reset_index().sort_values(by=['Casa', 'Ano', 'Mês'], ascending=[True, True, True])
		)
		ano_filtro_grafico = data_inicio.year
		inputs_expenses_base_casa_ano = inputs_expenses_base_casa[inputs_expenses_base_casa['Ano'] == ano_filtro_grafico]
		
		
		with st.container(border=True):
			grafico_valor_insumos_temporal(inputs_expenses_base_casa_ano, ano_filtro_grafico)
		st.markdown('---')

		# Filtro por categoria N2
		row_categoryN2 = st.columns([1, 1, 1])
		with row_categoryN2[1]:
			categorias_disponiveis = sorted(inputsExpenses_filtered['Nivel 2'].dropna().unique())
			categoryN2_selected = st.multiselect(
				'Selecione a(s) Categoria(s) (Nivel 2):',
				options=categorias_disponiveis,
				placeholder='Categorias'
			)
		if not categoryN2_selected:
			categoryN2_selected = categorias_disponiveis

		inputs_expenses_filtered_by_cat = inputsExpenses_filtered[inputsExpenses_filtered['Nivel 2'].isin(categoryN2_selected)]

		supplierExpenseN5 = supplier_expense_n5(data_inicio, data_fim)
		supplierExpenseN5 = supplierExpenseN5[supplierExpenseN5['Casa'].isin(companies_filtered)]
		supplierExpenseN5 = supplierExpenseN5[supplierExpenseN5['INSUMO N2'].isin(categoryN2_selected)]

		with st.container(border=True):
			# Gastos por fornecedor insumo N5
			col1, col2 = st.columns([1, 1], vertical_alignment='bottom')
			with col1:
				st.markdown('### Despesas por Fornecedor')
			with col2:
				supplierExpenseN5_selected = st.multiselect(
					'Selecione o(s) Fornecedor(es):',
					options=sorted(supplierExpenseN5['Fornecedor'].dropna().unique()),
					placeholder='Fornecedores'
				)
			
			if not supplierExpenseN5_selected:
				supplierExpenseN5_selected = supplierExpenseN5['Fornecedor'].dropna().unique()

			supplierExpenseN5_filtered = supplierExpenseN5[supplierExpenseN5['Fornecedor'].isin(supplierExpenseN5_selected)]
			supplierExpenseN5_filtered = function_format_number_columns(supplierExpenseN5_filtered, columns_money=['Valor Insumo', 'Valor Med Por Insumo'])

			
			dataframe_aggrid(supplierExpenseN5_filtered, 'Despesas por Fornecedor')
			function_copy_dataframe_as_tsv(supplierExpenseN5_filtered)

		# Insumos por Casa e Fornecedor
		col3, col4 = st.columns([1, 1])
		with col3:
			categoryN2_supplier_companies = (
				inputs_expenses_filtered_by_cat.groupby(['Casa', 'Fornecedor'])[['Valor Insumo']]
				.sum().reset_index().sort_values(by=['Casa', 'Valor Insumo'], ascending=[True, False])
			)
			categoryN2_supplier_companies = function_format_number_columns(categoryN2_supplier_companies, columns_money=['Valor Insumo'])

			st.markdown('### Insumos por Casa e Fornecedor')
			dataframe_aggrid(categoryN2_supplier_companies, 'Insumos por Casa e Fornecedor')
			function_copy_dataframe_as_tsv(categoryN2_supplier_companies)

		with col4:
			categoryN2_supplier = (
				inputs_expenses_filtered_by_cat.groupby('Fornecedor')[['Valor Insumo']]
				.sum().reset_index().sort_values(by='Valor Insumo', ascending=False)
			)
			categoryN2_supplier['Percentual'] = (categoryN2_supplier['Valor Insumo'] / categoryN2_supplier['Valor Insumo'].sum() * 100).round(1)
			categoryN2_supplier = function_format_number_columns(categoryN2_supplier, columns_money=['Valor Insumo'])
			categoryN2_supplier['Valor Gasto (R$)'] = categoryN2_supplier['Valor Insumo']
			st.markdown('### Compras Sem Pedido')
			st.dataframe(
				categoryN2_supplier[['Fornecedor', 'Valor Gasto (R$)', 'Percentual']],
				column_config={
					"Percentual": st.column_config.ProgressColumn("Percentual", format="%.1f%%", min_value=0, max_value=100)
				},
				hide_index=True
			)

		st.markdown('---')

		# Detalhamento por insumo
		categoryN2_inputs = (
			inputs_expenses_filtered_by_cat.groupby('Insumo')[['Valor Insumo', 'Quantidade Insumo']]
			.sum().reset_index()
		)
		categoryN2_inputs['Preco Medio'] = categoryN2_inputs['Valor Insumo'] / categoryN2_inputs['Quantidade Insumo']
		categoryN2_inputs['Percentual Repres'] = (categoryN2_inputs['Valor Insumo'] / categoryN2_inputs['Valor Insumo'].sum() * 100).round(1)
		categoryN2_inputs = categoryN2_inputs.sort_values(by='Valor Insumo', ascending=False)

		# Calcula preço médio mês anterior
		last_day_last_month = (datetime.today().replace(day=1) - pd.Timedelta(days=1)).date()
		first_day_last_month = last_day_last_month.replace(day=1)

		inputsExpenses2 = inputs_expenses_base.copy()
		categoryN2_inputs_last_month = inputsExpenses2[inputsExpenses2['Data Competencia'].between(first_day_last_month, last_day_last_month)]
		categoryN2_inputs_last_month = (
			categoryN2_inputs_last_month.groupby('Insumo')[['Valor Insumo', 'Quantidade Insumo']]
			.sum().reset_index()
		)
		categoryN2_inputs_last_month['Preco Medio Anterior'] = categoryN2_inputs_last_month['Valor Insumo'] / categoryN2_inputs_last_month['Quantidade Insumo']
		categoryN2_inputs_last_month = categoryN2_inputs_last_month[['Insumo', 'Preco Medio Anterior']]

		# Merge e variação percentual
		categoryN2_inputs_merged = categoryN2_inputs.merge(categoryN2_inputs_last_month, on='Insumo', how='left')
		categoryN2_inputs_merged['Variação Percentual'] = (
			(categoryN2_inputs_merged['Preco Medio'] - categoryN2_inputs_merged['Preco Medio Anterior'])
			/ categoryN2_inputs_merged['Preco Medio Anterior'] * 100
		)

		# Formatação
		categoryN2_inputs_merged = function_format_number_columns(
			categoryN2_inputs_merged,
			columns_money=['Valor Insumo', 'Preco Medio', 'Preco Medio Anterior'],
			columns_number=['Quantidade Insumo']
		)
		categoryN2_inputs_merged['Percentual Repres'] = categoryN2_inputs_merged['Percentual Repres'].map(lambda x: f"{x:.1f}%")
		categoryN2_inputs_merged['Variação Percentual'] = categoryN2_inputs_merged['Variação Percentual'].map(lambda x: f"{x:+.1f}%" if pd.notnull(x) else '-')
		categoryN2_inputs_merged_style = categoryN2_inputs_merged.style.map(function_highlight_percentage, subset=['Variação Percentual'], invert_color=True)
		
		st.markdown('### Detalhamento por Insumo')
		st.dataframe(categoryN2_inputs_merged_style, hide_index=True, width='stretch')
		function_copy_dataframe_as_tsv(categoryN2_inputs_merged)

		st.markdown('---')

		# Compras anuais por fornecedor e categoria (insumo N2)
		df_compras_anuais = GET_COMPRAS_POR_ANO()
		df_compras_anuais['Data Competencia'] = pd.to_datetime(df_compras_anuais['Data Competencia'], errors='coerce')

		with st.container(border=True):
			col1, col2 = st.columns([1, 1], vertical_alignment='bottom')
			with col1:
				st.markdown('### Compras por ano')
			with col2:
				ano = seletor_ano(2024, 2026, 'ano_compras', label='Selecionar ano', help=None)

			df_compras_anuais_filtrado = df_compras_anuais[
				df_compras_anuais['Casa'].isin(companies_filtered) &
				(df_compras_anuais['Data Competencia'].dt.year == ano)
			]
			df_compras_anuais_styled = df_compras_anuais_filtrado[['Casa', 'ID Fornecedor', 'Fornecedor', 'Insumo N2', 'ID Nivel 5', 'Insumo N5', 'Quantidade', 'Valor Total', 'Valor Médio por Insumo', 'Mês/Ano']]
			df_compras_anuais_styled = function_format_number_columns(
				df_compras_anuais_styled,
				columns_money=['Valor Total', 'Valor Médio por Insumo'],
			)
			df_compras_anuais_styled.sort_values(by=['Casa', 'Mês/Ano', 'Insumo N2', 'Fornecedor'], inplace=True)

			st.dataframe(df_compras_anuais_styled, hide_index=True, width='stretch')
			function_copy_dataframe_as_tsv(df_compras_anuais_filtrado)


if __name__ == '__main__':
	main()
