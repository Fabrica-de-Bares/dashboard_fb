import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query, execute_query


# CMV Teórico - Análise de Fichas Técnicas
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
          END AS `ID Casa`,
          CASE
              WHEN VIVC.ID_CASA = 118 THEN 'Bar Brahma - Centro'
              WHEN VIVC.ID_CASA = 103 THEN 'Bar Léo - Centro'
              WHEN VIVC.ID_CASA = 169 THEN 'Bar Brahma - Granja'
              WHEN VIVC.ID_CASA = 139 THEN 'Jacaré'
              WHEN VIVC.ID_CASA = 112 THEN 'Orfeu'
              ELSE VIVC.CASA 
          END AS 'Casa',
          VIVC.ID_ITEM_VENDIDO AS 'ID Item Zig',
          VIVC.ITEM_VENDIDO AS 'Item Vendido Zig',
          FT.ID AS 'ID Ficha Técnica',
          IE.ID AS 'ID Insumo Estoque',
          IE.DESCRICAO AS 'Insumo Estoque',
          AIFT.QUANTIDADE_POR_FICHA AS 'Quantidade na Ficha',
          UM.UNIDADE_MEDIDA AS 'Unidade Medida',
          0 AS 'Produção?'
      FROM T_FICHAS_TECNICAS FT
      LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON FT.FK_ITEM_VENDIDO_POR_CASA = VIVC.ID
      LEFT JOIN T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA AIFT ON AIFT.FK_FICHA_TECNICA = FT.ID
      LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON AIFT.FK_UNIDADE_MEDIDA = UM.ID
      INNER JOIN T_INSUMOS_ESTOQUE IE ON AIFT.FK_ITEM_ESTOQUE = IE.ID
      GROUP BY `ID Casa`, FT.ID, IE.ID;
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
            END AS `ID Casa`,
          CASE
              WHEN VIVC.ID_CASA = 118 THEN 'Bar Brahma - Centro'
              WHEN VIVC.ID_CASA = 103 THEN 'Bar Léo - Centro'
              WHEN VIVC.ID_CASA = 169 THEN 'Bar Brahma - Granja'
              WHEN VIVC.ID_CASA = 139 THEN 'Jacaré'
              WHEN VIVC.ID_CASA = 112 THEN 'Orfeu'
              ELSE VIVC.CASA 
          END AS 'Casa',
          VIVC.ID_ITEM_VENDIDO AS 'ID Item Zig',
          VIVC.ITEM_VENDIDO AS 'Item Vendido Zig',
          FT.ID AS 'ID Ficha Técnica',
          IP.ID AS 'ID Insumo Produção',
          IP.NOME_ITEM_PRODUZIDO AS 'Insumo Produção',
          AIPFT.QUANTIDADE AS 'Quantidade na Ficha',
          UM.UNIDADE_MEDIDA AS 'Unidade Medida',
          1 AS 'Produção?'
        FROM T_FICHAS_TECNICAS FT
          LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON FT.FK_ITEM_VENDIDO_POR_CASA = VIVC.ID
          LEFT JOIN T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA AIPFT ON AIPFT.FK_FICHA_TECNICA = FT.ID
          LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON AIPFT.FK_UNIDADE_MEDIDA = UM.ID
          INNER JOIN T_ITENS_PRODUCAO IP ON AIPFT.FK_ITEM_PRODUCAO = IP.ID
        GROUP BY `ID Casa`, FT.ID, IP.ID
    ''')

@st.cache_data
def GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO():
    return dataframe_query(f'''
        SELECT
            te.ID AS 'ID Casa',
            te.NOME_FANTASIA AS 'Casa',
            tftp.ID AS 'ID Ficha Técnica Produção',
            tip.ID AS 'ID Item Produzido',
            tip.NOME_ITEM_PRODUZIDO AS 'Item Produzido',
            tftp.QUANTIDADE_FICHA AS 'Quantidade Rendimento',
            tudm2.UNIDADE_MEDIDA AS 'U.M. Rendimento',
            tie.ID AS 'ID Insumo Estoque',
            tie.DESCRICAO AS 'Insumo Estoque',
            tip2.ID AS 'ID Insumo Produção',
            tip2.NOME_ITEM_PRODUZIDO AS 'Insumo Produção',
            taftip.QUANTIDADE AS 'Quantidade',
            tudm.UNIDADE_MEDIDA AS 'U.M. Ficha Itens',
            CASE WHEN tip2.ID IS NULL THEN 0 ELSE 1 END AS 'Produção?'
        FROM
            T_FICHA_TECNICA_PRODUCAO tftp
            LEFT JOIN T_ITENS_PRODUCAO tip ON tip.ID = tftp.FK_ITEM_PRODUZIDO
            LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm2 ON tudm2.ID = tftp.FK_UNIDADE_MEDIDA
            LEFT JOIN T_ASSOCIATIVA_FICHAS_TECNICAS_ITENS_PRODUCAO taftip ON taftip.FK_FICHA_PRODUCAO = tftp.ID
            LEFT JOIN T_EMPRESAS te ON te.ID = tip.FK_EMPRESA
            LEFT JOIN T_INSUMOS_ESTOQUE tie ON tie.ID = taftip.FK_INSUMO_ESTOQUE
            LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tudm.ID = taftip.UNIDADE_MEDIDA
            LEFT JOIN T_ITENS_PRODUCAO tip2 ON tip2.ID = taftip.FK_ITEM_PRODUZIDO
    ''')


@st.cache_data
def GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE():
    return dataframe_query(f'''
        SELECT 
            E.ID AS 'ID Casa',
            E.NOME_FANTASIA AS 'Casa',
            DATE(DR.COMPETENCIA) AS 'Data Compra',
            MONTH(DR.COMPETENCIA) AS 'Mês Compra',
            YEAR(DR.COMPETENCIA) AS 'Ano Compra',
            N5.ID AS 'ID N5',
            N5.DESCRICAO AS 'Insumo N5',
            UM.UNIDADE_MEDIDA_NAME AS 'U.M. N5',
            ROUND(CAST(SUM(DRI.VALOR) AS FLOAT), 2) AS 'Valor N5',
            ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'Quantidade N5',
            SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Preço Médio N5',
            IE.ID AS 'ID Insumo Estoque',
            IE.DESCRICAO AS 'Insumo Estoque',
            UM2.UNIDADE_MEDIDA AS 'U.M. Insumo Estoque',
            ACE.PROPORCAO AS 'Proporção ACE',
            ACE.PROPORCAO * ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'Quantidade Insumo Estoque',
            (SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE)) / ACE.PROPORCAO AS 'Preço Médio Insumo N5 Estoque'
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
        ID AS 'ID Insumo Produção',
        FK_EMPRESA AS 'ID Casa Produção'
        FROM T_ITENS_PRODUCAO
    ''')


@st.cache_data
def GET_FATURAMENTO_ITENS_VENDIDOS_DIA():
  return dataframe_query(f'''
    SELECT 
      CASE
        WHEN tivd.FK_CASA = 118 THEN 114
        WHEN tivd.FK_CASA = 103 THEN 116
        WHEN tivd.FK_CASA = 169 THEN 148
        WHEN tivd.FK_CASA = 139 THEN 105
        WHEN tivd.FK_CASA = 112 THEN 104
        ELSE tivd.FK_CASA
      END AS `ID Casa`,
      CASE
        WHEN tivd.FK_CASA = 118 THEN 'Bar Brahma - Centro'
        WHEN tivd.FK_CASA = 103 THEN 'Bar Léo - Centro'
        WHEN tivd.FK_CASA = 169 THEN 'Bar Brahma - Granja'
        WHEN tivd.FK_CASA = 139 THEN 'Jacaré'
        WHEN tivd.FK_CASA = 112 THEN 'Orfeu'
        ELSE te.NOME_FANTASIA
      END AS 'Casa',
          tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
          tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
          tivd.PRODUCT_NAME AS 'Item Vendido Zig',
          tivc2.DESCRICAO AS 'Categoria',
          tivt.DESCRICAO AS 'Tipo',
          DATE(tivd.EVENT_DATE) AS 'Data Venda',
          SUM(QUANTIDADE * VALOR_UNITARIO) / SUM(QUANTIDADE) AS 'Valor Unitário',
          SUM(tivd.QUANTIDADE) AS 'Quantidade',
          SUM(tivd.DESCONTO) AS 'Desconto',
          SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Faturamento Bruto',
          SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Faturamento Líquido'
        FROM T_ITENS_VENDIDOS_DIA tivd
        LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA 
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc 
          ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
          AND tvivpc.ID_CASA = tivd.FK_CASA
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA 
        LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
        GROUP BY `ID Casa`, tvivpc.ID_ZIG_ITEM_VENDIDO, DATE(tivd.EVENT_DATE)
  ''')

def GET_FATURAMENTO_ITENS_VENDIDOS_COMPLETO(data_inicio, data_fim, id_casa):
  """
    Busca faturamento de itens vendidos otimizando consultas entre tabelas.
   
    Lógica:
    - Se período está totalmente validado: usa apenas T_ITENS_VENDIDOS_DIA (rápido)
    - Se período está totalmente não validado: usa apenas T_ITENS_VENDIDOS (necessário)
    - Se período é misto: usa ambas tabelas com UNION
   
    Args:
        data_inicio: string no formato 'YYYY-MM-DD', date, ou Timestamp
        data_fim: string no formato 'YYYY-MM-DD', date, ou Timestamp
        id_casa: int
   
    Returns:
        DataFrame com dados de faturamento
    """
 
  # Converte as datas de entrada para objetos date
  # Converte as datas de entrada para datetime
  data_inicio_date = pd.to_datetime(data_inicio)
  data_fim_date = pd.to_datetime(data_fim)
  
  # Converte para string no formato SQL
  data_inicio_str = data_inicio_date.strftime('%Y-%m-%d')
  data_fim_str = data_fim_date.strftime('%Y-%m-%d')
  
  # Primeiro, verifica qual a última data validada no período solicitado
  query_validacao = f'''
      SELECT MAX(DATA_VALIDACAO) as ultima_validada
      FROM T_VALIDACAO_FATURAMENTO
      WHERE DATA_VALIDACAO BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
  '''
  
  resultado_validacao = dataframe_query(query_validacao)
  ultima_validada = resultado_validacao['ultima_validada'].iloc[0] if not resultado_validacao.empty else None
  
  # Converte ultima_validada para date object para comparação
  ultima_validada_date = pd.to_datetime(ultima_validada)
  ultima_validada_str = ultima_validada_date.strftime('%Y-%m-%d') if ultima_validada_date else None
  
  # Caso 1: Não há validação no período OU data_inicio > ultima_validada
  # Usa apenas T_ITENS_VENDIDOS (dados não validados)
  if ultima_validada_date is None or data_inicio_date > ultima_validada_date:
      print(f"📊 Consultando apenas T_ITENS_VENDIDOS (período não validado)")
      print(f"   Data início: {data_inicio_date}, Última validada: {ultima_validada_date}")
      return dataframe_query(f'''
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
              tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
              tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
              tiv.PRODUCT_NAME AS 'Item Vendido Zig',
              tivc2.DESCRICAO AS 'Categoria',
              tivt.DESCRICAO AS 'Tipo',
              DATE(tiv.EVENT_DATE) AS 'Data Venda',
              SUM(tiv.COUNT * tiv.UNIT_VALUE) / SUM(tiv.COUNT) AS 'Valor Unitário',
              SUM(tiv.COUNT) AS 'Quantidade',
              SUM(tiv.DISCOUNT_VALUE) AS 'Desconto',
              SUM(COALESCE((tiv.UNIT_VALUE * tiv.COUNT), 0)) AS 'Faturamento Bruto',
              SUM(COALESCE(((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE), 0)) AS 'Faturamento Líquido'
          FROM T_ITENS_VENDIDOS tiv
              LEFT JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tiv.LOJA_ID
              LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                  ON tvivpc.ID_ZIG_ITEM_VENDIDO = tiv.PRODUCT_ID
                  AND tvivpc.ID_CASA = te.ID
              LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tiv.PRODUCT_ID
              LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
              LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
          WHERE DATE(tiv.EVENT_DATE) BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND te.ID = '{id_casa}'
          GROUP BY `ID Casa`, tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)
          ORDER BY `Data Venda`, `ID Casa`, `Product ID`
      ''')
  
  # Caso 2: data_fim <= ultima_validada
  # Usa apenas T_ITENS_VENDIDOS_DIA (rápido, dados validados)
  elif data_fim_date <= ultima_validada_date:
      print(f"⚡ Consultando apenas T_ITENS_VENDIDOS_DIA (período validado - otimizado)")
      print(f"   Data fim: {data_fim_date}, Última validada: {ultima_validada_date}")
      return dataframe_query(f'''
          SELECT
              CASE
                  WHEN tivd.FK_CASA = 118 THEN 114
                  WHEN tivd.FK_CASA = 103 THEN 116
                  WHEN tivd.FK_CASA = 169 THEN 148
                  WHEN tivd.FK_CASA = 139 THEN 105
                  WHEN tivd.FK_CASA = 112 THEN 104
                  ELSE tivd.FK_CASA
              END AS `ID Casa`,
              CASE
                  WHEN tivd.FK_CASA = 118 THEN 'Bar Brahma - Centro'
                  WHEN tivd.FK_CASA = 103 THEN 'Bar Léo - Centro'
                  WHEN tivd.FK_CASA = 169 THEN 'Bar Brahma - Granja'
                  WHEN tivd.FK_CASA = 139 THEN 'Jacaré'
                  WHEN tivd.FK_CASA = 112 THEN 'Orfeu'
                  ELSE te.NOME_FANTASIA
              END AS 'Casa',
              tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
              tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
              tivd.PRODUCT_NAME AS 'Item Vendido Zig',
              tivc2.DESCRICAO AS 'Categoria',
              tivt.DESCRICAO AS 'Tipo',
              DATE(tivd.EVENT_DATE) AS 'Data Venda',
              SUM(QUANTIDADE * VALOR_UNITARIO) / SUM(QUANTIDADE) AS 'Valor Unitário',
              SUM(tivd.QUANTIDADE) AS 'Quantidade',
              SUM(tivd.DESCONTO) AS 'Desconto',
              SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Faturamento Bruto',
              SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Faturamento Líquido'
          FROM T_ITENS_VENDIDOS_DIA tivd
              LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA
              LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                  ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
                  AND tvivpc.ID_CASA = tivd.FK_CASA
              LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
              LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
              LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
          WHERE DATE(tivd.EVENT_DATE) BETWEEN '{data_inicio}' AND '{data_fim}' AND tivd.FK_CASA = '{id_casa}'
          GROUP BY `ID Casa`, tvivpc.ID_ZIG_ITEM_VENDIDO, DATE(tivd.EVENT_DATE)
          ORDER BY `Data Venda`, `ID Casa`, `Product ID`
      ''')
  
  # Caso 3: Período misto (data_inicio <= ultima_validada < data_fim)
  # Usa ambas tabelas com UNION
  else:
      print(f"🔄 Consultando ambas tabelas (período misto: validado até {ultima_validada_date})")
      print(f"   Período: {data_inicio_date} a {data_fim_date}")
      return dataframe_query(f'''
          WITH dados_historicos AS (
              SELECT
                  CASE
                      WHEN tivd.FK_CASA = 118 THEN 114
                      WHEN tivd.FK_CASA = 103 THEN 116
                      WHEN tivd.FK_CASA = 169 THEN 148
                      WHEN tivd.FK_CASA = 139 THEN 105
                      WHEN tivd.FK_CASA = 112 THEN 104
                      ELSE tivd.FK_CASA
                  END AS `ID Casa`,
                  CASE
                      WHEN tivd.FK_CASA = 118 THEN 'Bar Brahma - Centro'
                      WHEN tivd.FK_CASA = 103 THEN 'Bar Léo - Centro'
                      WHEN tivd.FK_CASA = 169 THEN 'Bar Brahma - Granja'
                      WHEN tivd.FK_CASA = 139 THEN 'Jacaré'
                      WHEN tivd.FK_CASA = 112 THEN 'Orfeu'
                      ELSE te.NOME_FANTASIA
                  END AS 'Casa',
                  tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
                  tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
                  tivd.PRODUCT_NAME AS 'Item Vendido Zig',
                  tivc2.DESCRICAO AS 'Categoria',
                  tivt.DESCRICAO AS 'Tipo',
                  DATE(tivd.EVENT_DATE) AS 'Data Venda',
                  SUM(QUANTIDADE * VALOR_UNITARIO) / SUM(QUANTIDADE) AS 'Valor Unitário',
                  SUM(tivd.QUANTIDADE) AS 'Quantidade',
                  SUM(tivd.DESCONTO) AS 'Desconto',
                  SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Faturamento Bruto',
                  SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Faturamento Líquido'
              FROM T_ITENS_VENDIDOS_DIA tivd
                  LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA
                  LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc
                      ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
                      AND tvivpc.ID_CASA = tivd.FK_CASA
                  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
                  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
                  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
              WHERE DATE(tivd.EVENT_DATE) BETWEEN '{data_inicio_str}' AND '{ultima_validada_str}' AND te.ID = '{id_casa}'
              GROUP BY `ID Casa`, tvivpc.ID_ZIG_ITEM_VENDIDO, DATE(tivd.EVENT_DATE)
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
                  END AS `ID Casa`,
                  CASE
                      WHEN te.ID = 118 THEN 'Bar Brahma - Centro'
                      WHEN te.ID = 103 THEN 'Bar Léo - Centro'
                      WHEN te.ID = 169 THEN 'Bar Brahma - Granja'
                      WHEN te.ID = 139 THEN 'Jacaré'
                      WHEN te.ID = 112 THEN 'Orfeu'
                      ELSE te.NOME_FANTASIA
                  END AS 'Casa',
                  tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
                  tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
                  tiv.PRODUCT_NAME AS 'Item Vendido Zig',
                  tivc2.DESCRICAO AS 'Categoria',
                  tivt.DESCRICAO AS 'Tipo',
                  DATE(tiv.EVENT_DATE) AS 'Data Venda',
                  SUM(tiv.COUNT * tiv.UNIT_VALUE) / SUM(tiv.COUNT) AS 'Valor Unitário',
                  SUM(tiv.COUNT) AS 'Quantidade',
                  SUM(tiv.DISCOUNT_VALUE) AS 'Desconto',
                  SUM(COALESCE((tiv.UNIT_VALUE * tiv.COUNT), 0)) AS 'Faturamento Bruto',
                  SUM(COALESCE(((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE), 0)) AS 'Faturamento Líquido'
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
              GROUP BY `ID Casa`, tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)
          )
          SELECT * FROM dados_historicos
          UNION ALL
          SELECT * FROM dados_recentes
          ORDER BY `Data Venda`, `ID Casa`, `Product ID`
      ''')

@st.cache_data
def GET_CMV_ORCADO_AB():
  return dataframe_query(f'''
      WITH Orcamento_CMV AS (
        SELECT 
            te.ID,
            te.NOME_FANTASIA,
            t.MES,
            t.ANO,
            SUM(t.VALOR) AS Valor_Orcamento_CMV
        FROM T_ORCAMENTOS t 
        LEFT JOIN T_EMPRESAS te ON te.ID = t.FK_EMPRESA 
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tccg.ID = t.FK_CLASSIFICACAO_1
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tccg2.ID = t.FK_CLASSIFICACAO_2
        WHERE tccg.ID IN (180, 236)
          AND tccg2.ID IN (957, 958, 493, 494)
        GROUP BY te.ID, te.NOME_FANTASIA, t.MES, t.ANO
    ),
    Orcamento_Faturamento AS (
        SELECT
            te.ID,
            te.NOME_FANTASIA,
            t.MES,
            t.ANO,
            SUM(t.VALOR) AS Valor_Orcamento_Faturamento
        FROM T_ORCAMENTOS t 
        LEFT JOIN T_EMPRESAS te ON te.ID = t.FK_EMPRESA 
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tccg.ID = t.FK_CLASSIFICACAO_1
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tccg2.ID = t.FK_CLASSIFICACAO_2
        WHERE tccg.ID IN (178, 245)
          AND tccg2.ID IN (442, 457, 899, 914)
        GROUP BY te.ID, te.NOME_FANTASIA, t.MES, t.ANO
    )
    SELECT
        f.ID AS 'ID Casa',
        f.NOME_FANTASIA AS 'Casa',
        f.MES AS 'Mês',
        f.ANO AS 'Ano',
        c.Valor_Orcamento_CMV AS 'Valor Orçamento CMV',
        f.Valor_Orcamento_Faturamento AS 'Valor Orçamento Faturamento',
        ROUND(c.Valor_Orcamento_CMV / f.Valor_Orcamento_Faturamento * 100, 2) AS '% CMV Orçado'
    FROM Orcamento_Faturamento f
    LEFT JOIN Orcamento_CMV c 
        ON f.ID = c.ID 
      AND f.MES = c.MES 
      AND f.ANO = c.ANO
    WHERE f.ANO >= 2025
    ORDER BY f.NOME_FANTASIA, f.ANO, f.MES;
  ''')


############################### CMV ###################################

@st.cache_data
def GET_FATURAM_ZIG_ALIM_BEB_MENSAL(data_inicio, data_fim):
  return dataframe_query(f'''
  SELECT
    te.ID AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    tivc2.DESCRICAO AS Categoria,
    CASE 
      WHEN te.ID IN (103, 112, 118, 139, 169) THEN 1
      ELSE 0 
    END AS Delivery,
    cast(date_format(cast(tivd.EVENT_DATE AS date), '%Y-%m-01') AS date) AS Primeiro_Dia_Mes,
    concat(year(cast(tivd.EVENT_DATE AS date)), '-', month(cast(tivd.EVENT_DATE AS date))) AS Ano_Mes,
    cast(tivd.EVENT_DATE AS date) AS Data_Evento,
    SUM((tivd.VALOR_UNITARIO  * tivd.QUANTIDADE)) AS Valor_Bruto,
    SUM(tivd.DESCONTO) AS Desconto,
    SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Valor_Liquido
  FROM T_ITENS_VENDIDOS_DIA tivd
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivd.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tivd.EVENT_DATE AS date) >= '{data_inicio}'
    AND cast(tivd.EVENT_DATE AS date) <= '{data_fim}'
    AND tivc2.DESCRICAO IN ('Alimentos', 'Bebidas')
  GROUP BY 
    ID_Loja,
    Categoria,
    Primeiro_Dia_Mes
  UNION ALL
  SELECT
    te.ID AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    tivc2.DESCRICAO AS Categoria,
    CASE 
      WHEN te.ID IN (103, 112, 118, 139, 169) THEN 1
      ELSE 0 
    END AS Delivery,
    cast(date_format(cast(tivd.EVENT_DATE AS date), '%Y-%m-01') AS date) AS Primeiro_Dia_Mes,
    concat(year(cast(tivd.EVENT_DATE AS date)), '-', month(cast(tivd.EVENT_DATE AS date))) AS Ano_Mes,
    cast(tivd.EVENT_DATE AS date) AS Data_Evento,
    SUM((tivd.VALOR_UNITARIO  * tivd.QUANTIDADE)) AS Valor_Bruto,
    SUM(tivd.DESCONTO) AS Desconto,
    SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Valor_Liquido
  FROM T_ITENS_VENDIDOS_DIA tivd
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivd.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tivd.EVENT_DATE AS date) >= '{data_inicio}'
    AND cast(tivd.EVENT_DATE AS date) <= '{data_fim}'
    AND tivc2.DESCRICAO IN ('Serviço')
    AND te.ID IN (103, 112, 118, 139, 169)
  GROUP BY 
    ID_Loja,
    Categoria,
    Primeiro_Dia_Mes;
