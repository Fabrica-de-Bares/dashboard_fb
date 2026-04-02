import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query

@st.cache_data
def GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE():
    return dataframe_query(f'''
    SELECT
        CASE
            WHEN VIVC.ID_CASA = 118 THEN 114
            WHEN VIVC.ID_CASA = 103 THEN 116
            WHEN VIVC.ID_CASA = 169 THEN 148
            WHEN VIVC.ID_CASA = 139 THEN 105
            WHEN VIVC.ID_CASA = 112 THEN 104
            ELSE VIVC.ID_CASA
        END AS 'ID_CASA',
        CASE
            WHEN VIVC.ID_CASA = 118 THEN 'Bar Brahma - Centro'
            WHEN VIVC.ID_CASA = 103 THEN 'Bar Léo - Centro'
            WHEN VIVC.ID_CASA = 169 THEN 'Bar Brahma - Granja'
            WHEN VIVC.ID_CASA = 139 THEN 'Jacaré'
            WHEN VIVC.ID_CASA = 112 THEN 'Orfeu'
            ELSE VIVC.CASA 
        END AS 'CASA',
        VIVC.ID_ITEM_VENDIDO AS 'ID_ITEM_ZIG',
        VIVC.ITEM_VENDIDO AS 'ITEM VENDIDO ZIG',
        FT.ID AS 'ID_FICHA_TECNICA',
        IE.ID AS 'ID_INSUMO_ESTOQUE',
        IE.DESCRICAO AS 'INSUMO ESTOQUE',
        AIFT.QUANTIDADE_POR_FICHA AS 'QUANTIDADE POR FICHA',
        UM.UNIDADE_MEDIDA AS 'UNIDADE MEDIDA'
    FROM T_FICHAS_TECNICAS FT
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON VIVC.ID = FT.FK_ITEM_VENDIDO_POR_CASA 
        LEFT JOIN T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA AIFT ON AIFT.FK_FICHA_TECNICA = FT.ID
        INNER JOIN T_INSUMOS_ESTOQUE IE ON (AIFT.FK_ITEM_ESTOQUE = IE.ID)
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON UM.ID = AIFT.FK_UNIDADE_MEDIDA 
    GROUP BY VIVC.ID_CASA, FT.ID, IE.ID

''')

@st.cache_data
def GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO():
    return dataframe_query(f'''
    SELECT
        CASE
            WHEN VIVC.ID_CASA = 118 THEN 114
            WHEN VIVC.ID_CASA = 103 THEN 116
            WHEN VIVC.ID_CASA = 169 THEN 148
            WHEN VIVC.ID_CASA = 139 THEN 105
            WHEN VIVC.ID_CASA = 112 THEN 104
            ELSE VIVC.ID_CASA
        END AS 'ID_CASA',
        CASE
            WHEN VIVC.ID_CASA = 118 THEN 'Bar Brahma - Centro'
            WHEN VIVC.ID_CASA = 103 THEN 'Bar Léo - Centro'
            WHEN VIVC.ID_CASA = 169 THEN 'Bar Brahma - Granja'
            WHEN VIVC.ID_CASA = 139 THEN 'Jacaré'
            WHEN VIVC.ID_CASA = 112 THEN 'Orfeu'    
            ELSE VIVC.CASA 
        END AS 'CASA',
        VIVC.ID_ITEM_VENDIDO AS 'ID_ITEM_ZIG',
        VIVC.ITEM_VENDIDO AS 'ITEM VENDIDO ZIG',
        FT.ID AS 'ID_FICHA_TECNICA',
        IP.ID AS 'ID_INSUMO_PRODUÇÃO',
        IP.NOME_ITEM_PRODUZIDO AS 'INSUMO PRODUZIDO',
        AIPFT.QUANTIDADE AS 'QUANTIDADE POR FICHA',
        UM.UNIDADE_MEDIDA AS 'UNIDADE MEDIDA'
    FROM T_FICHAS_TECNICAS FT
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON VIVC.ID = FT.FK_ITEM_VENDIDO_POR_CASA 
        LEFT JOIN T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA AIPFT ON AIPFT.FK_FICHA_TECNICA = FT.ID
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON  UM.ID = AIPFT.FK_UNIDADE_MEDIDA
        INNER JOIN T_ITENS_PRODUCAO IP ON IP.ID = AIPFT.FK_ITEM_PRODUCAO 
    GROUP BY VIVC.ID_CASA, FT.ID, IP.ID
                
''')

