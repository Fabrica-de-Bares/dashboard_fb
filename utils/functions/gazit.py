import streamlit as st
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *

def grafico_barras_repasse_mensal_vencimento(df_parcelas):
    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas['Mes'] = df_parcelas['Data Vencimento'].dt.month
    df_parcelas['Ano'] = df_parcelas['Data Vencimento'].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano']).agg({
        'Repasse_Gazit_Bruto': 'sum',
        'Repasse_Gazit_Liquido': 'sum'
    }).reset_index()

    df_parcelas_agrupado['Repasse_Gazit_Bruto'] = df_parcelas_agrupado['Repasse_Gazit_Bruto'].round(2)
    df_parcelas_agrupado['Repasse_Gazit_Liquido'] = df_parcelas_agrupado['Repasse_Gazit_Liquido'].round(2)

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[int(mes) - 1] for mes in meses]
    
    # Cria lista de valores
    total_repasse_bruto = df_parcelas_agrupado['Repasse_Gazit_Bruto'].tolist()
    total_repasse_liquido = df_parcelas_agrupado['Repasse_Gazit_Liquido'].tolist()

    # Labels formatados
    labels_brutos = [format_brazilian(v) for v in total_repasse_bruto]
    labels_liquidos = [format_brazilian(v) for v in total_repasse_liquido]

    # Dados com labels
    dados_brutos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_repasse_bruto, labels_brutos)]
    dados_liquidos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_repasse_liquido, labels_liquidos)]
    
    # Options do grafico
    # Montar gráfico
    option = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "show": True,
            "data": ["Repasse Bruto Gazit", "Repasse Líquido Gazit"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True
        },
        "xAxis": [{"type": "category", "data": nomes_meses}],
        "yAxis": [{"type": "value"}],
        "series": [
            {
                "name": "Repasse Bruto Gazit",
                "type": "bar",
                "barWidth": "35%",
                "data": dados_brutos_com_labels,
                "itemStyle": {"color": "#FAC858"}
            },
            {
                "name": "Repasse Líquido Gazit",
                "type": "bar",
                "barWidth": "35%",
                "barGap": "5%",
                "data": dados_liquidos_com_labels,
                "itemStyle": {"color": "#5470C6"}
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    resultado_clique = st_echarts(option, events=events, height=300, width="100%", key="chart_total_repasse_mensal_vencimento")
    # st_echarts embrulha o retorno do evento num objeto tipo-dict (chave 'chart_event')
    # nessa versão do Streamlit; em versões mais antigas o retorno já vem "cru"
    mes_selecionado = resultado_clique.get('chart_event') if hasattr(resultado_clique, 'get') else resultado_clique

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
    
    return mes_selecionado



def grafico_barras_repasse_mensal_recebimento(df_parcelas):

    # Extrai mês e ano da coluna 'Data Vencimento'
    df_parcelas['Mes'] = df_parcelas['Data Recebimento'].dt.month
    df_parcelas['Ano'] = df_parcelas['Data Recebimento'].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano']).agg({
        'Repasse_Gazit_Bruto': 'sum',
        'Repasse_Gazit_Liquido': 'sum'
    }).reset_index()

    df_parcelas_agrupado['Repasse_Gazit_Bruto'] = df_parcelas_agrupado['Repasse_Gazit_Bruto']
    df_parcelas_agrupado['Repasse_Gazit_Liquido'] = df_parcelas_agrupado['Repasse_Gazit_Liquido']

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[int(mes) - 1] for mes in meses]
    
    # Cria lista de valores
    total_repasse_bruto = df_parcelas_agrupado['Repasse_Gazit_Bruto'].tolist()
    total_repasse_liquido = df_parcelas_agrupado['Repasse_Gazit_Liquido'].tolist()

    # Labels formatados
    labels_brutos = [format_brazilian(v) for v in total_repasse_bruto]
    labels_liquidos = [format_brazilian(v) for v in total_repasse_liquido]

    # Dados com labels
    dados_brutos_com_labels = [{"value": v,
                                "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}}
                                for v, lbl in zip(total_repasse_bruto, labels_brutos)]
    dados_liquidos_com_labels = [{"value": v,
                                  "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl},}
                                  for v, lbl in zip(total_repasse_liquido, labels_liquidos)]
        
    # Options do grafico
    # Montar gráfico
    option = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "show": True,
            "data": ["Repasse Bruto Gazit", "Repasse Líquido Gazit"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True
        },
        "xAxis": [{"type": "category", "data": nomes_meses}],
        "yAxis": [{"type": "value"}],
        "series": [
            {
                "name": "Repasse Bruto Gazit",
                "type": "bar",
                "barWidth": "35%",
                "data": dados_brutos_com_labels,
                "itemStyle": {"color": "#FAC858"}
            },
            {
                "name": "Repasse Líquido Gazit",
                "type": "bar",
                "barWidth": "35%",
                "barGap": "5%",
                "data": dados_liquidos_com_labels,
                "itemStyle": {"color": "#5470C6"}
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    resultado_clique = st_echarts(option, events=events, height=300, width="100%", key="chart_total_repasse_mensal_recebimento")
    # st_echarts embrulha o retorno do evento num objeto tipo-dict (chave 'chart_event')
    # nessa versão do Streamlit; em versões mais antigas o retorno já vem "cru"
    mes_selecionado = resultado_clique.get('chart_event') if hasattr(resultado_clique, 'get') else resultado_clique

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
    
    return mes_selecionado


def resumo_vendas_gazit(total_de_vendas, retencao_impostos, valor_liquido_a_pagar, total_recebimento_anexo, total_recebimento_aroo):

    valor_a_pagar_anexo = format_brazilian(round(total_recebimento_anexo * 0.3, 2))
    valor_a_pagar_aroo = format_brazilian(round(total_recebimento_aroo * 0.7, 2))
    total_de_vendas = format_brazilian(total_de_vendas)
    retencao_impostos = format_brazilian(retencao_impostos)
    valor_liquido_a_pagar = format_brazilian(valor_liquido_a_pagar)
    total_recebimento_anexo = format_brazilian(total_recebimento_anexo)
    total_recebimento_aroo = format_brazilian(total_recebimento_aroo)
    
    st.markdown(f"""
        <style>
        .custom-table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .custom-table th, .custom-table td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        .custom-table thead tr {{
            background-color: #FAC858;
            color: #31333F;
        }}
        .custom-table tbody tr:last-child {{
            background-color: #f0f2f6;
            font-weight: bold;
        }}
        .custom-table td[colspan="3"] {{
            text-align: left;
        }}
        </style>

        <table class="custom-table">
        <thead>
            <tr>
            <th>Espaço</th>
            <th>% Contrato</th>
            <th>Vendas Brutas</th>
            <th>Valor a pagar</th>
            </tr>
        </thead>
        <tbody>
            <tr>
            <td>PRICELESS (ANEXO)</td>
            <td>30%</td>
            <td>{total_recebimento_anexo}</td>
            <td>{valor_a_pagar_anexo}</td>
            </tr>
            <tr>
            <td>AROO</td>
            <td>70%</td>
            <td>{total_recebimento_aroo}</td>
            <td>{valor_a_pagar_aroo}</td>
            </tr>
            <tr><td colspan="4" style="height: 10px; border: none;"></td></tr>
            <tr>
            <td colspan="3">Total de Vendas</td>
            <td>{total_de_vendas}</td>
            </tr>
            <tr>
            <td colspan="3">Retenção de Impostos 14,53%</td>
            <td>{retencao_impostos}</td>
            </tr>
            <tr>
            <td colspan="3">Valor Líquido a Pagar</td>
            <td>{valor_liquido_a_pagar}</td>
            </tr>
        </tbody>
        </table>
        """, unsafe_allow_html=True)
