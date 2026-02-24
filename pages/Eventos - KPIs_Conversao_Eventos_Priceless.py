import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *
from utils.functions.faturamento import *

st.set_page_config(
    page_icon="📈",
    page_title="KPI's de Vendas - Conversão de Eventos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
    st.switch_page("Login.py")

def main():

    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS_ADITIVOS_AGRUPADOS()
    
    # Formata tipos de dados do dataframe de eventos
    tipos_de_dados_eventos = {
        'Valor Imposto': float,
        'Valor AB': float,
        'Valor Taxa Serviço': float,
        'Valor Total': float,
        'Valor Locação Total': float,
        'Valor Contratação Artístico': float,
        'Valor Contratação Técnico de Som': float,
        'Valor Contratação Bilheteria/Couvert Artístico': float,
        'Valor Locação Gerador': float,
        'Valor Locação Mobiliário': float,
        'Valor Locação Utensílios': float,
        'Valor Mão de Obra Extra': float,
        'Valor Taxa Administrativa': float,
        'Valor Comissão BV': float,
        'Valor Extras Gerais': float,
        'Valor Taxa Serviço': float,
        'Valor Acréscimo Forma de Pagamento': float,
        'Valor Imposto': float,
    }
    df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')
    # Seleciona apenas colunas do tipo float
    float_cols = df_eventos.select_dtypes(include=['float'])
    # Preenche NaN com 0 nessas colunas
    df_eventos[float_cols.columns] = float_cols.fillna(0)

    # Vendedores
    df_vendedores = df_eventos[['ID Responsavel Comercial', 'Comercial Responsável']].drop_duplicates().dropna()
    df_vendedores["ID Responsavel Comercial"] = df_vendedores["ID Responsavel Comercial"].astype(int)
    df_vendedores["ID - Responsavel"] = df_vendedores["ID Responsavel Comercial"].astype(str) + " - " + df_vendedores["Comercial Responsável"].astype(str)

    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📈 KPI's de Vendas - Conversão de Eventos")
    with col2:
        st.button(label='Atualizar', key='atualizar_kpis_vendas', on_click=st.cache_data.clear)
    st.divider()

    # Adiciona selecao de mes e ano
    col0, col1, col2, col3, col4= st.columns([0.5, 0.25, 0.25, 0.4, 1])
    with col0:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Terraço Notie', 'Escritório Fabrica de Bares', 'Blue Note SP (Sala)', 'The Cavern - Almoço']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='calendario')
    with col1:
        ano = seletor_ano(2025, 2026, key="seletor_ano_kpi_conversao_eventos_priceless")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_conversao_eventos_priceless"
        )
        mes = int(mes)
    with col3:
        id_vendedor, nome_vendedor = seletor_vendedor("Comercial Responsável:", df_vendedores, "seletor_vendedor_kpi_conversao_eventos")
    with col4:
        filtro_data_categoria = "Competência do Evento"
        filtro_data_categoria = st.segmented_control(
            label="Por Data de:",
            options=["Competência do Evento", "Recebimento do Lead", "Envio da Proposta"],
            selection_mode="single",
            default="Competência do Evento",
        )

    # Filtra por casa
    if id_casa != -1:
        df_eventos = df_eventos[df_eventos['ID Casa'] == id_casa]
    else:
        df_acessos_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
        lista_ids_casas = df_acessos_casas['ID Loja'].tolist()
        df_eventos = df_eventos[df_eventos['ID Casa'].isin(lista_ids_casas)]

    # Filtra por data
    if filtro_data_categoria:
        dict_filtro_data = {
            "Competência do Evento": "Data do Evento",
            "Recebimento do Lead": "Data Recebimento Lead",
            "Envio da Proposta": "Data Envio Proposta",
        }
        filtro_tipo_data = dict_filtro_data[filtro_data_categoria]
        st.divider()
        df_eventos_ano = df_filtrar_ano(df_eventos, filtro_tipo_data, ano)
        # Formata tipos de dados do dataframe de eventos ano
        tipos_de_dados_eventos_ano = {
            'Valor Imposto': float,
            'Valor AB': float,
            'Valor Total': float,
            'Valor Locação Total': float,
            'Valor Locação Gerador': float,
            'Valor Locação Mobiliário': float,
            'Valor Locação Utensílios': float,
            'Valor Locação Gerador': float,
            'Valor Mão de Obra Extra': float,
            'Valor Taxa Administrativa': float,
            'Valor Comissão BV': float,
            'Valor Extras Gerais': float,
            'Valor Taxa Serviço': float,
            'Valor Acréscimo Forma de Pagamento': float,
            'Valor Contratação Artístico': float,
            'Valor Contratação Técnico de Som': float,
            'Valor Contratação Bilheteria/Couvert Artístico': float,
            'Valor Imposto': float
        }
        df_eventos_ano = df_eventos_ano.astype(tipos_de_dados_eventos_ano, errors='ignore')

        df_eventos = df_filtrar_mes(df_eventos_ano, filtro_tipo_data, mes)
        
    else:
        st.warning("Selecione um filtro de data.")
        st.stop()   

    # Filtra por vendedor
    if id_vendedor != -1:
        df_eventos = df_eventos[df_eventos['ID Responsavel Comercial'] == id_vendedor]
        df_eventos_ano = df_eventos_ano[df_eventos_ano['ID Responsavel Comercial'] == id_vendedor]

    col1, col2, col3 = st.columns([1.3, 1.5, 3], gap="small", vertical_alignment="top")
    with col1:
        num_leads_recebidos, num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao = calculo_numero_propostas(df_eventos, ano, mes)
        cards_numero_propostas(
            num_leads_recebidos, num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao
        )
    with col2:
        valor_leads_recebidos, valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao = calculo_valores_propostas(df_eventos, ano, mes)
        valor_leads_recebidos = format_brazilian(valor_leads_recebidos)
        valor_lancadas = format_brazilian(valor_lancadas)
        valor_confirmadas = format_brazilian(valor_confirmadas)
        valor_declinadas = format_brazilian(valor_declinadas)
        valor_em_negociacao = format_brazilian(valor_em_negociacao)
        cards_valor_propostas(
            valor_leads_recebidos, valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao
        )
    with col3:
        grafico_pizza_num_propostas(
            num_confirmadas, num_declinadas, num_em_negociacao
        )
        grafico_barras_num_propostas(df_eventos_ano, filtro_tipo_data)


    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            col1, col2 = st.columns([1, 2], vertical_alignment = "bottom")
            with col1:
                st.markdown("### Eventos por status")
            with col2:
                options_eventos = ["Leads Recebidos", "Com Propostas Enviadas", "Confirmados", "Declinados", "Em Negociação"]
                selection = st.segmented_control(
                    "Selecione o status do evento", options_eventos, selection_mode="single", key="segmented_control_kpi_conversao", label_visibility="collapsed"
                )
            st.write('')

            # Formata valores monetários e datas
            df_eventos = df_formata_datas_sem_horario(df_eventos, ['Data Envio Proposta', 'Data de Contratação', 'Data do Evento', 'Data Recebimento Lead', 'Data Confirmação', 'Data Declínio', 'Data Em Negociação'])
            df_eventos = df_eventos.drop(columns=['ID Responsavel Comercial'])
            df_eventos_com_proposta_enviada = df_eventos[df_eventos['Data Envio Proposta'].notnull()]

            # Filtragem com base na seleção
            if selection == "Leads Recebidos":
                df_filtrado = df_eventos
                mensagem = f"Número de Leads Recebidos: {len(df_filtrado)}"
            elif selection == "Com Propostas Enviadas":
                df_filtrado = df_eventos_com_proposta_enviada[df_eventos_com_proposta_enviada['Data Envio Proposta'].notnull()]
                mensagem = f"Número de Propostas Enviadas: {len(df_filtrado)}"
            elif selection == "Confirmados":
                df_filtrado = df_eventos[df_eventos['Status do Evento'] == 'Confirmado']
                mensagem = f"Número de Eventos Confirmados: {len(df_filtrado)}"
            elif selection == "Declinados":
                df_filtrado = df_eventos[df_eventos['Status do Evento'] == 'Declinado']
                mensagem = f"Número de Eventos Declinados: {len(df_filtrado)}"
            elif selection == "Em Negociação":
                df_filtrado = df_eventos[df_eventos['Status do Evento'] == 'Em negociação']
                mensagem = f"Número de Eventos em Negociação: {len(df_filtrado)}"
            else:
                df_filtrado = None
                mensagem = None
                st.warning("Selecione um status de evento")

            # Exibição
            if df_filtrado is not None:
                df_filtrado_download = df_filtrado.copy()
                df_filtrado = format_columns_brazilian(df_filtrado, ['Valor Total', 'Número de Pessoas', 'Valor AB', 'Valor Locação Total', 'Valor Imposto', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Taxa Serviço', 'Valor Acréscimo Forma de Pagamento', 'Valor Imposto', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico'])
                df_filtrado = df_filtrado.drop(columns=['Is Aditivo'])
                st.dataframe(df_filtrado, width='stretch', hide_index=True)
                col1, col2 = st.columns([4, 1], vertical_alignment = "center")
                with col1:
                    st.markdown(mensagem)
                with col2:
                    button_download(df_filtrado_download, f'eventos_{selection}', f'download_eventos_{selection}')
                
            st.write('')


    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.markdown("### Motivo do Declínio")
            st.write('')
            grafico_barras_motivo_declinio(df_eventos_ano, filtro_tipo_data)
            st.write('')

if __name__ == "__main__":
    main()
