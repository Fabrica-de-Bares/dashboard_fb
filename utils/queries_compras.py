import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query, execute_query


@st.cache_data
def inputs_expenses():
  return dataframe_query(f'''
    SELECT 
      DRI.ID AS 'ID_zAssociac Despesa Item',
      E.ID AS 'ID Casa',
      E.NOME_FANTASIA AS 'Casa',
      DR.ID AS 'ID Despesa',
      F.ID AS 'ID Fornecedor',
      LEFT(F.FANTASY_NAME, 23) AS 'Fornecedor',
      STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') AS 'Data Competencia',
      I5.ID AS 'ID Insumo',
      I5.DESCRICAO AS 'Insumo',
      I4.ID AS 'ID Nivel 4',
      I4.DESCRICAO AS 'Nivel 4',
      I3.ID AS 'ID Nivel 3',
      I3.DESCRICAO AS 'Nivel 3',
      I2.ID AS 'ID Nivel 2',
      I2.DESCRICAO AS 'Nivel 2',
      I1.ID AS 'ID Nivel 1',
      I1.DESCRICAO AS 'Nivel 1',
      ROUND(CAST(DRI.QUANTIDADE AS FLOAT), 3) AS 'Quantidade Insumo',
      tudm.UNIDADE_MEDIDA_NAME AS 'Unidade Medida',
      ROUND(CAST(DRI.VALOR AS FLOAT), 2) AS 'Valor Insumo',
      MONTH(DR.COMPETENCIA) AS 'Mês',
      YEAR(DR.COMPETENCIA) AS 'Ano'
    FROM T_DESPESA_RAPIDA_ITEM DRI 
        INNER JOIN T_INSUMOS_NIVEL_5 I5 ON (DRI.FK_INSUMO = I5.ID)
        INNER JOIN T_INSUMOS_NIVEL_4 I4 ON (I5.FK_INSUMOS_NIVEL_4 = I4.ID)
        INNER JOIN T_INSUMOS_NIVEL_3 I3 ON (I4.FK_INSUMOS_NIVEL_3 = I3.ID)
        INNER JOIN T_INSUMOS_NIVEL_2 I2 ON (I3.FK_INSUMOS_NIVEL_2 = I2.ID)
        INNER JOIN T_INSUMOS_NIVEL_1 I1 ON (I2.FK_INSUMOS_NIVEL_1 = I1.ID)
        INNER JOIN ADMIN_USERS au ON (DRI.LAST_USER = au.ID)
        INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
        INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
        INNER JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (I5.FK_UNIDADE_MEDIDA = tudm.ID)
    WHERE DR.COMPETENCIA >= '2024-01-01'
      AND DR.BIT_CANCELADA = 0
      AND I1.ID IN (100,101)
      AND E.FK_GRUPO_EMPRESA = 100
    ORDER BY DR.ID
  ''')


@st.cache_data
def supplier_expense_n5(day,day2):
  return dataframe_query(f"""
    SELECT 
      F.ID AS 'ID Fornecedor',
      F.FANTASY_NAME AS 'Fornecedor',
        E.NOME_FANTASIA AS 'Casa',
        N2.DESCRICAO AS 'INSUMO N2',
        N5.ID AS 'ID Nivel 5',
        N5.DESCRICAO AS 'INSUMO N5',
        tudm.UNIDADE_MEDIDA_NAME AS 'Unidade Medida',                   
        SUM(DRI.QUANTIDADE) AS 'Quantidade Insumo',
        SUM(DRI.VALOR) AS 'Valor Insumo',
        SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Valor Med Por Insumo'                                
    FROM T_DESPESA_RAPIDA_ITEM DRI 
        INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
        INNER JOIN T_INSUMOS_NIVEL_4 N4 ON (N5.FK_INSUMOS_NIVEL_4 = N4.ID)
        INNER JOIN T_INSUMOS_NIVEL_3 N3 ON (N4.FK_INSUMOS_NIVEL_3 = N3.ID)
        INNER JOIN T_INSUMOS_NIVEL_2 N2 ON (N3.FK_INSUMOS_NIVEL_2 = N2.ID)
        INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
        INNER JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
        INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (N5.FK_UNIDADE_MEDIDA = tudm.ID)
    WHERE DR.COMPETENCIA >= '{day}'
        AND DR.COMPETENCIA <= '{day2}'
        AND DR.BIT_CANCELADA = 0
    GROUP BY F.ID, N5.ID, E.NOME_FANTASIA -- Incluí o último campo para exibir corretamente as despesas por fornecedor
    ORDER BY F.FANTASY_NAME, N5.DESCRICAO
""")


