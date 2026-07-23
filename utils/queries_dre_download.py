import streamlit as st
from utils.functions.general_functions import dataframe_query


@st.cache_data
def DRE_AUT_BLUE_ME_SEM_PEDIDO(ids_casa):
    return dataframe_query(f'''
    SELECT
    DISTINCT tdr.ID as 'tdr_ID',
    te.NOME_FANTASIA as 'Casa',
    tf.CORPORATE_NAME as 'Fornecedor',
    tdr.NF as 'Doc_Serie',
    STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') as 'Data_Emissao',
    STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d') as 'Data_Vencimento',
    tccg.DESCRICAO as 'Class_Cont_Grupo_1',
    tccg2.DESCRICAO as 'Class_Cont_Grupo_2',
    tdr.OBSERVACAO as 'Observacao',
    tdr.VALOR_PAGAMENTO * (-1) as 'Valor_Original',
    tdr.VALOR_LIQUIDO * (-1) as 'Valor_Liquido',
    tapdc.DESCRICAO_PLANO_DE_CONTAS as 'Plano_de_Contas',
    vcpj.Cargo as 'Cargo',
    vcpj.Cargo_DRE as 'Cargo_DRE',
    CASE
		WHEN tdr.FK_REAL_PROVISAO = 100 THEN 'Provisionado'
	     ELSE 'Real'
    END as Status_Provisao_Real,
    tsp.DESCRICAO as 'Status_Pagamento',
    DATE_FORMAT(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d'), '%m/%Y') AS Mes_Texto,
    tdr.BIT_CANCELADA
    FROM T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
    LEFT JOIN T_ASSOCIATIVA_PLANO_DE_CONTAS tapdc ON (tccg2.ID = tapdc.FK_CLASSIFICACAO_GRUPO_2)
    LEFT JOIN View_Cargos_PJ vcpj ON (tf.CORPORATE_NAME = vcpj.Codigo_PJ)
    LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri ON (tdr.ID = tdri.FK_DESPESA_RAPIDA)
    WHERE te.ID IN ({ids_casa})
    AND tdri.ID IS NULL
    AND STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') >= '2025-12-01 00:00:00'
    AND tdr.BIT_CANCELADA = 0
    AND tccg.FK_VERSAO_PLANO_CONTABIL = 103
    ORDER BY tdr.COMPETENCIA DESC;                                   
    ''')


@st.cache_data
def DRE_AUT_BLUE_ME_COM_PEDIDO(ids_casa):
  return dataframe_query(f'''
  WITH despesa_com_insumos AS (
    SELECT
        tdr.ID,
        tdr.FK_LOJA,
        tdr.COMPETENCIA,
        tdr.DATA_ENTREGA,
        tdr.VENCIMENTO,
        tdr.NF as Doc_Serie,
        tf.CORPORATE_NAME,
        tdr.VALOR_LIQUIDO,
        SUM(tdri.VALOR) AS Valor_Total_Insumos,
        SUM(CASE WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR ELSE 0 END) AS Valor_Alimentos,
        SUM(CASE WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR ELSE 0 END) AS Valor_Bebidas,
        SUM(CASE WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR ELSE 0 END) AS Valor_Descartaveis,
        SUM(CASE WHEN tin1.DESCRICAO = 'GELO / GAS / CARVAO / VELAS' THEN tdri.VALOR ELSE 0 END) AS Valor_Gelo_Gas,
        SUM(CASE WHEN tin1.DESCRICAO = 'UTENSILIOS' THEN tdri.VALOR ELSE 0 END) AS Valor_Utensilios,
        SUM(CASE WHEN tin1.DESCRICAO NOT IN ('ALIMENTOS', 'BEBIDAS', 'DESCARTAVEIS/HIGIENE E LIMPEZA', 'GELO / GAS / CARVAO / VELAS', 'UTENSILIOS') THEN tdri.VALOR ELSE 0 END) AS Valor_Outros
    FROM T_DESPESA_RAPIDA tdr
    LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
    LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri ON tdr.ID = tdri.FK_DESPESA_RAPIDA
    LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tdri.FK_INSUMO = tin5.ID
    LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID
    LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID
    LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
    LEFT JOIN T_INSUMOS_NIVEL_1 tin1 ON tin2.FK_INSUMOS_NIVEL_1 = tin1.ID
    WHERE tdri.ID IS NOT NULL
    AND tdr.BIT_CANCELADA = 0
    GROUP BY tdr.ID
)
SELECT
	dci.ID as 'tdr_ID',
	te.ID as 'ID_Loja',
    te.NOME_FANTASIA AS 'Loja',
    dci.CORPORATE_NAME AS 'Fornecedor',
    dci.Doc_Serie as 'Doc_Serie',
    STR_TO_DATE(dci.COMPETENCIA, '%Y-%m-%d') AS 'Data_Emissao',
    DATE(dci.DATA_ENTREGA) AS 'Data_Recebimento',
    STR_TO_DATE(dci.VENCIMENTO, '%Y-%m-%d') AS 'Data_Vencimento',
    dci.VALOR_LIQUIDO AS 'Valor_Liquido',
    dci.Valor_Total_Insumos AS 'Valor_Cotacao',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Alimentos / dci.Valor_Total_Insumos)), 2) AS 'Valor_Liq_Alimentos',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Bebidas / dci.Valor_Total_Insumos)), 2) AS 'Valor_Liq_Bebidas',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Descartaveis / dci.Valor_Total_Insumos)), 2) AS 'Valor_Liq_Descart_Hig_Limp',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Gelo_Gas / dci.Valor_Total_Insumos)), 2) AS 'Valor_Gelo_Gas_Carvao_Velas',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Utensilios / dci.Valor_Total_Insumos)), 2) AS 'Valor_Utensilios',
    ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Outros / dci.Valor_Total_Insumos)), 2) AS 'Valor_Liq_Outros',
    CASE
    	WHEN dci.DATA_ENTREGA IS NOT NULL
    		THEN DATE_FORMAT(dci.DATA_ENTREGA, '%m/%Y')
    	ELSE DATE_FORMAT(STR_TO_DATE(dci.COMPETENCIA, '%Y-%m-%d'), '%m/%Y')
    END AS 'Mes_Texto'
FROM despesa_com_insumos dci
JOIN T_EMPRESAS te ON dci.FK_LOJA = te.ID
WHERE te.ID IN ({ids_casa})
AND dci.COMPETENCIA >= '2025-12-01'
ORDER BY dci.ID DESC;
  ''')


@st.cache_data
def DRE_AUT_FATURAMENTO_ZIG(ids_casa):
  return dataframe_query(f'''
  SELECT
    te.ID AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    cast(tivd.EVENT_DATE AS date) AS Data_Evento,
    concat(month(cast(tivd.EVENT_DATE AS date)), '/', year(cast(tivd.EVENT_DATE AS date))) AS Mes_Texto,
    tivc2.DESCRICAO AS Categoria,
	  SUM((tivd.VALOR_UNITARIO  * tivd.QUANTIDADE)) AS Soma_Valor_Transacao_Bruto,
    SUM(tivd.DESCONTO) AS Soma_Desconto,
    SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Soma_Valor_Transacao_Liquido
  FROM T_ITENS_VENDIDOS_DIA tivd
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivd.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tivd.EVENT_DATE AS date) >= '2025-12-01'
  AND te.ID IN ({ids_casa})
  GROUP BY
    ID_Loja,
    Categoria,
    Data_Evento
  ORDER BY tivd.EVENT_DATE DESC;
  ''')


