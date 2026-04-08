import streamlit as st
import pandas as pd
import numpy as np 


# Análise SWOT
def render_swot_box(titulo, classe, lista, casa):
    itens = "".join([f"<li>{item}</li>" for item in lista])
    if casa == 'Arcos' or casa == 'Girondino' or casa == 'Jacaré' or casa == 'Ultra Evil Premium Ltda ':
        height = '18em'
    elif casa == 'Bar Léo - Centro':
        height = '32em'
    elif casa == 'Blue Note - São Paulo':
        if classe == 'fraquezas' or classe == 'ameacas': height = '30em'
        else: height = '34em'
    else: height = '26em'

    return f"""
<div class="swot-box" style="height: {height}">
    <div class="swot-title {classe}">{titulo}</div>
    <ul class="swot-list">
        {itens}
    </ul>
</div>
"""

def render_swot(dados, casa):
    col1, col2 = st.columns(2)

    # FORÇAS + OPORTUNIDADES
    with col1:
        st.markdown('<h6 style="text-align: center;">FATORES INTERNOS</h6>', unsafe_allow_html=True)
        st.markdown(render_swot_box("FORÇAS", "forcas", dados["forcas"], casa), unsafe_allow_html=True)

    with col2:
        st.markdown('<h6 style="text-align: center;">FATORES EXTERNOS</h6>', unsafe_allow_html=True)
        st.markdown(render_swot_box("OPORTUNIDADES", "oportunidades", dados["oportunidades"], casa), unsafe_allow_html=True)

    st.divider()

    col3, col4 = st.columns(2)

    # FRAQUEZAS + AMEAÇAS
    with col3:
        st.markdown(render_swot_box("FRAQUEZAS", "fraquezas", dados["fraquezas"], casa), unsafe_allow_html=True)
        st.markdown('<h6 style="text-align: center; margin-top: 15px;">FATORES INTERNOS</h6>', unsafe_allow_html=True)

    with col4:
        st.markdown(render_swot_box("AMEAÇAS", "ameacas", dados["ameacas"], casa), unsafe_allow_html=True)
        st.markdown('<h6 style="text-align: center; margin-top: 15px;">FATORES EXTERNOS</h6>', unsafe_allow_html=True)


# Orçamento Operacional
def loop_prepara_dados_despesas(lista_categorias_orcamento, df_orcamento_filtrado, lista_df_orcamentos):
    for categoria_orcamento in lista_categorias_orcamento:        
        df_orcamentos = df_orcamento_filtrado[df_orcamento_filtrado['Classificação Contábil 1'] == categoria_orcamento].copy()
        df_orcamentos = calcula_linha_total(df_orcamentos, categoria_orcamento)
        lista_df_orcamentos.append(df_orcamentos)

    return lista_df_orcamentos


# Cria linha no topo do df com valor total e título por class. cont.
def calcula_linha_total(df, categoria):
    colunas_numericas = df.select_dtypes(include='number').columns

    nova_linha = df[colunas_numericas].sum().to_frame().T # Soma essas colunas
    nova_linha['Classificação Contábil 2'] = categoria

    df = pd.concat([nova_linha, df], ignore_index=True) # Junta com o df original
    return df


# Insere linhas de porcentagens e outros valores no meio do df
def insere_nova_linha(df, colunas_meses, valor, apos_linha, categoria):
    nova_linha = pd.DataFrame([valor])
    nova_linha = nova_linha[colunas_meses]
    nova_linha['Categoria'] = categoria

    indices = df.index[df['Categoria'] == apos_linha]

    if len(indices) == 0:
        return df  # segurança
    
    indice = indices[-1]
    pos = df.index.get_loc(indice)

    df_final = pd.concat([
        df.iloc[:pos+1],
        nova_linha,
        df.iloc[pos+1:]
    ]).reset_index(drop=True)

    return df_final


