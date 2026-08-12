import streamlit as st
from utils.functions.general_functions import dataframe_query


@st.cache_data
def GET_TICKET_MEDIO_ZIGPAY(id_casa, data_inicio, data_fim):
  return dataframe_query(f'''
    SELECT
        te.ID AS 'ID Casa',
        te.NOME_FANTASIA AS 'Casa',
        DATE(tztc.DATA_EVENTO) AS 'Data Evento',
        MONTH(tztc.DATA_EVENTO) AS 'Mês Evento',
        YEAR(tztc.DATA_EVENTO) AS 'Ano Evento',
        CASE
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 1 THEN 'Domingo'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 2 THEN 'Segunda-feira'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 3 THEN 'Terça-feira'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 4 THEN 'Quarta-feira'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 5 THEN 'Quinta-feira'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 6 THEN 'Sexta-feira'
          WHEN DAYOFWEEK(tztc.DATA_EVENTO) = 7 THEN 'Sábado'
        END AS 'Dia Semana',
        tztc.TICKET_MEDIO AS 'Ticket Médio'
    FROM T_ZIG_TICKET_CLIENTES tztc
    INNER JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tztc.LOJA_ID
    WHERE te.ID = {id_casa}
    AND DATE(tztc.DATA_EVENTO) BETWEEN '{data_inicio}' AND '{data_fim}'
    ORDER BY tztc.DATA_EVENTO
  ''')


@st.cache_data
def GET_CHECKINS_CLIENTES_PERIODO(id_casa, data_inicio, data_fim):
  return dataframe_query(f'''
    SELECT
        tzcc.EVENT_USER_ID AS 'ID Cliente Zig',
        tzcc.NOME_CLIENTE AS 'Cliente',
        tzcc.CPF AS 'CPF',
        tzcc.TELEFONE AS 'Telefone',
        DATE(tzcc.EVENT_DATE) AS 'Data Evento',
        tzcc.CHECKIN AS 'Check-in',
        tzcc.CHECKOUT AS 'Check-out'
    FROM T_ZIG_CHECKINS_CLIENTES tzcc
    LEFT JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tzcc.LOJA_ID
    WHERE te.ID = {id_casa}
    AND DATE(tzcc.EVENT_DATE) BETWEEN '{data_inicio}' AND '{data_fim}'
    ORDER BY tzcc.NOME_CLIENTE
  ''')
