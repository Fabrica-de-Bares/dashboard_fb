import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas

@st.cache_data
def GET_FUNCIONARIOS_ATIVOS(lista_ids_casas, dt_inicio, dt_fim):
    ids_str = ', '.join(str(i) for i in lista_ids_casas)
    return dataframe_query(f'''
        SELECT DISTINCT
            CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                WHEN te.ID = 131 THEN 110
                ELSE te.ID
            END AS `ID Casa`,
            CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 'Girondino - CCBB'
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 'Girondino'
                WHEN te.ID = 131 THEN 'Blue Note - São Paulo'
                ELSE te.NOME_FANTASIA
            END AS `Casa`,
            tsf.ID AS 'ID Funcionário',
            tsf.COD_FUNCIONARIO_SINERGY AS 'Código Funcionário',
            tsf.CPF,
            tsf.NOME,
            tscf.DESCRICAO AS 'Cargo',
            tssc.DESCRICAO AS 'Setor',
            tstvf.DESCRICAO AS 'Vínculo'
        FROM T_SINERGY_HISTORICO_FUNCIONARIOS tshf
        INNER JOIN T_SINERGY_FUNCIONARIOS_STATUS tsfs ON tsfs.ID = tshf.FK_FUNCIONARIO_STATUS
        INNER JOIN T_SINERGY_FUNCIONARIOS tsf ON tsf.ID = tshf.FK_FUNCIONARIO
        INNER JOIN T_SINERGY_CARGOS_FUNCIONARIOS tscf ON tscf.ID = tshf.FK_CARGOS_FUNCIONARIOS
        INNER JOIN T_SINERGY_FILIAIS tsf2 ON tsf2.ID = tshf.FK_FILIAL
        INNER JOIN T_EMPRESAS te ON te.ID = tsf2.FK_EMPRESA
        INNER JOIN T_SINERGY_LOCAIS_DE_TRABALHO tsldt ON tsldt.ID = tshf.FK_LOCAL_DE_TRABALHO
        LEFT JOIN T_SINERGY_SETORES_CARGO tssc ON tssc.ID = tscf.FK_SETOR
        LEFT JOIN T_SINERGY_TIPOS_VINCULO_FUNCIONARIOS tstvf ON tstvf.ID = tshf.FK_TIPO_VINCULO
        WHERE (
            CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                WHEN te.ID = 131 THEN 110 -- Blue Note SP (Novo) cadastrado incorretamente, correto é Blue Note - São Paulo
                ELSE te.ID
            END
        ) IN ({ids_str})
            AND tshf.FK_FUNCIONARIO_STATUS = 100
            AND DATE(tshf.DATA_INICIO_VIGENCIA) <= '{dt_fim}'
            AND COALESCE(DATE(tshf.DATA_FIM_VIGENCIA), '{dt_fim}') >= '{dt_inicio}'
        ORDER BY te.NOME_FANTASIA, tssc.DESCRICAO, tscf.DESCRICAO, tsf.NOME
''')

@st.cache_data
def GET_FUNCIONARIOS_ATIVOS_POR_MES(lista_ids_casas, ano):
    ids_str = ', '.join(str(i) for i in lista_ids_casas)
    return dataframe_query(f'''
        WITH meses AS (
            SELECT 1 AS MES UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
            UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
            UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
        ),
        historico_mes AS (
            SELECT
                meses.MES,
                tshf.FK_FUNCIONARIO,
                tshf.FK_CARGOS_FUNCIONARIOS,
                tshf.FK_FILIAL,
                tshf.FK_LOCAL_DE_TRABALHO,
                tshf.FK_TIPO_VINCULO,
                ROW_NUMBER() OVER (
                    PARTITION BY meses.MES, tshf.FK_FUNCIONARIO
                    ORDER BY DATE(tshf.DATA_INICIO_VIGENCIA) DESC
                ) AS rn
            FROM meses
            INNER JOIN T_SINERGY_HISTORICO_FUNCIONARIOS tshf
                -- Considera qualquer vigência que tenha tocado o mês (não só o fim do mês)
                ON DATE(tshf.DATA_INICIO_VIGENCIA) <= LAST_DAY(STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d'))
                AND COALESCE(DATE(tshf.DATA_FIM_VIGENCIA), LAST_DAY(STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d')))
                    >= STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d')
                -- Status avaliado na própria vigência: só entram períodos em que o funcionário estava ativo
                AND tshf.FK_FUNCIONARIO_STATUS = 100
        )
        SELECT
            hm.MES,
            tscf.DESCRICAO AS 'Cargo',
            tstvf.DESCRICAO AS 'Vínculo',
            COUNT(DISTINCT tsf.ID) AS 'Nº Funcionários Ativos'
        FROM historico_mes hm
        INNER JOIN T_SINERGY_FUNCIONARIOS tsf ON tsf.ID = hm.FK_FUNCIONARIO
        INNER JOIN T_SINERGY_CARGOS_FUNCIONARIOS tscf ON tscf.ID = hm.FK_CARGOS_FUNCIONARIOS
        INNER JOIN T_SINERGY_FILIAIS tsf2 ON tsf2.ID = hm.FK_FILIAL
        INNER JOIN T_EMPRESAS te ON te.ID = tsf2.FK_EMPRESA
        INNER JOIN T_SINERGY_LOCAIS_DE_TRABALHO tsldt ON tsldt.ID = hm.FK_LOCAL_DE_TRABALHO
        LEFT JOIN T_SINERGY_TIPOS_VINCULO_FUNCIONARIOS tstvf ON tstvf.ID = hm.FK_TIPO_VINCULO
        WHERE hm.rn = 1
            AND (
                CASE
                    WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                    WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                    WHEN te.ID = 131 THEN 110 -- Blue Note SP (Novo) cadastrado incorretamente, correto é Blue Note - São Paulo
                    ELSE te.ID
                END
            ) IN ({ids_str})
        GROUP BY hm.MES, tscf.DESCRICAO, tstvf.DESCRICAO
        ORDER BY hm.MES, tscf.DESCRICAO
''')