@st.cache_data
def DRE_AUT_FATURAMENTO_ZIG_DELIVERY(ids_casa):
  return dataframe_query(f'''
  SELECT
    te.ID AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    cast(tivd.EVENT_DATE AS date) AS Data_Evento,
    concat(month(cast(tivd.EVENT_DATE AS date)), '/', year(cast(tivd.EVENT_DATE AS date))) AS Mes_Texto,
    tivc2.DESCRICAO AS Categoria,
    SUM((tivd.VALOR_UNITARIO  * tivd.QUANTIDADE)) AS Soma_Valor_Transacao_Bruto,
    SUM(tivd.DESCONTO) AS Soma_Desconto,
    SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Soma_Valor_Transacao_Liquido
  FROM T_ITENS_VENDIDOS_DIA tivd
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivd.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tivd.EVENT_DATE AS date) >= '2025-01-01'
  AND te.ID IN ({ids_casa})
  GROUP BY
    ID_Loja,
    Categoria,
    Data_Evento
  ORDER BY tivd.EVENT_DATE DESC;
  ''')


@st.cache_data
def DRE_AUT_RECEITAS_EXTRAORD(ids_casa):
  return dataframe_query(f'''
  SELECT
          vpa.ID AS 'ID_receita',
          CASE
              WHEN te.ID IN (149, 161, 162, 179) THEN 'Priceless'
              WHEN te.ID = 178 THEN 'Blue Note - São Paulo'                                                             
              ELSE te.NOME_FANTASIA
          END AS 'Casa',
          trec.NOME AS 'Cliente',
          trec2.CLASSIFICACAO AS 'Classificacao',
          tep.ID as 'ID_Evento',
		  tep.NOME_EVENTO as 'Nome_Evento',
		  tte.DESCRICAO as 'Tipo_Evento',
		  tme.DESCRICAO as 'Modelo_Evento',
          tre.VALOR as 'Valor_Total',
          tre.DATA_OCORRENCIA AS 'Data_Ocorrencia',
          vpa.DATA_RECEBIMENTO AS 'Recebimento_Parcela',
          vpa.VALOR_PARCELA AS 'Valor_Parcela',
          tsp.DESCRICAO as 'Status_Pgto',
		  tre.VALOR_CATEGORIA_AB as 'Categ_AB',
		  tre.VALOR_CATEGORIA_ALUGUEL as 'Categ_Aluguel',
		  tre.VALOR_CATEGORIA_ARTISTICO as 'Categ_Artist',
		  tre.VALOR_CATEGORIA_COUVERT as 'Categ_Couvert',
		  tre.VALOR_CATEGORIA_LOCACAO as 'Categ_Locacao',
		  tre.VALOR_CATEGORIA_PATROCINIO as 'Categ_Patroc',
		  tre.VALOR_CATEGORIA_TAXA_SERVICO as 'Categ_Taxa_Serv',
		  DATE_FORMAT(CAST(tre.DATA_OCORRENCIA AS DATE), '%m/%Y') AS 'Ocorrencia_Mes_Texto',
		  DATE_FORMAT(CAST(vpa.DATA_RECEBIMENTO AS DATE), '%m/%Y') AS 'Recebimento_Mes_Texto'
      FROM (
          SELECT
              tre.ID,
              tre.FK_EMPRESA,
              tre.FK_CLIENTE,
              tre.DATA_VENCIMENTO_PARCELA_1 AS DATA_VENCIMENTO,
              tre.DATA_RECEBIMENTO_PARCELA_1 AS DATA_RECEBIMENTO,
              tre.VALOR_PARCELA_1 AS VALOR_PARCELA,
              tre.FK_STATUS_PAGAMENTO_PARCELA_1 AS STATUS_PGTO
          FROM T_RECEITAS_EXTRAORDINARIAS tre
          UNION ALL
          SELECT
              tre.ID,
              tre.FK_EMPRESA,
              tre.FK_CLIENTE,
              tre.DATA_VENCIMENTO_PARCELA_2 AS DATA_VENCIMENTO,
              tre.DATA_RECEBIMENTO_PARCELA_2 AS DATA_RECEBIMENTO,
              tre.VALOR_PARCELA_2 AS VALOR_PARCELA,
              tre.FK_STATUS_PAGAMENTO_PARCELA_2 AS STATUS_PGTO
          FROM T_RECEITAS_EXTRAORDINARIAS tre
          UNION ALL
          SELECT
              tre.ID,
              tre.FK_EMPRESA,
              tre.FK_CLIENTE,
              tre.DATA_VENCIMENTO_PARCELA_3 AS DATA_VENCIMENTO,
              tre.DATA_RECEBIMENTO_PARCELA_3 AS DATA_RECEBIMENTO,
              tre.VALOR_PARCELA_3 AS VALOR_PARCELA,
              tre.FK_STATUS_PAGAMENTO_PARCELA_3 AS STATUS_PGTO
          FROM T_RECEITAS_EXTRAORDINARIAS tre
          UNION ALL
          SELECT
              tre.ID,
              tre.FK_EMPRESA,
              tre.FK_CLIENTE,
              tre.DATA_VENCIMENTO_PARCELA_4 AS DATA_VENCIMENTO,
              tre.DATA_RECEBIMENTO_PARCELA_4 AS DATA_RECEBIMENTO,
              tre.VALOR_PARCELA_4 AS VALOR_PARCELA,
              tre.FK_STATUS_PAGAMENTO_PARCELA_4 AS STATUS_PGTO
          FROM T_RECEITAS_EXTRAORDINARIAS tre
          UNION ALL
          SELECT
              tre.ID,
              tre.FK_EMPRESA,
              tre.FK_CLIENTE,
              tre.DATA_VENCIMENTO_PARCELA_5 AS DATA_VENCIMENTO,
              tre.DATA_RECEBIMENTO_PARCELA_5 AS DATA_RECEBIMENTO,
              tre.VALOR_PARCELA_5 AS VALOR_PARCELA,
              tre.FK_STATUS_PAGAMENTO_PARCELA_5 AS STATUS_PGTO
          FROM T_RECEITAS_EXTRAORDINARIAS tre
      ) vpa
      INNER JOIN T_EMPRESAS te ON (vpa.FK_EMPRESA = te.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS tre ON (vpa.ID = tre.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (vpa.FK_CLIENTE = trec.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON (tre.FK_CLASSIFICACAO = trec2.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON (tre.FK_FORMA_PAGAMENTO = tfdp.ID)
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (vpa.STATUS_PGTO = tsp.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tre.FK_CONTA_BANCARIA = tcb.ID)
      LEFT JOIN T_EVENTO_PRE tep ON (tre.FK_EVENTO = tep.ID)
      LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
	  LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
      WHERE vpa.DATA_VENCIMENTO IS NOT NULL
      AND te.ID IN ({ids_casa})
      AND trec2.ID IN (111,124,130,109,104,125) # Eventos / Coleta de Oleo / Patrocínios / Visibilidade nos Bares (mkt)
	  AND (STR_TO_DATE(tre.DATA_OCORRENCIA, '%Y-%m-%d') >= '2025-12-01 00:00:00' OR STR_TO_DATE(vpa.DATA_RECEBIMENTO, '%Y-%m-%d') >= '2025-12-01 00:00:00')
	  ORDER BY tre.ID desc;
  ''')


