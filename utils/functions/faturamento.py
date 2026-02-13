import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *

def get_parcelas_por_tipo_data(df_parcelas, df_eventos, filtro_data, ano):
    if filtro_data == 'Competência':
        df = df_parcelas.merge(
            df_eventos[['Data Evento', 'ID Evento']],
            how='left',
            on='ID Evento'
        )
        df = df_filtrar_ano(df, 'Data Evento', ano)
        return df
    elif filtro_data == 'Recebimento (Caixa)':
        df = df_filtrar_ano(df_parcelas, 'Data Recebimento', ano)
        return df
    elif filtro_data == 'Vencimento':
        df = df_filtrar_ano(df_parcelas, 'Data Vencimento', ano)
        return df


def montar_tabs_geral(df_parcelas, casa, lista_ids_casas, tipo_data, df_orcamentos):

    if tipo_data == 'Competência':
        tipo_data = 'Data Evento'
    elif tipo_data == 'Recebimento (Caixa)':
        tipo_data = 'Data Recebimento'
    elif tipo_data == 'Vencimento':
        tipo_data = 'Data Vencimento'
    else: return

    tab_names = ['**Total de Eventos**']
    tabs = st.tabs(tab_names)
    with tabs[0]:
        st.markdown(f"#### Faturamento Total de Eventos - {casa}")
        grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, lista_ids_casas)
    # with tabs[1]:
    #     st.markdown("#### Alimentos e Bebidas")
    #     grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'A&B', df_orcamentos, id_casa)
    # with tabs[2]:
    #     st.markdown("#### Couvert")
    #     grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Couvert', df_orcamentos, id_casa)
    # with tabs[3]:
    #     st.markdown("#### Locação")
    #     grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Locação', df_orcamentos, id_casa)
    # with tabs[4]:
    #     st.markdown("#### Serviço")
    #     grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Serviço', df_orcamentos, id_casa)


def montar_tabs_priceless(df_parcelas_casa, id_casa, df_eventos, tipo_data, df_orcamentos):

    if tipo_data == 'Competência':
        tipo_data = 'Data Evento'
    elif tipo_data == 'Recebimento (Caixa)':
        tipo_data = 'Data Recebimento'
    elif tipo_data == 'Vencimento':
        tipo_data = 'Data Vencimento'
    
    df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas_casa, df_eventos)
    tab_names = ['**Total de Eventos - Priceless**', '**Locação Aroo**', '**Locação Anexo**', '**Locação Notiê**', '**Locação Mirante**', '**Alimentos e Bebidas**']
    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.markdown("### Total de Eventos - Priceless")
        grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, [149])
    with tabs[1]:
        st.markdown("### Locação Aroo")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Aroo", f"Aroo-{tipo_data}")
    with tabs[2]:
        st.markdown("### Locação Anexo")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Anexo", f"Anexo-{tipo_data}")
    with tabs[3]:
        st.markdown("### Locação Notiê")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Notiê", f"Notie-{tipo_data}")
    with tabs[4]:
        st.markdown("### Locação Mirante")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Mirante", f"Mirante-{tipo_data}")
    with tabs[5]:
        st.markdown("### Alimentos e Bebidas")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'A&B', df_orcamentos, id_casa)


def valores_labels_formatados(lista_valores):
    # Labels formatados
    labels = [format_brazilian(v) for v in lista_valores]

    # Dados com labels
    lista_valores_formatados = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(lista_valores, labels)]

    return lista_valores_formatados


