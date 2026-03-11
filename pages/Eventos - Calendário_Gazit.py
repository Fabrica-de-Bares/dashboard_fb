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
	page_icon="📆",
	page_title="Calendário de Eventos - Gazit",
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
    
    # Remove eventos com NaT ou datas nulas
    df_eventos = df_eventos.dropna(subset=["Data Evento"])

    # Filtra eventos do Priceless (id 149)
    df_eventos = df_eventos[df_eventos['ID Casa'] == 149]

    # Filtra eventos com valores de repasse para Gazit (Locação Aroos e Anexo)
    #df_eventos = df_eventos[(df_eventos['Valor Locação Aroo 1'] > 0) | (df_eventos['Valor Locação Aroo 2'] > 0) | (df_eventos['Valor Locação Aroo 3'] > 0) | (df_eventos['Valor Locação Anexo'] > 0)]

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📅 Calendário de Eventos - Gazit")
    with col2:
        st.button(label='Atualizar', key='atualizar_calendario', on_click=st.cache_data.clear)
               
    st.divider()
    
    json_eventos = dataframe_to_json_calendar(df_eventos, event_color_type='status')
    
    # Renderiza o calendário
    selected = st_calendar(
        events=json_eventos,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key="calendar",
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