import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


@st.cache_data
def GET_CASAS():
    df_casas = dataframe_query('''
      WITH empresas_normalizadas AS (
        SELECT
          CASE 
            WHEN ID IN (161, 162, 179) THEN 149
            WHEN ID = 178 THEN 110
            WHEN ID = 177 THEN 176    
            WHEN ID = 175 THEN 114                                 
            ELSE ID
          END AS ID_Casa_Normalizada,
          NOME_FANTASIA,
          FK_GRUPO_EMPRESA,
          BIT_SOCIOS_EXTERNOS
        FROM T_EMPRESAS
      )
      SELECT
        te.ID_Casa_Normalizada AS ID_Casa,
        te2.NOME_FANTASIA AS Casa,
        te.BIT_SOCIOS_EXTERNOS as Bit_Socios_Externos
      FROM empresas_normalizadas te
      LEFT JOIN T_EMPRESAS te2 ON te.ID_Casa_Normalizada = te2.ID
      WHERE te.FK_GRUPO_EMPRESA = 100
      GROUP BY te.ID_Casa_Normalizada, te2.NOME_FANTASIA
      ORDER BY te2.NOME_FANTASIA
      ''')
    # df_casas_validas = pd.DataFrame(casas_validas, columns=['Casa']) 
    # df_casas_validas = df_casas.merge(df_casas_validas, on="Casa", how="inner")
    return df_casas


@st.cache_data
def GET_EXTRATO_ZIG():
    df_extrato_zig = dataframe_query('''
      WITH extrato_normalizado AS (
        SELECT
          ID AS ID_Extrato,
          CASE 
            WHEN ID_LOJA_ZIG IN ('95a1ebd7-3da4-4121-a4eb-f9add8caa749', '544ef5bf-18b2-4081-977c-7733f0d6a8b8', 'b8c72c1c-ebdb-4669-a716-db036ee48537') THEN 149 -- Priceless
            WHEN ID_LOJA_ZIG IN ('544bab29-b7f7-438a-8481-d6e2bc701a64') THEN '54135ce0-be40-4609-ba07-24f2fe42b2aa' -- The Cavern                         
            ELSE ID_LOJA_ZIG
          END AS ID_Loja_Normalizada,
          DESCRICAO,
          DATA_LIQUIDACAO,
          DATA_TRANSACAO,
          VALOR
        FROM T_EXTRATO_FINANCEIRO_ZIG
      )
      SELECT 
        en.ID_Extrato,
        te.ID AS ID_Casa,
        te.NOME_FANTASIA AS Casa,
        en.DESCRICAO AS Descricao,
        en.DATA_LIQUIDACAO AS Data_Liquidacao,
        en.DATA_TRANSACAO AS Data_Transacao,
        en.VALOR AS Valor
      FROM extrato_normalizado en
      INNER JOIN T_EMPRESAS te ON en.ID_Loja_Normalizada = te.ID_ZIGPAY
      ORDER BY te.NOME_FANTASIA ASC, en.DATA_LIQUIDACAO DESC
      ''')
    df_extrato_zig['Data_Liquidacao'] = pd.to_datetime(df_extrato_zig['Data_Liquidacao']) 
    df_extrato_zig['Data_Transacao'] = pd.to_datetime(df_extrato_zig['Data_Transacao']) 
    return df_extrato_zig
    

@st.cache_data
def GET_ZIG_FATURAMENTO():
    df_zig_faturamento = dataframe_query('''
      WITH faturamento_normalizado AS (
        SELECT
          CASE 
            WHEN FK_LOJA IN (161, 162, 179) THEN 149
            WHEN FK_LOJA = 178 THEN 110
            WHEN FK_LOJA = 177 THEN 176  
            WHEN FK_LOJA = 175 THEN 114                                                      
            ELSE FK_LOJA
          END AS ID_Casa,
          DATA,
          VALOR,
          TIPO_PAGAMENTO
        FROM T_ZIG_FATURAMENTO
        WHERE DATA >= '2024-06-01'
      )
      SELECT
        fn.ID_Casa,
        te.NOME_FANTASIA AS Casa,
        fn.DATA AS Data_Venda,
        fn.VALOR AS Valor,
        fn.TIPO_PAGAMENTO AS Tipo_Pagamento
      FROM faturamento_normalizado fn
      LEFT JOIN T_EMPRESAS te ON fn.ID_Casa = te.ID
      ORDER BY te.NOME_FANTASIA ASC, fn.DATA DESC 
      ''')
    df_zig_faturamento['Data_Venda'] = pd.to_datetime(df_zig_faturamento['Data_Venda']) 
    return df_zig_faturamento


