import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.planejamento_anual import *
from utils.functions.forecast import highlight_titulos_dre
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.components import button_download, seletor_ano, input_selecao_casas
from utils.queries_controladoria import *


pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Orçamento Operacional",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("💰 Orçamento Operacional")
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
    
with col2:
    ano = seletor_ano(2025, 2026, 'ano')
st.divider()


df_orcamento_operacional = GET_ORCAMENTO_OPERACIONAL()
df_orcamento_filtrado = df_orcamento_operacional[
    (df_orcamento_operacional['Casa'] == casa) &
    (df_orcamento_operacional['Ano'] == ano)
].copy()
df_orcamento_filtrado.drop(columns=['Ano', 'ID Casa'], inplace=True)

# Nomeia meses
mapa_meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
df_orcamento_filtrado["Mês"] = df_orcamento_filtrado["Mês"].map(mapa_meses)

# Transforma meses em colunas
df_orcamento_pivot = df_orcamento_filtrado.pivot_table(
    index=["Casa", "Classificação Contábil 1", "Classificação Contábil 2"], 
    columns="Mês",
    values="Orçamento",
    aggfunc="sum"
).reset_index()

for col in df_orcamento_pivot.columns:
    if col not in ["Classificação Contábil 1", "Classificação Contábil 2"]:
        df_orcamento_pivot[col] = pd.to_numeric(df_orcamento_pivot[col], errors='coerce').fillna(0)


lista_categorias_orcamento = [
    'Faturamento Bruto',
    'Desconto sobre Venda',
    'Impostos sobre Venda',
    'Custo Mercadoria Vendida',
    'Custos Artístico Geral',
    'Custos de Eventos',
    'Gorjeta',
    'Deduções sobre Venda',
    'Mão de Obra - PJ',
    'Mão de Obra - Salários',
    'Mão de Obra - Extra',
    'Mão de Obra - Encargos e Provisões',
    'Mão de Obra - Benefícios',
    'Custo de Ocupação',
    'Utilidades',
    'Informática e TI',
    'Manutenção', # Despesas Gerais
    'Marketing',
    'Serviços de Terceiros',
    'Locação de Equipamentos',
    'Sistema de Franquias',
    'Patrocínio'
]

lista_df_orcamentos = []
lista_df_orcamentos = loop_prepara_dados_despesas(lista_categorias_orcamento, df_orcamento_pivot, lista_df_orcamentos)
df_orcamentos_concatenados = pd.concat(lista_df_orcamentos, ignore_index=True)
df_orcamentos_concatenados = df_orcamentos_concatenados[['Classificação Contábil 2', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']]
df_orcamentos_concatenados.rename(columns={'Classificação Contábil 2': 'Categoria'}, inplace=True)

# Formata colunas numéricas
df_orcamentos_concatenados = function_format_number_columns(
    df_orcamentos_concatenados,
    columns_money=[col for col in df_orcamentos_concatenados if col != 'Categoria'],
)

# Destaca linhas de título
df_orcamentos_concatenados_styled = df_orcamentos_concatenados.style.apply(highlight_titulos_dre, axis=1) 
height = (len(df_orcamentos_concatenados) + 1) * 35 # Define altura sem rolagem
st.dataframe(df_orcamentos_concatenados_styled, hide_index=True, width='stretch', height=height)
