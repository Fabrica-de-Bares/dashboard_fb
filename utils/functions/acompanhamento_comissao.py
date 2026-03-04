import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *


def calcular_comissao_casa(row, orcamento_mes, meta_atingida):
    """
    Calcula a comissão com base na meta atingida e no valor recebido, de acordo com a regra de cada casa.
    """

    if row['ID Casa'] in [149, 122, 156, 115, 104, 114, 148, 105, 116, 160, 128, 145]: # Arcos, Girondino, Riviera, Orfeu, Bar Brahma - Centro, Bar Brahma - Granja, Jacaré, Bar Leo Centro, 
        if meta_atingida:
            percentual_comissao = row['Comissão Com Meta Atingida']
            comissao = round(row['Valor da Parcela'] * row['Comissão Com Meta Atingida'] / 100, 2)
        else:
            percentual_comissao = row['Comissão Sem Meta Atingida']
            comissao = round(row['Valor da Parcela'] * row['Comissão Sem Meta Atingida'] / 100, 2)
    # elif row['ID Casa'] == 105: # Jacaré
        # 2,5% de locação + 3,5% de A&B + 5% 'de Repasse artístico e Fornecedores
        # if row['Categoria Parcela'] == 'Locação':
        #     percentual_comissao = 2.5
        #     comissao = round(row['Valor da Parcela'] * percentual_comissao / 100, 2)
        # elif row['Categoria Parcela'] == 'A&B':
        #     percentual_comissao = 3.5
        #     comissao = round(row['Valor da Parcela'] * percentual_comissao / 100, 2)
        # elif row['Categoria Parcela'] == 'Repasse Artistico':
        #     comissao = round(row['Valor Total Parcelas'] * 0.05, 2)
    else:
        percentual_comissao = 0.0
        comissao = 0.0

    return comissao, percentual_comissao


def calcular_comissao(df_recebimentos, orcamento_mes, meta_atingida):
    """
    Calcula a comissão total com base nos recebimentos e orçamentos (atingimento de meta). Não serve para a comissão do Blue Note
    """
    df_comissoes = df_recebimentos.copy()
    df_comissoes['Dedução Imposto'] = 0.0

    # Calcula a comissão para cada recebimento
    if not df_comissoes.empty:
        # Calcula a comissão para cada casa em relação ao atingimento de meta
        resultado = df_comissoes.apply(calcular_comissao_casa, axis=1, args=(orcamento_mes, meta_atingida))
        df_comissoes['Comissão'] = resultado.apply(lambda x: x[0])
        df_comissoes['% Comissão'] = resultado.apply(lambda x: x[1])

    return df_comissoes


def adiciona_gerentes(vendedores, vendedores_cargos, id_casa):
    vendedores_cargos = vendedores_cargos.copy()
    for _, item in vendedores_cargos.iterrows():
        if id_casa != -1:
            if item['Cargo'] == 'Gerente de Eventos' and item['ID Casa'] == id_casa:
                vendedores.append(item['ID - Responsavel'])
        else:
            if item['Cargo'] == 'Gerente de Eventos':
                vendedores.append(item['ID - Responsavel'])
    return vendedores

def calcular_comissao_gerente_priceless(df_recebimentos_total_mes, id_responsavel, id_casa):
    if id_casa in [149, -1]:
        df_recebimentos_total_mes = df_recebimentos_total_mes[df_recebimentos_total_mes['ID Casa'] == 149].copy()

        if not df_recebimentos_total_mes.empty:
            # Adiciona coluna de porcentagem da comissão de gerente
            df_recebimentos_total_mes['% Comissão'] = 0.5
            
            # Calcula a comissão para cada recebimento
            df_recebimentos_total_mes['Comissão'] = (df_recebimentos_total_mes['Valor da Parcela'] * 0.005)
            df_recebimentos_total_mes.drop(columns=['ID - Responsavel', 'Cargo', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'Ano Recebimento', 'Mês Recebimento'], inplace=True)
            df_recebimentos_total_mes['Dedução Imposto'] = 0.0
            df_recebimentos_total_mes['Valor Líquido'] = df_recebimentos_total_mes['Valor da Parcela'] - df_recebimentos_total_mes['Dedução Imposto']

            # Ordem das colunas
            df_recebimentos_total_mes = df_recebimentos_total_mes[['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'Data Vencimento', 'Data Recebimento', 'ID Parcela', 'Categoria Parcela', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', 'Comissão', '% Comissão']]

    return df_recebimentos_total_mes


def calcular_comissao_gerente_blue_note(df_recebimentos_total_mes, vendedor, id_casa):
    if id_casa in [110, -1]:
        df_recebimentos_total_mes = df_recebimentos_total_mes[df_recebimentos_total_mes['ID Casa'] == 110].copy()

        if not df_recebimentos_total_mes.empty:
            # Calcula imposto em relação à parcela
            df_recebimentos_total_mes['Dedução Imposto'] = (df_recebimentos_total_mes['Valor da Parcela'] / df_recebimentos_total_mes['Valor Total Evento']) * df_recebimentos_total_mes['Valor Total Imposto']
            df_recebimentos_total_mes['Valor Líquido'] = df_recebimentos_total_mes['Valor da Parcela'] - df_recebimentos_total_mes['Dedução Imposto']

            total_recebido = df_recebimentos_total_mes['Valor da Parcela'].sum() - df_recebimentos_total_mes['Dedução Imposto'].sum()
            # Adiciona coluna de porcentagem da comissão de gerente
            if total_recebido <= 100000:
                df_recebimentos_total_mes['% Comissão'] = 1.5
            elif total_recebido <= 250000:
                df_recebimentos_total_mes['% Comissão'] = 1.75
            elif total_recebido <= 500000:
                df_recebimentos_total_mes['% Comissão'] = 2.0
            else:
                df_recebimentos_total_mes['% Comissão'] = 3.0

            # Calcula a comissão para cada recebimento
            df_recebimentos_total_mes['Comissão'] = ((df_recebimentos_total_mes['Valor da Parcela'] - df_recebimentos_total_mes['Dedução Imposto']) * df_recebimentos_total_mes['% Comissão'] / 100)

            df_recebimentos_total_mes.drop(columns=['ID - Responsavel', 'Cargo', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'Ano Recebimento', 'Mês Recebimento'], inplace=True)

            # Ordem das colunas
            df_recebimentos_total_mes = df_recebimentos_total_mes[['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'Data Vencimento', 'Data Recebimento', 'ID Parcela', 'Categoria Parcela', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', 'Comissão', '% Comissão']]

    return df_recebimentos_total_mes

def highlight_total_row(row):
    if row['Casa'] == 'Total':
        return ['background-color: #f0f2f6; color: black;'] * len(row)
    else:
        return [''] * len(row)