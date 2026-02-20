import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query, execute_query


@st.cache_data
def GET_CASAS_VALIDAS_ANALISE_PRODUTOS():
    
    GET_CASAS = """
    SELECT te.ID AS ID_Casa,
    te.NOME_FANTASIA AS Casa,
    te.ID_ZIGPAY AS ID_Zigpay
    FROM T_EMPRESAS te
    """

    result, column_names = execute_query(GET_CASAS)
    df_casas = pd.DataFrame(result, columns=column_names)
    lista_casas_validas = [
        "Abaru - Priceless",
        "Arcos",
        "Bar Brahma - Centro",
        "Bar Brahma - Granja",
        "Bar Léo - Centro",
        "Blue Note - São Paulo",
        "Blue Note SP (Novo)",
        "Edificio Rolim",
        "Girondino",
        "Girondino - CCBB",
        "Jacaré",
        "Love Cabaret",
        "Notiê - Priceless",
        "Orfeu",
        "Priceless",
        "Riviera Bar",
        "Ultra Evil Premium Ltda ",
        "Delivery Bar Leo Centro",
        "Delivery Fabrica de Bares",
        "Delivery Jacaré",
        "Delivery Orfeu",
    ]
    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    df = df_casas.merge(df_validas, on="Casa", how="inner")
    return df


@st.cache_data
def GET_TRANSACOES_PERIODO_HORARIO_DIA_DA_SEMANA(id_loja):
  return dataframe_query(f'''
    SELECT
    te.ID AS 'ID Loja',
    te.NOME_FANTASIA AS 'Loja',
    tiv.TRANSACTION_ID  AS 'ID Transacao',
    tiv.PRODUCT_NAME AS 'Produto',
    tiv.UNIT_VALUE AS 'Valor Unitario',
    tiv.COUNT AS 'Quantidade',
    DATE_FORMAT(tiv.TRANSACTION_DATE, '%Y-%m-%d') AS 'Data Transacao',
    CASE 
      WHEN MONTH(tiv.TRANSACTION_DATE) = 1 THEN 'Janeiro'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 2 THEN 'Fevereiro'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 3 THEN 'Março'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 4 THEN 'Abril'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 5 THEN 'Maio'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 6 THEN 'Junho'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 7 THEN 'Julho'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 8 THEN 'Agosto'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 9 THEN 'Setembro'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 10 THEN 'Outubro'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 11 THEN 'Novembro'
      WHEN MONTH(tiv.TRANSACTION_DATE) = 12 THEN 'Dezembro'  
    END AS 'Mes',
    YEAR(tiv.TRANSACTION_DATE) AS 'Ano',
    CASE 
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 1 THEN 'Domingo'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 2 THEN 'Segunda-feira'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 3 THEN 'Terça-feira'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 4 THEN 'Quarta-feira'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 5 THEN 'Quinta-feira'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 6 THEN 'Sexta-feira'
      WHEN DAYOFWEEK(tiv.TRANSACTION_DATE) = 7 THEN 'Sábado'
    END AS 'Dia Semana',
    CASE
      WHEN HOUR(tiv.TRANSACTION_DATE) BETWEEN 0 AND 5 THEN 'Madrugada'
      WHEN HOUR(tiv.TRANSACTION_DATE) BETWEEN 6 AND 10 THEN 'Manhã'
      WHEN HOUR(tiv.TRANSACTION_DATE) BETWEEN 11 AND 15 THEN 'Almoço'
      WHEN HOUR(tiv.TRANSACTION_DATE) BETWEEN 16 AND 19 THEN 'Happy Hour'
      WHEN HOUR(tiv.TRANSACTION_DATE) BETWEEN 20 AND 23 THEN 'Jantar'
    END AS 'Periodo Dia'
  FROM T_ITENS_VENDIDOS tiv
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tiv.LOJA_ID = te.ID_ZIGPAY
  WHERE tiv.TRANSACTION_DATE >= '2025-01-01' AND 
  	te.ID = {id_loja}
''')


@st.cache_data
def GET_CASAS_VALIDAS_ANALISE_PRODUTOS():
    
    GET_CASAS = """
    SELECT te.ID AS ID_Casa,
    te.NOME_FANTASIA AS Casa,
    te.ID_ZIGPAY AS ID_Zigpay
    FROM T_EMPRESAS te
    """

    result, column_names = execute_query(GET_CASAS)
    df_casas = pd.DataFrame(result, columns=column_names)
    lista_casas_validas = [
        "Abaru - Priceless",
        "Arcos",
        "Bar Brahma - Centro",
        "Bar Brahma - Granja",
        "Bar Léo - Centro",
        "Blue Note - São Paulo",
        "Blue Note SP (Novo)",
        "Edificio Rolim",
        "Girondino",
        "Girondino - CCBB",
        "Jacaré",
        "Love Cabaret",
        "Notiê - Priceless",
        "Orfeu",
        "Priceless",
        "Riviera Bar",
        "Ultra Evil Premium Ltda ",
        "Delivery Bar Leo Centro",
        "Delivery Fabrica de Bares",
        "Delivery Jacaré",
        "Delivery Orfeu",
    ]
    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    df = df_casas.merge(df_validas, on="Casa", how="inner")
    return df