@st.cache_data
def GET_PARCELAS_RECEIT_EXTR():
    df_parc_receit_extr = dataframe_query('''
      SELECT 
          vpa.ID AS 'ID_Receita',
          CASE
              WHEN te.ID IN (161, 162, 179) THEN 149 
              WHEN te.ID = 178 THEN 110
              WHEN te.ID = 177 THEN 176
              WHEN te.ID = 175 THEN 114                                                                                    
              ELSE te.ID
          END AS 'ID_Casa',
          CASE
              WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
              WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
              WHEN te.ID = 177 THEN 'The Cavern'
              WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                     
              ELSE te.NOME_FANTASIA
          END AS 'Casa',
          trec.NOME AS 'Cliente',
          tre.DATA_OCORRENCIA AS 'Data_Ocorrencia',
          vpa.DATA_VENCIMENTO AS 'Vencimento_Parcela',
          vpa.DATA_RECEBIMENTO AS 'Recebimento_Parcela',
          vpa.VALOR_PARCELA AS 'Valor_Parcela',
          tre.NUM_DOCUMENTACAO AS 'Doc_NF',
          trec2.CLASSIFICACAO AS 'Classif_Receita',
          tfdp.DESCRICAO AS 'Forma_Pagamento',
          tsp.DESCRICAO AS 'Status_Pgto',
          tcb.NOME_DA_CONTA AS 'Conta_Bancaria',
          tre.OBSERVACOES AS 'Observacoes'
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
      INNER JOIN T_EMPRESAS te ON vpa.FK_EMPRESA = te.ID
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS tre ON vpa.ID = tre.ID
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON vpa.FK_CLIENTE = trec.ID
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON tre.FK_CLASSIFICACAO = trec2.ID
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON tre.FK_FORMA_PAGAMENTO = tfdp.ID
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON vpa.STATUS_PGTO = tsp.ID
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON tre.FK_CONTA_BANCARIA = tcb.ID
      WHERE vpa.DATA_VENCIMENTO IS NOT NULL
      AND NOT (
        te.ID = 110 # Blue Note - São Paulo
        AND tsp.DESCRICAO = 'Desconto'
      )
      AND tsp.DESCRICAO NOT IN ('Permuta', 'Encontro de Contas')                                        
      ORDER BY te.NOME_FANTASIA ASC, vpa.DATA_RECEBIMENTO DESC
    ''')
    df_parc_receit_extr['Data_Ocorrencia'] = pd.to_datetime(df_parc_receit_extr['Data_Ocorrencia']) 
    df_parc_receit_extr['Vencimento_Parcela'] = pd.to_datetime(df_parc_receit_extr['Vencimento_Parcela'])
    df_parc_receit_extr['Recebimento_Parcela'] = pd.to_datetime(df_parc_receit_extr['Recebimento_Parcela'])
    return df_parc_receit_extr


