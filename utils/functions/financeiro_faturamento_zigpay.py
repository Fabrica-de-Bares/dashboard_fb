import streamlit as st
import pandas as pd
from utils.functions.general_functions import *
from utils.queries_financeiro import *
from utils.components import *


def config_Faturamento_zig(lojas_selecionadas, data_inicio, data_fim):
  FaturamentoZig = GET_FATURAM_ZIG(data_inicio, data_fim)

  filtrar_por_classe_selecionada(FaturamentoZig, 'Loja', lojas_selecionadas)
  categorias_desejadas = ['Alimentos', 'Bebidas', 'Gifts', 'Delivery']
  FaturamentoZig = FaturamentoZig[FaturamentoZig['Categoria'].isin(categorias_desejadas)]
  FaturamentoZig = filtrar_por_classe_selecionada(FaturamentoZig, 'Loja', lojas_selecionadas)

  # Cálculo de novas colunas
  FaturamentoZig['Valor Bruto Venda'] = FaturamentoZig['Preco'] * FaturamentoZig['Qtd_Transacao']
  FaturamentoZig['Valor Líquido Venda'] = FaturamentoZig['Valor Bruto Venda'] - FaturamentoZig['Desconto']

  # Renomear colunas
  FaturamentoZig = FaturamentoZig.rename(columns={
    'ID_Venda_EPM': 'ID Venda', 'Data_Venda': 'Data da Venda', 'ID_Produto_EPM': 'ID Produto',
    'Nome_Produto': 'Nome Produto', 'Preco': 'Preço Unitário', 'Qtd_Transacao': 'Quantia comprada',
    'Valor Bruto Venda': 'Valor Bruto Venda', 'Desconto': 'Desconto', 'Valor Líquido Venda': 'Valor Líquido Venda',
    'Categoria': 'Categoria', 'Tipo': 'Tipo'
  })

  return FaturamentoZig


