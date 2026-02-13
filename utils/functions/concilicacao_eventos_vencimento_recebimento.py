import streamlit as st
import pandas as pd
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from streamlit_echarts import st_echarts
from utils.functions.faturamento import *

def filtra_parcelas_atrasadas(df_parcelas):
    df_parcelas = df_parcelas.copy()
    df_parcelas = df_parcelas[df_parcelas['Data Recebimento'].isna() & (df_parcelas['Data Vencimento'] < pd.Timestamp.now().normalize())]
    return df_parcelas

def colorir_parcelas_recebidas(row):
    # Converta as datas se ainda não estiverem em datetime
    venc = pd.to_datetime(row['Data Vencimento'], format='%d-%m-%Y', errors='coerce')
    receb = pd.to_datetime(row['Data Recebimento'], format='%d-%m-%Y', errors='coerce')

    if row['ID Parcela'] == 'TOTAL':
        return ['background-color: #f0f2f6; color: black;'] * len(row)
    else:
        if pd.isna(venc) or pd.isna(receb):
            return [''] * len(row)
        if receb > venc:
            return ['background-color: #fff9c4'] * len(row)  # Atrasado
        else:
            return [''] * len(row)  # Em dia


def colorir_parcelas_vencidas(row):
    # Converta as datas se ainda não estiverem em datetime
    venc = pd.to_datetime(row['Data Vencimento'], format='%d-%m-%Y', errors='coerce')
    receb = pd.to_datetime(row['Data Recebimento'], format='%d-%m-%Y', errors='coerce')

    if row['ID Parcela'] == 'TOTAL':
        return ['background-color: #f0f2f6; color: black;'] * len(row)
    else:
        if pd.isna(receb) and venc < pd.Timestamp.now():
            return ['background-color: #ffcccc'] * len(row)  # Atrasado
        elif venc < receb:
            return ['background-color: #fff9c4'] * len(row)
        else:
            return [''] * len(row)  # Em dia


