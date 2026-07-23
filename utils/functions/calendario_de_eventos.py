import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *


def dataframe_to_json_calendar(df_eventos, event_color_type=None):
    """
    Converte um DataFrame de eventos em um formato JSON adequado para o calendário.
    event_color_type = 'status'  -> Define a cor de acordo com o valor de 'Status Evento'
    event_color_type = 'casa'    -> Define a cor de acordo com o valor de 'Casa'
    """

    # Formata Data Evento para o formato YYYY-MM-DD (preparar para inserir no JSON)
    df_eventos = df_formata_datas_sem_horario_YYYY_MM_DD(df_eventos, ['Data Evento'])

    cores_status = {
        'Confirmado': '#22C55E',
        'Em negociação': '#EAB308',
    }

    cores_casa = {
        149: '#E35336',  # Priceless
        162: '#2323FF',  # Concierge Notiê
        122: '#FF13F0',  # Arcos
        114: '#FFA500',  # Bar Brahma - Centro
        148: '#84161f',  # Bar Brahma - Granja
        116: '#FF2C2C',  # Bar Leo Centro
        110: '#000080',  # Blue Note São Paulo
        156: '#FFB5C0',  # Girondino
        160: '#88E788',  # Girondino CCBB
        105: '#7E8C54',  # Jacaré
        128: '#9D00FF',  # Love Cabaret
        104: '#898989',  # Orfeu
        115: '#00CCC8',  # Riviera
        145: '#000000',  # Ultra Evil (Rolim)
        173: '#12b823' # Brahma - Paulista
    }


    eventos_json = []
    for _, row in df_eventos.iterrows():
        # Define a cor baseada no event_color_type
        if event_color_type == 'status':
            cor = cores_status.get(row['Status Evento'], '#EF4444')
        elif event_color_type == 'casa':
            cor = cores_casa.get(row['ID Casa'], '#4150F7')
        else:
            cor = '#4150F7'  # Azul


        evento = {
            "id": row['ID Evento'],
            "allDay": True,
            "start": row['Data Evento'],
            "end": row['Data Evento'],
            "title": f"{row['Nome Evento']}",
            "color": cor,
            "cliente": row['Cliente'],
            "event_date": row['Data Evento'],
            "tipo_evento": row['Tipo Evento'],
            "num_pessoas": row['Num Pessoas'],
            "status": row['Status Evento'],
            "motivo_declinio": row['Motivo Declínio'],
            "comercial_responsavel": row['Comercial Responsável'],
            "observacoes": row['Observações']
        }
        eventos_json.append(evento)
    return eventos_json


def get_custom_css():
    """Retorna a string com CSS customizado para o calendário."""
    return """
    /* ======== BOTÕES ======== */
    .fc-button {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .fc-button:hover {
        background-color: #f9fafb !important;
        border-color: #9ca3af !important;
    }
    .fc-button:disabled {
        background-color: #f3f4f6 !important;
        color: #9ca3af !important;
        border-color: #e5e7eb !important;
    }
    /* ======== TÍTULO ======== */
    .fc-toolbar-title {
        font-size: 22px;
        color: #111827;
        font-weight: 600;
    }
    /* ======== FUNDO DO CALENDÁRIO ======== */
    .fc {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    /* ======== EVENTOS ======== */
    .fc-daygrid-event {
        border-radius: 6px;
        padding: 2px 4px;
        font-size: 13px;
        font-weight: 500;
        border: none;
    }
    .fc-daygrid-event:hover {
        opacity: 0.8;
        cursor: pointer;
    }
    .fc-event-title {
        white-space: normal !important;
    }
    /* ======== BARRA DE NAVEGAÇÃO SUPERIOR ======== */
    .fc-toolbar.fc-header-toolbar {
        margin-bottom: 12px;
    }
    /* ======== DIAS ======== */
    .fc-daygrid-day-number {
        color: #374151;
        font-weight: 500;
    }
    .fc-col-header-cell-cushion {
        color: #6b7280;
        font-weight: 500;
    }
    /* ======== OVERFLOW DE EVENTOS ======== */
    .fc-daygrid-more-link {
        color: #3b82f6;
        font-weight: 500;
    }
    """

