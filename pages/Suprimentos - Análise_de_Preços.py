import streamlit as st
import pandas as pd
from utils.queries_compras import *
from utils.functions.compras_curva_abc import *
from utils.functions.general_functions import *
from utils.components import *

st.set_page_config(
  layout = 'wide',
  page_title = 'Análise de Preços',
  page_icon='💲',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')

def main ():
  config_sidebar()
  streamlit_style = """
    <style>
    iframe[title="streamlit_echarts.st_echarts"]{ height: 300px;} 
   </style>
    """
  st.markdown(streamlit_style, unsafe_allow_html=True)

  st.title('💲 Análise de Preços')

  dfComparativo = GET_COMPRAS_PRODUTOS_QUANTIA_NOME_COMPRA()

  tab1, tab2, tab3, tab4 = st.tabs(["COMPARATIVO ENTRE LOJAS", "ALIMENTOS", "BEBIDAS", " PRODUTOS DE LIMP/HIGIENE"])
  with tab1:
    comparativo_valor_mais_baixo(dfComparativo)
    comparativo_entre_lojas(dfComparativo)

  with tab2:
    dfNomeCompras, lojas, dfSemFiltroData, data_fim = config_tabela_para_pareto(dfComparativo, 'ALIMENTOS', 1)
    produto = config_diagramas_pareto(dfNomeCompras, 'ALIMENTOS', 'Alimentos')
    with st.container(border=True):
      dfNomeCompras = dfNomeCompras.drop(['Categoria'], axis=1)
      pesquisa_por_produto(dfNomeCompras, 1, data_fim, dfSemFiltroData, 'Grafico1', produto)
    with st.container(border=True):
      config_compras_insumos_detalhadas('ALIMENTOS', 'datainicio1', 'datafim1', 'insumosdetalhados1', lojas)

  with tab3:
    dfNomeCompras2, lojas2, dfSemFiltroData2, data_fim2 = config_tabela_para_pareto(GET_COMPRAS_PRODUTOS_QUANTIA_NOME_COMPRA(), 'BEBIDAS', 2)
    produto2 = config_diagramas_pareto(dfNomeCompras2, 'BEBIDAS', 'Bebidas')
    with st.container(border=True):
      dfNomeCompras2 = dfNomeCompras2.drop(['Categoria'], axis=1)
      pesquisa_por_produto(dfNomeCompras2, 2, data_fim2, dfSemFiltroData2, 'Grafico2', produto2)
    with st.container(border=True):
      config_compras_insumos_detalhadas('BEBIDAS', 'datainicio2', 'datafim2', 'insumosdetalhados2', lojas2)

  with tab4:
    dfNomeCompras3, lojas3, dfSemFiltroData3, data_fim3 = config_tabela_para_pareto(GET_COMPRAS_PRODUTOS_QUANTIA_NOME_COMPRA(), 'DESCARTAVEIS/HIGIENE E LIMPEZA', 3)
    produto3 = config_diagramas_pareto(dfNomeCompras3, 'DESCARTAVEIS/HIGIENE E LIMPEZA', 'Produtos de Limpeza e Higiene')
    with st.container(border=True):
      dfNomeCompras3 = dfNomeCompras3.drop(['Categoria'], axis=1)
      pesquisa_por_produto(dfNomeCompras3, 3, data_fim3, dfSemFiltroData3, 'Grafico3', produto3)
    with st.container(border=True):
      config_compras_insumos_detalhadas('DESCARTAVEIS/HIGIENE E LIMPEZA', 'datainicio3', 'datafim3', 'insumosdetalhados3', lojas3)



if __name__ == '__main__':
  main()