def grafico_barras_vencimento_x_recebimento(df_parcelas_recebimento, df_parcelas_vencimento, lista_ids_casa):
    
    if df_parcelas_recebimento.empty or df_parcelas_vencimento.empty:
        st.error("Não há dados de eventos disponíveis para o gráfico.")
        return
    
    df_parcelas_recebimento = df_parcelas_recebimento[df_parcelas_recebimento['ID Casa'].isin(lista_ids_casa)].copy()
    df_parcelas_vencimento = df_parcelas_vencimento[df_parcelas_vencimento['ID Casa'].isin(lista_ids_casa)].copy()
    
    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas_vencimento['Mes'] = df_parcelas_vencimento['Data Vencimento'].dt.month
    df_parcelas_recebimento['Mes'] = df_parcelas_recebimento['Data Recebimento'].dt.month
    
    # Agrupa os valores por mês
    df_vencimento_agrupado = df_parcelas_vencimento.groupby('Mes')['Valor Parcela'].sum().reset_index()
    df_recebimento_agrupado = df_parcelas_recebimento.groupby('Mes')['Valor Parcela'].sum().reset_index()

    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    
    df_vencimento_agrupado = df_meses.merge(df_vencimento_agrupado, how='left', on='Mes')
    df_recebimento_agrupado = df_meses.merge(df_recebimento_agrupado, how='left', on='Mes')
    
    df_vencimento_agrupado.fillna(0, inplace=True)
    df_recebimento_agrupado.fillna(0, inplace=True)

    # Cria lista de valores
    total_vencimento = df_vencimento_agrupado['Valor Parcela'].round(2).tolist()
    total_recebimento = df_recebimento_agrupado['Valor Parcela'].round(2).tolist()

    # Labels formatados
    labels_vencimento = [format_brazilian_without_decimal(v) for v in total_vencimento]
    labels_recebimento = [format_brazilian_without_decimal(v) for v in total_recebimento]

    # Dados com labels
    dados_vencimentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_vencimento, labels_vencimento)]
    dados_recebimentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000","formatter": lbl}} for v, lbl in zip(total_recebimento, labels_recebimento)]

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
            "data": ["Vencimento", "Recebimento"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "0%",
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
                "type": "value"
            }
        ],
        "series": [
            {
                "name": "Vencimento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_vencimentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Recebimento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_recebimentos_com_labels,
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
    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key="chart_vencimento_recebimento")

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
            df_parcelas_recebimento = df_filtrar_mes(df_parcelas_recebimento, 'Data Recebimento', mes_selecionado)
            df_parcelas_recebimento.drop(columns=['Mes'], inplace=True)
            
            df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data Vencimento', 'Data Recebimento', 'Data Evento'])
            df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)
            if df_parcelas_recebimento is not None and not df_parcelas_recebimento.empty:
                df_parcelas_recebimento_download = df_parcelas_recebimento.copy()
                total_recebido = format_brazilian(df_parcelas_recebimento['Valor Parcela'].sum())
                df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela'])

            df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data Vencimento', mes_selecionado)
            df_parcelas_vencimento.drop(columns=['Mes'], inplace=True)
            
            df_parcelas_vencimento = df_formata_datas_sem_horario(df_parcelas_vencimento, ['Data Vencimento', 'Data Recebimento', 'Data Evento'])
            df_parcelas_vencimento = rename_colunas_parcelas(df_parcelas_vencimento)
            if df_parcelas_vencimento is not None and not df_parcelas_vencimento.empty:
                df_parcelas_vencimento_download = df_parcelas_vencimento.copy()
                total_vencido = format_brazilian(df_parcelas_vencimento['Valor Parcela'].sum())
                df_parcelas_vencimento = format_columns_brazilian(df_parcelas_vencimento, ['Valor Parcela'])

        if df_parcelas_recebimento is not None and df_parcelas_vencimento is not None:
            df_parcelas_recebimento['ID Evento'] = df_parcelas_recebimento['ID Evento'].astype(int)
            df_parcelas_recebimento['ID Casa'] = df_parcelas_recebimento['ID Casa'].astype(int)
            df_parcelas_vencimento['ID Evento'] = df_parcelas_vencimento['ID Evento'].astype(int)
            df_parcelas_vencimento['ID Casa'] = df_parcelas_vencimento['ID Casa'].astype(int)

            # Inverter o dicionário
            meses_invertido = meses_invertido = {
                "01": "Janeiro",
                "02": "Fevereiro",
                "03": "Março",
                "04": "Abril",
                "05": "Maio",
                "06": "Junho",
                "07": "Julho",
                "08": "Agosto",
                "09": "Setembro",
                "10": "Outubro",
                "11": "Novembro",
                "12": "Dezembro"
            }
            nome_mes = meses_invertido[f'{mes_selecionado}'] 

            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.markdown(f"### Parcelas Recebidas em {nome_mes}")
            with col2:
                button_download(df_parcelas_recebimento_download, f'parcelas_recebidas_{nome_mes}', f'parcelas_recebidas{nome_mes}')
            # Adiciona linha de total
            linha_total_recebimento = pd.DataFrame({
                'ID Parcela': ['TOTAL'],
                'ID Evento': [''],
                'ID Casa': [''],
                'Casa': [''],
                'Nome Evento': [''],
                'Status Evento': [''],
                'Categoria Parcela': [''],
                'Valor Parcela': [total_recebido],
                'Data Vencimento': [''],
                'Status Pagamento': [''],
                'Data Recebimento': [''],
            })
            # Tipos de dados para string
            df_parcelas_recebimento = df_parcelas_recebimento.astype({
                'ID Parcela': str,
                'ID Evento': str,
                'Casa': str,
                'ID Casa': str,
                'Nome Evento': str,
                'Status Evento': str,
                'Categoria Parcela': str
            })
            df_parcelas_recebimento = pd.concat([df_parcelas_recebimento, linha_total_recebimento], ignore_index=True)
            df_parcelas_recebimento_styled = df_parcelas_recebimento.style.apply(colorir_parcelas_recebidas, axis=1)
            st.dataframe(df_parcelas_recebimento_styled,
                        height=35 * len(df_parcelas_recebimento) + 35,
                        width='stretch', hide_index=True)

            # Legenda de cores
            st.markdown("""
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #fff9c4; border: 1px solid #ccc; margin-right: 10px;"></div>
                    <span>Parcelas recebidas em atraso (podem ter a data de vencimento em outros meses)</span>
                </div>
            """, unsafe_allow_html=True)

            st.write("")

            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.markdown(f"### Parcelas com Vencimento em {nome_mes}")
            with col2:
                button_download(df_parcelas_vencimento_download, f'parcelas_vencidas_{nome_mes}', f'parcelas_vencidas{nome_mes}')
            linha_total_vencimento = pd.DataFrame({
                'ID Parcela': ['TOTAL'],
                'ID Evento': [''],
                'ID Casa': [''],
                'Casa': [''],
                'Nome Evento': [''],
                'Status Evento': [''],
                'Categoria Parcela': [''],
                'Valor Parcela': [total_vencido],
                'Data Vencimento': [''],
                'Status Pagamento': [''],
                'Data Recebimento': [''],
            })
            # Tipos de dados para string
            df_parcelas_vencimento = df_parcelas_vencimento.astype({
                'ID Parcela': str,
                'ID Evento': str,
                'ID Casa': str
            })
            df_parcelas_vencimento = pd.concat([df_parcelas_vencimento, linha_total_vencimento], ignore_index=True)
            df_parcelas_vencimento_styled = df_parcelas_vencimento.style.apply(colorir_parcelas_vencidas, axis=1)
            st.dataframe(df_parcelas_vencimento_styled,
                        height=35 * len(df_parcelas_vencimento) + 35,
                        width='stretch', hide_index=True)
            
            # Legenda de cores
            st.markdown("""
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #fff9c4; border: 1px solid #ccc; margin-right: 10px;"></div>
                    <span>Parcelas recebidas em atraso</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #ffcccc; border: 1px solid #ccc; margin-right: 10px;"></div>
                    <span>Parcelas vencidas e não recebidas</span>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
    else:
        st.markdown("Selecione um mês no gráfico para visualizar as parcelas recebidas e com vencimento no mês selecionado.")