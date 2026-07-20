import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
from utils.functions.general_functions import config_sidebar, format_brazilian_without_decimal
from utils.functions.controladoria_planejamento_anual import *
from utils.components import seletor_ano, input_selecao_casas, button_download
from utils.queries_controladoria import *
from utils.queries_pessoas import *


pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Headcount de Pessoas",
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
    st.title("👥 Headcount de Pessoas")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    lista_casas_retirar = ['Bar Brahma - Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
with col2:
    ano = seletor_ano(2026, 2026, 'ano')
st.divider()

if id_casa == -1:
    df_casas_permitidas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
    lista_ids_casas = tuple(df_casas_permitidas['ID Loja'].unique().tolist())
else:
    lista_ids_casas = (id_casa,)


nomes_meses = { # Renomeia meses
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
nomes_meses_inv = {nome: numero for numero, nome in nomes_meses.items()}

# Recupera dados
df_headcount_pessoas = GET_HEADCOUNT_PESSOAS()

# Para Nº Colaboradores
df_num_colaboradores_raw = df_headcount_pessoas[
    (df_headcount_pessoas['ID Casa'].isin(lista_ids_casas)) &
    (df_headcount_pessoas['Ano'] == ano) &
    (df_headcount_pessoas['Tipo Dado'] == 'Nº COLABORADORES')
].copy()

if df_num_colaboradores_raw.empty:
    st.warning('Sem dados para exibir.')
    st.stop()

df_num_colaboradores_raw['Valor'] = pd.to_numeric(df_num_colaboradores_raw['Valor'], errors='coerce')

# Colunas de mês existentes na base (independe do Modelo Contrato)
colunas_meses = [
    nomes_meses[m] for m in sorted(df_num_colaboradores_raw['Mês'].unique())
]

df_funcionarios_ativos_mes = GET_FUNCIONARIOS_ATIVOS_POR_MES(lista_ids_casas, ano)
# Menor Aprendiz, Estagiário e Diretor s/ FGTS não existem como Modelo Contrato em
# T_HEADCOUNT_PESSOAS (só CLT/PJ) — contabiliza junto com CLT
VINCULOS_REMAP_CLT = {'Menor Aprendiz': 'CLT', 'Estagiário': 'CLT', 'Diretor s/ FGTS': 'CLT'}
df_funcionarios_ativos_mes['Vínculo'] = df_funcionarios_ativos_mes['Vínculo'].replace(VINCULOS_REMAP_CLT)

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

# Pré-calcula, por modelo, os cruzamentos já remapeados (headcount aprovado x efetivo)
cruzamentos_por_modelo = {}
for modelo_contrato, titulo in VARIANTES:
    _, _, _, df_aprovado_cru = constroi_aprovado(df_num_colaboradores_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo)
    _, _, _, df_efetivo_cru = constroi_efetivo(df_funcionarios_ativos_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo)
    df_aprovado_remap, df_efetivo_remap = remapeia_headcount(df_aprovado_cru, df_efetivo_cru)
    cruzamentos_por_modelo[modelo_contrato] = (df_aprovado_remap, df_efetivo_remap)


tab_comparativo, tab_aprovado, tab_efetivo = st.tabs(['👥 Headcount Aprovado x Efetivo', 'Headcount Aprovado', 'Headcount Efetivo'])

with tab_comparativo:
    if not colunas_meses_efetivo:
        st.info('Sem meses disponíveis pra essa análise.')
    else:
        # --- Passo 1: tabelas comparativas (todos os meses, independem do seletor abaixo) ---
        dif_por_cargo_multi_mes_por_modelo = {}
        for modelo_contrato, titulo in VARIANTES:
            if modelo_contrato not in cruzamentos_por_modelo:
                st.info(f'Sem dados de {titulo} pra montar o comparativo.')
                st.divider()
                continue
            df_aprovado_cruzamento, df_efetivo_cruzamento = cruzamentos_por_modelo[modelo_contrato]

            if df_aprovado_cruzamento.empty:
                st.info('Sem dados disponíveis pra essa análise.')
                st.divider()
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
                height=(len(df_comparativo_headcount_exibicao) + 2) * 35
            )

            dif_por_cargo_multi_mes_por_modelo[modelo_contrato] = (
                df_comparativo_headcount_exibicao[df_comparativo_headcount_exibicao['CARGO'] != 'TOTAL']
                .set_index('CARGO').xs('Diferença', axis=1, level=1)
            )

            st.divider()

        # --- Passo 2: seletor de mês, seguido de tudo que depende dele ---
        st.markdown('### Diferença de Headcount por mês')
        mes_analise = st.selectbox(
            'Mês de referência para a análise',
            colunas_meses_efetivo,
            index=len(colunas_meses_efetivo) - 1,
            key='selectbox_mes_analise_comparativo'
        )

        algum_modelo_comparativo_processado = False
        totais_geral_comparativo = {'aprovado': 0, 'efetivo': 0}
        for modelo_contrato, titulo in VARIANTES:
            if modelo_contrato not in dif_por_cargo_multi_mes_por_modelo:
                continue
            algum_modelo_comparativo_processado = True
            st.markdown(f'#### {titulo}')

            df_aprovado_cruzamento, df_efetivo_cruzamento = cruzamentos_por_modelo[modelo_contrato]
            df_dif_por_cargo = dif_por_cargo_multi_mes_por_modelo[modelo_contrato]

            totais_aprovado_mes = df_aprovado_cruzamento.loc[df_dif_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
            totais_efetivo_mes = df_efetivo_cruzamento.loc[df_dif_por_cargo.index, colunas_meses_efetivo].sum(axis=0)
            totais_diferenca_mes = totais_efetivo_mes - totais_aprovado_mes

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

            totais_geral_comparativo['aprovado'] += totais_aprovado_mes.loc[mes_analise]
            totais_geral_comparativo['efetivo'] += totais_efetivo_mes.loc[mes_analise]

            # --- Gráfico "Diferença por cargo" (só desse modelo) ---
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
            st.caption(f'Diferença por cargo {titulo} em {mes_analise} (Efetivo - Aprovado, não acumulado)')
            st_echarts(options=options_diferenca_cargo, height="400px", key=f'echarts_diferenca_por_cargo_{modelo_contrato.lower()}')

            st.divider()

        # --- Total Geral (CLT + PJ) — soma dos totais já calculados por modelo, sem misturar cargos ---
        if algum_modelo_comparativo_processado:
            st.markdown('#### Total (CLT + PJ)')
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f'Aprovado Total em {mes_analise}', int(totais_geral_comparativo['aprovado']), help='Soma de CLT + PJ')
            with col2:
                st.metric(f'Efetivo Total em {mes_analise}', int(totais_geral_comparativo['efetivo']), help='Soma de CLT + PJ')
            with col3:
                st.metric(
                    f'Diferença Total em {mes_analise}',
                    int(totais_geral_comparativo['efetivo'] - totais_geral_comparativo['aprovado']),
                    help='Soma de CLT + PJ — Efetivo - Aprovado no mês selecionado (positivo = acima do aprovado)'
                )

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
            st.markdown("### Detalhamento de funcionários")
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
                df_funcionarios_ativos = GET_FUNCIONARIOS_ATIVOS(lista_ids_casas, dt_inicio_mes, dt_fim_mes)
                df_funcionarios_ativos['Vínculo'] = df_funcionarios_ativos['Vínculo'].replace(VINCULOS_REMAP_CLT)
                df_funcionarios_ativos = df_funcionarios_ativos[df_funcionarios_ativos['Vínculo'] == modelo_contrato]

                if cargos_selecionado:
                    df_funcionarios_ativos = df_funcionarios_ativos[df_funcionarios_ativos['Cargo'].isin(cargos_selecionado)]

                _, col_download = st.columns([5, 1])
                with col_download:
                    button_download(df_funcionarios_ativos, f'Detalhamento_Funcionarios_{titulo}_{casa}_{mes_selecionado}_{ano}', f'download_detalhamento_funcionarios_{modelo_contrato.lower()}')
                st.dataframe(df_funcionarios_ativos, hide_index=True, width='stretch')
