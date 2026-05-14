import streamlit as st
import pandas as pd
from utils.queries_conciliacao import *
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import cores_casas
from decimal import Decimal
from streamlit_echarts import st_echarts


nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

# Filtra tabela de ajustes por casa e ano (de acordo com os seletores)
def define_df_ajustes(id_casa, ano):
    df_ajustes = GET_AJUSTES()
    if id_casa != 157:
        df_ajustes_filtrado = df_ajustes[df_ajustes["ID_Casa"] == id_casa]
        df_ajustes_filtrado = df_ajustes_filtrado[df_ajustes_filtrado['Data_Ajuste'].dt.year == ano]
    else: 
        df_ajustes_filtrado = df_ajustes[df_ajustes['Data_Ajuste'].dt.year == ano]

    return df_ajustes_filtrado


def total_ajustes_mes(df_ajustes_filtrado):
    # Pega o mês da data do ajuste
    df_ajustes_filtrado_copia = df_ajustes_filtrado.copy()
    df_ajustes_filtrado_copia['Mes'] = df_ajustes_filtrado_copia['Data_Ajuste'].dt.month

    # Ajustes positivos
    ajustes_pos = df_ajustes_filtrado_copia[df_ajustes_filtrado_copia['Valor'] > 0].groupby(['Mes'])['Valor'].sum().reindex(range(1, 13), fill_value=0).reset_index()
    lista_ajustes_pos_mes = ajustes_pos['Valor'].tolist()
    lista_ajustes_pos_mes = [float(valor) if isinstance(valor, Decimal) else valor for valor in lista_ajustes_pos_mes]
    
    # Ajustes negativos
    ajustes_neg = df_ajustes_filtrado_copia[df_ajustes_filtrado_copia['Valor'] < 0].groupby(['Mes'])['Valor'].sum().reindex(range(1, 13), fill_value=0).reset_index()
    lista_ajustes_neg_mes = ajustes_neg['Valor'].tolist()
    lista_ajustes_neg_mes = [float(valor) if isinstance(valor, Decimal) else valor for valor in lista_ajustes_neg_mes]

    # Lista com valor total de ajustes por mês (uma de positivos, outra de negativos)
    lista_ajustes_pos_mes_fmt = valores_labels_formatados(lista_ajustes_pos_mes) 
    lista_ajustes_neg_mes_fmt = valores_labels_formatados(lista_ajustes_neg_mes)

    return lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt


def qtd_ajustes_mes(df_ajustes_filtrado):
    # Pega o mês da data do ajuste
    df_ajustes_filtrado_copia = df_ajustes_filtrado.copy()
    df_ajustes_filtrado_copia['Mes'] = df_ajustes_filtrado_copia['Data_Ajuste'].dt.month

    # Contabiliza ajustes por mês
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    df_ajustes_filtrado_copia = df_ajustes_filtrado_copia.merge(df_meses, on='Mes', how='right')

    ajustes_mes = df_ajustes_filtrado_copia.groupby(['Mes'])['Casa'].count().reset_index()
    ajustes_mes.rename(columns = {'Casa':'Qtd_Ajustes'}, inplace=True)

    # Lista com qtd de ajustes por mês
    lista_qtd_ajustes_mes = ajustes_mes['Qtd_Ajustes'].tolist() 
    return lista_qtd_ajustes_mes


# Contabiliza cada categoria de ajuste para gráfico de pizza - exibido ao clicar no gráfico de valor total por mês
def contagem_categorias(df, categoria):
    df_copia = df.copy()
    
    if categoria in ['', None]:
        # Conta os NaN/None e, se quiser, strings vazias também
        contagem = df_copia['Categoria'].isna().sum() + (df_copia['Categoria'] == '').sum()
    else:
        contagem = int((df_copia['Categoria'] == categoria).sum())
    
    return int(contagem)