# Total de Eventos
def grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, lista_ids_casa):
    df_parcelas = df_parcelas.copy()

    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month

    # Agrupa os valores por mês
    df_parcelas_agrupado = df_parcelas.groupby('Mes')['Valor Parcela'].sum().reset_index()
    
    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    df_parcelas_agrupado = df_meses.merge(df_parcelas_agrupado, how='left', on='Mes')
    df_parcelas_agrupado.fillna(0, inplace=True)

    # Filtra as casas selecionadas
    df_orcamentos = df_orcamentos[df_orcamentos['ID Casa'].isin(lista_ids_casa)]

    # Cria lista de valores
    total_eventos = df_parcelas_agrupado['Valor Parcela'].tolist()
    valores_orcamentos = df_orcamentos.copy().groupby(['Mês'])['Valor'].sum().reset_index()

    # Labels formatados
    labels = [format_brazilian(v) for v in total_eventos]

    # Dados com labels
    dados_eventos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_eventos, labels)]
    dados_orcamentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(valores_orcamentos['Valor'], valores_orcamentos['Valor'].apply(format_brazilian))]
    
    # Options do grafico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "show": True,
            "data": ["Orçamento de Eventos", "Faturamento de Eventos"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "0",
            "right": "4%",
            "bottom": "0%",
            "containLabel": True
        },
        "xAxis": [
            {
                "type": "category",
                "data": nomes_meses
            }
        ],
        "yAxis": [
            {
                "show": False
            }
        ],
        "series": [
            {
                "name": "Orçamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_orcamentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Faturamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_eventos_com_labels,
                "itemStyle": {
                    "color": "#FAC858"
                }
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key=f"chart_total_eventos_{tipo_data}")
    
    
    # Dicionário para mapear os meses
    meses = {
        "Jan": "01",
        "Fev": "02",
        "Mar": "03",
        "Abr": "04",
        "Mai": "05",
        "Jun": "06",
        "Jul": "07",
        "Ago": "08",
        "Set": "09",
        "Out": "10",
        "Nov": "11",
        "Dez": "12"
    }
    
    # Obter o mês correspondente ao mês selecionado
    if mes_selecionado != None:
        mes_selecionado = meses[mes_selecionado]
        
        col1, col2, col3 = st.columns([1, 12, 1])
        with col2:
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            if 'Total Gazit' in df_parcelas.columns:
                df_parcelas.drop(columns=['Total Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor Total Locação' in df_parcelas.columns:
                df_parcelas.drop(columns=['Valor Total Locação'], inplace=True)
            df_parcelas.drop(columns=['Mes'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data Vencimento', 'Data Recebimento', 'Data Evento'])
            df_parcelas_download = df_parcelas.copy()
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            if df_parcelas is not None and not df_parcelas.empty:
                total_parcelas_mes = format_brazilian(df_parcelas['Valor Parcela'].sum())
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, width='stretch', hide_index=True)
        if df_parcelas is not None and not df_parcelas.empty:
            col1, col2 = st.columns([4, 1], vertical_alignment="center")
            with col1:
                st.markdown(f"**Valor Total das Parcelas: R$ {total_parcelas_mes}**")
            with col2:
                button_download(df_parcelas_download, f"Parcelas_{mes_selecionado}", key=f'download_parcelas_{mes_selecionado}')
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")


# Locação

def df_fracao_locacao_espacos(df_eventos):
    # Adiciona coluna de cálculo de fração de cada espaço em relação ao valor total de locação
    # Aroo
    df_eventos['Fracao_Aroo'] = (df_eventos['Valor Locação Aroo 1'] + df_eventos['Valor Locação Aroo 2'] + df_eventos['Valor Locação Aroo 3']) / df_eventos['Valor Total Locação']
    df_eventos['Fracao_Aroo'] = df_eventos['Fracao_Aroo'].fillna(0)

    # Anexo
    df_eventos['Fracao_Anexo'] = df_eventos['Valor Locação Anexo'] / df_eventos['Valor Total Locação']
    df_eventos['Fracao_Anexo'] = df_eventos['Fracao_Anexo'].fillna(0)

    # Notie
    df_eventos['Fracao_Notie'] = df_eventos['Valor Locação Notie'] / df_eventos['Valor Total Locação']
    df_eventos['Fracao_Notie'] = df_eventos['Fracao_Notie'].fillna(0)

    # Mirante
    df_eventos['Fracao_Mirante'] = df_eventos['Valor Locação Mirante'] / df_eventos['Valor Total Locação']
    df_eventos['Fracao_Mirante'] = df_eventos['Fracao_Mirante'].fillna(0)

    return df_eventos



# Gráficos de Locação dos espaços Priceless (Aroo, Anexo, Notiê e Mirante)
def grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, espaco, key):
    df_parcelas = df_parcelas.copy()

    # Normaliza
    df_parcelas['Categoria Parcela'] = df_parcelas['Categoria Parcela'].str.replace('ç', 'c')

    # Filtra pela categoria 'Locação'
    df_parcelas = (
    df_parcelas
    .loc[df_parcelas['Categoria Parcela'] == 'Locacão']
    .copy()
    )

    # Define o nome da coluna de valor da parcela de acordo com o espaço
    dict_espacos = {
        'Aroo': 'Valor Parcela AROO',
        'Anexo': 'Valor Parcela ANEXO',
        'Notiê': 'Valor Parcela Notie',
        'Mirante': 'Valor Parcela Mirante'
    }


    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month
    df_parcelas['Ano'] = df_parcelas[tipo_data].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano'])[dict_espacos[espaco]].sum().reset_index()

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[mes - 1] for mes in meses]
    
    # Cria lista de valores
    total_espaco = df_parcelas_agrupado[dict_espacos[espaco]].tolist()

    # Valores e labels formatados
    total_espaco_formatados = valores_labels_formatados(total_espaco)

    # Options do grafico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": [
            {
                "type": "category",
                "data": nomes_meses,
                "boundaryGap": True,
                "axisTick": {
                    "alignWithLabel": True
                }
            }
        ],
        "yAxis": [
            {
                "type": "value"
            }
        ],
        "series": [
            {
                "name": f"Faturamento de Locação {espaco}",
                "type": "bar",
                "barWidth": "60%",
                "data": total_espaco_formatados,
                "itemStyle": {
                    "color": "#FAC858"
                },
                "label": {
                "show": True,
                "position": "top",
                "color": "#000"  # cor do texto
                }
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    mes_selecionado = st_echarts(option, events=events, height=300, width="100%", key=key)
    
    # Dicionário para mapear os meses
    meses = {
        "Janeiro": "01",
        "Fevereiro": "02",
        "Março": "03",
        "Abril": "04",
        "Maio": "05",
        "Junho": "06",
        "Julho": "07",
        "Agosto": "08",
        "Setembro": "09",
        "Outubro": "10",
        "Novembro": "11",
        "Dezembro": "12"
    }
    
    # Obter o mês correspondente ao mês selecionado
    if mes_selecionado != None:
        mes_selecionado = meses[mes_selecionado]
        
        col1, col2, col3 = st.columns([1, 12, 1])
        with col2:
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            df_parcelas.drop(columns=['Mes', 'Ano', 'Valor Total Locação', 'Total Gazit', 'Repasse_Gazit_Bruto', 'Repasse_Gazit_Liquido'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data Vencimento', 'Data Recebimento', 'Data Evento'])
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            df_parcelas_download = df_parcelas.copy()
            if df_parcelas is not None and not df_parcelas.empty:
                total_parcelas_mes = format_brazilian(df_parcelas['Valor Parcela'].sum())
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação', 'Valor Parcela Aroos', 'Valor Parcela Anexo', 'Valor Parcela Notiê', 'Valor Parcela Mirante'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, width='stretch', hide_index=True)
        if df_parcelas is not None and not df_parcelas.empty:
            col1, col2 = st.columns([4, 1], vertical_alignment="center")
            with col1:
                st.markdown(f"**Valor Total das Parcelas: R$ {total_parcelas_mes}**")
            with col2:
                button_download(df_parcelas_download, f"Parcelas_{mes_selecionado}", key=f"download_parcelas_{mes_selecionado}")
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")

# Gráfico de Faturamento por Categoria de Evento
def grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, categoria_evento, df_orcamentos, id_casa):
    
    df_parcelas = df_parcelas.copy()
    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month

    # Filtra pela categoria
    df_parcelas = (
    df_parcelas
    .loc[df_parcelas['Categoria Parcela'] == categoria_evento]
    .copy()
    )

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes'])['Valor Parcela'].sum().reset_index()

    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    df_parcelas_agrupado = df_meses.merge(df_parcelas_agrupado, how='left', on='Mes')
    df_parcelas_agrupado.fillna(0, inplace=True)
    
    # Cria lista de valores
    total_categoria = df_parcelas_agrupado['Valor Parcela'].tolist()
    if id_casa == -1:
        df_valores_orcamentos = df_orcamentos[df_orcamentos['Categoria Orcamento'] == categoria_evento].copy().groupby(['Mês', 'Categoria Orcamento'])['Valor'].sum().reset_index()
    else:
        df_valores_orcamentos = df_orcamentos[(df_orcamentos['ID Casa'] == id_casa) & (df_orcamentos['Categoria Orcamento'] == categoria_evento)].copy().groupby(['Mês', 'Categoria Orcamento'])['Valor'].sum().reset_index()

    # Valores e labels formatados
    labels = [format_brazilian(v) for v in total_categoria]
    df_valores_orcamentos['Valor'] = df_valores_orcamentos['Valor'].round(2)

    # Dados com labels
    dados_categoria_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_categoria, labels)]
    dados_orcamentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(df_valores_orcamentos['Valor'], df_valores_orcamentos['Valor'].apply(format_brazilian))]

    # Options do grafico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "show": True,
            "data": ["Orçamento", "Faturamento"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "0",
            "right": "4%",
            "bottom": "0%",
            "containLabel": True
        },
        "xAxis": [
            {
                "type": "category",
                "data": nomes_meses
            }
        ],
        "yAxis": [
            {
                "show": False
            }
        ],
        "series": [
            {
                "name": "Orçamento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_orcamentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Faturamento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_categoria_com_labels,
                "itemStyle": {
                    "color": "#FAC858"
                }
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key=f"chart_faturamento_{categoria_evento}")
    
    # Dicionário para mapear os meses
    meses = {
        "Jan": "01",
        "Fev": "02",
        "Mar": "03",
        "Abr": "04",
        "Mai": "05",
        "Jun": "06",
        "Jul": "07",
        "Ago": "08",
        "Set": "09",
        "Out": "10",
        "Nov": "11",
        "Dez": "12"
    }
    
    # Obter o mês correspondente ao mês selecionado
    if mes_selecionado != None:
        mes_selecionado = meses[mes_selecionado]
        
        col1, col2, col3 = st.columns([1, 12, 1])
        with col2:
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            df_parcelas.drop(columns=['Mes'], inplace=True)
            if 'Total Gazit' in df_parcelas.columns:
                df_parcelas.drop(columns=['Total Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor Total Locação' in df_parcelas.columns:
                df_parcelas.drop(columns=['Valor Total Locação'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data Vencimento', 'Data Recebimento', 'Data Evento'])
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            if df_parcelas is not None and not df_parcelas.empty: df_parcelas_download = df_parcelas.copy()
            if df_parcelas is not None and not df_parcelas.empty:
                total_parcelas_mes = format_brazilian(df_parcelas['Valor Parcela'].sum())
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, width='stretch', hide_index=True)
        if df_parcelas is not None and not df_parcelas.empty:
            col1, col2 = st.columns([4, 1], vertical_alignment="center")
            with col1:
                st.markdown(f"**Valor Total das Parcelas: R$ {total_parcelas_mes}**")
            with col2:
                button_download(df_parcelas_download, f"Parcelas_{mes_selecionado}", key=f"button_download_parcelas_{mes_selecionado}")
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")


# Gráfico de Faturamento por Classificação do Evento (Tipo de Evento, Modelo de Evento, Segmento)
def grafico_linhas_faturamento_classificacoes_evento(df_eventos, lista_ids_casa, coluna_categoria):
    # Filtro por casa, se aplicável
    df_eventos = df_eventos[df_eventos['ID Casa'].isin(lista_ids_casa)].copy()

    if df_eventos.empty:
        st.error("Não há dados de eventos disponíveis para o gráfico.")
        return

    # Extrai mês do evento
    df_eventos['Mês'] = df_eventos['Data Evento'].dt.month
    df_eventos = df_eventos.groupby(['Mês', coluna_categoria])['Valor Total Evento'].sum().reset_index()

    # Dicionário de nomes dos meses
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    # DataFrame com todos os meses
    df_meses = pd.DataFrame({'Mês': list(meses.keys()), 'Nome_Mes': list(meses.values())})

    # Todas as categorias únicas
    categorias = df_eventos[coluna_categoria].unique().tolist()
    df_categorias = pd.DataFrame({coluna_categoria: categorias})

    # Gera combinações mês × categoria
    df_completo = pd.merge(
        df_meses.assign(key=1), 
        df_categorias.assign(key=1), 
        on='key'
    ).drop('key', axis=1)

    # Merge com dados reais
    df_completo = df_completo.merge(df_eventos, how='left', on=['Mês', coluna_categoria])
    df_completo['Valor Total Evento'] = df_completo['Valor Total Evento'].fillna(0)

    # Lista de valores para cada categoria
    valores_por_categoria = {}
    for categoria in categorias:
        df_filtrado = df_completo[df_completo[coluna_categoria] == categoria].sort_values(by='Mês')
        valores = df_filtrado['Valor Total Evento'].round(2).tolist()
        labels = [format_brazilian(v) for v in valores]
        valores_por_categoria[categoria] = [
            {
                "value": v,
                "label": {"show": False}
            } for v, lbl in zip(valores, labels)
        ]

    # Monta a série do gráfico
    series = []
    for categoria, valores in valores_por_categoria.items():
        series.append({
            "name": categoria,
            "type": "line",
            "stack": "Total",
            "label": {
                "show": True,
                "position": "top"
            },
            "areaStyle": {},
            "emphasis": {
                "focus": "series"
            },
            "data": valores
        })

    # Configuração do gráfico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "label": {
                    "backgroundColor": "#6a7985"
                }
            }
        },
        "legend": {
            "data": list(valores_por_categoria.keys())
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
            }
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": [{
            "type": "category",
            "boundaryGap": False,
            "data": list(meses.values())
        }],
        "yAxis": [{"type": "value"}],
        "series": series
    }
    st_echarts(options=option, height="320px")