import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query

@st.cache_data
def GET_DESPESAS():
  return dataframe_query(f'''
  SELECT 
    tdr.ID AS ID,
    te.NOME_FANTASIA AS Loja,
    tf.CORPORATE_NAME AS Fornecedor,
    tdr.NF AS Doc_Serie,
    STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') AS Data_Emissao,
    STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d') AS Data_Vencimento,
    CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
    tdr.OBSERVACAO AS Descricao,
    tdr.VALOR_LIQUIDO AS Valor_Liquido,
    tccg2.DESCRICAO AS Classificacao_Contabil_2,
    tccg1.DESCRICAO AS Classificacao_Contabil_1,
    CASE 
      WHEN tdr.FK_Status = 'Provisionado' THEN 'Provisionado'
      ELSE 'Real'
    END AS Status
  FROM T_DESPESA_RAPIDA tdr
  JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
  LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON tccg2.FK_GRUPO_1 = tccg1.ID
  WHERE tccg1.FK_VERSAO_PLANO_CONTABIL = 103
    AND tdr.BIT_CANCELADA = 0
    AND NOT EXISTS (
      SELECT 1
      FROM T_DESPESA_RAPIDA_ITEM tdri
      WHERE tdri.FK_DESPESA_RAPIDA = tdr.ID);
''')


@st.cache_data
def GET_ORCAMENTOS_DESPESAS():
  return dataframe_query(f'''
  SELECT
    to2.ID AS ID_Orcamento,
    te.NOME_FANTASIA AS Loja,
    tccg2.DESCRICAO AS Classificacao_Contabil_2,
    tccg1.DESCRICAO AS Classificacao_Contabil_1,
    to2.VALOR AS Orcamento,
    cast(date_format(cast(CONCAT(to2.ANO, '-', to2.MES, '-01') AS date), '%Y-%m-01') as date) AS Primeiro_Dia_Mes
  FROM
    T_ORCAMENTOS to2 
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON tccg2.FK_GRUPO_1 = tccg1.ID
  LEFT JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID;
''')


@st.cache_data
def GET_FATURAM_ZIG(data_inicial, data_final):
  # Formatando as datas para o formato de string com aspas simples
  data_inicial_str = f"'{data_inicial.strftime('%Y-%m-%d %H:%M:%S')}'"
  data_final_str = f"'{data_final.strftime('%Y-%m-%d %H:%M:%S')}'"
    
  return dataframe_query(f'''
  SELECT tiv.ID AS 'ID_Venda_EPM',
    te.NOME_FANTASIA AS Loja,
    tiv.TRANSACTION_DATE as 'Data_Venda',
    CAST(tiv.EVENT_DATE as DATE) as 'Data_Evento',
    tivc.ID as 'ID_Produto_EPM',
    tiv.PRODUCT_NAME as 'Nome_Produto',
    tiv.UNIT_VALUE as 'Preco',
    tiv.COUNT as 'Qtd_Transacao',
    tiv.DISCOUNT_VALUE as 'Desconto',
    tivc2.DESCRICAO as 'Categoria',
    tivt.DESCRICAO as 'Tipo'
  FROM T_ITENS_VENDIDOS tiv 
    LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON (tiv.PRODUCT_ID = tivc.ID_ZIGPAY)
    LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON (tivc.FK_CATEGORIA = tivc2.ID)
    LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON (tivc.FK_TIPO = tivt.ID)
    LEFT JOIN T_EMPRESAS te ON (tiv.LOJA_ID = te.ID_ZIGPAY)
  WHERE CAST(tiv.EVENT_DATE as DATETIME) >= {data_inicial_str} AND CAST(tiv.EVENT_DATE as DATETIME) <= {data_final_str}
  ''')


@st.cache_data
def GET_FATURAM_ZIG_AGREGADO(data_inicio, data_fim):
  return dataframe_query(f''' 
  SELECT
    CASE
        WHEN te.ID = 117 THEN 118 -- Delivery BBC                                
        ELSE te.ID
      END AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    tivc2.DESCRICAO AS Categoria,
    cast(date_format(cast(tiv.EVENT_DATE as date), '%Y-%m-01') as date) AS Primeiro_Dia_Mes,
    concat(year(cast(tiv.EVENT_DATE as date)), '-', month(cast(tiv.EVENT_DATE as date))) AS Ano_Mes,
    cast(tiv.EVENT_DATE as date) AS Data_Evento,
    SUM((tiv.UNIT_VALUE * tiv.COUNT)) AS Valor_Bruto,
    SUM(tiv.DISCOUNT_VALUE) AS Desconto,
    SUM((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE) AS Valor_Liquido
  FROM T_ITENS_VENDIDOS tiv
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tiv.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tiv.EVENT_DATE as date) >= '{data_inicio}'
    AND cast(tiv.EVENT_DATE as date) <= '{data_fim}'
  GROUP BY 
    ID_Loja,
    Categoria,
    Primeiro_Dia_Mes;
''')