''')


@st.cache_data
def GET_VALORACAO_ESTOQUE(loja, data_contagem):
  # Condição dinâmica baseada no parâmetro 'loja'
  if loja == 'Girondino - Agregado':
    where_loja = "te.ID IN (156, 160)"
  else:
    where_loja = f"te.NOME_FANTASIA = '{loja}'"
  return dataframe_query(f'''
  SELECT 
  	te.ID AS 'ID_Loja',
  	te.NOME_FANTASIA AS 'Loja',
  	tin5.ID AS 'ID_Insumo',
  	REPLACE(tin5.DESCRICAO, ',', '.') AS 'Insumo',
  	tci.QUANTIDADE_INSUMO AS 'Quantidade',
  	tin5.FK_INSUMOS_NIVEL_4 AS 'ID_Nivel_4',
  	tudm.UNIDADE_MEDIDA_NAME AS 'Unidade_Medida',
    tin.DESCRICAO AS 'Categoria',
  	tve.VALOR_EM_ESTOQUE AS 'Valor_em_Estoque',
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
    AND tci.DATA_CONTAGEM = '{data_contagem}'
    AND {where_loja}
  ORDER BY DATA_CONTAGEM DESC
  ''')


@st.cache_data
def GET_EVENTOS_CMV(data_inicio, data_fim):
  return dataframe_query(f'''
  SELECT 
    te.ID AS 'ID_Loja',
   	te.NOME_FANTASIA AS 'Loja',
   	SUM(tec.VALOR_EVENTOS_A_B) AS 'Valor',
   	tec.DATA AS 'Data',
    cast(date_format(cast(tec.DATA AS date), '%Y-%m-01') AS date) AS 'Primeiro_Dia_Mes'
  FROM T_EVENTOS_CMV tec 
  LEFT JOIN T_EMPRESAS te ON tec.FK_EMPRESA = te.ID 
  WHERE tec.DATA BETWEEN '{data_inicio}' AND '{data_fim}'
  GROUP BY te.ID
  ''')


@st.cache_data
def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO():
  return dataframe_query(f'''
    SELECT
      te.ID AS ID_Loja,
      te.NOME_FANTASIA AS Loja,
      DATE_FORMAT(tdr.COMPETENCIA, '%Y-%m-01') AS Primeiro_Dia_Mes,
      SUM(tdr.VALOR_PAGAMENTO) AS BlueMe_Sem_Pedido_Valor,
      SUM(CASE
        WHEN tccg2.DESCRICAO IN ('ALIMENTOS', 'Insumos - Alimentos') THEN tdr.VALOR_PAGAMENTO
        ELSE 0
      END) AS BlueMe_Sem_Pedido_Alimentos,
      SUM(CASE
        WHEN tccg2.DESCRICAO IN ('BEBIDAS', 'Insumos - Bebidas') THEN tdr.VALOR_PAGAMENTO
        ELSE 0
      END) AS BlueMe_Sem_Pedido_Bebidas,
      SUM(CASE
        WHEN tccg2.DESCRICAO IN ('EMBALAGENS', 'Insumos - Embalagens') THEN tdr.VALOR_PAGAMENTO
        ELSE 0
      END) AS BlueMe_Sem_Pedido_Descart_Hig_Limp,
      SUM(CASE
        WHEN tccg2.DESCRICAO NOT IN ('ALIMENTOS', 'Insumos - Alimentos', 'BEBIDAS', 'Insumos - Bebidas', 'EMBALAGENS', 'Insumos - Embalagens') THEN tdr.VALOR_PAGAMENTO
        ELSE 0
      END) AS BlueMe_Sem_Pedido_Outros
    FROM
      T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
    INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
    WHERE
      tdr.BIT_CANCELADA = 0
      AND tdr.FK_DESPESA_TEKNISA IS NULL
      AND tccg.ID IN (162, 205, 236)
      AND NOT EXISTS (
        SELECT 1
        FROM T_DESPESA_RAPIDA_ITEM tdri
        WHERE tdri.FK_DESPESA_RAPIDA = tdr.ID
      )
    GROUP BY
      te.ID,
      te.NOME_FANTASIA,
      DATE_FORMAT(tdr.COMPETENCIA, '%Y-%m-01')
    ORDER BY
      te.ID,
      Primeiro_Dia_Mes;
