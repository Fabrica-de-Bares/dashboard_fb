import streamlit as st
from utils.functions.general_functions import dataframe_query

@st.cache_data
def fabrica_faturamento_couvert(day1, day2):
  return dataframe_query(f""" 
    SELECT
        TE.NOME_FANTASIA AS 'Loja',
        DATE_FORMAT(IV.EVENT_DATE, '%d/%m/%Y') AS 'Data Evento',
        SUM(IV.UNIT_VALUE * IV.COUNT) AS 'Valor Bruto',
        SUM(IV.DISCOUNT_VALUE) AS Desconto,
        SUM((IV.UNIT_VALUE * IV.COUNT) - IV.DISCOUNT_VALUE) AS 'Valor Liquido'
    FROM T_ITENS_VENDIDOS IV
    LEFT JOIN T_ITENS_VENDIDOS_CADASTROS ICV ON IV.PRODUCT_ID = ICV.ID_ZIGPAY
    LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS ICV2 ON ICV.FK_CATEGORIA = ICV2.ID
    LEFT JOIN T_ITENS_VENDIDOS_TIPOS IVT ON ICV.FK_TIPO = IVT.ID
    LEFT JOIN T_EMPRESAS TE ON IV.LOJA_ID = TE.ID_ZIGPAY
    WHERE ICV2.DESCRICAO = 'Couvert'
        AND IV.EVENT_DATE >= '{day1}'
        AND IV.EVENT_DATE <= '{day2}'
    GROUP BY IV.EVENT_DATE
    ORDER BY YEAR(IV.EVENT_DATE), MONTH(IV.EVENT_DATE), DAY(IV.EVENT_DATE)
""", use_eshows=False)

@st.cache_data
def eshows_custos(day1, day2):
  return dataframe_query(f"""
    SELECT 
		CASE
			WHEN C.NAME = 'Bar Brahma' THEN 'Bar Brahma - Centro'
      WHEN C.NAME = 'Bar Léo - Aurora' THEN 'Bar Léo - Centro'
      WHEN C.NAME = 'Bar Brahma Granja' THEN 'Bar Brahma - Granja'
      WHEN C.NAME = 'Jacaré ' THEN 'Jacaré'
      WHEN C.NAME = 'Blue Note São Paulo' THEN 'Blue Note SP (Novo)'
			ELSE C.NAME
        END AS 'Loja',
        DATE_FORMAT(P.DATA_INICIO, '%d/%m/%Y') AS 'Data Evento',
        SUM(P.VALOR_BRUTO) AS 'Valor Gasto'
    FROM T_PROPOSTAS P
    LEFT JOIN T_COMPANIES C ON P.FK_CONTRANTE = C.ID
        WHERE (C.FK_GRUPO = '124')
        AND P.FK_STATUS_PROPOSTA IS NOT NULL
        AND P.FK_STATUS_PROPOSTA NOT IN ('102')
        AND P.DATA_INICIO >= '{day1}'
        AND P.DATA_INICIO <= '{day2}'                                  
    GROUP BY YEAR(P.DATA_INICIO), MONTH(P.DATA_INICIO), DAY(P.DATA_INICIO), C.ID
    ORDER BY YEAR(P.DATA_INICIO), MONTH(P.DATA_INICIO), DAY(P.DATA_INICIO)
  """, use_eshows=True)


@st.cache_data
def propostas_eshows(day1, day2):
  return dataframe_query(f"""
    SELECT 
        CASE
          WHEN C.NAME = 'Bar Brahma' THEN 'Bar Brahma - Centro'
          WHEN C.NAME = 'Bar Léo - Aurora' THEN 'Bar Léo - Centro'
          WHEN C.NAME = 'Bar Brahma Granja' THEN 'Bar Brahma - Granja'
          WHEN C.NAME = 'Jacaré ' THEN 'Jacaré'
          WHEN C.NAME = 'Blue Note São Paulo' THEN 'Blue Note SP (Novo)'
          ELSE C.NAME
        END AS 'Loja',
        P.ID AS 'ID Proposta',
        DATE_FORMAT(P.DATA_INICIO, '%d/%m/%Y') AS 'Data Evento',
        TIME_FORMAT(P.DATA_INICIO, '%H:%i') AS 'Horário',    
        A.NOME AS 'Artista',
        P.VALOR_BRUTO AS 'Valor Bruto'
    FROM T_PROPOSTAS P
        LEFT JOIN T_COMPANIES C ON P.FK_CONTRANTE = C.ID
        LEFT JOIN T_ATRACOES A ON A.ID = P.FK_CONTRATADO
    WHERE (C.FK_GRUPO = '124')
        AND P.FK_STATUS_PROPOSTA IS NOT NULL
        AND P.FK_STATUS_PROPOSTA NOT IN ('102')
    AND P.DATA_INICIO >= '{day1}'
    AND P.DATA_INICIO <= '{day2}'  
    ORDER BY YEAR(P.DATA_INICIO), MONTH(P.DATA_INICIO), DAY(P.DATA_INICIO), C.ID
  """, use_eshows=True)   