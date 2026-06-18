import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


# Garante que as casas estão corretamente formatadas no SQL
# casas_validas = [c for c in casas_validas if c != 'All bar']
casas_str = "', '".join(casas_validas)  # vira: "Bar Brahma - Centro', 'Orfeu"
casas_str = f"'{casas_str}'"  # adiciona aspas ao redor da lista toda


# Faturamento da Zig por dia da semana: considerar casas de Delivery separadamente
@st.cache_data
def GET_ITENS_VENDIDOS_DIA_DA_SEMANA():
    df_itens_vendidos_dia_da_semana = dataframe_query(f'''
    SELECT 
      CASE
        WHEN tivd.FK_CASA = 117 THEN 118 -- Delivery BBC
        WHEN te.ID IN (161, 162) THEN 149 -- Priceless
        WHEN te.ID = 131 THEN 110 -- Blue Note
        WHEN te.ID = 177 THEN 176 -- The Cavern                                    
        ELSE tivd.FK_CASA
      END AS 'ID_Casa',
      CASE
        WHEN te.NOME_FANTASIA = 'Hotel Maraba' THEN 'Delivery Brahma Centro'
        WHEN te.NOME_FANTASIA IN ('Terraço Notie', 'Notiê - Priceless') THEN 'Priceless'
        WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
        WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern'                                    
        ELSE te.NOME_FANTASIA
      END AS 'Casa',
          tivc2.DESCRICAO AS Categoria,
          DATE(tivd.EVENT_DATE) AS 'Data Evento',
          SUM(tivd.DESCONTO) AS 'Desconto',
          SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Valor Bruto',
          SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Valor Liquido'
        FROM T_ITENS_VENDIDOS_DIA tivd
        LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA 
        LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
        GROUP BY te.ID, tivc2.DESCRICAO, DATE(tivd.EVENT_DATE)
		ORDER BY tivd.EVENT_DATE DESC;                                                                     
    '''
    )
    # Agrupa por casa e data
    df_itens_vendidos_dia_da_semana = df_itens_vendidos_dia_da_semana.groupby(['ID_Casa', 'Casa', 'Categoria', 'Data Evento'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()
    return df_itens_vendidos_dia_da_semana


@st.cache_data
def GET_ITENS_VENDIDOS_DIA():
    df_itens_vendidos_dia = dataframe_query(f'''
    SELECT 
      CASE
        WHEN tivd.FK_CASA = 118 THEN 114
        WHEN tivd.FK_CASA = 103 THEN 116
        WHEN tivd.FK_CASA = 169 THEN 148
        WHEN tivd.FK_CASA = 139 THEN 105
        WHEN tivd.FK_CASA = 112 THEN 104
        WHEN te.ID IN (161, 162) THEN 149 -- Priceless
        WHEN te.ID = 131 THEN 110 -- Blue Note
        WHEN te.ID = 177 THEN 176 -- The Cavern                                    
        ELSE tivd.FK_CASA
      END AS 'ID_Casa',
      CASE
        WHEN tivd.FK_CASA = 118 THEN 'Bar Brahma - Centro'
        WHEN tivd.FK_CASA = 103 THEN 'Bar Léo - Centro'
        WHEN tivd.FK_CASA = 169 THEN 'Bar Brahma - Granja'
        WHEN tivd.FK_CASA = 139 THEN 'Jacaré'
        WHEN tivd.FK_CASA = 112 THEN 'Orfeu'
        WHEN te.NOME_FANTASIA IN ('Terraço Notie', 'Notiê - Priceless') THEN 'Priceless'
        WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
        WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern'                                    
        ELSE te.NOME_FANTASIA
      END AS 'Casa',
      CASE
      	WHEN te.ID IN (103, 112, 118, 139, 169) THEN 'Delivery'
        ELSE tivc2.DESCRICAO 
      END AS Categoria,
          DATE(tivd.EVENT_DATE) AS 'Data Evento',
          SUM(tivd.DESCONTO) AS 'Desconto',
          SUM(COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0)) AS 'Valor Bruto',
          SUM(COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0)) AS 'Valor Liquido'
        FROM T_ITENS_VENDIDOS_DIA tivd
        LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA 
        LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
        GROUP BY te.ID, tivc2.DESCRICAO, DATE(tivd.EVENT_DATE)
		ORDER BY tivd.EVENT_DATE DESC;                                                                     
    '''
    )
    # Agrupa por casa e data
    df_itens_vendidos_dia = df_itens_vendidos_dia.groupby(['ID_Casa', 'Casa', 'Categoria', 'Data Evento'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()
    return df_itens_vendidos_dia


# Faturamento de Eventos: Eventos A&B, Locações, Couvert
@st.cache_data
def GET_FATURAMENTO_EVENTOS():
    df_faturamento_eventos = dataframe_query(f'''
    SELECT
        te.ID AS 'ID_Casa',
        tep.ID AS 'ID_Evento',                                     
        te.NOME_FANTASIA AS 'Casa',
        tep.DATA_EVENTO AS 'Data Evento',
        tme.DESCRICAO as 'Modelo_Evento',
        SUM(
            ROUND(COALESCE(tep.VALOR_AB, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO), 2)
            +
            ROUND(COALESCE(tep.VALOR_TAXA_SERVICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO), 2)
        ) AS 'Eventos A&B',
        SUM(
            ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
        ) AS 'Eventos Couvert',
        SUM(
            ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_ESPACO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_GERADOR, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_LOCACAO_UTENSILIOS, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_COMISSAO_BV, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_EXTRAS_GERAIS, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2)
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_IMPOSTO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
            +
            ROUND(COALESCE((COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO, 0) * (tpep.VALOR_PARCELA / tep.VALOR_TOTAL_EVENTO)), 0), 2) 
        ) AS 'Eventos Locações',
        MONTH(tep.DATA_EVENTO) AS 'Mês',
        YEAR(tep.DATA_EVENTO) AS 'Ano'                                                                         
    FROM T_PARCELAS_EVENTOS_PRICELESS tpep
    LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
    LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
    LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
    WHERE tep.FK_STATUS_EVENTO = 101
    GROUP BY
        te.ID,
        te.NOME_FANTASIA,
        tep.ID,                                      
        tep.DATA_EVENTO    
    ORDER BY tep.DATA_EVENTO                                                                       
    '''
    )

    # Mantém essas colunas
    id_vars = ['ID_Casa', 'Casa', 'Data Evento']

    # Essas viram categoria
    value_vars = ['Eventos A&B', 'Eventos Couvert', 'Eventos Locações']

    df_eventos_melt = df_faturamento_eventos.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Categoria',
        value_name='Valor Bruto'
    )

    # remove zero e null
    df_eventos_melt = df_eventos_melt[
        df_eventos_melt['Valor Bruto'].notna() &
        (df_eventos_melt['Valor Bruto'] != 0)
    ]

    # cria colunas finais
    df_eventos_melt['Desconto'] = 0
    df_eventos_melt['Valor Liquido'] = df_eventos_melt['Valor Bruto']

    df_eventos_tratado = df_eventos_melt[
        ['ID_Casa', 'Casa', 'Categoria', 'Data Evento', 'Valor Bruto', 'Desconto', 'Valor Liquido']
    ]
    df_eventos_tratado = df_eventos_tratado.groupby(['ID_Casa', 'Casa', 'Categoria', 'Data Evento'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()

    return df_faturamento_eventos, df_eventos_tratado


# Faturamento de Eventos - PRICELESS: Eventos A&B, Locações, Couvert
@st.cache_data
def GET_FATURAMENTO_EVENTOS_PRICELESS():
    df_faturamento_eventos_priceless = dataframe_query(f'''
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
        te.ID AS 'ID_Casa', 
        tep.ID AS 'ID_Evento',                                                                                             
        te.NOME_FANTASIA AS 'Casa',
        tep.DATA_EVENTO AS 'Data Evento',
        tme.DESCRICAO as 'Modelo_Evento',                                               
        SUM(
           (CASE 
	           WHEN tcep.DESCRICAO='A&B' THEN ROUND(COALESCE(tep.VALOR_AB,0) * COALESCE(tpep.VALOR_PARCELA / NULLIF(tep.VALOR_AB,0),0),2) 
	           ELSE 0 
	        END)
           +
           (CASE 
	           WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_SERVICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) 
	           ELSE 0 
	        END)                                       
        ) AS 'Eventos A&B',
        SUM(
           (CASE 
           	   WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) 
               ELSE 0 
            END)
           +
           (CASE 
	           WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) 
	           ELSE 0 
	        END)
           +
           (CASE 
	           WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) 
	           ELSE 0 
	        END)                                         
        ) AS 'Eventos Couvert',
        SUM(
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_GERADOR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_UTENSILIOS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_COMISSAO_BV,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_EXTRAS_GERAIS,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_IMPOSTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Outros' THEN ROUND(COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Outros_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_1,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_2,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_AROO_3,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_ANEXO,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_NOTIE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_MIRANTE,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)
           +
           (CASE WHEN tcep.DESCRICAO='Locação' THEN ROUND(COALESCE(tep.VALOR_LOCACAO_BAR,0) * (tpep.VALOR_PARCELA / NULLIF(t.Valor_Locacao_Total,0)),2) ELSE 0 END)                                        
        ) AS 'Eventos Locações',
        MONTH(tep.DATA_EVENTO) AS 'Mês',
        YEAR(tep.DATA_EVENTO) AS 'Ano'                                                                                                                                                                                      
        FROM T_PARCELAS_EVENTOS_PRICELESS tpep
        JOIN T_EVENTOS_PRICELESS tep ON tpep.FK_EVENTO_PRICELESS = tep.ID
        LEFT JOIN TOTALS t ON t.ID = tep.ID
        LEFT JOIN T_EMPRESAS te ON tep.FK_EMPRESA = te.ID
        LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)                                               
        LEFT JOIN T_STATUS_PAGAMENTO tsp ON tpep.FK_STATUS_PAGAMENTO = tsp.ID
        LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON tpep.FK_CATEGORIA_PARCELA = tcep.ID
        WHERE te.ID = 149
        AND tep.FK_STATUS_EVENTO = 101
        GROUP BY
	        te.ID,
	        te.NOME_FANTASIA,
	        tep.ID,                                      
	        tep.DATA_EVENTO   
        ORDER BY tep.DATA_EVENTO DESC;                                            
    ''') 

    # Mantém essas colunas
    id_vars = ['ID_Casa', 'Casa', 'Data Evento']

    # Essas viram categoria
    value_vars = ['Eventos A&B', 'Eventos Couvert', 'Eventos Locações']

    df_eventos_melt = df_faturamento_eventos_priceless.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Categoria',
        value_name='Valor Bruto'
    )

    # remove zero e null
    df_eventos_melt = df_eventos_melt[
        df_eventos_melt['Valor Bruto'].notna() &
        (df_eventos_melt['Valor Bruto'] != 0)
    ]

    # cria colunas finais
    df_eventos_melt['Desconto'] = 0
    df_eventos_melt['Valor Liquido'] = df_eventos_melt['Valor Bruto']

    df_eventos_tratado_priceless = df_eventos_melt[
        ['ID_Casa', 'Casa', 'Categoria', 'Data Evento', 'Valor Bruto', 'Desconto', 'Valor Liquido']
    ]
    df_eventos_tratado_priceless = df_eventos_tratado_priceless.groupby(['ID_Casa', 'Casa', 'Categoria', 'Data Evento'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()

    return df_faturamento_eventos_priceless, df_eventos_tratado_priceless                                          


# Faturamento de Eventos - PRICELESS: Eventos A&B, Locações, Couvert
@st.cache_data
def GET_EVENTOS_REBATE_FORNEC_PRICELESS():
    return dataframe_query(f'''
        SELECT 
          vpa.ID AS 'ID_receita', 
          CASE
              WHEN te.ID IN (161, 162) THEN 'Priceless'
              WHEN te.ID IN (131, 178) THEN 'Blue Note - São Paulo'                                                             
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
      AND te.ID IN (149, 161, 162)
      AND trec2.ID IN (111,124,130,109,104) # Eventos / Coleta de Oleo / Patrocínios / Visibilidade nos Bares (mkt)
	  AND (STR_TO_DATE(tre.DATA_OCORRENCIA, '%Y-%m-%d') >= '2025-12-01 00:00:00' OR STR_TO_DATE(vpa.DATA_RECEBIMENTO, '%Y-%m-%d') >= '2025-12-01 00:00:00')
	  ORDER BY tre.ID desc;                                         
    ''') 


# Receitas Extraordinárias: Patrocínio, Eventos Rebate Fornecedores (Priceless), Bilheteria, Bilheteria-Rebate, Cashback, Membership, Premium Corp, Patrocínio (Blue Note) 
@st.cache_data
def GET_DEMAIS_RECEITAS_EXTR():
    return dataframe_query(f'''
        SELECT 
          vpa.ID AS 'ID_receita',                  
          CASE
              WHEN te.ID IN (161, 162) THEN 'Priceless'
              WHEN te.ID IN (131, 178) THEN 'Blue Note - São Paulo'                                                             
              ELSE te.NOME_FANTASIA
          END AS 'Casa', 
          trec.NOME AS 'Cliente', 
          trec2.CLASSIFICACAO AS 'Classificacao', 
          tre.VALOR as 'Valor_Total', 
          tre.DATA_OCORRENCIA AS 'Data_Ocorrencia',
          vpa.DATA_RECEBIMENTO AS 'Recebimento_Parcela',
          vpa.VALOR_PARCELA AS 'Valor Bruto',
          tsp.DESCRICAO as 'Status_Pgto',
		  tre.VALOR_CATEGORIA_PATROCINIO as 'Categ_Patroc',
		  tre.VALOR_CATEGORIA_TAXA_SERVICO as 'Categ_Taxa_Serv'
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
      AND trec2.ID IN (111, 130, 131, 133, 142, 144, 152) # Eventos, Patrocínios, Bilheteria, Premium Corp, Bilheteria-Rebate, Cashback, Membership
	  ORDER BY tre.ID desc;
    ''')
    

# Receitas Extraordinárias: (Lojin/Gifts e Coleta de Óleo/Outras Receitas)
@st.cache_data
def GET_PARCELAS_RECEIT_EXTR():
    df_parc_receit_extr = dataframe_query(f'''
    SELECT 
        CASE
            WHEN te.ID = 131 THEN 110
            WHEN te.ID = 177 THEN 176                              
            ELSE te.ID    
        END AS 'ID_Casa',                                                                                                                      
        CASE
            WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
            WHEN te.NOME_FANTASIA = 'The Cavern - Almoço' THEN 'The Cavern'                              
            ELSE te.NOME_FANTASIA    
        END AS 'Casa',  
        tre.DATA_OCORRENCIA as 'Data Ocorrencia',
        vpa.VALOR_PARCELA as 'Valor Parcela',
        trec2.CLASSIFICACAO as 'Categoria'
        FROM View_Parcelas_Agrupadas vpa
        INNER JOIN T_EMPRESAS te ON (vpa.FK_EMPRESA = te.ID)
        LEFT JOIN T_RECEITAS_EXTRAORDINARIAS tre ON (vpa.ID = tre.ID)
        LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON (tre.FK_CLASSIFICACAO = trec2.ID)
        WHERE YEAR(tre.DATA_OCORRENCIA) > 2024 
        AND trec2.CLASSIFICACAO IN ('Coleta de Óleo', 'Lojinha')                                  
        AND te.NOME_FANTASIA IN ({casas_str})
        ORDER BY te.NOME_FANTASIA ASC, tre.DATA_OCORRENCIA
        ''')
    
    df_parc_receit_extr = df_parc_receit_extr.groupby(['ID_Casa', 'Casa', 'Data Ocorrencia', 'Categoria'], as_index=False)['Valor Parcela'].sum()
    df_parc_receit_extr['Categoria'] = df_parc_receit_extr['Categoria'].replace(
        'Coleta de Óleo',
        'Outras Receitas'
    )
    df_parc_receit_extr['Categoria'] = df_parc_receit_extr['Categoria'].replace(
        'Lojinha',
        'Gifts'
    )
    
    # Adequa para poder concatenar ao faturamento agregado
    df_parc_receit_extr = df_parc_receit_extr.rename(columns={
        'Data Ocorrencia':'Data Evento',
        'Valor Parcela':'Valor Bruto'
    })
    
    df_parc_receit_extr['Desconto'] = 0
    df_parc_receit_extr['Valor Liquido'] = df_parc_receit_extr['Valor Bruto']
    df_parc_receit_extr = df_parc_receit_extr[['ID_Casa', 'Casa', 'Categoria', 'Data Evento', 'Valor Bruto', 'Desconto', 'Valor Liquido']]
    
    return df_parc_receit_extr
 

# Concatena todos os tipos de faturamento (Zig, Eventos e Receitas Extraordinárias)
@st.cache_data
def GET_TODOS_FATURAMENTOS_DIA(id_casa):
    # Faturament - Zig
    faturamento_agregado_diario = GET_ITENS_VENDIDOS_DIA()
    
    # Faturamento - Eventos A&B, Couvert e Locações
    if id_casa == 149:
        faturamento_eventos_inicial, faturamento_eventos_tratado = GET_FATURAMENTO_EVENTOS_PRICELESS()
    else:
        faturamento_eventos_inicial, faturamento_eventos_tratado = GET_FATURAMENTO_EVENTOS()
    
    # Faturamento - Receitas Extraordinárias
    parc_receitas_extr = GET_PARCELAS_RECEIT_EXTR() # 'Gifts' (Lojinha) e 'Outras Receitas' (Coleta de Óleo)
   
    # Concatena todos os tipos de faturamento
    todos_faturamentos = pd.concat([faturamento_agregado_diario, faturamento_eventos_tratado, parc_receitas_extr])

    return faturamento_agregado_diario, todos_faturamentos, faturamento_eventos_inicial, faturamento_eventos_tratado, parc_receitas_extr


# Orçamentos mensais
@st.cache_data
def GET_ORCAMENTOS():
    return  dataframe_query(f'''
    SELECT
        te.ID AS 'ID_Casa',
        te.NOME_FANTASIA AS 'Casa',
        to2.ANO AS 'Ano',
        to2.MES AS 'Mês',
        to2.VALOR AS 'Orçamento',
        tccg1.DESCRICAO AS 'Classificacao_Contabil_1',                    
        CASE
        WHEN tccg2.DESCRICAO IN ('VENDA DE ALIMENTO', 'Alimentação') THEN 'Alimentos'
        WHEN tccg2.DESCRICAO IN ('VENDA DE BEBIDAS', 'Bebida') THEN 'Bebidas'
        WHEN tccg2.DESCRICAO IN ('VENDA DE COUVERT/ SHOWS', 'Artístico (couvert/shows)') THEN 'Couvert'
        WHEN tccg2.DESCRICAO IN ('DELIVERY', 'Delivery') THEN 'Delivery'
        WHEN tccg2.DESCRICAO IN ('GIFTS', 'Gifts') THEN 'Gifts'
        ELSE tccg2.DESCRICAO
        END AS 'Categoria'
    FROM T_ORCAMENTOS to2
    JOIN T_EMPRESAS te ON (to2.FK_EMPRESA = te.ID)
    JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (to2.FK_CLASSIFICACAO_1 = tccg1.ID)
    JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (to2.FK_CLASSIFICACAO_2 = tccg2.ID)
    WHERE to2.ANO >= 2025
    # AND to2.FK_CLASSIFICACAO_1 IN (178, 245)                           
    ORDER BY ID_Casa, to2.MES, to2.ANO;
    ''')


# Descontos DRE
@st.cache_data
def GET_DESCONTOS():
    return dataframe_query(f'''
    SELECT 
        CASE
            WHEN te.ID = 162 THEN 'Priceless'
            WHEN te.ID = 131 THEN 'Blue Note - São Paulo'                        
            ELSE te.NOME_FANTASIA                                                                           
        END AS 'Casa',
        MONTH(tddre.DATA) AS 'Mês',
        YEAR(tddre.DATA) AS 'Ano',                  
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
        tddre.DESCONTOS_DRE AS 'Descontos - DRE'
    FROM T_DESCONTOS_DRE AS tddre
    LEFT JOIN T_EMPRESAS AS te ON (tddre.FK_CASA = te.ID)
    # WHERE tddre.DESCONTOS_DRE IN ('Desconto - Alimentação Escritório', 'Descontos - Operação', 'Descontos - Marketing')
    ORDER BY tddre.CATEGORIA ASC
    ''')


# Promoções DRE
@st.cache_data
def GET_PROMOCOES():
    return dataframe_query(f'''
    SELECT 
        CASE                   
            WHEN te.ID = 131 THEN 'Blue Note - São Paulo' 
            WHEN te.ID = 162 THEN 'Priceless'
            ELSE te.NOME_FANTASIA                                                     
        END AS 'Casa',
        MONTH(tpz.DATA) AS 'Mês',
        YEAR(tpz.DATA) AS 'Ano',                   
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
        END AS 'Categoria'
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
    ORDER BY tpz.DATA ASC, tpz.PROMOCAO ASC;
    ''')


# Calcula Faturamento Mensal de A&B: envolve Faturamento Zig, Descontos, Promoções e Eventos
def FATURAMENTO_MENSAL_AB(df_faturamento_categoria_mensal, df_descontos, df_promocoes, df_eventos, tipo):
    if tipo == 'Alimentos':
        categoria_promocoes = 'A'
        valor_descontos = 'Dedução Faturamento - Alimento'
    elif tipo == 'Bebidas':
        categoria_promocoes = 'B'
        valor_descontos = 'Dedução Faturamento - Bebida'

    # Adapta Descontos, Promoções e Eventos para merge
    df_descontos = df_descontos[df_descontos['Categoria'].isin(['EVENTOS', 'EVENTO'])].copy()
    df_promocoes = df_promocoes[(df_promocoes['Categoria'] == 'Eventos') & (df_promocoes['A&B'] == categoria_promocoes)].copy()
    df_promocoes = df_promocoes.groupby(['Casa', 'Mês', 'Ano'], as_index=False)['Desconto total'].sum()

    df_eventos = df_eventos[df_eventos['Modelo_Evento'].isin(['Consumação Mínima', 'Comanda Aberta / Couvert Antecipado'])].copy()
    df_eventos = df_eventos.groupby(['Casa', 'Mês', 'Ano'], as_index=False)['Eventos A&B'].sum()
    
    df_faturamento_categoria_mensal = (
        df_faturamento_categoria_mensal[['ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mês', 'Valor Bruto', 'Desconto', 'Valor Liquido']]
        .merge(df_descontos[['Casa', 'Ano', 'Mês', valor_descontos]], on=['Casa', 'Ano', 'Mês'], how='left')
        .merge(df_promocoes[['Casa', 'Ano', 'Mês', 'Desconto total']], on=['Casa', 'Ano', 'Mês'], how='left')
        .merge(df_eventos[['Casa', 'Ano', 'Mês', 'Eventos A&B']], on=['Casa', 'Ano', 'Mês'], how='left')
    ).fillna(0)

    df_faturamento_resultante = df_faturamento_categoria_mensal.copy()
    df_faturamento_resultante = df_faturamento_resultante.astype({
        'Valor Bruto': 'float',
        valor_descontos: 'float',
        'Desconto total': 'float',
        'Eventos A&B': 'float'
    })
   
    condicao = df_faturamento_resultante['Categoria'] == tipo
    df_faturamento_resultante.loc[condicao, 'Valor Bruto'] = (
        df_faturamento_resultante['Valor Bruto'] 
        - df_faturamento_resultante[valor_descontos]        # subtrai Descontos
        - df_faturamento_resultante['Desconto total']       # subtrai Promoções
        - (df_faturamento_resultante['Eventos A&B'] * 0.5)  # subtrai Eventos 
    )

    df_faturamento_resultante.drop(columns=[valor_descontos, 'Desconto total', 'Eventos A&B'], inplace=True)
    return df_faturamento_resultante


# Para obter faturamentos mensais 
@st.cache_data
def GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_categoria, df_descontos, df_promocoes, df_faturamento_eventos):
    df_faturamento_categoria_mensal = df_faturamento_categoria.copy() 

    # Zera a hora
    df_faturamento_categoria_mensal['Data Evento'] = pd.to_datetime(df_faturamento_categoria_mensal['Data Evento'], errors='coerce').dt.normalize()
    df_faturamento_categoria_mensal['Ano'] = df_faturamento_categoria_mensal['Data Evento'].dt.year
    df_faturamento_categoria_mensal['Mês'] = df_faturamento_categoria_mensal['Data Evento'].dt.month
    df_faturamento_categoria_mensal = df_faturamento_categoria_mensal[df_faturamento_categoria_mensal['Ano'] > 2024]
    
    # Agrupa para ter os valores por mês
    df_faturamento_categoria_mensal = df_faturamento_categoria_mensal.groupby(['ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mês'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()

    # Calcula FATURAMENTO_MENSAL_AB 
    df_faturamento_categoria_final = FATURAMENTO_MENSAL_AB(df_faturamento_categoria_mensal, df_descontos, df_promocoes, df_faturamento_eventos, 'Alimentos')
    df_faturamento_categoria_final = FATURAMENTO_MENSAL_AB(df_faturamento_categoria_final, df_descontos, df_promocoes, df_faturamento_eventos, 'Bebidas')

    return df_faturamento_categoria_final


######################################## CMV ########################################
@st.cache_data
def GET_VALORACAO_ESTOQUE(data_inicio, data_fim):
  return dataframe_query(f'''
  SELECT 
  	te.ID AS 'ID_Loja',
  	te.NOME_FANTASIA AS 'Loja',
  	tin5.ID AS 'ID_Insumo',
  	REPLACE(tin5.DESCRICAO, ',', '.') AS 'Insumo',
  	tci.QUANTIDADE_INSUMO AS 'Quantidade',
  	tin5.FK_INSUMOS_NIVEL_4 AS 'ID_Nivel_4',
  	tudm.UNIDADE_MEDIDA_NAME AS 'Unidade_Medida',
    tin.DESCRICAO AS 'Categoria',
  	tve.VALOR_EM_ESTOQUE AS 'Valor_em_Estoque',
  	tci.DATA_CONTAGEM
  FROM T_VALORACAO_ESTOQUE tve 
  LEFT JOIN T_CONTAGEM_INSUMOS tci ON tve.FK_CONTAGEM = tci.ID 
  LEFT JOIN T_EMPRESAS te ON tci.FK_EMPRESA = te.ID 
  LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tci.FK_INSUMO = tin5.ID
  LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
  LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
  LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.ID
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tin5.FK_UNIDADE_MEDIDA = tudm.ID
  WHERE tci.QUANTIDADE_INSUMO != 0
    AND tci.DATA_CONTAGEM >= '{data_inicio}'
    AND tci.DATA_CONTAGEM <= '{data_fim}'
  ORDER BY DATA_CONTAGEM DESC
  ''')


@st.cache_data
def GET_VALORACAO_PRODUCAO(data_inicio, data_fim):
    return dataframe_query(f'''
        SELECT
            te.ID as 'ID_Loja',
            te.NOME_FANTASIA as 'Loja',
            tipc.DATA_CONTAGEM as 'Data_Contagem',
            DATE_FORMAT(DATE_SUB(tipc.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') AS 'Mes_Texto',
            tip.NOME_ITEM_PRODUZIDO as 'Item_Produzido',
            tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
            tipc.QUANTIDADE_INSUMO as 'Quantidade',
            tin.DESCRICAO as 'Categoria',
            tipv.VALOR as 'Valor_Unidade_Medida',
            ROUND(tipc.QUANTIDADE_INSUMO * tipv.VALOR, 2) as 'Valor_Total'
        FROM T_ITENS_PRODUCAO_CONTAGEM tipc
        LEFT JOIN T_ITENS_PRODUCAO_VALORACAO tipv ON (tipc.FK_ITEM_PRODUZIDO = tipv.FK_ITEM_PRODUZIDO) AND (DATE_FORMAT(tipc.DATA_CONTAGEM, '%m/%Y') = DATE_FORMAT(tipv.DATA_VALORACAO, '%m/%Y'))
        LEFT JOIN T_ITENS_PRODUCAO tip ON (tipv.FK_ITEM_PRODUZIDO = tip.ID)
        LEFT JOIN T_EMPRESAS te ON (tip.FK_EMPRESA = te.ID)
        LEFT JOIN T_INSUMOS_NIVEL_1 tin ON (tip.FK_INSUMO_NIVEL_1 = tin.ID)
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tip.FK_UNIDADE_MEDIDA = tudm.ID)
        WHERE tipc.DATA_CONTAGEM >= '{data_inicio}'
        AND tipc.DATA_CONTAGEM <= '{data_fim}'
    ''')


@st.cache_data
def GET_EVENTOS_CMV(data_inicio, data_fim):
    return dataframe_query(f'''
        SELECT 
            te.ID AS 'ID_Loja',
            te.NOME_FANTASIA AS 'Loja',
            tec.VALOR_EVENTOS_A_B AS 'Valor_AB',
            tec.DATA AS 'Data',
            cast(date_format(cast(tec.DATA AS date), '%Y-%m-01') AS date) AS 'Primeiro_Dia_Mes'
        FROM T_EVENTOS_CMV tec 
        LEFT JOIN T_EMPRESAS te ON tec.FK_EMPRESA = te.ID 
        WHERE tec.DATA BETWEEN '{data_inicio}' AND '{data_fim}'
    ''')


######################################## Despesas ########################################
@st.cache_data
def GET_AUT_BLUE_ME_SEM_PEDIDO():
    return dataframe_query(f'''
    SELECT DISTINCT
        tdr.ID,                   
        CASE
            WHEN te.ID = 131 THEN 110
            WHEN te.ID IN (161, 162) THEN 149              
            ELSE te.ID    
        END AS 'ID_Casa', 
        CASE
            WHEN te.ID = 131 THEN 'Blue Note - São Paulo'
            WHEN te.ID IN (161, 162) THEN 'Priceless'               
            ELSE te.NOME_FANTASIA    
        END AS 'Casa', 
        STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') AS 'Data_Competencia',
        STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d') AS 'Data_Vencimento',
        tf.CORPORATE_NAME AS 'Fornecedor',
        tdr.OBSERVACAO AS 'Descricao',
        tdr.VALOR_PAGAMENTO AS 'Valor_Pagamento',
        tdr.VALOR_LIQUIDO AS 'Valor_Liquido',
        CASE
            WHEN tccg.DESCRICAO = 'Despesas com Transporte / Hospedagem' THEN 'Manutenção' -- considera como Despesas Gerais  
            WHEN tccg2.DESCRICAO = '  -  Pro Labore' THEN 'Mão de Obra - Benefícios'            
            ELSE tccg.DESCRICAO                            
        END as 'Classificacao_Contabil_1',
        tccg2.DESCRICAO as 'Classificacao_Contabil_2',
        vcpj.Cargo_DRE as 'Cargo_DRE'
    FROM T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN View_Cargos_PJ vcpj ON (tf.CORPORATE_NAME = vcpj.Codigo_PJ)
    LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri ON (tdr.ID = tdri.FK_DESPESA_RAPIDA)
    WHERE tccg.FK_VERSAO_PLANO_CONTABIL = 103 AND YEAR(tdr.COMPETENCIA) >= 2024
    AND tdri.ID IS NULL
    AND tdr.BIT_CANCELADA = 0  
    AND tccg.ID NOT IN (165,206,244)          
    UNION ALL
    SELECT   # Aut_Endividamentos (Ações Trabalhistas e Endividamentos)
        tdr.ID,                   
        CASE
            WHEN te.ID = 131 THEN 110
            ELSE te.ID    
        END AS 'ID_Casa', 
        CASE
            WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo'
            ELSE te.NOME_FANTASIA    
        END AS 'Casa', 
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN DATE(tc2.`Data`)
            ELSE DATE(tc.`Data`)
        END AS 'Data_Competencia',
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN DATE(tdp.`DATA`)
            ELSE DATE(tdr.VENCIMENTO)
        END as 'Data_Vencimento',
        tf.CORPORATE_NAME AS 'Fornecedor',
        tdr.OBSERVACAO AS 'Descricao',
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN tdp.VALOR
            ELSE IF(tdr.VALOR_LIQUIDO IS NULL, tdr.VALOR_PAGAMENTO, tdr.VALOR_LIQUIDO)
        END as 'Valor_Pagamento', # nesse caso, valor liquido é o considerado
        NULL AS 'Valor_Liquido',   
        CASE              
            WHEN tccg2.ID = 867 THEN 'Mão de Obra - Encargos e Provisões' -- Ações Trabalhistas  
            -- Endividamentos
            WHEN te.NOME_FANTASIA NOT IN ('Priceless', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Orfeu') AND tccg2.DESCRICAO IN ('Endividamento Geral', 'Processo Judicial', 'Processo Civil', 'Recurso Processual', 'Empréstimos Gerais') THEN 'Dividendos e Remunerações Variáveis'
            WHEN te.NOME_FANTASIA IN ('Priceless', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Orfeu') AND tccg2.DESCRICAO IN ('Endividamento Geral', 'Processo Civil', 'Recurso Processual', 'Empréstimos Gerais') THEN 'Dividendos e Remunerações Variáveis'
            WHEN te.NOME_FANTASIA IN ('Priceless', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Orfeu') AND tccg2.DESCRICAO IN ('Processo Judicial') THEN 'Mão de Obra - Encargos e Provisões'
            ELSE tccg.DESCRICAO
        END AS 'Classificacao_Contabil_1', 
        CASE
            WHEN te.NOME_FANTASIA IN ('Priceless', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Orfeu') AND tccg2.DESCRICAO = 'Processo Judicial' THEN '  -  Ações trabalhistas'  
            ELSE tccg2.DESCRICAO                                                                              
        END AS 'Classificacao_Contabil_2',              
        NULL AS 'Cargo_DRE'
    FROM T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
    LEFT JOIN T_CALENDARIO tc ON (tdr.FK_DATA_REALIZACAO_PGTO = tc.ID)
    LEFT JOIN T_CALENDARIO tc2 ON (tdp.FK_DATA_REALIZACAO_PGTO = tc2.ID)
    WHERE tccg.ID IN (165,206,244)
    UNION ALL                       
    SELECT   # Casos Bar Léo, Riviera: Processo Judicial vai pra Ações Trabalhistas também
        tdr.ID,                   
        te.ID AS 'ID_Casa', 
        te.NOME_FANTASIA AS 'Casa', 
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN DATE(tc2.`Data`)
            ELSE DATE(tc.`Data`)
        END AS 'Data_Competencia',
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN DATE(tdp.`DATA`)
            ELSE DATE(tdr.VENCIMENTO)
        END as 'Data_Vencimento',
        tf.CORPORATE_NAME AS 'Fornecedor',
        tdr.OBSERVACAO AS 'Descricao',
        CASE
            WHEN tdp.FK_DESPESA IS NOT NULL THEN tdp.VALOR
            ELSE IF(tdr.VALOR_LIQUIDO IS NULL, tdr.VALOR_PAGAMENTO, tdr.VALOR_LIQUIDO)
        END as 'Valor_Pagamento', # nesse caso, valor liquido é o considerado
        NULL AS 'Valor_Liquido',   
        'Mão de Obra - Encargos e Provisões' AS 'Classificacao_Contabil_1', 
        '  -  Ações trabalhistas' AS 'Classificacao_Contabil_2',              
        NULL AS 'Cargo_DRE'
    FROM T_DESPESA_RAPIDA tdr
    INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
    LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
    LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
    LEFT JOIN T_CALENDARIO tc ON (tdr.FK_DATA_REALIZACAO_PGTO = tc.ID)
    LEFT JOIN T_CALENDARIO tc2 ON (tdp.FK_DATA_REALIZACAO_PGTO = tc2.ID)
    WHERE te.ID IN (116, 115)
    AND tccg2.DESCRICAO = 'Processo Judicial';                                    
    ''')


@st.cache_data
def GET_AUT_BLUE_ME_COM_PEDIDO(): # Nova versão - considerando data de recebimento
    return dataframe_query(f'''
        WITH despesa_com_insumos AS (
            SELECT
                tdr.ID,
                tdr.FK_LOJA,
                tdr.COMPETENCIA,
                tdr.DATA_ENTREGA,           
                tdr.VALOR_LIQUIDO,
                SUM(tdri.VALOR) AS Valor_Total_Insumos,
                SUM(CASE WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR ELSE 0 END) AS Valor_Alimentos,
                SUM(CASE WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR ELSE 0 END) AS Valor_Bebidas,
                SUM(CASE WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR ELSE 0 END) AS Valor_Descartaveis,
                SUM(CASE WHEN tin1.DESCRICAO = 'GELO / GAS / CARVAO / VELAS' THEN tdri.VALOR ELSE 0 END) AS Valor_Gelo_Gas,
                SUM(CASE WHEN tin1.DESCRICAO = 'UTENSILIOS' THEN tdri.VALOR ELSE 0 END) AS Valor_Utensilios,
                SUM(CASE WHEN tin1.DESCRICAO NOT IN ('ALIMENTOS', 'BEBIDAS', 'DESCARTAVEIS/HIGIENE E LIMPEZA', 'GELO / GAS / CARVAO / VELAS', 'UTENSILIOS') THEN tdri.VALOR ELSE 0 END) AS Valor_Outros,
                tf.CORPORATE_NAME
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
            GROUP BY tdr.ID, tdr.FK_LOJA, tdr.COMPETENCIA, tdr.DATA_ENTREGA, tdr.VALOR_LIQUIDO, tf.CORPORATE_NAME
        )
        SELECT
            CASE WHEN te.NOME_FANTASIA = 'Blue Note SP (Novo)' THEN 'Blue Note - São Paulo' ELSE te.NOME_FANTASIA END AS Casa,
            dci.CORPORATE_NAME AS Fornecedor,
            CASE
                WHEN dci.DATA_ENTREGA IS NOT NULL THEN STR_TO_DATE(dci.DATA_ENTREGA, '%Y-%m-%d')
                ELSE STR_TO_DATE(dci.COMPETENCIA, '%Y-%m-%d')
            END AS Data_Emissao,              
            # STR_TO_DATE(dci.COMPETENCIA, '%Y-%m-%d') AS Data_Emissao,
            dci.VALOR_LIQUIDO AS Valor_Liquido,
            dci.Valor_Total_Insumos AS Valor_Cotacao,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Alimentos / dci.Valor_Total_Insumos)), 2) AS Valor_Liq_Alimentos,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Bebidas / dci.Valor_Total_Insumos)), 2) AS Valor_Liq_Bebidas,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Descartaveis / dci.Valor_Total_Insumos)), 2) AS Valor_Liq_Descart_Hig_Limp,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Gelo_Gas / dci.Valor_Total_Insumos)), 2) AS Valor_Gelo_Gas_Carvao_Velas,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Utensilios / dci.Valor_Total_Insumos)), 2) AS Valor_Utensilios,
            ROUND((dci.VALOR_LIQUIDO * (dci.Valor_Outros / dci.Valor_Total_Insumos)), 2) AS Valor_Liq_Outros
        FROM despesa_com_insumos dci
        JOIN T_EMPRESAS te ON dci.FK_LOJA = te.ID
        WHERE te.ID <> 135 
        AND YEAR(STR_TO_DATE(dci.COMPETENCIA, '%Y-%m-%d')) > 2024
        ORDER BY dci.ID;
    ''')


def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO_PERIODO_LOJA():
  return dataframe_query(f'''
    SELECT
      q.ID_Casa,
      q.Casa,
      q.Primeiro_Dia_Mes,
      SUM(q.Valor_Liquido) AS BlueMe_Com_Pedido_Valor_Liquido,
      SUM(q.Valor_Insumos) AS BlueMe_Com_Pedido_Valor_Insumos,
      SUM(q.Valor_Liq_Alimentos) AS Valor_Liq_Alimentos,
      SUM(q.Valor_Liq_Bebidas) AS Valor_Liq_Bebidas,
      SUM(q.Valor_Liq_Descart_Hig_Limp) AS BlueMe_Com_Pedido_Valor_Liq_Descart_Hig_Limp,
      SUM(q.Valor_Liq_Outros) AS BlueMe_Com_Pedido_Valor_Liq_Outros
    FROM (
      SELECT
        tdr.ID AS tdr_ID,
        te.ID AS ID_Casa,
        te.NOME_FANTASIA AS Casa,
        tdr.VALOR_LIQUIDO AS Valor_Liquido,
        SUM(tdri.VALOR) AS Valor_Insumos,
        CASE
            WHEN tdr.DATA_ENTREGA IS NOT NULL THEN CAST(DATE_FORMAT(tdr.DATA_ENTREGA, '%Y-%m-01') AS DATE)
            ELSE CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE)
        END AS Primeiro_Dia_Mes,                 
        # CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE),'%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'ALIMENTOS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Alimentos,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'BEBIDAS' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Bebidas,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO = 'DESCARTAVEIS/HIGIENE E LIMPEZA' THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Descart_Hig_Limp,
        ROUND(
          tdr.VALOR_LIQUIDO * (
            SUM(CASE
              WHEN tin1.DESCRICAO NOT IN (
                'ALIMENTOS',
                'BEBIDAS',
                'DESCARTAVEIS/HIGIENE E LIMPEZA',
                'GELO / GAS / CARVAO / VELAS',
                'UTENSILIOS'
              )
              THEN tdri.VALOR
              ELSE 0
            END) / NULLIF(SUM(tdri.VALOR),0)
          ),
          2
        ) AS Valor_Liq_Outros
      FROM
        T_DESPESA_RAPIDA tdr JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
        JOIN T_DESPESA_RAPIDA_ITEM tdri ON tdr.ID = tdri.FK_DESPESA_RAPIDA
        LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tdri.FK_INSUMO = tin5.ID
        LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID
        LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID
        LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
        LEFT JOIN T_INSUMOS_NIVEL_1 tin1 ON tin2.FK_INSUMOS_NIVEL_1 = tin1.ID
      WHERE
        tdri.ID IS NOT NULL
        AND te.ID <> 135
        AND tdr.BIT_CANCELADA = 0
      GROUP BY
        tdr.ID,
        te.ID,
        te.NOME_FANTASIA,
        tdr.VALOR_LIQUIDO,
        tdr.COMPETENCIA,
        tdr.DATA_ENTREGA                 
    ) q
    GROUP BY
      q.ID_Casa,
      q.Casa,
      q.Primeiro_Dia_Mes
    ORDER BY
      q.ID_Casa,
      q.Primeiro_Dia_Mes;
''')


@st.cache_data
def GET_AUT_FOLHA_PAGAMENTO():
    return dataframe_query(f'''
    SELECT
        CASE 
            WHEN te.ID = 131 THEN 110
            ELSE te.ID                                  
        END AS 'ID_Casa',
        CASE
            WHEN te.ID = 131 THEN 'Blue Note - São Paulo'
            ELSE te.NOME_FANTASIA 
        END AS 'Casa',
        tffs.CNPJ AS 'CNPJ_CASA',
        tffs.NUMERO_MATRICULA AS 'NUM_MATRICULA_FUNC',
        tffs.NOME AS 'NOME_FUNC',
        tffs.CPF AS 'CPF_FUNC',
        CAST(SUBSTRING(tffs.REFERENCIA, 1, 2) AS UNSIGNED) AS 'Mês',
        CAST(SUBSTRING(tffs.REFERENCIA, 3, 4) AS UNSIGNED) AS 'Ano',
        tffs.CODIGO_VERBA,
        tffs.VERBA,
        tffs.PROCESSO,
        tffs.QUANTIDADE,
        tffs.VALOR AS 'Valor'
    FROM T_FICHA_FINANCEIRA_SINERGY tffs
    LEFT JOIN T_EMPRESAS AS te ON (tffs.FK_CASA = te.ID)
    WHERE tffs.CODIGO_VERBA = 2003; # Gorjeta
    ''')


# @st.cache_data
# def GET_AUT_ENDIVIDAMENTOS():
#     return dataframe_query(f'''
#     SELECT DISTINCT
#         te.ID as 'ID_Casa',
#         te.NOME_FANTASIA as 'Casa',
#         CASE
#             WHEN tdp.FK_DESPESA IS NOT NULL THEN DATE(tc2.`Data`)
#             ELSE DATE(tc.`Data`)
#         END AS 'Data_Competencia',
#         CASE
#             WHEN tdp.FK_DESPESA IS NOT NULL THEN date(tdp.`DATA`)
#             ELSE date(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d %H:%i:%s'))
#         END as 'Data_Vencimento',                   
#         tf.CORPORATE_NAME as 'Fornecedor',
#         tdr.OBSERVACAO as 'Descricao',
#         CASE
#             WHEN tdp.FK_DESPESA IS NOT NULL THEN tdp.VALOR
#             ELSE IF(tdr.VALOR_LIQUIDO IS NULL, tdr.VALOR_PAGAMENTO, tdr.VALOR_LIQUIDO)
#         END as 'Valor_Pagamento',
#         tdr.VALOR_PAGAMENTO as 'Valor_Liquido',                   
#         tccg.DESCRICAO as 'Classificacao_Contabil_1',
#         tccg2.DESCRICAO as 'Classificacao_Contabil_2'
#     FROM T_DESPESA_RAPIDA tdr
#     INNER JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
#     LEFT JOIN T_LOJAS tl ON (te.FK_LOJA = tl.ID)
#     LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
#     LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
#     LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID)
#     LEFT JOIN T_DEPESA_PARCELAS tdp ON (tdp.FK_DESPESA = tdr.ID)
#     LEFT JOIN T_CALENDARIO tc ON (tdr.FK_DATA_REALIZACAO_PGTO = tc.ID)
#     LEFT JOIN T_CALENDARIO tc2 ON (tdp.FK_DATA_REALIZACAO_PGTO = tc2.ID)
#     LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
#     WHERE tccg.ID IN (165,206,244)
#     ORDER BY tdr.ID desc, tdp.ID desc;
#     ''')


@st.cache_data
def GET_AJUSTES_MANUAIS_DRE():
    return dataframe_query(f'''
    SELECT                        
        CASE
            WHEN te.ID IN (161, 162) THEN 149
            ELSE te.ID    
        END AS 'ID_Casa', 
        CASE
            WHEN te.ID IN (161, 162) THEN 'Priceless'
            ELSE te.NOME_FANTASIA    
        END AS 'Casa',                  
        tam.MES_COMPETENCIA AS 'Mês',
        tam.ANO_COMPETENCIA AS 'Ano',          
        tccg1.DESCRICAO AS 'Classificacao_Contabil_1',
        tccg2.DESCRICAO AS 'Classificacao_Contabil_2',
        tam.VALOR AS 'Valor Ajuste',
        tam.DESCRICAO AS 'Descrição Ajuste'
    FROM T_AJUSTES_MANUAIS_DRE AS tam
    LEFT JOIN T_EMPRESAS AS te ON (tam.FK_EMPRESA = te.ID)   
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tam.FK_CLASSIFICACAO_CONTABIL_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tam.FK_CLASSIFICACAO_CONTABIL_2 = tccg2.ID)
    # UNION ALL 
    # SELECT                         
    #     te.ID 'ID_Casa', 
    #     te.NOME_FANTASIA AS 'Casa',                  
    #     tam.MES_COMPETENCIA AS 'Mês',
    #     tam.ANO_COMPETENCIA AS 'Ano',          
    #     'Dividendos e Remunerações Variáveis' AS 'Classificacao_Contabil_1',
    #     'Processo Judicial' AS 'Classificacao_Contabil_2',
    #     tam.VALOR AS 'Valor Ajuste',
    #     tam.DESCRICAO AS 'Descrição Ajuste'
    # FROM T_AJUSTES_MANUAIS_DRE AS tam
    # LEFT JOIN T_EMPRESAS AS te ON (tam.FK_EMPRESA = te.ID)   
    # LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tam.FK_CLASSIFICACAO_CONTABIL_1 = tccg1.ID)
    # LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (tam.FK_CLASSIFICACAO_CONTABIL_2 = tccg2.ID)
    # WHERE te.NOME_FANTASIA IN ('Bar Brahma - Centro')
    # AND tccg2.DESCRICAO = '  -  Ações trabalhistas';                                                                                                                                                       
    ''')


@st.cache_data
def GET_CONSUMO_CARTAO_BLACK():
    return dataframe_query(f'''
    SELECT 
        tccb.CARTAO_FB,
        tccb.NOME,
        tccb.CENTRO_CUSTO,                                                                                
        CASE
            WHEN te.ID IN (161, 162) THEN 149
            ELSE te.ID    
        END AS 'ID_Casa', 
        CASE
            WHEN te.ID IN (161, 162) THEN 'Priceless'
            ELSE te.NOME_FANTASIA    
        END AS 'Casa',                  
        tccb.MES AS 'Mês',
        tccb.ANO AS 'Ano',
        tccb.VALOR AS 'Valor Cartão Black'
    FROM T_CONSUMO_CARTAO_BLACK AS tccb
    LEFT JOIN T_EMPRESAS AS te ON (tccb.FK_EMPRESA = te.ID)
    WHERE te.ID IN (127, 114, 148, 116, 156, 105, 104, 115, 162);                                                                                  
    ''')


@st.cache_data
def GET_PARAMETROS_IMPOSTOS():
    return dataframe_query(f'''
    SELECT 
        te.ID AS 'ID_Casa',
        te.NOME_FANTASIA AS 'Casa',                   
        DATE(tpci.DATA_INICIO_VIGENCIA) AS 'Data Inicio',
        DATE(tpci.DATA_FIM_VIGENCIA) AS 'Data Fim',
        tccg1.DESCRICAO AS 'Classificacao_Contabil_1',
        CASE                   
            WHEN tpci.NOME_IMPOSTO IN ('CSLL s/ Serviço', 'IRPJ s/ Serviço', 'CSLL s/ Comercio', 'IRPJ s/ Comercio', 'CSLL Não operacional', 'IRPJ Não operacional') THEN tpci.NOME_IMPOSTO                
            ELSE tccg2.DESCRICAO 
        END AS 'Classificacao_Contabil_2',
        tpci.NOME_IMPOSTO AS 'Nome Imposto',
        tpci.PORC_TAXA_APLICADA AS 'Taxa',
        tpci.DESCRICAO AS 'Descrição'
    FROM T_PARAMETROS_CALCULO_IMPOSTOS AS tpci
    LEFT JOIN T_EMPRESAS AS te ON (te.ID = tpci.FK_EMPRESA)   
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 AS tccg1 ON (tpci.FK_CLASSIFICACAO_CONT_GRUPO_1 = tccg1.ID)
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 AS tccg2 ON (tpci.FK_CLASSIFICACAO_CONT_GRUPO_2 = tccg2.ID);                                                                                                                                                  
    ''')


@st.cache_data
def GET_IMPOSTO_SIMPLES():
    return dataframe_query(f'''
    SELECT 
        tais.MINIMO_RECEITA_BRUTA,
        tais.MAXIMO_RECEITA_BRUTA,
        tais.ALIQUOTA,
        tais.VALOR_DEDUZIR,
        tais.DATA_INICIO_VIGENCIA AS 'Data Inicio',
        tais.DATA_FIM_VIGENCIA AS 'Data Fim'                                                                                               
    FROM T_ALIQUOTAS_IMPOSTO_SIMPLES AS tais;                                                                                                                                                
    ''')