@st.cache_data
def GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO():
    return dataframe_query(f'''
    SELECT
        TE.ID AS 'ID_CASA',
        TE.NOME_FANTASIA AS 'CASA',
        FTP.ID AS 'ID_FICHA_TECNICA_PRODUÇÃO',
        IP.ID AS 'ID_ITEM_PRODUZIDO',
        IP.NOME_ITEM_PRODUZIDO AS 'ITEM PRODUZIDO',
        FTP.QUANTIDADE_FICHA AS 'QUANTIDADE RENDIMENTO',
        UM2.UNIDADE_MEDIDA AS 'U.M. RENDIMENTO',
        IE.ID AS 'ID_INSUMO_ESTOQUE',
        IE.DESCRICAO AS 'INSUMO ESTOQUE',
        IP2.ID AS 'ID_INSUMO_PRODUÇÃO',
        IP2.NOME_ITEM_PRODUZIDO AS 'INSUMO PRODUÇÃO',
        AFTIP.QUANTIDADE AS 'QUANTIDADE',
        UM.UNIDADE_MEDIDA AS 'U.M. FICHA ITENS'
    FROM T_FICHA_TECNICA_PRODUCAO FTP
        LEFT JOIN T_ITENS_PRODUCAO IP ON IP.ID = FTP.FK_ITEM_PRODUZIDO
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM2 ON UM2.ID = FTP.FK_UNIDADE_MEDIDA
        LEFT JOIN T_ASSOCIATIVA_FICHAS_TECNICAS_ITENS_PRODUCAO AFTIP ON AFTIP.FK_FICHA_PRODUCAO = FTP.ID
        LEFT JOIN T_EMPRESAS TE ON TE.ID = IP.FK_EMPRESA
        LEFT JOIN T_INSUMOS_ESTOQUE IE ON IE.ID = AFTIP.FK_INSUMO_ESTOQUE
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON UM.ID = AFTIP.UNIDADE_MEDIDA
        LEFT JOIN T_ITENS_PRODUCAO IP2 ON IP2.ID = AFTIP.FK_ITEM_PRODUZIDO
''')

@st.cache_data
def GET_QUANTIDADES_INSUMOS_N5_COM_PROPORCAO_ESTOQUE():
    return dataframe_query(f'''
    SELECT 
            E.ID AS 'ID CASA',
            E.NOME_FANTASIA AS 'CASA',
            DATE(DR.COMPETENCIA) AS 'DATA COMPRA',
            MONTH(DR.COMPETENCIA) AS 'MÊS COMPRA',
            YEAR(DR.COMPETENCIA) AS 'ANO COMPRA',
            N5.ID AS 'ID N5',
            N5.DESCRICAO AS 'INSUMO N5',
            UM.UNIDADE_MEDIDA_NAME AS 'U.M. N5',
            ROUND(CAST(SUM(DRI.VALOR) AS FLOAT), 2) AS 'VALOR N5',
            ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'QUANTIDADE N5',
            SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'PREÇO MÉDIO N5',
            IE.ID AS 'ID INSUMO ESTOQUE',
            IE.DESCRICAO AS 'INSUMO ESTOQUE',
            UM2.UNIDADE_MEDIDA AS 'U.M. INSUMO ESTOQUE',
            ACE.PROPORCAO AS 'PROPORÇÃO ACE',
            ACE.PROPORCAO * ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'QUANTIDADE INSUMO ESTOQUE'
        FROM T_DESPESA_RAPIDA_ITEM DRI 
            INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
            LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
            LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
            LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
            LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
            INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
            INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
            LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON (N5.FK_UNIDADE_MEDIDA = UM.ID)
            LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON (ACE.FK_INSUMO = N5.ID)
            LEFT JOIN T_INSUMOS_ESTOQUE IE ON (IE.ID = ACE.FK_INSUMO_ESTOQUE)
            LEFT JOIN T_UNIDADES_DE_MEDIDAS UM2 ON IE.FK_UNIDADE_MEDIDA = UM2.ID
        WHERE DR.BIT_CANCELADA = 0
        		AND DR.COMPETENCIA >= '2023-01-01'
            AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
            AND E.FK_GRUPO_EMPRESA = 100
        GROUP BY E.ID, N5.ID
        ORDER BY E.NOME_FANTASIA ASC, N5.DESCRICAO
''')


def GET_CASAS_ITENS_PRODUCAO():
    return dataframe_query(f'''
        SELECT
        ID AS 'ID INSUMO PRODUÇÃO',
        FK_EMPRESA AS 'ID CASA PRODUÇÃO'
        FROM T_ITENS_PRODUCAO
    ''')

