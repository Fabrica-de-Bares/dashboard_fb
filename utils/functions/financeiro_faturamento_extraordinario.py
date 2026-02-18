import pandas as pd
from utils.functions.general_functions import *
from utils.queries_financeiro import *
from utils.components import *


def config_receit_extraord(lojas_selecionadas, data_inicio, data_fim):
  df = GET_RECEIT_EXTRAORD()

  classificacoes = obter_valores_unicos_ordenados(GET_CLSSIFICACAO(), 'Classificacao')
  df = df[df['Classificacao'].isin(classificacoes)]

  df = filtrar_por_datas(df, data_inicio, data_fim, 'Data_Evento')
  df = filtrar_por_classe_selecionada(df, 'Loja', lojas_selecionadas)

  df = pd.DataFrame(df)
  df.drop(['ID_Evento'], axis=1, inplace=True)

  df = df.rename(columns = {'ID_receita': 'ID', 'Cliente' : 'Cliente', 'Classificacao': 'Classificação', 
                            'Nome_Evento': 'Nome do Evento', 'Categ_AB': 'Categ. AB', 
                            'Categ_Aluguel': 'Categ. Aluguel', 'Categ_Artist': 'Categ. Artista', 
                            'Categ_Couvert': 'Categ. Couvert', 'Categ_Locacao': 'Categ. Locação', 
                            'Categ_Patroc': 'Categ. Patrocínio', 'Categ_Taxa_Serv': 'Categ. Taxa de serviço', 
                            'Valor_Total': 'Valor Total', 'Data_Evento': 'Data Evento'})
  
  Classificacoes = ['Eventos', 'Coleta de Óleo', 'Bilheteria', 'Patrocínio']
  if 'Blue Note - São Paulo' in lojas_selecionadas or 'Blue Note SP (Novo)' in lojas_selecionadas or 'Blue Note SP (Sala 2)' in lojas_selecionadas:
    Classificacoes.append('Premium Corp')
  df = df[df['Classificação'].isin(Classificacoes)]

  df = df_format_date_brazilian(df, 'Data Evento')
  df = pd.DataFrame(df)
  return df


def faturam_receit_extraord(df, checkbox_agrupa=False):
  df = df.drop(['ID', 'Cliente', 'Data Evento', 'Nome do Evento'], axis=1)
  colunas_a_somar = ['Categ. AB', 'Categ. Aluguel', 'Categ. Artista', 'Categ. Couvert', 'Categ. Locação', 
                      'Categ. Patrocínio', 'Categ. Taxa de serviço', 'Valor Total']
  agg_funct = {col: 'sum' for col in colunas_a_somar}

  if checkbox_agrupa is False:
    colunas_a_agrupar = ['Classificação', 'Loja']
  else:
    colunas_a_agrupar = ['Classificação']

  agrupado = df.groupby(colunas_a_agrupar).agg({
    'Categ. AB': 'sum',
    'Categ. Aluguel': 'sum',
    'Categ. Artista': 'sum',
    'Categ. Couvert': 'sum',
    'Categ. Locação': 'sum',
    'Categ. Patrocínio': 'sum',
    'Categ. Taxa de serviço': 'sum',
    'Valor Total': 'sum',
  }).reset_index()
  agrupado['Quantia'] = df.groupby(colunas_a_agrupar).size().values
  agrupado = agrupado.sort_values(by='Quantia', ascending=False) 
  if checkbox_agrupa is True: agrupado['Loja'] = 'Agrupamento'

  totais = agrupado[colunas_a_somar + ['Quantia']].sum()

  df_totais = pd.DataFrame(totais, columns=['Totais']).reset_index().rename(columns={'index': 'Categoria'})
  df_totais_transposed = df_totais.set_index('Categoria').T
  df_totais_transposed_formatted = format_columns_brazilian(df_totais_transposed, colunas_a_somar)

  agrupado = format_columns_brazilian(agrupado, colunas_a_somar + ['Valor Total'])
  agrupado = agrupado[['Loja', 'Classificação', 'Categ. AB', 'Categ. Aluguel', 'Categ. Artista', 'Categ. Couvert', 'Categ. Locação', 'Categ. Patrocínio', 'Categ. Taxa de serviço', 'Valor Total', 'Quantia']]

  return agrupado, df_totais_transposed_formatted