@st.cache_data
def blueme_with_order(day,day2):
  return dataframe_query(f'''
    SELECT
      tdr.ID AS 'ID Despesa',
      te.ID AS 'ID Casa',
      te.NOME_FANTASIA AS 'Casa',
      tf.CORPORATE_NAME AS 'Fornecedor',
      tdr.NF AS 'Doc Serie',
      DATE_FORMAT(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d'), '%d/%m/%Y') AS 'Data Competencia',
      DATE_FORMAT(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), '%d/%m/%Y') AS 'Data Vencimento',
      tdr.VALOR_PAGAMENTO AS 'Valor Original',
      tdr.VALOR_LIQUIDO AS 'Valor Liquido',	
      SUM(tdri.VALOR) AS 'Valor Cotação',
      DATE_FORMAT(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d'), '%d/%m/%Y') AS 'Mes Texto'
    FROM T_DESPESA_RAPIDA tdr
    JOIN T_EMPRESAS te
        ON tdr.FK_LOJA = te.ID
    LEFT JOIN T_FORNECEDOR tf
        ON tdr.FK_FORNECEDOR = tf.ID
    LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri
        ON tdr.ID = tdri.FK_DESPESA_RAPIDA
    LEFT JOIN T_INSUMOS_NIVEL_5 tin5
        ON tdri.FK_INSUMO = tin5.ID
    WHERE
        te.ID <> 135
        AND tdri.ID IS NOT NULL
        AND DATE(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d')) >= '{day}'
        AND DATE(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d')) <= '{day2}'
    GROUP BY
        tdr.ID,
        te.ID,
        te.NOME_FANTASIA,
        tf.CORPORATE_NAME,
        tdr.NF,
        tdr.COMPETENCIA,
        tdr.VENCIMENTO,
        tdr.VALOR_PAGAMENTO,
        tdr.VALOR_LIQUIDO
    ORDER BY
        tdr.ID
  ''')


@st.cache_data
def companies(day,day2):
  return dataframe_query(f'''
    SELECT DISTINCT 
      E.ID as 'ID_Casa',
      E.NOME_FANTASIA as 'Casa'
    FROM T_DESPESA_RAPIDA DR 
      LEFT JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
    WHERE E.FK_GRUPO_EMPRESA = 100
      AND DR.BIT_CANCELADA = 0
      AND STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') >= '{day}'
      AND STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') <= '{day2}'
      AND E.ID NOT IN (127,165,166,167,117,101,162,129,161,142,143,130,111,131)
    ORDER BY E.NOME_FANTASIA 
  ''')


@st.cache_data
def purchases_without_orders(day,day2):
  return dataframe_query(f'''
    WITH Ultimo_Status AS (
      SELECT
          FK_DESPESA_RAPIDA,
          MAX(ID) AS Ultimo_Status_ID
      FROM T_DESPESA_STATUS
      GROUP BY FK_DESPESA_RAPIDA
    )
    SELECT
        DISTINCT DR.ID AS 'tdr_ID',
        E.NOME_FANTASIA AS 'Casa',
        LEFT(F.FANTASY_NAME, 23) AS 'Fornecedor',
        DR.NF AS 'Doc Serie',
        DATE_FORMAT(DR.COMPETENCIA, '%d/%m/%Y') AS 'Data Competencia',
        DATE_FORMAT(DR.VENCIMENTO, '%d/%m/%Y') AS 'Data Vencimento',
        CCG1.DESCRICAO AS 'Class Cont Grupo 1',
        CCG2.DESCRICAO AS 'Class Cont Grupo 2',
        DR.OBSERVACAO AS 'Observação',
        DR.VALOR_PAGAMENTO AS 'Valor Original',
        DR.VALOR_LIQUIDO AS 'Valor Liquido',
      CASE
        WHEN SP2.DESCRICAO = 'Provisionado'
        THEN 'Provisionado'
          ELSE 'Real'
      END AS 'Status Provisão Real',
      SP.DESCRICAO AS 'Status Pagamento',
      DATE_FORMAT(STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d'), '%m/%Y') AS 'Mes Texto'
    FROM T_DESPESA_RAPIDA DR
        INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
        LEFT JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 CCG1 ON (DR.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = CCG1.ID)
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 CCG2 ON (DR.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = CCG2.ID)
        LEFT JOIN T_STATUS_PAGAMENTO SP ON (DR.FK_STATUS_PGTO = SP.ID)
        LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri ON (DR.ID = tdri.FK_DESPESA_RAPIDA)
        LEFT JOIN Ultimo_Status US ON (DR.ID = US.FK_DESPESA_RAPIDA)
        LEFT JOIN T_DESPESA_STATUS DS ON (DR.ID = DS.FK_DESPESA_RAPIDA AND DS.ID = US.Ultimo_Status_ID)
        LEFT JOIN T_STATUS S ON (DS.FK_STATUS_NAME = S.ID)
        LEFT JOIN T_STATUS_PAGAMENTO SP2 ON (S.FK_STATUS_PAGAMENTO = SP2.ID)
    WHERE tdri.ID IS NULL
        AND DATE(DR.COMPETENCIA) >= '{day}'
      AND DATE(DR.COMPETENCIA) <= '{day2}'
      AND DR.BIT_CANCELADA = 0
        AND DR.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = 236
        AND E.FK_GRUPO_EMPRESA = 100
    ORDER BY DR.ID ASC
  ''')


