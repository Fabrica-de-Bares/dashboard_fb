import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_planejamento_anual import *
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.functions.general_functions_conciliacao import calcular_datas
from utils.components import button_download, seletor_ano, input_selecao_casas
from utils.queries_controladoria import *
from utils.constants.general_constants import (
    MAPEAMENTO_CATEGORIA_REAL_ORCAMENTO,
    CATEGORIAS_REAL_BENEFICIOS,
    CATEGORIA_REAL_PATROCINIO_RECEITA,
    CATEGORIA_REAL_PATROCINIO_DESPESA,
)


pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Orçamento Operacional",
    page_icon="💰",
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
    st.title("💰 Orçamento Operacional")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Seletor de casa e ano
col1, col2, col3 = st.columns(3)

with col3:
    tipo_valor = st.selectbox("Selecione a informação a visualizar:", ['Orçamento Operacional', 'Histórico Real'])

with col1:
    lista_casas_retirar = ['Blue Note SP (Novo)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Terraço Notie Novo', 'The Cavern - Almoço']
    if tipo_valor == 'Histórico Real':
        # 'Todas as Casas' não é suportado no Histórico Real (depende de um arquivo Base_DRE por casa)
        lista_casas_retirar = lista_casas_retirar + ['Todas as Casas']
        if st.session_state.get('casa') == 'Todas as Casas':
            del st.session_state['casa']  # evita erro do selectbox com valor fora das opções válidas
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')

with col2:
    ano = seletor_ano(2023, 2026, 'ano')
st.divider()

# Recupera dados - Orçamentos, Revisão e Real
df_orcamento_operacional = GET_ORCAMENTO_OPERACIONAL()
df_revisao_orcamento_operacional = GET_REVISAO_ORCAMENTO_OPERACIONAL()
df_historico_real_dre = GET_HISTORICO_REAL_DRE()