''')

def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO_PERIODO_LOJA(data_inicio, data_fim, loja):
  return dataframe_query(f'''
    SELECT
      q.ID_Loja,
      q.Loja,
      q.Primeiro_Dia_Mes,
      SUM(q.Valor_Liquido) AS BlueMe_Com_Pedido_Valor_Liquido,
      SUM(q.Valor_Insumos) AS BlueMe_Com_Pedido_Valor_Insumos,
      SUM(q.Valor_Liq_Alimentos) AS BlueMe_Com_Pedido_Valor_Liq_Alimentos,
      SUM(q.Valor_Liq_Bebidas) AS BlueMe_Com_Pedido_Valor_Liq_Bebidas,
      SUM(q.Valor_Liq_Descart_Hig_Limp) AS BlueMe_Com_Pedido_Valor_Liq_Descart_Hig_Limp,
      SUM(q.Valor_Liq_Outros) AS BlueMe_Com_Pedido_Valor_Liq_Outros
    FROM (
      SELECT
        tdr.ID AS tdr_ID,
        te.ID AS ID_Loja,
        te.NOME_FANTASIA AS Loja,
        tdr.VALOR_LIQUIDO AS Valor_Liquido,
        SUM(tdri.VALOR) AS Valor_Insumos,
        CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE),'%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Alimentos,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Bebidas,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Descart_Hig_Limp,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO NOT IN (
                'ALIMENTOS',
                'BEBIDAS',
                'DESCARTAVEIS/HIGIENE E LIMPEZA',
                'GELO / GAS / CARVAO / VELAS',
                'UTENSILIOS'
              )
              THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Outros
      FROM
        T_DESPESA_RAPIDA tdr
        JOIN T_EMPRESAS te
          ON tdr.FK_LOJA = te.ID
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
      WHERE
        tdri.ID IS NOT NULL
        AND te.ID <> 135
        AND tdr.BIT_CANCELADA = 0
      GROUP BY
        tdr.ID,
        te.ID,
        te.NOME_FANTASIA,
        tdr.VALOR_LIQUIDO,
        tdr.COMPETENCIA
    ) q
    WHERE
      q.Primeiro_Dia_Mes >= '{data_inicio}'
      AND q.Primeiro_Dia_Mes <= '{data_fim}'
      AND (
        CASE 
          WHEN q.Loja = 'Girondino' THEN 'Girondino - Agregado'
          WHEN q.Loja = 'Girondino - CCBB' THEN 'Girondino - Agregado'
          WHEN q.Loja = 'Blue Note - São Paulo' THEN 'Blue Note - Agregado'
          WHEN q.Loja = 'Blue Note SP (Novo)' THEN 'Blue Note - Agregado'
          WHEN q.Loja = 'The Cavern' THEN 'The Cavern - Agregado'
          WHEN q.Loja = 'The Cavern - Almoço' THEN 'The Cavern - Agregado'
          ELSE q.Loja
        END
		) = '{loja}'
    GROUP BY
      q.ID_Loja,
      q.Loja,
      q.Primeiro_Dia_Mes
    ORDER BY
      q.ID_Loja,
      q.Primeiro_Dia_Mes;
