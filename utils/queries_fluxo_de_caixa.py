import streamlit as st
from utils.functions.general_functions import dataframe_query

#################################### PROJEÇÃO ########################################

@st.cache_data
def GET_BARES_AGRUPADOS():
  return dataframe_query(f"""
SELECT te.NOME_FANTASIA AS 'Empresa'
FROM T_BARES_AGRUPADOS AS tbg 
LEFT JOIN T_EMPRESAS AS te ON (te.ID = tbg.FK_EMPRESA) 
ORDER BY te.NOME_FANTASIA                                                                       
""")


@st.cache_data
def GET_SALDOS_BANCARIOS():
  return dataframe_query(f"""
SELECT * FROM View_Saldos_Bancarios
WHERE Data >= CURDATE() 
AND Data < DATE_ADD(CURDATE(), INTERVAL 365 DAY)
AND Empresa IS NOT NULL
ORDER BY Data ASC
""")


@st.cache_data
def GET_VALOR_LIQUIDO_RECEBIDO():
  return dataframe_query(f'''
SELECT
  tc.DATA AS Data,
  te.NOME_FANTASIA AS Empresa,
  sum(trem.VALOR_RECEBIDO) AS Valor_Liquido_Recebido
FROM
  T_CALENDARIO tc
LEFT JOIN T_RECEITAS_EXTRATOS_MANUAL trem on
  tc.DATA = trem.DATA
LEFT JOIN T_EMPRESAS te on
  trem.FK_LOJA = te.ID
WHERE tc.DATA >= CURDATE() 
	AND tc.DATA < DATE_ADD(CURDATE(), INTERVAL 365 DAY)
	AND te.NOME_FANTASIA IS NOT NULL
GROUP BY
  te.NOME_FANTASIA,
  tc.DATA
ORDER BY tc.DATA ASC
''')


@st.cache_data
def GET_PROJECAO_ZIG():
  return dataframe_query(f'''
SELECT * FROM View_Projecao_Zig_Agrupadas
WHERE Data >= CURDATE() 
AND Data < DATE_ADD(CURDATE(), INTERVAL 365 DAY)
AND Empresa IS NOT NULL
ORDER BY Data ASC
''')


@st.cache_data
def GET_RECEITAS_EXTRAORD_FLUXO_CAIXA():
  return dataframe_query(f'''
    SELECT
      tc.DATA AS Data,
      te.NOME_FANTASIA AS Empresa,
      SUM(vpa.VALOR_PARCELA) AS Receita_Projetada_Extraord
    FROM
      T_CALENDARIO tc
    LEFT JOIN View_Parcelas_Agrupadas vpa ON tc.DATA = vpa.DATA_VENCIMENTO
    LEFT JOIN T_EMPRESAS te ON vpa.FK_EMPRESA = te.ID
    WHERE
      vpa.DATA_VENCIMENTO IS NOT NULL
      AND vpa.DATA_RECEBIMENTO IS NULL
      AND Data >= CURDATE() 
      AND Data < DATE_ADD(CURDATE(), INTERVAL 365 DAY)
      AND te.NOME_FANTASIA IS NOT NULL
    GROUP BY
      te.NOME_FANTASIA,
      vpa.DATA_VENCIMENTO
    ORDER BY
      te.NOME_FANTASIA,
      vpa.DATA_VENCIMENTO,
      Data ASC
''')


