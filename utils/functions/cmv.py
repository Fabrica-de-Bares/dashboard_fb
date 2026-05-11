import pandas as pd
from utils.functions.general_functions import *
from utils.queries_cmv import *
from utils.components import *
import calendar
from babel.dates import format_date
from utils.functions.date_functions import *
import io

pd.set_option('future.no_silent_downcasting', True)

def substituicao_ids(df, colNome, colID):
  substituicoesIds = {
    103: 116,
    112: 104,
    118: 114,
    117: 114,
    139: 105,
    161: 149,
    162: 149,
    110: 131,
    178: 131,
    160: 156,
    177: 176
  }

  substituicoesNomes = {
    'Delivery Fabrica de Bares': 'Bar Brahma - Centro',
    'Hotel Maraba': 'Bar Brahma - Centro',
    'Delivery Brahma Centro': 'Bar Brahma - Centro',
    'Delivery Bar Leo Centro': 'Bar Léo - Centro',
    'Delivery Brahma Granja Viana': 'Bar Brahma - Granja',
    'Delivery Orfeu': 'Orfeu',
    'Delivery Jacaré': 'Jacaré',
    'Notiê - Priceless': 'Priceless',
    'Terraço Notie': 'Priceless',
    'Blue Note - São Paulo': 'Blue Note - Agregado',
    'Blue Note SP (Novo)': 'Blue Note - Agregado',
    'Blue Note SP (Sala 2)': 'Blue Note - Agregado',
    'Girondino - CCBB': 'Girondino - Agregado',
    'Girondino': 'Girondino - Agregado',
    'The Cavern': 'The Cavern - Agregado',
    'The Cavern - Almoço': 'The Cavern - Agregado'
  }

  df.loc[:, colNome] = df[colNome].replace(substituicoesNomes)
  df.loc[:, colID] = df[colID].replace(substituicoesIds)
  return df


def criar_seletores_cmv(data_inicio_default, data_fim_default):
  col1, col2, col3 = st.columns([2, 1, 1])

  # Adiciona seletores
  with col1:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Escritório Fabrica de Bares', 'Todas as Casas']
    id_casa, casa, id_zigpay = input_selecao_casas_agregadas(lista_retirar_casas, key='calendario')
  with col2:
    data_inicio = st.date_input('Data de Início', value=data_inicio_default, key='data_inicio_input', format="DD/MM/YYYY")
  with col3:
    data_fim = st.date_input('Data de Fim', value=data_fim_default, key='data_fim_input', format="DD/MM/YYYY")

  # Converte as datas selecionadas para o formato Timestamp
  data_inicio = pd.to_datetime(data_inicio)
  data_fim = pd.to_datetime(data_fim)
  return casa, data_inicio, data_fim

def primeiro_dia_mes_para_mes_ano(df):
  df['Primeiro_Dia_Mes'] = pd.to_datetime(df['Primeiro_Dia_Mes'], format='%d-%m-%Y', errors='coerce')
  
  df['Primeiro_Dia_Mes_Formatado'] = df['Primeiro_Dia_Mes'].apply(
    lambda x: format_date(x, format='MMMM/yyyy', locale='pt_BR') if pd.notnull(x) else None
  )
  return df


def config_faturamento_bruto_zig(data_inicio, data_fim, loja):
  df = GET_FATURAM_ZIG_ALIM_BEB_MENSAL(data_inicio=data_inicio, data_fim=data_fim)
  df = substituicao_ids(df, 'Loja', 'ID_Loja')
  

  df['Valor_Bruto'] = df['Valor_Bruto'].astype(float)
  df = df.dropna(subset=['ID_Loja'])

  df = df.groupby(['ID_Loja', 'Loja', 'Primeiro_Dia_Mes', 'Categoria', 'Delivery', 'Ano_Mes']).agg({
    'Valor_Bruto': 'sum',
    'Desconto': 'sum',
    'Valor_Liquido': 'sum',
    'Data_Evento': 'first'
  }).reset_index()

  # Faturamento Delivery
  df_delivery = df[(df['Delivery'] == 1)]
  df_delivery = df_delivery[df_delivery['Loja'] == loja]

  # Faturamento Zig
  df_zig = df[df['Delivery'] == 0]
  df_zig = df_zig[df_zig['Loja'] == loja]
  

  faturamento_bruto_alimentos = df_zig[(df_zig['Categoria'] == 'Alimentos')]['Valor_Bruto'].sum()
  faturamento_bruto_bebidas = df_zig[(df_zig['Categoria'] == 'Bebidas')]['Valor_Bruto'].sum()
  
  # Faturamento de serviço de deliver é distribuído entre alimentos e bebidas na mesma proporção do faturamento bruto do zig para cada categoria
  faturamento_servico_delivery = df_delivery[df_delivery['Categoria'] == 'Serviço']['Valor_Bruto'].sum()
  faturamento_alimentos_delivery = df_delivery[(df_delivery['Categoria'] == 'Alimentos')]['Valor_Bruto'].sum()
  faturamento_bebidas_delivery = df_delivery[(df_delivery['Categoria'] == 'Bebidas')]['Valor_Bruto'].sum()

  if faturamento_servico_delivery > 0:
    faturamento_alimentos_delivery = faturamento_alimentos_delivery + faturamento_servico_delivery * (faturamento_bruto_alimentos / (faturamento_bruto_alimentos + faturamento_bruto_bebidas))
    faturamento_bebidas_delivery = faturamento_bebidas_delivery + faturamento_servico_delivery * (faturamento_bruto_bebidas / (faturamento_bruto_alimentos + faturamento_bruto_bebidas))
  
  return df_delivery, df_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_alimentos_delivery, faturamento_bebidas_delivery



