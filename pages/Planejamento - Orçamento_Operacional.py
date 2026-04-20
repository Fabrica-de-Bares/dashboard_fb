import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.planejamento_anual import *
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

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
    
with col2:
    ano = seletor_ano(2023, 2026, 'ano')

with col3:
    tipo_valor = st.selectbox("Selecione a informação a visualizar:", ['Orçamento Operacional', 'Histórico Real'])
st.divider()

# Recupera dados - Orçamentos e Real
df_orcamento_operacional = GET_ORCAMENTO_OPERACIONAL()
df_historico_real_dre = GET_HISTORICO_REAL_DRE()
df_ordem_categorias_dre = GET_ORDEM_CATEGORIAS_DRE()


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
        'Patrocínio'
    ]

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

    # Df apenas com os títulos das seções principais
    df_orcamentos_resumo = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'].isin(lista_categorias_dre)].copy()

    # Calcula porcentagens e outros valores
    colunas_numericas = df_orcamentos_resumo.select_dtypes(include='number').columns
    df_orcamentos_resumo = define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_dre, colunas_numericas, 'Orçamento')
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
    
    # Necessário ter a ordem das linhas de DRE quandp tiver itens com alteração de valor (lógica do BIT_CANCELADO)
    ordem_categorias_dre = df_ordem_categorias_dre['Categoria'].unique().tolist()
    
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, '- Hostess', 'Salários')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Eventos Locações', 'Eventos Rebate Fornecedores - Premium Corp')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Eventos Rebate Fornecedores - Premium Corp', 'Membership')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Alimentação e Transporte', 'Viagens e Estadias - Artístico')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Embalagens', '% sobre Receita Bruta A&B')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Embalagens', '% sobre Receita Bruta de A&B')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Recurso Processual', 'Depreciação/Amortização')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, '- Subgerente', '- Coordenador/ Monitor')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, '- Coordenador/ Monitor', '- Atores do Evento')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, '- Atores do Evento', '- Guias')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, '- Guias', '- Manutenção')
    ordem_categorias_dre = altera_pos_item_lista(ordem_categorias_dre, 'Eventos de Marketing', 'Brindes e Confraternizações - Marketing')
    
    df_real_dre_ordenado = df_real_dre_formatado.copy()
    df_real_dre_ordenado = df_real_dre_ordenado.reset_index(drop=True)
    
    # Transforma a coluna em Categorical
    df_real_dre_ordenado['Categoria'] = pd.Categorical(
        df_real_dre_ordenado['Categoria'], 
        categories=ordem_categorias_dre, 
        ordered=True
    )
    df_real_dre_ordenado = df_real_dre_ordenado.sort_values('Categoria')
    
    # Remove ocorrência repetida de 'Eventos A&B'
    mask_eventos = df_real_dre_ordenado['Categoria'] == 'Eventos A&B'
    indices = df_real_dre_ordenado[mask_eventos].index
    if len(indices) == 2: # Duas ocorrências
        df_real_dre_ordenado = df_real_dre_ordenado.drop(indices[0]) # Remove a primeira
    
    # Corrige 'Serviços de Terceiros'
    mask_serv = df_real_dre_ordenado['Categoria'] == 'Serviços de Terceiros'
    indices_serv = df_real_dre_ordenado[mask_serv].index
    if len(indices_serv) >= 2:
        df_real_dre_ordenado.loc[indices_serv[1], 'Categoria'] = 'Serviços de Terceiros - Eventos' # Renomeia a segunda ocorrencia
    
        # Reposiciona em 'Custos Eventos'
        linha_mover = df_real_dre_ordenado[df_real_dre_ordenado['Categoria'] == 'Serviços de Terceiros - Eventos']
        linha_mover = linha_mover.reset_index(drop=True)
        linha_referencia = df_real_dre_ordenado[df_real_dre_ordenado['Categoria'] == 'Comissões de Vendas - Eventos']

        # remove a linha que será movida
        df_temp = df_real_dre_ordenado[df_real_dre_ordenado['Categoria'] != 'Serviços de Terceiros - Eventos']
        idx = linha_referencia.index[0] # pega índice da referência
        
        parte_cima = df_temp.loc[:idx] # divide o df
        parte_baixo = df_temp.loc[idx+1:]
        df_real_dre_ordenado = pd.concat([parte_cima, linha_mover, parte_baixo]) # insere no meio
            
    
    # Calcula porcentagens e outros valores
    colunas_numericas = df_real_dre_ordenado.select_dtypes(include='number').columns
    df_real_dre_ordenado[colunas_numericas] = df_real_dre_ordenado[colunas_numericas].abs()
    df_real_dre_ordenado = define_linhas_calculadas(df_real_dre_ordenado, df_real_dre_ordenado, lista_categorias_dre, colunas_numericas, 'DRE Real', mapa_posicao_percentual=mapa_posicao_percentual)
    

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