@st.cache_data
def GET_ORCAM_FATURAM():
  return dataframe_query(f'''
  SELECT
	CASE
		WHEN te.ID IN (149) THEN 162
		ELSE te.ID
	END AS ID_Loja,
	CASE
		WHEN te.NOME_FANTASIA IN ('Priceless') THEN 'Terraço Notie'
		ELSE te.NOME_FANTASIA
	END AS Loja,
	CONCAT(to2.ANO, '-', to2.MES) AS Ano_Mes,
    cast(date_format(cast(CONCAT(to2.ANO, '-', to2.MES, '-01') AS date), '%Y-%m-01') as date) AS Primeiro_Dia_Mes,
    to2.VALOR AS Orcamento_Faturamento,
    CASE
      WHEN tccg.DESCRICAO IN ('VENDA DE ALIMENTO', 'Alimentação') THEN 'Alimentos'
      WHEN tccg.DESCRICAO IN ('VENDA DE BEBIDAS', 'Bebida') THEN 'Bebidas'
      WHEN tccg.DESCRICAO IN ('VENDA DE COUVERT/ SHOWS', 'Artístico (couvert/shows)') THEN 'Couvert'
      WHEN tccg.DESCRICAO IN ('SERVICO', 'Serviço') THEN 'Serviço'
      WHEN tccg.DESCRICAO IN ('DELIVERY', 'Delivery') THEN 'Delivery'
      WHEN tccg.DESCRICAO IN ('GIFTS', 'Gifts') THEN 'Gifts'
      ELSE tccg.DESCRICAO
    END AS Categoria
  FROM
    T_ORCAMENTOS to2
  JOIN
    T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
  JOIN
    T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg ON to2.FK_CLASSIFICACAO_2 = tccg.ID
  WHERE
    to2.FK_CLASSIFICACAO_1 IN (178, 245)
  ORDER BY
    ID_Loja,
    Ano_Mes;
  ''')

############### Receitas extraordinárias ################

@st.cache_data
def GET_RECEIT_EXTRAORD():
  #'Data_Evento' é, na realidade, a data da competencia, eu só coloquei esse nome pra ficar mais fácil de programar
  return dataframe_query(f'''
  SELECT
    tre.ID as 'ID_receita',
    te.NOME_FANTASIA as 'Loja',
    trec3.NOME as 'Cliente',
    trec.CLASSIFICACAO as 'Classificacao',
    tep.ID as 'ID_Evento',
    tep.NOME_EVENTO as 'Nome_Evento',
    tre.VALOR as 'Valor_Total',
    CAST(tre.DATA_OCORRENCIA AS DATE) as 'Data_Evento',
    tre.VALOR_CATEGORIA_AB as 'Categ_AB',
    tre.VALOR_CATEGORIA_ALUGUEL as 'Categ_Aluguel',
    tre.VALOR_CATEGORIA_ARTISTICO as 'Categ_Artist',
    tre.VALOR_CATEGORIA_COUVERT as 'Categ_Couvert',
    tre.VALOR_CATEGORIA_LOCACAO as 'Categ_Locacao',
    tre.VALOR_CATEGORIA_PATROCINIO as 'Categ_Patroc',
    tre.VALOR_CATEGORIA_TAXA_SERVICO as 'Categ_Taxa_Serv'
  FROM T_RECEITAS_EXTRAORDINARIAS tre
    INNER JOIN T_EMPRESAS te ON (tre.FK_EMPRESA = te.ID)
    LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec ON (tre.FK_CLASSIFICACAO = trec.ID)
    LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec3 ON (tre.FK_CLIENTE = trec3.ID)
    LEFT JOIN T_EVENTO_PRE tep ON (tre.FK_EVENTO = tep.ID)
  WHERE tre.FK_STATUS_PGTO = 103 
    AND CAST(tre.DATA_OCORRENCIA AS DATE) >= '2023-10-01'
  ''')



def GET_CLSSIFICACAO():
  return dataframe_query(f'''
  SELECT
    trec.CLASSIFICACAO as 'Classificacao'
  FROM T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec 
  GROUP BY trec.CLASSIFICACAO 
''')