@st.cache_data
def GET_CUSTOS_BLUEME_SEM_PARC():
    df_custos_blueme_sem_parcelam = dataframe_query('''
      SELECT 
      tdr.ID as 'ID_Despesa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 149 
        WHEN te.ID = 178 THEN 110
        WHEN te.ID = 177 THEN 176
        WHEN te.ID = 175 THEN 114                                                                                                                                     
        ELSE te.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless' 
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern' 
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                                                                           
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
      tf.CORPORATE_NAME as 'Fornecedor',
      tdr.VALOR_LIQUIDO as 'Valor',
      tdr.VENCIMENTO as 'Data_Vencimento',
      tc.`DATA` as 'Previsao_Pgto',
      tc2.`DATA` as 'Realizacao_Pgto',    
      tdr.COMPETENCIA as 'Data_Competencia',
      tdr.LANCAMENTO as 'Data_Lancamento',
      tfdp.DESCRICAO as 'Forma_Pagamento',
      tccg.DESCRICAO as 'Class_Cont_1',
      tccg2.DESCRICAO as 'Class_Cont_2',
      tdr.NF as 'Doc_NF',
      tscd.DESCRICAO as 'Status_Conf_Document',
      tsad.DESCRICAO as 'Status_Aprov_Diret',
      tsac.DESCRICAO as 'Status_Aprov_Caixa',
      CASE
        WHEN tsp.DESCRICAO IS NULL THEN "Pendente"
        ELSE tsp.DESCRICAO 
      END as 'Status_Pgto',
      tcb.ID as 'ID_Conta_Bancaria',
      tcb.NOME_DA_CONTA as 'Conta_Bancaria',
      tdr.FK_LOJA_CNPJ as 'CNPJ_Loja'
      FROM T_DESPESA_RAPIDA tdr
      INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tdr.FK_CONTA_BANCARIA = tcb.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON (tdr.FK_FORMA_PAGAMENTO = tfdp.ID)
      LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
      LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON (tdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID)
      LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
      LEFT JOIN T_STATUS_APROVACAO_CAIXA tsac ON (tdr.FK_APROVACAO_CAIXA = tsac.ID)
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
      LEFT JOIN T_CALENDARIO tc ON (tdr.PREVISAO_PAGAMENTO = tc.ID)	
      LEFT JOIN T_CALENDARIO tc2 ON (tdr.FK_DATA_REALIZACAO_PGTO = tc2.ID)
      LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
      WHERE 
          te.ID IS NOT NULL
          AND tdp.FK_DESPESA IS NULL
          AND tdr.BIT_CANCELADA = 0
          AND (tdr.FK_DESPESA_TEKNISA IS NULL OR tdr.BIT_DESPESA_TEKNISA_PENDENTE = 1)
          AND (tdr.FK_FORMA_PAGAMENTO != 109 OR tdr.FK_FORMA_PAGAMENTO IS NULL)
      ORDER BY 
          te.NOME_FANTASIA ASC, tc2.`DATA` DESC
      ''')
    df_custos_blueme_sem_parcelam['Data_Vencimento'] = pd.to_datetime(df_custos_blueme_sem_parcelam['Data_Vencimento'], errors='coerce') 
    df_custos_blueme_sem_parcelam['Previsao_Pgto'] = pd.to_datetime(df_custos_blueme_sem_parcelam['Previsao_Pgto'], errors='coerce') 
    df_custos_blueme_sem_parcelam['Realizacao_Pgto'] = pd.to_datetime(df_custos_blueme_sem_parcelam['Realizacao_Pgto'], errors='coerce') 
    df_custos_blueme_sem_parcelam['Data_Competencia'] = pd.to_datetime(df_custos_blueme_sem_parcelam['Data_Competencia'], errors='coerce') 
    df_custos_blueme_sem_parcelam['Data_Lancamento'] = pd.to_datetime(df_custos_blueme_sem_parcelam['Data_Lancamento'], errors='coerce') 
    return df_custos_blueme_sem_parcelam


@st.cache_data
def GET_CUSTOS_BLUEME_COM_PARC():
    df_custos_blueme_com_parcelam = dataframe_query('''
      SELECT
      tdp.ID as 'ID_Parcela',
      tdr.ID as 'ID_Despesa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 149 
        WHEN te.ID = 178 THEN 110
        WHEN te.ID = 177 THEN 176
        WHEN te.ID = 175 THEN 114                                                                                                                                      
        ELSE te.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern'
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                                          
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
      tdr.FK_LOJA_CNPJ as 'CNPJ_Loja',
      tf.CORPORATE_NAME as 'Fornecedor',
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
      tdp.VALOR as 'Valor_Parcela',
      tdp.`DATA` as 'Vencimento_Parcela',
      tc.`DATA` AS 'Previsao_Parcela',
      tc2.`DATA` AS 'Realiz_Parcela',
      tdr.VALOR_PAGAMENTO as 'Valor_Original',
      tdr.VALOR_LIQUIDO as 'Valor_Liquido',
      STR_TO_DATE(tdr.LANCAMENTO, '%Y-%m-%d') as 'Data_Lancamento',
      tfdp.DESCRICAO as 'Forma_Pagamento',
      tdr.NF as 'Doc_NF',
      tccg.DESCRICAO as 'Class_Cont_1',
      tccg2.DESCRICAO as 'Class_Cont_2',
      tscd.DESCRICAO as 'Status_Conf_Document',
      tsad.DESCRICAO as 'Status_Aprov_Diret',
      tsac.DESCRICAO as 'Status_Aprov_Caixa',
      CASE
          WHEN tdp.PARCELA_PAGA = 1 
              THEN 'Parcela_Paga'
          ELSE 'Parcela_Pendente'
      END as 'Status_Pgto',
      tcb.ID as 'ID_Conta_Bancaria',
      tcb.NOME_DA_CONTA as 'Conta_Bancaria'
    FROM 
      T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON (tdr.FK_FORMA_PAGAMENTO = tfdp.ID)
    LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON (tdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID)
    LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
    LEFT JOIN T_STATUS_APROVACAO_CAIXA tsac ON (tdr.FK_APROVACAO_CAIXA = tsac.ID)
    LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
    LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
    LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tdp.FK_CONTA_BANCARIA = tcb.ID)
    LEFT JOIN T_CALENDARIO tc ON (tdp.FK_PREVISAO_PGTO = tc.ID)
    LEFT JOIN T_CALENDARIO tc2 ON (tdp.FK_DATA_REALIZACAO_PGTO = tc2.ID)
    WHERE 
      tdp.FK_DESPESA IS NOT NULL
      AND tdr.BIT_CANCELADA = 0
      AND (tdr.FK_DESPESA_TEKNISA IS NULL OR tdr.BIT_DESPESA_TEKNISA_PENDENTE = 1)
    ORDER BY 
      te.NOME_FANTASIA ASC, tc2.`DATA` DESC
    ''')
    df_custos_blueme_com_parcelam['Vencimento_Parcela'] = pd.to_datetime(df_custos_blueme_com_parcelam['Vencimento_Parcela'], errors='coerce') 
    df_custos_blueme_com_parcelam['Previsao_Parcela'] = pd.to_datetime(df_custos_blueme_com_parcelam['Previsao_Parcela'], errors='coerce') 
    df_custos_blueme_com_parcelam['Realiz_Parcela'] = pd.to_datetime(df_custos_blueme_com_parcelam['Realiz_Parcela'], errors='coerce') 
    df_custos_blueme_com_parcelam['Data_Lancamento'] = pd.to_datetime(df_custos_blueme_com_parcelam['Data_Lancamento'], errors='coerce') 

    return df_custos_blueme_com_parcelam