@st.cache_data
def DRE_BILHETERIA_AUTOMATIZADA(ids_casa):
  return dataframe_query(f'''
  SELECT
    te.NOME_FANTASIA AS 'Casa',
    tpb.NOME_PLATAFORMA AS 'Plataforma',
    DATE_FORMAT(tfb.DATA_COMPETENCIA,'%m/%Y') AS 'Mes_Texto_Competencia',
    DATE(tfb.DATA_COMPETENCIA) AS 'Data Competência',
    DATE(tfb.DATA_COMPRA) AS 'Data Compra',
    tfb.DESCRICAO AS 'Descrição',
    tfb.REBATE AS 'Rebate',
    tfb.QUANTIDADE AS 'Qtde',
    tfb.VALOR_INGRESSO AS 'Valor Ingresso',
    tfb.VALOR_DESCONTOS AS 'Valor Descontos',
    CASE
      WHEN te.ID = 128 THEN (tfb.VALOR_INGRESSO * tfb.QUANTIDADE) 
      WHEN te.ID = 145 THEN tfb.VALOR_BRUTO             
    END AS 'Valor Bruto',
    CASE
      WHEN te.ID = 128 THEN (tfb.VALOR_INGRESSO * tfb.QUANTIDADE - tfb.VALOR_DESCONTOS) 
      WHEN te.ID = 145 THEN (tfb.VALOR_BRUTO - tfb.VALOR_DESCONTOS)            
    END AS 'Valor Liquido'
	FROM T_FATURAMENTO_BILHETERIA tfb
	INNER JOIN T_EMPRESAS te ON te.ID = tfb.FK_EMPRESA
	INNER JOIN T_PLATAFORMAS_BILHETERIA tpb ON tpb.ID = tfb.FK_PLATAFORMA_VENDA
	WHERE tfb.FK_EMPRESA IN ({ids_casa})
	AND STR_TO_DATE(tfb.DATA_COMPETENCIA, '%Y-%m-%d') >= '2026-06-01 00:00:00'
	ORDER BY tfb.DATA_COMPETENCIA;
  ''')


@st.cache_data
def DRE_BD_EVENTOS_NOVO(ids_casa):
  return dataframe_query(f'''
  SELECT
    te.NOME_FANTASIA AS 'Casa',
    tpep.ID AS 'ID_Parcela',
    tep.ID AS 'ID_Evento',
    tep.DATA_EVENTO AS 'Data_Evento',
    tep.NOME_EVENTO AS 'Nome_do_Evento',
    tee.NOME_COMPLETO AS 'Comercial_Responsável',
    tme.DESCRICAO as 'Modelo_Evento',
    ROUND(COALESCE(tpep.VALOR_PARCELA, 0), 2) AS 'Valor_Parcela',
    ROUND(COALESCE(tep.VALOR_TOTAL_EVENTO, 0), 2) AS 'Valor Total',
    ROUND(COALESCE((COALESCE(tep.VALOR_AB, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor AB',
    ROUND(COALESCE((COALESCE(tep.VALOR_TAXA_SERVICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Taxa Serviço',
    ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_ESPACO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Locação Espaço',
    ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Contratação Artístico',
    ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Contratação Técnico de Som',
    ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Contatação Bilheteria/Couvert Artístico',
    ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_GERADOR, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Locação Gerador',
    ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Locação Decoração/Mobiliário',
    ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_UTENSILIOS, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Locação Utensílios',
    ROUND(COALESCE((COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Mão de Obra Extra',
    ROUND(COALESCE((COALESCE(tep.VALOR_COMISSAO_BV, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Comissão BV',
    ROUND(COALESCE((COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Taxa Administrativa',
    ROUND(COALESCE((COALESCE(tep.VALOR_EXTRAS_GERAIS, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Extras Gerais',
    ROUND(COALESCE((COALESCE(tep.VALOR_IMPOSTO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor_Imposto',
    ROUND(COALESCE((COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) AS 'Valor Acréscimo Forma de Pagamento',
    tpep.DATA_VENCIMENTO_PARCELA AS 'Data_Vencimento',
    tsp.DESCRICAO AS 'Status_Pagamento',
    tpep.DATA_RECEBIMENTO_PARCELA AS 'Data_Recebimento',
    DATE_FORMAT(STR_TO_DATE(tep.DATA_EVENTO, '%Y-%m-%d'), '%m/%Y') AS 'Mes_Texto_Evento',
    DATE_FORMAT(STR_TO_DATE(tpep.DATA_RECEBIMENTO_PARCELA, '%Y-%m-%d'), '%m/%Y') AS 'Mes_Texto_Recebimento'
  FROM T_PARCELAS_EVENTOS_PRICELESS tpep
  LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
  LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
  LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
  LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
  LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
  LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tee.ID = tep.FK_EXECUTIVA_EVENTOS)
  WHERE te.ID IN ({ids_casa})
  AND tep.FK_STATUS_EVENTO = 101
  ORDER BY tep.DATA_EVENTO DESC;
  ''')


@st.cache_data
def DRE_BD_EVENTOS_NOVO_PRICELESS(ids_casa):
  return dataframe_query(f'''
    WITH TOTALS AS (
  SELECT
    ID,
    ROUND(
    	COALESCE(VALOR_LOCACAO_AROO_1,0)+
    	COALESCE(VALOR_LOCACAO_AROO_2,0)+
    	COALESCE(VALOR_LOCACAO_AROO_3,0)+
    	COALESCE(VALOR_LOCACAO_ANEXO,0)+
    	COALESCE(VALOR_LOCACAO_NOTIE,0)+
    	COALESCE(VALOR_LOCACAO_MIRANTE,0)+
    	COALESCE(VALOR_LOCACAO_BAR,0),2) AS Valor_Locacao_Total,
    ROUND(
    	COALESCE(VALOR_TAXA_SERVICO,0)+
    	COALESCE(VALOR_LOCACAO_DECORACAO_MOBILIARIO,0)+
    	COALESCE(VALOR_LOCACAO_GERADOR,0)+
    	COALESCE(VALOR_LOCACAO_UTENSILIOS,0)+
    	COALESCE(VALOR_MAO_DE_OBRA_EXTRA,0)+
    	COALESCE(VALOR_TAXA_ADMINISTRATIVA,0)+
    	COALESCE(VALOR_COMISSAO_BV,0)+
    	COALESCE(VALOR_EXTRAS_GERAIS,0)+
    	COALESCE(VALOR_IMPOSTO,0)+
    	COALESCE(VALOR_ACRESCIMO_FORMA_PAGAMENTO,0),2) AS Valor_Outros_Total
  FROM T_EVENTOS_PRICELESS
)
SELECT
  te.NOME_FANTASIA AS 'Casa',
  tpep.ID AS 'ID_Parcela',
  tep.ID AS 'ID_Evento',
  tep.DATA_EVENTO AS 'Data_Evento',
  tep.NOME_EVENTO AS 'Nome_do_Evento',
  tcep.DESCRICAO AS 'Categoria Parcela',
  ROUND(COALESCE(tpep.VALOR_PARCELA,0),2) AS 'Valor_Parcela',
  ROUND(COALESCE(tep.VALOR_TOTAL_EVENTO,0),2) AS 'Valor Total',
  CASE WHEN tcep.DESCRICAO='A&B' THEN ROUND(COALESCE(tep.VALOR_AB,0) * COALESCE(tpep.VALOR_PARCELA / NULLIF(tep.VALOR_AB,0),0),2) ELSE 0 END AS 'Valor AB',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_SERVICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Taxa Serviço',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Contratação Artístico',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Contratação Técnico de Som',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Contatação Bilheteria/Couvert Artístico',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_GERADOR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Gerador',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Decoração/Mobiliário',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_UTENSILIOS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Utensílios',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Mão de Obra Extra',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_COMISSAO_BV,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Comissão BV',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Taxa Administrativa',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_EXTRAS_GERAIS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Extras Gerais',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_IMPOSTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor_Imposto',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Acréscimo Forma de Pagamento',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_1,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 1',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_2,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 2',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_3,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 3',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_ANEXO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Anexo',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_NOTIE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Notie',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_MIRANTE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Mirante',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_BAR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Bar',
  tpep.DATA_VENCIMENTO_PARCELA AS 'Data_Vencimento',
  tsp.DESCRICAO AS 'Status_Pagamento',
  tpep.DATA_RECEBIMENTO_PARCELA AS 'Data_Recebimento',
  DATE_FORMAT(tep.DATA_EVENTO,'%m/%Y') AS 'Mes_Texto_Evento',
  DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA,'%m/%Y') AS 'Mes_Texto_Recebimento'
FROM T_PARCELAS_EVENTOS_PRICELESS tpep
JOIN T_EVENTOS_PRICELESS tep ON tpep.FK_EVENTO_PRICELESS = tep.ID
LEFT JOIN TOTALS t ON t.ID = tep.ID
LEFT JOIN T_EMPRESAS te ON tep.FK_EMPRESA = te.ID
LEFT JOIN T_STATUS_PAGAMENTO tsp ON tpep.FK_STATUS_PAGAMENTO = tsp.ID
LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON tpep.FK_CATEGORIA_PARCELA = tcep.ID
WHERE te.ID IN ({ids_casa})
AND tep.FK_STATUS_EVENTO = 101
ORDER BY tep.DATA_EVENTO DESC;
''')


