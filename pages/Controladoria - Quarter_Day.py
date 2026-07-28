import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_quarterday import *
from utils.functions.general_functions import *
from utils.functions.general_functions_conciliacao import calcular_datas
from utils.queries_controladoria import *
from utils.components import input_selecao_casas

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="KPI's - Quarter Day",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

datas = calcular_datas()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title(f"📈 KPI's - Quarter Day {datas['ano_atual']}")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

lista_retirar_casas = ['Todas as Casas', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Escritório Fabrica de Bares', 'The Cavern', 'The Cavern - Almoço', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Terraço Notie Novo']
id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto', agregado=True)


# Dados - Orçamentos e Real
df_orcamento_operacional = GET_ORCAMENTO_OPERACIONAL()
df_historico_real_dre = GET_HISTORICO_REAL_DRE()

# Dados - Ticket Médio e N Clientes 
df_ticket_medio_clientes = GET_TICKET_MEDIO_CLIENTES()


categorias_quarter = ['Faturamento Bruto', 'Faturamento Bruto - Alimentos', 'Faturamento Bruto - Bebidas', 'Ticket Médio - A&B', 'Nº de Clientes', 'Faturamento Eventos', 'Faturamento - Artístico', 'Faturamento Delivery', 'CMV', 'EBITDA']

if casa != 'Girondino - Agregado':
    if df_orcamento_operacional[df_orcamento_operacional['Casa'] == casa].empty or df_historico_real_dre[df_historico_real_dre['Casa'] == casa].empty:
        st.warning(f"Sem dados de orçamento/faturamento lançados para {casa}.")
        st.stop()