def renderiza_orcamento_operacional(df_orcamento_operacional, ano, casa):
    if ano == 2024 or ano == 2023:
        st.warning(f'Sem dados de orçamento de {ano} para o plano de contas Fábrica de Bares (2025).')
        return
    elif casa == 'The Cavern' and (ano < 2026):
        st.warning(f'{casa} sem dados para {ano}.')
        return
    elif casa == 'Bar Brahma - Paulista' and ano < 2026:
        st.warning(f'{casa} sem dados para {ano}.')
        return

    if casa == 'Todas as Casas':
        casas_permitidas = [c['Loja'] for c in st.session_state['casas_permitidas']]
        casas_somar = [c for c in casas_permitidas if c not in lista_casas_retirar]
        filtro_casa = df_orcamento_operacional['Casa'].isin(casas_somar)
    else:
        filtro_casa = df_orcamento_operacional['Casa'] == casa

    df_orcamento_filtrado = df_orcamento_operacional[
        filtro_casa &
        (df_orcamento_operacional['Ano'] == ano)
    ].copy()

    if df_orcamento_filtrado.empty:
        st.info(f'{casa} sem dados para {ano}.')
        return

    df_orcamento_filtrado.drop(columns=['Ano', 'ID Casa'], inplace=True)

    # Nomeia meses
    mapa_meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    df_orcamento_filtrado["Mês"] = df_orcamento_filtrado["Mês"].map(mapa_meses)

    # Faturamento Bruto por casa - usado no cálculo de Receitas/Despesas Financeiras (taxa por casa)
    df_faturamento_por_casa = df_orcamento_filtrado[
        df_orcamento_filtrado['Classificação Contábil 1'] == 'Faturamento Bruto'
    ].pivot_table(index='Casa', columns='Mês', values='Orçamento', aggfunc='sum').fillna(0)
    for col in df_faturamento_por_casa.columns:
        df_faturamento_por_casa[col] = pd.to_numeric(df_faturamento_por_casa[col], errors='coerce').fillna(0)

    # Transforma meses em colunas
    df_orcamento_pivot = df_orcamento_filtrado.pivot_table(
        index=["Classificação Contábil 1", "Classificação Contábil 2"],
        columns="Mês",
        values="Orçamento",
        aggfunc="sum"
    ).reset_index()

    for col in df_orcamento_pivot.columns:
        if col not in ["Classificação Contábil 1", "Classificação Contábil 2"]:
            df_orcamento_pivot[col] = pd.to_numeric(df_orcamento_pivot[col], errors='coerce').fillna(0)

    lista_categorias_dre = [
        'Faturamento Bruto',
        'Desconto sobre Venda',
        'Impostos sobre Venda',
        'Custo Mercadoria Vendida',
        'Custos Artístico Geral',
        'Custos de Eventos',
        'Gorjeta',
        'Deduções sobre Venda',
        'Mão de Obra - PJ',
        'Mão de Obra - Salários',
        'Mão de Obra - Extra',
        'Mão de Obra - Encargos e Provisões',
        'Mão de Obra - Benefícios',
        'Custo de Ocupação',
        'Utilidades',
        'Informática e TI',
        'Manutenção', # Despesas Gerais
        'Marketing',
        'Serviços de Terceiros',
        'Locação de Equipamentos',
        'Sistema de Franquias',
        'Patrocínio',
        'Imposto de Renda',
        'Investimento - CAPEX',
        'Dividendos e Remunerações Variáveis',
        'Endividamento'
    ]

    # Categorias que precisam entrar em df_orcamentos_concatenados (soma/detalhamento) mas não devem
    # aparecer como linha própria no Resumo do Orçamento - entram consolidadas em outra linha calculada
    categorias_ocultas_resumo = ['Dividendos e Remunerações Variáveis', 'Endividamento']

    lista_df_orcamentos = []
    lista_df_orcamentos = loop_prepara_dados_despesas(lista_categorias_dre, df_orcamento_pivot, lista_df_orcamentos)
    df_orcamentos_concatenados = pd.concat(lista_df_orcamentos, ignore_index=True)
    df_orcamentos_concatenados = df_orcamentos_concatenados[['Classificação Contábil 2', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']]
    df_orcamentos_concatenados.rename(columns={'Classificação Contábil 2': 'Categoria'}, inplace=True)

    # Cria colunas de acumulado do ano e trimestres
    colunas_meses = df_orcamentos_concatenados.select_dtypes(include='number').columns
    df_orcamentos_concatenados[f'Ano {ano}'] = df_orcamentos_concatenados[colunas_meses].sum(axis=1)
    df_orcamentos_concatenados['1º Trimestre'] = df_orcamentos_concatenados[['Janeiro', 'Fevereiro', 'Março']].sum(axis=1)
    df_orcamentos_concatenados['2º Trimestre'] = df_orcamentos_concatenados[['Abril', 'Maio', 'Junho']].sum(axis=1)
    df_orcamentos_concatenados['3º Trimestre'] = df_orcamentos_concatenados[['Julho', 'Agosto', 'Setembro']].sum(axis=1)
    df_orcamentos_concatenados['4º Trimestre'] = df_orcamentos_concatenados[['Outubro', 'Novembro', 'Dezembro']].sum(axis=1)

    # Garante todos os meses e cria as mesmas colunas de acumulado do ano e trimestres no Faturamento Bruto por casa
    meses_ano = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    df_faturamento_por_casa = df_faturamento_por_casa.reindex(columns=meses_ano, fill_value=0)
    df_faturamento_por_casa[f'Ano {ano}'] = df_faturamento_por_casa[meses_ano].sum(axis=1)
    df_faturamento_por_casa['1º Trimestre'] = df_faturamento_por_casa[['Janeiro', 'Fevereiro', 'Março']].sum(axis=1)
    df_faturamento_por_casa['2º Trimestre'] = df_faturamento_por_casa[['Abril', 'Maio', 'Junho']].sum(axis=1)
    df_faturamento_por_casa['3º Trimestre'] = df_faturamento_por_casa[['Julho', 'Agosto', 'Setembro']].sum(axis=1)
    df_faturamento_por_casa['4º Trimestre'] = df_faturamento_por_casa[['Outubro', 'Novembro', 'Dezembro']].sum(axis=1)

    # Df apenas com os títulos das seções principais
    df_orcamentos_resumo = df_orcamentos_concatenados[
        df_orcamentos_concatenados['Categoria'].isin(lista_categorias_dre) &
        ~df_orcamentos_concatenados['Categoria'].isin(categorias_ocultas_resumo)
    ].copy()

    # Calcula porcentagens e outros valores
    colunas_numericas = df_orcamentos_resumo.select_dtypes(include='number').columns
    df_orcamentos_resumo = define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_dre, colunas_numericas, 'Orçamento', faturamento_bruto_por_casa=df_faturamento_por_casa)
    height = (len(df_orcamentos_resumo) + 1) * 35 # Define altura sem rolagem

    st.subheader(f'Resumo do Orçamento - {ano}')
    df_orcamentos_resumo_styled = df_orcamentos_resumo.copy()
    df_orcamentos_resumo_styled.loc[df_orcamentos_resumo_styled['Categoria'] == 'Faturamento Bruto', 'Categoria'] = df_orcamentos_resumo_styled['Categoria'].str.upper()
    df_orcamentos_resumo_styled.loc[df_orcamentos_resumo_styled['Categoria'] == 'Imposto de Renda', 'Categoria'] = 'Impostos'
    df_orcamentos_resumo_styled.loc[df_orcamentos_resumo_styled['Categoria'] == 'Investimento - CAPEX', 'Categoria'] = 'CAPEX (Investimentos)'

    linhas_percentual = df_orcamentos_resumo_styled['Categoria'].str.contains('%')
    linhas_moeda = ~linhas_percentual
    colunas_valores = df_orcamentos_resumo_styled.columns.drop('Categoria')

    # Aplica estilos e formatação de porcentagens e moeda
    df_orcamentos_resumo_styled = (
        df_orcamentos_resumo_styled.style
        .format(formatar_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_valores])
        .format(formatar_moeda_br, subset=pd.IndexSlice[linhas_moeda, colunas_valores])
        .apply(highlight_secoes_dre, axis=1)
    )

    df_orcamentos_resumo_styled = df_orcamentos_resumo_styled.apply(highlight_secoes_dre, axis=1) 
    st.dataframe(df_orcamentos_resumo_styled, hide_index=True, width='stretch', height=height)
    st.divider()


    st.subheader('Informações detalhadas por categoria')
    for df in lista_df_orcamentos:
        class_cont = df['Classificação Contábil 2'].iloc[0]
        if class_cont == 'Faturamento Bruto': expandido = True
        else: expandido = False

        with st.expander(f'Visualizar orçamentos de {class_cont}', expanded=expandido):
            df_formatado = df[['Classificação Contábil 2', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']]
            df_formatado = df_formatado[df_formatado['Classificação Contábil 2'] != class_cont].copy()
            df_formatado.rename(columns={'Classificação Contábil 2': 'Categoria'}, inplace=True)

            # Cria colunas de acumulado do ano e trimestres
            colunas_meses = df_formatado.select_dtypes(include='number').columns
            df_formatado[f'Ano {ano}'] = df_formatado[colunas_meses].sum(axis=1)
            df_formatado['1º Trimestre'] = df_formatado[['Janeiro', 'Fevereiro', 'Março']].sum(axis=1)
            df_formatado['2º Trimestre'] = df_formatado[['Abril', 'Maio', 'Junho']].sum(axis=1)
            df_formatado['3º Trimestre'] = df_formatado[['Julho', 'Agosto', 'Setembro']].sum(axis=1)
            df_formatado['4º Trimestre'] = df_formatado[['Outubro', 'Novembro', 'Dezembro']].sum(axis=1)

            # Formata colunas numéricas
            df_formatado = function_format_number_columns(
                df_formatado,
                columns_money=[col for col in df_orcamentos_concatenados if col != 'Categoria'],
            )
            height = (len(df_formatado) + 1) * 35 # Define altura sem rolagem
            st.dataframe(df_formatado, hide_index=True, width='stretch', height=height)

    # # Formata colunas numéricas
    # df_orcamentos_concatenados_fmt = function_format_number_columns(
    #     df_orcamentos_concatenados,
    #     columns_money=[col for col in df_orcamentos_concatenados if col != 'Categoria'],
    # )

    # # Destaca linhas de título
    # df_orcamentos_concatenados_styled = df_orcamentos_concatenados_fmt.style.apply(highlight_titulos_dre, axis=1)
    # height = (len(df_orcamentos_concatenados_fmt) + 1) * 35 # Define altura sem rolagem
    # st.dataframe(df_orcamentos_concatenados_styled, hide_index=True, width='stretch', height=height)


def renderiza_dre_real_revisao(df_historico_real_dre, df_revisao_orcamento_operacional, ano, casa):
    if ano == 2024 or ano == 2023:
        st.warning(f'Sem dados de orçamento de {ano} para o plano de contas Fábrica de Bares (2025).')
        return
    elif casa == 'The Cavern' and (ano < 2026):
        st.warning(f'{casa} sem dados para {ano}.')
        return
    elif casa == 'Bar Brahma - Paulista' and ano < 2026:
        st.warning(f'{casa} sem dados para {ano}.')
        return

    if casa == 'Todas as Casas':
        casas_permitidas = [c['Loja'] for c in st.session_state['casas_permitidas']]
        casas_somar = [c for c in casas_permitidas if c not in lista_casas_retirar]
    else:
        casas_somar = [casa]

    mapa_meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    meses_ano = list(mapa_meses.values())
    categoria_real_faturamento_bruto = MAPEAMENTO_CATEGORIA_REAL_ORCAMENTO['Faturamento Bruto']

    lista_categorias_dre_base = [
        'Faturamento Bruto', 'Desconto sobre Venda', 'Impostos sobre Venda', 'Custo Mercadoria Vendida',
        'Custos Artístico Geral', 'Custos de Eventos', 'Gorjeta', 'Deduções sobre Venda',
        'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões',
        'Mão de Obra - Benefícios', 'Custo de Ocupação', 'Utilidades', 'Informática e TI', 'Manutenção',
        'Marketing', 'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias', 'Patrocínio',
        'Imposto de Renda', 'Investimento - CAPEX', 'Dividendos e Remunerações Variáveis', 'Endividamento'
    ]
    categorias_ocultas_resumo = ['Dividendos e Remunerações Variáveis', 'Endividamento']

    df_historico_real_dre = df_historico_real_dre.copy()
    df_historico_real_dre['Mês'] = pd.to_datetime(df_historico_real_dre['Mês'], errors='coerce')

    # --- Calcula, por casa, a Revisão de Orçamento (todos os meses) e os meses fechados no Real
    # (Faturamento Bruto real != 0) - cada casa pode acabar contribuindo com uma fonte diferente
    # no mesmo mês (ex: Casa A já fechou Agosto, Casa B ainda não) ---
    resultados_por_casa = {}
    for casa_nome in casas_somar:
        df_revisao_filtrado = df_revisao_orcamento_operacional[
            (df_revisao_orcamento_operacional['Casa'] == casa_nome) &
            (df_revisao_orcamento_operacional['Ano'] == ano)
        ].copy()

        df_revisao_valores_casa = None
        if not df_revisao_filtrado.empty:
            df_revisao_filtrado.drop(columns=['Ano', 'ID Casa'], inplace=True)
            df_revisao_filtrado["Mês"] = df_revisao_filtrado["Mês"].map(mapa_meses)

            df_faturamento_por_casa = df_revisao_filtrado[
                df_revisao_filtrado['Classificação Contábil 1'] == 'Faturamento Bruto'
            ].pivot_table(index='Casa', columns='Mês', values='Orçamento', aggfunc='sum').fillna(0)
            df_faturamento_por_casa = df_faturamento_por_casa.reindex(columns=meses_ano, fill_value=0)
            for col in df_faturamento_por_casa.columns:
                df_faturamento_por_casa[col] = pd.to_numeric(df_faturamento_por_casa[col], errors='coerce').fillna(0)

            df_revisao_pivot = df_revisao_filtrado.pivot_table(
                index=["Classificação Contábil 1", "Classificação Contábil 2"],
                columns="Mês",
                values="Orçamento",
                aggfunc="sum"
            ).reset_index()
            for col in df_revisao_pivot.columns:
                if col not in ["Classificação Contábil 1", "Classificação Contábil 2"]:
                    df_revisao_pivot[col] = pd.to_numeric(df_revisao_pivot[col], errors='coerce').fillna(0)

            lista_categorias_dre = list(lista_categorias_dre_base)  # cópia - define_linhas_calculadas muta a lista
            lista_df_revisao = loop_prepara_dados_despesas(lista_categorias_dre, df_revisao_pivot, [])
            df_revisao_concatenados = pd.concat(lista_df_revisao, ignore_index=True)
            df_revisao_concatenados = df_revisao_concatenados[['Classificação Contábil 2'] + meses_ano]
            df_revisao_concatenados.rename(columns={'Classificação Contábil 2': 'Categoria'}, inplace=True)

            df_revisao_resumo = df_revisao_concatenados[
                df_revisao_concatenados['Categoria'].isin(lista_categorias_dre) &
                ~df_revisao_concatenados['Categoria'].isin(categorias_ocultas_resumo)
            ].copy()

            df_revisao_resumo = define_linhas_calculadas(
                df_revisao_resumo, df_revisao_concatenados, lista_categorias_dre, meses_ano, 'Orçamento',
                faturamento_bruto_por_casa=df_faturamento_por_casa
            )

            # Só as linhas de valor (as % são recalculadas depois de combinar com o Real, ver abaixo)
            df_revisao_valores_casa = df_revisao_resumo[~df_revisao_resumo['Categoria'].str.contains('%')].copy()
            df_revisao_valores_casa = df_revisao_valores_casa.drop_duplicates(subset='Categoria', keep='first').set_index('Categoria')[meses_ano]

        df_real_casa = df_historico_real_dre[
            (df_historico_real_dre['Casa'] == casa_nome) & (df_historico_real_dre['Mês'].dt.year == ano)
        ].copy()
        df_real_casa['Valor'] = pd.to_numeric(df_real_casa['Valor'], errors='coerce')
        df_real_casa['MesNum'] = df_real_casa['Mês'].dt.month

        # Mês só conta como fechado (Real) se o Faturamento Bruto real daquela casa for != 0
        # naquele mês - só ter linha em T_VALORES_REAIS_DRE não basta: já existe caso de mês com
        # todas as linhas presentes mas zeradas (upload de planilha modelo antes do fechamento)
        fat_bruto_mes = df_real_casa[
            df_real_casa['Categoria'] == categoria_real_faturamento_bruto
        ].groupby('MesNum')['Valor'].sum()
        meses_fechados_casa = set(fat_bruto_mes[fat_bruto_mes != 0].index)

        df_real_pivot_casa = df_real_casa.pivot_table(
            index='Categoria', columns='MesNum', values='Valor', aggfunc='sum'
        ).reindex(columns=range(1, 13), fill_value=0)

        resultados_por_casa[casa_nome] = (df_revisao_valores_casa, df_real_pivot_casa, meses_fechados_casa)

    ordem_categorias = next(
        (r[0].index.tolist() for r in resultados_por_casa.values() if r[0] is not None), None
    )
    if ordem_categorias is None:
        st.info(f'{casa} sem dados de Revisão de Orçamento para {ano}.')
        return

    # Status da casa naquele mês:
    # - 'real': já tem DRE Real fechada (Faturamento Bruto real != 0)
    # - 'sem_orcamento': Revisão de Orçamento de Faturamento Bruto daquele mês é 0 (ou nem existe) -
    #   a casa não tem operação orçada (ex: Nuv Gastrobar, Blue Note SP Sala 2 antes de começarem a
    #   operar) - não conta nem como Real fechada nem como em aberto, é ignorada no status do mês
    # - 'aberto': tem orçamento pra esse mês mas ainda não fechou o Real
    def status_casa_no_mes(casa_nome, mes_num):
        if mes_num in resultados_por_casa[casa_nome][2]:
            return 'real'
        df_revisao_valores_casa = resultados_por_casa[casa_nome][0]
        if df_revisao_valores_casa is None:
            return 'sem_orcamento'
        mes_nome = mapa_meses[mes_num]
        if 'Faturamento Bruto' not in df_revisao_valores_casa.index:
            return 'sem_orcamento'
        if df_revisao_valores_casa.loc['Faturamento Bruto', mes_nome] == 0:
            return 'sem_orcamento'
        return 'aberto'

    # Status de cada mês (pro cabeçalho colorido da tabela): considera só as casas com 'real' ou
    # 'aberto' - casas 'sem_orcamento' são ignoradas (não empurram o mês pra 'misto' sozinhas).
    # 'misto' só acontece quando há de fato uma mistura de casas com Real fechada e casas ainda
    # em aberto usando Revisão.
    casas_contribuintes = [
        c for c, (rv, rp, mf) in resultados_por_casa.items() if rv is not None or mf
    ]
    status_por_mes = {}
    for mes_num in range(1, 13):
        status_relevantes = [
            s for s in (status_casa_no_mes(c, mes_num) for c in casas_contribuintes) if s != 'sem_orcamento'
        ]
        if not status_relevantes or all(s == 'aberto' for s in status_relevantes):
            status_por_mes[mes_num] = 'orcamento'
        elif all(s == 'real' for s in status_relevantes):
            status_por_mes[mes_num] = 'real'
        else:
            status_por_mes[mes_num] = 'misto'

    if casa == 'Todas as Casas':
        st.write(
            'Cada casa usa os valores da DRE Final nos meses em que já existe DRE Final e valores do Orçamento Revisado nos '
            'demais meses. Casas diferentes podem contribuir com valores de DRE Real ou com valores de '
            'Orçamento no mesmo mês.'
        )
        st.write('Cabeçalho: 🔵 Real (todas as casas com DRE Final) · 🟣 Misto (parte das casas com DRE Final) · 🔴 Revisão de Orçamento.')
    else:
        meses_fechados_casa_unica = resultados_por_casa[casa][2]
        if not meses_fechados_casa_unica:
            st.info(f'{casa} ainda sem meses fechados em {ano} - exibindo só Revisão de Orçamento.')
        else:
            meses_fechados_nomes = ', '.join(mapa_meses[m] for m in sorted(meses_fechados_casa_unica))
            st.caption(f'Meses com DRE Real fechado em {ano}: {meses_fechados_nomes}. Os demais usam a Revisão de Orçamento.')
        st.caption('Cabeçalho: 🔵 Real · 🔴 Revisão de Orçamento.')

    # --- Combina cada casa (mês fechado usa Real, senão Revisão) e soma entre casas ---
    df_total_combinado = pd.DataFrame(0.0, index=ordem_categorias, columns=meses_ano)
    for casa_nome, (df_revisao_valores_casa, df_real_pivot_casa, meses_fechados_casa) in resultados_por_casa.items():
        if df_revisao_valores_casa is None and not meses_fechados_casa:
            continue  # casa sem nenhum dado (nem Real nem Revisão) - não contribui em nada

        def linha_real(categoria_real, _pivot=df_real_pivot_casa):
            if categoria_real in _pivot.index:
                return _pivot.loc[categoria_real]
            return pd.Series(0.0, index=range(1, 13))

        linhas_real = {
            canonico: linha_real(categoria_real)
            for canonico, categoria_real in MAPEAMENTO_CATEGORIA_REAL_ORCAMENTO.items()
        }
        linhas_real['Mão de Obra - Benefícios'] = sum(linha_real(c) for c in CATEGORIAS_REAL_BENEFICIOS)
        linhas_real['Patrocínio'] = linha_real(CATEGORIA_REAL_PATROCINIO_RECEITA) - linha_real(CATEGORIA_REAL_PATROCINIO_DESPESA)

        df_real_valores_casa = pd.DataFrame(linhas_real).T
        df_real_valores_casa.columns = [mapa_meses[c] for c in df_real_valores_casa.columns]
        df_real_valores_casa = df_real_valores_casa.reindex(ordem_categorias, fill_value=0)

        df_revisao_valores_casa_uso = (
            df_revisao_valores_casa if df_revisao_valores_casa is not None
            else pd.DataFrame(0.0, index=ordem_categorias, columns=meses_ano)
        )

        df_combinado_casa = pd.DataFrame(index=ordem_categorias, columns=meses_ano, dtype=float)
        for mes_num, mes_nome in enumerate(meses_ano, start=1):
            if mes_num in meses_fechados_casa:
                df_combinado_casa[mes_nome] = df_real_valores_casa[mes_nome]
            else:
                df_combinado_casa[mes_nome] = df_revisao_valores_casa_uso[mes_nome]

        df_total_combinado = df_total_combinado.add(df_combinado_casa, fill_value=0)

    df_valores_combinado = df_total_combinado.reset_index().rename(columns={'index': 'Categoria'})

    # Cria colunas de acumulado do ano e trimestres a partir dos meses já combinados
    df_valores_combinado[f'Ano {ano}'] = df_valores_combinado[meses_ano].sum(axis=1)
    df_valores_combinado['1º Trimestre'] = df_valores_combinado[['Janeiro', 'Fevereiro', 'Março']].sum(axis=1)
    df_valores_combinado['2º Trimestre'] = df_valores_combinado[['Abril', 'Maio', 'Junho']].sum(axis=1)
    df_valores_combinado['3º Trimestre'] = df_valores_combinado[['Julho', 'Agosto', 'Setembro']].sum(axis=1)
    df_valores_combinado['4º Trimestre'] = df_valores_combinado[['Outubro', 'Novembro', 'Dezembro']].sum(axis=1)

    colunas_totais = meses_ano + [f'Ano {ano}', '1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre']

    # % sobre Receita Bruta de cada categoria, recalculada sobre os valores já combinados (Real
    # tem linhas de % posicionais no banco, que dependem do Excel por casa e não seriam confiáveis
    # numa ordem canônica única - por isso são recalculadas aqui em vez de vir de nenhuma das duas fontes)
    faturamento_bruto_combinado = df_valores_combinado[df_valores_combinado['Categoria'] == 'Faturamento Bruto'][colunas_totais].sum()
    df_final = df_valores_combinado.copy()
    for categoria in ordem_categorias:
        valores_categoria = df_final[df_final['Categoria'] == categoria][colunas_totais].sum()
        porc_categoria = valores_categoria / faturamento_bruto_combinado
        df_final = insere_nova_linha(df_final, colunas_totais, porc_categoria, categoria, 'Categoria', '% sobre Receita Bruta')
    df_final = df_final.fillna(0)

    height = (len(df_final) + 1) * 35

    st.subheader(f'Resumo do Orçamento (DRE Final + Revisão) - {ano}')
    df_final_styled = df_final.copy()
    df_final_styled.loc[df_final_styled['Categoria'] == 'Faturamento Bruto', 'Categoria'] = df_final_styled['Categoria'].str.upper()
    df_final_styled.loc[df_final_styled['Categoria'] == 'Imposto de Renda', 'Categoria'] = 'Impostos'
    df_final_styled.loc[df_final_styled['Categoria'] == 'Investimento - CAPEX', 'Categoria'] = 'CAPEX (Investimentos)'

    # Cabeçalho colorido por mês (🔵 Real / 🟣 misto / 🔴 Revisão) - st.dataframe não aplica cor de
    # fundo do Styler no cabeçalho, então o indicador vai no próprio texto da coluna
    emoji_status_mes = {'real': '🔵', 'misto': '🟣', 'orcamento': '🔴'}
    df_final_styled = df_final_styled.rename(columns={
        mes_nome: f'{emoji_status_mes[status_por_mes[mes_num]]} {mes_nome}'
        for mes_num, mes_nome in enumerate(meses_ano, start=1)
    })

    linhas_percentual = df_final_styled['Categoria'].str.contains('%')
    linhas_moeda = ~linhas_percentual
    colunas_valores = df_final_styled.columns.drop('Categoria')

    df_final_styled = (
        df_final_styled.style
        .format(formatar_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_valores])
        .format(formatar_moeda_br, subset=pd.IndexSlice[linhas_moeda, colunas_valores])
        .apply(highlight_secoes_dre, axis=1)
    )
    st.dataframe(df_final_styled, hide_index=True, width='stretch', height=height)

    if casa == 'Todas as Casas':
        linhas_por_mes = []
        for mes_num, mes_nome in enumerate(meses_ano, start=1):
            status_casas = {c: status_casa_no_mes(c, mes_num) for c in casas_contribuintes}
            casas_reais = sorted(c for c, s in status_casas.items() if s == 'real')
            casas_sem_orcamento = sorted(c for c, s in status_casas.items() if s == 'sem_orcamento')
            casas_abertas = sorted(c for c, s in status_casas.items() if s == 'aberto')
            linhas_por_mes.append({
                'Mês': mes_nome,
                'Casas com DRE Final': ', '.join(casas_reais) if casas_reais else '—',
                'Casas sem faturamento orçado (fechadas)': ', '.join(casas_sem_orcamento) if casas_sem_orcamento else '—',
                'Casas sem DRE Final (usando Revisão)': ', '.join(casas_abertas) if casas_abertas else '—',
            })
        df_casas_fechamento = pd.DataFrame(linhas_por_mes)
        with st.expander('Ver casas com DRE Final/Orçamento em cada mês'):
            st.dataframe(df_casas_fechamento, hide_index=True, width='stretch')


if tipo_valor == 'Orçamento Operacional':
    tab_original, tab_revisao, tab_real_revisao = st.tabs([
        'Orçamento Operacional', 'Revisão Orçamento Operacional', 'DRE Final + Revisão Orçamento'
    ])
    with tab_original:
        renderiza_orcamento_operacional(df_orcamento_operacional, ano, casa)
    with tab_revisao:
        renderiza_orcamento_operacional(df_revisao_orcamento_operacional, ano, casa)
    with tab_real_revisao:
        renderiza_dre_real_revisao(df_historico_real_dre, df_revisao_orcamento_operacional, ano, casa)

else: # Histórico Real
    if casa == 'Todas as Casas':
        st.warning('Selecione uma casa específica para visualizar o Histórico Real.')
        st.stop()

    if casa == 'The Cavern' and ano < 2026:
        st.warning(f'{casa} sem dados para {ano}.')
        st.stop()

    df_historico_real_dre['Mês'] = pd.to_datetime(df_historico_real_dre['Mês'], errors='coerce')
    df_real_dre_filtrado = df_historico_real_dre[
        (df_historico_real_dre['Casa'] == casa) &
        (df_historico_real_dre['Mês'].dt.year == ano)
    ].copy()

    if df_real_dre_filtrado.empty:
        st.warning(f'{casa} sem dados para {ano}.')
        st.stop()
    
    # Vou calcular as porcentagens, não considerar o inputado
    df_real_dre_filtrado = df_real_dre_filtrado[~df_real_dre_filtrado['Categoria'].str.contains('% sobre')].copy()
    df_real_dre_filtrado['Valor'] = pd.to_numeric(df_real_dre_filtrado['Valor'], errors='coerce')

    lista_categorias_dre = [
        'FATURAMENTO BRUTO',
        '(-) Desconto sobre Venda',
        '(-) Impostos sobre Venda',
        '(-) Custo Mercadoria Vendida',
        '(-) Custos Artístico Geral',
        '(-) Custos Eventos',
        '(-) Dedução da Gorjeta',
        '(-) Deduções sobre Venda',
        'PJ',
        'MDO CLT - Salário',
        'Mão de Obra Extra',
        'Encargos e Provisões',
        'Benefícios',
        'Outros B',
        'Custo de Ocupação',
        'Utilidades',
        'Informática e TI',
        'Despesas Gerais',
        'Marketing',
        'Serviços de Terceiros',
        'Locação de Equipamentos',
        'Sistema de Franquias',
        '(+) Receitas de Patrocínio'
    ]

    mapa_posicao_percentual = { # Posição de cada % sobre Receita Bruta
        '(-) Desconto sobre Venda': 'Descontos - Marketing',
        '(-) Custo Mercadoria Vendida': 'Embalagens',
        '(-) Custos Artístico Geral': 'Locação de Equipamentos Variável',
        '(-) Custos Eventos': 'Repasse Gazit - Locação Anexo Abaru',
        '(-) Dedução da Gorjeta': '-  Comissões e Gorjeta',
        '(-) Deduções sobre Venda': 'Outros D',
        'PESSOAL': '-  Pro Labore',
        'Custo de Ocupação': 'Taxas publicas administrativas - Ocupação',
        'Utilidades': 'Material de Consumo - Gelo/ Gas CO2/ Carvao /Velas',
        'Informática e TI': 'Sistemas Gerais - Comunicação e Marketing',
        'Despesas Gerais': 'Viagens e Estadias - Operação',
        'Marketing': 'Ferramentas de Marketing',
        'Serviços de Terceiros': 'Valet/Motoboy',
        'Locação de Equipamentos': 'Locação de Utensílios',
        'Sistema de Franquias': 'Fee Gestão FB',
    }


    # Para manter categorias com o mesmo nome antes do pivot
    df_real_dre_filtrado['id_linha'] = df_real_dre_filtrado.groupby(['Categoria', 'Mês']).cumcount()

    # ordem original das categorias
    df_real_dre_filtrado['ordem'] = range(len(df_real_dre_filtrado))

    # Transforma meses em colunas
    df_real_dre_pivot = df_real_dre_filtrado.pivot_table(
        index=["Categoria", 'id_linha', 'ordem'], 
        columns="Mês",
        values="Valor",
        sort=False
    ).reset_index()
    
    # Remove linhas duplicadas
    df_real_dre_pivot = df_real_dre_pivot.groupby(['Categoria', 'id_linha']).first().reset_index()
    df_real_dre_pivot = df_real_dre_pivot.sort_values(by=['ordem'])
    df_real_dre_pivot.drop(columns=['id_linha', 'ordem'], inplace=True)
    
    # Renomeia colunas
    df_real_dre_formatado = df_real_dre_pivot.copy()
    meses = {
        '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
        '04': 'Abril', '05': 'Maio', '06': 'Junho',
        '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
        '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
    }

    datas = calcular_datas()
    if ano != datas['ano_atual']: # Para outros anos, renomeia a última coluna como 'Ano'
        ultima_data = max([col for col in df_real_dre_formatado.columns if isinstance(col, pd.Timestamp)])
        df_real_dre_formatado.columns = [
            'Ano' if col == ultima_data
            else meses[col.strftime('%m')] if isinstance(col, pd.Timestamp)
            else col
            for col in df_real_dre_formatado.columns
        ]
    else: # Para não renomear o mês mais recente do ano atual como 'Ano' 
        df_real_dre_formatado.columns = [
            col if col == pd.Timestamp('2025-12-31')
            else meses[col.strftime('%m')] if isinstance(col, pd.Timestamp)
            else col
            for col in df_real_dre_formatado.columns
    ]
    
    # Necessário ter a ordem das linhas de DRE
    if casa == 'Girondino - CCBB': id_base = 156
    elif casa == 'Terraço Notie': id_base = 149
    else: id_base = id_casa

    df_base = pd.read_excel(f"assets/sheets/Base_DRE - {id_base}.xlsx", sheet_name="DRE")
    if casa == 'Riviera Bar': col_categorias = 'c'
    else: col_categorias = 'Unnamed: 0'
    
    df_base = df_base[
        (~df_base[col_categorias].isna()) & 
        (~df_base[col_categorias].str.contains('% sobre', na=False)) & (
        (~df_base[col_categorias].isin(['Eventos',
        # Cargos - Salários
        '  - Hostess','  -  Maitre','  -  Garçon III','  -  Garçon II','  -  Garçon I','  -  Passador de Chopp', 
        '  -  Cumin','  -  Sub Chefe de Bar','  -  Bartender III','  -  Bartender II','  -  Bartender I','  -  Bar Back','  -  Barista III',
        '  -  Barista II','  -  Barista I','  -  Chopeiro III','  -  Chopeiro II','  -  Chopeiro I','  -  Sub Chefe de Cozinha','  -  Cozinheiro Líder',
        '  -  Cozinheiro III','  -  Cozinheiro II','  -  Cozinheiro I','  -  Ajud cozinha','  -  Saladeiro','  -  Pia','  -  Sub Chefe de Confeitaria',
        '  -  Confeiteiro III','  -  Confeiteiro II','  -  Confeiteiro I','  -  Copeiro','  -  Pizzaiolo','  -  Ajudante de Pizzaiolo','  -  Boqueta',
        '  -  Churrasqueiro I','  -  Churrasqueiro II','  -  Churrasqueiro III','  -  Ajud Limpeza','  -  Estoquista III','  -  Estoquista II',
        '  -  Estoquista I','  -  Chefe de Manutenção','  -  Aux. Manutenção III','  -  Aux. Manutenção II','  -  Aux. Manutenção I','  -  Chefe da Portaria',
        '  -  Porteiro III','  -  Porteiro II','  -  Porteiro I','  -  Hostess III','  -  Hostess II','  -  Hostess I','  -  Chefe de Bilheteria',
        '  -  Bilheteiro III','  -  Bilheteiro II','  -  Bilheteiro I','  -  Caixa','  -  Operador de Delivery'])))
    ].copy()
    
    # Remove a primeira linha (nome da casa)
    df_base = df_base.iloc[1:].reset_index(drop=True)

    # Remove todas as linhas abaixo disso
    indice = df_base[df_base[col_categorias] == 'MEMÓRIA DE CÁLCULO DAS PROJEÇÕES DE CUSTOS COM IMPOSTOS E PESSOAL'].index
    if not indice.empty:
        df_base = df_base.loc[:indice[0]]
    df_base = df_base.iloc[:-1]
    
    ordem_categorias_dre = df_base[col_categorias].unique().tolist() # Lista ordenada das categorias
    ordem_categorias_dre = [cat.replace("  -", "-") for cat in ordem_categorias_dre]

    df_real_dre_ordenado = df_real_dre_formatado.copy()
    df_real_dre_ordenado = df_real_dre_ordenado.reset_index(drop=True)
    
    # Transforma a coluna em Categorical para ordenar
    df_real_dre_ordenado['Categoria'] = pd.Categorical(
        df_real_dre_ordenado['Categoria'], 
        categories=ordem_categorias_dre, 
        ordered=True
    )
    df_real_dre_ordenado = df_real_dre_ordenado.sort_values('Categoria')
    df_real_dre_ordenado = df_real_dre_ordenado[~df_real_dre_ordenado['Categoria'].isna()].copy()

    # Calcula porcentagens e outros valores
    colunas_numericas = df_real_dre_ordenado.select_dtypes(include='number').columns
    df_real_dre_ordenado = define_linhas_calculadas(df_real_dre_ordenado, df_real_dre_ordenado, lista_categorias_dre, colunas_numericas, 'DRE Real', mapa_posicao_percentual=mapa_posicao_percentual)

    colunas = ['Categoria', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    df_real_dre_ordenado = df_real_dre_ordenado.reindex(columns=colunas, fill_value=0)

    st.subheader(f'DRE Real - {ano}')
    height = (len(df_real_dre_ordenado) + 1) * 35
    
    # Aplica estilos e formatação de porcentagens e moeda
    linhas_percentual = df_real_dre_ordenado['Categoria'].str.contains('% sobre', na=False)
    linhas_moeda = ~linhas_percentual
    colunas_valores = df_real_dre_ordenado.columns.drop('Categoria')

    df_real_dre_styled = (
        df_real_dre_ordenado.style
        .format(formatar_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_valores])
        .format(formatar_moeda_br, subset=pd.IndexSlice[linhas_moeda, colunas_valores])
        .apply(highlight_secoes_dre, axis=1)
    )
    st.dataframe(df_real_dre_styled, hide_index=True, width='stretch', height=height)