@st.cache_data
def DRE_BD_EVENTOS_GERAL_PRICELESS():
  return dataframe_query(f'''
  SELECT
  tep.ID AS 'ID Evento',
  te.NOME_FANTASIA AS 'Casa',
  tee.NOME_COMPLETO AS 'Comercial Responsável',
  tep.NOME_EVENTO AS 'Nome do Evento',
  trec.NOME AS 'Cliente',
  trec.PESSOA_DE_CONTATO AS 'Pessoa de Contato',
  trec.TELEFONE AS 'Telefone',
  tep.DATA_RECEBIMENTO_LEAD AS 'Data Recebimento Lead',
  tep.DATA_CONTRATACAO AS 'Data Assinatura Contrato',
  tep.DATA_ENVIO_PROPOSTA AS 'Data Envio Proposta',
  tep.DATA_EVENTO AS 'Data Evento',
  tsep.DESCRICAO AS 'Status Evento',
  tte.DESCRICAO AS 'Tipo Evento',
  tme.DESCRICAO AS 'Modelo Evento',
  tep.VALOR_TOTAL_EVENTO AS 'Valor Total',
  tep.NUM_CLIENTES AS 'Num Pessoas',
  tep.VALOR_AB AS 'Valor AB',
  tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Servico',
  tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
  tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
  tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
  tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
  tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
  tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notiê',
  tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
  tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
  tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
  tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locacao Decoração Mobiliário',
  tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locacao Utensílios',
  tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
  tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
  tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
  tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Couvert Artístico',
  tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
  tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
  tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
  tep.VALOR_IMPOSTO AS 'Valor Imposto',
  tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
  temd.DESCRICAO AS 'Motivo Declínio',
  tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observacoes Declínio',
  tep.OBSERVACOES AS 'Observações Gerais',
  DATE_FORMAT(tep.DATA_EVENTO, '%m/%Y') AS 'Mes_Texto'                     
FROM T_EVENTOS_PRICELESS tep
LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
WHERE te.ID in (149)
  ''')


@st.cache_data
def DRE_AUT_FOLHA(ids_casa):
  return dataframe_query(f'''
    WITH funcionarios_ativos_periodo AS (
    SELECT DISTINCT
        te.ID AS id_casa,
        te.NOME_FANTASIA AS casa,
        tsf.ID AS id_func,
        tsf.COD_FUNCIONARIO_SINERGY AS cod_func,
        tsf.CPF AS cpf,
        tsf.NOME AS nome
    FROM T_SINERGY_HISTORICO_FUNCIONARIOS tshf
    INNER JOIN T_SINERGY_FUNCIONARIOS_STATUS tsfs ON tsfs.ID = tshf.FK_FUNCIONARIO_STATUS
    INNER JOIN T_SINERGY_FUNCIONARIOS tsf ON tsf.ID = tshf.FK_FUNCIONARIO
    INNER JOIN T_SINERGY_CARGOS_FUNCIONARIOS tscf ON tscf.ID = tshf.FK_CARGOS_FUNCIONARIOS
    INNER JOIN T_SINERGY_FILIAIS tsf2 ON tsf2.ID = tshf.FK_FILIAL
    INNER JOIN T_EMPRESAS te ON te.ID = tsf2.FK_EMPRESA
    WHERE te.ID IN ({ids_casa})   -- <- único lugar onde você define a casa
)
SELECT
    fa.id_casa AS 'ID_CASA',
    tffs.CNPJ AS 'CNPJ_CASA',
    tffs.NUMERO_MATRICULA AS 'NUM_MATRICULA_FUNC',
    tffs.NOME AS 'NOME_FUNC',
    tffs.CPF AS 'CPF_FUNC',
    tffs.CODIGO_VERBA,
    tffs.VERBA,
    tffs.PROCESSO,
    tffs.QUANTIDADE,
    tffs.VALOR,
    CONCAT(SUBSTRING(tffs.REFERENCIA, 1, 2), '/', SUBSTRING(tffs.REFERENCIA, 3, 4)) AS 'Mes_Texto',
    tffs.DATA_CALCULO,
    tffs.DATA_PAGAMENTO
FROM funcionarios_ativos_periodo fa
INNER JOIN T_FICHA_FINANCEIRA_SINERGY tffs
    ON fa.cpf = tffs.CPF
    AND fa.cod_func = tffs.NUMERO_MATRICULA
    AND fa.id_casa = tffs.FK_CASA   -- <- garante o mesmo filtro sem repetir literal
WHERE tffs.CODIGO_VERBA = 2003 -- Filtro verba = Gorjeta
    AND STR_TO_DATE(CONCAT('01/', SUBSTRING(tffs.REFERENCIA, 1, 2), '/', SUBSTRING(tffs.REFERENCIA, 3, 4)), '%d/%m/%Y') >= '2025-12-01'
ORDER BY fa.casa, fa.nome;
  ''')



@st.cache_data
def DRE_AUT_DESCONTOS(ids_casa):
  return dataframe_query(f'''
  SELECT 
    te.NOME_FANTASIA AS 'Unidade',
    tddre.DATA AS 'Mês',
    tddre.CATEGORIA AS 'Categoria',
    tddre.TOTAL_DESCONTO AS 'Total Desc',
    tddre.CMV AS 'CMV',
    tddre.PERMANECE_DESCONTO AS 'Permanece no Desconto',
    tddre.ALOCA_CENTRO_CUSTO AS 'Aloca no Centro de Custo',
    CASE
        WHEN tddre.CENTRO_CUSTO = '-  Alimentação Funcionário' THEN '  -  Alimentação Funcionário'
        ELSE tddre.CENTRO_CUSTO 
    END AS 'Centro de Custo',
    tddre.DEDUCAO_FATURAMENTO_ALIM AS 'Dedução Faturamento - Alimento',
    tddre.DEDUCAO_FATURAMENTO_BEB AS 'Dedução Faturamento - Bebida',
    tddre.DESCONTOS_DRE AS 'Descontos - DRE',
    concat(month(cast(tddre.DATA AS date)), '/', year(cast(tddre.DATA AS date))) AS 'Mes_Texto'
  FROM T_DESCONTOS_DRE AS tddre
  LEFT JOIN T_EMPRESAS AS te ON (tddre.FK_CASA = te.ID)
  WHERE te.ID IN ({ids_casa})
  ORDER BY tddre.CATEGORIA ASC;
  ''')