# Calcula porcentagens e outros valores
def define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_orcamento, colunas_meses):
    # Define valores mais usados
    cmv = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custo Mercadoria Vendida'][colunas_meses].sum()
    custos_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custos Artístico Geral'][colunas_meses].sum()
    faturamento_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Artístico (couvert/shows)'][colunas_meses].sum()
    faturamento_bruto = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Faturamento Bruto'][colunas_meses].sum()
    custos_eventos = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custos de Eventos'][colunas_meses].sum()

    # RECEITA LIQUIDA
    receita_liquida = (
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Faturamento Bruto'][colunas_meses].sum() -
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Desconto sobre Venda'][colunas_meses].sum() - 
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Impostos sobre Venda'][colunas_meses].sum()
    )
    df_final = insere_nova_linha(df_orcamentos_resumo, colunas_meses, receita_liquida, 'Impostos sobre Venda', 'RECEITA LÍQUIDA')

    # % sobre Receita Bruta - CMV
    receita_bruta = (
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Alimentação'][colunas_meses].sum() +
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Bebida'][colunas_meses].sum() +
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Delivery'][colunas_meses].sum()
    )
    porc_receita_bruta_cmv = (cmv / receita_bruta) * 100
    df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_bruta_cmv, 'Custo Mercadoria Vendida', '% sobre Receita Bruta')
    
    # % sobre Receita Líquida - CMV
    porc_receita_liquida_cmv = (cmv / receita_liquida * 100).round(2)
    df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_liquida_cmv, '% sobre Receita Bruta', '% sobre Receita Líquida')

    # % sobre Receita Artístico
    porc_receita_artistico = (custos_artistico / faturamento_artistico * 100).round(2)
    df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_artistico, 'Custos Artístico Geral', '% sobre Receita Artístico')

    # % sobre Receita de Eventos
    faturamento_eventos = (
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Locações'][colunas_meses].sum() +
        df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Couvert'][colunas_meses].sum() 
    )
    porc_receita_eventos = (custos_eventos / faturamento_eventos.replace(0, np.nan) * 100).round(2)
    df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_eventos, 'Custos de Eventos', '% sobre Receita de Eventos')

    # PESSOAL
    pessoal = 0
    for categoria in lista_categorias_orcamento:
        if categoria in ['Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios']:
            pessoal += df_final[df_final['Categoria'] == categoria][colunas_meses].sum() 

    df_final = insere_nova_linha(df_final, colunas_meses, pessoal, 'Deduções sobre Venda', 'PESSOAL')
    lista_categorias_orcamento.append('PESSOAL')

    # MARGEM BRUTA DE CONTRIBUIÇÃO
    margem_bruta_contribuicao = (
        df_final[df_final['Categoria'] == 'RECEITA LÍQUIDA'][colunas_meses].sum() -
        df_final[df_final['Categoria'] == 'Deduções sobre Venda'][colunas_meses].sum() -
        df_final[df_final['Categoria'] == 'Gorjeta'][colunas_meses].sum() -
        df_final[df_final['Categoria'] == 'Custos de Eventos'][colunas_meses].sum() -
        df_final[df_final['Categoria'] == 'Custos Artístico Geral'][colunas_meses].sum() -
        df_final[df_final['Categoria'] == 'Custo Mercadoria Vendida'][colunas_meses].sum() 
    )
    df_final = insere_nova_linha(df_final, colunas_meses, margem_bruta_contribuicao, 'Deduções sobre Venda', 'MARGEM BRUTA DE CONTRIBUIÇÃO')
    lista_categorias_orcamento.append('MARGEM BRUTA DE CONTRIBUIÇÃO')

    # TOTAL - DESPESAS OPERATIVAS
    total_despesas_operativas = 0
    for categoria in lista_categorias_orcamento:
        if categoria in ['PESSOAL', 'Custo de Ocupação', 'Utilidades', 'Informática e TI', 'Manutenção', 'Marketing', 'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias']:
            total_despesas_operativas += df_final[df_final['Categoria'] == categoria][colunas_meses].sum() 

    df_final = insere_nova_linha(df_final, colunas_meses, total_despesas_operativas, 'Sistema de Franquias', 'TOTAL - DESPESAS OPERATIVAS')
    lista_categorias_orcamento.append('TOTAL - DESPESAS OPERATIVAS')
    
    # EBTIDA e EBIT
    total_despesas_operativas = df_final[df_final['Categoria'] == 'TOTAL - DESPESAS OPERATIVAS'][colunas_meses].sum() 
    margem_bruta_contribuicao = df_final[df_final['Categoria'] == 'MARGEM BRUTA DE CONTRIBUIÇÃO'][colunas_meses].sum() 
    ebitda = margem_bruta_contribuicao - total_despesas_operativas
    df_final = insere_nova_linha(df_final, colunas_meses, ebitda, 'TOTAL - DESPESAS OPERATIVAS', 'EBITDA')
    lista_categorias_orcamento.append('EBITDA')
    
    ebit = ebitda
    df_final = insere_nova_linha(df_final, colunas_meses, ebit, 'EBITDA', 'EBIT')

    # Calcula % sobre Receita Bruta de cada categoria
    for categoria in lista_categorias_orcamento:
        # Casos específicos (não pedem o cálculo ou foram calculados acima)
        if categoria not in ['Faturamento Bruto', 'Custo Mercadoria Vendida', 'Impostos sobre Venda', 'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Patrocínio']:
            custos_categoria = df_final[df_final['Categoria'] == categoria][colunas_meses].sum()
            porc_faturamento_bruto_categoria = (custos_categoria / faturamento_bruto * 100).round(2)
            if categoria == 'PESSOAL':
                apos_linha = 'Mão de Obra - Benefícios'
            else:
                apos_linha = categoria
            df_final = insere_nova_linha(df_final, colunas_meses, porc_faturamento_bruto_categoria, apos_linha, '% sobre Receita Bruta')

    df_final = df_final.fillna(0)
    return df_final


# Funções de estilos (cores) e formatações numéricas
def highlight_secoes_dre(row):
    if row['Categoria'] in [
        'Desconto sobre Venda', 'Custo Mercadoria Vendida', 'Impostos sobre Venda', 'Custos Artístico Geral', 'Custos de Eventos',
        'Gorjeta', 'Deduções sobre Venda', 'PESSOAL', 'Custo de Ocupação', 'Utilidades', 'Informática e TI', 'Manutenção', 'Marketing', 
        'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias', 'TOTAL - DESPESAS OPERATIVAS', 'Patrocínio'
        ]:
        return ['background-color: rgba(255, 165, 0, 0.05); color: #993300; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['FATURAMENTO BRUTO', 'RECEITA LÍQUIDA', 'MARGEM BRUTA DE CONTRIBUIÇÃO', 'EBITDA', 'EBIT']:
        return ['background-color: #E8F2FC; color: black; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['% sobre Receita Bruta', '% sobre Receita Líquida', '% sobre Receita Artístico', '% sobre Receita de Eventos']:
        return ['background-color: #FFFFFF; color: black; font-weight: 500'] * len(row)

    elif row['Categoria'] in ['Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios',]:
        return ['background-color: #FFFFFF; color: #993300; font-weight: 500'] * len(row)

    else:
        return [''] * len(row)
    

def formatar_moeda_br(valor):
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_porcentagem(valor):
    if pd.isna(valor):
        return ""
    return f"{valor:,.2f}%".replace(".", ",")

