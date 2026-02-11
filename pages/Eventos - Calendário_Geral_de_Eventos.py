import streamlit as st
from streamlit_calendar import calendar as st_calendar
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.calendario_de_eventos import *

st.set_page_config(
	page_icon=":calendar:",
	page_title="Calendário Geral de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
    
    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS()
    df_aditivos = GET_ADITIVOS()
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

    df_eventos_aditivos_agrupado = GET_EVENTOS_ADITIVOS_AGRUPADOS()
    
    # Substitui NaT ou datas nulas por uma data padrão ou remove linhas
    df_eventos = df_eventos.dropna(subset=["Data Evento"])

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📅 Calendário Geral de Eventos")
    with col2:
        st.button(label='Atualizar', key='atualizar_calendario', on_click=st.cache_data.clear)
               
    st.divider()

    # Filtro de casa:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='calendario')

    if casa != 'Todas as Casas':
        df_eventos = df_eventos[df_eventos['ID Casa'] == id_casa]

        if id_casa == 149: # Priceless - Locação dividida por espaços
            df_eventos = df_eventos.drop(columns=['Valor Locação Espaço', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico'])
            df_aditivos = df_aditivos.drop(columns=['Valor Locação Espaço', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico'])
            df_eventos_aditivos_agrupado = df_eventos_aditivos_agrupado.drop(columns=['Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico'])

        else:
            df_eventos = df_eventos.drop(columns=['Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Valor Locação Bar'])
            df_aditivos = df_aditivos.drop(columns=['Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Valor Locação Bar'])

            if id_casa in [104, 115, 116, 156, 122]: # Orfeu, Riviera, Bar Leo Centro, Girondino, Arcos - Com locação de um số espaço, SEM Couvert/Bilheteria
                df_eventos = df_eventos.drop(columns=['Valor Contratação Bilheteria/Couvert Artístico'])
                df_aditivos = df_aditivos.drop(columns=['Valor Contratação Bilheteria/Couvert Artístico'])
                df_eventos_aditivos_agrupado = df_eventos_aditivos_agrupado.drop(columns=['Valor Contratação Bilheteria/Couvert Artístico'])


    json_eventos = dataframe_to_json_calendar(df_eventos, event_color_type='status')

    # Renderiza o calendário
    selected = st_calendar(
        events=json_eventos,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key=f"calendar_{casa}",
    )

    # Adiciona a legenda de cores dos eventos
    st.markdown("""
    <div style="margin-top: -24px; padding: 10px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; display: flex; align-items: center;">
        <h6 style="padding: 0">Legenda:</h6>
        <div style="display: flex; gap: 16px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #22C55E; border-radius: 4px; margin-right: 8px;"></div>
                <span>Confirmado</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #EAB308; border-radius: 4px; margin-right: 8px;"></div>
                <span>Em negociação</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #EF4444; border-radius: 4px; margin-right: 8px;"></div>
                <span>Declinados</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    if selected:
        
        if selected.get("callback") == "eventClick":
            id_evento_selecionado = selected["eventClick"]["event"]["id"]
            with st.container(border=True):
                st.write("")
                col1, col2, col3 = st.columns([1, 15, 1])
                with col2:
                    infos_evento(id_evento_selecionado, df_eventos_aditivos_agrupado, df_eventos)
                    st.write("")
                    lista_aditivos = mostrar_aditivos(id_evento_selecionado, df_aditivos)
                    st.write("")
                    mostrar_parcelas(id_evento_selecionado, df_parcelas, lista_aditivos)
                    st.write("")
        else:
            st.info("Selecione um evento no calendário para ver os detalhes.")

if __name__ == '__main__':
  main()