for categoria in (categorias_quarter):
    if categoria == 'Faturamento Bruto': class_cont = ['FATURAMENTO BRUTO']
    elif categoria == 'Faturamento Bruto - Alimentos': class_cont = ['Alimentação']
    elif categoria == 'Faturamento Bruto - Bebidas': class_cont = ['Bebida']
    elif categoria == 'Faturamento Eventos': class_cont = ['Eventos A&B', 'Eventos Couvert', 'Eventos Locações', 'Eventos Rebate Fornecedores']
    elif categoria == 'Faturamento - Artístico':
        class_cont = ['Artístico (couvert/shows)']
        if id_casa not in [114, 148, 110, 105, 128, 145]: # Considera Artístico apenas para essas casas
            continue
    elif categoria == 'Faturamento Delivery':
        class_cont = ['Delivery']
        if id_casa not in [114, 148, 116, 104, 105]: # Considera Delivery apenas para essas casas
            continue
    elif categoria == 'CMV': class_cont = 'CMV'
    elif categoria == 'EBITDA': class_cont = ['EBITDA']

    with st.container(border=True): 
        if categoria == 'Ticket Médio - A&B':
            df_faturamento_categoria = prepara_dados_ticket_clientes(df_ticket_medio_clientes, casa, datas, 'TICKET_MEDIO')
            for col in df_faturamento_categoria:
                if col != 'Ano': df_faturamento_categoria[col] = pd.to_numeric(df_faturamento_categoria[col], errors='coerce').astype(float)
            df_faturamento_categoria_styled = formata_colunas(df_faturamento_categoria, categoria, categoria)
        
        elif categoria == 'Nº de Clientes':
            df_faturamento_categoria = prepara_dados_ticket_clientes(df_ticket_medio_clientes, casa, datas, 'NUM_CLIENTES')
            for col in df_faturamento_categoria:
                df_faturamento_categoria[col] = pd.to_numeric(df_faturamento_categoria[col], errors='coerce').astype('Int64')
            df_faturamento_categoria_styled = formata_colunas(df_faturamento_categoria, categoria, categoria)
        
        else:
            df_faturamento_categoria = prepara_dados_faturamento_orcamento(df_historico_real_dre, df_orcamento_operacional, casa, datas, class_cont)
            df_faturamento_categoria_styled = formata_colunas(df_faturamento_categoria, 'Faturamento Total', categoria)
        
        st.subheader(f'{categoria}') # Exibe df
        st.dataframe(df_faturamento_categoria_styled, hide_index=True, width='stretch')
        st.divider()

        # Prepara dados para o gráfico
        df_faturamento_grafico = df_faturamento_categoria[['Ano', 1,2,3,4,5,6,7,8,9,10,11,12]]
        lista_anos = df_faturamento_grafico['Ano'].astype(str).tolist()
        series = []
        for ano in lista_anos:
            df_faturamento_grafico_ano = df_faturamento_grafico[df_faturamento_grafico['Ano'].astype(str) == ano].copy()
            if categoria == 'CMV': # Multiplica por 100 para exibir no gráfico
                lista_valores_mes = df_faturamento_grafico_ano.drop(columns=['Ano']).iloc[0].mul(100).replace({np.nan: 0}).tolist() 
            else:
                df_faturamento_grafico_ano = df_faturamento_grafico_ano.fillna(0)
                lista_valores_mes = df_faturamento_grafico_ano.drop(columns=['Ano']).iloc[0].fillna(0).tolist()

            series.append({
                "name": str(ano),
                "type": "line",
                "data": lista_valores_mes,
            })


        ## Crescimento ano a ano (ex.: 2024 > 2025)
        df_crescimento = df_faturamento_categoria.copy()
        cols_meses = [col for col in df_crescimento.columns if isinstance(col, (int, float))]

        for col in cols_meses + ['Acumulado', 'ANO', '1 TRI', '2 TRI', '3 TRI', '4 TRI']:
            df_crescimento[col] = df_crescimento[col].replace(0, np.nan).pct_change()

        df_crescimento['% Crescimento Anual'] = df_faturamento_categoria['Ano'].astype(str).shift(1) + ' > ' + df_faturamento_categoria['Ano'].astype(str)
        
        if categoria not in ['Ticket Médio - A&B', 'Nº de Clientes']:
            df_crescimento = df_crescimento.iloc[1:-1] # Remove primeira e última linha
        else:
            df_crescimento = df_crescimento.iloc[1:] # Remove primeira e última linha

        # Organiza colunas
        df_crescimento = df_crescimento[['% Crescimento Anual', 1,2,3,4,5,6,7,8,9,10,11,12, 'Acumulado', 'ANO',  '1 TRI', '2 TRI', '3 TRI', '4 TRI']]
        df_crescimento_styled = formata_colunas(df_crescimento, 'Crescimento Anual', categoria)
        st.dataframe(df_crescimento_styled, hide_index=True, width='stretch')
        st.divider()


        ## Crescimento ano anterior (ex.: 2025 em relação aos anteriores)
        # ano_base = datas['ano_atual'] - 1
        # df_crescimento_ano_anterior = calcula_crescimento_ano(ano_base, df_faturamento_categoria)
        # df_crescimento_ano_anterior_styled = formata_colunas(df_crescimento_ano_anterior, 'Crescimento Ano Anterior', categoria)
        # st.dataframe(df_crescimento_ano_anterior_styled, hide_index=True, width='stretch')
        # st.divider()


        ## Crescimento ano atual
        ano_base = datas['ano_atual']
        df_crescimento_ano_atual = calcula_crescimento_ano(ano_base, df_faturamento_categoria)

        # Atingimento do Orçado
        if categoria not in ['Ticket Médio - A&B', 'Nº de Clientes']:
            df_real = df_faturamento_categoria[df_faturamento_categoria['Ano'] == datas['ano_atual']].copy()
            df_orc = df_faturamento_categoria[df_faturamento_categoria['Ano'].astype(str).str.contains('Orçamento')]

            df_atingimento = df_real.copy()

            for col in cols_meses + ['Acumulado', 'ANO', '1 TRI', '2 TRI', '3 TRI', '4 TRI']:
                orc = df_orc.iloc[0][col]
                real = df_real.iloc[0][col]
                
                df_atingimento[col] = ((real / orc - 1) if orc != 0 else np.nan)

            df_atingimento[f'% Crescimento de {ano_base}'] = f"Orçamento {datas['ano_atual']}"
            df_atingimento.drop(columns=['Ano'], inplace=True)
            df_crescimento_ano_atual = pd.concat([df_crescimento_ano_atual, df_atingimento]) # Concatena crescimento com atingimento do orçado

        df_crescimento_ano_atual_styled = formata_colunas(df_crescimento_ano_atual, 'Crescimento Ano Atual', categoria)
        st.dataframe(df_crescimento_ano_atual_styled, hide_index=True, width='stretch')
        st.divider()

        
        ## % sobre Faturamento da Casa
        if categoria not in ['Faturamento Bruto', 'CMV', 'Ticket Médio - A&B', 'Nº de Clientes']:
            # Recalcula faturamento bruto total
            df_total = prepara_dados_faturamento_orcamento(df_historico_real_dre, df_orcamento_operacional, casa, datas, ['FATURAMENTO BRUTO'])
            df_categoria = df_faturamento_categoria.copy() # Recupera faturamento da categoria
            cols_meses = [col for col in df_categoria.columns if isinstance(col, (int, float))]
            cols_calc = cols_meses + ['Acumulado',  'ANO', '1 TRI', '2 TRI', '3 TRI', '4 TRI']

            df_percentual = df_categoria.copy()

            for col in cols_calc:
                total = df_total[col].replace(0, np.nan)
                df_percentual[col] = df_categoria[col] / total # Divide faturamento da categoria pelo faturamento total

            df_percentual = df_percentual.rename(columns={'Ano': '% Sobre Faturamento da Casa'})
            df_percentual = df_percentual.iloc[:-1] # Remove a última linha
            df_percentual_styled = formata_colunas(df_percentual, 'Percentual', categoria)
            st.dataframe(df_percentual_styled, hide_index=True, width='stretch')
            st.divider()

        grafico_linhas_faturamento(series, categoria, lista_anos, key=categoria)
     

