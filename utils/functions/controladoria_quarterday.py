import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts
import numpy as np


def prepara_dados_faturamento_orcamento(df_historico_real_dre, df_orcamento_operacional, casa, datas, class_cont):
    # --- Normaliza nome da casa ---
    if casa == 'Girondino - Agregado':
        df_historico_real_dre['Casa'] = df_historico_real_dre['Casa'].replace('Girondino - CCBB', 'Girondino')
        df_orcamento_operacional['Casa'] = df_orcamento_operacional['Casa'].replace('Girondino - CCBB', 'Girondino')
        nome_casa = 'Girondino'
    else:
        nome_casa = casa

    # --- Filtra e prepara histórico real ---
    df_historico_real_dre['Mês'] = pd.to_datetime(df_historico_real_dre['Mês'], errors='coerce')
    df_historico_real_dre = df_historico_real_dre[
        (df_historico_real_dre['Casa'] == nome_casa) &
        (df_historico_real_dre['Mês'].dt.day != 31)
    ].copy()

    if casa in ('Girondino', 'Girondino - CCBB'):
        df_historico_real_dre.loc[df_historico_real_dre['Mês'].dt.year == 2024, 'Valor'] = 0

    # --- Monta df_categoria real ---
    if class_cont == 'CMV':
        df_fat = df_historico_real_dre[df_historico_real_dre['Categoria'].isin(['Alimentação', 'Bebida', 'Eventos A&B', 'Delivery', 'Membership'])].copy()
        df_fat = df_fat.groupby('Mês', as_index=False)['Valor'].sum()
        df_cmv = df_historico_real_dre[df_historico_real_dre['Categoria'] == '(-) Custo Mercadoria Vendida'].copy()
        df_categoria = pd.merge(df_fat[['Mês', 'Valor']], df_cmv[['Mês', 'Valor']], on='Mês', how='left')
        df_categoria['Valor_y'] *= -1
        df_categoria['Valor'] = df_categoria['Valor_y'] / df_categoria['Valor_x'].replace(0, np.nan)
        df_cmv_acumulado = df_categoria.copy()
    else:
        df_categoria = df_historico_real_dre[df_historico_real_dre['Categoria'].isin(class_cont)].copy()

    # --- Pivot do histórico real ---
    df_categoria['Ano'] = df_categoria['Mês'].dt.year
    df_categoria['MesNum'] = df_categoria['Mês'].dt.month
    df_categoria = df_categoria.groupby(['Ano', 'MesNum'], as_index=False)['Valor'].sum()
    df_categoria = df_categoria.pivot_table(index='Ano', columns='MesNum', values='Valor').reset_index().fillna(0)
    df_categoria[df_categoria.columns[0]] = pd.to_numeric(df_categoria.iloc[:, 0], errors='coerce').astype('Int64')

    # --- Colunas auxiliares ---
    cols_meses = [col for col in df_categoria.columns if isinstance(col, (int, float))]
    cols_acumulado = [col for col in cols_meses if col <= datas['mes_atual'] - 1]
    cols_1_tri = [col for col in cols_meses if 1 <= col <= 3]
    cols_2_tri = [col for col in cols_meses if 4 <= col <= 6]
    cols_3_tri = [col for col in cols_meses if 7 <= col <= 9]
    cols_4_tri = [col for col in cols_meses if 10 <= col <= 12]
    cols_resumo = ['Acumulado', 'ANO', '1 TRI', '2 TRI', '3 TRI', '4 TRI']

    def adiciona_resumo(df):
        df['Acumulado'] = df[cols_acumulado].sum(axis=1)
        df['ANO']       = df[cols_meses].sum(axis=1)
        df['1 TRI']     = df[cols_1_tri].sum(axis=1)
        df['2 TRI']     = df[cols_2_tri].sum(axis=1)
        df['3 TRI']     = df[cols_3_tri].sum(axis=1)
        df['4 TRI']     = df[cols_4_tri].sum(axis=1)
        return df

    # --- Filtra orçamento ---
    df_orcamento_ano_atual = df_orcamento_operacional[
        (df_orcamento_operacional['Casa'] == nome_casa) &
        (df_orcamento_operacional['Ano'] == datas['ano_atual'])
    ].copy()

    # --- Monta df_orcamento_categoria ---
    if class_cont == ['FATURAMENTO BRUTO']:
        df_orcamento_categoria = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 1'] == 'Faturamento Bruto'].copy()

    elif class_cont == 'CMV':
        df_orc_fat = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 2'].isin(['Alimentação', 'Bebida', 'Eventos A&B', 'Delivery', 'Membership'])].copy()
        df_orc_fat = df_orc_fat.groupby(['Ano', 'Mês'], as_index=False)['Orçamento'].sum()
        df_orc_cmv = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 1'] == 'Custo Mercadoria Vendida'].copy()
        df_orc_cmv = df_orc_cmv.groupby(['Ano', 'Mês'], as_index=False)['Orçamento'].sum()

        df_orcamento_categoria = pd.merge(df_orc_fat, df_orc_cmv, on=['Ano', 'Mês'], how='left')
        df_orcamento_categoria['Orçamento'] = df_orcamento_categoria['Orçamento_y'] / df_orcamento_categoria['Orçamento_x']

        def pivot_orc(col):
            return (
                df_orcamento_categoria.pivot_table(index='Ano', columns='Mês', values=col, aggfunc='sum')
                .reindex(columns=range(1, 13))
                .reset_index()
            )

        df_orc_fat_pivot  = adiciona_resumo(pivot_orc('Orçamento_x'))
        df_orc_custo_pivot = adiciona_resumo(pivot_orc('Orçamento_y'))

        df_resultado = df_orc_custo_pivot.copy()
        df_resultado[cols_resumo] = (
            df_orc_custo_pivot[cols_resumo].values /
            df_orc_fat_pivot[cols_resumo].replace(0, np.nan).values
        )

    elif class_cont == ['EBITDA']:
        cats_ebitda = [
            'Faturamento Bruto', 'Desconto sobre Venda', 'Impostos sobre Venda', 'Custo Mercadoria Vendida',
            'Custos Artístico Geral', 'Custos de Eventos', 'Gorjeta', 'Deduções sobre Venda',
            'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra',
            'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Custo de Ocupação',
            'Utilidades', 'Informática e TI', 'Manutenção', 'Marketing', 'Serviços de Terceiros',
            'Locação de Equipamentos', 'Sistema de Franquias'
        ]
        df_orcamento_categoria = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 1'].isin(cats_ebitda)].copy()
        df_orcamento_categoria.loc[df_orcamento_categoria['Classificação Contábil 1'] != 'Faturamento Bruto', 'Orçamento'] *= -1
        # df_acumulado_categoria = df_orcamento_categoria[df_orcamento_categoria['Mês'] <= datas['mes_atual'] - 1].groupby(['Ano', 'Classificação Contábil 1'], as_index=False)['Orçamento'].sum()
        
    else:
        df_orcamento_categoria = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 2'].isin(class_cont)].copy()

    # --- Pivot do orçamento e concatena ---
    df_orcamento_categoria = (
        df_orcamento_categoria
        .groupby(['Mês', 'Ano'], as_index=False)['Orçamento'].sum()
        .pivot_table(index='Ano', columns='Mês', values='Orçamento')
        .reset_index()
        .fillna(0)
    )
    df_orcamento_categoria.loc[0, 'Ano'] = f"Orçamento {datas['ano_atual']}"

    if class_cont == 'CMV':
        df_orcamento_categoria.loc[
            df_orcamento_categoria['Ano'].str.startswith('Orçamento'), cols_resumo
        ] = df_resultado[cols_resumo].values

    df_categoria = pd.concat([df_categoria, df_orcamento_categoria])

    # --- Calcula colunas de resumo ---
    if class_cont == 'CMV':
        df_cmv_acumulado['Ano'] = df_cmv_acumulado['Mês'].dt.year
        df_cmv_acumulado['Mes'] = df_cmv_acumulado['Mês'].dt.month

        df_ac_custo = adiciona_resumo(
            df_cmv_acumulado.pivot_table(index='Ano', columns='Mes', values='Valor_y', aggfunc='sum')
            .reindex(columns=range(1, 13)).reset_index()
        )
        df_ac_fat = adiciona_resumo(
            df_cmv_acumulado.pivot_table(index='Ano', columns='Mes', values='Valor_x', aggfunc='sum')
            .reindex(columns=range(1, 13)).reset_index()
        )

        df_acumulado_porcentagem = pd.merge(
            df_ac_custo[['Ano'] + cols_resumo],
            df_ac_fat[['Ano'] + cols_resumo],
            on='Ano', how='left'
        )
        for col in cols_resumo:
            df_acumulado_porcentagem[col] = (
                df_acumulado_porcentagem[f'{col}_x'].astype(float)
                .div(df_acumulado_porcentagem[f'{col}_y'].astype(float).replace(0, np.nan))
            )

        cols_numericas = [c for c in df_categoria.columns if c != 'Ano']
        df_categoria[cols_numericas] = df_categoria[cols_numericas].apply(pd.to_numeric, errors='coerce')

        mask = ~df_categoria['Ano'].astype(str).str.startswith('Orçamento')
        df_categoria.loc[mask, cols_resumo] = df_acumulado_porcentagem[cols_resumo].astype(float).values
    else:
        df_categoria = adiciona_resumo(df_categoria)

    return df_categoria


