import streamlit as st
import pandas as pd
from utils.queries_produto import *
from utils.functions.general_functions import *
from utils.components import *
from utils.components import *
from utils.user import logout
from utils.functions.api_zigpay import *
from utils.queries_produto import *

st.set_page_config(
	layout="wide",
	page_title="Análise de Consumo",
	page_icon="🍴",
	initial_sidebar_state="collapsed"
)
pd.set_option("future.no_silent_downcasting", True)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
	st.switch_page("Login.py")

config_sidebar()


col, col2, col3 = st.columns([6, 1, 1])
with col:
	st.title("🍴 Análise de Consumo")
with col2:
	st.button(label="Atualizar", on_click=st.cache_data.clear)

seletores_container = st.container(border=True)
with seletores_container:
	col1, col2, col3 = st.columns([2, 1, 1])
	with col1:
		# Seleção da casa
		lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless', 'Todas as Casas']
		id_casa, casa, id_zigpay = input_selecao_casas(
			lista_retirar_casas, key="seletor_casa_analise_consumo"
        )
	with col2:
		# Seleção do mês
		nome_mes, num_mes = seletor_mes_produtos(key="seletor_mes_analise_consumo")
	with col3:
		# Seleção do ano
		ano = seletor_ano(2025, 2026, key="seletor_ano_analise_consumo")

# Obtendo os dados de transações e compradores
df_transacoes = GET_TRANSACOES_PERIODO_HORARIO_DIA_DA_SEMANA(id_casa)
df_compradores_zig = df_compradores_zigpay_mes(num_mes, ano, id_zigpay)

# Filtrando os dados de transações para o mês e ano selecionados
df_transacoes = df_transacoes[
	(df_transacoes["Ano"] == ano) & (df_transacoes["Mes"] == nome_mes)
]

# Limpa colunas desnecessárias
df_transacoes = df_transacoes[['Data Transacao', 'ID Transacao', 'Produto', 'Valor Unitario', 'Quantidade', 'Periodo Dia', 'Dia Semana']]
df_compradores_zig = df_compradores_zig[['userDocument', 'userName', 'transactionId']]

# Merge dos dados de transações com os dados de compradores
df_transacoes_compradores = df_transacoes.merge(
	df_compradores_zig, left_on="ID Transacao", right_on="transactionId", how="left"
)

# Seletor do produto
opcoes_produtos = df_transacoes_compradores["Produto"].unique().tolist()
opcoes_produtos = sorted(opcoes_produtos)
produto_selecionado = seletores_container.selectbox(
	"Selecione o produto", opcoes_produtos, key="seletor_produto_analise_consumo"
)

# Filtro do produto selecionado
df_produto_selecionado_compradores = df_transacoes_compradores[
	df_transacoes_compradores["Produto"] == produto_selecionado
]

# Compradores do produto selecionado
lista_compradores_produto_selecionado = (
	df_produto_selecionado_compradores["userDocument"].unique().tolist()
)

# Transações com o produto selecionado
lista_transacoes_produto_selecionado = (
	df_produto_selecionado_compradores["ID Transacao"].unique().tolist()
)

# Produtos comprados pelos compradores do produto selecionado
df_produtos_comprador = df_transacoes_compradores[
	df_transacoes_compradores["userDocument"].isin(lista_compradores_produto_selecionado)
]
# Retira coluna duplicada (transactionId)
df_produtos_comprador = df_produtos_comprador[['ID Transacao', 'Data Transacao', 'Produto', 'Valor Unitario', 'Quantidade', 'userDocument', 'userName', 'Periodo Dia']]

# Todas as transações dos compradores do produto selecionado
lista_transacoes_compradores_produto_selecionado = (
	df_produtos_comprador["ID Transacao"].unique().tolist()
)

# Dataframe que mostra os compradores do produto selecionado
df_produto_selecionado_compradores = df_produto_selecionado_compradores[['Data Transacao', 'Produto', 'userDocument', 'userName', 'Periodo Dia']]

# Dataframe que relaciona a data da venda dos produtos com a data de venda do produto selecionado
df_produtos_comprados_no_dia = df_produtos_comprador.merge(df_produto_selecionado_compradores, on=['userDocument', 'Data Transacao'], how='inner')
df_produtos_comprados_no_dia = df_produtos_comprados_no_dia.drop_duplicates(subset=['ID Transacao', 'Produto_x'])
df_produtos_comprados_no_dia = df_produtos_comprados_no_dia[['ID Transacao', 'Data Transacao', 'Produto_x', 'Valor Unitario', 'Quantidade', 'userDocument', 'userName_x', 'Periodo Dia_x']]
lista_transacoes_compradores_dia = df_produtos_comprados_no_dia['ID Transacao'].unique().tolist()