''')


@st.cache_data
def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO():
  return dataframe_query(f'''
    SELECT
      CASE
        WHEN q.ID_Loja = 131 THEN 110
        ELSE q.ID_Loja
      END AS ID_Loja,
      CASE
        WHEN q.Loja = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
        ELSE q.Loja
      END AS Loja,
      q.Primeiro_Dia_Mes AS Primeiro_Dia_Mes,
      SUM(q.Valor_Liquido) AS BlueMe_Com_Pedido_Valor_Liquido,
      SUM(q.Valor_Insumos) AS BlueMe_Com_Pedido_Valor_Insumos,
      SUM(q.Valor_Liq_Alimentos) AS BlueMe_Com_Pedido_Valor_Liq_Alimentos,
      SUM(q.Valor_Liq_Bebidas) AS BlueMe_Com_Pedido_Valor_Liq_Bebidas,
      SUM(q.Valor_Liq_Descart_Hig_Limp) AS BlueMe_Com_Pedido_Valor_Liq_Descart_Hig_Limp,
      SUM(q.Valor_Liq_Outros) AS BlueMe_Com_Pedido_Valor_Liq_Outros
    FROM (
      SELECT
        tdr.ID AS tdr_ID,
        te.ID AS ID_Loja,
        te.NOME_FANTASIA AS Loja,
        tdr.VALOR_LIQUIDO AS Valor_Liquido,
        SUM(tdri.VALOR) AS Valor_Insumos,
        CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE),'%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Alimentos,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Bebidas,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Descart_Hig_Limp,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO NOT IN (
                'ALIMENTOS',
                'BEBIDAS',
                'DESCARTAVEIS/HIGIENE E LIMPEZA',
                'GELO / GAS / CARVAO / VELAS',
                'UTENSILIOS'
              )
              THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Outros
      FROM
        T_DESPESA_RAPIDA tdr
        JOIN T_EMPRESAS te
          ON tdr.FK_LOJA = te.ID
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
      WHERE
        tdri.ID IS NOT NULL
        AND te.ID <> 135
        AND tdr.BIT_CANCELADA = 0
      GROUP BY
        tdr.ID,
        te.ID,
        te.NOME_FANTASIA,
        tdr.VALOR_LIQUIDO,
        tdr.COMPETENCIA
    ) q
    GROUP BY
      q.ID_Loja,
      q.Primeiro_Dia_Mes
    ORDER BY
      q.ID_Loja,
      q.Primeiro_Dia_Mes;
