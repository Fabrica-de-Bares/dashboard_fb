"""
CMV Teórico por Prato via Fichas Técnicas Oficiais (módulo BlueMe) — lógica de dados.

Porte quase literal das funções 100%-pandas de
`brands/fabrica-de-bares/scripts/gerar_excel_cmv_teorico_girondino.py` (repo Mini_Gabu)
para dentro do dashboard_fb — nenhuma dessas funções depende de Streamlit nem de
openpyxl no script de origem, então o porte é direto. dashboard_fb é um repositório
GitHub separado, deployado independentemente do Mini_Gabu (não é possível importar o
script de lá em runtime) — por isso a duplicação. Se o script de origem mudar, replicar
manualmente aqui.

Metodologia: preço vigente = MEDIA_MES do mês anterior ao período (fallback ULTIMA_LOCAL
mais recente); CMV% sobre Faturamento BRUTO (fix 13/08/2026 — desconto de gerente de
casa é linha própria de custo/despesa na DRE, não deve reduzir o denominador do CMV
teórico); fichas técnicas com mais de 1 cadastro ATIVO simultâneo no mesmo ID_ZIGPAY são
marcadas "Ficha Ambígua" em vez de terem a linha de venda duplicada (fix 13/08/2026).
"""
from datetime import date

import pandas as pd


# ===========================================================================
# UNIDADE DE MEDIDA
# ===========================================================================

# Sinônimos de unidade de medida cujo preço é por KG/L, mas a quantidade na ficha é
# registrada em gramas/ml (por isso a divisão por 1000) — mesma lista da query de
# referência usada pela BlueMe internamente.
UNIDADES_KG_L = {
    "KG", "KILO", "KILOGRAMA", "KILOGRAMAS", "KILOS",
    "QUILO", "QUILOGRAMA", "QUILOGRAMAS", "QUILOS",
    "LT", "L", "LITRO", "LITROS", "LTR", "LIT",
}

# Nome por extenso por sigla, curado à mão. ATENÇÃO: "GR" (maiúsculo) e "gr" (minúsculo)
# são unidades DIFERENTES em T_UNIDADES_DE_MEDIDAS — GR = Garrafa, gr = Grama (confirmado
# com o Gabriel, jul/2026) — por isso a sigla NÃO pode ser normalizada para maiúscula
# antes do lookup, senão as duas colidem.
UNIDADE_MEDIDA_NOME_CASE_SENSITIVE = {"GR": "Garrafa", "gr": "Grama"}
UNIDADE_MEDIDA_NOME = {
    "UN": "Unidade", "PC": "Pacote", "KG": "Quilograma", "LT": "Litro",
    "CX": "Caixa", "SC": "Saco", "BB": "Bombona",
    "GALAO": "Galão", "BARRIL": "Barril", "FR": "Fardo", "PT": "Pote",
    "BD": "Balde", "ML": "Mililitros",
}


def _unidade_medida_nome(unidade) -> str:
    if not unidade or pd.isna(unidade):
        return "—"
    sigla = str(unidade).strip()
    if sigla in UNIDADE_MEDIDA_NOME_CASE_SENSITIVE:
        return UNIDADE_MEDIDA_NOME_CASE_SENSITIVE[sigla]
    return UNIDADE_MEDIDA_NOME.get(sigla.upper(), sigla)


def _unidade_e_kg_l(unidade) -> bool:
    if not unidade or pd.isna(unidade):
        return False
    limpa = str(unidade).upper().replace(".", "").replace(" ", "").strip()
    return limpa in UNIDADES_KG_L


# ===========================================================================
# PERÍODO
# ===========================================================================

def _mes_corte(ano: int, mes: int) -> date:
    """Primeiro dia do mês anterior ao período analisado — corte usado para escolher o
    MEDIA_MES vigente (preço médio do mês anterior ao fechamento, mesma regra da BlueMe)."""
    if mes == 1:
        return date(ano - 1, 12, 1)
    return date(ano, mes - 1, 1)


# ===========================================================================
# RESOLUÇÃO DE PREÇO — fallback MEDIA_MES (<= mês anterior) -> ULTIMA_LOCAL (mais recente)
# ===========================================================================

