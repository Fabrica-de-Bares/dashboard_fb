import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query


# Para Descontos - DRE
@st.cache_data
def GET_CASAS_SIMPLES():
    return dataframe_query('''
      SELECT 
        te.ID AS 'ID_Casa',
        te.NOME_FANTASIA AS 'Casa'
        FROM T_EMPRESAS te                       
    ''')


@st.cache_data
def GET_DESCONTOS():
  return dataframe_query('''
    SELECT 
      td.FK_CASA,
      td.FUNCIONARIO,
      td.PRIMEIRO_DIA_MES AS 'DATA',
      td.CLIENTES,
      td.JUSTIFICATIVA,
      td.CATEGORIA,
      td.PORCENTAGEM,
      td.DESCONTO,
      td.PRODUTOS     
    FROM T_DESCONTOS AS td
    WHERE td.FK_CASA IS NOT NULL
    AND td.FK_CASA != 0                                                                                                                                                     
  ''')


@st.cache_data
def GET_PROMOCOES():
  return dataframe_query('''
    SELECT 
      tp.FK_CASA,
      tp.DATA,
      tp.PRODUTO,
      tp.PROMOCAO,
      tp.CATEGORIA_PRODUTO,
      tp.QUANTIDADE_USOS,
      tp.DESCONTO_TOTAL  
    FROM T_PROMOCOES_ZIG AS tp                                                                                                                                                    
  ''')


# Para Auditoria de Despesas
@st.cache_data
def GET_DATAS_FECHAMENTO():
  return dataframe_query('''
    SELECT 
      te.ID AS 'ID Casa',
      te.NOME_FANTASIA AS 'Casa',
      tdf.MES,
      tdf.ANO,
      tdf.DATA_FECHAMENTO
    FROM T_DATAS_FECHAMENTO_DRE tdf
    LEFT JOIN T_EMPRESAS AS te ON (tdf.FK_EMPRESA = te.ID);
  ''')


@st.cache_data
def GET_LOGS_DESPESAS():
  return dataframe_query('''
    SELECT
			tlogdr.ID AS 'ID Despesa',
			tlogdr.LOG_DATE as 'Data Alteração',
      CASE
        WHEN te.ID = 177 THEN 176    
        WHEN te.ID IN (161, 162) THEN 149   
        ELSE te.ID                                                           
			END AS 'ID Casa',
      CASE                   
        WHEN te.ID = 177 THEN 'The Cavern'   
        WHEN te.ID IN (161, 162) THEN 'Priceless'   
        ELSE te.NOME_FANTASIA           
			END AS 'Casa',
			au.FULL_NAME as 'Nome Usuário',
			au.EMAIL as 'Email Usuário',
			STR_TO_DATE(tlogdr.COMPETENCIA, '%Y-%m-%d') AS 'Data Competência',
      STR_TO_DATE(tlogdr.VENCIMENTO, '%Y-%m-%d') AS 'Data Vencimento',
      tlogdr.VALOR_PAGAMENTO AS 'Valor Original',
      tlogdr.VALOR_LIQUIDO AS 'Valor Liquido',                         
      tfp.DESCRICAO AS 'Forma Pagamento',
      tsp.DESCRICAO AS 'Status Pagamento',
      tf.CORPORATE_NAME AS 'Fornecedor',
      tlogdr.OBSERVACAO AS 'Observação',                                                                                   
      tccg1.DESCRICAO AS 'Class. Cont. 1',
      tccg2.DESCRICAO AS 'Class. Cont. 2',
      tsad.DESCRICAO AS 'Status Aprovação Diretoria',
      tsao.DESCRICAO AS 'Status Aprovação Operação',
      tdmr.MOTIVO_DESCRICAO AS 'Motivo Reprovação',
      CASE
        WHEN tlogdr.FK_REAL_PROVISAO = 100 THEN 'Provisão'
        ELSE 'Real'                                                   
      END AS 'Real/Provisão',
      tlogdr.BIT_CANCELADA AS 'Bit Cancelada'                                                                                                                                                                   
		FROM ZLOG_T_DESPESA_RAPIDA tlogdr 
			LEFT JOIN ADMIN_USERS au ON (tlogdr.LOG_USER = au.ID)
			LEFT JOIN T_EMPRESAS te ON (tlogdr.FK_LOJA = te.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfp ON (tlogdr.FK_FORMA_PAGAMENTO = tfp.ID) 
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tlogdr.FK_STATUS_PGTO = tsp.ID)                   
			LEFT JOIN T_FORNECEDOR tf ON (tlogdr.FK_FORNECEDOR = tf.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tlogdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg1.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tlogdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
      LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tlogdr.FK_APROVACAO_DIRETORIA = tsad.ID)   
      LEFT JOIN T_STATUS_APROVACAO_OPERACAO tsao ON (tlogdr.FK_APROVACAO_OPERACAO = tsao.ID)  
      LEFT JOIN T_DESPESA_MOTIVO_REPROVACAO tdmr ON (tlogdr.FK_MOTIVO_REPROVACAO = tdmr.ID)
      LEFT JOIN T_REAL_PROVISAO trp ON (tlogdr.FK_REAL_PROVISAO = trp.ID)                                                                                       
      # WHERE tlogdr.BIT_CANCELADA = 0;                                                                          
  ''')


