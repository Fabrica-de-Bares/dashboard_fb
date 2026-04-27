import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts
import numpy as np


def prepara_dados_faturamento_orcamento(df_historico_real_dre, df_orcamento_operacional, casa, datas, class_cont): 
    if casa == 'Girondino - Agregado':
        df_historico_real_dre['Casa'] = df_historico_real_dre['Casa'].replace('Girondino - CCBB', 'Girondino')
        nome_casa = 'Girondino'
    else:
        nome_casa = casa
    
    # Filtra histórico real pela categoria
    df_historico_real_dre['Mês'] = pd.to_datetime(df_historico_real_dre['Mês'], errors='coerce')
    df_historico_real_dre = df_historico_real_dre[(df_historico_real_dre['Casa'] == nome_casa) & (df_historico_real_dre['Mês'].dt.day != 31)].copy()
    # df_historico_real_dre['Mês'] = df_historico_real_dre['Mês'].fillna('2025-06-01 00:00:00')

    # Tratamento para caso específico
    if casa == 'Girondino' or casa == 'Girondino - CCBB':
        df_historico_real_dre.loc[df_historico_real_dre['Mês'].dt.year == 2024, 'Valor'] = 0

    if class_cont == 'CMV': # Calcula % do CMV
        df_faturamento_a_b = df_historico_real_dre[df_historico_real_dre['Categoria'].isin(['Alimentação', 'Bebida', 'Eventos A&B', 'Delivery'])].copy()
        df_faturamento_a_b = df_faturamento_a_b.groupby(['Mês'], as_index=False)['Valor'].sum()
        df_cmv = df_historico_real_dre[df_historico_real_dre['Categoria'].isin(['(-) Custo Mercadoria Vendida'])].copy()
        df_categoria = pd.merge(
            df_faturamento_a_b[['Mês', 'Valor']],
            df_cmv[['Mês', 'Valor']],
            on=['Mês'],
            how='left'
        )
        df_categoria['Valor_y'] = df_categoria['Valor_y'] * (-1)
        df_categoria['Valor'] = df_categoria['Valor_y'] / df_categoria['Valor_x'].replace(0, np.nan) # Calcula CMV de cada mês/ano
    else:
        df_categoria = df_historico_real_dre[df_historico_real_dre['Categoria'].isin(class_cont)].copy()
        
    # Cria colunas de mês e ano
    df_categoria['Ano'] = df_categoria['Mês'].dt.year
    df_categoria['MesNum'] = df_categoria['Mês'].dt.month
    
    # Agrupa por mês e ano (no caso de Eventos, por ex)
    df_categoria = df_categoria.groupby(['Ano', 'MesNum'], as_index=False)['Valor'].sum()
    
    # Transforma meses em colunas
    df_categoria = df_categoria.pivot_table(
        index="Ano", 
        columns="MesNum",
        values="Valor",
    ).reset_index().fillna(0)

    df_categoria[df_categoria.columns[0]] = pd.to_numeric( # Anos formatados como Int
        df_categoria.iloc[:, 0], errors='coerce'
    ).astype('Int64')    
    
    # Filtra orçamento
    if casa == 'Girondino - Agregado':
        df_orcamento_operacional['Casa'] = df_orcamento_operacional['Casa'].replace('Girondino - CCBB', 'Girondino')
        casa = 'Girondino'

    df_orcamento_ano_atual = df_orcamento_operacional[(df_orcamento_operacional['Casa'] == casa) & (df_orcamento_operacional['Ano'] == datas['ano_atual'])].copy()
    
    if class_cont == ['FATURAMENTO BRUTO']:
        df_orcamento_categoria = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 1'] == 'Faturamento Bruto'].copy()
    elif class_cont == 'CMV': # Calcula % do orçamento do CMV
        df_orcamento_a_b = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 2'].isin(['Alimentação', 'Bebida', 'Eventos A&B', 'Delivery'])].copy()
        df_orcamento_a_b = df_orcamento_a_b.groupby(['Ano', 'Mês'], as_index=False)['Orçamento'].sum()
        df_orcamento_cmv = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 1'] == 'Custo Mercadoria Vendida'].copy()
        df_orcamento_cmv = df_orcamento_cmv.groupby(['Ano', 'Mês'], as_index=False)['Orçamento'].sum()
        df_orcamento_categoria = pd.merge(
            df_orcamento_a_b,
            df_orcamento_cmv,
            on=['Ano', 'Mês'],
            how='left'
        )
        df_orcamento_categoria['Orçamento'] = df_orcamento_categoria['Orçamento_y'] / df_orcamento_categoria['Orçamento_x'] # Calcula orçamento CMV
    elif class_cont == ['EBITDA']:
        df_orcamento_categoria = df_orcamento_ano_atual[
            (df_orcamento_ano_atual['Classificação Contábil 1'].isin(
                ['Faturamento Bruto', 'Desconto sobre Venda', 'Impostos sobre Venda', 'Custo Mercadoria Vendida', 'Custos Artístico Geral',
                 'Custos de Eventos', 'Gorjeta', 'Deduções sobre Venda', 'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra',
                 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Custo de Ocupação', 'Utilidades', 'Informática e TI',
                 'Manutenção', 'Marketing', 'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias']))
                ].copy()
        df_orcamento_categoria.loc[df_orcamento_categoria['Classificação Contábil 1'] != 'Faturamento Bruto', 'Orçamento'] *= -1
    else:
        df_orcamento_categoria = df_orcamento_ano_atual[df_orcamento_ano_atual['Classificação Contábil 2'].isin(class_cont)].copy()
    
    df_orcamento_categoria = df_orcamento_categoria.groupby(['Mês', 'Ano'], as_index=False)['Orçamento'].sum()

    # Transforma meses em colunas
    df_orcamento_categoria = df_orcamento_categoria.pivot_table(
        index="Ano", 
        columns="Mês",
        values="Orçamento",
    ).reset_index().fillna(0)
    df_orcamento_categoria.loc[0, 'Ano'] = f"Orçamento {datas['ano_atual']}"

    # Concatena
    df_categoria = pd.concat([df_categoria, df_orcamento_categoria])

    # Cria colunas de acumulado e trimestres
    cols_meses = [col for col in df_categoria.columns if isinstance(col, (int, float))]

    cols_acumulado = [col for col in cols_meses if col <= datas['mes_atual'] - 1]
    cols_1_tri = [col for col in cols_meses if 1 <= col <= 3]
    cols_2_tri = [col for col in cols_meses if 4 <= col <= 6]
    cols_3_tri = [col for col in cols_meses if 7 <= col <= 9]
    cols_4_tri = [col for col in cols_meses if 10 <= col <= 12]

    if class_cont == 'CMV':
        df_categoria[cols_meses] = df_categoria[cols_meses].replace(0, np.nan)
        df_categoria['Acumulado'] = df_categoria[cols_acumulado].mean(axis=1)
        df_categoria['ANO'] = df_categoria[cols_meses].mean(axis=1)
        df_categoria['1 TRI'] = df_categoria[cols_1_tri].mean(axis=1)
        df_categoria['2 TRI'] = df_categoria[cols_2_tri].mean(axis=1)
        df_categoria['3 TRI'] = df_categoria[cols_3_tri].mean(axis=1)
        df_categoria['4 TRI'] = df_categoria[cols_4_tri].mean(axis=1)
    else:
        df_categoria['Acumulado'] = df_categoria[cols_acumulado].sum(axis=1)
        df_categoria['ANO'] = df_categoria[cols_meses].sum(axis=1)
        df_categoria['1 TRI'] = df_categoria[cols_1_tri].sum(axis=1)
        df_categoria['2 TRI'] = df_categoria[cols_2_tri].sum(axis=1)
        df_categoria['3 TRI'] = df_categoria[cols_3_tri].sum(axis=1)
        df_categoria['4 TRI'] = df_categoria[cols_4_tri].sum(axis=1)

    return df_categoria


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
    elif valor == '-':
        return valor
    else:
        return f"{valor * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    

def formata_colunas(df, kpi, categoria):
    df = df.rename(columns={
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    })
    df = df.fillna('-')
    colunas_valores = df.columns[1:]
    df = df.reset_index(drop=True)

    # Formata valores numéricos
    if categoria == 'CMV': # Todos são porcentagens
        df_styled = df.style.format(formatar_porcentagem, subset=colunas_valores)
        if kpi != 'Faturamento Total':
            df_styled = df_styled.applymap(highlight_taxas, subset=colunas_valores) # Aplica estilos
    else:
        if kpi == 'Faturamento Total':
            df_styled = df.style.format(formatar_moeda_br, subset=colunas_valores)
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
    
