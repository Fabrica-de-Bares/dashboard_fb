from datetime import timedelta
import streamlit as st
import pandas as pd
from utils.queries_fluxo_de_caixa import *
from utils.functions.general_functions import *
from utils.components import *
from utils.functions.fluxo_de_caixa_previsao_faturamento import *
from workalendar.america import Brazil
from streamlit_echarts import st_echarts
from datetime import datetime


st.set_page_config(
    page_title="Previsão de Faturamento",
    page_icon="🪙",
    layout="wide"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

col, col2, col3 = st.columns([6, 1, 1])
with col:
  st.title('🪙 Previsão de Faturamento')
with col2:
  st.button(label="Atualizar", on_click = st.cache_data.clear)

config_sidebar()
st.divider()

dfPrevisoes = GET_PREVISOES_ZIG_AGRUPADAS()
dfPrevisoes['Data'] = pd.to_datetime(dfPrevisoes['Data'])
df_parciais = criar_parciais(dfPrevisoes)
df_parciais = df_parciais.loc[:,~df_parciais.columns.duplicated()]
df_unificado = unificar_parciais(df_parciais)


# Filtre os dados com base no intervalo de datas
grouped_df = df_unificado.groupby(['Data_Parcial', 'Empresa'], as_index=False).agg({'Valor_Parcial': 'sum'})
sorted_df = grouped_df.sort_values(by=['Data_Parcial', 'Empresa'])

# lojasComDados = preparar_dados_lojas_user_financeiro()
data_inicio_default = datetime.today() - timedelta(days=8)
data_fim_default = datetime.today() - timedelta(days=2)

# Seletores
lojasSelecionadas, checkbox_agrupa, multiplicador, data_inicio, data_fim = criar_seletores_previsao(data_inicio_default, data_fim_default)
st.divider()

if lojasSelecionadas == []:
  st.warning('Nenhuma casa selecionada')
  st.stop()

sorted_df.rename(columns = {'Empresa': 'Loja', 'Data_Parcial': 'Data', 'Valor_Parcial': 'Valor Projetado'}, inplace=True)
faturamentoReal = GET_FATURAMENTO_REAL()

faturamentoReal['Data'] = pd.to_datetime(faturamentoReal['Data'])
sorted_df['Data'] = pd.to_datetime(sorted_df['Data'])

dfComparacao = sorted_df.merge(faturamentoReal, on=['Data', 'Loja'], how='outer')
dfComparacao = filtrar_por_datas(dfComparacao, data_inicio, data_fim, 'Data')
dfComparacao = dfComparacao[dfComparacao['Loja'] != 'Piratininga']

dfComparacao = filtrar_por_classe_selecionada(dfComparacao, 'Loja', lojasSelecionadas)
if checkbox_agrupa:
  dfComparacao = dfComparacao.groupby('Data', as_index=False)[['Valor Projetado', 'Valor_Faturado']].sum()
  dfComparacao['Loja'] = 'Agrupamento'
else:
  dfComparacao = dfComparacao.copy()
 
dfComparacao.rename(columns = {'Valor_Faturado': 'Valor Faturado'}, inplace=True)
dfComparacao['Valor Projetado'] = dfComparacao['Valor Projetado'].fillna(0)
dfComparacao['Valor Faturado'] = dfComparacao['Valor Faturado'].fillna(0)

dfComparacao['Valor Projetado'] = dfComparacao['Valor Projetado'].astype(float)
dfComparacao['Valor Faturado'] = dfComparacao['Valor Faturado'].astype(float)
dfComparacao['Valor Projetado'] = dfComparacao['Valor Projetado'] * multiplicador

dfComparacao['Diferença'] = dfComparacao['Valor Faturado'] - dfComparacao['Valor Projetado']

dfComparacao['Atingimento do Projetado'] = (dfComparacao['Valor Faturado'] / dfComparacao['Valor Projetado'])
dfComparacao['Atingimento do Projetado'] = dfComparacao['Atingimento do Projetado']


dfComparacao2 = dfComparacao.copy()

dfComparacaoAgg = dfComparacao.groupby('Loja').agg({
  'Valor Projetado': 'sum',
  'Valor Faturado': 'sum',
}).reset_index()
dfComparacaoAgg['Diferença'] = dfComparacaoAgg['Valor Faturado'] - dfComparacaoAgg['Valor Projetado']



dfComparacao = df_format_date_brazilian(dfComparacao, 'Data')
dfComparacao = format_columns_brazilian(dfComparacao, ['Valor Projetado', 'Valor Faturado', 'Diferença'])
dfComparacao = dfComparacao[['Data', 'Loja', 'Valor Projetado', 'Valor Faturado', 'Diferença', 'Atingimento do Projetado']]
dfComparacaoStyled = dfComparacao.style.map(highlight_values, subset=['Diferença'])
dfComparacaoAgg = format_columns_brazilian(dfComparacaoAgg, ['Valor Projetado', 'Valor Faturado', 'Diferença'])
altura_dfComparacaoAgg = len(dfComparacaoAgg)
dfComparacaoAggStyled = dfComparacaoAgg.style.map(highlight_values, subset=['Diferença'])




with st.container(border=True):
  col, col1, col2 = st.columns([1, 8, 1])
  with col1:
    st.subheader('Previsão de Faturamento x Realizado')
    st.dataframe(
        dfComparacaoStyled,
        column_config={
            'Atingimento do Projetado': st.column_config.ProgressColumn(
                "Atingimento do Projetado",
                format='percent',
                min_value=0,
                max_value=1,
            )
        },
        hide_index=True
    )



with st.container(border=True):
  col, col1, col2 = st.columns([1, 8, 1])
  with col1:
    st.subheader('Faturamento Acumulado do Período')
    st.dataframe(dfComparacaoAggStyled, width='stretch', hide_index=True, height= altura_dfComparacaoAgg * 35 + 35)
    



def grafico_previsao_faturamento(df):
  dfComparacaoAgg = df.groupby('Data').agg({
    'Valor Projetado': 'sum',
    'Valor Faturado': 'sum'
  }).reset_index()

  dfComparacaoAgg = df_format_date_brazilian(dfComparacaoAgg, 'Data')
  dfComparacaoAgg['Valor Projetado'] = dfComparacaoAgg['Valor Projetado'].astype(float)
  dfComparacaoAgg['Valor Faturado'] = dfComparacaoAgg['Valor Faturado'].astype(float)

  # Prepare os dados para o gráfico
  dates = dfComparacaoAgg['Data'].tolist()
  faturamento = dfComparacaoAgg['Valor Faturado'].tolist()
  valor_previsto = dfComparacaoAgg['Valor Projetado'].tolist()

  option = {
    'title': {
        'text': ' '
    },
    'tooltip': {
        'trigger': 'axis'
    },
    'legend': {
        'data': ['Valor Faturado', 'Valor Projetado']
    },
    'xAxis': {
        'type': 'category',
        'data': dates,
        'axisLabel': {
            # 'interval': 1,  # Ajuste conforme a quantidade de dados para evitar sobrecarga
            'rotate': 45
        }
    },
    'yAxis': {
        'type': 'value'
    },
    'series': [
        {
            'name': 'Valor Faturado',
            'type': 'line',
            'data': faturamento
        },
        {
            'name': 'Valor Projetado',
            'type': 'line',
            'data': valor_previsto
        }
    ]
  }

  # Exibe o gráfico no Streamlit
  st_echarts(options=option, width=1000)
  return



with st.container(border=True):
  col, col1, col2 = st.columns([1, 8, 1])
  with col1:
    st.subheader('Valores Projetado vs Faturado por Dia')
  col, col1, col2 = st.columns([1, 8, 1])
  with col1:
    grafico_previsao_faturamento(dfComparacao2)
