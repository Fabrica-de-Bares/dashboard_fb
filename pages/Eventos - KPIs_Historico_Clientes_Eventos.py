import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_clientes_eventos import *

st.set_page_config(
	page_icon=":busts_in_silhouette:",
	page_title="KPI's de Vendas - Histórico e Recorrência de Clientes",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
    st.markdown(" <style>iframe{ height: 500px !important } ", unsafe_allow_html=True)
    config_sidebar()

    df_clientes_eventos = GET_CLIENTES_EVENTOS()

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title(":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
    with col2:
        st.button(label='Atualizar', key='atualizar_historico_clientes_eventos', on_click=st.cache_data.clear)
    st.divider()

    # Filtro por Casa
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'The Cavern']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='historico_clientes_eventos')
    if id_casa != -1:
        df_clientes_eventos = df_clientes_eventos[df_clientes_eventos['ID Casa'] == id_casa]
    else:
        df_acessos_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=['ID Loja', 'Loja', 'ID Zigpay'])
        lista_ids_casas = df_acessos_casas['ID Loja'].tolist()
        df_clientes_eventos = df_clientes_eventos[df_clientes_eventos['ID Casa'].isin(lista_ids_casas)]

    tab1, tab2 = st.tabs(["**Histórico de Clientes**", "**Recorrência de Clientes**"])

    with tab1:
        col1, col2 = st.columns([2, 3], vertical_alignment="center")
        with col1:
            st.markdown("## Histórico de Clientes", help="Buscar informações de cadastro dos clientes e informações de todos os eventos que já foram feitos por aquele cliente em todas as unidades.")

        df_clientes = df_clientes_eventos.copy().drop_duplicates(subset=['ID Cliente'])
        df_clientes['ID - Cliente'] = df_clientes['ID Cliente'].astype(str) + ' - ' + df_clientes['Cliente']
        lista_clientes = df_clientes['ID - Cliente'].tolist()
        
        with col2:
            clientes_selecionados = st.multiselect(
                label="Buscar Cliente",
                options=lista_clientes,
                default=None,
                key="casas_historico_clientes",
                placeholder="Nome do Cliente",
            )
        st.divider()

        if clientes_selecionados:
            lista_ids_clientes_selecionados = [int(cliente.split(' - ')[0]) for cliente in clientes_selecionados]
            df_clientes_selecionados = df_clientes[df_clientes['ID Cliente'].isin(lista_ids_clientes_selecionados)].copy()
            df_clientes_selecionados.fillna('Não informado', inplace=True)

            for _, cliente in df_clientes_selecionados.groupby('ID Cliente'):

                st.markdown(f'### :material/group:  {cliente['Cliente'].values[0]}')
                st.write('')

                col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small", vertical_alignment="top")
                with col1:
                    st.markdown(f'**Documento:** {cliente['Documento'].values[0]}')
                    st.markdown(f'**E-mail:** {cliente['Email'].values[0]}')
                with col2:
                    st.markdown(f'**Telefone:** {cliente['Telefone'].values[0]}')
                    st.markdown(f'**Pessoa de Contato:** {cliente['Pessoa de Contato'].values[0]}')
                with col3:
                    st.markdown(f'**Endereço:** {cliente['Endereço'].values[0]}')
                    st.markdown(f'**CEP:** {cliente['CEP'].values[0]}')
                if cliente['Setor Empresa'].values[0] != 'Não informado' or cliente['Razão Social'].values[0] != 'Não informado':
                    with col4:
                        st.markdown(f'**Razão Social:** {cliente["Razão Social"].values[0]}')
                        st.markdown(f'**Setor Empresa:** {cliente["Setor Empresa"].values[0]}')

                st.markdown("#### Eventos Realizados")
                df_eventos_realizados_cliente = df_clientes_eventos.copy()
                df_eventos_realizados_cliente = df_eventos_realizados_cliente[df_eventos_realizados_cliente['ID Cliente'] == cliente['ID Cliente'].values[0]]
                df_eventos_realizados_cliente = df_format_date_columns_brazilian(df_eventos_realizados_cliente, ['Data Evento', 'Data Recebimento Lead', 'Data Envio Proposta', 'Data Contratação'])
                df_eventos_realizados_cliente = format_columns_brazilian(df_eventos_realizados_cliente, ['Valor Total Evento', 'Valor AB', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Valor Imposto'])
                st.dataframe(df_eventos_realizados_cliente.drop(columns=['ID Cliente', 'Cliente', 'Documento', 'Email', 'Telefone', 'Pessoa de Contato', 'Endereço', 'CEP']), width='stretch', hide_index=True)
                st.divider()
        else:
            st.warning("Selecione um cliente para visualizar as informações.")
            st.divider()

    with tab2:
        col1, col2 = st.columns([2, 3], vertical_alignment='center')
        with col1:
            st.markdown("## Recorrência de Clientes")
        with col2:
            periodo = input_periodo_datas(key='data_inicio', label='Período de Competência do Evento')
        st.divider()  
        
        if periodo and len(periodo) == 2:
            data_inicio = periodo[0]
            data_fim = periodo[1]
            df_numero_clientes_periodo = df_clientes_eventos.copy()
            df_numero_clientes_periodo = df_numero_clientes_periodo[(df_numero_clientes_periodo['Data Evento'] >= data_inicio) & (df_numero_clientes_periodo['Data Evento'] <= data_fim)]
            df_numero_clientes_periodo['N° Eventos'] = df_numero_clientes_periodo.groupby('ID Cliente')['ID Evento'].transform('count')
            df_numero_clientes_periodo = df_numero_clientes_periodo.groupby('ID Cliente').agg({
                'Cliente': 'first',
                'Documento': 'first',
                'Email': 'first',
                'Telefone': 'first',
                'Pessoa de Contato': 'first',
                'Endereço': 'first',
                'CEP': 'first',
                'Data Evento': 'max',
                'Valor Total Evento': 'sum',
                'N° Eventos': 'first'
            }).reset_index()
            num_clientes_atendidos = len(df_numero_clientes_periodo)
            df_numero_clientes_periodo = df_numero_clientes_periodo.rename(columns={
                'Valor Total Evento': 'Valor Total Eventos',
                'Data Evento': 'Data Último Evento',
            })
            
            df_numero_clientes_periodo = df_numero_clientes_periodo.sort_values(by='N° Eventos', ascending=False).reset_index(drop=True)
            df_numero_clientes_periodo_formatado = df_format_date_columns_brazilian(df_numero_clientes_periodo, ['Data Último Evento'])
            df_numero_clientes_periodo_formatado = format_columns_brazilian(df_numero_clientes_periodo_formatado, ['Valor Total Eventos'])

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.1, 3, 0.1], gap="large", vertical_alignment="top")
                with col2:
                    st.markdown(f'### Clientes atendidos no período')
                    st.dataframe(df_numero_clientes_periodo_formatado, width='stretch', hide_index=True)
                    st.markdown(f'N° de Clientes Atendidos: {num_clientes_atendidos}')

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.1, 3, 0.1], gap="large", vertical_alignment="top")
                with col2:
                    st.markdown("### Top 10 Clientes em Nº de Eventos")
                    grafico_ranking_clientes_por_num_eventos(df_numero_clientes_periodo, key=f'ranking_clientes_num_{casa}')

            with st.container(border=True):
                col1, col2, col3 = st.columns([0.1, 3, 0.1], gap="large", vertical_alignment="top")
                with col2:
                    st.markdown("### Top 10 Clientes em Valor de Eventos")
                    df_numero_clientes_periodo = df_numero_clientes_periodo.sort_values(by='Valor Total Eventos', ascending=True).reset_index(drop=True)
                    grafico_ranking_clientes_por_valor_eventos(df_numero_clientes_periodo, key=f'ranking_clientes_valor_{casa}')

        elif not periodo or len(periodo) != 2:
            st.warning("Por favor, selecione um período válido.")

if __name__ == '__main__':
    main()