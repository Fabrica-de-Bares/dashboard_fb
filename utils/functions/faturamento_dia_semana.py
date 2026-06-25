import pandas as pd
import streamlit as st
from utils.functions.general_functions_conciliacao import calcular_datas, traduz_semana_mes


# Filtrando Datas
datas = calcular_datas()


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
    df_faturamento_diario_casa['Mes_Ano'] = df_faturamento_diario_casa['Data Evento'].dt.strftime('%m/%Y')
    df_faturamento_diario_casa = df_faturamento_diario_casa[['Casa', 'Categoria', 'Data Evento', 'Valor Bruto', 'Dia Semana', 'Nome Mes', 'Mes_Ano']]

    # Arcos não abre de segunda-feira: zera segundas com faturamento de A&B para não impactar na projeção (vêm de Eventos)
    condicao = (df_faturamento_diario_casa['Casa'] == 'Arcos') & (df_faturamento_diario_casa['Dia Semana'] == 'Segunda-feira')
    df_faturamento_diario_casa.loc[condicao, 'Valor Bruto'] = 0

    # Agrupa o faturamento das casas selecionadas
    df_faturamento_diario_casa = df_faturamento_diario_casa.groupby(['Categoria', 'Data Evento', 'Dia Semana', 'Nome Mes', 'Mes_Ano'], as_index=False)[['Valor Bruto']].sum()

    return df_faturamento_diario_casa


def concatena_meses_reais_projetados(df_dias_futuros_mes, df_faturamento_diario_casa):
    # Usa a projeção para o mês corrente (ainda não está finalizado) e para o próximo ano
    # if ano == datas['ano_atual']:
    #     df_projecao_futuro = df_dias_futuros_mes[df_dias_futuros_mes['Data Evento'].dt.year == datas['ano_atual']].copy()
    # else:
    df_projecao_futuro = df_dias_futuros_mes # Quero utilizar o ano anterior e o atual 
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
    df_merge['Mes_Ano'] = df_merge['Data Evento'].dt.strftime('%m/%Y')

    return df_merge


# Calcula faturamento geral (junta todas as categorias da Zig) por dia da semana para cada mês
def calcula_faturamento_medio(df_faturamento_todos_meses, qtd_casas_selecionadas, detalhamento_categoria=False, categoria_selecionada=None):
    # garante que é número
    df_faturamento_todos_meses['Valor Final'] = pd.to_numeric(df_faturamento_todos_meses['Valor Final'], errors='coerce')
   
    # Filtra pelo ano selecionado o df que tem todos os meses do ano atual e seguinte
    # df_faturamento_todos_meses = df_faturamento_todos_meses[df_faturamento_todos_meses['Data Evento'].dt.year == ano].copy()
    df_faturamento_todos_meses = df_faturamento_todos_meses[ # Ano anterior e atual para comparação
        (df_faturamento_todos_meses['Data Evento'].dt.year == datas['ano_atual']) | 
        (df_faturamento_todos_meses['Data Evento'].dt.year == datas['ano_atual'] - 1)
    ].copy()

    # Calcula a média de faturamento de cada categoria por dia da semana
    df_faturamento_categoria_dia_semana = df_faturamento_todos_meses.groupby(['Categoria', 'Dia Semana', 'Mes_Ano'], dropna=False, as_index=False)[['Valor Final']].mean()

    if detalhamento_categoria == False:
        # Soma de todas as categorias por dia da semana
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana.groupby(['Dia Semana', 'Mes_Ano'], as_index=False)[['Valor Final']].sum()
    else:
        df_faturamento_categoria_dia_semana_filtrado = df_faturamento_categoria_dia_semana[df_faturamento_categoria_dia_semana['Categoria'] == categoria_selecionada].copy()
        df_faturamento_dia_semana = df_faturamento_categoria_dia_semana_filtrado[['Dia Semana', 'Mes_Ano', 'Valor Final']]
    
    # Média - divide pela quantidade de casas selecionadas (não apenas soma)
    df_faturamento_dia_semana['Valor Final'] = df_faturamento_dia_semana['Valor Final'] / qtd_casas_selecionadas

    pivot_faturamento_geral = df_faturamento_dia_semana.pivot(
        index='Mes_Ano',
        columns='Dia Semana',
        values='Valor Final'
    ).fillna(0)
    
    pivot_faturamento_geral = pivot_faturamento_geral[['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']]
    pivot_faturamento_geral = pivot_faturamento_geral.reset_index()  # transforma Mes_Ano em coluna
    return pivot_faturamento_geral


def calcula_variacao_ano_anterior(pivot_faturamento):
    linhas = []
    dias_semana = [col for col in pivot_faturamento.columns if col not in ['Mês', 'Ano']]
    for mes in sorted(pivot_faturamento['Mês'].unique()):
        df_mes = pivot_faturamento[pivot_faturamento['Mês'] == mes].copy()
        linha_ano_anterior = df_mes[df_mes['Ano'] == datas['ano_atual'] - 1]
        linha_ano_atual = df_mes[df_mes['Ano'] == datas['ano_atual']]

        if len(linha_ano_anterior) and len(linha_ano_atual):
            variacao_valor = linha_ano_atual.iloc[0][dias_semana] - linha_ano_anterior.iloc[0][dias_semana]
            variacao_pct = linha_ano_atual.iloc[0][dias_semana] / linha_ano_anterior.iloc[0][dias_semana] - 1

            linha_var = variacao_valor.to_frame().T
            for col in dias_semana:
                linha_var[f'{col}_pct'] = variacao_pct[col]
            linha_var['Mês'] = mes
            linha_var['Ano'] = 'Variação'
            linhas.append(linha_ano_anterior)
            linhas.append(linha_ano_atual)
            linhas.append(linha_var)

    pivot_faturamento = pd.concat(linhas, ignore_index=True)
    return pivot_faturamento


def aplica_estilos(row, df):
    mes_atual = datas['mes_atual']
    ano_atual = datas['ano_atual']
    estilos = [''] * len(row)

    row_original = df.loc[row.name] # Linha completa do dataframe original (com as colunas _pct)

    if row['Ano'] == 'Variação':
        for i, col in enumerate(row.index):
            if col in ['Mês', 'Ano']:
                estilos[i] = 'font-weight: 600'
            elif col in ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']:
                pct_col = f'{col}_pct'
                if pd.notna(row_original[pct_col]):
                    if row_original[pct_col] > 0: estilos[i] = 'font-weight:600; color:#198754;' # Verde
                    elif row_original[pct_col] < 0: estilos[i] = 'font-weight:600; color:#dc3545;' # Vermelho
                    else: estilos[i] = 'font-weight:600'
        return estilos

    if row['Mês'] >= mes_atual and row['Ano'] == ano_atual:
        return ['background-color: rgba(255,255,224)'] * len(row) # Amarelo para meses futuros

    return estilos


def formato_br(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