def GET_DATA_VALIDACAO(data):
    data = pd.to_datetime(data)
    data_str = data.strftime('%Y-%m-%d')

    # Primeiro, verifica qual a última data validada no período solicitado
    query_validacao = f"""
        SELECT MAX(DATA_VALIDACAO) as ultima_validada
        FROM T_VALIDACAO_FATURAMENTO
        WHERE DATA_VALIDACAO <= '{data_str}'
    """

    resultado_validacao = dataframe_query(query_validacao)
    ultima_validada = resultado_validacao['ultima_validada'].iloc[0] if not resultado_validacao.empty else None
  
    # Converte ultima_validada para date object para comparação
    ultima_validada_date = pd.to_datetime(ultima_validada)
    ultima_validada_str = ultima_validada_date.strftime('%Y-%m-%d') if ultima_validada_date else None

    return ultima_validada_date

def GET_VENDAS_POR_DIA_COMPLETO(data, id_casa):
    """
    Busca e retorna a quantidade de itens vendidos em um dia especifico de uma casa
    
    Lógica:
    - Se a data já está totalmente validado: usa apenas o banco de dados
    - Se a data ainda não foi validada: combina banco de dados com API

    Retorna vendas de um dia combinando:
        DataFrame com os dados
    """

    data = pd.to_datetime(data)
    data_str = data.strftime('%Y-%m-%d')

    # Primeiro, verifica qual a última data validada no período solicitado
    query_validacao = f"""
        SELECT MAX(DATA_VALIDACAO) as ultima_validada
        FROM T_VALIDACAO_FATURAMENTO
    """

    resultado_validacao = dataframe_query(query_validacao)
    ultima_validada = resultado_validacao['ultima_validada'].iloc[0] if not resultado_validacao.empty else None
  
    # Converte ultima_validada para date object para comparação
    ultima_validada_date = pd.to_datetime(ultima_validada)
    ultima_validada_str = ultima_validada_date.strftime('%Y-%m-%d') if ultima_validada_date else None

    df = dataframe_query(f"""
        SELECT
            CASE
                WHEN te.ID = 118 THEN 114
                WHEN te.ID = 103 THEN 116
                WHEN te.ID = 169 THEN 148
                WHEN te.ID = 139 THEN 105
                WHEN te.ID = 112 THEN 104
                ELSE te.ID
            END AS `ID Casa`,
            CASE
                WHEN te.ID = 118 THEN 'Bar Brahma - Centro'
                WHEN te.ID = 103 THEN 'Bar Léo - Centro'
                WHEN te.ID = 169 THEN 'Bar Brahma - Granja'
                WHEN te.ID = 139 THEN 'Jacaré'
                WHEN te.ID = 112 THEN 'Orfeu'
                ELSE te.NOME_FANTASIA
            END AS 'Casa',
            DATE(tiv.EVENT_DATE) AS 'Data Venda',
            tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
            tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
            tiv.PRODUCT_NAME AS 'Item Vendido Zig',
            tivc2.DESCRICAO AS 'Categoria',
            tivt.DESCRICAO AS 'Tipo',
            SUM(tiv.COUNT) AS 'Quantidade'
        FROM T_ITENS_VENDIDOS tiv
            LEFT JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tiv.LOJA_ID
            LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                ON tvivpc.ID_ZIG_ITEM_VENDIDO = tiv.PRODUCT_ID
                AND tvivpc.ID_CASA = te.ID
            LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tiv.PRODUCT_ID
            LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
            LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
        WHERE DATE(tiv.EVENT_DATE) <= '{data_str}' AND te.ID = '{id_casa}'
        GROUP BY `ID Casa`, tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)
        ORDER BY `Data Venda`, `ID Casa`, `Product ID`
    """)

    return df


def GET_QUANTIDADE_ITENS_VENDIDOS_COMPLETO(lista_ids_zigpay,data_inicio, data_fim, id_casa):
  """
    Busca quantidade de itens vendidos otimizando consultas entre tabelas.
   
    Lógica:
    - Se período está totalmente validado: usa apenas T_ITENS_VENDIDOS_DIA (rápido)
    - Se período está totalmente não validado: usa apenas T_ITENS_VENDIDOS (necessário)
    - Se período é misto: usa ambas tabelas com UNION
   
    Args:
        data_inicio: string no formato 'YYYY-MM-DD', date, ou Timestamp
        data_fim: string no formato 'YYYY-MM-DD', date, ou Timestamp
        id_casa: int
   
    Returns:
        DataFrame com dados de quantidades
    """
  
  # garante lista
  if not isinstance(lista_ids_zigpay, (list, tuple)):
      lista_ids_zigpay = [lista_ids_zigpay]
      
  if not lista_ids_zigpay:
      return pd.DataFrame()


  # placeholders do IN
  placeholders = ', '.join(['%s'] * len(lista_ids_zigpay))


 
  # Converte as datas de entrada para objetos date
  # Converte as datas de entrada para datetime
  data_inicio_date = pd.to_datetime(data_inicio)
  data_fim_date = pd.to_datetime(data_fim)
  
  # Converte para string no formato SQL
  data_inicio_str = data_inicio_date.strftime('%Y-%m-%d')
  data_fim_str = data_fim_date.strftime('%Y-%m-%d')
  
  print(f"Data início funcao: {data_inicio_str}, Data fim: {data_fim_str}")
  # Primeiro, verifica qual a última data validada no período solicitado
  