# @st.cache_data
# def GET_IDS_APROVACAO_OPERACAO_ALTERADOS():
#    return dataframe_query('''
#     SELECT DISTINCT ID AS 'ID Despesa'
#     FROM (
#         SELECT
#             ID, 
#             LOG_DATE,
#             FK_APROVACAO_OPERACAO,
#             LAG(FK_APROVACAO_OPERACAO) OVER (
#                 PARTITION BY ID
#                 ORDER BY LOG_DATE
#             ) AS status_anterior
#         FROM ZLOG_T_DESPESA_RAPIDA
#     ) t
#     WHERE FK_APROVACAO_OPERACAO = 102 # Depois: reprovado
#     AND status_anterior = 101         # Antes: aprovado
#     AND YEAR(LOG_DATE) = 2026
#     ORDER BY ID, LOG_DATE;                      
#   ''')


@st.cache_data
def GET_CLASS_CONT_1():
  return dataframe_query('''
    SELECT 
      tccg1.ID,
      tccg1.DESCRICAO
    FROM T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1
    WHERE tccg1.FK_VERSAO_PLANO_CONTABIL = 103;
  ''')


@st.cache_data
def GET_CLASS_CONT_2():
  return dataframe_query('''
    SELECT 
      tccg2.ID,
      tccg2.DESCRICAO AS 'DESCRICAO_2',
      tccg2.FK_GRUPO_1,
      tccg1.DESCRICAO AS 'DESCRICAO_1'
    FROM T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tccg2.FK_GRUPO_1 = tccg1.ID)
    WHERE tccg1.FK_VERSAO_PLANO_CONTABIL = 103;
  ''')