@st.cache_data
def GET_EXTRATOS_BANCARIOS():
  df_extratos_bancarios = dataframe_query(''' 
    SELECT
    teb.ID as 'ID_Extrato_Bancario',
    tcb.ID as 'ID_Conta_Bancaria',
    tcb.NOME_DA_CONTA as 'Nome_Conta_Bancaria',
    CASE
        WHEN te.ID IN (161, 162, 179) THEN 149 
        WHEN te.ID = 178 THEN 110
        WHEN te.ID = 177 THEN 176 
        WHEN te.ID = 175 THEN 114                                                                                                       
        ELSE te.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless' 
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern'
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                            
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
    teb.DATA_TRANSACAO as 'Data_Transacao',
    CASE 
        WHEN teb.FK_TIPO_CREDITO_DEBITO = 100 THEN 'CREDITO'
        ELSE 'DEBITO'
    END as 'Tipo_Credito_Debito',
    teb.DESCRICAO_TRANSACAO as 'Descricao_Transacao',
    teb.VALOR as 'Valor'
    FROM T_EXTRATOS_BANCARIOS teb
    INNER JOIN T_CONTAS_BANCARIAS tcb ON (teb.FK_CONTA_BANCARIA = tcb.ID)
    INNER JOIN T_EMPRESAS te ON (tcb.FK_LOJA = te.ID)
    WHERE teb.DESCRICAO_TRANSACAO NOT LIKE '%RESG AUTOMATICO%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%APLICACAO AUTOMATICA%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%APLIC.AUTOM.INVESTFACIL*%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%RESG.AUTOM.INVEST FACIL*%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%RESGATE INVEST FACIL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%APLICACAO CONTAMAX%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%Pix Enviado-Conta Transacional%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%RESGATE CONTAMAX AUTOMATICO%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%APLIC.INVEST FACIL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%RENTAB.INVEST FACILCRED*%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%BB RENDE FACIL - RENDE FACIL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%BB RENDE FCIL - RENDE FACIL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%BB RENDE FCIL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%SALDO TOTAL%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%0000     00000 BB Rende Fácil%'
    AND teb.DESCRICAO_TRANSACAO NOT LIKE '%0000 00000 BB Rende Fácil Rende Facil%'                                      
    ORDER BY te.NOME_FANTASIA ASC, teb.DATA_TRANSACAO DESC
    ''')
  df_extratos_bancarios['Data_Transacao'] = pd.to_datetime(df_extratos_bancarios['Data_Transacao'], errors='coerce')
  return df_extratos_bancarios


