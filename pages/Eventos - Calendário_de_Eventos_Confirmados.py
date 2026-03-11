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
	page_title="Calendário de Eventos Confirmados",
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
        st.title("📅 Calendário de Eventos Confirmados")
    with col2:
        st.button(label='Atualizar', key='atualizar_calendario', on_click=st.cache_data.clear)
    st.divider()

    # Filtro eventos confirmados
    df_eventos = df_eventos[df_eventos['Status Evento'] == 'Confirmado']

    json_eventos = dataframe_to_json_calendar(df_eventos, event_color_type='casa')

    # Renderiza o calendário
    selected = st_calendar(
        events=json_eventos,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key=f"calendar",
    )

    # Adiciona a legenda de cores dos eventos
    st.markdown("""
        <div style="margin-top: -24px; padding: 10px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; display: grid; grid-template-columns: max-content 1fr; gap: 16px; align-items: start;">
            <h6 style="padding: 0; margin: 0;">Legenda:</h6>
            <div style="display: flex; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #000000; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Priceless</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #582310; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Arcos</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #DF2526; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Bar Brahma - Centro</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #84161f; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Bar Brahma - Granja</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #E9A700; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Bar Leo Centro</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #081F5C; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Blue Note São Paulo</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #4A5129; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Girondino</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #8CA706; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Girondino CCBB</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #0CA22E; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Jacaré</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #E799BB; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Love Cabaret</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #006E77; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Orfeu</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #C2185B; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Riviera</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: #2C3E50; border-radius: 4px; margin-right: 8px;"></div>
                    <span>Ultra Evil (Rolim)</span>
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