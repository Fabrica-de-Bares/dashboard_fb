import streamlit as st
import pandas as pd
from utils.queries_financeiro import *
from utils.functions.financeiro_faturamento_zigpay import *
from utils.functions.general_functions import *
from utils.components import *

st.set_page_config(
  layout = 'wide',
  page_title = 'Faturamento Zigpay',
  page_icon='💰',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')

def main():
  config_sidebar()
  col, col2, col3 = st.columns([6, 1, 1])
  with col:
    st.title('💰 Faturamento Zigpay')
  with col2:
    st.button(label="Atualizar", on_click = st.cache_data.clear)
  st.divider()

  data_inicio_default, data_fim_default = get_first_and_last_day_of_month()

  # Seletores
  col1, col2, col3 = st.columns([2, 1, 1])
  with col1:
     # Filtro de casa:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Todas as Casas', 'Escritório Fabrica de Bares']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='calendario', adicionar_delivery=True)
    lojas_selecionadas = df_casas_selecionadas['Casa'].tolist()
  with col2:
    data_inicio = st.date_input(
        'Data de Início',
        value=data_inicio_default,
        key='data_inicio_input',
        format="DD/MM/YYYY"
    )
  with col3:
    data_fim = st.date_input(
        'Data de Fim',
        value=data_fim_default,
        key='data_fim_input',
        format="DD/MM/YYYY"
    )

    # Converte as datas selecionadas para o formato Timestamp
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

  st.divider()

  if lojas_selecionadas == []:
    st.warning("Nenhuma casa selecionada.")
    st.stop()
  OrcamentoFaturamento = config_orcamento_faturamento(lojas_selecionadas, data_inicio, data_fim) 
  orcamfatformatado = OrcamentoFaturamento.copy()
  categorias_desejadas = ['Alimentos', 'Bebidas', 'Couvert', 'Gifts']
  soma_valor_bruto = orcamfatformatado.loc[orcamfatformatado['Categoria'].isin(categorias_desejadas), 'Valor Bruto'].sum()
  soma_valor_bruto = format_brazilian(soma_valor_bruto)
  orcamfatformatado = format_columns_brazilian(orcamfatformatado, ['Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido', 'Faturam - Orçamento'])
  orcamfatformatado.loc[orcamfatformatado['Orçamento'] == '0,00', 'Atingimento %'] = '-'


  with st.container(border=True):
    col0, col1, col2 = st.columns([1, 10, 7])
    with col1:
      st.subheader("Faturamento Bruto")
      orcamfatformatadoStyled = orcamfatformatado.style.map(highlight_values, subset=['Faturam - Orçamento'])
      st.dataframe(orcamfatformatadoStyled, width=700, hide_index=True)
    with col2:
      st.subheader("Valores Líquidos:")
      Grafico_Donut(OrcamentoFaturamento)

    col0, col1 = st.columns([1, 17])
    with col1:
      st.write(f"Produtos vendidos na Zigpay. \n"
               f"Soma dos Valores Brutos de Alimentos, Bebidas, Couvert e Gifts: **R$ {soma_valor_bruto}**")
  
  st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)

  FaturamentoZig = config_Faturamento_zig(lojas_selecionadas, data_inicio, data_fim)

  # Formatação de datas
  FaturamentoZig = df_format_date_brazilian(FaturamentoZig, 'Data da Venda')

  with st.container(border=True):
    col0, col1, col2 = st.columns([1, 10, 1])
    with col1:
      col1, col2 = st.columns([6, 1], vertical_alignment='bottom')
      with col1:
        st.subheader("Top 10 Alimentos Vendidos:")
      with col2:
        st.markdown("*Sem delivery")
      top_dez(FaturamentoZig, 'Alimentos', key='top10alimentos')

  with st.container(border=True):
    col0, col1, col2 = st.columns([1, 10, 1])
    with col1:
      col1, col2 = st.columns([6, 1], vertical_alignment='bottom')
      with col1:
        st.subheader("Top 10 Bebidas Vendidas:")
      with col2:
        st.markdown("*Sem delivery")
      top_dez(FaturamentoZig, 'Bebidas', key='top10bebidas')

  with st.container(border=True):
    col0, col1, col2 = st.columns([1, 10, 1])
    with col1:
      col3, col4 = st.columns([6, 3])
      with col3:
        st.subheader("Faturamento por Categoria:")
      FaturamentoZigClasse = vendas_agrupadas_por_tipo(FaturamentoZig)

  classificacoes = obter_valores_unicos_ordenados(FaturamentoZig, 'Tipo')

  with st.container(border=True):
    col0, col1, col2 = st.columns([1, 10, 1])
    with col1:
      col3, col4 = st.columns([6, 3])
      with col3:
        st.subheader("Vendas de Produtos por Categoria:")
      with col4:
        classificacoes_selecionadas = st.multiselect(label='Selecione Classificações', options=classificacoes)
        FaturamentoZigClasse = filtrar_por_classe_selecionada(FaturamentoZig, 'Tipo', classificacoes_selecionadas)
      FaturamentoZigClasse = vendas_agrupadas(FaturamentoZigClasse)

  with st.container(border=True):  
    col0, col1, col2 = st.columns([1, 10, 1])
    with col1:
      st.subheader("Faturamento Por Dia:")
      st.markdown("*Sem delivery")
      faturam_por_dia(FaturamentoZig)

if __name__ == '__main__':
  main()
