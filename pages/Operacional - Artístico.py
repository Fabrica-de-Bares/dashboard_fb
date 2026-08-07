import streamlit as st
import pandas as pd
from utils.queries_artistico import *
from utils.functions.general_functions import *
from utils.components import *
from datetime import date, datetime
from matplotlib.dates import relativedelta

st.set_page_config(
  layout = 'wide',
  page_title = 'Artístico',
  page_icon='🎵',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')

def dados_fabrica_eshows(data_inicio, data_fim):
  df_fabrica_faturamento_couvert = fabrica_faturamento_couvert(data_inicio, data_fim)
  df_eshows_custos = eshows_custos(data_inicio, data_fim)
  df_propostas_eshows = propostas_eshows(data_inicio, data_fim)

  df_merged = df_fabrica_faturamento_couvert.merge(df_eshows_custos, on=['Data Evento', 'Loja'], how='outer')
  df_merged.fillna(0, inplace=True)
  df_merged['Resultado'] = df_merged['Valor Liquido'] - df_merged['Valor Gasto']
  df_merged['Data Evento'] = pd.to_datetime(df_merged['Data Evento'], dayfirst=True)  # Certifica que é datetime
  df_merged = df_merged.sort_values(by='Data Evento', ascending=True)
  df_merged['Data Evento'] = df_merged['Data Evento'].dt.strftime('%d/%m/%Y')
  df_merged['Loja'] = df_merged['Loja'].replace(["0", 0], "")

  return df_fabrica_faturamento_couvert, df_eshows_custos, df_propostas_eshows, df_merged

def main():
  config_sidebar()
  col, col2, col3 = st.columns([6, 1, 1])
  with col:
    st.title('🎵 Artístico')
  with col2:
    st.button(label="Atualizar", on_click = st.cache_data.clear)
  st.divider()

  data_inicio = date(datetime.today().year, datetime.today().month, 1) - relativedelta(months=1)
  data_fim = date(datetime.today().year, datetime.today().month, 1) - relativedelta(days=1)


  st.markdown('## Lucro por Casa')
  st.divider()

  col1, col2 = st.columns([1, 4], vertical_alignment='top')
  with col1:
    data_range = st.date_input(
      'Selecione o período:',
      value=(data_inicio, data_fim),
      format='DD/MM/YYYY'
    )
  with col2:
    lista_casas_retirar = ['The Cavern']
    df_lojas_selecionadas = input_multiselecao_casas(lista_casas_retirar, key="casas_artistico")
    lojas_selecionadas = df_lojas_selecionadas['Casa'].to_list()
  st.divider()

  if len(lojas_selecionadas) == 0:
      st.warning('Nenhuma loja selecionada')
      st.stop()

  if len(data_range) == 2:
    data_inicio, data_fim = data_range

    num_meses_entre_datas = (data_fim.year - data_inicio.year) * 12 + (data_fim.month - data_inicio.month) + 1

    data_inicio_anterior = data_inicio - relativedelta(months=num_meses_entre_datas)
    data_fim_anterior = data_fim - relativedelta(months=num_meses_entre_datas)

    last_day_of_the_month = (data_fim.replace(day=1) + relativedelta(months=1, days=-1)).day
    if data_fim.day == last_day_of_the_month:
      data_fim_anterior = (data_fim_anterior.replace(day=1) + relativedelta(months=1, days=-1))

    # Calcula fatores do período escolhido
    df_fabrica_faturamento_couvert, df_eshows_custos, df_propostas_eshows, df_merged = dados_fabrica_eshows(data_inicio, data_fim)

    # Calcula fatores do período anterior
    df_fabrica_faturamento_couvert_anterior, df_eshows_custos_anterior, df_propostas_eshows_anterior, df_merged_anterior = dados_fabrica_eshows(data_inicio_anterior, data_fim_anterior)
    df_merged_anterior['Loja'] = df_merged_anterior['Loja'].replace(["0", 0], "")

    df_merged_filtrado = df_merged[df_merged['Loja'].isin(lojas_selecionadas)]
    if df_merged_filtrado.empty:
      st.warning('Sem dados encontrados para o período selecionado.')
      st.stop()
    df_merged_anterior_filtrado = df_merged_anterior[df_merged_anterior['Loja'].isin(lojas_selecionadas)]

    lucro_total = float(df_merged_filtrado['Resultado'].sum())
    lucro_total_anterior = float(df_merged_anterior_filtrado['Resultado'].sum())
    delta_lucro = float(lucro_total - lucro_total_anterior)
    delta_lucro_porcentagem = float((delta_lucro / lucro_total_anterior) * 100) if lucro_total_anterior != 0 else 0.0

    # Gráfico do st.metric
    df_chart = df_merged_filtrado.groupby('Data Evento').agg({'Resultado': 'sum'}).reset_index()
    df_chart.sort_values(by='Data Evento', inplace=True)
    chart_data = [float(v) for k, v in df_chart.to_dict()['Resultado'].items()]

    col1, col2, col3, col4 = st.columns([1.5, 2, 1, 0.5])
    with col2:
      st.metric('Lucro Total no Período',
                f'{f"R$ {lucro_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")}',
                f"{delta_lucro_porcentagem:,.2f} %".replace(",", "X").replace(".", ",").replace("X", "."),
                chart_data=chart_data,
                chart_type="area",
                border=True)
      
    col1, col2 = st.columns([4, 1], vertical_alignment='bottom')
    with col1:
      st.markdown('### Lucro Geral')
    with col2:
      button_download(df_merged_filtrado, f'lucro_{data_inicio}_{data_fim}', 'lucro_por_loja')
    dataframe_aggrid(df_merged_filtrado, name='Lucro por Loja', num_columns=['Valor Bruto', 'Desconto', 'Valor Liquido', 'Valor Gasto', 'Resultado'], fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW, fit_columns_on_grid_load=True, num_cel_style='monetary', num_columns_style=['Resultado'])

  col1, col2 = st.columns([4, 1], vertical_alignment='bottom')
  with col1:
    st.markdown('### Propostas Eshows')
  with col2:
    df_propostas_eshows = df_propostas_eshows[df_propostas_eshows['Loja'].isin(lojas_selecionadas)]
    button_download(df_propostas_eshows, f'propostas_{data_inicio}_{data_fim}', 'propostas_eshows')
  dataframe_aggrid(df_propostas_eshows, name='Propostas Eshows', num_columns=['Valor Bruto'], fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW, fit_columns_on_grid_load=True)


if __name__ == '__main__':
  main()
