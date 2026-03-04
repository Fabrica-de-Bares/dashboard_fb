import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


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


@st.cache_data
def GET_LOGS_DESPESAS():
  return dataframe_query('''
    SELECT
			tlogdr.ID AS 'ID Despesa',
			tlogdr.LOG_DATE as 'Data Alteração',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
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
      tccg2.DESCRICAO AS 'Class. Cont. 2'
      # tlogdr.FK_REAL_PROVISAO,
      # tlogdr.FK_APROVACAO_DIRETORIA                                                         
      # tscd.DESCRICAO AS 'Status Documentação',
      # tsad.DESCRICAO AS 'Status Aprovação Diretoria',
      # tsad.DESCRICAO AS 'Status Aprovação Caixa',
      # tsao.DESCRICAO AS 'Status Aprovação Operação'                                                                                                              
		FROM ZLOG_T_DESPESA_RAPIDA tlogdr 
			LEFT JOIN ADMIN_USERS au ON (tlogdr.LOG_USER = au.ID)
			LEFT JOIN T_EMPRESAS te ON (tlogdr.FK_LOJA = te.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfp ON (tlogdr.FK_FORMA_PAGAMENTO = tfp.ID)                   
			LEFT JOIN T_FORNECEDOR tf ON (tlogdr.FK_FORNECEDOR = tf.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tlogdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg1.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tlogdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
      LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON (tlogdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID) 
      LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tlogdr.FK_APROVACAO_DIRETORIA = tsad.ID)   
      LEFT JOIN T_STATUS_APROVACAO_CAIXA tsac ON (tlogdr.FK_APROVACAO_CAIXA = tsac.ID)                                            
      LEFT JOIN T_STATUS_APROVACAO_OPERACAO tsao ON (tlogdr.FK_APROVACAO_OPERACAO = tsao.ID)                                            
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tlogdr.FK_STATUS_PGTO = tsp.ID) 
      WHERE YEAR(tlogdr.LOG_DATE) = 2026;                                                                          
  ''')