@st.cache_data
def GET_MUTUOS():
    df_mutuos = dataframe_query('''
      SELECT
      tm.ID as 'Mutuo_ID',
      tm.`DATA` as 'Data_Mutuo',
      CASE 
        WHEN te.ID = 175 THEN 114
        ELSE te.ID                                                    
      END AS 'ID_Casa_Saida',
      CASE
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'
        ELSE te.NOME_FANTASIA                                                                        
      END AS 'Casa_Saida',
      tcb_s.ID AS 'ID_Conta_Saida',
      tcb_s.NOME_DA_CONTA AS 'Conta_Saida',
      CASE 
        WHEN te2.ID = 175 THEN 114
        ELSE te2.ID                                                    
      END AS 'ID_Casa_Entrada',
      CASE
        WHEN te2.ID = 175 THEN 'Bar Brahma - Centro'
        ELSE te2.NOME_FANTASIA                                                                        
      END AS 'Casa_Entrada',
      tcb_e.ID AS 'ID_Conta_Entrada',
      tcb_e.NOME_DA_CONTA AS 'Conta_Entrada',
      tm.VALOR as 'Valor',
      tm.TAG_FATURAM_ZIG as 'Tag_Faturam_Zig',
      tm.OBSERVACOES as 'Observacoes'
      FROM T_MUTUOS tm 
      LEFT JOIN T_EMPRESAS te ON (tm.FK_LOJA_SAIDA = te.ID)
      LEFT JOIN T_EMPRESAS te2 ON (tm.FK_LOJA_ENTRADA = te2.ID)
      LEFT JOIN T_CONTAS_BANCARIAS AS tcb_s ON (tm.FK_CONTA_BANCARIA_SAIDA = tcb_s.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb_e ON (tm.FK_CONTA_BANCARIA_ENTRADA = tcb_e.ID)
      ORDER BY te.NOME_FANTASIA ASC, tm.`DATA` DESC
      ''')
    df_mutuos['Data_Mutuo'] = pd.to_datetime(df_mutuos['Data_Mutuo'], errors='coerce') 
    return df_mutuos


@st.cache_data
def GET_TESOURARIA():
    df_tesouraria = dataframe_query('''
    SELECT 
    ttt.ID as 'ID_Transacao_Tesouraria',
    CASE
        WHEN te2.ID IN (161, 162, 179) THEN 149 
        WHEN te2.ID = 178 THEN 110
        WHEN te2.ID = 177 THEN 176
        WHEN te2.ID = 175 THEN 114                                                                                                                                                                                
        ELSE te2.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te2.ID IN (161, 162, 179) THEN 'Priceless' 
        WHEN te2.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te2.ID = 177 THEN 'The Cavern'
        WHEN te2.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                            
        ELSE te2.NOME_FANTASIA                                                                 
      END AS 'Casa',
    ttt.FK_EMPRESA_TESOURARIA as 'ID_Empresa_Tesouraria',
    te.NOME_FANTASIA as 'Empresa_Tesouraria',
    ttt.DATA_TRANSACAO as 'Data_Transacao',
    ttt.VALOR as 'Valor',
    ttt.DESCRICAO as 'Descricao'
    FROM T_TESOURARIA_TRANSACOES ttt 
    LEFT JOIN T_EMPRESAS te ON (ttt.FK_EMPRESA_TESOURARIA = te.ID)
    LEFT JOIN T_EMPRESAS te2 ON (ttt.FK_LOJA = te2.ID)
    ORDER BY te2.NOME_FANTASIA ASC, ttt.ID DESC, ttt.DATA_TRANSACAO DESC
    ''')
    df_tesouraria['Data_Transacao'] = pd.to_datetime(df_tesouraria['Data_Transacao'], errors='coerce') 
    return df_tesouraria


@st.cache_data
def GET_AJUSTES():
    df_ajustes_conciliacao = dataframe_query('''
      SELECT 
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 149 
        WHEN te.ID = 178 THEN 110
        WHEN te.ID = 177 THEN 176
        WHEN te.ID = 175 THEN 114                                                                                                                                                                                                                      
        ELSE te.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern'
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                                                        
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
      tac.DATA_AJUSTE AS 'Data_Ajuste',
      tac.VALOR AS 'Valor',
      tcac.DESCRICAO AS 'Categoria',
      tac.DESCRICAO AS 'Descrição'
      FROM T_AJUSTES_CONCILIACAO tac
      INNER JOIN T_EMPRESAS te ON (tac.FK_EMPRESA = te.ID)
      LEFT JOIN T_CATEGORIA_AJUSTES_CONCILIACAO tcac ON (tac.FK_CATEGORIA_AJUSTE = tcac.ID)
      ORDER BY te.NOME_FANTASIA ASC, tac.DATA_AJUSTE DESC
      ''')
    df_ajustes_conciliacao['Data_Ajuste'] = pd.to_datetime(df_ajustes_conciliacao['Data_Ajuste'], errors='coerce') 
    return df_ajustes_conciliacao