@st.cache_data
def GET_EVENTOS_FLUXO_CAIXA():
  return dataframe_query('''
    SELECT
      tc.DATA AS Data,
      te.NOME_FANTASIA AS Empresa,
      SUM(parcelas.VALOR_PARCELA) AS Receita_Projetada_Eventos
    FROM
        T_CALENDARIO tc
    LEFT JOIN (
        SELECT tep.ID AS ID_EVENTO,
              te.ID AS FK_EMPRESA,
              trec.ID AS FK_CLIENTE,
              tpep.DATA_VENCIMENTO_PARCELA AS DATA_VENCIMENTO,
              tpep.DATA_RECEBIMENTO_PARCELA AS DATA_RECEBIMENTO,
              tpep.VALOR_PARCELA
        FROM T_PARCELAS_EVENTOS_PRICELESS tpep
        LEFT JOIN T_EVENTOS_PRICELESS tep ON tep.ID = tpep.FK_EVENTO_PRICELESS
        LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
        LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON trec.ID = tep.FK_CLIENTE
    ) AS parcelas ON tc.DATA = parcelas.DATA_VENCIMENTO
    LEFT JOIN T_EMPRESAS te ON parcelas.FK_EMPRESA = te.ID
    WHERE
        parcelas.DATA_VENCIMENTO IS NOT NULL
        AND parcelas.DATA_RECEBIMENTO IS NULL
        AND tc.DATA >= CURDATE() 
        AND tc.DATA < DATE_ADD(CURDATE(), INTERVAL 365 DAY)
        AND te.NOME_FANTASIA IS NOT NULL
    GROUP BY
        te.NOME_FANTASIA,
        parcelas.DATA_VENCIMENTO
    ORDER BY
        te.NOME_FANTASIA,
        parcelas.DATA_VENCIMENTO,
        Data ASC
''')


@st.cache_data
def GET_RECEITAS_EXTRAORD_DO_DIA():
  return dataframe_query(f'''
    WITH vpa AS 
    (SELECT
      tre.ID,
      tre.FK_EMPRESA,
      tre.FK_CLIENTE,
      tre.OBSERVACOES,
      tre.FK_CLASSIFICACAO,
      tre.DATA_VENCIMENTO_PARCELA_1 AS DATA_VENCIMENTO,
      tre.DATA_RECEBIMENTO_PARCELA_1 AS DATA_RECEBIMENTO,
      tre.VALOR_PARCELA_1 AS VALOR_PARCELA
    FROM
      T_RECEITAS_EXTRAORDINARIAS tre
    UNION ALL
    SELECT
      tre.ID,
      tre.FK_EMPRESA,
      tre.FK_CLIENTE,
      tre.OBSERVACOES,
      tre.FK_CLASSIFICACAO,
      tre.DATA_VENCIMENTO_PARCELA_2 AS DATA_VENCIMENTO,
      tre.DATA_RECEBIMENTO_PARCELA_2 AS DATA_RECEBIMENTO,
      tre.VALOR_PARCELA_2 AS VALOR_PARCELA
    FROM
      T_RECEITAS_EXTRAORDINARIAS tre
    UNION ALL
    SELECT
      tre.ID,
      tre.FK_EMPRESA,
      tre.FK_CLIENTE,
      tre.OBSERVACOES,
      tre.FK_CLASSIFICACAO,
      tre.DATA_VENCIMENTO_PARCELA_3 AS DATA_VENCIMENTO,
      tre.DATA_RECEBIMENTO_PARCELA_3 AS DATA_RECEBIMENTO,
      tre.VALOR_PARCELA_3 AS VALOR_PARCELA
    FROM
      T_RECEITAS_EXTRAORDINARIAS tre
    UNION ALL
    SELECT
      tre.ID,
      tre.FK_EMPRESA,
      tre.FK_CLIENTE,
      tre.OBSERVACOES,
      tre.FK_CLASSIFICACAO,
      tre.DATA_VENCIMENTO_PARCELA_4 AS DATA_VENCIMENTO,
      tre.DATA_RECEBIMENTO_PARCELA_4 AS DATA_RECEBIMENTO,
      tre.VALOR_PARCELA_4 AS VALOR_PARCELA
    FROM
      T_RECEITAS_EXTRAORDINARIAS tre
    UNION ALL
    SELECT
      tre.ID,
      tre.FK_EMPRESA,
      tre.FK_CLIENTE,
      tre.OBSERVACOES,
      tre.FK_CLASSIFICACAO,
      tre.DATA_VENCIMENTO_PARCELA_5 AS DATA_VENCIMENTO,
      tre.DATA_RECEBIMENTO_PARCELA_5 AS DATA_RECEBIMENTO,
      tre.VALOR_PARCELA_5 AS VALOR_PARCELA
    FROM
      T_RECEITAS_EXTRAORDINARIAS tre)
    SELECT 
      vpa.ID AS ID_Receita_Extraordinária,
      te.NOME_FANTASIA AS Empresa,
      trec.NOME AS Nome_Cliente,
      vpa.OBSERVACOES AS Observações,
      trec2.CLASSIFICACAO AS Classificação,
      vpa.DATA_VENCIMENTO AS Data_Vencimento_Parcela,
      vpa.VALOR_PARCELA AS Valor_Parcela
    FROM vpa
    LEFT JOIN T_EMPRESAS te ON vpa.FK_EMPRESA = te.ID
    LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON vpa.FK_CLIENTE = trec.ID
    LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON vpa.FK_CLASSIFICACAO = trec2.ID 
    WHERE
      vpa.DATA_VENCIMENTO IS NOT NULL
      AND vpa.DATA_RECEBIMENTO IS NULL 
      AND te.NOME_FANTASIA IS NOT NULL
''')