def prepara_dados_ticket_clientes(df_ticket, casa, datas, coluna_valor):
    if casa == 'Girondino - Agregado':
        df_ticket['Casa'] = df_ticket['Casa'].replace('Girondino - CCBB', 'Girondino')
        df = df_ticket[df_ticket['Casa'] == 'Girondino'].copy()
    else:
        df = df_ticket[df_ticket['Casa'] == casa].copy()

    df['Ano'] = pd.to_datetime(df['MES']).dt.year
    df['Mes'] = pd.to_datetime(df['MES']).dt.month

    df = df.pivot_table(
        index='Ano',
        columns='Mes',
        values=coluna_valor,
        aggfunc='sum'
    ).reset_index()
    
    # garante meses 1-12
    for mes in range(1, 13):
        if mes not in df.columns:
            df[mes] = np.nan

    if coluna_valor == 'TICKET_MEDIO':
        df['Acumulado'] = df[list(range(1, datas['mes_atual']))].mean(axis=1)
        df['ANO']       = df[list(range(1, 13))].mean(axis=1)
        df['1 TRI']     = df[list(range(1, 4))].mean(axis=1)
        df['2 TRI']     = df[list(range(4, 7))].mean(axis=1)
        df['3 TRI']     = df[list(range(7, 10))].mean(axis=1)
        df['4 TRI']     = df[list(range(10, 13))].mean(axis=1)
    elif coluna_valor == 'NUM_CLIENTES':
        df['Acumulado'] = df[list(range(1, datas['mes_atual']))].sum(axis=1)
        df['ANO']       = df[list(range(1, 13))].sum(axis=1)
        df['1 TRI']     = df[list(range(1, 4))].sum(axis=1)
        df['2 TRI']     = df[list(range(4, 7))].sum(axis=1)
        df['3 TRI']     = df[list(range(7, 10))].sum(axis=1)
        df['4 TRI']     = df[list(range(10, 13))].sum(axis=1)
    
    return df 