def get_calendar_options():
    """Retorna o dicionário com opções de configuração do calendário."""
    return {
        "locale": "pt-br",
        "initialView": "dayGridMonth",
        "height": 700,
        "headerToolbar": {
            "start": "prev,next today",
            "center": "title",
            "end": "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        },
        "dayMaxEvents": False,
    }


def infos_evento(id_evento, df_eventos_aditivos_agrupados, df_eventos):

    evento_inicial = df_eventos.loc[df_eventos['ID Evento'] == str(id_evento)]
    evento = df_eventos_aditivos_agrupados.loc[df_eventos_aditivos_agrupados['ID Evento'] == str(id_evento)].copy()

    if evento.empty:
        st.error(f"Evento {id_evento} não encontrado.")
        return
    
    evento['Data Evento'] = evento['Data Evento'].fillna('Data não informada')
    evento['Data Contratação'] = evento['Data Contratação'].fillna('Data não informada')
    evento['Observações'] = evento['Observações'].fillna('Nenhuma observação informada')

    st.markdown(f"### Evento - {evento['Nome Evento'].values[0]}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<b>Comercial Responsável:</b> {evento['Comercial Responsável'].values[0]}", unsafe_allow_html=True)
        st.markdown(f"<b>Cliente:</b> {evento['Cliente'].values[0]}", unsafe_allow_html=True)
        st.markdown(f"<b>Data do Evento:</b> {formata_data_sem_horario(evento['Data Evento'].values[0])}", unsafe_allow_html=True)
        st.markdown(f"<b>Data de Contratação:</b> {formata_data_sem_horario(evento['Data Contratação'].values[0])}", unsafe_allow_html=True)
        st.markdown(f"<b>Tipo de Evento:</b> {evento['Tipo Evento'].values[0]}", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<b>Número de Pessoas:</b> {evento['Num Pessoas'].values[0]}", unsafe_allow_html=True)
        st.markdown(f"<b>Valor Total do Evento:</b> R$ {format_brazilian(evento['Valor Total Evento'].values[0])}", unsafe_allow_html=True)
        st.markdown(f"<b>Status:</b> {evento['Status Evento'].values[0]}", unsafe_allow_html=True)
        if evento['Status Evento'].values[0] == 'Declinado':
            st.markdown(f"<b>Motivo do Declinio:</b> {evento['Motivo Declínio'].values[0]}", unsafe_allow_html=True)
        
        texto_observacoes = escape_dolar(evento['Observações'].values[0])
        st.markdown(f"<b>Observações:</b> {texto_observacoes}", unsafe_allow_html=True)
    with st.expander("Ver detalhes"):
        evento_inicial = format_columns_brazilian(evento_inicial, [
            'Valor Total Evento',
            'Valor Locação Aroo 1',
            'Valor Locação Aroo 2',
            'Valor Locação Aroo 3',
            'Valor Locação Anexo',
            'Valor Locação Notie',
            'Valor Locação Mirante',
            'Valor AB',
            'Valor Imposto',
            'Total Gazit',
            'Valor Total Locação',
            'Valor Locação Aroo 1',
            'Valor Locação Aroo 2',
            'Valor Locação Aroo 3',
            'Valor Locação Anexo',
            'Valor Locação Notie',
            'Valor Locação Mirante',
            'Valor Locação Espaço',
            'Valor Locação Gerador',
            'Valor Locação Mobiliário',
            'Valor Locação Utensílios',
            'Valor Mão de Obra Extra',
            'Valor Taxa Administrativa',
            'Valor Comissão BV',
            'Valor Extras Gerais',
            'Valor Taxa Serviço',
            'Valor Acréscimo Forma de Pagamento',
            'Valor Contratação Artístico',
            'Valor Contratação Técnico de Som',
            'Valor Contratação Bilheteria/Couvert Artístico'
        ])
        evento_inicial = df_format_date_columns_brazilian(evento_inicial, ['Data Evento', 'Data Contratação'])
        st.dataframe(evento_inicial, width='stretch', hide_index=True)    


def mostrar_aditivos(id_evento, df_aditivos):
    id_evento = str(id_evento)
    lista_aditivos = df_aditivos[df_aditivos['ID Evento do Aditivo'] == id_evento]['ID Aditivo'].tolist()
    if len(lista_aditivos) == 0:
        st.warning("Nenhum aditivo encontrado para este evento.")
    else:
        aditivos = df_aditivos[df_aditivos['ID Evento do Aditivo'] == id_evento]
        aditivos = df_format_date_columns_brazilian(aditivos, ['Data Evento', 'Data Contratação'])
        aditivos = format_columns_brazilian(aditivos, ['Valor Total Aditivo', 'Valor AB', 'Valor Total Locação', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Valor Locação Espaço', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Taxa Serviço', 'Valor Acréscimo Forma de Pagamento', 'Valor Imposto'])
        st.markdown(f"#### Aditivos")
        st.dataframe(aditivos, width='stretch', hide_index=True)
    return lista_aditivos

def mostrar_parcelas(id_evento, df_parcelas, lista_aditivos):
    id_evento = str(id_evento)
    
    if df_parcelas[(df_parcelas['ID Evento'] == id_evento) | (df_parcelas['ID Evento'].isin(lista_aditivos))].empty:
        st.warning("Nenhuma parcela encontrada para este evento.")
    else:
        parcelas = df_parcelas[(df_parcelas['ID Evento'] == id_evento) | (df_parcelas['ID Evento'].isin(lista_aditivos))]
        parcelas = df_format_date_columns_brazilian(parcelas, ['Data Vencimento', 'Data Recebimento'])
        parcelas = format_columns_brazilian(parcelas, ['Valor Parcela'])
        parcelas = rename_colunas_parcelas(parcelas)
        st.markdown(f"#### Parcelas")
        st.dataframe(parcelas, width='stretch', hide_index=True)