@st.cache_data
def assoc_expense_items(day,day2):
  return dataframe_query(f'''
    SELECT 
      DRI.ID AS 'ID Associac Despesa Item',
      E.ID AS 'ID Casa',
      E.NOME_FANTASIA AS 'Casa',
      DR.ID AS 'ID Despesa',
      DATE_FORMAT(DR.COMPETENCIA, '%d/%m/%Y') AS 'Data Competencia',
      I5.ID AS 'ID Insumo',
      I5.DESCRICAO AS 'Insumo',
      UM.UNIDADE_MEDIDA_NAME AS 'Unidade Medida',                         
      CAST(REPLACE(DRI.QUANTIDADE, ',', '.') AS DECIMAL(10,2)) AS 'Quantidade Insumo',
      DRI.VALOR / CAST(REPLACE(DRI.QUANTIDADE, ',', '.') AS DECIMAL(10,2)) AS 'Valor Unitario',
      DRI.VALOR AS 'Valor Total'
    FROM T_DESPESA_RAPIDA_ITEM DRI 
      INNER JOIN T_INSUMOS_NIVEL_5 I5 ON (DRI.FK_INSUMO = I5.ID)
      INNER JOIN T_INSUMOS_NIVEL_4 I4 ON (I5.FK_INSUMOS_NIVEL_4 = I4.ID)
      INNER JOIN T_INSUMOS_NIVEL_3 I3 ON (I4.FK_INSUMOS_NIVEL_3 = I3.ID)
      INNER JOIN T_INSUMOS_NIVEL_2 I2 ON (I3.FK_INSUMOS_NIVEL_2 = I2.ID)
      INNER JOIN T_INSUMOS_NIVEL_1 I1 ON (I2.FK_INSUMOS_NIVEL_1 = I1.ID)
      INNER JOIN ADMIN_USERS AU ON (DRI.LAST_USER = AU.ID)
      INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
      INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
      LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON (I5.FK_UNIDADE_MEDIDA = UM.ID)
    WHERE DR.BIT_CANCELADA = 0 AND DATE(DR.COMPETENCIA) >= '{day}' AND DATE(DR.COMPETENCIA) <= '{day2}'
  ''')



##### PARETO #####

@st.cache_data
def GET_COMPRAS_PRODUTOS_QUANTIA_NOME_COMPRA():
  return dataframe_query(f'''
    SELECT
      tin4.ID AS 'ID Produto Nivel 4',
      tin5.ID AS 'ID Produto Nivel 5',
      tin5.DESCRICAO AS 'Nome Produto',	
      te.NOME_FANTASIA AS 'Loja', 
      tf.FANTASY_NAME AS 'Fornecedor',
        tin.DESCRICAO AS 'Categoria',
      CAST(REPLACE(tdri.QUANTIDADE, ',', '.') AS DECIMAL(10, 2)) AS 'Quantidade',
      tdri.UNIDADE_MEDIDA AS 'Unidade de Medida',
      tdri.VALOR AS 'Valor Total', 
      (tdri.VALOR / (CAST(REPLACE(tdri.QUANTIDADE, ',', '.') AS DECIMAL(10, 2)))) AS 'Valor Unitário',
      tdr.COMPETENCIA AS 'Data Compra',
      1 AS 'Fator de Proporção'
    FROM T_DESPESA_RAPIDA_ITEM tdri
      LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tdri.FK_INSUMO = tin5.ID
      LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
      LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
      LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID 
      LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.id
      LEFT JOIN T_DESPESA_RAPIDA tdr ON tdri.FK_DESPESA_RAPIDA = tdr.ID 
      LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID 
      LEFT JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID 
    WHERE tdr.COMPETENCIA > '2024-01-01'
      AND tdr.BIT_CANCELADA = 0
  ''')
    