@st.cache_data
def GET_RECEITAS_EVENTOS_DO_DIA():
  return dataframe_query(f'''
    SELECT 
      tep.ID AS ID_Evento,
      te.NOME_FANTASIA AS Empresa,
      trec.NOME AS Nome_Cliente,
      tep.OBSERVACOES AS Observações,
      'Eventos' AS Classificação,
      DATE(tpep.DATA_VENCIMENTO_PARCELA) AS Data_Vencimento_Parcela,
      tpep.VALOR_PARCELA AS Valor_Parcela
    FROM T_PARCELAS_EVENTOS_PRICELESS tpep
      LEFT JOIN T_EVENTOS_PRICELESS tep ON tep.ID = tpep.FK_EVENTO_PRICELESS
      LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON tep.FK_CLIENTE = trec.ID
    WHERE
      tpep.DATA_VENCIMENTO_PARCELA IS NOT NULL
      AND tpep.DATA_RECEBIMENTO_PARCELA IS NULL 
      AND te.NOME_FANTASIA IS NOT NULL;
  ''')


# @st.cache_data
# def GET_DESPESAS_APROVADAS():
#   return dataframe_query(f'''
# SELECT
# vvap.Empresa as 'Empresa',
# vvap.Data as 'Data',
# SUM(vvap.Valores_Aprovados_Previsao) as 'Despesas_Aprovadas_Pendentes' 
# FROM View_Valores_Aprovados_Previsao vvap
# WHERE Data >= CURDATE() 
# AND Data < DATE_ADD(CURDATE(), INTERVAL 14 DAY)
# AND Empresa IS NOT NULL
# GROUP BY Data, Empresa  
# ORDER BY Data ASC
# ''')


# @st.cache_data
# def GET_DESPESAS_PAGAS():
#   return dataframe_query(f'''
# SELECT
# vvap.Empresa as 'Empresa',
# vvap.Data as 'Data',
# SUM(vvap.Valores_Pagos) as 'Despesas_Pagas' 
# FROM View_Valores_Pagos_por_Previsao vvap
# WHERE Data >= CURDATE() 
# AND Data < DATE_ADD(CURDATE(), INTERVAL 14 DAY)
# AND Empresa IS NOT NULL
# GROUP BY Data, Empresa  
# ORDER BY Data ASC
# ''')