def config_orcamento_faturamento(lojas_selecionadas, data_inicio, data_fim):
  
  FaturamZigAgregado = GET_FATURAM_ZIG_AGREGADO(data_inicio=data_inicio, data_fim=data_fim)
  OrcamFaturam = GET_ORCAM_FATURAM()

  # Conversão de tipos para a padronização de valores
  FaturamZigAgregado['Primeiro_Dia_Mes'] = pd.to_datetime(FaturamZigAgregado['Primeiro_Dia_Mes'], format='%y-%m-%d')
  OrcamFaturam['Primeiro_Dia_Mes'] = pd.to_datetime(OrcamFaturam['Primeiro_Dia_Mes'])
  FaturamZigAgregado['Data_Evento'] = pd.to_datetime(FaturamZigAgregado['Data_Evento'], format='%y-%m-%d')

  # Padronização de categorias (para não aparecer as categorias não desejadas)
  OrcamFaturam['Categoria'] = OrcamFaturam['Categoria'].str.replace('ç', 'c')
  categorias_desejadas_orcamento = ['Alimentos', 'Bebidas', 'Couvert', 'Gifts', 'Serviço']
  OrcamFaturam = OrcamFaturam[OrcamFaturam['Categoria'].isin(categorias_desejadas_orcamento)]
  categorias_desejadas_faturamento = ['Alimentos', 'Bebidas', 'Couvert', 'Gifts', 'Serviço']
  FaturamZigAgregado = FaturamZigAgregado[FaturamZigAgregado['Categoria'].isin(categorias_desejadas_faturamento)]

  # substituicoesIds = {
  #   103: 116,
  #   112: 104,
  #   118: 114,
  #   117: 114,
  #   139: 105
  # }

  # substituicoesNomes = {
  #   'Delivery Fabrica de Bares': 'Bar Brahma - Centro',
  #   'Hotel Maraba': 'Bar Brahma - Centro',
  #   'Delivery Bar Leo Centro': 'Bar Léo - Centro',
  #   'Delivery Orfeu': 'Orfeu',
  #   'Delivery Jacaré': 'Jacaré'
  # }

  # FaturamZigAgregado['Loja'] = FaturamZigAgregado['Loja'].replace(substituicoesNomes)
  # FaturamZigAgregado['ID_Loja'] = FaturamZigAgregado['ID_Loja'].apply(lambda x: substituicoesIds.get(x, x))
  FaturamZigAgregado = filtrar_por_classe_selecionada(FaturamZigAgregado, 'Loja', lojas_selecionadas)
  OrcamFaturam = filtrar_por_classe_selecionada(OrcamFaturam, 'Loja', lojas_selecionadas)

  # Soma faturamentos de lojas equivalentes
  FaturamZigAgregado = FaturamZigAgregado.groupby(['ID_Loja', 'Loja','Categoria', 'Primeiro_Dia_Mes', 'Ano_Mes', 'Data_Evento']).agg({
    'Valor_Bruto': 'sum',
    'Desconto': 'sum',
    'Valor_Liquido': 'sum'
  }).reset_index()
 
  # Normaliza as categorias para resolver problema com C cedilha da palavra "Serviço" e caracteres que têm a mesma aparência mas são representados de maneira diferente
  FaturamZigAgregado['Categoria'] = FaturamZigAgregado['Categoria'].str.normalize('NFKD')
  OrcamFaturam['Categoria'] = OrcamFaturam['Categoria'].str.normalize('NFKD')

  # Merge das tabelas de faturamento e orçamento
  OrcamentoFaturamento = pd.merge(FaturamZigAgregado, OrcamFaturam, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes', 'Ano_Mes', 'Categoria'], how='outer')
  OrcamentoFaturamento = OrcamentoFaturamento.dropna(subset=['Categoria'])
  OrcamentoFaturamento['Data_Evento'] = OrcamentoFaturamento['Data_Evento'].fillna(OrcamentoFaturamento['Primeiro_Dia_Mes'])
  OrcamentoFaturamento['Data_Evento'] = pd.to_datetime(OrcamentoFaturamento['Data_Evento'])

  
  # Filtra período de data
  OrcamentoFaturamento = filtrar_por_datas(OrcamentoFaturamento, data_inicio, data_fim, 'Data_Evento')
  contagem_delivery = OrcamentoFaturamento[OrcamentoFaturamento['Categoria'] == 'Delivery'].shape[0]
  
  # Exclui colunas que não serão usadas na análise, agrupa tuplas de valores de categoria iguais e renomeia as colunas restantes
  OrcamentoFaturamento.drop(['ID_Loja', 'Loja', 'Data_Evento'], axis=1, inplace=True)
  OrcamentoFaturamento = OrcamentoFaturamento.groupby('Categoria').agg({
    'Orcamento_Faturamento': 'sum',
    'Valor_Bruto': 'sum',
    'Desconto': 'sum',
    'Valor_Liquido': 'sum'
  }).reset_index()
  OrcamentoFaturamento.columns = ['Categoria', 'Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido']

  # Conversão de valores para padronização
  cols = ['Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido']
  OrcamentoFaturamento[cols] = OrcamentoFaturamento[cols].astype(float)

  if 'Delivery' in OrcamentoFaturamento['Categoria'].values:
    OrcamentoFaturamento.loc[OrcamentoFaturamento['Categoria'] == 'Delivery', 'Orçamento'] /= contagem_delivery


  # Criação da coluna 'Faturam - Orçamento' e da linha 'Total Geral'
  OrcamentoFaturamento['Faturam - Orçamento'] = OrcamentoFaturamento['Valor Bruto'] - OrcamentoFaturamento['Orçamento']
  Total = OrcamentoFaturamento[['Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido', 'Faturam - Orçamento']].sum()
  NovaLinha = pd.DataFrame([{
    'Categoria': 'Total Geral', 'Orçamento': Total['Orçamento'], 'Valor Bruto': Total['Valor Bruto'],
    'Desconto': Total['Desconto'], 'Valor Líquido': Total['Valor Líquido'],
    'Faturam - Orçamento': Total['Faturam - Orçamento']
  }])
  OrcamentoFaturamento = pd.concat([OrcamentoFaturamento, NovaLinha], ignore_index=True)

  OrcamentoFaturamento['Atingimento %'] = (OrcamentoFaturamento['Valor Bruto']/OrcamentoFaturamento['Orçamento']) *100
  OrcamentoFaturamento['Atingimento %'] = OrcamentoFaturamento['Atingimento %'].apply(format_brazilian)
  OrcamentoFaturamento['Atingimento %'] = OrcamentoFaturamento['Atingimento %'].apply(lambda x: x + '%')

  OrcamentoFaturamento = OrcamentoFaturamento.reindex(['Categoria', 'Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido',
    'Atingimento %', 'Faturam - Orçamento'], axis=1)

  return OrcamentoFaturamento



def top_dez(dataframe, categoria, key):
  df = dataframe[dataframe['Categoria'] == categoria]

  # Agrupar por ID Produto
  agrupado = df.groupby(['ID Produto', 'Nome Produto']).agg({
    'Preço Unitário': 'mean',
    'Quantia comprada': 'sum',
    'Valor Bruto Venda': 'sum',
    'Desconto': 'sum',
    'Valor Líquido Venda': 'sum'
  }).reset_index()

  # Ordenar por Valor Líquido Venda em ordem decrescente
  topDez = agrupado.sort_values(by='Valor Líquido Venda', ascending=False).head(10).reset_index(drop=True)

  topDez['Valor Líquido Venda'] = topDez['Valor Líquido Venda'].astype(float)
  topDez['Valor Bruto Venda'] = topDez['Valor Bruto Venda'].astype(float)

  valor_total_bruto = topDez['Valor Bruto Venda'].sum()
  valor_total_liq = topDez['Valor Líquido Venda'].sum()
  
  topDez['% do Valor Líquido Total'] = (topDez['Valor Líquido Venda']/valor_total_liq) * 100
  topDez['% do Valor Bruto Total'] = (topDez['Valor Bruto Venda']/valor_total_bruto) * 100

  # Aplicar a formatação brasileira nas colunas
  colunas = ['Valor Líquido Venda', 'Valor Bruto Venda']
  topDez = format_columns_brazilian(topDez, colunas)
  
  topDez = format_columns_brazilian(topDez, ['Preço Unitário', 'Desconto'])
  topDez['Quantia comprada'] = topDez['Quantia comprada'].apply(lambda x: str(x))

  # Reordenar as colunas
  colunas_ordenadas = [
    'Nome Produto', 'Preço Unitário', 'Quantia comprada', '% do Valor Bruto Total', 
    'Valor Bruto Venda', 'Desconto', '% do Valor Líquido Total', 'Valor Líquido Venda'
  ]
  topDez = topDez.reindex(columns=colunas_ordenadas)

  altura_total = len(topDez) * 40 + 45
  dataframe_aggrid(topDez, 'top_dez', height=altura_total, num_columns=['Preço Unitário', 'Quantia comprada', 'Valor Bruto Venda', 'Desconto', 'Valor Líquido Venda'], progress_columns=['% do Valor Líquido Total', '% do Valor Bruto Total'], key=key)

  return topDez



def vendas_agrupadas(dataframe):
  # Agrupar por ID Produto
  agrupado = dataframe.groupby(['ID Produto', 'Nome Produto', 'Loja']).agg({
    'Preço Unitário': 'mean',
    'Quantia comprada': 'sum',
    'Valor Bruto Venda': 'sum',
    'Desconto': 'sum',
    'Valor Líquido Venda': 'sum'
  }).reset_index()

  # Ordenar por Valor Líquido Venda em ordem decrescente
  AgrupadoSorted = agrupado.sort_values(by='Valor Líquido Venda', ascending=False).reset_index(drop=True)

  AgrupadoSorted['Valor Líquido Venda'] = AgrupadoSorted['Valor Líquido Venda'].astype(float)
  AgrupadoSorted['Valor Bruto Venda'] = AgrupadoSorted['Valor Bruto Venda'].astype(float)

  valor_total_bruto = AgrupadoSorted['Valor Bruto Venda'].sum()
  valor_total_liq = AgrupadoSorted['Valor Líquido Venda'].sum()
  
  AgrupadoSorted['% do Valor Líquido Total'] = (AgrupadoSorted['Valor Líquido Venda']/valor_total_liq) * 100
  AgrupadoSorted['% do Valor Bruto Total'] = (AgrupadoSorted['Valor Bruto Venda']/valor_total_bruto) * 100


  # Aplicar a formatação brasileira nas colunas
  colunas = ['Valor Líquido Venda', 'Valor Bruto Venda']
  AgrupadoSorted = format_columns_brazilian(AgrupadoSorted, colunas)
  
  AgrupadoSorted = format_columns_brazilian(AgrupadoSorted, ['Preço Unitário', 'Desconto'])
  AgrupadoSorted['Quantia comprada'] = AgrupadoSorted['Quantia comprada'].apply(lambda x: str(x))

  # Reordenar as colunas
  colunas_ordenadas = [
    'Nome Produto', 'Preço Unitário', 'Quantia comprada', '% do Valor Bruto Total', 
    'Valor Bruto Venda', 'Desconto', '% do Valor Líquido Total', 'Valor Líquido Venda'
  ]
  AgrupadoSorted = AgrupadoSorted.reindex(columns=colunas_ordenadas)

  st.data_editor(
    AgrupadoSorted,
    width=1080,
    column_config={
      "% do Valor Líquido Total": st.column_config.ProgressColumn(
        "% do Valor Líquido Total",
        help="O Valor Líquido da Venda do produto em porcentagem",
        format="%.2f%%",
        min_value=0,
        max_value=100,
    ),
      "% do Valor Bruto Total": st.column_config.ProgressColumn(
        "% do Valor Bruto Total",
        help="O Valor Bruto da Venda do produto em porcentagem",
        format="%.2f%%",
        min_value=0,
        max_value=100,
      ),
    },
    disabled=True,
    hide_index=True,
    key='vendas_agrupadas'
  )

  return AgrupadoSorted




def vendas_agrupadas_por_tipo(dataframe):
  # Agrupar por ID Produto
  agrupado = dataframe.groupby(['Tipo']).agg({
    'Valor Bruto Venda': 'sum',
    'Desconto': 'sum',
    'Valor Líquido Venda': 'sum'
  }).reset_index()

  # Ordenar por Valor Líquido Venda em ordem decrescente
  AgrupadoSorted = agrupado.sort_values(by='Valor Líquido Venda', ascending=False).reset_index(drop=True)

  AgrupadoSorted['Valor Líquido Venda'] = AgrupadoSorted['Valor Líquido Venda'].astype(float)
  AgrupadoSorted['Valor Bruto Venda'] = AgrupadoSorted['Valor Bruto Venda'].astype(float)

  valor_total_bruto = AgrupadoSorted['Valor Bruto Venda'].sum()
  valor_total_liq = AgrupadoSorted['Valor Líquido Venda'].sum()
  
  AgrupadoSorted['% do Valor Líquido Total'] = (AgrupadoSorted['Valor Líquido Venda']/valor_total_liq) * 100
  AgrupadoSorted['% do Valor Bruto Total'] = (AgrupadoSorted['Valor Bruto Venda']/valor_total_bruto) * 100


  # Aplicar a formatação brasileira nas colunas
  colunas = ['Valor Líquido Venda', 'Valor Bruto Venda']
  AgrupadoSorted = format_columns_brazilian(AgrupadoSorted, colunas)
  
  # AgrupadoSorted = format_columns_brazilian(AgrupadoSorted, ['Preço Unitário', 'Desconto'])
  AgrupadoSorted = format_columns_brazilian(AgrupadoSorted, ['Desconto'])

  # AgrupadoSorted['Quantia comprada'] = AgrupadoSorted['Quantia comprada'].apply(lambda x: str(x))

  # Reordenar as colunas
  colunas_ordenadas = [
    'Tipo', '% do Valor Bruto Total', 'Valor Bruto Venda', 'Desconto', '% do Valor Líquido Total', 'Valor Líquido Venda'
  ]
  AgrupadoSorted = AgrupadoSorted.reindex(columns=colunas_ordenadas)

  st.data_editor(
    AgrupadoSorted,
    width=1080,
    column_config={
      "% do Valor Líquido Total": st.column_config.ProgressColumn(
        "% do Valor Líquido Total",
        help="O Valor Líquido da Venda do produto em porcentagem",
        format="%.2f%%",
        min_value=0,
        max_value=100,
    ),
      "% do Valor Bruto Total": st.column_config.ProgressColumn(
        "% do Valor Bruto Total",
        help="O Valor Bruto da Venda do produto em porcentagem",
        format="%.2f%%",
        min_value=0,
        max_value=100,
      ),
    },
    disabled=True,
    hide_index=True,
    key = 'tabela_vendas_agrupadas_por_tipo'
  )

  return AgrupadoSorted


def Grafico_Donut(df): 
  # Extrair dados do DataFrame
  data = []
  for index, row in df.iterrows():
    if row['Categoria'] != 'Total Geral':  # Ignorar a linha de 'Total Geral'
      data.append({"value": row['Valor Líquido'], "name": row['Categoria']})

  # Configurar opções do gráfico
  options = {
    "tooltip": {"trigger": "item"},
    "legend": {"orient": "vertical", "left": "5%", "top": "middle"},
    "series": [
      {
      "name": "Valor Líquido por Categoria",
      "type": "pie",
      "radius": ["40%", "70%"],
      "avoidLabelOverlap": False,
      "itemStyle": {
        "borderRadius": 10,
        "borderColor": "#fff",
        "borderWidth": 2,
      },
      "label": {"show": False, "position": "center"},
      "emphasis": {
          "label": {"show": True, "fontSize": "20", "fontWeight": "bold"}
      },
      "labelLine": {"show": False},
      "data": data,
      }
    ],
  }
  # Renderizar o gráfico
  st_echarts(
    options=options, height="300px", width="550px", key='grafico_donut_faturamento'
  )


def faturam_por_dia(df):
  df['Data da Venda'] = df['Data da Venda'].astype(str)

  # Preparar os dados para o gráfico de área empilhada
  df = df.groupby(['Data da Venda', 'Categoria'])['Valor Líquido Venda'].sum().reset_index()
  df['Valor Líquido Venda'] = df['Valor Líquido Venda'].astype(float)
  df = df.pivot(index='Data da Venda', columns='Categoria', values='Valor Líquido Venda').fillna(0)

  # Calcular o valor total diário
  df['Total'] = df.sum(axis=1)
  df.round({'Total': 2})
  df = df.reset_index()

  # Extrair datas e categorias
  datas = df['Data da Venda'].tolist()
  categorias = df.columns[1:-1].tolist()

  # Preparar séries de dados
  series = []
  for categoria in categorias:
    series.append({
      "name": categoria,
      "type": "line",
      "stack": "Total",
      "areaStyle": {},
      "emphasis": {"focus": "series"},
      "data": df[categoria].tolist(),
    })
  
  # Configurações do gráfico
  options = {
    "title": {"text": "  "},
    "tooltip": {
      "trigger": "axis",
      "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": categorias},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    "xAxis": [
      {
        "type": "category",
        "boundaryGap": False,
        "data": datas,
      }
    ],
    "yAxis": [{"type": "value"}],
    "series": series,
  }
    
  # Renderizar o gráfico no Streamlit
  st_echarts(options=options, height="400px", key='faturam_por_dia')