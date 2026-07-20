import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_alteracao_despesas import *
from utils.functions.general_functions import *
from utils.queries_controladoria import *
from utils.components import seletor_mes, seletor_ano, input_selecao_casas

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Auditoria - Alteração de Despesas em Sistema",
    page_icon="🔎",
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
    st.title("🔎 Auditoria - Alteração de Despesas em Sistema")
    st.write("Aba para visualizar despesas alteradas após as datas de fechamento de cada mês de DRE.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Dados - Logs despesas
df_log_despesas_inicial = GET_LOGS_DESPESAS()
df_datas_fechamento = GET_DATAS_FECHAMENTO()

# Seletor de ano
ano_competencia_selecionado = seletor_ano(2026, 2026, 'ano', 'Selecione o ano')
st.divider()


lista_dfs_tipos_alteracao = []
tipos_alteracao = [
    {
        "titulo": "Alteração em Data de Competência",
        "campo_filtro": "Data Competência",
        "colunas_comparar": ["Data Competência"],
        "titulo_excel": "Data de Competência"
    },
    {
        "titulo": "Alteração em Data de Vencimento",
        "campo_filtro": "Data Vencimento",
        "colunas_comparar": ["Data Vencimento"],
        "titulo_excel": "Data de Vencimento"
    },
    {
        "titulo": "Alteração em Valor",
        "campo_filtro": "Valor",
        "colunas_comparar": ["Valor Original", "Valor Liquido"],
        "titulo_excel": "Valor"
    },
    {
        "titulo": "Alteração em Classificação Contábil",
        "campo_filtro": "Class. Cont.",
        "colunas_comparar": ["Class. Cont. 1", "Class. Cont. 2"],
        "titulo_excel": "Classificação Contábil"
    },
    {
        "titulo": "Despesas Canceladas",
        "campo_filtro": "Canceladas",
        "colunas_comparar": ["Bit Cancelada"],
        "titulo_excel": "Despesas Canceladas"
    },
    {
        "titulo": "Alteração de Provisão/Real",
        "campo_filtro": "Real/Provisão",
        "colunas_comparar": ["Real/Provisão"],
        "titulo_excel": "Provisão-Real"
    }
]

# Filtra pela casa selecionada
df_log_despesas_filtrado = filtragem_inicial_despesas(df_log_despesas_inicial)

for tipo in tipos_alteracao:
    df = despesas_alteradas_por_campo(df_log_despesas_filtrado, tipo["colunas_comparar"])
    lista_dfs_tipos_alteracao.append({
        "df": df,
        "titulo": tipo["titulo"],
        "campo_filtro": tipo["campo_filtro"],
        "colunas_comparar": tipo["colunas_comparar"],
        "tipo": tipo["titulo_excel"],
    })


# 1. Resumo dos ajustes para fechamento (início do mês até data de fechamento)
with st.container(border=True):
    lista_casas = df_datas_fechamento['Casa'].unique().tolist()
    df_ajustes_casa = pd.DataFrame(columns=['Casa', 'Mês', 'Ano', 'Tipo', 'Quantidade', 'Período de Ajustes'])
    periodos_por_mes = {} # Para armazenar o período de ajustes de cada mês
    dfs_detalhados = {} # Para exibir depois os df de ajustes

    for casa in lista_casas:
        # Define período de ajustes para cada mês de competência da casa
        df_datas_fim_periodo_ajuste = df_datas_fechamento[df_datas_fechamento['Casa'] == casa].copy()
        
        if ano_competencia_selecionado == 2026:
            df_datas_fim_periodo_ajuste = df_datas_fechamento[
                (df_datas_fechamento['MES'] >= 3) & 
                (df_datas_fechamento['ANO'] >= 2026) &
                (df_datas_fechamento['Casa'] == casa)
            ].copy()
        lista_datas_fechamento = df_datas_fim_periodo_ajuste['DATA_FECHAMENTO'].tolist()
        
        for data in lista_datas_fechamento:
            data_fim_periodo_ajuste = data.date()
            data_inicio_periodo_ajuste = pd.Timestamp(day=1, month=data_fim_periodo_ajuste.month, year=data_fim_periodo_ajuste.year).date()
            mes_competencia_ajuste = df_datas_fim_periodo_ajuste[df_datas_fim_periodo_ajuste['DATA_FECHAMENTO'] == data]['MES'].iloc[0]
            ano_competencia_ajuste = df_datas_fim_periodo_ajuste[df_datas_fim_periodo_ajuste['DATA_FECHAMENTO'] == data]['ANO'].iloc[0]
            
            # Dicionário com período de ajustes por mês de cada casa
            periodos_por_mes.setdefault(casa, {})[int(mes_competencia_ajuste)] = (
                f"{data_inicio_periodo_ajuste.strftime('%d/%m')} a {data_fim_periodo_ajuste.strftime('%d/%m')}"
            )  
        
            # Filtra o df de cada tipo de alteração pelas despesas com alteração dentro do período de ajuste
            for item in lista_dfs_tipos_alteracao:
                if item['tipo'] in ['Data de Competência', 'Classificação Contábil', 'Provisão-Real']:
                    df_alteracoes = item['df']
                    df_alteracoes = df_alteracoes[df_alteracoes['Casa'] == casa].copy()
                    periodo = periodos_por_mes[casa][int(mes_competencia_ajuste)]
                    
                    df_alteracoes_mes = filtragem_mes_ano_competencia(df_alteracoes, mes_competencia_ajuste, ano_competencia_ajuste, 'Ajustes Fechamento', data_fim_periodo_ajuste)
                    dfs_detalhados.setdefault(casa, {}) \
                    .setdefault(int(mes_competencia_ajuste), {})[item['tipo']] = df_alteracoes_mes
                    
                    quantidade_alteracoes = exibe_contagem_despesas(df_alteracoes_mes, exibe_res=False) # Calcula quantidade de ajustes por mês e tipo
                    df_ajustes_casa.loc[len(df_ajustes_casa)] = [ # Insere resultados no df
                        casa,
                        mes_competencia_ajuste, 
                        ano_competencia_ajuste,
                        item['tipo'],
                        quantidade_alteracoes,
                        periodo
                    ]

    df_ajustes_casa_fmt = df_ajustes_casa.pivot_table( # Transforma meses em colunas
        index=["Casa", 'Mês', 'Ano', 'Período de Ajustes'], 
        columns="Tipo",
        values="Quantidade",
        sort=False
    ).reset_index()
    df_ajustes_casa_fmt = df_ajustes_casa_fmt.sort_values(by=['Mês', 'Casa'])
  
    df_ajustes_casa_fmt = df_ajustes_casa_fmt.rename(columns={ # Renomeia meses
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    })

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Resumo - Ajustes para fechamento de cada casa')
    with col2:
        lista_meses = ['Todos', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        mes = st.selectbox('Selecione o mês de competência', lista_meses)
        meses = {
            "Janeiro": 1,
            "Fevereiro": 2,
            "Março": 3,
            "Abril": 4,
            "Maio": 5,
            "Junho": 6,
            "Julho": 7,
            "Agosto": 8,
            "Setembro": 9,
            "Outubro": 10,
            "Novembro": 11,
            "Dezembro": 12
        }
    
    st.write("")    
    if mes != 'Todos': # Filtra pelo mês de competência selecionado
        mes_competencia = meses[mes]
        df_ajustes_casa_fmt = df_ajustes_casa_fmt[(df_ajustes_casa_fmt['Mês'] == mes_competencia)].copy()

    if not df_ajustes_casa_fmt.empty:
        height = (len(df_ajustes_casa_fmt) + 1) * 35 # Define altura sem rolagem

        df_ajustes_casa_fmt = df_ajustes_casa_fmt[(df_ajustes_casa_fmt['Ano'] == ano_competencia_selecionado)].copy()
        df_ajustes_casa_fmt.drop(columns={'Ano'}, inplace=True)
        df_ajustes_casa_fmt.rename(columns={
            'Mês': 'Mês de Competência', 
            'Data de Competência': 'Alteração de Data de Competência',
            'Classificação Contábil': 'Alteração de Classificação Contábil',
            'Provisão-Real': 'Alteração de Provisão-Real'
        }, inplace=True)
        df_ajustes_casa_fmt = df_ajustes_casa_fmt[['Casa', 'Alteração de Data de Competência', 'Alteração de Classificação Contábil', 'Alteração de Provisão-Real', 'Mês de Competência', 'Período de Ajustes']]
        
        # Cria coluna e linha de Total
        df_ajustes_casa_fmt = somar_total(df_ajustes_casa_fmt)

        height = min((len(df_ajustes_casa_fmt) + 1) * 35, 600) # Altura padrão
        st.dataframe(df_ajustes_casa_fmt, hide_index=True, width='stretch', height=height)

        with st.expander('Visualizar detalhamento dos ajustes'):
            col1, col2 = st.columns(2)
            with col1:
                lista_casas.sort()
                casa_sel = st.selectbox("Selecione uma casa", lista_casas)
            with col2:
                mes_sel = st.selectbox("Selecione o mês de competência", list(dfs_detalhados.get(casa_sel, {}).keys()))
            st.divider()

            dfs_mes = dfs_detalhados[casa_sel][mes_sel]
            for tipo, df in dfs_mes.items():
                st.markdown(f"<h4>{tipo}</h4>", unsafe_allow_html=True)
                df_styled = format_columns_brazilian(df, ['Valor Original', 'Valor Liquido'])
                if tipo == 'Data de Competência':
                    colunas_comparar = ['Data Competência']
                elif tipo == 'Classificação Contábil':
                    colunas_comparar = ["Class. Cont. 1", "Class. Cont. 2"]
                elif tipo == 'Provisão-Real':
                    colunas_comparar = ['Real/Provisão']
                
                df_styled = destacar_alteracoes(df_styled, colunas_comparar)
                st.dataframe(df_styled, hide_index=True, width='stretch')
                st.divider()
    else:
        st.warning('Sem resultados.')
        
st.divider()

# 2. Alteração de despesas após data de fechamento do mês selecionado
dfs_exportar = {} # Lista de dataframes para excel

with st.container(border=True):
    st.subheader('Alteração de despesas após data de fechamento da DRE')
    col1, col2 = st.columns(2)
    with col1:
        lista_retirar_casas = ['Todas as Casas', 'Brahminha', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Terraço Notie', 'Terraço Notie Novo', 'The Cavern - Almoço']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='seletor_casas_despesas')	
    with col2:
        mes_competencia_selecionado = int(seletor_mes("Selecione o mês da DRE", key="seletor_mes_despesas"))


    # Recupera data de fechamento para casa, mês e ano de competência selecionados
    df_data_fechamento_mes_selecionado = df_datas_fechamento[
        (df_datas_fechamento['MES'] == mes_competencia_selecionado) & 
        (df_datas_fechamento['ANO'] == ano_competencia_selecionado) &
        (df_datas_fechamento['ID Casa'] == id_casa)
    ].copy()
    if not df_data_fechamento_mes_selecionado.empty:
        data_fechamento_mes_selecionado = df_data_fechamento_mes_selecionado['DATA_FECHAMENTO'].iloc[0]
        mapeamento_meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        nome_mes = mapeamento_meses[mes_competencia_selecionado]
    else:
        st.warning("Sem data de fechamento lançada para esse mês.")
        st.stop()

    st.write(f"**Data de fechamento da DRE de {nome_mes}:** {data_fechamento_mes_selecionado.date().strftime('%d/%m/%Y')}")
    st.divider()

    # Seletores de class. cont.
    col1, col2 = st.columns(2)
    with col1:
        df_class_cont_1 = GET_CLASS_CONT_1()
        lista_class_cont_1 = df_class_cont_1['DESCRICAO'].tolist()
        lista_class_cont_1_selecionadas = st.multiselect(label='Filtro de Classificação Contábil 1', options=lista_class_cont_1, default=None)
    with col2:
        df_class_cont_2 = GET_CLASS_CONT_2()
        if not lista_class_cont_1_selecionadas: lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
        else: 
            df_class_cont_2 = df_class_cont_2[df_class_cont_2['DESCRICAO_1'].isin(lista_class_cont_1_selecionadas)].copy()
            lista_class_cont_2 = df_class_cont_2['DESCRICAO_2'].tolist()
        lista_class_cont_2_selecionadas = st.multiselect(label='Filtro de Classificação Contábil 2', options=lista_class_cont_2, default=None)
    st.divider()


    # Despesas criadas após data de fechamento
    st.markdown(f'''<h4>Despesas criadas</h4>''', unsafe_allow_html=True)
    df_log_despesas_inicial = df_log_despesas_inicial[df_log_despesas_inicial['ID Casa'] == id_casa].copy() 
    df_log_despesas_criadas = busca_despesas_criadas(df_log_despesas_inicial, id_casa, data_fechamento_mes_selecionado)
    df_log_despesas_criadas = filtragem_classificacao_contabil(df_log_despesas_criadas, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
    df_log_despesas_criadas = filtragem_mes_ano_competencia(df_log_despesas_criadas, mes_competencia_selecionado, ano_competencia_selecionado, 'Criadas', data_fechamento_mes_selecionado)
    df_log_despesas_criadas.rename(columns={'Data Alteração': 'Data Criação'}, inplace=True)

    if not df_log_despesas_criadas.empty:
        df_log_despesas_criadas_styled = format_columns_brazilian(df_log_despesas_criadas, ['Valor Original', 'Valor Liquido'])
        st.dataframe(df_log_despesas_criadas_styled, hide_index=True, width='stretch')

    quantidade = exibe_contagem_despesas(df_log_despesas_criadas)
    dfs_exportar["Despesas Criadas"] = df_log_despesas_criadas # adiciona para exportação
    st.divider()


    # Tipos de alteração definidos anteriormente
    for item in lista_dfs_tipos_alteracao:
        titulo = item["titulo"]
        df = item["df"]
        campo_filtro = item["campo_filtro"]
        colunas_comparar = item["colunas_comparar"]
        titulo_excel = item["tipo"]
        
        st.markdown(f'''<h4>{titulo}</h4>''', unsafe_allow_html=True)
        df = df[df['Casa'] == casa].copy() 
        df = filtragem_classificacao_contabil(df, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
        # Filtra apenas despesas com data alteração > data fechamento
        df = filtragem_mes_ano_competencia(df, mes_competencia_selecionado, ano_competencia_selecionado, campo_filtro, data_fechamento_mes_selecionado)
        
        if not df.empty:
            df_styled = format_columns_brazilian(df, ['Valor Original', 'Valor Liquido'])
            df_styled = destacar_alteracoes(df_styled, colunas_comparar)
            st.dataframe(df_styled, hide_index=True, width="stretch")
            exibe_legenda()

        quantidade = exibe_contagem_despesas(df)
        dfs_exportar[titulo_excel] = df
        st.divider()


    # Despesas com casa alterada
    st.markdown(f'''<h4>Despesas com casa alterada</h4>''', unsafe_allow_html=True)
    df_despesas_alteracao_casa = despesas_alteradas_por_campo(df_log_despesas_inicial, ['Casa'])
    df_despesas_alteracao_casa = filtragem_classificacao_contabil(df_despesas_alteracao_casa, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas)
    df_despesas_alteracao_casa = filtragem_mes_ano_competencia(df_despesas_alteracao_casa, mes_competencia_selecionado, ano_competencia_selecionado, 'Casa', data_fechamento_mes_selecionado)

    df_despesas_alteracao = df_despesas_alteracao_casa[ # Despesas alteradas para a mes/ano selecionados
        (df_despesas_alteracao_casa['ID Casa'] == id_casa) &
        (df_despesas_alteracao_casa['Data Alteração'] >= data_fechamento_mes_selecionado)
    ].copy()
    lista_ids_alteracao_mes_selecionado = df_despesas_alteracao['ID Despesa'].tolist()
    df_despesas_alteracao_casa = df_despesas_alteracao_casa[df_despesas_alteracao_casa['ID Despesa'].isin(lista_ids_alteracao_mes_selecionado)].copy()
    df_despesas_alteracao_casa['ID Casa'] = pd.to_numeric(df_despesas_alteracao_casa['ID Casa'], errors='coerce').astype('Int64')
    df_despesas_alteracao_casa.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

    if not df_despesas_alteracao_casa.empty:
        df_despesas_alteracao_casa_styled = format_columns_brazilian(df_despesas_alteracao_casa, ['Valor Original', 'Valor Liquido'])
        df_despesas_alteracao_casa_styled = destacar_alteracoes(df_despesas_alteracao_casa_styled, ['Casa'])
        st.dataframe(df_despesas_alteracao_casa_styled, hide_index=True, width='stretch')
        exibe_legenda()

    quantidade = exibe_contagem_despesas(df_despesas_alteracao_casa)
    dfs_exportar["Despesas Casa Alterada"] = df_despesas_alteracao_casa


    # Botão para exportar Excel
    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        button_download(dfs_exportar)