def calcula_crescimento_ano(ano_base, df_faturamento_bruto):
    df_real = df_faturamento_bruto[~df_faturamento_bruto['Ano'].astype(str).str.contains('Orçamento')].copy() # Faturamento anos anteriores
    df_base = df_real[df_real['Ano'] == ano_base].copy() # Faturamento ano base
    
    cols_meses = [col for col in df_faturamento_bruto.columns if isinstance(col, (int, float))]
    cols_calc = cols_meses + ['Acumulado', 'ANO', '1 TRI', '2 TRI', '3 TRI', '4 TRI']
    base = df_base.iloc[0][cols_calc].replace(0, np.nan)
    df_crescimento_ano_base = df_real.copy()

    df_crescimento_ano_base[cols_calc] = (base / df_crescimento_ano_base[cols_calc].replace(0, np.nan) - 1)

    # remove o próprio ano base
    df_crescimento_ano_base = df_crescimento_ano_base[df_crescimento_ano_base['Ano'] < ano_base].copy()

    # Organiza colunas
    df_crescimento_ano_base = df_crescimento_ano_base.sort_values('Ano')
    df_crescimento_ano_base = df_crescimento_ano_base.rename(columns={'Ano': f'% Crescimento de {ano_base}'})
    return df_crescimento_ano_base


def formatar_moeda_br(valor):
    if pd.isna(valor) or valor == 0:
        return "-"
    return f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") # Sem casas decimais e sem 'R$'


def formatar_porcentagem(valor):
    if pd.isna(valor) or valor == 0 or valor == -1:
        return "-"
    else:
        return f"{valor * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_ticket_medio(valor):
    if pd.isna(valor) or valor == 0:
        return "-"
    return f"{valor:.2f}".replace(",", "X").replace(".", ",").replace("X", ".") # Sem casas decimais e sem 'R$'


def formata_colunas(df, kpi, categoria):
    df = df.rename(columns={
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    })
    df = df.fillna(0)
    colunas_valores = df.columns[1:]
    df = df.reset_index(drop=True)

    # Formata valores numéricos
    if categoria == 'CMV': # Todos são porcentagens
        df_styled = df.style.format(formatar_porcentagem, subset=colunas_valores)
        if kpi != 'Faturamento Total':
            df_styled = df_styled.applymap(highlight_taxas, subset=colunas_valores) # Aplica estilos
    else:
        if kpi == 'Faturamento Total' or kpi == 'Nº de Clientes':
            df_styled = df.style.format(formatar_moeda_br, subset=colunas_valores)
        elif kpi == 'Ticket Médio - A&B':
            df_styled = df.style.format(formatar_ticket_medio, subset=colunas_valores)
        else:
            df_styled = df.style.applymap(highlight_taxas, subset=colunas_valores) # Aplica estilos
            df_styled = df_styled.format(formatar_porcentagem, subset=colunas_valores)
    
    return df_styled


def grafico_linhas_faturamento(series, titulo, anos, key):
    options = { # Configurações do gráfico
        "title": {
            "text": titulo
        },
        "tooltip": {
            "trigger": 'axis'
        },
        "legend": {
            "data": anos
        },
        "grid": {
            "left": '3%',
            "right": '4%',
            "bottom": '3%',
            "containLabel": True
        },
        "toolbox": {
            "feature": {
            "saveAsImage": {}
            }
        },
        "xAxis": {
            "type": 'category',
            "boundaryGap": False,
            "data": ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        },
        "yAxis": {
            "type": 'value'
        },
        "series": series
    }

    # Renderizar no Streamlit
    return st_echarts(options=options, height="400px", key=key)


def highlight_taxas(val):
    try:
        if float(val) < 0:
            return 'color: red;'
        elif float(val) > 0:
            return 'color: green;'
        else:
            return ''
    except:
        return ''
    