df_produtos_comprados_no_dia_e_periodo = df_produtos_comprador.merge(df_produto_selecionado_compradores, on=['userDocument', 'Data Transacao', 'Periodo Dia'], how='inner')
df_produtos_comprados_no_dia_e_periodo = df_produtos_comprados_no_dia_e_periodo.drop_duplicates(subset=['ID Transacao', 'Produto_x'])
df_produtos_comprados_no_dia_e_periodo = df_produtos_comprados_no_dia_e_periodo[['ID Transacao', 'Data Transacao', 'Produto_x', 'Valor Unitario', 'Quantidade', 'userDocument', 'userName_x', 'Periodo Dia']]

lista_transacoes_compradores_dia_e_periodo = df_produtos_comprados_no_dia_e_periodo['ID Transacao'].unique().tolist()

if produto_selecionado:
	# Números de transações e compradores
	col1, col4, col5 = st.columns([1, 1, 1])
	with col4:
		with st.container(border=True):
			st.write(
				f"N.º de clientes que compraram {produto_selecionado}:"
			)
			st.write(f"{len(lista_compradores_produto_selecionado)}")

# Top produtos mais comprados junto com o produto selecionado (por dia)
df_top_produtos_dia = df_produtos_comprados_no_dia.groupby('Produto_x').agg({
	'Valor Unitario': 'first',
	'Produto_x': 'count',
	'Quantidade': 'sum'
}).rename(columns={
	'Produto_x': 'Número de Transações',
	'Valor Unitario': 'Valor Unitário (R$)',
	'Quantidade': 'Quantidade de Vendas'
}).reset_index().rename(columns={'Produto_x': 'Produto'})
df_top_produtos_dia = df_top_produtos_dia[df_top_produtos_dia['Produto'] != produto_selecionado]

# Top produtos mais comprados junto com o produto selecionado (por dia e período)
df_top_produtos_dia_e_periodo = df_produtos_comprados_no_dia_e_periodo.groupby('Produto_x').agg({
	'Valor Unitario': 'first',
	'Produto_x': 'count',
	'Quantidade': 'sum'
}).rename(columns={
	'Produto_x': 'Número de Transações',
	'Valor Unitario': 'Valor Unitário (R$)',
	'Quantidade': 'Quantidade de Vendas'
}).reset_index().rename(columns={'Produto_x': 'Produto'})
df_top_produtos_dia_e_periodo = df_top_produtos_dia_e_periodo[df_top_produtos_dia_e_periodo['Produto'] != produto_selecionado]

with st.container(border=True):
	st.markdown(
		f"### Produtos mais comprados junto com {produto_selecionado}:"
	)
	st.dataframe(df_top_produtos_dia_e_periodo, width='stretch', hide_index=True)

with st.container(border=True):
	st.markdown(
		f"### Produtos mais comprados no mesmo dia que {produto_selecionado} (podem ser em horários diferentes):"
	)
	st.dataframe(df_top_produtos_dia, width='stretch', hide_index=True)

with st.expander(f"Produtos comprados na mesma refeição que {produto_selecionado}: {len(df_produtos_comprados_no_dia_e_periodo)}"):
	st.write(r"\* Compras efetuadas dentro de um mesmo momento de consumo (Almoço, Jantar, Happy Hour, Madrugada etc)")
	st.dataframe(df_produtos_comprados_no_dia_e_periodo, width='stretch', hide_index=True)

with st.expander(
	f"Produtos comprados no mesmo dia que {produto_selecionado}: {len(df_produtos_comprados_no_dia)}"):
	st.dataframe(df_produtos_comprados_no_dia, width='stretch', hide_index=True)

with st.expander(
	f"Produtos comprados no mês pelos compradores de {produto_selecionado}: {len(df_produtos_comprador)}"
):
	st.dataframe(df_produtos_comprador, width='stretch', hide_index=True)

with st.expander(
	f"N.º de Transações com {produto_selecionado}: {len(df_produto_selecionado_compradores)}"
):
	st.dataframe(
		df_produto_selecionado_compradores[['Produto', 'userDocument', 'userName', 'Data Transacao', 'Periodo Dia']], width='stretch', hide_index=True)
