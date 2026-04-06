import streamlit as st
import pandas as pd


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


def calcula_linha_total(df, categoria):
    colunas_numericas = df.select_dtypes(include='number').columns

    nova_linha = df[colunas_numericas].sum().to_frame().T # Soma essas colunas
    nova_linha['Classificação Contábil 2'] = categoria

    df = pd.concat([nova_linha, df], ignore_index=True) # Junta com o df original
    return df


def define_linhas_calculadas(df):
    colunas_meses = df.select_dtypes(include='number').columns
    receita_liquida = df[df['Categoria'] == 'Faturamento Bruto'][colunas_meses].values \
                    - df[df['Categoria'] == 'Desconto sobre Venda'][colunas_meses].values \
                    - df[df['Categoria'] == 'Impostos sobre Venda'][colunas_meses].values

    nova_linha = pd.DataFrame(receita_liquida, columns=colunas_meses)
    nova_linha['Categoria'] = 'RECEITA LÍQUIDA'

    # Insere na linha correspondente
    indice = df[
        df['Categoria'] == 'Impostos sobre Venda'
    ].index.max()

    df_parte1 = df.loc[:indice]
    df_parte2 = df.loc[indice+1:]

    df_final = pd.concat([
        df_parte1,
        nova_linha,
        df_parte2
    ])
    return df_final