#   ultima_validada_date, ultima_validada_str= GET_ULTIMA_VALIDACAO(data_inicio_str, data_fim_str)
  ultima_validada_date = GET_DATA_VALIDACAO(data_fim_str)
  
  ultima_validada_str = ultima_validada_date.strftime('%Y-%m-%d') if ultima_validada_date else None

  # Caso 1: Não há validação no período OU data_inicio > ultima_validada
  # Usa apenas T_ITENS_VENDIDOS (dados não validados)
  if ultima_validada_date is None or data_inicio_date > ultima_validada_date:
      print(f"📊 Consultando apenas T_ITENS_VENDIDOS (período não validado)")
      print(f"   Data início: {data_inicio_date}, Última validada: {ultima_validada_date}")
      query = f'''
          SELECT
              CASE
                  WHEN te.ID = 118 THEN 114
                  WHEN te.ID = 103 THEN 116
                  WHEN te.ID = 169 THEN 148
                  WHEN te.ID = 139 THEN 105
                  WHEN te.ID = 112 THEN 104
                  ELSE te.ID
              END AS 'ID CASA',
              CASE
                  WHEN te.ID = 118 THEN 'Bar Brahma - Centro'
                  WHEN te.ID = 103 THEN 'Bar Léo - Centro'
                  WHEN te.ID = 169 THEN 'Bar Brahma - Granja'
                  WHEN te.ID = 139 THEN 'Jacaré'
                  WHEN te.ID = 112 THEN 'Orfeu'
                  ELSE te.NOME_FANTASIA
              END AS 'CASA',
              tvivpc.ID_ITEM_VENDIDO AS 'ID ITEM ZIG',
              tvivpc.ID_ZIG_ITEM_VENDIDO AS 'PRODUCT ID',
              tiv.PRODUCT_NAME AS 'ITEM VENDIDO ZIG',
              tivc2.DESCRICAO AS 'CATEGORIA',
              tivt.DESCRICAO AS 'TIPO',
              DATE(tiv.EVENT_DATE) AS 'DATA VENDA',
              SUM(tiv.COUNT) AS 'QUANTIDADE'
          FROM T_ITENS_VENDIDOS tiv
              LEFT JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tiv.LOJA_ID
              LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                  ON tvivpc.ID_ZIG_ITEM_VENDIDO = tiv.PRODUCT_ID
                  AND tvivpc.ID_CASA = te.ID
              LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tiv.PRODUCT_ID
              LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
              LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
          WHERE DATE(tiv.EVENT_DATE) BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
            AND te.ID = '{id_casa}'
            AND te.FK_GRUPO_EMPRESA = 100
            AND tivc2.ID IN (100,101,102,103,104)
            AND te.ID_ZIGPAY IN ({placeholders})
          GROUP BY 'ID CASA', tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)
          ORDER BY 'DATA VENDA', 'ID CASA', 'PRODUCT ID'
      '''
  
  # Caso 2: data_fim <= ultima_validada
  # Usa apenas T_ITENS_VENDIDOS_DIA (rápido, dados validados)
  elif data_fim_date <= ultima_validada_date:
      print(f"⚡ Consultando apenas T_ITENS_VENDIDOS_DIA (período validado - otimizado)")
      print(f"   Data fim: {data_fim_date}, Última validada: {ultima_validada_date}")
      query = f'''
          SELECT
              CASE
                  WHEN tivd.FK_CASA = 118 THEN 114
                  WHEN tivd.FK_CASA = 103 THEN 116
                  WHEN tivd.FK_CASA = 169 THEN 148
                  WHEN tivd.FK_CASA = 139 THEN 105
                  WHEN tivd.FK_CASA = 112 THEN 104
                  ELSE tivd.FK_CASA
              END AS 'ID CASA',
              CASE
                  WHEN tivd.FK_CASA = 118 THEN 'BAR BRAHMA - CENTRO'
                  WHEN tivd.FK_CASA = 103 THEN 'BAR LÉO - CENTRO'
                  WHEN tivd.FK_CASA = 169 THEN 'BAR BRAHMA - GRANJA'
                  WHEN tivd.FK_CASA = 139 THEN 'JACARÉ'
                  WHEN tivd.FK_CASA = 112 THEN 'ORFEU'
                  ELSE te.NOME_FANTASIA
              END AS 'CASA',
              TVIVPC.ID_ITEM_VENDIDO AS 'ID ITEM ZIG',
              TVIVPC.ID_ZIG_ITEM_VENDIDO AS 'PRODUCT ID',
              tivd.PRODUCT_NAME AS 'ITEM VENDIDO ZIG',
              tivc2.DESCRICAO AS 'CATEGORIA',
              tivt.DESCRICAO AS 'TIPO',
              DATE(tivd.EVENT_DATE) AS 'DATA VENDA',
              SUM(tivd.QUANTIDADE) AS 'QUANTIDADE'
          FROM T_ITENS_VENDIDOS_DIA tivd
              LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA
              LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                  ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
                  AND tvivpc.ID_CASA = tivd.FK_CASA
              LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
              LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
              LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
          WHERE DATE(tivd.EVENT_DATE) BETWEEN '{data_inicio}' AND '{data_fim}' 
              AND tivd.FK_CASA = '{id_casa}'     
              AND te.FK_GRUPO_EMPRESA = 100
              AND tivc2.ID IN (100,101,102,103,104)
              AND te.ID_ZIGPAY IN ({placeholders})        
          GROUP BY 'ID CASA', TVIVPC.ID_ZIG_ITEM_VENDIDO, DATE(TIVD.EVENT_DATE)
          ORDER BY 'DATA VENDA', 'ID CASA', 'PRODUCT ID'
      '''
  
  # Caso 3: Período misto (data_inicio <= ultima_validada < data_fim)
  # Usa ambas tabelas com UNION
  else:
      print(f"🔄 Consultando ambas tabelas (período misto: validado até {ultima_validada_date})")
      print(f"   Período: {data_inicio_date} a {data_fim_date}")
      query = f'''
          WITH dados_historicos AS (
              SELECT
                  CASE
                      WHEN tivd.FK_CASA = 118 THEN 114
                      WHEN tivd.FK_CASA = 103 THEN 116
                      WHEN tivd.FK_CASA = 169 THEN 148
                      WHEN tivd.FK_CASA = 139 THEN 105
                      WHEN tivd.FK_CASA = 112 THEN 104
                      ELSE tivd.FK_CASA
                  END AS 'ID CASA',
                  CASE
                      WHEN tivd.FK_CASA = 118 THEN 'Bar Brahma - Centro'
                      WHEN tivd.FK_CASA = 103 THEN 'Bar Léo - Centro'
                      WHEN tivd.FK_CASA = 169 THEN 'Bar Brahma - Granja'
                      WHEN tivd.FK_CASA = 139 THEN 'Jacaré'
                      WHEN tivd.FK_CASA = 112 THEN 'Orfeu'
                      ELSE te.NOME_FANTASIA
                  END AS 'CASA',
                  tvivpc.ID_ITEM_VENDIDO AS 'ID ITEM ZIG',
                  tvivpc.ID_ZIG_ITEM_VENDIDO AS 'PRODUCT ID',
                  tivd.PRODUCT_NAME AS 'ITEM VENDIDO ZIG',
                  tivc2.DESCRICAO AS 'CATEGORIA',
                  tivt.DESCRICAO AS 'TIPO',
                  DATE(tivd.EVENT_DATE) AS 'DATA VENDA',
                  SUM(tivd.QUANTIDADE) AS 'QUANTIDADE'
              FROM T_ITENS_VENDIDOS_DIA tivd
                  LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA
                  LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                      ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
                      AND tvivpc.ID_CASA = tivd.FK_CASA
                  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
                  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
                  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
              WHERE DATE(tivd.EVENT_DATE) BETWEEN '{data_inicio_str}' AND '{ultima_validada_str}'
                  AND te.ID = '{id_casa}'
                  AND te.FK_GRUPO_EMPRESA = 100
                  AND tivc2.ID IN (100,101,102,103,104)
                  AND te.ID_ZIGPAY IN ({placeholders})
              GROUP BY 'ID CASA', tvivpc.ID_ZIG_ITEM_VENDIDO, DATE(tivd.EVENT_DATE)
          ),
          dados_recentes AS (
              SELECT
                  CASE
                      WHEN te.ID = 118 THEN 114
                      WHEN te.ID = 103 THEN 116
                      WHEN te.ID = 169 THEN 148
                      WHEN te.ID = 139 THEN 105
                      WHEN te.ID = 112 THEN 104
                      ELSE te.ID
                  END AS 'ID CASA',
                  CASE
                      WHEN te.ID = 118 THEN 'Bar Brahma - Centro'
                      WHEN te.ID = 103 THEN 'Bar Léo - Centro'
                      WHEN te.ID = 169 THEN 'Bar Brahma - Granja'
                      WHEN te.ID = 139 THEN 'Jacaré'
                      WHEN te.ID = 112 THEN 'Orfeu'
                      ELSE te.NOME_FANTASIA
                  END AS 'CASA',
                  tvivpc.ID_ITEM_VENDIDO AS 'ID ITEM ZIG',
                  tvivpc.ID_ZIG_ITEM_VENDIDO AS 'PRODUCT ID',
                  tiv.PRODUCT_NAME AS 'ITEM VENDIDO ZIG',
                  tivc2.DESCRICAO AS 'CATEGORIA',
                  tivt.DESCRICAO AS 'TIPO',
                  DATE(tiv.EVENT_DATE) AS 'DATA VENDA',
                  SUM(tiv.COUNT) AS 'QUANTIDADE'
              FROM T_ITENS_VENDIDOS tiv
                  LEFT JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tiv.LOJA_ID
                  LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                      ON tvivpc.ID_ZIG_ITEM_VENDIDO = tiv.PRODUCT_ID
                      AND tvivpc.ID_CASA = te.ID
                  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tiv.PRODUCT_ID
                  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
                  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
              WHERE DATE(tiv.EVENT_DATE) > '{ultima_validada_str}'
                AND DATE(tiv.EVENT_DATE) <= '{data_fim_str}'
                AND te.ID = '{id_casa}'    
                AND te.FK_GRUPO_EMPRESA = 100
                AND tivc2.ID IN (100,101,102,103,104)
                AND te.ID_ZIGPAY IN ({placeholders})
              GROUP BY 'ID CASA', tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)
          )
          SELECT * FROM dados_historicos
          UNION ALL
          SELECT * FROM dados_recentes
          ORDER BY 'DATA VENDA', 'ID CASA', 'PRODUCT ID'
      '''

  params = lista_ids_zigpay

  return dataframe_query(query, params)