@st.cache_data
def DRE_AUT_PROMOCOES_UTILIZADAS(ids_casa):
  return dataframe_query(f'''
  SELECT 
    te.NOME_FANTASIA AS 'Casa',
    tpz.DATA AS 'Mês',
    tpz.PRODUTO AS 'Produto',
    tpz.PROMOCAO AS 'Promoção',
    tpz.CATEGORIA_PRODUTO 'Categoria Produto',
    tpz.QUANTIDADE_USOS AS 'Quantidade de usos',
    tpz.DESCONTO_TOTAL AS 'Desconto total',  
    CASE 
        WHEN tivc.DESCRICAO = 'Alimentos' THEN 'A'
        WHEN tivc.DESCRICAO = 'Bebidas' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%PORÇÕES%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%PIZZA%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%SOBREMESA%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%EXECUTIVO%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%CLÁSSICO%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%ENTRADA%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%PRINCIPAIS%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%ALIMENTO%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%PRATO%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%SANDUÍCHE%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%COMEÇAR%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%NA BRASA%' THEN 'A'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%SUGEST%' THEN 'A'
        WHEN tpz.PRODUTO LIKE '%FEIJOADA%' THEN 'A'
        WHEN tpz.PRODUTO LIKE '%CUSCUZ%' THEN 'A'
        WHEN tpz.PRODUTO LIKE '%PANETONE%' THEN 'A'
        WHEN tpz.PRODUTO LIKE '%BOLINHO%' THEN 'A'
		WHEN tpz.PRODUTO LIKE '%PERNIL%' THEN 'A'
		WHEN tpz.PRODUTO LIKE '%PERNIL%' THEN 'A'
		WHEN tpz.PRODUTO LIKE '%BUFFET%' THEN 'A'
		WHEN tpz.PRODUTO LIKE '%MIGNON%' THEN 'A'
        WHEN tpz.PRODUTO LIKE '%SUCO%' THEN 'B'
        WHEN tpz.PRODUTO LIKE '%GIN%' THEN 'B'
        WHEN tpz.PRODUTO LIKE '%CHOP%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%CAIPIRINHA%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%CERVEJA%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%SOFT%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%ÁLCOOL%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%AUTORAIS%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%CAFÉ%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%BEBIDA%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%DOSE%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%CHOP%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%VINHO%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%BANHO DE FOLHAS%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%DRINK%' THEN 'B'
        WHEN tpz.CATEGORIA_PRODUTO LIKE '%MILKSHAKE%' THEN 'B'
       	WHEN tpz.CATEGORIA_PRODUTO LIKE '%BEBER%' THEN 'B'
        ELSE tivc.DESCRICAO
    END AS 'A&B',
    CASE 
    	WHEN tpz.PROMOCAO LIKE '%[Evento]%' THEN 'Eventos'
    	ELSE NULL
    END AS 'Categoria',
    concat(month(cast(tpz.DATA AS date)), '/', year(cast(tpz.DATA AS date))) AS 'Mes_Texto'
  FROM T_PROMOCOES_ZIG tpz
  LEFT JOIN (
      SELECT 
          NOME_PRODUTO,
          MIN(FK_CATEGORIA) AS FK_CATEGORIA
      FROM T_ITENS_VENDIDOS_CADASTROS
      GROUP BY NOME_PRODUTO
  ) tivc2 
      ON tpz.PRODUTO = tivc2.NOME_PRODUTO
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc ON (tivc.ID = tivc2.FK_CATEGORIA)
  LEFT JOIN T_EMPRESAS AS te ON (tpz.FK_CASA = te.ID)
  WHERE te.ID IN ({ids_casa})
  ORDER BY tpz.DATA ASC, tpz.PROMOCAO ASC;
  ''')


@st.cache_data
def DRE_AUT_ENDIVIDAMENTOS(ids_casa):
  return dataframe_query(f'''
  SELECT DISTINCT
	CASE
		WHEN tdp.FK_DESPESA IS NOT NULL
		THEN CONCAT(tdr.ID,"-",tdp.ID)
		ELSE tdr.ID
	END as 'ID_Despesa_ID_Parcela',
    te.NOME_FANTASIA as 'Empresa',
    tf.CORPORATE_NAME as 'Fornecedor_Razao_Social',
    tf.FANTASY_NAME as 'Fornecedor',
    tdr.NF 'Doc_Serie',
    tccg.DESCRICAO as 'Class_Cont_1',
    tccg2.DESCRICAO as 'Class_Cont_2',
    tdr.VALOR_PAGAMENTO as 'Valor_Original',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN 'True'
    	ELSE 'False'
    END AS 'Parcelamento',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN COUNT(tdp.ID) OVER (PARTITION BY tdr.ID)
    	ELSE NULL
    END AS 'Qtd_Parcelas',
    tdp.PARCELA as 'Num_Parcela',
    STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') as 'Data_Emissao',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN date(tdp.`DATA`)
    	ELSE date(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d %H:%i:%s'))
    END as 'Data_Vencimento',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN tdp.VALOR
    	ELSE IF(tdr.VALOR_LIQUIDO IS NULL, tdr.VALOR_PAGAMENTO, tdr.VALOR_LIQUIDO)
    END as 'Valor_Liquido',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN IF (tdp.PARCELA_PAGA = 1, "Pago", "Pendente")
    	ELSE tsp.DESCRICAO
    END as 'Status_Pagamento',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN DATE(tc2.`Data`)
    	ELSE DATE(tc.`Data`)
    END AS 'Data_Realiz_Pgto',
    tdr.OBSERVACAO as 'Descricao',
	CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
        THEN DATE_FORMAT(STR_TO_DATE(tdp.`DATA`, '%Y-%m-%d'), '%m/%Y')
    	ELSE DATE_FORMAT(STR_TO_DATE(tdr.VENCIMENTO , '%Y-%m-%d'), '%m/%Y')
    END AS 'Mes_Texto_Vencimento',
    CASE
    	WHEN tdp.FK_DESPESA IS NOT NULL
    		THEN DATE_FORMAT(DATE(tc2.`Data`), '%m/%Y')
    	ELSE DATE_FORMAT(DATE(tc.`Data`), '%m/%Y')
    END AS 'Mes_Texto_Pagamento'    
  FROM T_DESPESA_RAPIDA tdr
  INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
  LEFT JOIN T_LOJAS tl ON (te.FK_LOJA = tl.ID)
  LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON (tdr.FK_FORMA_PAGAMENTO = tfdp.ID)
  LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
  LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON (tdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID)
  LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
  LEFT JOIN T_STATUS_APROVACAO_CAIXA tsac ON (tdr.FK_APROVACAO_CAIXA = tsac.ID)
  LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
  LEFT JOIN T_CALENDARIO tc ON (tdr.FK_DATA_REALIZACAO_PGTO = tc.ID)
  LEFT JOIN T_CALENDARIO tc2 ON (tdp.FK_DATA_REALIZACAO_PGTO = tc2.ID)
  LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tdp.FK_CONTA_BANCARIA = tcb.ID)
  LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
  WHERE tccg.ID IN (165,206,244)
  AND te.ID IN ({ids_casa})
  ORDER BY tdr.ID desc, tdp.ID desc;
  ''')