''')



@st.cache_data
def GET_TRANSF_ESTOQUE():
  return dataframe_query(f'''
  SELECT
    tti.ID as 'ID_Transferencia',
    te.ID as 'ID_Loja_Saida',
    te.NOME_FANTASIA as 'Casa_Saida',
    te2.ID as 'ID_Loja_Entrada',
    te2.NOME_FANTASIA as 'Casa_Entrada',
    tti.DATA_TRANSFERENCIA as 'Data_Transferencia',
    tin5.ID as 'ID_Insumo_Nivel_5',
    tin5.DESCRICAO as 'Insumo_Nivel_5',
    tin.DESCRICAO as 'Categoria',
    tti.QUANTIDADE as 'Quantidade',
    tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
    tti.VALOR_TRANSFERENCIA as 'Valor_Transferencia',
    tti.OBSERVACAO as 'Observacao'
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
def GET_PERDAS_E_CONSUMO_AGRUPADOS():
  return dataframe_query(f'''
  WITH vpec AS (
    SELECT
      tpecc.ID AS Perdas_ID,
      tl.ID AS ID_Loja,
      tl.NOME_FANTASIA AS Loja,
      tpecc.DATA_BAIXA AS Data_Baixa,        
      CASE
        WHEN tpecc.FK_MOTIVO = 106 THEN tpecc.VALOR
        ELSE 0
      END AS Consumo_Interno,
      CASE
        WHEN tpecc.FK_MOTIVO <> 106 THEN tpecc.VALOR
        ELSE 0
      END AS Quebras_e_Perdas,
      CAST(DATE_FORMAT(CAST(tpecc.DATA_BAIXA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes
    FROM
      T_PERDAS_E_CONSUMO_CONSOLIDADOS tpecc
    JOIN T_EMPRESAS tl ON tpecc.FK_EMPRESA = tl.ID
  )
  SELECT
    vpec.ID_Loja,
    vpec.Loja,
    vpec.Primeiro_Dia_Mes,
    SUM(vpec.Consumo_Interno) AS Consumo_Interno,
    SUM(vpec.Quebras_e_Perdas) AS Quebras_e_Perdas
  FROM vpec
  GROUP BY
    vpec.ID_Loja,
    vpec.Primeiro_Dia_Mes
  ORDER BY
    vpec.ID_Loja,
    vpec.Primeiro_Dia_Mes;
''')

  