@st.cache_data
def GET_VALORACAO_ESTOQUE(loja, data_contagem):
  return dataframe_query(f'''
  SELECT
  	te.ID AS 'ID_LOJA',
  	te.NOME_FANTASIA AS 'LOJA',
  	tin5.ID AS 'ID_INSUMO',
  	REPLACE(tin5.DESCRICAO, ',', '.') AS 'INSUMO',
  	tci.QUANTIDADE_INSUMO AS 'QUANTIDADE',
  	tin5.FK_INSUMOS_NIVEL_4 AS 'ID_NIVEL_4',
  	tudm.UNIDADE_MEDIDA_NAME AS 'UNIDADE_MEDIDA',
    tin.DESCRICAO AS 'CATEGORIA',
  	tve.VALOR_EM_ESTOQUE AS 'VALOR_EM_ESTOQUE',
  	tci.DATA_CONTAGEM
  FROM T_VALORACAO_ESTOQUE tve
  LEFT JOIN T_CONTAGEM_INSUMOS tci ON tve.FK_CONTAGEM = tci.ID
  LEFT JOIN T_EMPRESAS te ON tci.FK_EMPRESA = te.ID
  LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tci.FK_INSUMO = tin5.ID
  LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID
  LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID
  LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.ID
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tin5.FK_UNIDADE_MEDIDA = tudm.ID
  WHERE tci.QUANTIDADE_INSUMO != 0
  ORDER BY DATA_CONTAGEM DESC
  ''')