@st.cache_data
def GET_DESPESAS_PENDENTES():
  return dataframe_query(f'''
SELECT
	tc.DATA as 'Previsao_Pgto',
	DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data_Vencimento',
    te.NOME_FANTASIA as 'Empresa',
    tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
    tdr.VALOR_LIQUIDO as 'Valor_Liquido',
	tdr.FK_STATUS_PGTO as 'Status_Pgto'
FROM T_DESPESA_RAPIDA tdr 
INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
LEFT JOIN T_CALENDARIO tc ON (tdr.PREVISAO_PAGAMENTO = tc.ID)
LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
WHERE tdp.ID IS NULL
  AND DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
  AND te.FK_GRUPO_EMPRESA = 100
  AND tdr.BIT_CANCELADA = 0
  -- AND tdr.PREVISAO_PAGAMENTO = 1220 # data de previsao = 19/01
  -- AND te.ID = 114 # Bar Brahma
  AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
  AND (tdr.FK_STATUS_PGTO IS NULL OR tdr.FK_STATUS_PGTO IN (100, 108))
UNION ALL
SELECT
	tc.DATA as 'Previsao_Pgto',
	DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) as 'Data_Vencimento',
    te.NOME_FANTASIA as 'Empresa',
    tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
    tdp.VALOR as 'Valor_Liquido',
    CASE
        WHEN tdp.PARCELA_PAGA = 1 THEN 'Pago'
        ELSE 'Pendente'
    END as 'Status_Pgto'
FROM T_DESPESA_RAPIDA tdr 
INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
LEFT JOIN T_CALENDARIO tc ON (tdp.FK_PREVISAO_PGTO = tc.ID)
LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
WHERE tdp.ID IS NOT NULL
  AND DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
  AND te.FK_GRUPO_EMPRESA = 100
  AND tdr.BIT_CANCELADA = 0
  -- AND tdp.FK_PREVISAO_PGTO = 1220 # data de previsao = 19/01
  -- AND te.ID = 114
  AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
  AND (tdp.PARCELA_PAGA IS NULL OR tdp.PARCELA_PAGA = 0)
''')


@st.cache_data
def GET_DESPESAS_PAGAS():
  return dataframe_query(f'''
SELECT
	tc.DATA as 'Previsao_Pgto',
	DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data_Vencimento',
    te.NOME_FANTASIA as 'Empresa',
    tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
    tdr.VALOR_LIQUIDO as 'Valor_Liquido',
	tdr.FK_STATUS_PGTO as 'Status_Pgto'
FROM T_DESPESA_RAPIDA tdr 
INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
LEFT JOIN T_CALENDARIO tc ON (tdr.PREVISAO_PAGAMENTO = tc.ID)
LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
WHERE tdp.ID IS NULL
  AND DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
  AND te.FK_GRUPO_EMPRESA = 100
  AND tdr.BIT_CANCELADA = 0
  -- AND tdr.PREVISAO_PAGAMENTO = 1220 # data de previsao = 19/01
  -- AND te.ID = 114 # Bar Brahma
  AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
  AND (tdr.FK_STATUS_PGTO = 103)
UNION ALL
SELECT
	tc.DATA as 'Previsao_Pgto',
	DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) as 'Data_Vencimento',
    te.NOME_FANTASIA as 'Empresa',
    tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
    tdp.VALOR as 'Valor_Liquido',
    CASE
        WHEN tdp.PARCELA_PAGA = 1 THEN 'Pago'
        ELSE 'Pendente'
    END as 'Status_Pgto'
FROM T_DESPESA_RAPIDA tdr 
INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
LEFT JOIN T_CALENDARIO tc ON (tdp.FK_PREVISAO_PGTO = tc.ID)
LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
WHERE tdp.ID IS NOT NULL
  AND DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
  AND te.FK_GRUPO_EMPRESA = 100
  AND tdr.BIT_CANCELADA = 0
  -- AND tdp.FK_PREVISAO_PGTO = 1220 # data de previsao = 19/01
  -- AND te.ID = 114
  AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
  AND (tdp.PARCELA_PAGA = 1)
''')