def config_faturamento_eventos(data_inicio, data_fim, loja, faturamento_bruto_alimentos, faturamento_bruto_bebidas):
  df = GET_EVENTOS_CMV(data_inicio=data_inicio, data_fim=data_fim)
  df = substituicao_ids(df, 'Loja', 'ID_Loja')
  df = df[df['Loja'] == loja]

  df['Valor'] = df['Valor'].astype(float)

  faturmento_total_zig = faturamento_bruto_alimentos + faturamento_bruto_bebidas
  faturamento_total_eventos = df['Valor'].sum()

  if faturmento_total_zig > 0:
    faturamento_alimentos_eventos = (faturamento_bruto_alimentos * faturamento_total_eventos) / faturmento_total_zig
    faturamento_bebidas_eventos = (faturamento_bruto_bebidas * faturamento_total_eventos) / faturmento_total_zig
  else:
    faturamento_alimentos_eventos = 0
    faturamento_bebidas_eventos = 0

  return df, faturamento_alimentos_eventos, faturamento_bebidas_eventos



def config_compras(data_inicio, data_fim, loja):
  df1 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO()  
  df2 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO_PERIODO_LOJA(data_inicio, data_fim, loja)

  df1 = substituicao_ids(df1, 'Loja', 'ID_Loja')
  df2 = substituicao_ids(df2, 'Loja', 'ID_Loja')

  df_compras = pd.merge(df2, df1, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')

  df_compras = df_compras[df_compras['Loja'] == loja]  
  df_compras = df_compras.groupby(['ID_Loja', 'Loja', 'Primeiro_Dia_Mes']).agg(
    {'BlueMe_Sem_Pedido_Alimentos': 'sum', 
     'BlueMe_Sem_Pedido_Bebidas': 'sum', 
     'BlueMe_Com_Pedido_Valor_Liq_Alimentos': 'sum', 
     'BlueMe_Com_Pedido_Valor_Liq_Bebidas': 'sum',
    }).reset_index()

  df_compras = filtrar_por_datas(df_compras, data_inicio, data_fim, 'Primeiro_Dia_Mes')

  Compras_Alimentos = df_compras['BlueMe_Sem_Pedido_Alimentos'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'].sum()
  Compras_Bebidas = df_compras['BlueMe_Sem_Pedido_Bebidas'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'].sum()

  Compras_Alimentos = float(Compras_Alimentos)
  Compras_Bebidas = float(Compras_Bebidas)

  df_compras = primeiro_dia_mes_para_mes_ano(df_compras)

  df_compras['Compras Alimentos'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'] + df_compras['BlueMe_Sem_Pedido_Alimentos']
  df_compras['Compras Bebidas'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'] + df_compras['BlueMe_Sem_Pedido_Bebidas']
  df_compras = df_compras.rename(columns={
    'Primeiro_Dia_Mes': 'Mes Ano', 
    'BlueMe_Com_Pedido_Valor_Liq_Alimentos': 'BlueMe c/ Pedido Alim.',
    'BlueMe_Com_Pedido_Valor_Liq_Bebidas': 'BlueMe c/ Pedido Bebidas',
    'BlueMe_Sem_Pedido_Alimentos': 'BlueMe s/ Pedido Alim.',
    'BlueMe_Sem_Pedido_Bebidas': 'BlueMe s/ Pedido Bebidas'
  })

  df_compras = df_compras[['ID_Loja', 'Loja', 'BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']]

  # Exibe todos os valores em apenas uma linha
  df_compras = df_compras.groupby(['ID_Loja', 'Loja'], as_index=False)[['BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']].sum()
  
  return df_compras, Compras_Alimentos, Compras_Bebidas



def config_insumos_blueme_sem_pedido(data_inicio, data_fim, loja):
  df = GET_INSUMOS_BLUE_ME_SEM_PEDIDO()
  df = substituicao_ids(df, 'Loja', 'ID_Loja')
  df = df.drop(['Primeiro_Dia_Mes'], axis=1)
  df = df[df['Loja'] == loja]
  df = filtrar_por_datas(df, data_inicio, data_fim, 'Data_Emissao')
  df = df_format_date_brazilian(df, 'Data_Emissao')

  df.rename(columns = {'tdr_ID': 'tdr ID', 'ID_Loja': 'ID Loja', 'Loja': 'Loja', 'Fornecedor': 'Fornecedor', 'Plano_de_Contas': 'Classificacao',
                       'Doc_Serie': 'Doc_Serie', 'Data_Emissao': 'Data Emissão', 'Valor': 'Valor'}, inplace=True)
  df['Valor'] = df['Valor'].astype(float)
  return  df


def config_insumos_blueme_com_pedido(data_inicio, data_fim, loja):
    df = GET_INSUMOS_BLUE_ME_COM_PEDIDO(data_inicio, data_fim, loja)

    df = (
        df
        .pipe(substituicao_ids, 'Loja', 'ID_Loja')
        .drop(columns=['Primeiro_Dia_Mes'])
        .loc[lambda x: x['Loja'] == loja]
        .pipe(filtrar_por_datas, data_inicio, data_fim, 'Data_Emissao')
        .pipe(df_format_date_brazilian, 'Data_Emissao')
    )

    # Colunas numéricas
    colunas_float = [
        'Valor_Cotacao',
        'Valor_Liquido',
        'Valor_Liq_Alimentos',
        'Valor_Liq_Bebidas',
        'Valor_Liq_Descart_Hig_Limp',
        'Valor_Gelo_Gas_Carvao_Velas',
        'Valor_Utensilios',
        'Valor_Liq_Outros'
    ]

    df[colunas_float] = df[colunas_float].astype(float)

    # Cálculo de insumos
    df['Insumos - V. Líq'] = df['Valor_Cotacao'] - df['Valor_Liquido']

    # Renomear colunas
    df = df.rename(columns={
        'tdr_ID': 'tdr ID',
        'ID_Loja': 'ID Loja',
        'Doc_Serie': 'Doc_Serie',
        'Data_Emissao': 'Data Emissão',
        'Valor_Liquido': 'Valor Líquido',
        'Valor_Cotacao': 'Valor Cotação',
        'Valor_Liq_Alimentos': 'Valor Líq. Alimentos',
        'Valor_Liq_Bebidas': 'Valor Líq. Bebidas',
        'Valor_Liq_Descart_Hig_Limp': 'Valor Líq. Hig/Limp.',
        'Valor_Gelo_Gas_Carvao_Velas': 'Valor Líq Gelo/Gas/Carvão/Velas',
        'Valor_Utensilios': 'Valor Líq. Utensilios',
        'Valor_Liq_Outros': 'Valor Líq. Outros'
    })

    # Ordem final
    ordem_colunas = [
        'tdr ID',
        'ID Loja',
        'Loja',
        'Fornecedor',
        'Doc_Serie',
        'Data Emissão',
        'Valor Líquido',
        'Valor Cotação',
        'Insumos - V. Líq',
        'Valor Líq. Alimentos',
        'Valor Líq. Bebidas',
        'Valor Líq. Hig/Limp.',
        'Valor Líq Gelo/Gas/Carvão/Velas',
        'Valor Líq. Utensilios',
        'Valor Líq. Outros'
    ]

    return df[ordem_colunas]


def config_valoracao_producao(data_inicio, loja):
  if data_inicio.month == 12:
    data_contagem = data_inicio.replace(year=data_inicio.year + 1, month=1, day=1)
  else:
    data_contagem = data_inicio.replace(month=data_inicio.month + 1, day=1)
  df_valoracao_producao = GET_VALORACAO_PRODUCAO(data_contagem)

  df_valoracao_producao = substituicao_ids(df_valoracao_producao, 'Loja', 'ID_Loja')
  df_valoracao_producao = df_valoracao_producao[df_valoracao_producao['Loja'] == loja]
  df_valoracao_producao = df_valoracao_producao.drop(['Mes_Texto', 'Data_Contagem'], axis=1)

  df_valoracao_producao['Valor_Total'] = df_valoracao_producao['Valor_Total'].astype(float)
  df_valoracao_producao['Quantidade'] = df_valoracao_producao['Quantidade'].astype(float)
  df_valoracao_producao['Valor_Unidade_Medida'] = df_valoracao_producao['Valor_Unidade_Medida'].astype(float)
  df_producao_alimentos = df_valoracao_producao[df_valoracao_producao['Categoria'] == 'ALIMENTOS']
  df_producao_bebidas = df_valoracao_producao[df_valoracao_producao['Categoria'] == 'BEBIDAS']
  valor_producao_alimentos = df_producao_alimentos['Valor_Total'].sum()
  valor_producao_bebidas = df_producao_bebidas['Valor_Total'].sum()
  return df_producao_alimentos, df_producao_bebidas, valor_producao_alimentos, valor_producao_bebidas

def config_diferenca_producao(df_atual, df_anterior):
  df_atual = df_atual.copy()
  df_anterior = df_anterior.copy()
  df_atual.rename(columns={'Valor_Total': 'Valor_Total_Atual', 'Quantidade': 'Quantidade_Atual'}, inplace=True)
  df_anterior.rename(columns={'Valor_Total': 'Valor_Total_Anterior', 'Quantidade': 'Quantidade_Anterior'}, inplace=True)
  df_atual.drop(['ID_Loja', 'Loja', 'Valor_Unidade_Medida'], axis=1, inplace=True)
  df_anterior.drop(['ID_Loja', 'Loja', 'Valor_Unidade_Medida'], axis=1, inplace=True)
  df_diferenca_producao = pd.merge(df_atual, df_anterior, on=['Item_Produzido', 'Categoria', 'Unidade_Medida'], how='outer')
  df_diferenca_producao.fillna(0, inplace=True)
  df_diferenca_producao['Valor_Total_Atual'] = df_diferenca_producao['Valor_Total_Atual'].astype(float)
  df_diferenca_producao['Valor_Total_Anterior'] = df_diferenca_producao['Valor_Total_Anterior'].astype(float)
  df_diferenca_producao['Quantidade_Atual'] = df_diferenca_producao['Quantidade_Atual'].astype(float)
  df_diferenca_producao['Quantidade_Anterior'] = df_diferenca_producao['Quantidade_Anterior'].astype(float)
  df_diferenca_producao['Diferenca_Valor_Total'] = df_diferenca_producao['Valor_Total_Atual'] - df_diferenca_producao['Valor_Total_Anterior']
  df_diferenca_producao['Diferenca_Quantidade'] = df_diferenca_producao['Quantidade_Atual'] - df_diferenca_producao['Quantidade_Anterior']
  df_diferenca_producao.sort_values(by=['Diferenca_Valor_Total', 'Categoria'], inplace=True)
  df_diferenca_producao = format_columns_brazilian(df_diferenca_producao, ['Quantidade_Atual', 'Quantidade_Anterior', 'Valor_Total_Atual', 'Valor_Total_Anterior', 'Diferenca_Valor_Total', 'Diferenca_Quantidade'])
  df_diferenca_producao.rename(columns={'Unidade_Medida': 'Unidade de Medida', 'Quantidade_Atual': 'Quantidade Atual', 'Quantidade_Anterior': 'Quantidade Anterior', 'Diferenca_Valor_Total': 'Diferença Valor Total', 'Diferenca_Quantidade': 'Diferença Quantidade', 'Valor_Total_Atual': 'Valor Total Atual', 'Valor_Total_Anterior': 'Valor Total Anterior'}, inplace=True)
  return df_diferenca_producao



def config_producao_agregada(df_a, df_b, df_a_anterior, df_b_anterior):
  df_a_e_b = pd.concat([df_a, df_b])
  df_a_e_b_anterior = pd.concat([df_a_anterior, df_b_anterior])
  df_a_e_b.drop(['Unidade_Medida', 'Valor_Unidade_Medida', 'Quantidade', 'Item_Produzido'], axis=1, inplace=True)
  df_a_e_b_anterior.drop(['Unidade_Medida', 'Valor_Unidade_Medida', 'Quantidade', 'Item_Produzido'], axis=1, inplace=True)
  df_a_e_b.rename(columns={'Valor_Total': 'Valor Produção Atual'}, inplace=True)
  df_a_e_b_anterior.rename(columns={'Valor_Total': 'Valor Produção Mês Anterior'}, inplace=True)
  df_a_e_b = df_a_e_b.groupby(['Categoria', 'Loja', 'ID_Loja']).agg({'Valor Produção Atual': 'sum'}).reset_index()
  df_a_e_b_anterior = df_a_e_b_anterior.groupby(['ID_Loja', 'Loja', 'Categoria']).agg({'Valor Produção Mês Anterior': 'sum'}).reset_index()
  df_total = df_a_e_b_anterior.merge(df_a_e_b, on=['ID_Loja', 'Loja', 'Categoria'], how='outer')
  df_total.fillna(0, inplace=True)
  return df_total


def config_valoracao_estoque(data_inicio, data_fim, loja):
  if data_inicio.month == 12:
    data_inicio_nova = data_inicio.replace(year=data_inicio.year + 1, month=1, day=1)
  else:
    data_inicio_nova = data_inicio.replace(month=data_inicio.month + 1, day=1)

  if loja == 'Blue Note - Agregado':
    loja = 'Blue Note - São Paulo'
  elif loja == 'The Cavern - Agregado':
    loja = 'The Cavern'

  df_valoracao_estoque = GET_VALORACAO_ESTOQUE(loja, data_inicio_nova)

  df_valoracao_estoque.drop(['DATA_CONTAGEM'], axis=1, inplace=True)
  
  return df_valoracao_estoque



def config_diferenca_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior):
  df_valoracao_estoque_atual = df_valoracao_estoque_atual.copy()
  df_valoracao_estoque_mes_anterior = df_valoracao_estoque_mes_anterior.copy()
  df_valoracao_estoque_atual.rename(columns={'Valor_em_Estoque': 'Valor_em_Estoque_Atual', 'Quantidade': 'Quantidade_Atual'}, inplace=True)
  df_valoracao_estoque_mes_anterior.rename(columns={'Valor_em_Estoque': 'Valor_em_Estoque_Mes_Anterior', 'Quantidade': 'Quantidade_Mes_Anterior'}, inplace=True)
  df_diferenca_estoque = pd.merge(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior, on=['ID_Loja', 'Loja', 'ID_Insumo', 'Insumo', 'Unidade_Medida','ID_Nivel_4', 'Categoria'], how='outer')
  cols = ['Quantidade_Atual', 'Quantidade_Mes_Anterior', 'Valor_em_Estoque_Atual', 'Valor_em_Estoque_Mes_Anterior']
  df_diferenca_estoque[cols] = df_diferenca_estoque[cols].fillna(0)
  df_diferenca_estoque['Valor_em_Estoque_Atual'] = df_diferenca_estoque['Valor_em_Estoque_Atual'].astype(float)
  df_diferenca_estoque['Valor_em_Estoque_Mes_Anterior'] = df_diferenca_estoque['Valor_em_Estoque_Mes_Anterior'].astype(float)
  df_diferenca_estoque['Quantidade_Atual'] = df_diferenca_estoque['Quantidade_Atual'].astype(float)
  df_diferenca_estoque['Quantidade_Mes_Anterior'] = df_diferenca_estoque['Quantidade_Mes_Anterior'].astype(float)
  df_diferenca_estoque['Preço Mês Atual'] = df_diferenca_estoque['Valor_em_Estoque_Atual'] / df_diferenca_estoque['Quantidade_Atual']
  df_diferenca_estoque['Preço Mês Anterior'] = df_diferenca_estoque['Valor_em_Estoque_Mes_Anterior'] / df_diferenca_estoque['Quantidade_Mes_Anterior']
  df_diferenca_estoque['Diferença Preço'] = round(df_diferenca_estoque['Preço Mês Atual'] - df_diferenca_estoque['Preço Mês Anterior'], 2)
  df_diferenca_estoque['Diferenca_Estoque'] = df_diferenca_estoque['Valor_em_Estoque_Atual'] - df_diferenca_estoque['Valor_em_Estoque_Mes_Anterior']
  df_diferenca_estoque.sort_values(by=['Diferenca_Estoque', 'Categoria'], inplace=True)

  df_diferenca_estoque = df_diferenca_estoque.drop(
    columns=['ID_Loja', 'ID_Nivel_4']
  )

  df_diferenca_estoque = df_diferenca_estoque.rename(columns={
    'Quantidade_Atual': 'Quantidade Atual',
    'Quantidade_Mes_Anterior': 'Quantidade Mes Anterior',
    'Diferenca_Estoque': 'Diferença Valor Estoque',
    'Valor_em_Estoque_Atual': 'Valor em Estoque Atual',
    'Valor_em_Estoque_Mes_Anterior': 'Valor em Estoque Mes Anterior',
    'Unidade_Medida': 'Unidade de Medida',
    'ID_Insumo': 'ID Insumo',
    'Preço Mês Atual': 'Preço Mês Atual',
    'Preço Mês Anterior': 'Preço Mês Anterior',
    'Diferença Preço': 'Diferença Preço'
  })

  df_diferenca_estoque = df_diferenca_estoque[
    [
      'Loja',
      'Categoria',
      'ID Insumo',
      'Insumo',
      'Unidade de Medida',
      'Preço Mês Anterior',
      'Quantidade Mes Anterior',
      'Valor em Estoque Mes Anterior',
      'Preço Mês Atual',
      'Quantidade Atual',
      'Valor em Estoque Atual',
      'Diferença Preço',
      'Diferença Valor Estoque'
    ]
  ]

  df_diferenca_estoque = format_columns_brazilian(
    df_diferenca_estoque,
    [
      'Quantidade Atual',
      'Quantidade Mes Anterior',
      'Valor em Estoque Atual',
      'Valor em Estoque Mes Anterior',
      'Diferença Valor Estoque',
      'Preço Mês Atual',
      'Preço Mês Anterior',
      'Diferença Preço'
    ]
  )

  df_diferenca_estoque_download = df_diferenca_estoque.copy()
  df_diferenca_estoque = df_diferenca_estoque.style.map(highlight_values_inverse, subset=['Diferença Preço'])

  return df_diferenca_estoque, df_diferenca_estoque_download


def config_variacao_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior):
  df_valoracao_estoque_atual['Valor_em_Estoque'] = df_valoracao_estoque_atual['Valor_em_Estoque'].astype(float)
  df_valoracao_estoque_mes_anterior['Valor_em_Estoque'] = df_valoracao_estoque_mes_anterior['Valor_em_Estoque'].astype(float)

  valoracao_estoque_atual_alimentos = df_valoracao_estoque_atual[df_valoracao_estoque_atual['Categoria'] == 'ALIMENTOS']['Valor_em_Estoque'].sum()
  valoracao_estoque_atual_bebidas = df_valoracao_estoque_atual[df_valoracao_estoque_atual['Categoria'] == 'BEBIDAS']['Valor_em_Estoque'].sum()

  valoracao_estoque_mes_anterior_alimentos = df_valoracao_estoque_mes_anterior[df_valoracao_estoque_mes_anterior['Categoria'] == 'ALIMENTOS']['Valor_em_Estoque'].sum()
  valoracao_estoque_mes_anterior_bebidas = df_valoracao_estoque_mes_anterior[df_valoracao_estoque_mes_anterior['Categoria'] == 'BEBIDAS']['Valor_em_Estoque'].sum()
  
  variacao_estoque_alimentos = valoracao_estoque_atual_alimentos - valoracao_estoque_mes_anterior_alimentos
  variacao_estoque_bebidas = valoracao_estoque_atual_bebidas - valoracao_estoque_mes_anterior_bebidas

  df_valoracao_estoque_atual = df_valoracao_estoque_atual.rename(columns={'Valor_em_Estoque': 'Estoque Atual', 'Quantidade': 'Quantidade Atual'})
  df_valoracao_estoque_mes_anterior = df_valoracao_estoque_mes_anterior.rename(columns={'Valor_em_Estoque': 'Estoque Mes Anterior', 'Quantidade': 'Quantidade Mes Anterior'})

  df_variacao_estoque = pd.merge(df_valoracao_estoque_mes_anterior, df_valoracao_estoque_atual, on=['ID_Loja', 'Loja', 'Categoria', 'ID_Insumo', 'Insumo', 'Unidade_Medida'], how='outer').fillna(0)
  df_variacao_estoque = df_variacao_estoque.rename(columns={'ID_Loja': 'ID Loja', 'Unidade_Medida': 'Unidade de Medida', 'ID_Insumo': 'ID Insumo'})

  df_variacao_estoque = df_variacao_estoque.groupby(['ID Loja', 'Loja', 'Categoria']).agg({
    'Estoque Mes Anterior': 'sum',
    'Estoque Atual': 'sum'
  }).reset_index()

  df_variacao_estoque = df_variacao_estoque[df_variacao_estoque['Categoria'] != 0]  

  return df_variacao_estoque, variacao_estoque_alimentos, variacao_estoque_bebidas


def config_valoracao_estoque_valores(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior):
  df_valoracao_estoque_atual['Valor_em_Estoque'] = df_valoracao_estoque_atual['Valor_em_Estoque'].astype(float)
  df_valoracao_estoque_mes_anterior['Valor_em_Estoque'] = df_valoracao_estoque_mes_anterior['Valor_em_Estoque'].astype(float)

  valoracao_estoque_atual_alimentos = df_valoracao_estoque_atual[df_valoracao_estoque_atual['Categoria'] == 'ALIMENTOS']['Valor_em_Estoque'].sum()
  valoracao_estoque_atual_bebidas = df_valoracao_estoque_atual[df_valoracao_estoque_atual['Categoria'] == 'BEBIDAS']['Valor_em_Estoque'].sum()

  valoracao_estoque_mes_anterior_alimentos = df_valoracao_estoque_mes_anterior[df_valoracao_estoque_mes_anterior['Categoria'] == 'ALIMENTOS']['Valor_em_Estoque'].sum()
  valoracao_estoque_mes_anterior_bebidas = df_valoracao_estoque_mes_anterior[df_valoracao_estoque_mes_anterior['Categoria'] == 'BEBIDAS']['Valor_em_Estoque'].sum()

  return valoracao_estoque_atual_alimentos, valoracao_estoque_atual_bebidas, valoracao_estoque_mes_anterior_alimentos, valoracao_estoque_mes_anterior_bebidas

def config_faturamento_total(df_faturamento_delivery, df_faturamento_zig, df_faturamento_eventos):
  df_faturamento_eventos.rename(columns={'Valor': 'Faturamento_Eventos'})

  df_faturamento_delivery = df_faturamento_delivery.drop(['Ano_Mes', 'Data_Evento', 'Desconto', 'Valor_Liquido', 'Delivery'], axis=1)
  df_faturamento_zig = df_faturamento_zig.drop(['Ano_Mes', 'Data_Evento', 'Desconto', 'Valor_Liquido', 'Delivery'], axis=1)
  df_faturamento_zig_alimentos = df_faturamento_zig[df_faturamento_zig['Categoria'] == 'Alimentos']
  df_faturamento_zig_bebidas = df_faturamento_zig[df_faturamento_zig['Categoria'] == 'Bebidas']
  df_faturamento_zig_alimentos = df_faturamento_zig_alimentos.rename(columns={'Valor_Bruto': 'Faturamento Alimentos'})
  df_faturamento_zig_bebidas = df_faturamento_zig_bebidas.rename(columns={'Valor_Bruto': 'Faturamento Bebidas'})

  df_faturamento_delivery_alimentos = df_faturamento_delivery[df_faturamento_delivery['Categoria'] == 'Alimentos']
  df_faturamento_delivery_bebidas = df_faturamento_delivery[df_faturamento_delivery['Categoria'] == 'Bebidas']
  df_faturamento_delivery_alimentos = df_faturamento_delivery_alimentos.rename(columns={'Valor_Bruto': 'Faturamento Delivery Alimentos'})
  df_faturamento_delivery_bebidas = df_faturamento_delivery_bebidas.rename(columns={'Valor_Bruto': 'Faturamento Delivery Bebidas'})

  df_faturamento_zig_alimentos = df_faturamento_zig_alimentos.drop(['Categoria'], axis=1)
  df_faturamento_zig_bebidas = df_faturamento_zig_bebidas.drop(['Categoria'], axis=1)
  df_faturamento_delivery_alimentos = df_faturamento_delivery_alimentos.drop(['Categoria'], axis=1,)
  df_faturamento_delivery_bebidas = df_faturamento_delivery_bebidas.drop(['Categoria'], axis=1)

  df_faturamento_eventos = df_faturamento_eventos.rename(columns={'Valor': 'Faturamento Eventos'})

  df_faturamento_zig_alimentos['ID_Loja'] = df_faturamento_zig_alimentos['ID_Loja'].astype(int)
  df_faturamento_zig_bebidas['ID_Loja'] = df_faturamento_zig_bebidas['ID_Loja'].astype(int)
  df_faturamento_delivery_alimentos['ID_Loja'] = df_faturamento_delivery_alimentos['ID_Loja'].astype(int)
  df_faturamento_delivery_bebidas['ID_Loja'] = df_faturamento_delivery_bebidas['ID_Loja'].astype(int)
  df_faturamento_eventos['ID_Loja'] = df_faturamento_eventos['ID_Loja'].astype(int)


  df_faturamento_total = pd.merge(df_faturamento_zig_alimentos, df_faturamento_zig_bebidas, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')
  df_faturamento_total = pd.merge(df_faturamento_total, df_faturamento_delivery_alimentos, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')
  df_faturamento_total = pd.merge(df_faturamento_total, df_faturamento_delivery_bebidas, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')
  df_faturamento_total = pd.merge(df_faturamento_total, df_faturamento_eventos, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')

  df_faturamento_total = df_faturamento_total.fillna(0)
  df_faturamento_total = df_faturamento_total.drop(['Data'], axis=1)  

  df_faturamento_total = primeiro_dia_mes_para_mes_ano(df_faturamento_total)
  df_faturamento_total = df_faturamento_total.rename(columns={'Primeiro_Dia_Mes_Formatado': 'Mês'})
  df_faturamento_total = df_faturamento_total.drop(['Primeiro_Dia_Mes'], axis=1)
  df_faturamento_total = format_columns_brazilian(df_faturamento_total, ['Faturamento Alimentos', 'Faturamento Bebidas', 'Faturamento Delivery Alimentos', 'Faturamento Delivery Bebidas', 'Faturamento Eventos'])
  cols = ['ID_Loja', 'Loja', 'Mês', 'Faturamento Alimentos', 'Faturamento Bebidas', 'Faturamento Delivery Alimentos', 'Faturamento Delivery Bebidas', 'Faturamento Eventos']
  df_faturamento_total = df_faturamento_total[cols]
  return df_faturamento_total



def processar_transferencias(df, casa_col, loja, data_inicio, data_fim):
  # Filtrar pelo nome da loja e pelo intervalo de datas
  df = df[df[casa_col] == loja]
  df = filtrar_por_datas(df, data_inicio, data_fim, 'Data_Transferencia')
  
  # Agrupar por casa e categoria, somando os valores
  df_grouped = df.groupby([casa_col, 'Categoria']).agg({
    'Valor_Transferencia': 'sum'
  }).reset_index()
  
  # Ajustar categoria para formato capitalizado
  df_grouped['Categoria'] = df_grouped['Categoria'].str.capitalize()
  
  # Pivotar para transformar categorias em colunas
  df_pivot = df_grouped.pivot_table(
    index=casa_col,
    columns='Categoria',
    values='Valor_Transferencia',
    fill_value=0
  ).reset_index()
  
  # Renomear colunas para refletir o tipo de operação
  operacao = 'Entrada' if casa_col == 'Casa_Entrada' else 'Saída'
  df_pivot.columns = [f'{operacao} {col}' if col != casa_col else 'Loja' for col in df_pivot.columns]
  
  return df_pivot


def config_transferencias_gastos(data_inicio, data_fim, loja):
  df_transf_estoque = GET_TRANSF_ESTOQUE()
  df_transf_estoque = substituicao_ids(df_transf_estoque, 'Casa_Saida', 'ID_Loja_Saida')
  df_transf_estoque = substituicao_ids(df_transf_estoque, 'Casa_Entrada', 'ID_Loja_Entrada')
  df_entradas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Entrada', loja, data_inicio, data_fim)
  df_saidas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Saida', loja, data_inicio, data_fim)

  df_perdas_e_consumo = GET_PERDAS_E_CONSUMO_AGRUPADOS()
  df_perdas_e_consumo = filtrar_por_datas(df_perdas_e_consumo, data_inicio, data_fim, 'Primeiro_Dia_Mes')
  df_perdas_e_consumo = substituicao_ids(df_perdas_e_consumo, 'Loja', 'ID_Loja')
  df_perdas_e_consumo = df_perdas_e_consumo[df_perdas_e_consumo['Loja'] == loja]
  df_perdas_e_consumo.fillna(0, inplace=True)

  df_transf_e_gastos = pd.merge(df_entradas_pivot, df_saidas_pivot, on='Loja', how='outer')
  df_transf_e_gastos = pd.merge(df_transf_e_gastos, df_perdas_e_consumo, on='Loja', how='outer')
  df_transf_e_gastos = primeiro_dia_mes_para_mes_ano(df_transf_e_gastos)
  df_transf_e_gastos = df_transf_e_gastos.rename(columns={
    'Primeiro_Dia_Mes': 'Mês',
    'ID_Loja': 'ID Loja',
    'Consumo_Interno': 'Consumo Interno',
    'Quebras_e_Perdas': 'Quebras e Perdas'
  })
  cols = ['ID Loja', 'Loja', "Mês", 'Entrada Alimentos', 'Entrada Bebidas', 'Saída Alimentos', 'Saída Bebidas', 'Consumo Interno', 'Quebras e Perdas']
  for col in cols:
    if col not in df_transf_e_gastos.columns:
        df_transf_e_gastos[col] = 0

  df_transf_e_gastos = df_transf_e_gastos[cols]

  # Conversão para float para evitar erros de tipo
  saida_alimentos = float(df_saidas_pivot['Saída Alimentos'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Alimentos' in df_saidas_pivot.columns else 0.0
  saida_bebidas = float(df_saidas_pivot['Saída Bebidas'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Bebidas' in df_saidas_pivot.columns else 0.0
  entrada_alimentos = float(df_entradas_pivot['Entrada Alimentos'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Alimentos' in df_entradas_pivot.columns else 0.0
  entrada_bebidas = float(df_entradas_pivot['Entrada Bebidas'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Bebidas' in df_entradas_pivot.columns else 0.0
  consumo_interno = float(df_transf_e_gastos['Consumo Interno'].iloc[0]) if not df_perdas_e_consumo.empty and 'Consumo Interno' in df_transf_e_gastos.columns else 0.0
  quebras_e_perdas = float(df_transf_e_gastos['Quebras e Perdas'].iloc[0]) if not df_perdas_e_consumo.empty and 'Quebras e Perdas' in df_transf_e_gastos.columns else 0.0

  return df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas

def config_transferencias_detalhadas(data_inicio, data_fim, loja):
  df_transf_estoque = GET_TRANSF_ESTOQUE()
  df_transf_estoque = substituicao_ids(df_transf_estoque, 'Casa_Saida', 'ID_Loja_Saida')
  df_transf_estoque = substituicao_ids(df_transf_estoque, 'Casa_Entrada', 'ID_Loja_Entrada')
  df_transf_estoque = filtrar_por_datas(df_transf_estoque, data_inicio, data_fim, 'Data_Transferencia')
  df_transf_estoque = df_transf_estoque.rename(columns={'Casa_Saida': 'Casa Saída', 'Casa_Entrada': 'Casa Entrada', 'Data_Transferencia': 'Data Transferência', 
                                                        'Valor_Transferencia': 'Valor Transferência', 'ID_Insumo_Nivel_5': 'ID Insumo Nível 5', 
                                                        'Unidade_Medida': 'Unidade de Medida', 'Insumo_Nivel_5': 'Nome Insumo'})
  df_transf_estoque.drop(['ID_Transferencia'], axis=1, inplace=True)
  df_saidas = df_transf_estoque[df_transf_estoque['Casa Saída'] == loja]
  df_entradas = df_transf_estoque[df_transf_estoque['Casa Entrada'] == loja]
  df_saidas = df_format_date_brazilian(df_saidas, 'Data Transferência')
  df_entradas = df_format_date_brazilian(df_entradas, 'Data Transferência')
  
  return df_entradas, df_saidas


def highlight_rows_cmv_dre(linha):

  linhas_entrada = [
    '(+) Estoque inicial Alimento',
    '(+) Estoque inicial Bebida',
    '(+) Estoque inicial Produção Alimentos',
    '(+) Estoque inicial Produção Bebidas',
    '(+) Compra de Alimento',
    '(+) Compra de Bebida',
    '(+) Entradas transferência Alimentos',
    '(+) Entradas transferência Bebidas',
  ]

  linhas_saida = [
    '(-) Saídas transferência Alimentos',
    '(-) Saídas transferência Bebidas',
    '(-) Quebras e perdas',
    '(-) Estoque final Alimentos',
    '(-) Estoque final Bebidas',
    '(-) Fechamento Produção Alimentos',
    '(-) Fechamento Produção Bebidas',
  ]

  linhas_amarelo = [
    '(-) Consumo Funcionário',
  ]

  linhas_cinza = [
    '(=) Custo Alimento Vendido',
    '(=) Custo Bebida Vendida',
    'Somatório de A&B',
  ]

  if linha['Descrição'] in linhas_cinza:
    return ['background-color: #E6EAF1'] * len(linha)
  elif linha['Descrição'] in linhas_amarelo:
    return ['background-color: #FFFCE7'] * len(linha)
  elif linha['Descrição'] in linhas_entrada:
    return ['background-color: #E8F2FC'] * len(linha)
  elif linha['Descrição'] in linhas_saida:
    return ['background-color: #FFEDED'] * len(linha)
  else:
    return

