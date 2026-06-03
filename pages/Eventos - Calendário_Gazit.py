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
    df_eventos_concierge = GET_EVENTOS_CONCIERGE()
    df_eventos_concierge['Casa'] = df_eventos_concierge['Casa'].apply(lambda x: 'Concierge Priceless' if x == 'Terraço Notie' else x)
    df_eventos_concierge['ID Casa'] = df_eventos_concierge['ID Casa'].apply(lambda x: 149 if x == 162 else x)
    df_eventos_concierge['Valor Comissão BV'] = 0
    dfs_e = [df for df in [df_eventos, df_eventos_concierge] if not df.empty]
    df_eventos = pd.concat(dfs_e, ignore_index=True) if dfs_e else pd.DataFrame()

    df_aditivos = GET_ADITIVOS()

    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()
    df_parcelas_concierge = GET_PARCELAS_EVENTOS_CONCIERGE()
    dfs_p = [df for df in [df_parcelas, df_parcelas_concierge] if not df.empty]
    df_parcelas = pd.concat(dfs_p, ignore_index=True) if dfs_p else pd.DataFrame()

    df_eventos_aditivos_agrupado = GET_EVENTOS_ADITIVOS_AGRUPADOS_CALENDARIO()
    
    # Remove eventos com NaT ou datas nulas
    df_eventos = df_eventos.dropna(subset=["Data Evento"])

    # Filtra eventos do Priceless (id 149)
    df_eventos = df_eventos[df_eventos['ID Casa'] == 149]

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📅 Calendário de Eventos - Gazit")
    with col2:
        st.button(label='Atualizar', key='atualizar_calendario', on_click=st.cache_data.clear)
               
    st.divider()
    
    df_eventos['ID Evento'] = df_eventos['ID Evento'].astype(str)
    df_eventos_aditivos_agrupado['ID Evento'] = (
        df_eventos_aditivos_agrupado['ID Evento'].astype(str)
    )
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
            if not str(id_evento_selecionado).startswith("C"): # Evento Concierge
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
                with st.container(border=True):
                    st.write("")
                    col1, col2, col3 = st.columns([1, 15, 1])
                    with col2:
                        infos_evento(id_evento_selecionado, df_eventos, df_eventos)
                        st.write("")
                        mostrar_parcelas(id_evento_selecionado, df_parcelas, [])
                        st.write("")
        else:
            st.info("Selecione um evento no calendário para ver os detalhes.")

if __name__ == '__main__':
  main()