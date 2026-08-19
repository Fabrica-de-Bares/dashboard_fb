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

    if row['ID Casa'] in [149, 122, 156, 115, 104, 114, 148, 105, 116, 160, 128, 145, 173]: # Arcos, Girondino, Riviera, Orfeu, Bar Brahma - Centro, Bar Brahma - Granja, Jacaré, Bar Leo Centro, Bar Brahma - Paulista
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

def calcular_comissao_gerente_priceless(df_recebimentos_total_mes, id_responsavel, id_casa, meta_atingida):
    if id_casa in [149, -1]:
        df_recebimentos_total_mes = df_recebimentos_total_mes[df_recebimentos_total_mes['ID Casa'] == 149].copy()

        if not df_recebimentos_total_mes.empty:
            # Adiciona coluna de porcentagem da comissão de gerente
            if meta_atingida:
                df_recebimentos_total_mes['% Comissão'] = 1.0
            else:
                df_recebimentos_total_mes['% Comissão'] = 0.5
            
            # Calcula a comissão para cada recebimento
            df_recebimentos_total_mes['Comissão'] = (df_recebimentos_total_mes['Valor da Parcela'] * df_recebimentos_total_mes['% Comissão'] / 100)
            df_recebimentos_total_mes.drop(columns=['ID - Responsavel', 'Cargo', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'Ano Recebimento', 'Mês Recebimento'], inplace=True)
            df_recebimentos_total_mes['Dedução Imposto'] = 0.0
            df_recebimentos_total_mes['Valor Líquido'] = df_recebimentos_total_mes['Valor da Parcela'] - df_recebimentos_total_mes['Dedução Imposto']

            # Ordem das colunas
            df_recebimentos_total_mes = df_recebimentos_total_mes[['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'Data Vencimento', 'Data Recebimento', 'ID Parcela', 'Categoria Parcela', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', 'Comissão', '% Comissão']]

    return df_recebimentos_total_mes


IDS_REGRA_COMISSAO_BLUE_NOTE = [110, 178, 180]  # casas que seguem a mesma regra de comissão por faixa de total recebido
COLUNAS_COMISSAO_BLUE_NOTE = ['ID Casa', 'Casa', 'ID Evento', 'Nome Evento', 'Data Vencimento', 'Data Recebimento', 'ID Parcela', 'Categoria Parcela', 'Valor da Parcela', 'Dedução Imposto', 'Valor Líquido', 'Comissão', '% Comissão']


def _tabela_comissao_blue_note(df_recebimentos_total_mes, id_casa_regra):
    """
    Calcula, para todas as executivas de uma casa Blue Note, o imposto deduzido, o valor
    líquido e a comissão por faixa de total recebido da casa no mês. Não filtra por vendedor.
    """
    df_recebimentos_total_mes = df_recebimentos_total_mes[df_recebimentos_total_mes['ID Casa'] == id_casa_regra].copy()

    if not df_recebimentos_total_mes.empty:
        # Calcula imposto em relação à parcela (sem imposto lançado = considera dedução 0)
        df_recebimentos_total_mes['Dedução Imposto'] = ((df_recebimentos_total_mes['Valor da Parcela'] / df_recebimentos_total_mes['Valor Total Evento']) * df_recebimentos_total_mes['Valor Total Imposto']).fillna(0)
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

    return df_recebimentos_total_mes


def calcular_comissao_blue_note(df_recebimentos_total_mes, vendedor, id_casa, id_casa_regra):
    df_comissao_vendedor = pd.DataFrame(columns=COLUNAS_COMISSAO_BLUE_NOTE)

    if id_casa in [id_casa_regra, -1]:
        tabela = _tabela_comissao_blue_note(df_recebimentos_total_mes, id_casa_regra)

        if not tabela.empty:
            # Filtra apenas eventos do vendedor
            tabela = tabela[tabela['ID - Responsavel'] == vendedor]

            # Remove colunas desnecessárias
            tabela = tabela.drop(columns=['ID - Responsavel', 'Cargo', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'Ano Recebimento', 'Mês Recebimento'])

            # Ordem das colunas
            df_comissao_vendedor = tabela[COLUNAS_COMISSAO_BLUE_NOTE]

    return df_comissao_vendedor


def calcular_comissao_gerente_blue_note(df_recebimentos_total_mes, vendedor, id_casa, id_casa_regra, ano, mes):
    """
    A partir de agosto/2026, a Gerente de Eventos do Blue Note recebe, além da própria
    comissão por escalonamento, um bônus de 10% sobre a comissão (não sobre a venda) das
    demais executivas da casa no mês.
    """
    regra_vigente = (int(ano) > 2026) or (int(ano) == 2026 and int(mes) >= 8)
    df_bonus_gerente = pd.DataFrame(columns=COLUNAS_COMISSAO_BLUE_NOTE)

    if id_casa in [id_casa_regra, -1] and regra_vigente:
        df_recebimentos_total_mes = _tabela_comissao_blue_note(df_recebimentos_total_mes, id_casa_regra)

        if not df_recebimentos_total_mes.empty:
            # Mantém apenas as demais executivas (exclui a própria gerente e outras gerentes)
            df_recebimentos_total_mes = df_recebimentos_total_mes[
                (df_recebimentos_total_mes['ID - Responsavel'] != vendedor) &
                (df_recebimentos_total_mes['Cargo'] != 'Gerente de Eventos')
            ].copy()

            # Descarta parcelas sem comissão (nada para bonificar)
            df_recebimentos_total_mes = df_recebimentos_total_mes[df_recebimentos_total_mes['Comissão'] != 0]

            if not df_recebimentos_total_mes.empty:
                # Bônus da gerente: 10% sobre a comissão da executiva, não sobre a venda
                df_recebimentos_total_mes['Comissão'] = df_recebimentos_total_mes['Comissão'] * 10 / 100
                df_recebimentos_total_mes['% Comissão'] = 10.0

                # Zera os valores de venda/imposto/líquido para não contar a venda da
                # executiva novamente no total vendido/líquido da casa
                df_recebimentos_total_mes['Valor da Parcela'] = 0.0
                df_recebimentos_total_mes['Dedução Imposto'] = 0.0
                df_recebimentos_total_mes['Valor Líquido'] = 0.0

                # Identifica visualmente as linhas de bônus de gerência
                df_recebimentos_total_mes['Nome Evento'] = '[Comissão Gerência] ' + df_recebimentos_total_mes['Nome Evento'].astype(str)

                # Remove colunas desnecessárias
                df_recebimentos_total_mes.drop(columns=['ID - Responsavel', 'Cargo', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida', 'Ano Recebimento', 'Mês Recebimento'], inplace=True)

                # Ordem das colunas
                df_bonus_gerente = df_recebimentos_total_mes[COLUNAS_COMISSAO_BLUE_NOTE]

    return df_bonus_gerente

def highlight_total_row(row):
    if row['Casa'] == 'Total':
        return ['background-color: #f0f2f6; color: black;'] * len(row)
    else:
        return [''] * len(row)