# Para a validação do faturamento da Zigpay
@st.cache_data
def GET_FATURAMENTO_ZIGPAY_VALIDACAO(lista_ids_zigpay, mes, ano):

    # garante lista
    if not isinstance(lista_ids_zigpay, (list, tuple)):
        lista_ids_zigpay = [lista_ids_zigpay]

    if not lista_ids_zigpay:
        return pd.DataFrame()

    # placeholders do IN
    placeholders = ', '.join(['%s'] * len(lista_ids_zigpay))

    query = f'''
        SELECT
            te.ID AS 'ID Casa',
            te.NOME_FANTASIA AS 'Casa',
            CAST(tiv.EVENT_DATE AS DATE) AS 'Data Evento',
            DATE_FORMAT(tiv.EVENT_DATE, '%m/%Y') AS Mes_Texto,
            SUM((tiv.UNIT_VALUE * tiv.COUNT)) AS Soma_Valor_Transacao_Bruto,
            SUM(tiv.DISCOUNT_VALUE) AS Soma_Desconto,
            SUM((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE) AS Soma_Valor_Transacao_Liquido
        FROM T_ITENS_VENDIDOS tiv
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc 
            ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 
            ON tivc.FK_CATEGORIA = tivc2.ID
        LEFT JOIN T_EMPRESAS te 
            ON tiv.LOJA_ID = te.ID_ZIGPAY
        WHERE MONTH(tiv.EVENT_DATE) = %s 
          AND YEAR(tiv.EVENT_DATE) = %s
          AND te.FK_GRUPO_EMPRESA = 100
          AND tivc2.ID IN (100,101,102,103,104)
          AND te.ID_ZIGPAY IN ({placeholders})
        GROUP BY te.ID, CAST(tiv.EVENT_DATE AS DATE)
        ORDER BY tiv.EVENT_DATE
    '''

    params = [mes, ano] + list(lista_ids_zigpay)

    return dataframe_query(query, params)


def GET_CADASTROS_COUVERT_ZIGPAY():
  return dataframe_query('''
    SELECT
    tivc.ID_ZIGPAY AS 'ID Zigpay',
    tivc.NOME_PRODUTO AS 'Nome Produto',
    tivc2.DESCRICAO AS 'Categoria'
    FROM T_ITENS_VENDIDOS_CADASTROS tivc
    INNER JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
    WHERE tivc2.ID = 102
  ''')

def GET_ITENS_SEM_CADASTRO():
  return dataframe_query('''
    SELECT DISTINCT
      tiv.PRODUCT_NAME,
      tiv.PRODUCT_ID,
      tiv.PRODUCT_SKU,
      tivc2.DESCRICAO AS Categoria,
      te.NOME_FANTASIA as Casa,
      te.ID_ZIGPAY AS 'ID Zigpay'
    FROM T_ITENS_VENDIDOS tiv
      LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
      LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
      LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
      INNER JOIN T_EMPRESAS te ON (tiv.LOJA_ID = te.ID_ZIGPAY)
    WHERE tiv.EVENT_DATE > '2026-03-01 00:00:00'
      AND tivc2.DESCRICAO IS NULL
    ORDER BY tiv.PRODUCT_NAME asc
  ''')

def GET_ITENS_COM_CADASTRO_DUPLICADO():
  return dataframe_query('''
    SELECT *
    FROM T_ITENS_VENDIDOS_CADASTROS tivc
    WHERE tivc.ID_ZIGPAY IN (
        SELECT ID_ZIGPAY
        FROM T_ITENS_VENDIDOS_CADASTROS
        GROUP BY ID_ZIGPAY
        HAVING COUNT(*) > 1
    )
    ORDER BY tivc.ID_ZIGPAY;
  ''')


# Para Orçamento Operacional
@st.cache_data
def GET_ORCAMENTO_OPERACIONAL():
  return dataframe_query('''
    SELECT
        te.ID AS 'ID Casa',
        te.NOME_FANTASIA AS 'Casa',
        to2.ANO AS 'Ano',
        to2.MES AS 'Mês',
        to2.VALOR AS 'Orçamento',
        CASE
            WHEN tccg1.DESCRICAO = 'Despesas com Transporte / Hospedagem' THEN 'Manutenção' -- considera como Despesas Gerais  
            ELSE tccg1.DESCRICAO                            
        END as 'Classificação Contábil 1',               
        tccg2.DESCRICAO AS 'Classificação Contábil 2'
    FROM T_ORCAMENTOS to2
    JOIN T_EMPRESAS te ON (to2.FK_EMPRESA = te.ID)
    JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (to2.FK_CLASSIFICACAO_1 = tccg1.ID)
    JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (to2.FK_CLASSIFICACAO_2 = tccg2.ID)
    WHERE FK_PLANO_DE_CONTAS = 103
    ORDER BY te.NOME_FANTASIA, to2.MES, to2.ANO;
  ''')