def GET_COMPRAS_PRODUTOS_COM_RECEBIMENTO(data_inicio, data_fim, categoria):
  return dataframe_query(f'''
    SELECT 	
      tin5.ID AS 'ID Produto Nivel 5',
      tin5.DESCRICAO AS 'Nome Produto', 
      tin.DESCRICAO AS 'Categoria',
      te.NOME_FANTASIA AS 'Loja', 
      tf.FANTASY_NAME AS 'Fornecedor', 
      tdr.COMPETENCIA AS 'Data Compra',
      CAST(REPLACE(tdri.QUANTIDADE, ',', '.') AS DECIMAL(10, 2)) AS 'Quantidade',
      tdri.UNIDADE_MEDIDA AS 'Unidade de Medida',
      tdri.VALOR AS 'Valor Total', 
      (tdri.VALOR / (CAST(REPLACE(tdri.QUANTIDADE, ',', '.') AS DECIMAL(10, 2)))) AS 'Valor Unitário',
      tps.DATA AS 'Data_Recebida'
    FROM T_DESPESA_RAPIDA_ITEM tdri
    LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tdri.FK_INSUMO = tin5.ID
    LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
    LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
    LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID 
    LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.id
    LEFT JOIN T_DESPESA_RAPIDA tdr ON tdri.FK_DESPESA_RAPIDA = tdr.ID 
    LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID 
    LEFT JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID 
    LEFT JOIN T_PEDIDOS tp ON tp.ID = tdr.FK_PEDIDO
    LEFT JOIN T_PEDIDO_STATUS tps ON tps.FK_PEDIDO = tp.ID
    WHERE tdr.COMPETENCIA >= '{data_inicio}'
      AND tdr.COMPETENCIA <= '{data_fim}'
      AND tin.DESCRICAO = '{categoria}'
      AND tdr.BIT_CANCELADA = 0
    GROUP BY 
      tin5.ID,
      te.ID,
      tf.ID,
      tdr.COMPETENCIA
    ORDER BY
      tdr.COMPETENCIA DESC
  ''')



@st.cache_data
def GET_COMPRAS_POR_ANO():
  return dataframe_query('''
    SELECT 
      F.ID AS 'ID Fornecedor',
      F.FANTASY_NAME AS 'Fornecedor',
      E.NOME_FANTASIA AS 'Casa',
      DR.COMPETENCIA AS 'Data Competencia',
      N2.DESCRICAO AS 'Insumo N2',
      N5.ID AS 'ID Nivel 5',
      N5.DESCRICAO AS 'Insumo N5',
      -- tudm.UNIDADE_MEDIDA_NAME AS 'Unidade Medida',                   
      -- DRI.QUANTIDADE AS 'Quantidade Insumo',
      SUM(DRI.VALOR) AS 'Valor Compra',
      CONCAT(MONTH(DR.COMPETENCIA), '/', YEAR(DR.COMPETENCIA)) AS 'Mes/Ano'                   
      -- SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Valor Med Por Insumo'                                
    FROM T_DESPESA_RAPIDA_ITEM DRI 
      INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
      INNER JOIN T_INSUMOS_NIVEL_4 N4 ON (N5.FK_INSUMOS_NIVEL_4 = N4.ID)
      INNER JOIN T_INSUMOS_NIVEL_3 N3 ON (N4.FK_INSUMOS_NIVEL_3 = N3.ID)
      INNER JOIN T_INSUMOS_NIVEL_2 N2 ON (N3.FK_INSUMOS_NIVEL_2 = N2.ID)
      INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
      INNER JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
      INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
      LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (N5.FK_UNIDADE_MEDIDA = tudm.ID)
    WHERE DR.BIT_CANCELADA = 0
    GROUP BY E.NOME_FANTASIA, F.ID, MONTH(DR.COMPETENCIA), YEAR(DR.COMPETENCIA), N2.DESCRICAO, N5.ID 
    ORDER BY F.FANTASY_NAME, N2.DESCRICAO
  ''')