# Função auxiliar para gráfico com todas as casas
def lista_ajustes_casa(casa, ano):
    df_ajustes = GET_AJUSTES()
    df_ajustes_casa = df_ajustes[(df_ajustes['Casa'] == casa) & (df_ajustes['Data_Ajuste'].dt.year == ano)].copy()
    df_ajustes_casa.loc[:, 'Mes'] = df_ajustes_casa['Data_Ajuste'].dt.month

    # df_total_ajustes_mes = df_ajustes_casa.groupby(['Mes'])['Valor'].sum().reset_index()

    # Quantidade de ajustes por mês de cada casa
    df_qtd_ajustes_mes = df_ajustes_casa.groupby(['Mes'])['Valor'].count().reindex(range(1, 13), fill_value=0).reset_index()
    lista_qtd_ajustes_mes = df_qtd_ajustes_mes['Valor'].tolist()

    return lista_qtd_ajustes_mes


# Primeiro gráfico: com todos os meses e todas as casas
def grafico_ajustes_todas_casas(casas_validas, nomes_meses, lista_ajustes_casas):
    series = [
        {
            "name": nome,
            "type": "bar",
            "barGap": "10%",
            "data": lista_ajustes_casas[i],
            "itemStyle": {"color": cores_casas[i]}
        }
        for i, nome in enumerate(casas_validas)
    ]

    grafico_ajustes_todas_casas = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": casas_validas,
            "orient": "vertical",   # legenda em coluna
            "right": "0%",        
            "top": "center",
            "backgroundColor": "#ffffff55",
        },
        "grid": {
            "left": "2%", 
            "right": "23%",  
            "containLabel": True},
        "xAxis": [{
            "type": "category", 
            "axisTick": {"show": True}, 
            "data": nomes_meses}],
        "yAxis": [
            {
            "type": "value", 
            }
        ],
        "series": series
    }

    st_echarts(options=grafico_ajustes_todas_casas, height="600px", width="100%")


# Gráfico de pizza: exibido ao clicar no gráfico de contagem por mês
def grafico_pizza_cont_categ(categ1, categ2, categ3, categ4, categ5, categ6, categ7):
    grafico_contagem_categ = {
        "tooltip": {
            "trigger": "item"
        },
        "legend": {
            "orient": "vertical",   # legenda em coluna
            "left": "0%",        
            "top": "center"
        },
        "series": [
            {
                "name": "Contagem de categorias",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["70%", "50%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2
                },
                "label": {
                    "show": False,
                    "position": "center"
                },
                "emphasis": {
                    "label": {
                        "show": False,
                        "fontSize": 15,
                        "fontWeight": "bold"
                    }
                },
                "labelLine": {
                    "show": False
                },
                "data": [
                    { "value": categ1, "name": "Tesouraria - Depósito em conta" },
                    { "value": categ2, "name": "Tesouraria - Despesa paga em dinheiro" },
                    { "value": categ3, "name": "Receita de evento recebido via cartão de credito Zigpay/Cielo" },
                    { "value": categ4, "name": "Adição de saldo no cartão pré-pago" },
                    { "value": categ5, "name": "RESG/VENCTO CDB" },
                    { "value": categ6, "name": "APLICACAO CDB" },
                    { "value": categ7, "name": "Sem categoria lançada" }
                ]
            }
        ]
    }
    st_echarts(options=grafico_contagem_categ, height="300px")


# Primeiro gráfico: contagem de ajustes por mês
def grafico_qtd_ajustes_mes(lista_qtd_ajustes_mes):
    grafico_qtd_ajustes_mes = {
        "tooltip": {
            "trigger": 'axis',
            "axisPointer": {
            "type": 'shadow'
            }
        },
        "grid": {
            "left": "4%",
            "right": "4%",
            "bottom": "0%",
            "containLabel": True
        },
        "xAxis": [
            {
            "type": 'category',
            "axisTick": { "show": False },
            "data": nomes_meses
            }
        ],
        "yAxis": [
            {
            "type": 'value'
            }
        ],
        "series": [
            {
            "name": 'Quantidade de Ajustes',
            "type": 'bar',
            "barWidth": "50%",
            "barGap": "5%",
            "data": lista_qtd_ajustes_mes,
            "itemStyle": {
                "color": "#1C6EBA"
            },
            "label": {
                "show": True,
                "position": "top" 
            }
            }
        ]
    }

    # Evento de clique - abre tabela de ajustes detalhada e gráfico de pizza
    events = {
        "click": "function(params) { return params.name; }"
    }

    st_echarts(options=grafico_qtd_ajustes_mes, events=events, height="400px", width="100%")