@st.cache_data
def GET_INSUMOS_BLUE_ME_COM_PEDIDO(data_inicio, data_fim, loja):
  return dataframe_query(f'''
    SELECT
      tdr.ID AS tdr_ID,
      te.ID AS ID_Loja,
      CASE 
      	WHEN te.NOME_FANTASIA = 'Girondino' THEN 'Girondino - Agregado'
      	WHEN te.NOME_FANTASIA = 'Girondino - CCBB' THEN 'Girondino - Agregado'
      	WHEN te.NOME_FANTASIA = 'Blue Note - São Paulo' THEN 'Blue Note - Agregado'
      	WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - Agregado'
        WHEN te.NOME_FANTASIA = 'The Cavern' THEN 'The Cavern - Agregado'
        WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern - Agregado'
      	ELSE te.NOME_FANTASIA
      END AS `Loja`,
      tf.CORPORATE_NAME AS Fornecedor,
      tdr.NF AS Doc_Serie,
      tdr.COMPETENCIA AS Data_Emissao,
      tdr.VALOR_LIQUIDO AS Valor_Liquido,
      SUM(tdri.VALOR) AS Valor_Cotacao,
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE),'%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
      ROUND(
        tdr.VALOR_LIQUIDO * (
          SUM(CASE WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR ELSE 0 END)
          / NULLIF(SUM(tdri.VALOR),0)
        ),
        2
      ) AS Valor_Liq_Alimentos,
      ROUND(
        tdr.VALOR_LIQUIDO * (
          SUM(CASE WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR ELSE 0 END)
          / NULLIF(SUM(tdri.VALOR),0)
        ),
        2
      ) AS Valor_Liq_Bebidas,
      ROUND(
        tdr.VALOR_LIQUIDO * (
          SUM(CASE WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR ELSE 0 END)
          / NULLIF(SUM(tdri.VALOR),0)
        ),
        2
      ) AS Valor_Liq_Descart_Hig_Limp,
      ROUND(
        tdr.VALOR_LIQUIDO * (
          SUM(CASE WHEN tin1.DESCRICAO = 'GELO / GAS / CARVAO / VELAS' THEN tdri.VALOR ELSE 0 END)
          / NULLIF(SUM(tdri.VALOR),0)
        ),
          2
        ) AS Valor_Gelo_Gas_Carvao_Velas,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE WHEN tin1.DESCRICAO = 'UTENSILIOS' THEN tdri.VALOR ELSE 0 END)
            / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Utensilios,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO NOT IN (
                'ALIMENTOS',
                'BEBIDAS',
                'DESCARTAVEIS/HIGIENE E LIMPEZA',
                'GELO / GAS / CARVAO / VELAS',
                'UTENSILIOS'
              )
              THEN tdri.VALOR ELSE 0
            END)
            / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Outros
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
    WHERE
      DATE(tdr.COMPETENCIA) BETWEEN DATE('{data_inicio}') AND DATE('{data_fim}')
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
      tdr.VALOR_LIQUIDO;
''')


 

