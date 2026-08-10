import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *
from utils.functions.acompanhamento_comissao import *
from utils.functions.faturamento import *


st.set_page_config(
    page_icon="📊",
    page_title="KPI's de Vendas - Cálculo da Comissão de Eventos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
    st.switch_page("Login.py")


def main():
    
    st.markdown(" <style>iframe{ height: 320px !important } ", unsafe_allow_html=True)
    config_sidebar()

    # Header
    col1, col2 = st.columns([5, 1], vertical_alignment='center')
    with col1:
        st.title("📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    st.divider()

    # Recupera dados dos eventos
    df_recebimentos = GET_RECEBIMENTOS_EVENTOS()
    df_orcamentos = GET_ORCAMENTOS_EVENTOS()
    df_eventos = GET_EVENTOS_COMISSOES()

    # Recupera dados dos eventos e parcelas para seção de faturamento
    df_orcamentos_faturamento = df_orcamentos.copy()
    df_eventos_faturamento = GET_EVENTOS_E_ADITIVOS_PRICELESS()
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

    # Acessos das comissões dos vendedores por logins de vendedores (email)
    df_acessos_comissoes = GET_ACESSOS_COMISSOES()
    user = st.session_state["user_login"]
    if user not in st.secrets["comissions_total_access"]["users"]:
        df_acessos_comissoes = df_acessos_comissoes[df_acessos_comissoes['Login'] == user]

    # Lista dos vendedores cujas comissões serão exibidas
    lista_vendedores_logado = df_acessos_comissoes['ID - Responsavel'].unique().tolist()

    # Formata tipos de dados do dataframe de eventos
    tipos_de_dados_eventos = {
		'Valor Locação Aroo 1': float,
		'Valor Locação Aroo 2': float,
		'Valor Locação Aroo 3': float,
		'Valor Locação Anexo': float,
		'Valor Locação Notie': float,
		'Valor Locação Mirante': float,
		'Valor Imposto': float,
		'Valor AB': float,
		'Valor Total Evento': float,
		'Valor Total Locação': float,
		'Valor Locação Gerador': float,
		'Valor Locação Mobiliário': float,
		'Valor Locação Utensílios': float,
		'Valor Taxa Serviço': float,
		'Valor Locação Espaço': float,
		'Valor Contratação Artístico': float,
		'Valor Contratação Técnico de Som': float,
		'Valor Contratação Bilheteria/Couvert Artístico': float,
		'Valor Mão de Obra Extra': float,
		'Valor Taxa Administrativa': float,
		'Valor Comissão BV': float,
		'Valor Extras Gerais': float,
		'Valor Acréscimo Forma de Pagamento': float
	}
    df_eventos_faturamento = df_eventos_faturamento.astype(tipos_de_dados_eventos, errors='ignore')
    df_eventos_faturamento['Data Contratação'] = pd.to_datetime(df_eventos_faturamento['Data Contratação'], errors='coerce')
    df_eventos_faturamento['Data Evento'] = pd.to_datetime(df_eventos_faturamento['Data Evento'], errors='coerce')
    # Formata tipos de dados do dataframe de parcelas
    tipos_de_dados_parcelas = {
        'Valor Parcela': float,
        'Categoria Parcela': str
    }
    df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
    df_parcelas['Data Vencimento'] = pd.to_datetime(df_parcelas['Data Vencimento'], errors='coerce')
    df_parcelas['Data Recebimento'] = pd.to_datetime(df_parcelas['Data Recebimento'], errors='coerce')
    # Formata tipos de dados do dataframe de orcamentos
    tipos_de_dados_orcamentos = {
        'Valor': float
    }
    df_orcamentos_faturamento = df_orcamentos_faturamento.astype(tipos_de_dados_orcamentos, errors='ignore')
    # Adiciona coluna de concatenação de ID e Nome Evento
    df_eventos_faturamento['ID_Nome_Evento'] = df_eventos_faturamento['ID Evento'].astype(str) + " - " + df_eventos_faturamento['Nome Evento']
    # Calcula o valor de repasse para Gazit
    df_eventos_faturamento = calcular_repasses_gazit(df_eventos_faturamento)

    st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)
    # Faturamento por Categoria
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Faturamento de Eventos", help='Comparar Orçamento e Faturamento para verificar o atingimento da meta')
            st.divider()
            col1, col2 = st.columns([1, 1], gap="large")
            with col1:
                lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'The Cavern - Almoço', 'Terraço Notie', 'Escritório Fabrica de Bares', 'Terraço Notie Novo']
                id_casa_faturamento, casa_faturamento, id_zigpay_faturamento = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto_comissao')
            with col2:
                ano = seletor_ano(2024, 2026, key='ano_faturamento')
        filtro_data_categoria = "Recebimento (Caixa)"

        # Filtros parcelas
        df_parcelas_filtradas_por_status = filtrar_por_classe_selecionada(df_parcelas, 'Status Evento', ['Confirmado'])
        df_parcelas_filtradas_por_data = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos_faturamento, filtro_data_categoria, ano)

        # Filtros orcamentos
        df_orcamentos_faturamento = filtrar_por_classe_selecionada(df_orcamentos_faturamento, 'Ano', [ano])
        if casa_faturamento != "Todas as Casas":
            df_orcamentos_faturamento = filtrar_por_classe_selecionada(df_orcamentos_faturamento, 'ID Casa', [id_casa_faturamento])
        else:
            df_acessos_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
            lista_acessos_casas = df_acessos_casas['ID Loja'].tolist()
            df_orcamentos_faturamento = filtrar_por_classe_selecionada(df_orcamentos_faturamento, 'ID Casa', lista_acessos_casas)
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            if filtro_data_categoria is None:
                st.warning("Por favor, selecione um filtro de data.")
            if casa_faturamento == "Todas as Casas":
                montar_tabs_geral(df_parcelas_filtradas_por_data, casa_faturamento, lista_acessos_casas, filtro_data_categoria, df_orcamentos_faturamento)
            else:
                df_parcelas_casa = df_filtrar_casa(df_parcelas_filtradas_por_data, casa_faturamento)
                if casa_faturamento == "Priceless":
                    montar_tabs_priceless(df_parcelas_casa, id_casa_faturamento, df_eventos_faturamento, filtro_data_categoria, df_orcamentos_faturamento)
                else:
                    montar_tabs_geral(df_parcelas_casa, casa_faturamento, [id_casa_faturamento], filtro_data_categoria, df_orcamentos_faturamento)
    st.write("")

    st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Cálculo da Comissão de Eventos")
            st.divider()
            # Vendedores
            df_vendedores = df_recebimentos[['ID - Responsavel', 'ID Responsavel', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'ID Casa']].copy().drop_duplicates()

            # Formata valores monetários
            df_recebimentos['Valor da Parcela'] = df_recebimentos['Valor da Parcela'].astype(float)
            df_recebimentos['Valor Total Evento'] = df_recebimentos['Valor Total Evento'].astype(float)
            df_recebimentos['Valor Total Imposto'] = df_recebimentos['Valor Total Imposto'].astype(float)
            df_recebimentos['Comissão Com Meta Atingida'] = df_recebimentos['Comissão Com Meta Atingida'].astype(float)
            df_recebimentos['Comissão Sem Meta Atingida'] = df_recebimentos['Comissão Sem Meta Atingida'].astype(float)
            df_orcamentos['Valor'] = df_orcamentos['Valor'].astype(float)
            
            # Seletores
            col0, col1, col2, col3= st.columns([1,1,1,1])
            with col0:
                lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'The Cavern - Almoço', 'Terraço Notie', 'Escritório Fabrica de Bares', 'Blue Note SP (Sala 2)',]
                id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='acompanhamento_comissao_casas')
                # Filtra por casa se não for "Todas as Casas"
                if id_casa != -1:
                    df_recebimentos = df_recebimentos[df_recebimentos['ID Casa'] == id_casa]
                    df_orcamentos = df_orcamentos[df_orcamentos['ID Casa'] == id_casa]
                    lista_vendedores_logado = df_acessos_comissoes[df_acessos_comissoes['ID Casa'] == id_casa]['ID - Responsavel'].tolist()
                else:
                    df_acesso_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
                    lista_ids_casas_acesso = df_acesso_casas["ID Loja"].to_list()
                    df_recebimentos = df_recebimentos[df_recebimentos['ID Casa'].isin(lista_ids_casas_acesso)]
                    df_orcamentos = df_orcamentos[df_orcamentos['ID Casa'].isin(lista_ids_casas_acesso)]
                    lista_vendedores_logado = df_acessos_comissoes[df_acessos_comissoes['ID Casa'].isin(lista_ids_casas_acesso)]['ID - Responsavel'].tolist()

            with col1:
                ano = seletor_ano(2025, 2026, key="seletor_ano_kpi_comissao")
            with col2:
                mes = seletor_mes(
                    "Selecionar mês:", key="seletor_mes_kpi_comissao"
                )
            with col3:
                if id_casa != -1:
                    df_vendedores = df_vendedores[df_vendedores['ID Casa'] == id_casa]
                id_vendedor, nome_vendedor = seletor_vendedor_logado("Comercial Responsável:", df_vendedores, lista_vendedores_logado, "seletor_vendedor_kpi_comissao")
            st.divider()

            # Verifica se há dados disponíveis para o mês e casa selecionados
            if df_recebimentos.empty and df_orcamentos.empty:
                st.error("Não há dados disponíveis de recebimentos e orçamentos para o mês e casa selecionados.")
                st.stop()
            elif df_recebimentos.empty:
                st.error("Não há dados disponíveis de recebimentos para o mês e casa selecionados.")
                st.stop()
            elif df_orcamentos.empty and id_casa != 173 and mes != '07' and ano != 2026:
                st.error("Não há dados disponíveis de orçamentos para o mês e casa selecionados.")
                st.stop()

            df_recebimentos = df_recebimentos[(df_recebimentos['Ano Recebimento'] == ano) & (df_recebimentos['Mês Recebimento'] == int(mes))]
            df_orcamentos = df_orcamentos[(df_orcamentos['Ano'] == ano) & (df_orcamentos['Mês'] == int(mes))]

            # Cópia de recebimentos sem o filtro de ID Responsavel
            df_recebimentos_total_mes = df_recebimentos.copy()

            # Calcula o recebimento total do mês
            total_recebido_mes = df_recebimentos['Valor da Parcela'].sum()

            # Calcula o orcamento do mês
            orcamento_mes = df_orcamentos['Valor'].sum()

            # Calcula o percentual de atingimento da meta
            if orcamento_mes > 0:
                porcentagem_atingimento = (total_recebido_mes / orcamento_mes) * 100
            else:
                porcentagem_atingimento = 0
            
            # Verifica se o vendedor atingiu a meta
            meta_atingida = False
            if total_recebido_mes >= orcamento_mes:
                meta_atingida = True
            if id_casa == 173 and mes == '07' and ano == 2026:
                meta_atingida = False

            # Calcula a comissão total para o mês, casa e vendedor(es) selecionados (menos para o Blue Note, pois possui o cálculo de comissão diferente) - considera apenas comissões por atingimento de meta/orçamento
            df_comissoes_por_meta = calcular_comissao(df_recebimentos, orcamento_mes, meta_atingida)
            comissao = 0

            # Map de vendedores e cargos
            vendedores_cargos = df_acessos_comissoes[['ID - Responsavel', 'Cargo', 'ID Casa']].drop_duplicates()
            if id_casa != -1:
                vendedores_cargos = vendedores_cargos[vendedores_cargos['ID Casa'] == id_casa]

            # Visualização das parcelas
            if df_recebimentos.empty:
                st.warning("Não há recebimentos e comissões para os filtros selecionados.")
                st.stop()
            else:
                vendedores = df_recebimentos['ID - Responsavel'].tolist()
                vendedores = adiciona_gerentes(vendedores, vendedores_cargos, id_casa)
                vendedores = list(set(vendedores))
                total_vendido = 0
                total_liquido = 0
                altura_header = 318
                altura_maxima_pagina = 1300
                altura_atual = altura_header
                altura_nome_vendedor = 52
                altura_linha = 35
                altura_expander = 86
                
                for vendedor in list(set(lista_vendedores_logado)):
                    df_vendedor = df_comissoes_por_meta[df_comissoes_por_meta['ID - Responsavel'] == vendedor].copy()
                    cargo_vendedor = vendedores_cargos[vendedores_cargos['ID - Responsavel'] == vendedor]['Cargo'].values[0]
                    ids_casas_vendedor = df_acessos_comissoes[df_acessos_comissoes['ID - Responsavel'] == vendedor]['ID Casa'].unique().tolist()
                    
                    # Define os tipos das colunas
                    df_vendedor['Ano Recebimento'] = df_vendedor['Ano Recebimento'].astype(int).astype(str)
                    df_vendedor['Mês Recebimento'] = df_vendedor['Mês Recebimento'].astype(int).astype(str)
                    
                    if 149 in ids_casas_vendedor and cargo_vendedor == 'Gerente de Eventos do Squad':
                        df_recebimentos_total_mes_outros_vendedores = df_recebimentos_total_mes[(df_recebimentos_total_mes['ID - Responsavel'] != vendedor) & (df_recebimentos_total_mes['ID Casa'] == 149)].copy()
                        df_recebimentos_gerente_priceless = calcular_comissao_gerente_priceless(df_recebimentos_total_mes_outros_vendedores, vendedor, id_casa, meta_atingida)
                        df_vendedor = pd.concat([df_vendedor, df_recebimentos_gerente_priceless], ignore_index=True)

                    for id_casa_regra_blue_note in IDS_REGRA_COMISSAO_BLUE_NOTE:
                        if id_casa_regra_blue_note in ids_casas_vendedor:
                            df_recebimentos_gerente_blue_note = calcular_comissao_blue_note(df_recebimentos_total_mes, vendedor, id_casa, id_casa_regra_blue_note)
                            df_vendedor = pd.concat([df_vendedor, df_recebimentos_gerente_blue_note], ignore_index=True)

                    df_vendedor['Valor Líquido'] = df_vendedor['Valor da Parcela'] - df_vendedor['Dedução Imposto']
                        
                    if not df_vendedor.empty:

                        df_vendedor = df_vendedor[['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'ID Parcela', 'Data Vencimento', 'Data Recebimento', 'Categoria Parcela', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', '% Comissão', 'Comissão']]

                        # Drop comissoes iguais a zero
                        df_vendedor = df_vendedor[df_vendedor['Comissão'] != 0]

                        # Calcula valores totais para a linha de total
                        total_vendido_vendedor = df_vendedor['Valor da Parcela'].sum()
                        total_vendido += total_vendido_vendedor # para o card de total vendido no final
                        total_liquido_vendedor = df_vendedor['Valor Líquido'].sum()
                        total_liquido += total_liquido_vendedor
                        total_deducao_imposto = df_vendedor['Dedução Imposto'].sum()
                        total_comissao = df_vendedor['Comissão'].sum()
                        comissao += total_comissao

                        lista_ids_eventos = df_vendedor['ID Evento'].unique().tolist()
                        df_vendedor = df_format_date_columns_brazilian(df_vendedor, ['Data Vencimento', 'Data Recebimento'])
                        df_download_vendedor = df_vendedor.copy()
                        df_vendedor['ID Parcela'] = (
                            df_vendedor['ID Parcela']
                            .round(0)
                            .astype('Int64')  # aceita NaN
                        )
                        df_vendedor = df_vendedor.astype({
                            'ID Evento': str,
                            'ID Parcela': str,
                            'Valor da Parcela': str,
                            '% Comissão': str,
                            'Comissão': str,
                            'Data Vencimento': str,
                            'Data Recebimento': str,
                            'Categoria Parcela': str
                        })
                        linha_total = pd.DataFrame({
                            'Casa': ['Total'],
                            'ID Evento': [''],
                            'Nome Evento': [''],
                            'ID Parcela': [''],
                            'Valor da Parcela': [total_vendido_vendedor],
                            'Dedução Imposto': [total_deducao_imposto],
                            'Valor Líquido': [total_liquido_vendedor],
                            'Data Vencimento': [''],
                            'Data Recebimento': [''],
                            'Categoria Parcela': [''],
                            '% Comissão': [''],
                            'Comissão': [total_comissao]
                        })
                        df_vendedor = pd.concat([df_vendedor, linha_total], ignore_index=True)

                        # Calcula a altura do dataframe com a linha total e linha de cabeçalho
                        altura_dataframe = len(df_vendedor) * altura_linha + altura_linha
                        altura_vendedor = altura_nome_vendedor + altura_dataframe + altura_expander
                        altura_atual += altura_vendedor

                        # Formata as colunas
                        df_vendedor = format_columns_brazilian(df_vendedor, ['Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', '% Comissão', 'Comissão'])
                        df_vendedor = df_vendedor[['Casa', 'ID Evento', 'Nome Evento', 'ID Parcela', 'Categoria Parcela', 'Data Vencimento', 'Data Recebimento', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', '% Comissão', 'Comissão']]
                        df_vendedor_styled = df_vendedor.style.apply(highlight_total_row, axis=1)

                        # Formata a página para impressao
                        if altura_atual >= altura_maxima_pagina:
                            st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)
                            altura_atual = altura_vendedor
                        else:
                            altura_atual += altura_vendedor

                        if f'{id_vendedor} - {nome_vendedor}' == '-1 - Todos os vendedores' or f'{id_vendedor} - {nome_vendedor}' == vendedor:
                            # Exibe a comissão do vendedor
                            col1, col2 = st.columns([4, 1], vertical_alignment='center')
                            with col1:
                                st.markdown(f"#### {vendedor}")
                            with col2:
                                nome_arquivo = safe_sheet_name(f'comissao_{vendedor}')
                                button_download(df_download_vendedor, nome_arquivo, f'download_comissao_{vendedor}')

                            st.dataframe(df_vendedor_styled, width='stretch', hide_index=True)

                            with st.expander(f"Ver eventos correspondentes"):
                                df_eventos_vendedor = df_eventos[df_eventos['ID Evento'].isin(lista_ids_eventos)]
                                df_eventos_vendedor = format_columns_brazilian(df_eventos_vendedor, ['Valor Total', 'Valor AB', 'Valor Imposto'])
                                st.dataframe(df_eventos_vendedor[['ID Evento', 'Casa', 'Nome Evento', 'Cliente', 'Data Contratacao', 'Data Evento', 'Valor Total', 'Valor AB', 'Valor Imposto', 'Status Evento']], width='stretch', hide_index=True)

    st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            # Exibe os KPIs
            st.markdown(f"## Resumo Final da Comissão - {casa} - {mes}/{ano}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                kpi_card("Orçamento do Mês", f"R$ {format_brazilian(orcamento_mes)}", "rgb(30, 58, 138)", "white", "white")
            with col2:
                kpi_card("Faturamento do Mês", f"R$ {format_brazilian(total_recebido_mes)}", "rgb(30, 58, 138)", "white", "white")
            with col3:
                if id_casa in IDS_REGRA_COMISSAO_BLUE_NOTE:
                    meta_atingida = total_liquido >= orcamento_mes
                    porcentagem_atingimento = (total_liquido / orcamento_mes) * 100

                if meta_atingida:
                    kpi_card("Atingimento da Meta", f"{format_brazilian(porcentagem_atingimento)} %", "rgb(30, 58, 138)", "white", "rgb(0, 255, 100)")
                else:
                    kpi_card("Atingimento da Meta", f"{format_brazilian(porcentagem_atingimento)} %", "rgb(30, 58, 138)", "white", "rgb(255, 30, 30)")
            with col4:
                if id_casa in IDS_REGRA_COMISSAO_BLUE_NOTE:
                    total_vendido = total_liquido
                else:
                    total_vendido = total_recebido_mes
                kpi_card("Total Vendido/Recebido no Mês", f"R$ {format_brazilian(total_vendido)}", "rgb(30, 58, 138)", "white", "white")
            with col5:
                kpi_card("Comissão", f"R$ {format_brazilian(comissao)}", "rgb(30, 58, 138)", "white", "white")
            st.html("<br>")

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Farol - Eventos sem Comercial Responsável")
            st.divider()

            df_eventos_sem_comercial = df_eventos_faturamento[df_eventos_faturamento['Comercial Responsável'].isnull()]
            df_eventos_sem_comercial = df_formata_datas_sem_horario(df_eventos_sem_comercial, ['Data Evento', 'Data Contratação'])
            df_eventos_sem_comercial = format_columns_brazilian(df_eventos_sem_comercial, ['Valor Total Evento', 'Valor AB', 'Valor Imposto'])
            
            if id_casa != -1:
                df_eventos_sem_comercial = df_eventos_sem_comercial[df_eventos_sem_comercial['Casa'] == casa]

            st.dataframe(df_eventos_sem_comercial[['Casa','ID Evento', 'Nome Evento', 'Comercial Responsável', 'Cliente', 'Data Contratação', 'Data Evento', 'Valor Total Evento', 'Valor AB', 'Valor Imposto', 'Status Evento', 'Motivo Declínio', 'Observações']], width='stretch', hide_index=True)

if __name__ == "__main__":
    main()
