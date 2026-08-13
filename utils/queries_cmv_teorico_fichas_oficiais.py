"""
Queries — CMV Teórico por Prato via Fichas Técnicas Oficiais (módulo BlueMe).

Porte de `brands/fabrica-de-bares/queries/37_cmv_teorico_vendas_mes.sql` a
`43_cmv_teorico_rendimento_producao.sql` (repo Mini_Gabu) para dentro do dashboard_fb.
dashboard_fb é um repositório GitHub separado (Fabrica-de-Bares/dashboard_fb, submodule
do Mini_Gabu) deployado independentemente — não é possível importar os arquivos .sql do
Mini_Gabu em runtime, então o SQL é duplicado aqui literalmente, com o único ajuste
proposital: em vez de rodar 1x por ID bruto de casa (`{{id_loja}}`, padrão do script
standalone via `_rodar_por_loja`), cada query aqui recebe a lista já resolvida de IDs
brutos (`ids_brutos`) e usa `FK_EMPRESA IN (...)` — 1 roundtrip por query em vez de N,
funciona igual para casa simples (1 ID) ou casa agregada (Girondino = 156+160, Blue Note
= 131+110+178 etc.).

Metodologia de preço (cascata MEDIA_MES do mês anterior -> ULTIMA_LOCAL mais recente,
conversão de unidade KG/L) fica em `utils/functions/cmv_teorico_fichas_oficiais.py` —
aqui só o SQL bruto, mesma decisão do script de origem (não sobrecarregar o banco
operacional, compartilhado com o POS, com subqueries correlacionadas MAX(ID)/
MAX(MES_REFERENCIA)).

Metodologia de CMV%: sobre Faturamento BRUTO, não Líquido (fix 13/08/2026 — desconto de
gerente de casa é linha própria de custo/despesa na DRE, não deve reduzir o denominador
do CMV teórico). Ver `montar_mix_venda` em `utils/functions/cmv_teorico_fichas_oficiais.py`.
"""
from datetime import date

import streamlit as st
import pandas as pd

from utils.functions.general_functions import dataframe_query


# ===========================================================================
# RESOLUÇÃO DE CASA AGREGADA
# ===========================================================================

# Cópia comentada de `substituicoesIds` (utils/functions/cmv.py:13) — fonte de verdade já
# existente no próprio dashboard_fb para casa agregada -> casa canônica. NÃO é o mesmo
# dict que `transform.CASAS_NORMALIZADAS` do Mini_Gabu (inacessível em runtime aqui).
# Mantido como cópia local proposital (mesmo padrão de pequena duplicação curada que o
# dashboard já usa, ex. forecast.py:812 duplicando o replace de Blue Note de cmv.py) —
# se o dict de cmv.py mudar, atualizar aqui também.
SUBSTITUICOES_IDS_CASA = {
    103: 116,
    112: 104,
    118: 114,
    117: 114,
    139: 105,
    161: 149,
    162: 149,
    179: 149,
    110: 131,
    178: 131,
    160: 156,
    177: 176,
    181: 156,
}


def ids_brutos_da_casa(id_casa: int) -> list:
    """IDs brutos (empresa) que alimentam a casa canônica `id_casa` — inclui o próprio
    `id_casa` + qualquer ID que aponte para ele em SUBSTITUICOES_IDS_CASA. Para Girondino
    (156) retorna [156, 160]; para uma casa simples sem satélite retorna [id_casa]."""
    brutos = [raw for raw, canonico in SUBSTITUICOES_IDS_CASA.items() if canonico == id_casa]
    return [id_casa] + brutos


def _in_clause(ids_brutos) -> str:
    return ",".join(str(int(i)) for i in ids_brutos)


def _periodo_mes(ano: int, mes: int) -> tuple:
    """(periodo_inicio, periodo_fim_exclusivo) — mesma lógica de
    scripts/query_runner.py::calcular_placeholders no Mini_Gabu: 1º dia do mês e 1º dia do
    mês seguinte (filtro `< fim_exclusivo` evita perder horários do último dia em colunas
    DATETIME)."""
    periodo_inicio = date(ano, mes, 1)
    if mes == 12:
        periodo_fim_exclusivo = date(ano + 1, 1, 1)
    else:
        periodo_fim_exclusivo = date(ano, mes + 1, 1)
    return periodo_inicio, periodo_fim_exclusivo


