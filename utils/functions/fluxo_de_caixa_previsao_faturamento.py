import streamlit as st
import pandas as pd
import numpy as np
from utils.queries_fluxo_de_caixa import *
from utils.components import *
from utils.functions.general_functions import *


# Função para criar os dados parciais
def criar_parciais(df):
  df_parciais = pd.DataFrame()
  for i in range(1, 5):
    parcial = df.copy()
    parcial['Valor'] = parcial['Valor'].astype(float)
    parcial['Data_Parcial'] = parcial['Data'] + pd.DateOffset(days=7 * i)
    parcial['Valor_Parcial'] = (parcial['Valor'] / 4).round(2)
    parcial = parcial.rename(columns={'Data_Parcial': f'Data_Parcial_{i}', 'Valor_Parcial': f'Valor_Parcial_{i}'})
    df_parciais = pd.concat([df_parciais, parcial[['Empresa', f'Data_Parcial_{i}', f'Valor_Parcial_{i}']]], axis=1)

  for i in range(1, 5):
    df_parciais[f'Data_Parcial_{i}'] = pd.to_datetime(df_parciais[f'Data_Parcial_{i}'])

  return df_parciais

def criar_seletores_previsao(data_inicio_default, data_fim_default):
  col1, col2 = st.columns(2, vertical_alignment='bottom')
  # col1, col2, col3, col4 = st.columns([4, 1, 2, 2])

  # Adiciona seletores
  with col1:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless']
    df_casas_selecionadas = input_multiselecao_casas(lista_retirar_casas, key='calendario')
    lojas_selecionadas = df_casas_selecionadas['Casa'].tolist()
  with col2:
    checkbox_agrupa = st.checkbox(label="Agrupar casas selecionadas", key="checkbox_agrupa_lojas_selecionadas")

  st.write("")
  col1, col2, col3 = st.columns([2, 2, 1], vertical_alignment='bottom')
  with col1:
    data_inicio = st.date_input('Data de Início', value=data_inicio_default, key='data_inicio_input', format="DD/MM/YYYY")
  with col2:
    data_fim = st.date_input('Data de Fim', value=data_fim_default, key='data_fim_input', format="DD/MM/YYYY")
  with col3:
    multiplicador = st.number_input("Multiplicador", value=1.0)


  # Converte as datas selecionadas para o formato Timestamp
  data_inicio = pd.to_datetime(data_inicio)
  data_fim = pd.to_datetime(data_fim)
  return lojas_selecionadas, checkbox_agrupa, multiplicador, data_inicio, data_fim

def unificar_parciais(df):
  dfs = {}

# Iterar sobre o intervalo e criar DataFrames
  for i in range(1, 5):
    dfs[i] = pd.DataFrame({
        'Empresa': df['Empresa'],
        'Data_Parcial': df[f'Data_Parcial_{i}'],
        'Valor_Parcial': df[f'Valor_Parcial_{i}']
    })

  # Converter o dicionário em uma lista de DataFrames, se necessário
  dfs_list = [dfs[i] for i in range(1, 5)]

  # Concatene todos os DataFrames temporários em um único DataFrame
  result_df = pd.concat(dfs_list, ignore_index=True)

  return result_df