@st.cache_data
def DRE_AUT_CONTAGEM(ids_casa):
  return dataframe_query(f'''
  SELECT 
    tci.ID as 'ID_Contagem',
    te.ID as 'ID_Loja',
    tci.DATA_CONTAGEM as 'Data_Contagem',
    te.NOME_FANTASIA as 'Loja',
    tci.FK_INSUMO as 'ID_Insumo',
    tin5.DESCRICAO as 'Insumo',
    tci.QUANTIDADE_INSUMO as 'Quantidade',
    tudm.UNIDADE_MEDIDA as 'Unidade_Medida',
    DATE_FORMAT(tci.DATA_CONTAGEM, '%m/%Y') AS Mes_Texto
  FROM T_CONTAGEM_INSUMOS tci 
  INNER JOIN T_EMPRESAS te ON (tci.FK_EMPRESA = te.ID)
  LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON (tci.FK_INSUMO = tin5.ID)
  LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON (tin5.FK_INSUMOS_NIVEL_4 = tin4.ID)
  LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON (tin4.FK_INSUMOS_NIVEL_3 = tin3.ID)
  LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON (tin3.FK_INSUMOS_NIVEL_2 = tin2.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin1 ON (tin2.FK_INSUMOS_NIVEL_1 = tin1.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  LEFT JOIN T_AGRUPAMENTO_CONTAGENS tac ON (tci.FK_AGRUPAMENTO_CONTAGENS = tac.ID)
  WHERE (
    (tci.FK_AGRUPAMENTO_CONTAGENS IS NULL AND DAY(tci.DATA_CONTAGEM) = 1)
    OR (tci.FK_AGRUPAMENTO_CONTAGENS IS NOT NULL AND DAY(tac.DATA_AGRUPAMENTO) = 1 AND tac.FK_ESTOQUE_TIPO_CONTAGEM = 103)
  )
  AND te.ID IN ({ids_casa})
  AND STR_TO_DATE(tci.DATA_CONTAGEM, '%Y-%m-%d') >= '2025-12-01 00:00:00';
  ''')


@st.cache_data
def DRE_AUT_PRECOS_INSUMOS(ids_casa):
  return dataframe_query(f'''
  SELECT 
    vir.tdr_ID as 'tdr_ID',
    vir.ID_Loja as 'ID_Loja',
    vir.Loja as 'Loja',
    vir.Fornecedor as 'Fornecedor',
    vir.Doc_Serie as 'Doc_Serie',
    STR_TO_DATE(vir.Data_Emissao, '%Y-%m-%d') AS Data_Emissao,
    vir.ID_Insumo_Nivel_5 as 'ID_Insumo_Nivel_5',
    vir.Nome_Insumo_Nivel_5 as 'Nome_Insumo_Nivel_5',
    vir.Nome_Insumo_Nivel_1 as 'Nome_Incumo_Nivel_1',
    vir.Quantidade as 'Quantidade',
    vir.Unidade_Medida as 'Unidade_Medida',
    vir.Valor_Insumos as 'Valor_Cotado',
    vir.Valor_Insumos / vir.Quantidade as 'Valor_Unidade_Medida',
    vir.Observacao as 'Observacao',
    DATE_FORMAT(STR_TO_DATE(vir.Data_Emissao, '%Y-%m-%d'), '%m/%Y') AS Mes_Texto
  FROM View_Insumos_Recebidos vir
  WHERE vir.ID_Loja IN ({ids_casa})
  AND STR_TO_DATE(vir.Data_Emissao, '%Y-%m-%d') >= '2025-12-01 00:00:00'
  ORDER BY vir.tdr_ID DESC;
  ''')


@st.cache_data
def DRE_AUT_VALOR_ESTOQUE(ids_casa):
  return dataframe_query(f'''
  SELECT DISTINCT
    tve.FK_CONTAGEM as 'ID_Contagem',
    te.ID as 'ID_Loja',
    te.NOME_FANTASIA as 'Loja',
    tci.DATA_CONTAGEM as 'Data_Contagem',
    tci.FK_INSUMO as 'ID_Insumo',
    tin5.DESCRICAO as 'Insumo',
    tin4.ID as 'ID_Nivel_4',
    tci.QUANTIDADE_INSUMO as 'Quantidade',
    tudm.UNIDADE_MEDIDA as 'Unidade_Medida',
    tin1.DESCRICAO as 'Categoria_Insumo',
    DATE_FORMAT(DATE_SUB(tci.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') as 'Mes_Texto',
    tve.PRECO_MEDIO_PAGO_NO_MES as 'Preco_Medio_Pago_no_Mes',
    tve.DATA_ULTIMA_COMPRA_LOCAL as 'Data_Ultima_Compra',
    tve.VALOR_ULTIMA_COMPRA_LOCAL as 'Valor_Ultima_Compra',
    tve.VALOR_ULTIMA_COMPRA_GLOBAL as 'Valor_Ultima_Compra_Global',
    tve.VALOR_EM_ESTOQUE as 'Valor_em_Estoque',
    tci.OBSERVACAO as 'Observacao'
  FROM T_VALORACAO_ESTOQUE tve
  INNER JOIN T_CONTAGEM_INSUMOS tci ON (tve.FK_CONTAGEM = tci.ID)
  INNER JOIN T_EMPRESAS te ON (tci.FK_EMPRESA = te.ID)
  INNER JOIN T_INSUMOS_NIVEL_5 tin5 ON (tci.FK_INSUMO = tin5.ID)
  INNER JOIN T_INSUMOS_NIVEL_4 tin4 ON (tin5.FK_INSUMOS_NIVEL_4 = tin4.ID)
  INNER JOIN T_INSUMOS_NIVEL_3 tin3 ON (tin4.FK_INSUMOS_NIVEL_3 = tin3.ID)
  INNER JOIN T_INSUMOS_NIVEL_2 tin2 ON (tin3.FK_INSUMOS_NIVEL_2 = tin2.ID)
  INNER JOIN T_INSUMOS_NIVEL_1 tin1 ON (tin2.FK_INSUMOS_NIVEL_1 = tin1.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  LEFT JOIN T_AGRUPAMENTO_CONTAGENS tac ON (tci.FK_AGRUPAMENTO_CONTAGENS = tac.ID)
  WHERE te.ID IN ({ids_casa})
  AND (tci.FK_AGRUPAMENTO_CONTAGENS IS NULL OR tac.FK_ESTOQUE_TIPO_CONTAGEM = 103)
  ORDER BY tci.DATA_CONTAGEM DESC, tve.VALOR_EM_ESTOQUE DESC;
  ''')


