import streamlit as st
import pandas as pd
import calendar
from utils.components import seletor_ano
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import casas_validas
from utils.functions.general_functions import config_sidebar
from utils.functions.conciliacoes import *
from utils.functions.farol_conciliacao import *
from utils.queries_conciliacao import *


nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
casas_validas = [casa for casa in casas_validas if casa != 'Blue Note SP (Sala 2)']

st.set_page_config(
    page_title="Conciliação FB - Farol",
    page_icon="📊",
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
    st.title("📊 Farol de conciliação")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Recuperando dados
df_casas = GET_CASAS()

# Filtrando Datas
datas = calcular_datas()


# Filtrando por casa e ano
col1, col2 = st.columns(2)

# Seletor de mês
with col1: 
    meses = ['Todos os meses', '1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_farol = st.selectbox("Selecione um mês ou trimestre", meses)

# Seletor de ano
with col2:
    ano_farol = seletor_ano(2024, 2026, 'ano_farol')
    
st.divider()

# Conciliação completa (2024 -- atual)
datas_completas = pd.date_range(start=datas['jan_ano_passado'], end=datas['dez_ano_atual'])
df_conciliacao_farol = pd.DataFrame()
df_conciliacao_farol['Data'] = datas_completas

# Lista: tabela de conciliação (2024 -- atual) de cada casa usando list comprehension
lista_conciliacao_casas = [conciliacao_casa(df_conciliacao_farol, casa, datas_completas) for casa in casas_validas]


meses = list(range(1, 13))
qtd_dias = []

# Calcula quantidade de dias em casa mês
for i in range(1, 13):
    dias_no_mes = calendar.monthrange(ano_farol, i)[1]
    qtd_dias.append(dias_no_mes)

df_meses = pd.DataFrame({'Mes': meses, 'Qtd_dias': qtd_dias})

conditions = [
    df_meses['Mes'].between(1, 3),
    df_meses['Mes'].between(4, 6),
    df_meses['Mes'].between(7, 9),
    df_meses['Mes'].between(10, 12)
]

# Calcula quantidade de dias em cada trimestre
choices = [1, 2, 3, 4]
df_trimestres = pd.DataFrame({'Mes': meses, 'Trimestre': np.select(conditions, choices, default=np.nan)})
df_trimestres = df_trimestres.merge(df_meses, right_on='Mes', left_on='Mes', how='inner')
df_dias_trimestre = df_trimestres.groupby(['Trimestre'])['Qtd_dias'].sum().reset_index()
df_trimestres = df_trimestres.merge(df_dias_trimestre, right_on='Trimestre', left_on='Trimestre', how='inner')

# Lista: porcentagem de dias não conciliados por mês de cada casa usando list comprehension
lista_casas_mes = [lista_dias_nao_conciliados_casa(df_conciliacao_casa, ano_farol, df_meses, datas['mes_atual']) for df_conciliacao_casa in lista_conciliacao_casas]

# Lista: porcentagem de dias não conciliados por trimestre de cada casa usando list comprehension
lista_casas_trim = [lista_dias_nao_conciliados_casa_trim(df_conciliacao_casa, ano_farol, df_trimestres, mes_farol) for df_conciliacao_casa in lista_conciliacao_casas]


# Exibe gráficos
with st.container(border=True):
    col1, col2, col3 = st.columns([0.05, 4, 0.05], vertical_alignment="center")
    with col2:
        st.subheader(f"Porcentagem (%) dias não conciliados - {mes_farol}")
        if mes_farol == 'Todos os meses':
            grafico_dias_nao_conciliados(casas_validas, nomes_meses, lista_casas_mes) 
        elif mes_farol == '1º Trimestre' or mes_farol == '2º Trimestre' or mes_farol == '3º Trimestre' or mes_farol == '4º Trimestre':
            grafico_dias_nao_conciliados_trim(df_conciliacao_farol, casas_validas, mes_farol, lista_casas_trim, ano_farol, datas_completas)
        else:   
            grafico_dias_nao_conciliados_mes(casas_validas, lista_casas_mes, mes_farol, df_conciliacao_farol, ano_farol, datas_completas)


# Cria e exibe tabela do farol de conciliação
df_farol_conciliacao = pd.DataFrame()
df_farol_conciliacao['Casa'] = casas_validas

# Função que cria a coluna de cada mês da tabela
df_farol_conciliacao = df_farol_conciliacao_mes(lista_casas_mes, df_farol_conciliacao, ano_farol, datas['mes_atual'])

if mes_farol == 'Todos os meses': # Exibe o farol
    st.divider()
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Status Conciliação Bancária - Resumo')
        st.write('Porcentagem (%) de dias conciliados por casa e mês.')
    with col2:
        casas_farol = st.multiselect('Selecione uma ou mais casas', casas_validas, placeholder='Selecione uma ou mais casas', label_visibility='hidden', key='casa_farol')

    if casas_farol:
        df_farol_conciliacao = df_farol_conciliacao[df_farol_conciliacao['Casa'].isin(casas_farol)].copy()

    height = (len(df_farol_conciliacao) + 1) * 35
    df_farol_conciliacao_styled = df_farol_conciliacao.style.map(lambda val: estilos_celulas(val, ano_atual, ano_farol, datas['mes_atual'], mes_farol))
    st.dataframe(df_farol_conciliacao_styled, hide_index=True, height=height)
    
    st.divider()
    st.subheader(":material/arrow_downward: Visualização - Dias não conciliados")
    
    casas = df_casas['Casa'].tolist()
    casa_selecionada = st.selectbox("Selecione uma casa", casas, index=None, placeholder='Selecione uma casa', label_visibility='hidden', key='casa_visualizacao_dias')

    # Definindo um dicionário para mapear nomes de casas a IDs de casas
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

    # Obtendo o ID da casa selecionada
    if casa_selecionada != None:
        id_casa = mapeamento_casas[casa_selecionada]
        
        # Exibe dataframes dos dias não conciliados da casa para cada mês
        df_farol_conciliacao_casa_mes(df_conciliacao_farol, casa_selecionada, lista_casas_mes, casas_validas, ano_farol, datas_completas)

