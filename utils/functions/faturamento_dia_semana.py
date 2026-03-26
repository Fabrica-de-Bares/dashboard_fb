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
    df_projecao_futuro = df_projecao_futuro.rename(columns={'Valor Final':'Valor Bruto'})
    
    df_concat = pd.concat([df_faturamento_diario_casa, df_projecao_futuro])
    # df_concat['ID_Casa'] = df_concat['ID_Casa'].fillna(id_casa)
    # df_concat['Casa'] = df_concat['Casa'].fillna(casa)

    # Cria mês em português
    df_concat['Nome Mes'] = df_concat['Data Evento'].dt.strftime('%B')
    df_concat['Nome Mes'] = df_concat['Nome Mes'].apply(
        lambda x: traduz_semana_mes(x, 'mes')
    )
    # Cria mês numérico
    df_concat['Mes_Ano'] = df_concat['Data Evento'].dt.strftime('%m-%Y')

    return df_concat


# Calcula faturamento geral (junta todas as categorias da Zig) por dia da semana para cada mês
def calcula_faturamento_medio(df_faturamento_todos_meses, ano, detalhamento_categoria=False, categoria_selecionada=None):
    # garante que é número
    df_faturamento_todos_meses['Valor Bruto'] = pd.to_numeric(
        df_faturamento_todos_meses['Valor Bruto'], 
        errors='coerce'
    )
   
    # Filtra pelo ano selecionado o df que tem todos os meses do ano atual e seguinte
    df_faturamento_todos_meses = df_faturamento_todos_meses[df_faturamento_todos_meses['Data Evento'].dt.year == ano]
    # st.write(df_faturamento_todos_meses[df_faturamento_todos_meses['Categoria']=='Alimentos']
    #   .groupby(['Dia Semana', 'Mes_Ano'])['Valor Bruto']
    #   .agg(['count','size','mean','sum']))

    # Calcula a média de faturamento de cada categoria por dia da semana
    df_faturamento_categoria_dia_semana = df_faturamento_todos_meses.groupby(['Categoria', 'Dia Semana', 'Mes_Ano'], dropna=False, as_index=False)[['Valor Bruto']].mean()

    if detalhamento_categoria == False:
        # Soma de todas as categorias por dia da semana
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana.groupby(['Dia Semana', 'Mes_Ano'], as_index=False)[['Valor Bruto']].sum()
    else:
        df_faturamento_categoria_dia_semana_filtrado = df_faturamento_categoria_dia_semana[df_faturamento_categoria_dia_semana['Categoria'] == categoria_selecionada]
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana_filtrado[['Dia Semana', 'Mes_Ano', 'Valor Bruto']]
    
    # ordem_meses = [
    #     'Janeiro', 'Fevereiro', 'Março',
    #     'Abril', 'Maio', 'Junho',
    #     'Julho', 'Agosto', 'Setembro',
    #     'Outubro', 'Novembro', 'Dezembro'
    # ]

    # df_faturamento_geral_dia_semana['Nome Mes'] = pd.Categorical(
    #     df_faturamento_geral_dia_semana['Nome Mes'],
    #     categories=ordem_meses,
    #     ordered=True
    # )

    pivot_faturamento_geral = df_faturamento_dia_semana.pivot(
        index='Mes_Ano',
        columns='Dia Semana',
        values='Valor Bruto'
    ).fillna(0)
    
    pivot_faturamento_geral = pivot_faturamento_geral[['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']]
    pivot_faturamento_geral = pivot_faturamento_geral.reset_index()  # transforma Mes_Ano em coluna
    return pivot_faturamento_geral