@st.cache_data
def GET_INSUMOS_BLUE_ME_SEM_PEDIDO():
  return dataframe_query(f'''
    SELECT
      tdr.ID AS tdr_ID,
      te.ID AS ID_Loja,
      te.NOME_FANTASIA AS Loja,
      tf.CORPORATE_NAME AS Fornecedor,
      tdr.NF AS Doc_Serie,
      tdr.COMPETENCIA AS Data_Emissao,
      tdr.VALOR_PAGAMENTO AS Valor,
      tccg2.DESCRICAO AS Plano_de_Contas,
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes
    FROM T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
    LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
    LEFT JOIN T_STATUS_PAGAMENTO tsp2 ON (
      SELECT ts.FK_STATUS_PAGAMENTO
      FROM T_DESPESA_STATUS tds
      LEFT JOIN T_STATUS ts ON tds.FK_STATUS_NAME = ts.ID
      WHERE tds.FK_DESPESA_RAPIDA = tdr.ID
      ORDER BY tds.ID DESC
      LIMIT 1
    ) = tsp2.ID
    WHERE tdr.BIT_CANCELADA = 0
      AND tdr.FK_DESPESA_TEKNISA IS NULL
      AND tccg.ID IN (162, 205, 236)
      AND NOT EXISTS (
        SELECT 1 FROM T_DESPESA_RAPIDA_ITEM tdri
        WHERE tdri.FK_DESPESA_RAPIDA = tdr.ID
      )
    ORDER BY tdr.ID;
''')