@st.cache_data
def GET_ULTIMA_VALIDACAO(data_inicio_str, data_fim_str):
    query = f'''
      SELECT MAX(DATA_VALIDACAO) as ultima_validada
      FROM T_VALIDACAO_FATURAMENTO
      WHERE DATA_VALIDACAO BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
  '''
    resultado = dataframe_query(query)
    
    if resultado.empty or pd.isna(resultado['ultima_validada'].iloc[0]):
        return None, None

    ultima_validada = pd.to_datetime(resultado['ultima_validada'].iloc[0])
   
    print(f"data_validado={ultima_validada}")

    # Converte ultima_validada para date object para comparação
    ultima_validada_date = pd.to_datetime(ultima_validada)
    ultima_validada_str = ultima_validada_date.strftime('%Y-%m-%dT%H:%M:%S') if ultima_validada_date else None

    return ultima_validada_date, ultima_validada_str
  

@st.cache_data
def GET_VALORACAO_PRODUCAO(data):
  return dataframe_query(f'''
  SELECT
    te.ID as 'ID_LOJA',
    te.NOME_FANTASIA as 'LOJA',
    tipc.DATA_CONTAGEM as 'DATA_CONTAGEM',
    DATE_FORMAT(DATE_SUB(tipc.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') AS 'MES_TEXTO',
    tip.NOME_ITEM_PRODUZIDO as 'ITEM_PRODUZIDO',
    tipc.QUANTIDADE_INSUMO as 'QUANTIDADE',
    tudm.UNIDADE_MEDIDA_NAME as 'UNIDADE_MEDIDA',
    tipv.VALOR as 'VALOR_UNIDADE_MEDIDA',
    ROUND(tipc.QUANTIDADE_INSUMO * tipv.VALOR, 2) as 'VALOR_TOTAL',
    tin.DESCRICAO as 'CATEGORIA'
  FROM T_ITENS_PRODUCAO_CONTAGEM tipc
  LEFT JOIN T_ITENS_PRODUCAO_VALORACAO tipv ON (tipc.FK_ITEM_PRODUZIDO = tipv.FK_ITEM_PRODUZIDO) AND (DATE_FORMAT(tipc.DATA_CONTAGEM, '%m/%Y') = DATE_FORMAT(tipv.DATA_VALORACAO, '%m/%Y'))
  LEFT JOIN T_ITENS_PRODUCAO tip ON (tipv.FK_ITEM_PRODUZIDO = tip.ID)
  LEFT JOIN T_EMPRESAS te ON (tip.FK_EMPRESA = te.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON (tip.FK_INSUMO_NIVEL_1 = tin.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tip.FK_UNIDADE_MEDIDA = tudm.ID)
  WHERE tipc.DATA_CONTAGEM = '{data}'
  ''')