@st.cache_data
def GET_DETALHES_DESPESAS_PENDENTES():
  return dataframe_query(f'''
  SELECT
    DATE_FORMAT(tc.DATA, '%Y-%m-%d') as 'Previsao_Pgto',
    tdr.VENCIMENTO AS 'Data_Vencimento',
    tdr.ID as 'ID_Despesa',
    tdr.FK_APROVACAO_DIRETORIA AS FK_Aprovacao_Diretoria,
    tsad.DESCRICAO AS Status_Aprovacao_Diretoria,
    "Nulo" as 'ID_Parcela',
    te.NOME_FANTASIA as 'Loja',
    tf.FANTASY_NAME as 'Fornecedor',
    tdr.VALOR_LIQUIDO as 'Valor',
    "Falso" as 'Parcelamento',
    CASE
        WHEN tdr.FK_STATUS_PGTO = 103 THEN 'Pago'
        ELSE 'Pendente'
    END as 'Status_Pgto'
  FROM T_DESPESA_RAPIDA tdr 
  INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
  INNER JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
  LEFT JOIN T_CALENDARIO tc ON (tdr.PREVISAO_PAGAMENTO = tc.ID)
  LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
  LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
  WHERE tdp.ID is NULL 
    AND tdr.BIT_CANCELADA = 0
   	AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
  UNION ALL
  SELECT
    DATE_FORMAT(tc.DATA, '%Y-%m-%d') as 'Previsao_Pgto',
    tdr.VENCIMENTO AS 'Data_Vencimento',
    tdr.ID as 'ID_Despesa',
    tdr.FK_APROVACAO_DIRETORIA AS FK_Aprovacao_Diretoria,
    tsad.DESCRICAO AS Status_Aprovacao_Diretoria,
    tdp.ID as 'ID_Parcela',
    te.NOME_FANTASIA as 'Loja',
    tf.FANTASY_NAME as 'Fornecedor',
    tdp.VALOR as 'Valor',
    "True" as 'Parcelamento',
    CASE
        WHEN tdp.PARCELA_PAGA = 1 THEN 'Pago'
        ELSE 'Pendente'
    END as 'Status_Pgto'
  FROM T_DESPESA_RAPIDA tdr 
  LEFT JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
  LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
  LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
  LEFT JOIN T_CALENDARIO tc ON (tdp.FK_PREVISAO_PGTO = tc.ID)
  LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
  WHERE tdp.ID is NOT NULL 
    AND tdr.BIT_CANCELADA = 0
    AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
''')

###########################  Previsão Faturamento  #############################

@st.cache_data
def GET_PREVISOES_ZIG_AGRUPADAS():
  return dataframe_query(f'''
  SELECT
    te.NOME_FANTASIA AS Empresa,
    tzf.DATA AS Data,
    SUM(tzf.VALOR) AS Valor
  FROM
    T_ZIG_FATURAMENTO tzf
    LEFT JOIN T_EMPRESAS te ON tzf.FK_LOJA = te.ID
  WHERE
    tzf.DATA >= '2023-08-01 00:00:00'
    AND tzf.VALOR > 0
  GROUP BY
    Data,
    Empresa
  ORDER BY
    Data,
    Empresa;
''')


@st.cache_data
def GET_FATURAMENTO_REAL():
  return dataframe_query(f'''
  SELECT
	  te.NOME_FANTASIA as 'Loja',
	  tzf.DATA as 'Data',
	  SUM(tzf.VALOR) as 'Valor_Faturado' 
	FROM T_ZIG_FATURAMENTO tzf 
	INNER JOIN T_EMPRESAS te ON (tzf.FK_LOJA = te.ID)
	GROUP BY te.ID, tzf.DATA
''')


@st.cache_data
def GET_DESPESAS_PROVISIONADAS_MENSAIS():
  return dataframe_query(f'''
    SELECT 
      te.ID AS 'ID Casa',
      te.NOME_FANTASIA AS 'Casa',
      tf.CORPORATE_NAME AS 'Fornecedor',
      tfpag.DESCRICAO AS 'Forma Pagamento',
      tpp.DESCRICAO AS 'Descrição',
      tpp.DATA_COMPETENCIA AS 'Data Competência',
      tpp.DATA_VENCIMENTO AS 'Data Vencimento',
      tccg1.DESCRICAO AS 'Classificação Contábil 1',
      tccg2.DESCRICAO AS 'Classificação Contábil 2',
      tpp.VALOR AS 'Valor',
      tfp.FREQUENCIA AS 'Frequência'
    FROM T_PROVISOES_PADRAO AS tpp
    LEFT JOIN T_EMPRESAS AS te ON (tpp.FK_EMPRESA = te.ID)  
    LEFT JOIN T_FORNECEDOR AS tf ON (tpp.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_FORMAS_DE_PAGAMENTO AS tfpag ON (tpp.FK_FORMA_PAGAMENTO = tfpag.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 AS tccg1 ON (tpp.FK_CLASSIFICACAO_CONT_GRUPO_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 AS tccg2 ON (tpp.FK_CLASSIFICACAO_CONT_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_FREQUENCIA_PROVISOES AS tfp ON (tpp.FK_FREQUENCIA = tfp.ID)
    WHERE tpp.FK_FREQUENCIA = 101 # Mensal                                   
''')