# Segundo gráfico: valor total de ajustes por mês
def grafico_total_ajustes_mes(df_ajustes_filtrado, lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt):
    grafico_total_ajustes_mes = {
        "tooltip": {
            "trigger": 'axis',
            "axisPointer": {
            "type": 'shadow'
            }
        },
        "grid": {
            "left": "4%",
            "right": "4%",
            "bottom": "0%",
            "containLabel": True
        },
        "xAxis": [
            {
            "type": 'category',
            "axisTick": { "show": True },
            "data": nomes_meses
            }
        ],
        "yAxis": [
            {
            "type": 'value'
            }
        ],
        "series": [
            {
            "name": 'Total de Ajustes Positivos',
            "type": 'bar',
            "barWidth": "40%",
            "barGap": "5%",
            "data": lista_ajustes_pos_mes_fmt,
            "itemStyle": {
                "color": "#F1C61A"
            },
            "label": {
                "show": True,
                "position": "left",
            }
            },
            {
            "name": 'Total de Ajustes Negativos',
            "type": 'bar',
            "barWidth": "40%",
            "barGap": "5%",
            "data": lista_ajustes_neg_mes_fmt,
            "itemStyle": {
                "color": "#F1C61A"
            },
            "label": {
                "show": True,
                "position": "bottom",
            }
            }
        ]
    }

    # Evento de clique - abre tabela de ajustes detalhada e gráfico de pizza
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibe o gráfico
    mes_selecionado = st_echarts(options=grafico_total_ajustes_mes, events=events, height="400px", width="100%")
    
    if not mes_selecionado:
        st.info("Selecione um mês para visualizar os ajustes correspondentes")

    else:
        st.divider()
        meses = {
        "Jan": "Janeiro",
        "Fev": "Fevereiro",
        "Mar": "Março",
        "Abr": "Abril",
        "Mai": "Maio",
        "Jun": "Junho",
        "Jul": "Julho",
        "Ago": "Agosto",
        "Set": "Setembro",
        "Out": "Outubro",
        "Nov": "Novembro",
        "Dez": "Dezembro"
        }
        mes = meses[mes_selecionado]
        st.subheader(f"Ajustes - {mes}")

        for mes in nomes_meses:
            if mes_selecionado == mes:
                mes_selecionado = nomes_meses.index(mes) + 1
        
        # Exibe df de ajustes do mês selecionado
        df_ajustes_formatado = df_ajustes_filtrado[df_ajustes_filtrado['Data_Ajuste'].dt.month == mes_selecionado]
        df_ajustes_final = formata_df(df_ajustes_formatado)
        st.dataframe(df_ajustes_final, width='stretch', hide_index=True)

        st.divider()

        # Exibe gráfico de pizza da quantidade de ajustes por categoria
        df_contagem_categ1 = contagem_categorias(df_ajustes_formatado, 'Tesouraria - Depósito em conta')
        df_contagem_categ2 = contagem_categorias(df_ajustes_formatado, 'Tesouraria - Despesa paga em dinheiro')
        df_contagem_categ3 = contagem_categorias(df_ajustes_formatado, 'Receita de evento recebido via cartão de crédito Zigpay/Cielo')
        df_contagem_categ4 = contagem_categorias(df_ajustes_formatado, 'Adição de saldo no cartão pré-pago')
        df_contagem_categ5 = contagem_categorias(df_ajustes_formatado, 'RESG/VENCTO CDB')
        df_contagem_categ6 = contagem_categorias(df_ajustes_formatado, 'APLICACAO CDB')
        df_contagem_categ7 = contagem_categorias(df_ajustes_formatado, None)

        st.subheader("Contagem de categorias")
        grafico_categorias = grafico_pizza_cont_categ(df_contagem_categ1, df_contagem_categ2, df_contagem_categ3, df_contagem_categ4, df_contagem_categ5, df_contagem_categ6, df_contagem_categ7)