#COMPRAS
@st.cache_data
def GET_INSUMOS_BLUE_ME_COM_PEDIDO(data_inicio, data_fim, loja):
  return dataframe_query(f'''
    SELECT
      tdr.ID AS 'ID_DESPESA',
      te.ID AS 'ID_LOJA',
      CASE 
      	WHEN te.NOME_FANTASIA = 'Girondino' THEN 'Girondino - Agregado'
      	WHEN te.NOME_FANTASIA = 'Girondino - CCBB' THEN 'Girondino - Agregado'
      	WHEN te.NOME_FANTASIA = 'Blue Note - São Paulo' THEN 'Blue Note - Agregado'
      	WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - Agregado'
        WHEN te.NOME_FANTASIA = 'The Cavern' THEN 'The Cavern - Agregado'
        WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern - Agregado'
      	ELSE te.NOME_FANTASIA
      END AS 'LOJA',
      tf.CORPORATE_NAME AS 'FORNECEDOR',
      tdr.NF AS 'DOC_SERIE',
      tdr.COMPETENCIA AS 'DATA_EMISSAO',
      tin5.DESCRICAO AS 'INSUMO ITEM',
      tdri.QUANTIDADE AS 'QUANTIDADE',
      tdri.UNIDADE_MEDIDA AS 'UNIDADE MEDIDA',
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE),'%Y-%m-01') AS DATE) AS 'PRIMEIRO_DIA_MES'
    FROM
      T_DESPESA_RAPIDA tdr
      JOIN T_EMPRESAS te
        ON tdr.FK_LOJA = te.ID
      LEFT JOIN T_FORNECEDOR tf
        ON tdr.FK_FORNECEDOR = tf.ID
      JOIN T_DESPESA_RAPIDA_ITEM tdri
        ON tdr.ID = tdri.FK_DESPESA_RAPIDA
      LEFT JOIN T_INSUMOS_NIVEL_5 tin5
        ON tdri.FK_INSUMO = tin5.ID
      LEFT JOIN T_INSUMOS_NIVEL_4 tin4
        ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID
      LEFT JOIN T_INSUMOS_NIVEL_3 tin3
        ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID
      LEFT JOIN T_INSUMOS_NIVEL_2 tin2
        ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
      LEFT JOIN T_INSUMOS_NIVEL_1 tin1
        ON tin2.FK_INSUMOS_NIVEL_1 = tin1.ID
    WHERE DATE(tdr.COMPETENCIA) BETWEEN DATE('{data_inicio}') AND DATE('{data_fim}')
      AND (
        CASE 
          WHEN te.NOME_FANTASIA = 'Girondino' THEN 'Girondino - Agregado'
          WHEN te.NOME_FANTASIA = 'Girondino - CCBB' THEN 'Girondino - Agregado'
          WHEN te.NOME_FANTASIA = 'Blue Note - São Paulo' THEN 'Blue Note - Agregado'
          WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - Agregado'
          WHEN te.NOME_FANTASIA = 'The Cavern' THEN 'The Cavern - Agregado'
          WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern - Agregado'
          ELSE te.NOME_FANTASIA
        END
		  ) = '{loja}'
      AND tdri.ID IS NOT NULL
      AND te.ID <> 135
      AND tdr.BIT_CANCELADA = 0
    GROUP BY
      tdr.ID,
      te.ID,
      te.NOME_FANTASIA,
      tf.CORPORATE_NAME,
      tdr.NF,
      tdr.COMPETENCIA,
      tdr.VALOR_LIQUIDO
''')


