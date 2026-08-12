import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_planejamento_anual import *
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.functions.general_functions_conciliacao import calcular_datas
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
    elif casa == 'Bar Brahma - Paulista' and ano <= 2026:
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


if tipo_valor == 'Orçamento Operacional':
    tab_original, tab_revisao = st.tabs(['Orçamento Operacional', 'Revisão Orçamento Operacional'])
    with tab_original:
        renderiza_orcamento_operacional(df_orcamento_operacional, ano, casa)
    with tab_revisao:
        renderiza_orcamento_operacional(df_revisao_orcamento_operacional, ano, casa)

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