@st.cache_data
def GET_BLOQUEIOS_JUDICIAIS():
    df_bloqueios_judiciais = dataframe_query('''
      SELECT
      tbj.ID as 'ID_Bloqueio',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 149 
        WHEN te.ID = 178 THEN 110
        WHEN te.ID = 177 THEN 176
        WHEN te.ID = 175 THEN 114                                                                                                                                                                                                                       
        ELSE te.ID                                                                 
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless' 
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern'
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                                                 
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
      tbj.DATA_TRANSACAO as 'Data_Transacao',
      tcb.ID as 'ID_Conta_Bancaria',
      tcb.NOME_DA_CONTA as 'Nome da Conta',
      tbj.VALOR as 'Valor',
      tbj.OBSERVACAO as 'Observacao'
      FROM T_BLOQUEIOS_JUDICIAIS tbj 
      LEFT JOIN T_EMPRESAS te ON (tbj.FK_EMPRESA = te.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tcb.ID = tbj.FK_CONTA_BANCARIA)
      ORDER BY te.NOME_FANTASIA ASC, tbj.DATA_TRANSACAO DESC
      ''')
    df_bloqueios_judiciais['Data_Transacao'] = pd.to_datetime(df_bloqueios_judiciais['Data_Transacao'], errors='coerce') 
    return df_bloqueios_judiciais


@st.cache_data
def GET_TIPO_CLASS_CONT_2():
    df_tipo_class_cont_2 = dataframe_query('''
    SELECT
    tccg2.ID as 'ID_Class_Cont_2',
    tccg2.DESCRICAO as 'Class_Cont_2',
    tccg.ID as 'ID_Class_Cont_1',
    tccg.DESCRICAO as 'Class_Cont_1',
    ttcdff.DESCRICAO as 'Tipo_Fluxo_Futuro'
    FROM T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tccg2.FK_GRUPO_1 = tccg.ID)
    LEFT JOIN T_TIPO_CLASSIF_DESPESA_FLUXO_FUTURO ttcdff ON (tccg2.FK_TIPO_FLUXO_FUTURO = ttcdff.ID)
    WHERE ttcdff.DESCRICAO IS NOT NULL
    ''')
    return df_tipo_class_cont_2


@st.cache_data
def GET_ORCAMENTOS():
    df_orcamentos = dataframe_query('''
      WITH T_ORCAMENTOS_ATUAL AS (
          SELECT t.*,
              ROW_NUMBER() OVER (
                  PARTITION BY t.FK_EMPRESA, t.FK_CLASSIFICACAO_1, t.FK_CLASSIFICACAO_2, t.MES, t.ANO
                  ORDER BY t.TAG_REVISAO DESC
              ) AS rn
          FROM T_ORCAMENTOS t
      )
      SELECT
      to2.ID as 'ID_Orcamento',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 149
        ELSE te.ID
      END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
        ELSE te.NOME_FANTASIA
      END AS 'Casa',
      tccg.ID as 'ID_Class_Cont_1',
      tccg.DESCRICAO as 'Class_Cont_1',
      tccg2.ID as 'ID_Class_Cont_2',
      tccg2.DESCRICAO as 'Class_Cont_2',
      to2.ANO as 'Ano_Orcamento',
      to2.MES as 'Mes_Orcamento',
      to2.VALOR as 'Valor_Orcamento',
      ttcdff.DESCRICAO as 'Tipo_Fluxo_Futuro'
      FROM T_ORCAMENTOS_ATUAL to2
      LEFT JOIN T_EMPRESAS te ON (to2.FK_EMPRESA = te.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (to2.FK_CLASSIFICACAO_1 = tccg.ID)
      LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (to2.FK_CLASSIFICACAO_2 = tccg2.ID)
      LEFT JOIN T_TIPO_CLASSIF_DESPESA_FLUXO_FUTURO ttcdff ON (tccg2.FK_TIPO_FLUXO_FUTURO = ttcdff.ID)
      WHERE to2.ANO >= 2025 AND to2.rn = 1
      ORDER BY te.NOME_FANTASIA, to2.ANO, to2.MES, tccg.DESCRICAO, tccg2.DESCRICAO
      ''')
    return df_orcamentos


