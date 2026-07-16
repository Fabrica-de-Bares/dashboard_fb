import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
from utils.functions.general_functions import config_sidebar, format_brazilian_without_decimal
from utils.functions.controladoria_planejamento_anual import *
from utils.functions.controladoria_quarterday import formatar_moeda_br
from utils.components import seletor_ano, input_selecao_casas, button_download
from utils.queries_controladoria import *
from utils.queries_pessoas import *


pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Headcount de Pessoas e Remuneração",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title("👥 Headcount de Pessoas e Remuneração")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma - Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
with col2:
    ano = seletor_ano(2026, 2026, 'ano')
st.divider()


nomes_meses = { # Renomeia meses
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
nomes_meses_inv = {nome: numero for numero, nome in nomes_meses.items()}

# Recupera dados
df_headcount_pessoas = GET_HEADCOUNT_PESSOAS()
df_headcount_pessoas = df_headcount_pessoas[(df_headcount_pessoas['ID Casa'] == id_casa) & (df_headcount_pessoas['Ano'] == ano)].copy()

if df_headcount_pessoas.empty:
    st.warning('Sem dados para exibir.')
    st.stop()

df_num_colaboradores_raw = df_headcount_pessoas[df_headcount_pessoas['Tipo Dado'] == 'Nº COLABORADORES'].copy()
df_num_colaboradores_raw['Valor'] = pd.to_numeric(df_num_colaboradores_raw['Valor'], errors='coerce')

df_remuneracao_raw = df_headcount_pessoas[df_headcount_pessoas['Tipo Dado'] == 'REMUNERAÇÃO'].copy()
df_remuneracao_raw['Valor'] = pd.to_numeric(df_remuneracao_raw['Valor'], errors='coerce')

# Colunas de mês existentes na base (independe do Modelo Contrato)
colunas_meses = [nomes_meses[m] for m in sorted(df_num_colaboradores_raw['Mês'].unique())]

df_funcionarios_ativos_mes = GET_FUNCIONARIOS_ATIVOS_POR_MES(id_casa, ano)
df_remuneracao_real_mes = GET_REMUNERACAO_REAL_POR_MES(id_casa, ano)
df_remuneracao_real_mes['Salário'] = pd.to_numeric(df_remuneracao_real_mes['Salário'], errors='coerce')

hoje = datetime.now()
ANO_INICIO_BASE, MES_INICIO_BASE = 2026, 6 # Início da base de pessoas: Junho/2026
if ano < ANO_INICIO_BASE:
    mes_inicio = 13 # Nenhum mês disponível
elif ano == ANO_INICIO_BASE:
    mes_inicio = MES_INICIO_BASE
else:
    mes_inicio = 1
mes_limite = 12 if ano < hoje.year else hoje.month if ano == hoje.year else 0
colunas_meses_efetivo = [col for col in colunas_meses if mes_inicio <= nomes_meses_inv[col] <= mes_limite]

# Um cargo CLT é diferente de um cargo PJ mesmo com o mesmo nome: cada modelo de contrato tem
# sua própria aba (nunca somadas/misturadas entre si)
VARIANTES = [('CLT', 'CLT'), ('PJ', 'PJ')]

# --- Pré-cálculo dos cruzamentos por modelo (CLT / PJ) ---
cruzamentos_headcount_por_modelo = {}
remapeadores_por_modelo = {}
cruzamentos_remuneracao_por_modelo = {}
for modelo_contrato, titulo in VARIANTES:
    _, _, _, df_aprovado_cru = constroi_aprovado(df_num_colaboradores_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo)
    _, _, _, df_efetivo_cru = constroi_efetivo(df_funcionarios_ativos_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo)
    remapear, df_aprovado_remap, df_efetivo_remap = remapeia_headcount(df_aprovado_cru, df_efetivo_cru)
    cruzamentos_headcount_por_modelo[modelo_contrato] = (df_aprovado_remap, df_efetivo_remap)
    remapeadores_por_modelo[modelo_contrato] = remapear

    if not df_remuneracao_raw.empty:
        _, _, _, df_orcado_rem_cru = constroi_remuneracao_orcada(df_remuneracao_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo)
        df_orcado_rem, df_real_rem = remapeia_remuneracao(remapear, df_orcado_rem_cru, df_remuneracao_real_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo)
        cruzamentos_remuneracao_por_modelo[modelo_contrato] = (df_orcado_rem, df_real_rem)

# --- Combinação "CLT+PJ", só pras abas de comparação ---
# Headcount e custo (R$) são grandezas aditivas: soma direta. A remuneração média combinada
# NÃO é a média simples entre CLT e PJ — é derivada como custo combinado / headcount
# combinado (média ponderada pelo tamanho de cada grupo), pra manter Custo = Headcount x
# Remuneração consistente também na visão combinada.
MODELO_COMBINADO = 'CLT+PJ'
VARIANTES_COMPARACAO = VARIANTES + [(MODELO_COMBINADO, MODELO_COMBINADO)]

if 'CLT' in cruzamentos_headcount_por_modelo and 'PJ' in cruzamentos_headcount_por_modelo:
    df_aprovado_clt, df_efetivo_clt = cruzamentos_headcount_por_modelo['CLT']
    df_aprovado_pj, df_efetivo_pj = cruzamentos_headcount_por_modelo['PJ']

    todos_cargos_combinado = df_aprovado_clt.index.union(df_efetivo_clt.index).union(df_aprovado_pj.index).union(df_efetivo_pj.index)
    if 'CLT' in cruzamentos_remuneracao_por_modelo and 'PJ' in cruzamentos_remuneracao_por_modelo:
        df_orcado_sal_clt, df_real_sal_clt = cruzamentos_remuneracao_por_modelo['CLT']
        df_orcado_sal_pj, df_real_sal_pj = cruzamentos_remuneracao_por_modelo['PJ']
        todos_cargos_combinado = todos_cargos_combinado.union(df_orcado_sal_clt.index).union(df_orcado_sal_pj.index)

    df_aprovado_clt = df_aprovado_clt.reindex(todos_cargos_combinado).fillna(0)
    df_efetivo_clt = df_efetivo_clt.reindex(todos_cargos_combinado).fillna(0)
    df_aprovado_pj = df_aprovado_pj.reindex(todos_cargos_combinado).fillna(0)
    df_efetivo_pj = df_efetivo_pj.reindex(todos_cargos_combinado).fillna(0)

    df_aprovado_combinado = df_aprovado_clt + df_aprovado_pj
    df_efetivo_combinado = df_efetivo_clt + df_efetivo_pj
    cruzamentos_headcount_por_modelo[MODELO_COMBINADO] = (df_aprovado_combinado, df_efetivo_combinado)

    if 'CLT' in cruzamentos_remuneracao_por_modelo and 'PJ' in cruzamentos_remuneracao_por_modelo:
        df_orcado_sal_clt = df_orcado_sal_clt.reindex(todos_cargos_combinado)
        df_real_sal_clt = df_real_sal_clt.reindex(todos_cargos_combinado)
        df_orcado_sal_pj = df_orcado_sal_pj.reindex(todos_cargos_combinado)
        df_real_sal_pj = df_real_sal_pj.reindex(todos_cargos_combinado)

        custo_orcado_clt = (df_aprovado_clt * df_orcado_sal_clt).where(df_aprovado_clt != 0, 0)
        custo_orcado_pj = (df_aprovado_pj * df_orcado_sal_pj).where(df_aprovado_pj != 0, 0)
        custo_orcado_combinado = custo_orcado_clt.fillna(0) + custo_orcado_pj.fillna(0)

        custo_real_clt = (df_efetivo_clt * df_real_sal_clt).where(df_efetivo_clt != 0, 0)
        custo_real_pj = (df_efetivo_pj * df_real_sal_pj).where(df_efetivo_pj != 0, 0)
        custo_real_combinado = custo_real_clt.fillna(0) + custo_real_pj.fillna(0)

        df_orcado_sal_combinado = custo_orcado_combinado / df_aprovado_combinado.replace(0, pd.NA)
        df_real_sal_combinado = custo_real_combinado / df_efetivo_combinado.replace(0, pd.NA)
        cruzamentos_remuneracao_por_modelo[MODELO_COMBINADO] = (df_orcado_sal_combinado, df_real_sal_combinado)

# --- Impacto Financeiro: pré-calcula Custo/Efeitos por modelo (CLT / PJ / combinado) ---
# No combinado, Custo Orçado/Real e os efeitos (Headcount/Remuneração) são somados
# diretamente de CLT+PJ, em vez de recalculados a partir de uma taxa média "blended" —
# isso evita um efeito mix artificial que faria a decomposição combinada não bater com a
# soma das decomposições de CLT e PJ, mesmo a diferença total batendo.
impacto_por_modelo = {}
for modelo_contrato, _titulo in VARIANTES:
    if modelo_contrato not in cruzamentos_headcount_por_modelo or modelo_contrato not in cruzamentos_remuneracao_por_modelo:
        continue
    df_aprovado_m, df_efetivo_m = cruzamentos_headcount_por_modelo[modelo_contrato]
    df_orcado_sal_m, df_real_sal_m = cruzamentos_remuneracao_por_modelo[modelo_contrato]
    todos_cargos_m = df_aprovado_m.index.union(df_efetivo_m.index).union(df_orcado_sal_m.index).union(df_real_sal_m.index)
    df_aprovado_m = df_aprovado_m.reindex(todos_cargos_m).fillna(0)
    df_efetivo_m = df_efetivo_m.reindex(todos_cargos_m).fillna(0)
    df_orcado_sal_m = df_orcado_sal_m.reindex(todos_cargos_m)
    df_real_sal_m = df_real_sal_m.reindex(todos_cargos_m)
    _, custo_orcado_m, custo_real_m, efeito_hc_m, efeito_rem_m = monta_impacto_financeiro(
        df_aprovado_m, df_efetivo_m, df_orcado_sal_m, df_real_sal_m, colunas_meses_efetivo
    )
    impacto_por_modelo[modelo_contrato] = {
        'aprovado': df_aprovado_m,
        'efetivo': df_efetivo_m,
        'custo_orcado': custo_orcado_m,
        'custo_real': custo_real_m,
        'efeito_headcount': efeito_hc_m,
        'efeito_remuneracao': efeito_rem_m,
    }

if 'CLT' in impacto_por_modelo and 'PJ' in impacto_por_modelo:
    todos_cargos_impacto_comb = impacto_por_modelo['CLT']['custo_orcado'].index.union(impacto_por_modelo['PJ']['custo_orcado'].index)

    def _soma_impacto(chave):
        a = impacto_por_modelo['CLT'][chave].reindex(todos_cargos_impacto_comb).fillna(0)
        b = impacto_por_modelo['PJ'][chave].reindex(todos_cargos_impacto_comb).fillna(0)
        return a + b

    impacto_por_modelo[MODELO_COMBINADO] = {
        chave: _soma_impacto(chave)
        for chave in ('aprovado', 'efetivo', 'custo_orcado', 'custo_real', 'efeito_headcount', 'efeito_remuneracao')
    }


tab_impacto_financeiro, tab_comparativo, tab_aprovado, tab_efetivo, tab_remuneracao_comparativo, tab_remuneracao_orcada, tab_remuneracao_real = st.tabs([
    '📊 Impacto Financeiro',
    '👥 Headcount Aprovado x Efetivo', 'Headcount Aprovado', 'Headcount Efetivo',
    '💰 Remuneração Orçada x Real', 'Remuneração Orçada', 'Remuneração Real'
])

with tab_impacto_financeiro:
    if df_remuneracao_raw.empty:
        st.info('Sem dados de remuneração para exibir.')
    else:
        sub_tab_clt, sub_tab_pj, sub_tab_combinado = st.tabs(['CLT', 'PJ', 'CLT+PJ'])
        for (modelo_contrato, titulo), sub_tab in zip(VARIANTES_COMPARACAO, [sub_tab_clt, sub_tab_pj, sub_tab_combinado]):
            with sub_tab:
                if modelo_contrato not in impacto_por_modelo:
                    st.info(f'Sem dados de {titulo} pra montar o impacto financeiro.')
                    continue

                if not colunas_meses_efetivo:
                    st.info('Sem meses disponíveis para essa análise.')
                    continue

                dados_impacto = impacto_por_modelo[modelo_contrato]
                df_aprovado_impacto = dados_impacto['aprovado']
                df_efetivo_impacto = dados_impacto['efetivo']
                df_custo_orcado = dados_impacto['custo_orcado']
                df_custo_real = dados_impacto['custo_real']
                df_efeito_headcount = dados_impacto['efeito_headcount']
                df_efeito_remuneracao = dados_impacto['efeito_remuneracao']

                # Monta a tabela comparativa (Orçado/Real/Diferença) a partir do custo já
                # pronto (somado direto no combinado, calculado por monta_impacto_financeiro no CLT/PJ)
                df_diferenca_custo = df_custo_orcado.fillna(0) - df_custo_real.fillna(0)
                df_comparativo_impacto = pd.concat(
                    {'Orçado': df_custo_orcado, 'Real': df_custo_real, 'Diferença': df_diferenca_custo}, axis=1
                ).swaplevel(axis=1)
                colunas_comparativo_impacto = pd.MultiIndex.from_product([colunas_meses_efetivo, ['Orçado', 'Real', 'Diferença']])
                df_comparativo_impacto = df_comparativo_impacto[colunas_comparativo_impacto]
                for col in colunas_comparativo_impacto:
                    df_comparativo_impacto[col] = pd.to_numeric(df_comparativo_impacto[col], errors='coerce')
                df_comparativo_impacto.index.name = 'CARGO'
                df_comparativo_impacto = df_comparativo_impacto.reset_index()

                col1, col_download, col2 = st.columns([3, 1, 1], vertical_alignment='center')
                with col1:
                    st.subheader(f'Impacto Financeiro {titulo} (Headcount x Remuneração) - {ano}', help='Custo = Headcount x Remuneração média, por cargo e mês (Orçado = Aprovado x Salário Orçado; Real = Efetivo x Salário Real).')
                with col2:
                    remover_cargos_sem_dados_impacto = st.toggle('Remover cargos sem dados', key=f'toggle_remover_cargos_sem_dados_impacto_{modelo_contrato.lower()}', value=False)

                df_comparativo_impacto_exibicao = df_comparativo_impacto
                if remover_cargos_sem_dados_impacto:
                    cargos_com_dados_impacto = df_custo_orcado.index[
                        (df_custo_orcado.sum(axis=1, skipna=True) != 0) | (df_custo_real.sum(axis=1, skipna=True) != 0)
                    ]
                    df_comparativo_impacto_exibicao = df_comparativo_impacto_exibicao[df_comparativo_impacto_exibicao['CARGO'].isin(cargos_com_dados_impacto)]

                colunas_numericas_impacto = [col for col in df_comparativo_impacto_exibicao.columns if col != ('CARGO', '')]
                linha_total_impacto = df_comparativo_impacto_exibicao[colunas_numericas_impacto].sum()
                linha_total_impacto[('CARGO', '')] = 'TOTAL'
                df_comparativo_impacto_exibicao = pd.concat(
                    [df_comparativo_impacto_exibicao, linha_total_impacto.to_frame().T],
                    ignore_index=True
                )

                colunas_diferenca_impacto = [col for col in df_comparativo_impacto_exibicao.columns if col[1] == 'Diferença']
                cores_diferenca_impacto = df_comparativo_impacto_exibicao[colunas_diferenca_impacto].map(destaca_diferenca)

                df_comparativo_impacto_exibida = df_comparativo_impacto_exibicao.copy()
                for col in colunas_numericas_impacto:
                    df_comparativo_impacto_exibida[col] = df_comparativo_impacto_exibida[col].apply(
                        lambda x: '' if pd.isna(x) or x == 0 else formatar_moeda_br(x)
                    )

                df_comparativo_impacto_styled = (
                    df_comparativo_impacto_exibida.style
                    .apply(lambda _: cores_diferenca_impacto, axis=None, subset=colunas_diferenca_impacto)
                    .apply(destaca_linha_total, axis=1)
                )

                with col_download:
                    button_download(df_comparativo_impacto_exibicao, f'Impacto_Financeiro_{titulo}_{casa}_{ano}', f'download_impacto_financeiro_{modelo_contrato.lower()}')

                st.dataframe(
                    df_comparativo_impacto_styled,
                    hide_index=True,
                    width='stretch',
                    height=(len(df_comparativo_impacto_exibicao) + 1) * 35
                )

                st.divider()
                st.markdown('##### Análise do impacto financeiro por mês')

                df_dif_custo_por_cargo = df_comparativo_impacto_exibicao[df_comparativo_impacto_exibicao['CARGO'] != 'TOTAL'].set_index('CARGO').xs('Diferença', axis=1, level=1)

                totais_custo_orcado_mes = df_custo_orcado.loc[df_dif_custo_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
                totais_custo_real_mes = df_custo_real.loc[df_dif_custo_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
                totais_diferenca_custo_mes = totais_custo_orcado_mes - totais_custo_real_mes
                totais_efeito_headcount_mes = df_efeito_headcount.loc[df_dif_custo_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
                totais_efeito_remuneracao_mes = df_efeito_remuneracao.loc[df_dif_custo_por_cargo.index, colunas_meses_efetivo].sum(axis=0)

                mes_analise_impacto = st.selectbox(
                    'Mês de referência para a análise',
                    colunas_meses_efetivo,
                    index=len(colunas_meses_efetivo) - 1,
                    key=f'selectbox_mes_analise_impacto_{modelo_contrato.lower()}'
                )
                diferenca_custo_por_cargo_no_mes = df_dif_custo_por_cargo[mes_analise_impacto].dropna().sort_values()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        f'Diferença de custo em {mes_analise_impacto}',
                        f'R$ {formatar_moeda_br(totais_diferenca_custo_mes.loc[mes_analise_impacto])}',
                        help='Custo Orçado - Custo Real no mês selecionado (positivo = economia, negativo = estouro do orçado)'
                    )
                with col2:
                    st.metric(
                        f'Efeito Headcount em {mes_analise_impacto}',
                        f'R$ {formatar_moeda_br(totais_efeito_headcount_mes.loc[mes_analise_impacto])}',
                        help='Parte da diferença explicada por ter mais/menos gente que o aprovado (positivo = menos gente que o aprovado)'
                    )
                with col3:
                    st.metric(
                        f'Efeito Remuneração em {mes_analise_impacto}',
                        f'R$ {formatar_moeda_br(totais_efeito_remuneracao_mes.loc[mes_analise_impacto])}',
                        help='Parte da diferença explicada pelo salário médio real estar acima/abaixo do orçado (positivo = salário real abaixo do orçado)'
                    )

                options_totais_custo_mes = {
                    "color": ["#2a78d6", "#1baf7a"],
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Orçado", "Real"], "top": "0%"},
                    "grid": {"top": "18%", "left": "90", "right": "4%", "bottom": "3%", "containLabel": True},
                    "xAxis": [{"type": "category", "data": colunas_meses_efetivo}],
                    "yAxis": [{"type": "value", "name": "Custo (R$)", "nameLocation": "middle", "nameGap": 80}],
                    "series": [
                        {"name": "Orçado", "type": "bar", "data": totais_custo_orcado_mes.round(0).astype(int).tolist()},
                        {"name": "Real", "type": "bar", "data": totais_custo_real_mes.round(0).astype(int).tolist()},
                    ],
                }
                st.caption('Custo Orçado x Custo Real — total de todos os cargos, por mês')
                st_echarts(options=options_totais_custo_mes, height="350px", key=f'echarts_totais_custo_orcado_real_mes_{modelo_contrato.lower()}')

                options_decomposicao_impacto = {
                    "color": ["#2a78d6", "#8e5cd9"],
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["Efeito Headcount", "Efeito Remuneração"], "top": "0%"},
                    "grid": {"top": "18%", "left": "90", "right": "4%", "bottom": "3%", "containLabel": True},
                    "xAxis": [{"type": "category", "data": colunas_meses_efetivo}],
                    "yAxis": [{"type": "value", "name": "Impacto (R$)", "nameLocation": "middle", "nameGap": 80}],
                    "series": [
                        {"name": "Efeito Headcount", "type": "bar", "stack": "impacto", "data": totais_efeito_headcount_mes.round(0).astype(int).tolist()},
                        {"name": "Efeito Remuneração", "type": "bar", "stack": "impacto", "data": totais_efeito_remuneracao_mes.round(0).astype(int).tolist()},
                    ],
                }
                st.caption('Decomposição da diferença de custo (positivo = economia): quanto vem de ter mais/menos gente (Headcount) x quanto vem do salário médio estar acima/abaixo do orçado (Remuneração)')
                st_echarts(options=options_decomposicao_impacto, height="350px", key=f'echarts_decomposicao_impacto_mes_{modelo_contrato.lower()}')

                dados_diferenca_custo_cargo = [
                    {"value": int(round(valor)), "itemStyle": {"color": "#2a78d6" if valor >= 0 else "#e34948"}}
                    for valor in diferenca_custo_por_cargo_no_mes
                ]
                options_diferenca_custo_cargo = {
                    "tooltip": {"trigger": "axis"},
                    "grid": {"left": "90", "right": "4%", "bottom": "15%", "containLabel": True},
                    "xAxis": [{
                        "type": "category",
                        "data": diferenca_custo_por_cargo_no_mes.index.tolist(),
                        "axisLabel": {"rotate": 45, "fontSize": 10},
                    }],
                    "yAxis": [{"type": "value", "name": "Diferença (R$)", "nameLocation": "middle", "nameGap": 80}],
                    "series": [{"name": "Diferença", "type": "bar", "data": dados_diferenca_custo_cargo}],
                }
                st.caption(f'Diferença de custo por cargo em {mes_analise_impacto} (Orçado - Real, R$; positivo = economia) — clique numa barra pra ver o detalhamento')
                events_diferenca_custo_cargo = {
                    "click": "function(params) { return params.name; }"
                }
                resultado_clique_impacto = st_echarts(
                    options=options_diferenca_custo_cargo,
                    events=events_diferenca_custo_cargo,
                    height="400px",
                    key=f'echarts_diferenca_custo_por_cargo_{modelo_contrato.lower()}'
                )
                # st_echarts embrulha o retorno do evento num objeto tipo-dict (chave 'chart_event')
                # nessa versão do Streamlit; em versões mais antigas o retorno já vem "cru"
                cargo_selecionado_impacto = (
                    resultado_clique_impacto.get('chart_event')
                    if hasattr(resultado_clique_impacto, 'get')
                    else resultado_clique_impacto
                )

                if not cargo_selecionado_impacto:
                    st.info('Clique numa barra do gráfico acima pra ver as pessoas do cargo e a remuneração real de cada uma comparada à orçada.')
                else:
                    st.markdown(f'##### Detalhamento — {cargo_selecionado_impacto} em {mes_analise_impacto}')

                    mes_numero_impacto = nomes_meses_inv[mes_analise_impacto]
                    # Salário orçado médio pra referência no detalhamento — no combinado (CLT+PJ)
                    # é a média ponderada pelo headcount (cruzamentos_remuneracao_por_modelo),
                    # só pra exibição; o Custo/Efeitos acima já são somas diretas de CLT+PJ
                    df_orcado_sal_ref, _ = cruzamentos_remuneracao_por_modelo[modelo_contrato]
                    salario_orcado_cargo = (
                        df_orcado_sal_ref.loc[cargo_selecionado_impacto, mes_analise_impacto]
                        if cargo_selecionado_impacto in df_orcado_sal_ref.index else pd.NA
                    )
                    aprovado_hc_cargo = (
                        df_aprovado_impacto.loc[cargo_selecionado_impacto, mes_analise_impacto]
                        if cargo_selecionado_impacto in df_aprovado_impacto.index else pd.NA
                    )
                    efetivo_hc_cargo = (
                        df_efetivo_impacto.loc[cargo_selecionado_impacto, mes_analise_impacto]
                        if cargo_selecionado_impacto in df_efetivo_impacto.index else pd.NA
                    )

                    # Remapeia o cargo das pessoas com o remapeador do modelo, pra bater com o
                    # nome-base usado no cruzamento (níveis I/II/III já unificados). Na aba
                    # combinada (CLT+PJ) junta as pessoas dos dois modelos, cada uma remapeada
                    # com o remapeador do seu próprio modelo.
                    if modelo_contrato == MODELO_COMBINADO:
                        partes_pessoas = []
                        for m in ('CLT', 'PJ'):
                            parte = df_remuneracao_real_mes[df_remuneracao_real_mes['Vínculo'] == m].copy()
                            parte['Cargo'] = parte['Cargo'].str.upper().apply(remapeadores_por_modelo[m])
                            partes_pessoas.append(parte)
                        df_pessoas_filtrado = pd.concat(partes_pessoas, ignore_index=True) if partes_pessoas else df_remuneracao_real_mes.iloc[0:0].copy()
                    else:
                        remapear_pessoas = remapeadores_por_modelo[modelo_contrato]
                        df_pessoas_filtrado = df_remuneracao_real_mes[df_remuneracao_real_mes['Vínculo'] == modelo_contrato].copy()
                        df_pessoas_filtrado['Cargo'] = df_pessoas_filtrado['Cargo'].str.upper().apply(remapear_pessoas)

                    df_pessoas_cargo_mes = df_pessoas_filtrado[
                        (df_pessoas_filtrado['Cargo'] == cargo_selecionado_impacto) &
                        (df_pessoas_filtrado['MES'] == mes_numero_impacto)
                    ][['CPF', 'NOME', 'Salário']].copy()
                    df_pessoas_cargo_mes['Salário Orçado (média do cargo)'] = salario_orcado_cargo
                    df_pessoas_cargo_mes['Diferença Salário'] = salario_orcado_cargo - df_pessoas_cargo_mes['Salário']
                    df_pessoas_cargo_mes['Headcount Aprovado'] = aprovado_hc_cargo
                    df_pessoas_cargo_mes['Headcount Efetivo'] = efetivo_hc_cargo
                    df_pessoas_cargo_mes = df_pessoas_cargo_mes.rename(columns={'Salário': 'Salário Real'})
                    df_pessoas_cargo_mes_download = df_pessoas_cargo_mes.copy()

                    for col in ['Salário Real', 'Salário Orçado (média do cargo)', 'Diferença Salário']:
                        df_pessoas_cargo_mes[col] = df_pessoas_cargo_mes[col].apply(
                            lambda x: '' if pd.isna(x) else formatar_moeda_br(x)
                        )
                    for col in ['Headcount Aprovado', 'Headcount Efetivo']:
                        df_pessoas_cargo_mes[col] = df_pessoas_cargo_mes[col].apply(
                            lambda x: '' if pd.isna(x) else format_brazilian_without_decimal(x)
                        )

                    _, col_download_impacto = st.columns([5, 1])
                    with col_download_impacto:
                        button_download(
                            df_pessoas_cargo_mes_download,
                            f'Detalhamento_Impacto_{titulo}_{cargo_selecionado_impacto}_{mes_analise_impacto}_{ano}',
                            f'download_detalhamento_impacto_{modelo_contrato.lower()}'
                        )
                    st.dataframe(df_pessoas_cargo_mes, hide_index=True, width='stretch')

with tab_comparativo:
    sub_tab_clt, sub_tab_pj, sub_tab_combinado = st.tabs(['CLT', 'PJ', 'CLT+PJ'])
    for (modelo_contrato, titulo), sub_tab in zip(VARIANTES_COMPARACAO, [sub_tab_clt, sub_tab_pj, sub_tab_combinado]):
        with sub_tab:
            if modelo_contrato not in cruzamentos_headcount_por_modelo:
                st.info(f'Sem dados de {titulo} pra montar o comparativo.')
                continue
            df_aprovado_cruzamento, df_efetivo_cruzamento = cruzamentos_headcount_por_modelo[modelo_contrato]

            if not colunas_meses_efetivo or df_aprovado_cruzamento.empty:
                st.info('Sem meses/dados disponíveis pra essa análise.')
                continue

            df_comparativo_headcount = monta_cruzamento(df_aprovado_cruzamento, df_efetivo_cruzamento, 'Aprovado', 'Efetivo', colunas_meses_efetivo)
            for col in pd.MultiIndex.from_product([colunas_meses_efetivo, ['Aprovado', 'Efetivo', 'Diferença']]):
                df_comparativo_headcount[col] = pd.to_numeric(df_comparativo_headcount[col], errors='coerce')

            col1, col_download, col2 = st.columns([3, 1, 1], vertical_alignment='center')
            with col1:
                st.subheader(f'Headcount Aprovado x Efetivo {titulo} - {ano}')
            with col2:
                remover_cargos_sem_dados = st.toggle('Remover cargos sem dados', key=f'toggle_remover_cargos_sem_dados_{modelo_contrato.lower()}', value=False)

            df_comparativo_headcount_exibicao = df_comparativo_headcount
            if remover_cargos_sem_dados:
                cargos_com_dados = df_aprovado_cruzamento.index[
                    (df_aprovado_cruzamento.sum(axis=1) != 0) | (df_efetivo_cruzamento.sum(axis=1) != 0)
                ]
                df_comparativo_headcount_exibicao = df_comparativo_headcount_exibicao[df_comparativo_headcount_exibicao['CARGO'].isin(cargos_com_dados)]

            # Adiciona linha de total
            colunas_numericas_comparativo = [col for col in df_comparativo_headcount_exibicao.columns if col != ('CARGO', '')]
            linha_total_comparativo = df_comparativo_headcount_exibicao[colunas_numericas_comparativo].sum()
            linha_total_comparativo[('CARGO', '')] = 'TOTAL'
            df_comparativo_headcount_exibicao = pd.concat(
                [df_comparativo_headcount_exibicao, linha_total_comparativo.to_frame().T],
                ignore_index=True
            )
            df_comparativo_headcount_exibicao[colunas_numericas_comparativo] = df_comparativo_headcount_exibicao[colunas_numericas_comparativo].astype(int)

            colunas_diferenca = [col for col in df_comparativo_headcount_exibicao.columns if col[1] == 'Diferença']
            df_comparativo_headcount_styled = (
                df_comparativo_headcount_exibicao.style
                .map(destaca_diferenca, subset=colunas_diferenca)
                .apply(destaca_linha_total, axis=1)
                .format({col: (lambda x: '' if x == 0 else format_brazilian_without_decimal(x)) for col in colunas_numericas_comparativo})
            )

            with col_download:
                button_download(df_comparativo_headcount_exibicao, f'Headcount_Aprovado_x_Efetivo_{titulo}_{casa}_{ano}', f'download_headcount_comparativo_{modelo_contrato.lower()}')

            st.dataframe(
                df_comparativo_headcount_styled,
                hide_index=True,
                width='stretch',
                height=(len(df_comparativo_headcount_exibicao) + 1) * 35
            )

            st.divider()
            st.markdown('##### Análise da diferença de Headcount por mês')

            df_dif_por_cargo = df_comparativo_headcount_exibicao[df_comparativo_headcount_exibicao['CARGO'] != 'TOTAL'].set_index('CARGO').xs('Diferença', axis=1, level=1)
            totais_aprovado_mes = df_aprovado_cruzamento.loc[df_dif_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
            totais_efetivo_mes = df_efetivo_cruzamento.loc[df_dif_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
            totais_diferenca_mes = totais_efetivo_mes - totais_aprovado_mes

            mes_analise = st.selectbox(
                'Mês de referência para a análise',
                colunas_meses_efetivo,
                index=len(colunas_meses_efetivo) - 1,
                key=f'selectbox_mes_analise_{modelo_contrato.lower()}'
            )
            diferenca_por_cargo_no_mes = df_dif_por_cargo[mes_analise].sort_values()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    f'Diferença em {mes_analise}',
                    int(totais_diferenca_mes.loc[mes_analise]),
                    help='Efetivo - Aprovado no mês selecionado (positivo = acima do aprovado)'
                )
            with col2:
                if not diferenca_por_cargo_no_mes.empty and diferenca_por_cargo_no_mes.iloc[0] < 0:
                    st.metric(
                        f'Maior déficit em {mes_analise}',
                        int(diferenca_por_cargo_no_mes.iloc[0]),
                        help='Efetivo - Aprovado (cargo mais abaixo do aprovado)'
                    )
                    st.caption(diferenca_por_cargo_no_mes.index[0])
                else:
                    st.metric(f'Maior déficit em {mes_analise}', 0, help='Nenhum cargo abaixo do aprovado')
                    st.caption('—')
            with col3:
                if not diferenca_por_cargo_no_mes.empty and diferenca_por_cargo_no_mes.iloc[-1] > 0:
                    st.metric(
                        f'Maior excedente em {mes_analise}',
                        int(diferenca_por_cargo_no_mes.iloc[-1]),
                        help='Efetivo - Aprovado (cargo mais acima do aprovado)'
                    )
                    st.caption(diferenca_por_cargo_no_mes.index[-1])
                else:
                    st.metric(f'Maior excedente em {mes_analise}', 0, help='Nenhum cargo acima do aprovado')
                    st.caption('—')

            options_totais_mes = {
                "color": ["#2a78d6", "#1baf7a"],
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["Aprovado", "Efetivo"], "top": "0%"},
                "grid": {"top": "18%", "left": "60", "right": "4%", "bottom": "3%", "containLabel": True},
                "xAxis": [{"type": "category", "data": colunas_meses_efetivo}],
                "yAxis": [{"type": "value", "name": "Nº de Funcionários", "nameLocation": "middle", "nameGap": 40}],
                "series": [
                    {"name": "Aprovado", "type": "bar", "data": totais_aprovado_mes.astype(int).tolist()},
                    {"name": "Efetivo", "type": "bar", "data": totais_efetivo_mes.astype(int).tolist()},
                ],
            }
            st.caption('Aprovado x Efetivo — total de todos os cargos, por mês')
            st_echarts(options=options_totais_mes, height="350px", key=f'echarts_totais_aprovado_efetivo_mes_{modelo_contrato.lower()}')

            dados_diferenca_mes = [
                {"value": int(valor), "itemStyle": {"color": "#2a78d6" if valor >= 0 else "#e34948"}}
                for valor in totais_diferenca_mes
            ]
            options_diferenca_mes = {
                "tooltip": {"trigger": "axis"},
                "grid": {"left": "60", "right": "4%", "bottom": "3%", "containLabel": True},
                "xAxis": [{"type": "category", "data": colunas_meses_efetivo}],
                "yAxis": [{"type": "value", "name": "Diferença", "nameLocation": "middle", "nameGap": 40}],
                "series": [{"name": "Diferença", "type": "bar", "data": dados_diferenca_mes}],
            }
            st.caption('Diferença total (azul = acima do aprovado, vermelho = abaixo)')
            st_echarts(options=options_diferenca_mes, height="350px", key=f'echarts_diferenca_total_mes_{modelo_contrato.lower()}')

            dados_diferenca_cargo = [
                {"value": int(valor), "itemStyle": {"color": "#2a78d6" if valor >= 0 else "#e34948"}}
                for valor in diferenca_por_cargo_no_mes
            ]
            options_diferenca_cargo = {
                "tooltip": {"trigger": "axis"},
                "grid": {"left": "60", "right": "4%", "bottom": "15%", "containLabel": True},
                "xAxis": [{
                    "type": "category",
                    "data": diferenca_por_cargo_no_mes.index.tolist(),
                    "axisLabel": {"rotate": 45, "fontSize": 10},
                }],
                "yAxis": [{"type": "value", "name": "Diferença", "nameLocation": "middle", "nameGap": 40}],
                "series": [{"name": "Diferença", "type": "bar", "data": dados_diferenca_cargo}],
            }
            st.caption(f'Diferença por cargo em {mes_analise} (Efetivo - Aprovado, não acumulado)')
            st_echarts(options=options_diferenca_cargo, height="400px", key=f'echarts_diferenca_por_cargo_{modelo_contrato.lower()}')

with tab_aprovado:
    sub_tab_clt, sub_tab_pj = st.tabs(['CLT', 'PJ'])
    for (modelo_contrato, titulo), sub_tab in zip(VARIANTES, [sub_tab_clt, sub_tab_pj]):
        with sub_tab:
            df_final, df_styled, height, _ = constroi_aprovado(df_num_colaboradores_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo)
            if df_final.empty:
                st.info(f'Não há headcount aprovado com Modelo Contrato = {titulo} pra essa casa/ano.')
                continue
            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.subheader(f'Headcount Aprovado {titulo} - {ano}')
            with col2:
                button_download(df_final, f'Headcount_Aprovado_{titulo}_{casa}_{ano}', f'download_headcount_aprovado_{modelo_contrato.lower()}')
            st.dataframe(df_styled, hide_index=True, width='stretch', height=height)

with tab_efetivo:
    sub_tab_clt, sub_tab_pj = st.tabs(['CLT', 'PJ'])
    for (modelo_contrato, titulo), sub_tab in zip(VARIANTES, [sub_tab_clt, sub_tab_pj]):
        with sub_tab:
            df_headcount_efetivo, df_headcount_efetivo_styled, height_efetivo, _ = constroi_efetivo(df_funcionarios_ativos_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo)
            if df_headcount_efetivo.empty:
                st.info(f'Ainda não há colaboradores com vínculo {titulo} cadastrados no Sinergy pra essa casa/ano.')
                continue

            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.subheader(f'Headcount Efetivo {titulo} - {ano}', help='a partir de junho de 2026, devido à base de pessoas da Sinergy.')
            with col2:
                button_download(df_headcount_efetivo, f'Headcount_Efetivo_{titulo}_{casa}_{ano}', f'download_headcount_efetivo_{modelo_contrato.lower()}')
            st.dataframe(df_headcount_efetivo_styled, hide_index=True, width='stretch', height=height_efetivo)

            # Detalhamento das pessoas ativas por cargo e mês
            st.markdown("##### Detalhamento de funcionários")
            cargos_disponiveis = df_funcionarios_ativos_mes[df_funcionarios_ativos_mes['Vínculo'] == modelo_contrato]
            col1, col2 = st.columns(2)
            with col1:
                mes_selecionado = st.selectbox('Filtrar por mês', colunas_meses_efetivo, key=f'selectbox_mes_{modelo_contrato.lower()}')
            with col2:
                cargos_selecionado = st.multiselect(
                    'Filtrar por cargo',
                    sorted(cargos_disponiveis['Cargo'].unique()),
                    key=f'multiselect_cargo_{modelo_contrato.lower()}'
                )

            if mes_selecionado:
                mes_numero = nomes_meses_inv[mes_selecionado]
                dt_inicio_mes = pd.Timestamp(ano, mes_numero, 1).date()
                dt_fim_mes = (pd.Timestamp(ano, mes_numero, 1) + pd.offsets.MonthEnd(0)).date()
                df_funcionarios_ativos = GET_FUNCIONARIOS_ATIVOS(id_casa, dt_inicio_mes, dt_fim_mes)
                df_funcionarios_ativos = df_funcionarios_ativos[df_funcionarios_ativos['Vínculo'] == modelo_contrato]

                if cargos_selecionado:
                    df_funcionarios_ativos = df_funcionarios_ativos[df_funcionarios_ativos['Cargo'].isin(cargos_selecionado)]

                _, col_download = st.columns([5, 1])
                with col_download:
                    button_download(df_funcionarios_ativos, f'Detalhamento_Funcionarios_{titulo}_{casa}_{mes_selecionado}_{ano}', f'download_detalhamento_funcionarios_{modelo_contrato.lower()}')
                st.dataframe(df_funcionarios_ativos, hide_index=True, width='stretch')

with tab_remuneracao_comparativo:
    if df_remuneracao_raw.empty:
        st.info('Sem dados de remuneração para exibir.')
    else:
        sub_tab_clt, sub_tab_pj, sub_tab_combinado = st.tabs(['CLT', 'PJ', 'CLT+PJ'])
        for (modelo_contrato, titulo), sub_tab in zip(VARIANTES_COMPARACAO, [sub_tab_clt, sub_tab_pj, sub_tab_combinado]):
            with sub_tab:
                if modelo_contrato not in cruzamentos_remuneracao_por_modelo:
                    st.info(f'Sem dados de {titulo} pra montar o comparativo.')
                    continue
                df_orcado_remuneracao_cruzamento, df_real_remuneracao_cruzamento = cruzamentos_remuneracao_por_modelo[modelo_contrato]

                if not colunas_meses_efetivo:
                    st.info('Sem meses disponíveis para essa análise.')
                    continue

                df_comparativo_remuneracao = pd.concat(
                    {
                        'Orçado': df_orcado_remuneracao_cruzamento,
                        'Real': df_real_remuneracao_cruzamento,
                        'Diferença': df_real_remuneracao_cruzamento.fillna(0) - df_orcado_remuneracao_cruzamento.fillna(0)
                    },
                    axis=1
                ).swaplevel(axis=1)
                colunas_comparativo_remuneracao = pd.MultiIndex.from_product([colunas_meses_efetivo, ['Orçado', 'Real', 'Diferença']])
                df_comparativo_remuneracao = df_comparativo_remuneracao[colunas_comparativo_remuneracao]
                for col in colunas_comparativo_remuneracao:
                    df_comparativo_remuneracao[col] = pd.to_numeric(df_comparativo_remuneracao[col], errors='coerce')
                df_comparativo_remuneracao.index.name = 'CARGO'
                df_comparativo_remuneracao = df_comparativo_remuneracao.reset_index()

                col1, col_download, col2 = st.columns([3, 1, 1], vertical_alignment='center')
                with col1:
                    st.subheader(f'Remuneração Orçada x Real {titulo} - {ano}')
                with col2:
                    remover_cargos_sem_dados_remuneracao = st.toggle('Remover cargos sem dados', key=f'toggle_remover_cargos_sem_dados_remuneracao_{modelo_contrato.lower()}', value=False)

                df_comparativo_remuneracao_exibicao = df_comparativo_remuneracao
                if remover_cargos_sem_dados_remuneracao:
                    cargos_com_dados_remuneracao = df_orcado_remuneracao_cruzamento.index[
                        (df_orcado_remuneracao_cruzamento.sum(axis=1, skipna=True) != 0) | (df_real_remuneracao_cruzamento.sum(axis=1, skipna=True) != 0)
                    ]
                    df_comparativo_remuneracao_exibicao = df_comparativo_remuneracao_exibicao[df_comparativo_remuneracao_exibicao['CARGO'].isin(cargos_com_dados_remuneracao)]

                colunas_diferenca_remuneracao = [col for col in df_comparativo_remuneracao_exibicao.columns if col[1] == 'Diferença']
                colunas_numericas_remuneracao = [col for col in df_comparativo_remuneracao_exibicao.columns if col != ('CARGO', '')]

                cores_diferenca_remuneracao = df_comparativo_remuneracao_exibicao[colunas_diferenca_remuneracao].map(destaca_diferenca)

                df_comparativo_remuneracao_exibida = df_comparativo_remuneracao_exibicao.copy()
                for col in colunas_numericas_remuneracao:
                    df_comparativo_remuneracao_exibida[col] = df_comparativo_remuneracao_exibida[col].apply(
                        lambda x: '' if pd.isna(x) or x == 0 else formatar_moeda_br(x)
                    )

                df_comparativo_remuneracao_styled = (
                    df_comparativo_remuneracao_exibida.style
                    .apply(lambda _: cores_diferenca_remuneracao, axis=None, subset=colunas_diferenca_remuneracao)
                )

                with col_download:
                    button_download(df_comparativo_remuneracao_exibicao, f'Remuneracao_Orcada_x_Real_{titulo}_{casa}_{ano}', f'download_remuneracao_comparativo_{modelo_contrato.lower()}')

                st.dataframe(
                    df_comparativo_remuneracao_styled,
                    hide_index=True,
                    width='stretch',
                    height=(len(df_comparativo_remuneracao_exibicao) + 1) * 35
                )

                st.divider()
                st.markdown('##### Análise da diferença de remuneração por mês')

                df_dif_remuneracao_por_cargo = df_comparativo_remuneracao_exibicao.set_index('CARGO').xs('Diferença', axis=1, level=1)

                mes_analise_remuneracao = st.selectbox(
                    'Mês de referência para a análise',
                    colunas_meses_efetivo,
                    index=len(colunas_meses_efetivo) - 1,
                    key=f'selectbox_mes_analise_remuneracao_{modelo_contrato.lower()}'
                )
                diferenca_remuneracao_por_cargo_no_mes = df_dif_remuneracao_por_cargo[mes_analise_remuneracao].dropna().sort_values()

                dados_diferenca_remuneracao_cargo = [
                    {"value": int(round(valor)), "itemStyle": {"color": "#2a78d6" if valor >= 0 else "#e34948"}}
                    for valor in diferenca_remuneracao_por_cargo_no_mes
                ]
                options_diferenca_remuneracao_cargo = {
                    "tooltip": {"trigger": "axis"},
                    "grid": {"left": "80", "right": "4%", "bottom": "15%", "containLabel": True},
                    "xAxis": [{
                        "type": "category",
                        "data": diferenca_remuneracao_por_cargo_no_mes.index.tolist(),
                        "axisLabel": {"rotate": 45, "fontSize": 10},
                    }],
                    "yAxis": [{"type": "value", "name": "Diferença (R$)", "nameLocation": "middle", "nameGap": 60}],
                    "series": [{"name": "Diferença", "type": "bar", "data": dados_diferenca_remuneracao_cargo}],
                }
                st.caption(f'Diferença por cargo em {mes_analise_remuneracao} (Real - Orçado, R$)')
                st_echarts(options=options_diferenca_remuneracao_cargo, height="400px", key=f'echarts_diferenca_remuneracao_por_cargo_{modelo_contrato.lower()}')

with tab_remuneracao_orcada:
    if df_remuneracao_raw.empty:
        st.info('Sem dados de remuneração para exibir.')
    else:
        sub_tab_clt, sub_tab_pj = st.tabs(['CLT', 'PJ'])
        for (modelo_contrato, titulo), sub_tab in zip(VARIANTES, [sub_tab_clt, sub_tab_pj]):
            with sub_tab:
                df_final, df_styled, height, _ = constroi_remuneracao_orcada(df_remuneracao_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo)
                if df_final.empty:
                    st.info(f'Não há remuneração orçada com Modelo Contrato = {titulo} pra essa casa/ano.')
                    continue
                col1, col2 = st.columns([4, 1], vertical_alignment='center')
                with col1:
                    st.subheader(f'Remuneração Orçada {titulo} - {ano}')
                with col2:
                    button_download(df_final, f'Remuneracao_Orcada_{titulo}_{casa}_{ano}', f'download_remuneracao_orcada_{modelo_contrato.lower()}')
                st.dataframe(df_styled, hide_index=True, width='stretch', height=height)

with tab_remuneracao_real:
    sub_tab_clt, sub_tab_pj = st.tabs(['CLT', 'PJ'])
    for (modelo_contrato, titulo), sub_tab in zip(VARIANTES, [sub_tab_clt, sub_tab_pj]):
        with sub_tab:
            df_media_salarial = constroi_remuneracao_real(df_remuneracao_real_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo)
            if df_media_salarial.empty:
                st.info(f'Ainda não há colaboradores com vínculo {titulo} cadastrados no Sinergy pra essa casa/ano.')
                continue

            # Converte pra texto já formatado (célula vazia em vez de NaN), pois o grid do st.dataframe
            # ignora o Styler.format() pra células com NaN de verdade e mostra "None" por conta própria
            df_media_salarial_exibida = df_media_salarial.copy()
            for col in colunas_meses_efetivo:
                df_media_salarial_exibida[col] = df_media_salarial_exibida[col].apply(
                    lambda x: '' if pd.isna(x) or x == 0 else formatar_moeda_br(x)
                )

            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.subheader(f'Remuneração Real {titulo} - {ano}', help='Média salarial por cargo/mês, apurada na folha do Sinergy (com fallback pro mês anterior quando falta ficha financeira do mês).')
            with col2:
                button_download(df_media_salarial, f'Remuneracao_Real_{titulo}_{casa}_{ano}', f'download_remuneracao_real_{modelo_contrato.lower()}')

            st.dataframe(
                df_media_salarial_exibida,
                hide_index=True,
                width='stretch',
                height=(len(df_media_salarial) + 1) * 35
            )

            # Detalhamento das pessoas ativas por cargo e mês
            st.markdown("##### Detalhamento de funcionários")
            pessoas_disponiveis = df_remuneracao_real_mes[df_remuneracao_real_mes['Vínculo'] == modelo_contrato]
            col1, col2 = st.columns(2)
            with col1:
                mes_selecionado_remuneracao = st.selectbox('Filtrar por mês', colunas_meses_efetivo, key=f'selectbox_mes_remuneracao_{modelo_contrato.lower()}')
            with col2:
                cargos_selecionado_remuneracao = st.multiselect(
                    'Filtrar por cargo',
                    sorted(pessoas_disponiveis['Cargo'].unique()),
                    key=f'multiselect_cargo_remuneracao_{modelo_contrato.lower()}'
                )

            if mes_selecionado_remuneracao:
                mes_numero_remuneracao = nomes_meses_inv[mes_selecionado_remuneracao]
                df_funcionarios_salario = df_remuneracao_real_mes[df_remuneracao_real_mes['MES'] == mes_numero_remuneracao].copy()
                df_funcionarios_salario['Referência'] = f'{mes_selecionado_remuneracao}/{ano}'
                df_funcionarios_salario = df_funcionarios_salario[df_funcionarios_salario['Vínculo'] == modelo_contrato]

                if cargos_selecionado_remuneracao:
                    df_funcionarios_salario = df_funcionarios_salario[df_funcionarios_salario['Cargo'].isin(cargos_selecionado_remuneracao)]

                _, col_download = st.columns([5, 1])
                with col_download:
                    button_download(
                        df_funcionarios_salario[['CPF', 'NOME', 'Cargo', 'Referência', 'Salário']],
                        f'Detalhamento_Remuneracao_{titulo}_{casa}_{mes_selecionado_remuneracao}_{ano}',
                        f'download_detalhamento_remuneracao_{modelo_contrato.lower()}'
                    )
                st.dataframe(
                    df_funcionarios_salario[['CPF', 'NOME', 'Cargo', 'Referência', 'Salário']].style.format({'Salário': formatar_moeda_br}),
                    hide_index=True,
                    width='stretch'
                )
