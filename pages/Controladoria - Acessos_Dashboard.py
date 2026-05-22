import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_alteracao_despesas import *
from utils.functions.general_functions import *
from utils.queries_controladoria import *

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Acessos Usuários - Dashboard",
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
    st.title("👥 Acessos Usuários - Dashboard")
    st.write("Aba para visualizar quais usuários tem acesso ao Dashboard FB, seus cargos, casas e abas que podem visualizar.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

df_usuarios_cargos = GET_USUARIOS_CARGOS()
df_cargos_abas = GET_CARGOS_ABAS()
df_todas_casas = GET_TODAS_CASAS()

# Lista que contém todas as casas válidas
lista_todas_casas = df_todas_casas['Casa'].unique().tolist()
texto_todas_casas = ", ".join(lista_todas_casas)

# Lista de cargos
lista_cargos = df_cargos_abas['Cargo'].unique().tolist()

# Cria df com cada usuário, seu cargo e lista de empresas
lista_usuarios = df_usuarios_cargos['Nome Usuário'].unique().tolist()
lista_usuarios = [usu for usu in lista_usuarios if usu != None] # Verificação de segurança
df_usu_cargo_emp = pd.DataFrame(columns=['ID Usuário', 'Login Usuário', 'Nome Usuário', 'Cargo', 'Empresas'])

for usuario in lista_usuarios:
    df_usuario = df_usuarios_cargos[df_usuarios_cargos['Nome Usuário'] == usuario].copy()
    lista_casas_usuario = df_usuario['Empresa'].unique().tolist()
    
    if set(lista_todas_casas).issubset(set(lista_casas_usuario)):
        texto_casas_usuario = 'Todas'
    else:
        texto_casas_usuario = ", ".join(lista_casas_usuario)

    df_usu_cargo_emp.loc[len(df_usu_cargo_emp)] = [
        df_usuario['ID Usuário'].iloc[0], 
        df_usuario['Login Usuário'].iloc[0],
        usuario,
        df_usuario['Cargo'].iloc[0],
        texto_casas_usuario
    ]


with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Usuários x Cargos x Empresas')
    with col2:
        lista_usuarios.sort()
        usuario_filtrado = st.selectbox('Buscar usuário', lista_usuarios, index=None, key='seletor_usuario')
    with col3:
        lista_cargos.sort()
        cargo_filtrado = st.selectbox('Buscar cargo', lista_cargos, index=None, key='seletor_cargo_usuario')

    if usuario_filtrado:
        df_usu_cargo_emp = df_usu_cargo_emp[df_usu_cargo_emp['Nome Usuário'] == usuario_filtrado].copy()
    if cargo_filtrado:
        df_usu_cargo_emp = df_usu_cargo_emp[df_usu_cargo_emp['Cargo'] == cargo_filtrado].copy()
    df_usu_cargo_emp.sort_values(by=['Nome Usuário'], inplace=True)

    st.write("")
    st.dataframe(df_usu_cargo_emp, hide_index=True, width='stretch')
    st.write(f'**Observação:** na coluna Empresa, "Todas" inclui: {texto_todas_casas}')

st.divider()

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Cargos x Abas')
    with col2:
        lista_cargos.sort()
        cargo_filtrado = st.selectbox('Buscar cargo', lista_cargos, index=None, key='seletor_cargo')

    if cargo_filtrado:
        df_cargos_abas = df_cargos_abas[df_cargos_abas['Cargo'] == cargo_filtrado].copy()
    df_cargos_abas.sort_values(by=['Cargo'], inplace=True)

    st.write("")
    st.dataframe(df_cargos_abas, hide_index=True, width='stretch')