@st.cache_data
def DRE_AUT_VALOR_ESTOQUE_LOVE(ids_casa):
  return dataframe_query(f'''
  SELECT
    tve.FK_CONTAGEM as 'ID_Contagem',
    te.ID as 'ID_Loja',
    te.NOME_FANTASIA as 'Loja',
    tci.DATA_CONTAGEM as 'Data_Contagem',
    tci.FK_INSUMO as 'ID_Insumo',
    tin5.DESCRICAO as 'Insumo',
    tin4.ID as 'ID_Nivel_4',
    tci.QUANTIDADE_INSUMO as 'Quantidade',
    tudm.UNIDADE_MEDIDA as 'Unidade_Medida',
    tin1.DESCRICAO as 'Categoria_Insumo',
    DATE_FORMAT(DATE_SUB(tci.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') as 'Mes_Texto',
    tve.PRECO_MEDIO_PAGO_NO_MES as 'Preco_Medio_Pago_no_Mes',
    tve.DATA_ULTIMA_COMPRA_LOCAL as 'Data_Ultima_Compra',
    tve.VALOR_ULTIMA_COMPRA_LOCAL as 'Valor_Ultima_Compra',
    tve.VALOR_ULTIMA_COMPRA_GLOBAL as 'Valor_Ultima_Compra_Global',
    tve.VALOR_EM_ESTOQUE as 'Valor_em_Estoque',
    tci.OBSERVACAO as 'Observacao'
  FROM T_VALORACAO_ESTOQUE tve
  INNER JOIN T_CONTAGEM_INSUMOS tci ON (tve.FK_CONTAGEM = tci.ID)
  INNER JOIN T_EMPRESAS te ON (tci.FK_EMPRESA = te.ID)
  INNER JOIN T_INSUMOS_NIVEL_5 tin5 ON (tci.FK_INSUMO = tin5.ID)
  INNER JOIN T_INSUMOS_NIVEL_4 tin4 ON (tin5.FK_INSUMOS_NIVEL_4 = tin4.ID)
  INNER JOIN T_INSUMOS_NIVEL_3 tin3 ON (tin4.FK_INSUMOS_NIVEL_3 = tin3.ID)
  INNER JOIN T_INSUMOS_NIVEL_2 tin2 ON (tin3.FK_INSUMOS_NIVEL_2 = tin2.ID)
  INNER JOIN T_INSUMOS_NIVEL_1 tin1 ON (tin2.FK_INSUMOS_NIVEL_1 = tin1.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  LEFT JOIN T_AGRUPAMENTO_CONTAGENS tac ON (tci.FK_AGRUPAMENTO_CONTAGENS = tac.ID)
  WHERE te.ID IN ({ids_casa})
  AND (tac.FK_ESTOQUE_TIPO_CONTAGEM IS NULL OR tac.FK_ESTOQUE_TIPO_CONTAGEM = 103)
  ORDER BY tci.DATA_CONTAGEM DESC, tve.VALOR_EM_ESTOQUE DESC;
''')

@st.cache_data
def DRE_AUT_PRECOS_CONSOLIDADOS(ids_casa):
  return dataframe_query(f'''
  SELECT 
	  vir.Loja as Loja,
    vir.ID_Insumo_Nivel_5,
    vir.Nome_Insumo_Nivel_5,
    DATE_FORMAT(STR_TO_DATE(vir.Data_Emissao, '%Y-%m-%d'), '%m/%Y') AS Mes_Texto,
    ROUND(SUM(vir.Quantidade), 2) AS Quantidade_Comprada_no_Mes,
    ROUND(SUM(vir.Valor_Insumos), 2) AS Valor_Total_Pago_no_Mes,
    ROUND(SUM(vir.Valor_Insumos) / SUM(vir.Quantidade), 2) AS Preco_Medio_Pago_no_Mes
  FROM View_Insumos_Recebidos vir
  WHERE vir.ID_Loja IN ({ids_casa})
  AND STR_TO_DATE(vir.Data_Emissao, '%Y-%m-%d') >= '2025-12-01 00:00:00'
  GROUP BY Mes_Texto, vir.ID_Insumo_Nivel_5
  ORDER BY Mes_Texto DESC, Nome_Insumo_Nivel_5 ASC;
  ''')


@st.cache_data
def DRE_AUT_EVENTOS_AEB(ids_casa):
  return dataframe_query(f'''
  SELECT
    tec.ID as 'Evento_CMV_ID',
    te.NOME_FANTASIA as 'Casa',
    tec.`DATA` as 'Data_Evento',
    tec.VALOR_EVENTOS_A_B as 'Valor_A_B',
    DATE_FORMAT(tec.`DATA`, '%m/%Y') AS Mes_Texto
  FROM T_EVENTOS_CMV tec 
  INNER JOIN T_EMPRESAS te ON (tec.FK_EMPRESA = te.ID)
  WHERE te.ID IN ({ids_casa})
  AND STR_TO_DATE(tec.`DATA`, '%Y-%m-%d') >= '2025-12-01 00:00:00';
  ''')


@st.cache_data
def DRE_AUT_TRANSFERENCIAS(ids_casa):
  return dataframe_query(f'''
  SELECT
    tti.ID as 'ID_Transferencia',
    te.NOME_FANTASIA as 'Empresa_Saida',
    te2.NOME_FANTASIA as 'Empresa_Entrada',
    tin5.ID as 'ID_Insumo',
    tin5.DESCRICAO as 'Nome_Insumo',
    tin4.DESCRICAO as 'Insumo_Nivel_4',
    tin1.DESCRICAO as 'Insumo_Nivel_1',
    tudm.UNIDADE_MEDIDA as 'Unidade_Medida',
    tti.QUANTIDADE as 'Quantidade',
    DATE_FORMAT(tti.DATA_TRANSFERENCIA, '%m/%Y') AS Mes_Texto,
    tti.VALOR_TRANSFERENCIA as 'Valor_da_Transferencia',
    tti.OBSERVACAO as 'Observacao'
  FROM T_TRANSFERENCIAS_INSUMOS tti
  INNER JOIN T_INSUMOS_NIVEL_5 tin5 ON (tti.FK_INSUMO_NIVEL_5 = tin5.ID)
  LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON (tin5.FK_INSUMOS_NIVEL_4 = tin4.ID)
  LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON (tin4.FK_INSUMOS_NIVEL_3 = tin3.ID)
  LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON (tin3.FK_INSUMOS_NIVEL_2 = tin2.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin1 ON (tin2.FK_INSUMOS_NIVEL_1 = tin1.ID)
  LEFT JOIN T_EMPRESAS te ON (tti.FK_EMRPESA_SAIDA = te.ID)
  LEFT JOIN T_EMPRESAS te2 ON (tti.FK_EMPRESA_ENTRADA = te2.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  WHERE (te.ID IN ({ids_casa}) OR te2.ID IN ({ids_casa}))
  AND STR_TO_DATE(tti.DATA_TRANSFERENCIA, '%Y-%m-%d') >= '2025-12-01 00:00:00';
  ''')


@st.cache_data
def DRE_AUT_CONSUMO_FUNCIONARIOS(ids_casa):
  return dataframe_query(f'''
  SELECT
    tpecc.ID as 'ID_Consumo_Funcionarios',
    te.NOME_FANTASIA as 'Casa',
    tpecc.DATA_BAIXA as 'Data_Baixa',
    DATE_FORMAT(tpecc.DATA_BAIXA, '%m/%Y') AS Mes_Texto,
    tmp.DESCRICAO as 'Motivo',
    tpecc.VALOR as 'Valor',
    tpecc.OBSERVACOES as 'Observacoes'
  FROM T_PERDAS_E_CONSUMO_CONSOLIDADOS tpecc
  INNER JOIN T_EMPRESAS te ON (tpecc.FK_EMPRESA = te.ID)
  INNER JOIN T_MOTIVO_PERDAS tmp ON (tpecc.FK_MOTIVO = tmp.ID)
  WHERE te.ID IN ({ids_casa})
  AND STR_TO_DATE(tpecc.DATA_BAIXA, '%Y-%m-%d') >= '2025-12-01 00:00:00';
  ''')


@st.cache_data
def DRE_AUT_INSUMOS_PRODUCAO(ids_casa):
  return dataframe_query(f'''
  SELECT
    tipc.ID as 'ID_Contagem_Producao',
    te.NOME_FANTASIA as 'Casa',
    tipc.DATA_CONTAGEM as 'Data_Contagem',
    DATE_FORMAT(DATE_SUB(tipc.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') AS Mes_Texto,
    tip.NOME_ITEM_PRODUZIDO as 'Nome_Item_Produzido',
    tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
    tipc.QUANTIDADE_INSUMO as 'Quantidade',
    tin.DESCRICAO as 'Nivel_1',
    tipv.VALOR as 'Valor_Unidade_Medida',
    ROUND(tipc.QUANTIDADE_INSUMO * tipv.VALOR, 2) as 'Valor_Total'
  FROM T_ITENS_PRODUCAO_CONTAGEM tipc
  LEFT JOIN T_ITENS_PRODUCAO_VALORACAO tipv ON (tipc.FK_ITEM_PRODUZIDO = tipv.FK_ITEM_PRODUZIDO) AND (DATE_FORMAT(tipc.DATA_CONTAGEM, '%m/%Y') = DATE_FORMAT(tipv.DATA_VALORACAO, '%m/%Y'))
  LEFT JOIN T_ITENS_PRODUCAO tip ON (tipv.FK_ITEM_PRODUZIDO = tip.ID)
  LEFT JOIN T_EMPRESAS te ON (tip.FK_EMPRESA = te.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON (tip.FK_INSUMO_NIVEL_1 = tin.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tip.FK_UNIDADE_MEDIDA = tudm.ID)
  WHERE te.ID IN ({ids_casa});
  ''')