@st.cache_data
def GET_DESPESAS_RAPIDAS_PREVISTAS():
  return dataframe_query('''
    SELECT
      tdr.ID AS 'ID_Despesa',
      tc.DATA as 'Previsao_Pgto',
      tdr.COMPETENCIA AS 'Data_Competencia',
      DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data_Vencimento',
      te.ID AS 'ID Casa',                   
      te.NOME_FANTASIA as 'Casa',
      tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
      tdr.VALOR_LIQUIDO as 'Valor_Liquido',
      CASE
        WHEN tdr.FK_STATUS_PGTO = 103 THEN 'Pago'
        ELSE 'Pendente'
      END as 'Status_Pgto',
      tf.CORPORATE_NAME AS 'Fornecedor',                   
      tccg1.DESCRICAO AS 'Class_Cont_1',
      tccg2.DESCRICAO AS 'Class_Cont_2',
      trp.DESCRICAO AS 'Real/Provisão'                   
    FROM T_DESPESA_RAPIDA tdr 
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_CALENDARIO tc ON (tdr.PREVISAO_PAGAMENTO = tc.ID)
    LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
    LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
    LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
    LEFT JOIN T_FORNECEDOR AS tf ON (tdr.FK_FORNECEDOR = tf.ID)                     
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 AS tccg1 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 AS tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_REAL_PROVISAO AS trp ON (tdr.FK_REAL_PROVISAO = trp.ID)                     
    WHERE tdp.ID IS NULL
      AND DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
      AND te.FK_GRUPO_EMPRESA = 100
      AND tdr.BIT_CANCELADA = 0
      AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
    --   AND (tdr.FK_STATUS_PGTO = 103)
    UNION ALL
    SELECT
      tdr.ID AS 'ID_Despesa',
      tc.DATA as 'Previsao_Pgto',
      tdr.COMPETENCIA AS 'Data_Competencia',
      DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) as 'Data_Vencimento',
      te.ID AS 'ID Casa',                   
      te.NOME_FANTASIA as 'Casa',
      tdr.FK_APROVACAO_DIRETORIA as 'Status_Diretoria',
      tdp.VALOR as 'Valor_Liquido',
      CASE
          WHEN tdp.PARCELA_PAGA = 1 THEN 'Pago'
          ELSE 'Pendente'
      END as 'Status_Pgto',
      tf.CORPORATE_NAME AS 'Fornecedor',                   
      tccg1.DESCRICAO AS 'Class_Cont_1',
      tccg2.DESCRICAO AS 'Class_Cont_2',
      trp.DESCRICAO AS 'Real/Provisão'                        
    FROM T_DESPESA_RAPIDA tdr 
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
    LEFT JOIN T_CALENDARIO tc ON (tdp.FK_PREVISAO_PGTO = tc.ID)
    LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
    LEFT JOIN T_FORNECEDOR AS tf ON (tdr.FK_FORNECEDOR = tf.ID)                     
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 AS tccg1 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 AS tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_REAL_PROVISAO AS trp ON (tdr.FK_REAL_PROVISAO = trp.ID)                                          
    WHERE tdp.ID IS NOT NULL
      AND DATE_ADD(tdp.DATA, INTERVAL 30 SECOND) >= '2025-01-01 00:00:00'
      AND te.FK_GRUPO_EMPRESA = 100
      AND tdr.BIT_CANCELADA = 0
      AND (tdr.FK_APROVACAO_DIRETORIA IS NULL OR tdr.FK_APROVACAO_DIRETORIA IN (100, 101, 103, 105, 108))
    --   AND (tdp.PARCELA_PAGA = 1)
  ''')