@st.cache_data
def GET_REMUNERACAO_REAL_POR_MES(lista_ids_casas, ano):
    ids_str = ', '.join(str(i) for i in lista_ids_casas)
    return dataframe_query(f'''
        WITH meses AS (
            SELECT 1 AS MES UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
            UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
            UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
        ),
        historico_mes AS (
            SELECT
                meses.MES,
                tshf.FK_FUNCIONARIO,
                tshf.FK_CARGOS_FUNCIONARIOS,
                tshf.FK_FILIAL,
                tshf.FK_LOCAL_DE_TRABALHO,
                tshf.FK_TIPO_VINCULO,
                ROW_NUMBER() OVER (
                    PARTITION BY meses.MES, tshf.FK_FUNCIONARIO
                    ORDER BY DATE(tshf.DATA_INICIO_VIGENCIA) DESC
                ) AS rn
            FROM meses
            INNER JOIN T_SINERGY_HISTORICO_FUNCIONARIOS tshf
                -- Considera qualquer vigência que tenha tocado o mês (não só o fim do mês)
                ON DATE(tshf.DATA_INICIO_VIGENCIA) <= LAST_DAY(STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d'))
                AND COALESCE(DATE(tshf.DATA_FIM_VIGENCIA), LAST_DAY(STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d')))
                    >= STR_TO_DATE(CONCAT('{ano}-', meses.MES, '-01'), '%Y-%m-%d')
                -- Status avaliado na própria vigência: só entram períodos em que o funcionário estava ativo
                AND tshf.FK_FUNCIONARIO_STATUS = 100
        )
        SELECT
            hm.MES,
            CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 'Girondino - CCBB'
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 'Girondino'
                WHEN te.ID = 131 THEN 'Blue Note - São Paulo'
                ELSE te.NOME_FANTASIA
            END AS 'Casa',
            tscf.DESCRICAO AS 'Cargo',
            tstvf.DESCRICAO AS 'Vínculo',
            tsf.CPF,
            tsf.NOME,
            COALESCE(ficha_atual.VALOR, ficha_anterior.VALOR) AS 'Salário'
        FROM historico_mes hm
        INNER JOIN T_SINERGY_FUNCIONARIOS tsf ON tsf.ID = hm.FK_FUNCIONARIO
        INNER JOIN T_SINERGY_CARGOS_FUNCIONARIOS tscf ON tscf.ID = hm.FK_CARGOS_FUNCIONARIOS
        INNER JOIN T_SINERGY_FILIAIS tsf2 ON tsf2.ID = hm.FK_FILIAL
        INNER JOIN T_EMPRESAS te ON te.ID = tsf2.FK_EMPRESA
        INNER JOIN T_SINERGY_LOCAIS_DE_TRABALHO tsldt ON tsldt.ID = hm.FK_LOCAL_DE_TRABALHO
        LEFT JOIN T_SINERGY_TIPOS_VINCULO_FUNCIONARIOS tstvf ON tstvf.ID = hm.FK_TIPO_VINCULO
        -- Salário do mês corrente
        LEFT JOIN T_FICHA_FINANCEIRA_SINERGY ficha_atual
            ON ficha_atual.CPF = tsf.CPF
            AND ficha_atual.VERBA = 'Salário Mês c/ Adic.'
            AND ficha_atual.PROCESSO = '1 - Mensal'
            AND ficha_atual.FK_CASA = CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                WHEN te.ID = 131 THEN 110
                ELSE te.ID
            END
            AND ficha_atual.REFERENCIA = DATE_FORMAT(STR_TO_DATE(CONCAT('{ano}-', hm.MES, '-01'), '%Y-%m-%d'), '%m%Y')
        -- Fallback: se não houver ficha financeira do mês corrente, usa a do mês anterior
        LEFT JOIN T_FICHA_FINANCEIRA_SINERGY ficha_anterior
            ON ficha_anterior.CPF = tsf.CPF
            AND ficha_anterior.VERBA = 'Salário Mês c/ Adic.'
            AND ficha_anterior.PROCESSO = '1 - Mensal'
            AND ficha_anterior.FK_CASA = CASE
                WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                WHEN te.ID = 131 THEN 110
                ELSE te.ID
            END
            AND ficha_anterior.REFERENCIA = DATE_FORMAT(DATE_SUB(STR_TO_DATE(CONCAT('{ano}-', hm.MES, '-01'), '%Y-%m-%d'), INTERVAL 1 MONTH), '%m%Y')
        WHERE hm.rn = 1
            AND (
                CASE
                    WHEN tsldt.DESCRICAO = 'TUTUM - GIRONDINO - CCBB' THEN 160
                    WHEN tsldt.DESCRICAO IN ('TUTUM - GIRONDINO - BOA VISTA', 'TUTUM BAR E EVENTOS LTDA - GIRONDINO') THEN 156
                    WHEN te.ID = 131 THEN 110
                    ELSE te.ID
                END
            ) IN ({ids_str})
        ORDER BY hm.MES, tscf.DESCRICAO, tsf.NOME
''')