@st.cache_data
def DRE_EVENTOS_CONCIERGE(ids_casa):
  return dataframe_query(f'''
  WITH TOTALS AS (
  SELECT
    ID,
    ROUND(
    	COALESCE(VALOR_LOCACAO_AROO_1,0)+
    	COALESCE(VALOR_LOCACAO_AROO_2,0)+
    	COALESCE(VALOR_LOCACAO_AROO_3,0)+
    	COALESCE(VALOR_LOCACAO_ANEXO,0)+
    	COALESCE(VALOR_LOCACAO_NOTIE,0)+
    	COALESCE(VALOR_LOCACAO_MIRANTE,0)+
    	COALESCE(VALOR_LOCACAO_BAR,0),2) AS Valor_Locacao_Total,
    ROUND(
    	COALESCE(VALOR_TAXA_SERVICO,0)+
    	COALESCE(VALOR_LOCACAO_DECORACAO_MOBILIARIO,0)+
    	COALESCE(VALOR_LOCACAO_GERADOR,0)+
    	COALESCE(VALOR_LOCACAO_UTENSILIOS,0)+
    	COALESCE(VALOR_MAO_DE_OBRA_EXTRA,0)+
    	COALESCE(VALOR_TAXA_ADMINISTRATIVA,0)+
    	COALESCE(VALOR_EXTRAS_GERAIS,0)+
    	COALESCE(VALOR_IMPOSTO,0)+
    	COALESCE(VALOR_ACRESCIMO_FORMA_PAGAMENTO,0),2) AS Valor_Outros_Total
  FROM T_EVENTOS_CONCIERGE
)
SELECT
  te.NOME_FANTASIA AS 'Casa',
  tpep.ID AS 'ID_Parcela',
  tep.ID AS 'ID_Evento',
  tep.DATA_EVENTO AS 'Data_Evento',
  tep.NOME_EVENTO AS 'Nome_do_Evento',
  tcep.DESCRICAO AS 'Categoria Parcela',
  ROUND(COALESCE(tpep.VALOR_PARCELA,0),2) AS 'Valor_Parcela',
  ROUND(COALESCE(tep.VALOR_TOTAL_EVENTO,0),2) AS 'Valor Total',
  CASE WHEN tcep.DESCRICAO='A&B' THEN ROUND(COALESCE(tep.VALOR_AB,0) * COALESCE(tpep.VALOR_PARCELA / NULLIF(tep.VALOR_AB,0),0),2) ELSE 0 END AS 'Valor AB',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_SERVICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Taxa Serviço',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Contratação Artístico',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Contratação Técnico de Som',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_GERADOR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Gerador',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Decoração/Mobiliário',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_UTENSILIOS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Locação Utensílios',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Mão de Obra Extra',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Taxa Administrativa',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_EXTRAS_GERAIS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Extras Gerais',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_IMPOSTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor_Imposto',
  CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END AS 'Valor Acréscimo Forma de Pagamento',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_1,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 1',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_2,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 2',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_3,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Aroo 3',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_ANEXO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Anexo',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_NOTIE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Notie',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_MIRANTE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Mirante',
  CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_BAR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END AS 'Valor Locação Bar',
  tpep.DATA_VENCIMENTO_PARCELA AS 'Data_Vencimento',
  tsp.DESCRICAO AS 'Status_Pagamento',
  tpep.DATA_RECEBIMENTO_PARCELA AS 'Data_Recebimento',
  DATE_FORMAT(tep.DATA_EVENTO,'%m/%Y') AS 'Mes_Texto_Evento',
  DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA,'%m/%Y') AS 'Mes_Texto_Recebimento'
FROM T_PARCELAS_EVENTOS_CONCIERGE tpep
JOIN T_EVENTOS_CONCIERGE tep ON tpep.FK_EVENTO_CONCIERGE = tep.ID
LEFT JOIN TOTALS t ON t.ID = tep.ID
LEFT JOIN T_EMPRESAS te ON tep.FK_EMPRESA = te.ID
LEFT JOIN T_STATUS_PAGAMENTO tsp ON tpep.FK_STATUS_PAGAMENTO = tsp.ID
LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON tpep.FK_CATEGORIA_PARCELA = tcep.ID
WHERE te.ID IN ({ids_casa})
AND tep.FK_STATUS_EVENTO = 101
ORDER BY tep.DATA_EVENTO DESC;  
''')


@st.cache_data
def DRE_AJUSTES_MANUAIS(ids_casa):
  return dataframe_query(f'''
    SELECT                        
      te.ID AS 'ID_Casa', 
      te.NOME_FANTASIA AS 'Casa',                  
      tam.MES_COMPETENCIA AS 'Mês',
      tam.ANO_COMPETENCIA AS 'Ano',
      tccg1.DESCRICAO AS 'Classificacao_Contabil_1',
      tccg2.DESCRICAO AS 'Classificacao_Contabil_2',                  
      tam.VALOR AS 'Valor Ajuste',
      tam.DESCRICAO AS 'Descrição Ajuste',
      CONCAT(tam.MES_COMPETENCIA, '/', tam.ANO_COMPETENCIA) AS Mes_Texto,
      tcc.DESCRICAO_CARGO_DRE AS 'Cargo_DRE'
    FROM T_AJUSTES_MANUAIS_DRE AS tam
    LEFT JOIN T_EMPRESAS AS te ON (tam.FK_EMPRESA = te.ID)   
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tam.FK_CLASSIFICACAO_CONTABIL_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tam.FK_CLASSIFICACAO_CONTABIL_2 = tccg2.ID)
    LEFT JOIN T_CADASTRO_DE_CARGOS tcc ON (tam.CARGO_DRE = tcc.ID)
    WHERE te.ID IN ({ids_casa}) AND tam.BIT_CANCELADO = 0 
    ORDER BY tam.MES_COMPETENCIA DESC, tam.ANO_COMPETENCIA DESC; 
  ''')


@st.cache_data
def DRE_CONSUMO_CARTAO_BLACK(ids_casa):
  return dataframe_query(f'''
    SELECT 
      tccb.CARTAO_FB AS 'CARTAO FB',
      tccb.NOME,
      tccb.CENTRO_CUSTO AS 'CENTRO DE CUSTO',                                                                                
      te.ID AS 'ID_Casa', 
      te.NOME_FANTASIA AS 'Casa',                  
      tccb.MES AS 'Mês',
      tccb.ANO AS 'Ano',
      tccb.VALOR AS 'Valor',
      CONCAT(tccb.MES, '/', tccb.ANO) AS Mes_Texto
    FROM T_CONSUMO_CARTAO_BLACK AS tccb
    LEFT JOIN T_EMPRESAS AS te ON (tccb.FK_EMPRESA = te.ID)
    WHERE tccb.FK_EMPRESA IN ({ids_casa})                   
    ORDER BY tccb.MES DESC, tccb.ANO DESC;  
  ''')