import pandas as pd
import streamlit as st
from utils.functions.general_functions_conciliacao import calcular_datas, traduz_semana_mes


# Filtrando Datas
datas = calcular_datas()

# Destaca colunas do mês atual e seguintes (faturamento projetado)
def destaca_mes_atual_seguintes(row):
    mes_atual = datas['inicio_mes_atual'].strftime('%m-%Y')
    if row['Mês-Ano'] >= mes_atual:
        return ['background-color: rgba(255,255,224)'] * (len(row))
    return [''] * (len(row))


def prepara_dados_faturamento_casa(df_faturamento_diario, casas_selecionadas):
    # Filtra por casa e ano
    df_faturamento_diario_casa = df_faturamento_diario.copy()
    df_faturamento_diario_casa['Data Evento'] = pd.to_datetime(df_faturamento_diario_casa['Data Evento'], errors='coerce')
    df_faturamento_diario_casa = df_faturamento_diario_casa[
        (df_faturamento_diario_casa['Casa'].isin(casas_selecionadas))
    ].copy()

    # Cria dia da semana em português
    df_faturamento_diario_casa['Dia Semana'] = df_faturamento_diario_casa['Data Evento'].dt.strftime('%A')
    df_faturamento_diario_casa['Dia Semana'] = df_faturamento_diario_casa['Dia Semana'].apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )

    # Cria mês em português
    df_faturamento_diario_casa['Nome Mes'] = df_faturamento_diario_casa['Data Evento'].dt.strftime('%B')
    df_faturamento_diario_casa['Nome Mes'] = df_faturamento_diario_casa['Nome Mes'].apply(
        lambda x: traduz_semana_mes(x, 'mes')
    )

    # Cria mês numérico
    df_faturamento_diario_casa['Mes_Ano'] = df_faturamento_diario_casa['Data Evento'].dt.strftime('%m-%Y')
    df_faturamento_diario_casa = df_faturamento_diario_casa[['Casa', 'Categoria', 'Data Evento', 'Valor Bruto', 'Dia Semana', 'Nome Mes', 'Mes_Ano']]

    # Arcos não abre de segunda-feira: zera segundas com faturamento de A&B para não impactar na projeção (vêm de Eventos)
    condicao = (df_faturamento_diario_casa['Casa'] == 'Arcos') & (df_faturamento_diario_casa['Dia Semana'] == 'Segunda-feira')
    df_faturamento_diario_casa.loc[condicao, 'Valor Bruto'] = 0

    # Agrupa o faturamento das casas selecionadas
    df_faturamento_diario_casa = df_faturamento_diario_casa.groupby(['Categoria', 'Data Evento', 'Dia Semana', 'Nome Mes', 'Mes_Ano'], as_index=False)[['Valor Bruto']].sum()

    return df_faturamento_diario_casa


def concatena_meses_reais_projetados(df_dias_futuros_mes, df_faturamento_diario_casa, id_casa, casa, ano):
    # Usa a projeção para o mês corrente (ainda não está finalizado) e para o próximo ano
    if ano == datas['ano_atual']:
        df_projecao_futuro = df_dias_futuros_mes[df_dias_futuros_mes['Data Evento'].dt.year == datas['ano_atual']]
    else:
        df_projecao_futuro = df_dias_futuros_mes
    df_projecao_futuro = df_projecao_futuro[['Categoria', 'Data Evento', 'Valor Final', 'Dia Semana', 'Nome Mes', 'Mes_Ano']]

    df_merge = pd.merge(
        df_projecao_futuro,
        df_faturamento_diario_casa,
        on=['Categoria', 'Data Evento', 'Dia Semana', 'Mes_Ano'],
        how='left'
    )
    # df_merge['Valor Final'] = df_merge['Faturamento Projetado'].fillna(id_casa)

    # Cria mês em português
    df_merge['Nome Mes'] = df_merge['Data Evento'].dt.strftime('%B')
    df_merge['Nome Mes'] = df_merge['Nome Mes'].apply(
        lambda x: traduz_semana_mes(x, 'mes')
    )
    # Cria mês numérico
    df_merge['Mes_Ano'] = df_merge['Data Evento'].dt.strftime('%m-%Y')

    return df_merge


# Calcula faturamento geral (junta todas as categorias da Zig) por dia da semana para cada mês
def calcula_faturamento_medio(df_faturamento_todos_meses, ano, detalhamento_categoria=False, categoria_selecionada=None):
    # garante que é número
    df_faturamento_todos_meses['Valor Final'] = pd.to_numeric(df_faturamento_todos_meses['Valor Final'], errors='coerce')
   
    # Filtra pelo ano selecionado o df que tem todos os meses do ano atual e seguinte
    df_faturamento_todos_meses = df_faturamento_todos_meses[df_faturamento_todos_meses['Data Evento'].dt.year == ano]
   
    # Calcula a média de faturamento de cada categoria por dia da semana
    df_faturamento_categoria_dia_semana = df_faturamento_todos_meses.groupby(['Categoria', 'Dia Semana', 'Mes_Ano'], dropna=False, as_index=False)[['Valor Final']].mean()

    if detalhamento_categoria == False:
        # Soma de todas as categorias por dia da semana
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana.groupby(['Dia Semana', 'Mes_Ano'], as_index=False)[['Valor Final']].sum()
    else:
        df_faturamento_categoria_dia_semana_filtrado = df_faturamento_categoria_dia_semana[df_faturamento_categoria_dia_semana['Categoria'] == categoria_selecionada]
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana_filtrado[['Dia Semana', 'Mes_Ano', 'Valor Final']]

    pivot_faturamento_geral = df_faturamento_dia_semana.pivot(
        index='Mes_Ano',
        columns='Dia Semana',
        values='Valor Final'
    ).fillna(0)
    
    pivot_faturamento_geral = pivot_faturamento_geral[['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']]
    pivot_faturamento_geral = pivot_faturamento_geral.reset_index()  # transforma Mes_Ano em coluna
    return pivot_faturamento_geral