# ===========================================================================
# QUERIES — porte de 37_...sql a 43_...sql (Mini_Gabu)
# ===========================================================================

@st.cache_data
def GET_FICHAS_OFICIAIS_VENDAS_MES(ids_brutos: tuple, ano: int, mes: int) -> pd.DataFrame:
    """Porte de 37_cmv_teorico_vendas_mes.sql. Único parametrizado por período."""
    periodo_inicio, periodo_fim_exclusivo = _periodo_mes(ano, mes)
    return dataframe_query(f'''
        SELECT
            tivd.FK_CASA,
            tivd.PRODUCT_ID,
            tivd.PRODUCT_NAME AS Produto,
            tivc2.DESCRICAO AS Categoria,
            tivt.DESCRICAO AS Tipo,
            SUM(tivd.QUANTIDADE) AS Quantidade,
            SUM(tivd.VALOR_UNITARIO * tivd.QUANTIDADE) AS Faturamento_Bruto,
            SUM(tivd.DESCONTO) AS Desconto,
            SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Faturamento_Liquido
        FROM T_ITENS_VENDIDOS_DIA tivd
        LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivc.ID_ZIGPAY = tivd.PRODUCT_ID
        LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc2.ID = tivc.FK_CATEGORIA
        LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivt.ID = tivc.FK_TIPO
        WHERE tivd.FK_CASA IN ({_in_clause(ids_brutos)})
            AND tivd.EVENT_DATE >= '{periodo_inicio}' AND tivd.EVENT_DATE < '{periodo_fim_exclusivo}'
        GROUP BY tivd.FK_CASA, tivd.PRODUCT_ID, tivd.PRODUCT_NAME, tivc2.DESCRICAO, tivt.DESCRICAO;
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_FICHAS_TECNICAS(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 38_cmv_teorico_fichas_tecnicas.sql. Cadastro (sem filtro de período)."""
    return dataframe_query(f'''
        SELECT
            tft.ID AS ID_Ficha_Tecnica,
            tft.ID_ZIGPAY,
            tft.FK_EMPRESA,
            tft.DESCRICAO_FICHA AS Ficha_Tecnica,
            tfa.DESCRICAO AS Categoria,
            tft.PRECO_VENDA,
            tft.META_CMV_PERCENT,
            tft.CUSTO_TOTAL AS Custo_Total_Cadastrado,
            tft.RENDIMENTO_PORCOES,
            tft.PESO_PORCAO_GRAMA
        FROM T_FICHAS_TECNICAS tft
        LEFT JOIN T_FICHAS_TECNICAS_APLICACOES tfa ON tfa.ID = tft.FK_FICHAS_TECNICAS_APLICACAO
        WHERE tft.FK_EMPRESA IN ({_in_clause(ids_brutos)})
            AND tft.ATIVO_REGISTRO = 1;
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_COMPOSICAO_INSUMOS(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 39_cmv_teorico_composicao_insumos.sql. Nível 0 da composição (insumos de
    estoque direto na ficha)."""
    return dataframe_query(f'''
        SELECT
            taift.ID AS ID_Linha,
            taift.FK_FICHA_TECNICA AS ID_Ficha_Tecnica,
            tft.FK_EMPRESA,
            taift.FK_ITEM_ESTOQUE,
            tie.DESCRICAO AS Insumo,
            COALESCE(tudm.UNIDADE_MEDIDA, tudm_insumo.UNIDADE_MEDIDA, tudm_insumo.UNIDADE_MEDIDA_NAME) AS Unidade_Medida,
            taift.QUANTIDADE_BRUTA,
            taift.QUANTIDADE_LIQUIDA,
            taift.QUANTIDADE_POR_FICHA,
            taift.CUSTO_TOTAL AS Custo_Total_Cadastrado
        FROM T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA taift
        INNER JOIN T_FICHAS_TECNICAS tft ON tft.ID = taift.FK_FICHA_TECNICA
        LEFT JOIN T_INSUMOS_ESTOQUE tie ON tie.ID = taift.FK_ITEM_ESTOQUE
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tudm.ID = taift.FK_UNIDADE_MEDIDA
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm_insumo ON tudm_insumo.ID = tie.FK_UNIDADE_MEDIDA
        WHERE tft.FK_EMPRESA IN ({_in_clause(ids_brutos)})
            AND tft.ATIVO_REGISTRO = 1;
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_COMPOSICAO_PRODUCAO(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 40_cmv_teorico_composicao_producao.sql. Nível 0 da composição (itens de
    produção direto na ficha)."""
    return dataframe_query(f'''
        SELECT
            taipft.ID AS ID_Linha,
            taipft.FK_FICHA_TECNICA AS ID_Ficha_Tecnica,
            tft.FK_EMPRESA,
            taipft.FK_ITEM_PRODUCAO,
            tip.NOME_ITEM_PRODUZIDO AS Item_Producao,
            COALESCE(tudm.UNIDADE_MEDIDA, tudm_item.UNIDADE_MEDIDA, tudm_item.UNIDADE_MEDIDA_NAME) AS Unidade_Medida,
            taipft.QUANTIDADE_BRUTA,
            taipft.QUANTIDADE_LIQUIDA,
            taipft.QUANTIDADE,
            taipft.CUSTO_TOTAL AS Custo_Total_Cadastrado
        FROM T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA taipft
        INNER JOIN T_FICHAS_TECNICAS tft ON tft.ID = taipft.FK_FICHA_TECNICA
        LEFT JOIN T_ITENS_PRODUCAO tip ON tip.ID = taipft.FK_ITEM_PRODUCAO
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tudm.ID = taipft.FK_UNIDADE_MEDIDA
        LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm_item ON tudm_item.ID = tip.FK_UNIDADE_MEDIDA
        WHERE tft.FK_EMPRESA IN ({_in_clause(ids_brutos)})
            AND tft.ATIVO_REGISTRO = 1;
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_PRECOS_INSUMOS_ESTOQUE(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 41_cmv_teorico_precos_insumos_estoque.sql. Linhas cruas de preço (MEDIA_MES
    / ULTIMA_LOCAL) — resolução do preço vigente fica em Python (evita sobrecarregar o
    banco operacional, compartilhado com o POS, com subqueries correlacionadas)."""
    return dataframe_query(f'''
        SELECT
            tpie.ID,
            tpie.FK_INSUMO_ESTOQUE,
            tpie.FK_EMPRESA,
            tpie.TIPO_PRECO,
            tpie.MES_REFERENCIA,
            tpie.PRECO_UNITARIO
        FROM T_PRECO_INSUMO_ESTOQUE tpie
        WHERE tpie.FK_EMPRESA IN ({_in_clause(ids_brutos)});
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_PRECOS_ITENS_PRODUCAO(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 42_cmv_teorico_precos_itens_producao.sql. CUSTO_LOTE_TOTAL/RENDIMENTO_TOTAL
    vêm junto pois, quando PRECO_UNITARIO ausente, o custo é recalculado como
    CUSTO_LOTE_TOTAL / RENDIMENTO_TOTAL (ver resolver_preco_item_producao)."""
    return dataframe_query(f'''
        SELECT
            tpip.ID,
            tpip.FK_ITEM_PRODUCAO,
            tpip.FK_EMPRESA,
            tpip.TIPO_PRECO,
            tpip.MES_REFERENCIA,
            tpip.PRECO_UNITARIO,
            tpip.CUSTO_LOTE_TOTAL,
            tpip.RENDIMENTO_TOTAL
        FROM T_PRECO_ITEM_PRODUCAO tpip
        WHERE tpip.FK_EMPRESA IN ({_in_clause(ids_brutos)});
    ''')


@st.cache_data
def GET_FICHAS_OFICIAIS_RENDIMENTO_PRODUCAO(ids_brutos: tuple) -> pd.DataFrame:
    """Porte de 43_cmv_teorico_rendimento_producao.sql. Fallback de rendimento quando
    nenhuma linha de preço de item de produção tem RENDIMENTO_TOTAL preenchido.
    T_FICHA_TECNICA_PRODUCAO não tem FK_EMPRESA — filtro de loja via T_ITENS_PRODUCAO."""
    return dataframe_query(f'''
        SELECT
            tftp.ID AS ID_Ficha_Producao,
            tftp.FK_ITEM_PRODUZIDO,
            tftp.QUANTIDADE_FICHA
        FROM T_FICHA_TECNICA_PRODUCAO tftp
        INNER JOIN T_ITENS_PRODUCAO tip ON tip.ID = tftp.FK_ITEM_PRODUZIDO
        WHERE tip.FK_EMPRESA IN ({_in_clause(ids_brutos)});
    ''')
