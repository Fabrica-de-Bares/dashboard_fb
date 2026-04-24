import pandas as pd
import streamlit as st


def prepara_colunas_real_dre(df, casa, ano, mes_selecionado):
    df_transformado = df.copy()

    # Removendo colunas e linhas desnecessárias - seleciona pelo índice da coluna em vez do nome
    if ano >= 2026:
        mapa = {}
        for i in range(12):
            col_num = 9 + (i * 3)  # 9, 12, 15, etc
            mes = i + 1
            mapa[f'Unnamed: {col_num}'] = f'{ano}-{mes:02d}-01 00:00:00'

        mapa['Unnamed: 48'] = 'ANO' # adiciona o ANO
        df_transformado.rename(columns=mapa, inplace=True)

        # Seleção dinâmica das colunas correspondentes ao mês selecionado
        if mes_selecionado not in ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre']: 
            coluna_mes = 9 + (mes_selecionado - 1) * 3
            df_transformado = df_transformado.iloc[:, [0, coluna_mes]]
            colunas_meses = df_transformado.columns[[1]]
        else:
            if mes_selecionado == '1º Trimestre':
                df_transformado = df_transformado.iloc[:, [0, 9, 12, 15]]
            elif mes_selecionado == '2º Trimestre':
                df_transformado = df_transformado.iloc[:, [0, 18, 21, 24]]
            elif mes_selecionado == '3º Trimestre':
                df_transformado = df_transformado.iloc[:, [0, 27, 30, 33]]
            elif mes_selecionado == '4º Trimestre':
                df_transformado = df_transformado.iloc[:, [0, 36, 39, 42]]
            colunas_meses = df_transformado.columns[[1, 2, 3]]

    else: # ANOS JÁ INSERIDOS
        if ano == 2023: # Planilha personalizada 
            df_transformado = df_transformado.iloc[:, [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 24]]
            df_transformado.rename(columns={'Unnamed: 24': 'ANO'}, inplace=True)

        elif ano == 2024 and casa != 'Girondino': # 2024 vem do arquivo de Jan/2025
            df_transformado = df_transformado.iloc[:, [0, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 46]]
        
        elif ano == 2025 or (ano == 2024 and casa == 'Girondino'): # 2025 vem do arquivo de Dez/2025
            df_transformado = df_transformado.iloc[:, [0, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 48]]
            
            mapa = {}
            for i in range(12):
                col_num = 9 + (i * 3)  # 9, 12, 15, etc
                mes = i + 1
                mapa[f'Unnamed: {col_num}'] = f'{ano}-{mes:02d}-01 00:00:00'

            mapa['Unnamed: 48'] = 'ANO' # adiciona o ANO
            df_transformado.rename(columns=mapa, inplace=True)
        
        colunas_meses = df_transformado.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]] # Define quais são as colunas de meses e acumulado do ano
       
    return df_transformado, colunas_meses


def prepara_partes_headcount(df, tipo_dado, ano):
    if tipo_dado == 'Nº COLABORADORES':
        df = df.dropna(subset=['Unnamed: 0'])
        df = df.rename(columns={'Unnamed: 0': 'Cargo'})
    else:
        df = df.dropna(subset=['Unnamed: 13'])
        df = df.rename(columns={'Unnamed: 13': 'Cargo'})

    df = df[~df['Cargo'].isin([tipo_dado, 'PJ', '  - Squad', 'Operação', 'Quadro/Função'])].copy() # Linhas desnecessárias
    df = df.fillna(0)

    for col in df.columns:
        if col != 'Cargo':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    colunas_meses = [col for col in df if col != 'Cargo']

    # Transforma colunas dos meses em linhas na coluna 'Mês'
    df_layout_final = df.melt(
        id_vars=['Cargo'],
        value_vars=colunas_meses,
        var_name='Mês',
        value_name='Valor'
    )

    df_layout_final['Mês'] = df_layout_final['Mês'].astype(str).str.replace('Unnamed: ', '', regex=False)
    df_layout_final['Mês'] = pd.to_numeric(df_layout_final['Mês'], errors='coerce')
    if tipo_dado == 'REMUNERAÇÃO':
        df_layout_final['Mês'] = df_layout_final['Mês'] - 13

    df_layout_final['Ano'] = ano
    df_layout_final['Tipo de Dado'] = tipo_dado

    return df_layout_final