@st.cache_data
def GET_TRANSF_ESTOQUE():
  return dataframe_query(f'''
  SELECT
    tti.ID as 'ID_TRANSFERENCIA',
    te.ID as 'ID_LOJA_SAIDA',
    te.NOME_FANTASIA as 'CASA_SAIDA',
    te2.ID as 'ID_LOJA_ENTRADA',
    te2.NOME_FANTASIA as 'CASA_ENTRADA',
    tti.DATA_TRANSFERENCIA as 'DATA_TRANSFERENCIA',
    tin5.ID as 'ID_INSUMO_NIVEL_5',
    tin5.DESCRICAO as 'INSUMO_NIVEL_5',
    tin.DESCRICAO as 'CATEGORIA',
    tti.QUANTIDADE as 'QUANTIDADE',
    tudm.UNIDADE_MEDIDA_NAME as 'UNIDADE_MEDIDA',
    tti.OBSERVACAO as 'OBSERVACAO'
  FROM T_TRANSFERENCIAS_INSUMOS tti 
    LEFT JOIN T_EMPRESAS te ON (tti.FK_EMRPESA_SAIDA = te.ID)
    LEFT JOIN T_EMPRESAS te2 ON tti.FK_EMPRESA_ENTRADA = te2.ID
    LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tti.FK_INSUMO_NIVEL_5 = tin5.ID
    LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
    LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
    LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID 
    LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.id
    LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  ORDER BY tti.ID DESC
''')

@st.cache_data
def GET_QUANTIDADE_ZIGPAY_VENDA(lista_ids_zigpay, mes, ano, dia):

    # garante lista
    if not isinstance(lista_ids_zigpay, (list, tuple)):
        lista_ids_zigpay = [lista_ids_zigpay]

    if not lista_ids_zigpay:
        return pd.DataFrame()

    # placeholders do IN
    placeholders = ', '.join(['%s'] * len(lista_ids_zigpay))

    query = f'''
        SELECT
            te.ID AS 'ID CASA',
            CAST(tiv.EVENT_DATE AS DATE) AS 'DATA EVENTO',
            tvivpc.ID_ZIG_ITEM_VENDIDO AS 'PRODUCT ID',
            tiv.PRODUCT_NAME AS 'ITEM VENDIDO ZIG',
            SUM(tiv.COUNT) AS 'QUANTIDADE'
        FROM T_ITENS_VENDIDOS tiv
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc 
            ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 
            ON tivc.FK_CATEGORIA = tivc2.ID
        LEFT JOIN T_EMPRESAS te 
            ON tiv.LOJA_ID = te.ID_ZIGPAY
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
            ON tvivpc.ID_ZIG_ITEM_VENDIDO = tiv.PRODUCT_ID
            AND tvivpc.ID_CASA = te.ID
        WHERE MONTH(tiv.EVENT_DATE) = %s 
          AND YEAR(tiv.EVENT_DATE) = %s
          AND DAY(tiv.EVENT_DATE)
          AND te.FK_GRUPO_EMPRESA = 100
          AND tivc2.ID IN (100,101,102,103,104)
          AND te.ID_ZIGPAY IN ({placeholders})
        GROUP BY te.ID,tiv.PRODUCT_ID, CAST(tiv.EVENT_DATE AS DATE)
        ORDER BY tiv.EVENT_DATE
    '''

    params = [mes, ano] + list(lista_ids_zigpay)

    return dataframe_query(query, params)


def GET_ULTIMA_DATA_CONTAGEM(data, id_casa):

    data_str = data.strftime('%Y-%m-%d')

    data_contagem = dataframe_query(f'''
        SELECT
            DATE(MAX(DATA_CONTAGEM)) AS ULTIMA_DATA_CONTAGEM
        FROM T_CONTAGEM_INSUMOS tci
        WHERE tci.DATA_CONTAGEM <= '{data_str}' AND tci.FK_EMPRESA = {id_casa}
    ''')
    return data_contagem['ULTIMA_DATA_CONTAGEM'].iloc[0]