def resolver_preco_insumo_estoque(df_precos: pd.DataFrame, mes_corte: date) -> pd.DataFrame:
    """1 linha por (FK_INSUMO_ESTOQUE, FK_EMPRESA) com Preco_Unitario resolvido + Fonte_Preco.
    Preço é por empresa (o preço de um insumo pode variar entre as empresas de uma mesma
    casa agregada). A chave de saída usa FK_ITEM_ESTOQUE (não FK_INSUMO_ESTOQUE) para
    casar direto com a composição (GET_FICHAS_OFICIAIS_COMPOSICAO_INSUMOS)."""
    chave = ["FK_INSUMO_ESTOQUE", "FK_EMPRESA"]
    chave_saida = ["FK_ITEM_ESTOQUE", "FK_EMPRESA"]
    if df_precos.empty:
        return pd.DataFrame(columns=chave_saida + ["Preco_Unitario", "Fonte_Preco"])

    df = df_precos.copy()
    df["MES_REFERENCIA"] = pd.to_datetime(df["MES_REFERENCIA"], errors="coerce")
    df["PRECO_UNITARIO"] = pd.to_numeric(df["PRECO_UNITARIO"], errors="coerce")
    mes_corte_ts = pd.Timestamp(mes_corte)

    media = df[(df["TIPO_PRECO"] == "MEDIA_MES") & (df["MES_REFERENCIA"] <= mes_corte_ts) & df["PRECO_UNITARIO"].notna()]
    media_pick = (media.sort_values("MES_REFERENCIA")
                        .groupby(chave).tail(1)
                        .set_index(chave)["PRECO_UNITARIO"])

    local = df[(df["TIPO_PRECO"] == "ULTIMA_LOCAL") & df["PRECO_UNITARIO"].notna()]
    local_pick = (local.sort_values("ID")
                        .groupby(chave).tail(1)
                        .set_index(chave)["PRECO_UNITARIO"])

    linhas = []
    for k in set(media_pick.index) | set(local_pick.index):
        if k in media_pick.index:
            linhas.append((*k, float(media_pick[k]), "MEDIA_MES"))
        else:
            linhas.append((*k, float(local_pick[k]), "ULTIMA_LOCAL"))
    return pd.DataFrame(linhas, columns=chave_saida + ["Preco_Unitario", "Fonte_Preco"])


def _preco_item_producao_de_linha(row: pd.Series, rendimento_fallback):
    """PRECO_UNITARIO direto se disponível; senão CUSTO_LOTE_TOTAL / RENDIMENTO_TOTAL (ou
    rendimento cadastrado em T_FICHA_TECNICA_PRODUCAO, se a linha de preço não tiver
    RENDIMENTO_TOTAL preenchido)."""
    preco = row.get("PRECO_UNITARIO")
    if pd.notna(preco):
        return float(preco)
    custo_lote = row.get("CUSTO_LOTE_TOTAL")
    rendimento = row.get("RENDIMENTO_TOTAL")
    if pd.isna(rendimento) or not rendimento:
        rendimento = rendimento_fallback
    if pd.notna(custo_lote) and rendimento:
        return float(custo_lote) / float(rendimento)
    return None