@st.cache_data
def GET_VALORACAO_PRODUCAO(data):
  return dataframe_query(f'''
  SELECT
    te.ID as 'ID_Loja',
    te.NOME_FANTASIA as 'Loja',
    tipc.DATA_CONTAGEM as 'Data_Contagem',
    DATE_FORMAT(DATE_SUB(tipc.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') AS 'Mes_Texto',
    tip.NOME_ITEM_PRODUZIDO as 'Item_Produzido',
    tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
    tipc.QUANTIDADE_INSUMO as 'Quantidade',
    tin.DESCRICAO as 'Categoria',
    tipv.VALOR as 'Valor_Unidade_Medida',
    ROUND(tipc.QUANTIDADE_INSUMO * tipv.VALOR, 2) as 'Valor_Total'
  FROM T_ITENS_PRODUCAO_CONTAGEM tipc
  LEFT JOIN T_ITENS_PRODUCAO_VALORACAO tipv ON (tipc.FK_ITEM_PRODUZIDO = tipv.FK_ITEM_PRODUZIDO) AND (DATE_FORMAT(tipc.DATA_CONTAGEM, '%m/%Y') = DATE_FORMAT(tipv.DATA_VALORACAO, '%m/%Y'))
  LEFT JOIN T_ITENS_PRODUCAO tip ON (tipv.FK_ITEM_PRODUZIDO = tip.ID)
  LEFT JOIN T_EMPRESAS te ON (tip.FK_EMPRESA = te.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON (tip.FK_INSUMO_NIVEL_1 = tin.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tip.FK_UNIDADE_MEDIDA = tudm.ID)
  WHERE tipc.DATA_CONTAGEM = '{data}'
  ''')