@st.cache_data
def GET_FATURAMENTO_AGREGADO():
    df_faturamento_agregado = dataframe_query('''
    # Faturamento Agregado
      SELECT 
        CASE
          WHEN te.ID IN (161, 162, 179) THEN 149 -- Priceless
              WHEN te.ID = 131 THEN 110 -- Blue Note
              WHEN te.ID = 177 THEN 176 -- The Cavern
              WHEN te.ID = 175 THEN 114 -- Brahminha                                                                                                                                                                         
              ELSE tivd.FK_CASA
            END AS 'ID_Casa',
          CASE
              WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
              WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
              WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern' 
              WHEN te.NOME_FANTASIA = 'Brahminha' THEN 'Bar Brahma - Centro'                                                                         
              ELSE te.NOME_FANTASIA
          END AS 'Casa',
      tivc2.DESCRICAO AS 'Categoria',
      YEAR(tivd.EVENT_DATE) AS 'Ano',
      MONTH(tivd.EVENT_DATE) AS 'Mes',
      SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Valor_Bruto',
      SUM(tivd.DESCONTO) AS 'Desconto',
      SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Valor_Liquido'
      FROM T_ITENS_VENDIDOS_DIA AS tivd
      LEFT JOIN T_EMPRESAS AS te ON (tivd.FK_CASA = te.ID)
      LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON (tivc.ID_ZIGPAY = tivd.PRODUCT_ID)
      LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON (tivc2.ID = tivc.FK_CATEGORIA)
      LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
      GROUP BY te.ID, tivc2.DESCRICAO, YEAR(tivd.EVENT_DATE), MONTH(tivd.EVENT_DATE)
              
      UNION ALL

      # Receitas Extraordinárias
      SELECT 
      # trec2.ID as ID_Faturam_Agregado,
      te.ID as ID_Casa,
      te.NOME_FANTASIA as Casa,
      trec2.CLASSIFICACAO as Categoria,
      YEAR(vpa.DATA_RECEBIMENTO) as Ano,
      MONTH(vpa.DATA_RECEBIMENTO) as Mes,
      SUM(vpa.VALOR_PARCELA) as Valor_Bruto,
      0 as Desconto,
      SUM(vpa.VALOR_PARCELA) as Valor_Liquido
      FROM View_Parcelas_Agrupadas vpa
      INNER JOIN T_EMPRESAS te ON (vpa.FK_EMPRESA = te.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS tre ON (vpa.ID = tre.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (vpa.FK_CLIENTE = trec.ID)
      LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON (tre.FK_CLASSIFICACAO = trec2.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON (tre.FK_FORMA_PAGAMENTO = tfdp.ID)
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tre.FK_STATUS_PGTO = tsp.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tre.FK_CONTA_BANCARIA = tcb.ID)
      WHERE vpa.DATA_RECEBIMENTO IS NOT NULL
      AND vpa.DATA_RECEBIMENTO >= '2025-01-01'
      AND trec2.ID IN (131,142,124,135,111,153,104,106,116,114,110,137)  # Bilheteria, Bilheteria-Rebate, Coleta de Oleo, Delivery, Eventos, Eventos de Marketing, Lojinha, Plataforma Ifood, Plataforma Rappi, Plataforma Total Acesso, Repasses FabLab, Voucher  
      GROUP BY te.ID, trec2.ID, YEAR(vpa.DATA_RECEBIMENTO), MONTH(vpa.DATA_RECEBIMENTO)          
      ''')
    return df_faturamento_agregado


