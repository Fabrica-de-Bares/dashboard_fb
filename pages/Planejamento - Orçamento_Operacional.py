import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.planejamento_anual import *
from utils.functions.forecast import highlight_titulos_dre
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.components import button_download, seletor_ano, input_selecao_casas
from utils.queries_controladoria import *


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

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Terraço Notie', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
    
with col2:
    ano = seletor_ano(2023, 2026, 'ano')

with col3:
    tipo_valor = st.selectbox("Selecione a informação a visualizar:", ['Orçamento Operacional', 'Histórico Real'])
st.divider()

# Recupera dados - Orçamentos e Real
df_orcamento_operacional = GET_ORCAMENTO_OPERACIONAL()
df_historico_real_dre = GET_HISTORICO_REAL_DRE()


if tipo_valor == 'Orçamento Operacional':
    if ano == 2024 or ano == 2023:
        st.warning(f'Sem dados de orçamento de {ano} para o plano de contas Fábrica de Bares (2025).')
        st.stop()
    elif casa == 'The Cavern' and (ano < 2026):
        st.warning(f'{casa} sem dados para {ano}.')
        st.stop()

    df_orcamento_filtrado = df_orcamento_operacional[
        (df_orcamento_operacional['Casa'] == casa) &
        (df_orcamento_operacional['Ano'] == ano)
    ].copy()
    df_orcamento_filtrado.drop(columns=['Ano', 'ID Casa'], inplace=True)

    # Nomeia meses
    mapa_meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    df_orcamento_filtrado["Mês"] = df_orcamento_filtrado["Mês"].map(mapa_meses)

    # Transforma meses em colunas
    df_orcamento_pivot = df_orcamento_filtrado.pivot_table(
        index=["Casa", "Classificação Contábil 1", "Classificação Contábil 2"], 
        columns="Mês",
        values="Orçamento",
        aggfunc="sum"
    ).reset_index()

    for col in df_orcamento_pivot.columns:
        if col not in ["Classificação Contábil 1", "Classificação Contábil 2"]:
            df_orcamento_pivot[col] = pd.to_numeric(df_orcamento_pivot[col], errors='coerce').fillna(0)


    lista_categorias_orcamento = [
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
        'Patrocínio'
    ]

    lista_df_orcamentos = []
    lista_df_orcamentos = loop_prepara_dados_despesas(lista_categorias_orcamento, df_orcamento_pivot, lista_df_orcamentos)
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

    # Df apenas com os títulos das seções principais
    df_orcamentos_resumo = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'].isin(lista_categorias_orcamento)].copy()

    # Calcula porcentagens e outros valores
    colunas_numericas = df_orcamentos_resumo.select_dtypes(include='number').columns
    df_orcamentos_resumo = define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_orcamento, colunas_numericas)
    height = (len(df_orcamentos_resumo) + 1) * 35 # Define altura sem rolagem

    st.subheader(f'Resumo do Orçamento - {ano}')
    df_orcamentos_resumo_styled = df_orcamentos_resumo.copy()
    df_orcamentos_resumo_styled.loc[df_orcamentos_resumo_styled['Categoria'] == 'Faturamento Bruto', 'Categoria'] = df_orcamentos_resumo_styled['Categoria'].str.upper()

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


else: # Histórico Real
    if casa == 'The Cavern' and ano < 2026:
        st.warning(f'{casa} sem dados para {ano}.')
        st.stop()

    df_real_dre_filtrado = df_historico_real_dre[
        (df_historico_real_dre['Casa'] == casa) &
        (df_historico_real_dre['Mês'].dt.year == ano)
    ].copy()

    if df_real_dre_filtrado.empty:
        st.warning(f'{casa} sem dados para {ano}.')
        st.stop()
    
    # Para manter categorias com o mesmo nome
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

    ultima_data = max([col for col in df_real_dre_formatado.columns if isinstance(col, pd.Timestamp)])
    df_real_dre_formatado.columns = [
        'Ano' if col == ultima_data
        else meses[col.strftime('%m')] if isinstance(col, pd.Timestamp)
        else col
        for col in df_real_dre_formatado.columns
    ]
    
    st.subheader(f'DRE Real - {ano}')
    height = (len(df_real_dre_formatado) + 1) * 35
    
    # Aplica estilos e formatação de porcentagens e moeda
    linhas_percentual = df_real_dre_formatado['Categoria'].str.contains('% sobre')
    linhas_moeda = ~linhas_percentual
    colunas_valores = df_real_dre_formatado.columns.drop('Categoria')

    df_real_dre_styled = (
        df_real_dre_formatado.style
        .format(formatar_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_valores])
        .format(formatar_moeda_br, subset=pd.IndexSlice[linhas_moeda, colunas_valores])
        .apply(highlight_secoes_dre, axis=1)
    )
    st.dataframe(df_real_dre_styled, hide_index=True, width='stretch', height=height)