def resolver_preco_item_producao(df_precos: pd.DataFrame, df_rendimento: pd.DataFrame, mes_corte: date) -> pd.DataFrame:
    """1 linha por (FK_ITEM_PRODUCAO, FK_EMPRESA) com Preco_Unitario resolvido + Fonte_Preco."""
    chave = ["FK_ITEM_PRODUCAO", "FK_EMPRESA"]
    if df_precos.empty:
        return pd.DataFrame(columns=chave + ["Preco_Unitario", "Fonte_Preco"])

    df = df_precos.copy()
    df["MES_REFERENCIA"] = pd.to_datetime(df["MES_REFERENCIA"], errors="coerce")
    for c in ("PRECO_UNITARIO", "CUSTO_LOTE_TOTAL", "RENDIMENTO_TOTAL"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    mes_corte_ts = pd.Timestamp(mes_corte)

    rendimento_fallback = pd.Series(dtype=float)
    if not df_rendimento.empty:
        df_r = df_rendimento.copy()
        df_r["QUANTIDADE_FICHA"] = pd.to_numeric(df_r["QUANTIDADE_FICHA"], errors="coerce")
        rendimento_fallback = df_r.groupby("FK_ITEM_PRODUZIDO")["QUANTIDADE_FICHA"].first()

    media = df[(df["TIPO_PRECO"] == "MEDIA_MES") & (df["MES_REFERENCIA"] <= mes_corte_ts)]
    media_pick = media.sort_values("MES_REFERENCIA").groupby(chave).tail(1).set_index(chave)

    local = df[df["TIPO_PRECO"] == "ULTIMA_LOCAL"]
    local_pick = local.sort_values("ID").groupby(chave).tail(1).set_index(chave)

    linhas = []
    for k in set(media_pick.index) | set(local_pick.index):
        fk_item_producao = k[0]
        rend_fb = rendimento_fallback.get(fk_item_producao)
        preco, fonte_preco = None, None
        if k in media_pick.index:
            preco = _preco_item_producao_de_linha(media_pick.loc[k], rend_fb)
            if preco is not None:
                fonte_preco = "MEDIA_MES"
        if preco is None and k in local_pick.index:
            preco = _preco_item_producao_de_linha(local_pick.loc[k], rend_fb)
            if preco is not None:
                fonte_preco = "ULTIMA_LOCAL"
        if preco is not None:
            linhas.append((*k, preco, fonte_preco))
    return pd.DataFrame(linhas, columns=chave + ["Preco_Unitario", "Fonte_Preco"])


# ===========================================================================
# CÁLCULO DE CUSTO — composição + preço resolvido, com conversão de unidade
# ===========================================================================

def calcular_custo_composicao(df_comp: pd.DataFrame, df_precos: pd.DataFrame, col_fk: str) -> pd.DataFrame:
    """Junta composição (N0) com preço resolvido, converte unidade (KG/L -> /1000) e
    calcula Custo_Total por linha: usa CUSTO_TOTAL cadastrado se não-zero; senão
    quantidade convertida x preço resolvido. Sem_Preco=1 quando nenhum dos dois está
    disponível — nunca inventa custo."""
    if df_comp.empty:
        return df_comp.assign(Preco_Unitario=pd.Series(dtype=float), Fonte_Preco=pd.Series(dtype=object),
                               Quantidade_Convertida=pd.Series(dtype=float),
                               Custo_Total=pd.Series(dtype=float), Sem_Preco=pd.Series(dtype=int))

    df = df_comp.merge(df_precos, on=[col_fk, "FK_EMPRESA"], how="left")

    for c in ("QUANTIDADE_BRUTA", "QUANTIDADE_LIQUIDA", "Custo_Total_Cadastrado"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    col_qtd_extra = "QUANTIDADE_POR_FICHA" if "QUANTIDADE_POR_FICHA" in df.columns else "QUANTIDADE"
    df[col_qtd_extra] = pd.to_numeric(df[col_qtd_extra], errors="coerce")

    def _quantidade(row) -> float:
        qtd = row["QUANTIDADE_LIQUIDA"]
        if pd.isna(qtd) or qtd == 0:
            qtd = row["QUANTIDADE_BRUTA"]
        if pd.isna(qtd) or qtd == 0:
            qtd = row[col_qtd_extra]
        if pd.isna(qtd):
            qtd = 0.0
        if _unidade_e_kg_l(row.get("Unidade_Medida")):
            qtd = qtd / 1000.0
        return float(qtd)

    df["Quantidade_Convertida"] = df.apply(_quantidade, axis=1)

    def _custo(row) -> tuple:
        cadastrado = row.get("Custo_Total_Cadastrado")
        if pd.notna(cadastrado) and cadastrado != 0:
            return float(cadastrado), 0
        preco = row.get("Preco_Unitario")
        if pd.notna(preco):
            return float(row["Quantidade_Convertida"]) * float(preco), 0
        return 0.0, 1

    custos = df.apply(lambda r: pd.Series(_custo(r), index=["Custo_Total", "Sem_Preco"]), axis=1)
    df["Custo_Total"] = custos["Custo_Total"]
    df["Sem_Preco"] = custos["Sem_Preco"]
    return df


def montar_custo_por_ficha(df_insumos_c: pd.DataFrame, df_producao_c: pd.DataFrame) -> pd.DataFrame:
    """Soma Custo_Total por ID_Ficha_Tecnica (= custo unitário do prato, já que a
    composição é por 1 unidade da ficha) e agrega o flag Sem_Preco (se qualquer
    componente estiver sem preço resolvido, o custo do prato fica marcado incompleto)."""
    partes = []
    if not df_insumos_c.empty:
        partes.append(df_insumos_c[["ID_Ficha_Tecnica", "Custo_Total", "Sem_Preco"]])
    if not df_producao_c.empty:
        partes.append(df_producao_c[["ID_Ficha_Tecnica", "Custo_Total", "Sem_Preco"]])
    if not partes:
        return pd.DataFrame(columns=["ID_Ficha_Tecnica", "Custo_Unitario_Ficha", "Sem_Preco_Ficha"])
    todos = pd.concat(partes, ignore_index=True)
    agg = todos.groupby("ID_Ficha_Tecnica").agg(
        Custo_Unitario_Ficha=("Custo_Total", "sum"),
        Sem_Preco_Ficha=("Sem_Preco", "max"),
    ).reset_index()
    return agg


# ===========================================================================
# MIX DE VENDA — custo/CMV% por prato, curva ABC, flags de pendência de cadastro
# ===========================================================================

def identificar_pares_fichas_ambiguas(df_fichas: pd.DataFrame) -> pd.DataFrame:
    """Pares (ID_ZIGPAY, FK_EMPRESA) com mais de 1 ficha técnica ATIVA simultânea —
    fan-out de cadastro DENTRO DA MESMA empresa/loja (ex.: "Cookie do Dia" cadastrado
    com 4 fichas ativas, uma por sabor do dia, em vez de 1 ficha só sendo atualizada).

    Duas fichas com o mesmo ID_ZIGPAY em empresas DIFERENTES não entram aqui — não é
    ambiguidade de cadastro, é coincidência de ID_ZIGPAY entre catálogos ZigPay de lojas
    distintas, cada ficha correta na sua casa (achado 19/08/2026: "Macchiato Duplo" tinha
    ficha própria no Girondino e outra na Girondino - CCBB, mesmo ID_ZIGPAY nas duas).

    df_fichas precisa ter ID_ZIGPAY e FK_EMPRESA (saída de
    GET_FICHAS_OFICIAIS_FICHAS_TECNICAS). Retorna 1 linha por par ambíguo com
    N_Fichas_Ativas (para exibição — ex.: "4 fichas ativas para este ID_ZIGPAY nesta
    empresa")."""
    if df_fichas.empty:
        return pd.DataFrame(columns=["ID_ZIGPAY", "FK_EMPRESA", "N_Fichas_Ativas"])
    fichas = df_fichas.copy()
    fichas["ID_ZIGPAY"] = fichas["ID_ZIGPAY"].astype(str)
    contagem = fichas.groupby(["ID_ZIGPAY", "FK_EMPRESA"])["ID_Ficha_Tecnica"].nunique()
    return contagem[contagem > 1].rename("N_Fichas_Ativas").reset_index()


def montar_mix_venda(df_vendas: pd.DataFrame, df_fichas: pd.DataFrame, df_custo_ficha: pd.DataFrame) -> pd.DataFrame:
    """1 linha por prato vendido no mês (por ficha técnica distinta — ver Ficha_Ambigua
    abaixo), com custo/CMV% e curva ABC por Faturamento Bruto.

    CMV% sobre Faturamento BRUTO, não Líquido: desconto dado por gerente de casa é uma
    linha própria de custo/despesa na DRE da casa, não deve reduzir o denominador do CMV
    teórico. Faturamento_Bruto/Desconto/Faturamento_Liquido ficam todos disponíveis como
    colunas de referência (padrão Bruto/Líquido flanqueando Desconto da brand).

    3 flags de pendência de cadastro, mutuamente exclusivas:
    - Sem_Ficha_Tecnica: nenhuma ficha técnica ativa vinculada ao (ID_ZIGPAY, empresa) do
      prato naquela loja.
    - Ficha_Ambigua: mais de 1 ficha técnica ATIVA simultânea no mesmo (ID_ZIGPAY,
      empresa) — ver identificar_pares_fichas_ambiguas. Nesse caso não dá para saber
      qual ficha é a "certa" — a linha fica marcada e sem custo calculado, até o
      cadastro no BlueMe ser corrigido.
    - Sem_Preco_Ficha: ficha única, mas algum insumo/item de produção da composição está
      sem preço resolvido (nem MEDIA_MES nem ULTIMA_LOCAL disponíveis).

    Coluna Casa (T_EMPRESAS.NOME_FANTASIA da FK_CASA da venda) identifica de qual loja
    física veio cada linha — relevante em casa agregada, onde cada loja tem catálogo
    ZigPay próprio e um mesmo prato (ex.: "Pão de Queijo") pode estar com ficha técnica
    cadastrada em uma loja e não na outra, sem ser duplicata nem prato fantasma.

    Match ficha <-> venda é feito por linha (par PRODUCT_ID + FK_CASA da venda <->
    ID_ZIGPAY + FK_EMPRESA da ficha), não só por PRODUCT_ID/ID_ZIGPAY — necessário porque
    o mesmo ID_ZIGPAY pode ter fichas DIFERENTES (custo diferente) em empresas diferentes
    da mesma casa agregada (caso Macchiato Duplo acima). O agrupamento final do Mix de
    Venda é por (PRODUCT_ID, ID_Ficha_Tecnica) — continua ignorando FK_CASA/loja de
    propósito para não fragmentar Quantidade/curva ABC quando lojas compartilham
    catálogo e ficha (ex.: Girondino + Delivery Girondino), mas abre 1 linha por ficha
    técnica distinta quando o mesmo ID_ZIGPAY aponta pra fichas diferentes em casas
    diferentes — a coluna Casa de cada linha já deixa evidente qual loja é qual.
    """
    if df_vendas.empty:
        return df_vendas

    df = df_vendas.copy()
    for c in ("Quantidade", "Faturamento_Bruto", "Desconto", "Faturamento_Liquido"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["PRODUCT_ID"] = df["PRODUCT_ID"].astype(str)
    # Gorjeta não é prato/ficha técnica.
    df = df[~df["Produto"].str.upper().str.contains("GORJETA", na=False)]
    if df.empty:
        return df

    fichas = df_fichas.copy()
    if not fichas.empty:
        fichas["ID_ZIGPAY"] = fichas["ID_ZIGPAY"].astype(str)
        fichas = fichas.merge(df_custo_ficha, on="ID_Ficha_Tecnica", how="left")
    else:
        fichas = pd.DataFrame(columns=["ID_ZIGPAY", "FK_EMPRESA", "ID_Ficha_Tecnica", "Ficha_Tecnica",
                                        "Categoria", "Custo_Unitario_Ficha", "Sem_Preco_Ficha", "META_CMV_PERCENT"])

    pares_ambiguos = identificar_pares_fichas_ambiguas(fichas)
    chave_ambigua = set(zip(pares_ambiguos["ID_ZIGPAY"], pares_ambiguos["FK_EMPRESA"]))
    if chave_ambigua:
        idx_fichas = pd.MultiIndex.from_arrays([fichas["ID_ZIGPAY"], fichas["FK_EMPRESA"]])
        fichas_unicas = fichas[~idx_fichas.isin(chave_ambigua)]
    else:
        fichas_unicas = fichas

    # Merge linha a linha (mantém FK_CASA) — precisa acontecer ANTES do agrupamento por
    # PRODUCT_ID para respeitar qual ficha pertence a qual empresa.
    linhas = df.merge(
        fichas_unicas[["ID_ZIGPAY", "FK_EMPRESA", "ID_Ficha_Tecnica", "Ficha_Tecnica",
                        "Custo_Unitario_Ficha", "Sem_Preco_Ficha", "META_CMV_PERCENT"]],
        left_on=["PRODUCT_ID", "FK_CASA"], right_on=["ID_ZIGPAY", "FK_EMPRESA"], how="left",
    )
    if chave_ambigua:
        idx_linhas = pd.MultiIndex.from_arrays([linhas["PRODUCT_ID"], linhas["FK_CASA"]])
        linhas["Ficha_Ambigua"] = idx_linhas.isin(chave_ambigua).astype(int)
        contagem_map = pares_ambiguos.set_index(["ID_ZIGPAY", "FK_EMPRESA"])["N_Fichas_Ativas"].to_dict()
        linhas["N_Fichas_Ambiguas"] = idx_linhas.map(contagem_map)
    else:
        linhas["Ficha_Ambigua"] = 0
        linhas["N_Fichas_Ambiguas"] = pd.NA
    linhas["Sem_Ficha_Tecnica"] = (linhas["ID_Ficha_Tecnica"].isna() & (linhas["Ficha_Ambigua"] == 0)).astype(int)
    linhas["Sem_Preco_Ficha"] = linhas["Sem_Preco_Ficha"].fillna(0).astype(int)
    linhas["Custo_Unitario_Ficha"] = linhas["Custo_Unitario_Ficha"].fillna(0.0)
    linhas["Custo_Total_Linha"] = linhas["Custo_Unitario_Ficha"] * linhas["Quantidade"]

    merged = linhas.groupby(["PRODUCT_ID", "Produto", "Categoria", "ID_Ficha_Tecnica"], dropna=False).agg(
        Quantidade=("Quantidade", "sum"),
        Faturamento_Bruto=("Faturamento_Bruto", "sum"),
        Desconto=("Desconto", "sum"),
        Faturamento_Liquido=("Faturamento_Liquido", "sum"),
        Custo_Total_Vendido=("Custo_Total_Linha", "sum"),
        Ficha_Tecnica=("Ficha_Tecnica", "first"),
        Sem_Preco_Ficha=("Sem_Preco_Ficha", "max"),
        Ficha_Ambigua=("Ficha_Ambigua", "max"),
        Sem_Ficha_Tecnica=("Sem_Ficha_Tecnica", "max"),
        N_Fichas_Ambiguas=("N_Fichas_Ambiguas", "max"),
        META_CMV_PERCENT=("META_CMV_PERCENT", "first"),
        Casa=("Casa", lambda s: " + ".join(sorted(pd.unique(s.dropna())))),
    ).reset_index()

    merged["Custo_Unitario_Ficha"] = (merged["Custo_Total_Vendido"] / merged["Quantidade"].replace(0, pd.NA)).fillna(0.0)
    merged["Preco_Medio"] = merged["Faturamento_Bruto"] / merged["Quantidade"].replace(0, pd.NA)

    merged["CMV_Percent"] = merged["Custo_Total_Vendido"] / merged["Faturamento_Bruto"].replace(0, pd.NA)
    # META_CMV_PERCENT vem como inteiro percentual (30 = 30%) — precisa /100 para comparar
    # com CMV_Percent (fração). NaN = sem meta cadastrada (nunca preenchida com fillna).
    merged["Meta_CMV_Percent"] = pd.to_numeric(merged["META_CMV_PERCENT"], errors="coerce") / 100.0
    merged["Delta_CMV_PP"] = merged["CMV_Percent"] - merged["Meta_CMV_Percent"]

    merged = merged.sort_values("Faturamento_Bruto", ascending=False).reset_index(drop=True)

    total = float(merged["Faturamento_Bruto"].sum())
    cumsum, abc = 0.0, []
    for v in merged["Faturamento_Bruto"]:
        cumsum += float(v)
        ratio = cumsum / total if total else 1.0
        abc.append("A" if ratio <= 0.70 else "B" if ratio <= 0.90 else "C")
    merged["ABC"] = abc

    # Coluna de conveniência para a UI (badge/filtro por status na página) — não existe no
    # script Mini_Gabu (lá as 3 flags ficam em colunas separadas no Excel).
    def _status(row) -> str:
        if row["Ficha_Ambigua"]:
            return "⚠️ Ficha Ambígua"
        if row["Sem_Ficha_Tecnica"]:
            return "🚫 Sem Ficha Técnica"
        if row["Sem_Preco_Ficha"]:
            return "❓ Sem Preço"
        return "✅ OK"
    merged["Status"] = merged.apply(_status, axis=1)

    return merged


def montar_painel_insumos(df_comp_c: pd.DataFrame, df_fichas: pd.DataFrame) -> pd.DataFrame:
    if df_comp_c.empty:
        return df_comp_c
    fichas = df_fichas[["ID_Ficha_Tecnica", "Ficha_Tecnica"]].copy() if not df_fichas.empty else pd.DataFrame(columns=["ID_Ficha_Tecnica", "Ficha_Tecnica"])
    df = df_comp_c.merge(fichas, on="ID_Ficha_Tecnica", how="left")
    df["Ficha_Tecnica"] = df["Ficha_Tecnica"].fillna("—")
    df["Unidade_Medida_Nome"] = df["Unidade_Medida"].apply(_unidade_medida_nome)
    return df.sort_values(["Ficha_Tecnica", "Insumo"]).reset_index(drop=True)


def montar_painel_producao(df_comp_c: pd.DataFrame, df_fichas: pd.DataFrame) -> pd.DataFrame:
    if df_comp_c.empty:
        return df_comp_c
    fichas = df_fichas[["ID_Ficha_Tecnica", "Ficha_Tecnica"]].copy() if not df_fichas.empty else pd.DataFrame(columns=["ID_Ficha_Tecnica", "Ficha_Tecnica"])
    df = df_comp_c.merge(fichas, on="ID_Ficha_Tecnica", how="left")
    df["Ficha_Tecnica"] = df["Ficha_Tecnica"].fillna("—")
    df["Unidade_Medida_Nome"] = df["Unidade_Medida"].apply(_unidade_medida_nome)
    return df.sort_values(["Ficha_Tecnica", "Item_Producao"]).reset_index(drop=True)