@st.cache_data
def GET_EVENTOS_FATURAM_AGREGADO():
    df_eventos_faturam_agregado = dataframe_query('''
      SELECT 
        tep.ID AS ID_Faturam_Agregado,
        CASE
          WHEN te.ID IN (161, 162, 179) THEN 149 
          WHEN te.ID = 178 THEN 110
          WHEN te.ID = 177 THEN 176
          WHEN te.ID = 175 THEN 114                                                                                                                                                                                                                               
          ELSE te.ID                                                                 
        END AS 'ID_Casa',
      CASE
        WHEN te.ID IN (161, 162, 179) THEN 'Priceless' 
        WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
        WHEN te.ID = 177 THEN 'The Cavern'
        WHEN te.ID = 175 THEN 'Bar Brahma - Centro'      
        ELSE te.NOME_FANTASIA                                                                 
      END AS 'Casa',
        YEAR(tpep.DATA_RECEBIMENTO_PARCELA) as Ano,
        MONTH(tpep.DATA_RECEBIMENTO_PARCELA) as Mes,
        SUM(tpep.VALOR_PARCELA) as Valor_Bruto,
        0 as Desconto,
        SUM(tpep.VALOR_PARCELA) as Valor_Liquido                          
      FROM T_EVENTOS_PRICELESS tep
      LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
      LEFT JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON (tep.ID = tpep.FK_EVENTO_PRICELESS)
      WHERE tpep.DATA_VENCIMENTO_PARCELA IS NOT NULL AND tpep.DATA_RECEBIMENTO_PARCELA >= '2025-09-01 00:00:00'
      GROUP BY te.ID, YEAR(tpep.DATA_RECEBIMENTO_PARCELA), MONTH(tpep.DATA_RECEBIMENTO_PARCELA)  
      ''')
    df_eventos_faturam_agregado['Categoria'] = 'Eventos'
    df_eventos_faturam_agregado = df_eventos_faturam_agregado[['ID_Faturam_Agregado', 'ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mes', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    return df_eventos_faturam_agregado


@st.cache_data
def GET_EVENTOS():
    df_eventos = dataframe_query('''
      SELECT tep.ID AS 'ID_Evento',
          tep.NOME_EVENTO AS 'Nome_Evento',
          CASE
            WHEN te.ID IN (161, 162, 179) THEN 149
            WHEN te.ID = 178 THEN 110                      
            WHEN te.ID = 177 THEN 176
            WHEN te.ID = 175 THEN 114                                                                                                                            
            ELSE te.ID                                                                 
          END AS 'ID_Casa',
          CASE
            WHEN te.ID IN (161, 162, 179) THEN 'Priceless'
            WHEN te.ID = 178 THEN 'Blue Note - São Paulo'
            WHEN te.ID = 177 THEN 'The Cavern'
            WHEN te.ID = 175 THEN 'Bar Brahma - Centro'                                                                                   
            ELSE te.NOME_FANTASIA                                                                 
          END AS 'Casa',
          tpep.ID AS 'ID_Parcela',
          tpep.VALOR_PARCELA AS 'Valor_Parcela',
          tpep.DATA_VENCIMENTO_PARCELA AS 'Vencimento_Parcela',
          tpep.DATA_RECEBIMENTO_PARCELA AS 'Recebimento_Parcela',
          tsp.DESCRICAO AS 'Status_Pgto',
          tfp.DESCRICAO AS 'Forma_Pgto',
          tcb.ID as 'ID_Conta_Bancaria',
          tcb.NOME_DA_CONTA AS 'Conta_Bancaria',
          tep.OBSERVACOES AS 'Observacoes'
      FROM T_EVENTOS_PRICELESS tep
      LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
      LEFT JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON (tep.ID = tpep.FK_EVENTO_PRICELESS)
      LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
      LEFT JOIN T_FORMAS_DE_PAGAMENTO tfp ON (tpep. FK_FORMA_PAGAMENTO = tfp.ID)
      LEFT JOIN T_CONTAS_BANCARIAS tcb ON (tpep.FK_CONTA_BANCARIA = tcb.ID)
      WHERE tpep.DATA_VENCIMENTO_PARCELA IS NOT NULL 
      AND tpep.DATA_RECEBIMENTO_PARCELA >= '2025-09-01 00:00:00'
      AND tep.FK_STATUS_EVENTO <> 102                           
      AND tsp.DESCRICAO NOT IN ('Desconto', 'Permuta')                         
      ORDER BY te.NOME_FANTASIA ASC, tpep.DATA_RECEBIMENTO_PARCELA DESC
      ''')
    return df_eventos
    

@st.cache_data
def GET_CONTAS_BANCARIAS():
    df_contas_bancarias = dataframe_query('''
      SELECT tcb.ID AS 'ID_Conta',
      tcb.NOME_DA_CONTA AS 'Nome da Conta',
      te.ID AS 'ID_Casa',
      te.NOME_FANTASIA AS 'Casa',
      tb.NAME AS 'Nome do Banco'

      FROM T_CONTAS_BANCARIAS tcb
      LEFT JOIN T_EMPRESAS te ON (tcb.FK_LOJA = te.ID)
      LEFT JOIN T_BANCOS tb ON (tcb.FK_BANCO = tb.ID)
      ''')
    return df_contas_bancarias