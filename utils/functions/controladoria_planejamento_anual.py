import streamlit as st
import pandas as pd
import numpy as np
from utils.functions.general_functions import format_brazilian_without_decimal
from utils.constants.general_constants import TAXA_DESPESAS_FINANCEIRAS_PADRAO, TAXA_DESPESAS_FINANCEIRAS_EXCECOES


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


# Cria linha no topo do df com valor total e título por class. cont. - Orçamento e Real DRE
def calcula_linha_total(df, categoria):
    colunas_numericas = df.select_dtypes(include='number').columns

    nova_linha = df[colunas_numericas].sum().to_frame().T # Soma essas colunas
    nova_linha['Classificação Contábil 2'] = categoria

    df = pd.concat([nova_linha, df], ignore_index=True) # Junta com o df original
    return df


# Insere linhas logo após o header (primeira linha do df) - Headcount Pessoas
def insere_apos_header(df, colunas_meses, valor, col, categoria):
    nova_linha = pd.DataFrame([valor])
    nova_linha = nova_linha[colunas_meses]
    nova_linha[col] = categoria

    df_final = pd.concat([
        df.iloc[:0],  # header (primeira linha)
        nova_linha,
        df.iloc[0:]
    ]).reset_index(drop=True)

    return df_final


# Insere linhas de porcentagens e outros valores no meio do df
def insere_nova_linha(df, colunas_meses, valor, apos_linha, col, categoria):
    nova_linha = pd.DataFrame([valor])
    nova_linha = nova_linha[colunas_meses]
    nova_linha[col] = categoria

    indices = df.index[df[col] == apos_linha]

    if len(indices) == 0:
        return df  # segurança
    
    indice = indices[-1]
    pos = np.where(df.index == indice)[0][-1]

    df_final = pd.concat([
        df.iloc[:pos+1],
        nova_linha,
        df.iloc[pos+1:]
    ]).reset_index(drop=True)

    return df_final


# Seleciona parte do df - Headcount Pessoas
def fatia_por_categoria(df, coluna, inicio, fim):
    idx_inicio = df.index[df[coluna] == inicio][0]
    idx_fim = df.index[df[coluna] == fim][0]
    return df.loc[idx_inicio:idx_fim]


# Calcula porcentagens e outros valores - Orçamento e Real DRE
<<<<<<< Updated upstream
def define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_dre, colunas_meses, tipo, mapa_posicao_percentual=None, faturamento_bruto_por_casa=None):
=======
def define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_dre, colunas_meses, tipo, mapa_posicao_percentual=None, casa=None):
>>>>>>> Stashed changes
    if tipo == 'Orçamento':
        # Define valores mais usados
        cmv = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custo Mercadoria Vendida'][colunas_meses].sum()
        custos_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custos Artístico Geral'][colunas_meses].sum()
        faturamento_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Artístico (couvert/shows)'][colunas_meses].sum()
        faturamento_bruto = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Faturamento Bruto'][colunas_meses].sum()
        custos_eventos = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Custos de Eventos'][colunas_meses].sum()

        # PATROCÍNIO líquido (valores gravados sempre positivos no upload - Despesas precisa entrar com sinal invertido)
        receitas_patrocinio = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == '(+) Receitas de Patrocínio'][colunas_meses].sum()
        despesas_patrocinio = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == '(-) Despesas de Patrocínio'][colunas_meses].sum()
        patrocinio_liquido = receitas_patrocinio - despesas_patrocinio

        # RECEITA LIQUIDA
        receita_liquida = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Faturamento Bruto'][colunas_meses].sum() -
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Desconto sobre Venda'][colunas_meses].sum() - 
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Impostos sobre Venda'][colunas_meses].sum()
        )
        df_final = insere_nova_linha(df_orcamentos_resumo, colunas_meses, receita_liquida, 'Impostos sobre Venda', 'Categoria', 'RECEITA LÍQUIDA')

        # Substitui a soma bruta de 'Patrocínio' (Receitas + Despesas somadas como positivas) pelo valor líquido
        df_final.loc[df_final['Categoria'] == 'Patrocínio', colunas_meses] = patrocinio_liquido.values

        # % sobre Receita Bruta - CMV
        receita_bruta = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Alimentação'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Bebida'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Delivery'][colunas_meses].sum()
        )
        porc_receita_bruta_cmv = (cmv / receita_bruta)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_bruta_cmv, 'Custo Mercadoria Vendida', 'Categoria', '% sobre Receita Bruta')
        
        # % sobre Receita Líquida - CMV
        porc_receita_liquida_cmv = (cmv / receita_liquida)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_liquida_cmv, '% sobre Receita Bruta', 'Categoria', '% sobre Receita Líquida')

        # % sobre Receita Artístico
        porc_receita_artistico = (custos_artistico / faturamento_artistico)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_artistico, 'Custos Artístico Geral', 'Categoria', '% sobre Receita Artístico')

        # % sobre Receita de Eventos
        faturamento_eventos = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Locações'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Couvert'][colunas_meses].sum()
        )
        porc_receita_eventos = (custos_eventos / faturamento_eventos.replace(0, np.nan))
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_eventos, 'Custos de Eventos', 'Categoria', '% sobre Receita de Eventos')

        # PESSOAL
        pessoal = 0
        for categoria in lista_categorias_dre:
            if categoria in ['Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios']:
                pessoal += df_final[df_final['Categoria'] == categoria][colunas_meses].sum() 

        df_final = insere_nova_linha(df_final, colunas_meses, pessoal, 'Deduções sobre Venda', 'Categoria', 'PESSOAL')
        lista_categorias_dre.append('PESSOAL')

        # MARGEM BRUTA DE CONTRIBUIÇÃO
        margem_bruta_contribuicao = (
            df_final[df_final['Categoria'] == 'RECEITA LÍQUIDA'][colunas_meses].sum() -
            df_final[df_final['Categoria'] == 'Deduções sobre Venda'][colunas_meses].sum() -
            df_final[df_final['Categoria'] == 'Gorjeta'][colunas_meses].sum() -
            df_final[df_final['Categoria'] == 'Custos de Eventos'][colunas_meses].sum() -
            df_final[df_final['Categoria'] == 'Custos Artístico Geral'][colunas_meses].sum() -
            df_final[df_final['Categoria'] == 'Custo Mercadoria Vendida'][colunas_meses].sum() 
        )
        df_final = insere_nova_linha(df_final, colunas_meses, margem_bruta_contribuicao, 'Deduções sobre Venda', 'Categoria', 'MARGEM BRUTA DE CONTRIBUIÇÃO')
        lista_categorias_dre.append('MARGEM BRUTA DE CONTRIBUIÇÃO')

        # TOTAL - DESPESAS OPERATIVAS
        total_despesas_operativas = 0
        for categoria in lista_categorias_dre:
            if categoria in ['PESSOAL', 'Custo de Ocupação', 'Utilidades', 'Informática e TI', 'Manutenção', 'Marketing', 'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias']:
                total_despesas_operativas += df_final[df_final['Categoria'] == categoria][colunas_meses].sum() 

        df_final = insere_nova_linha(df_final, colunas_meses, total_despesas_operativas, 'Sistema de Franquias', 'Categoria', 'TOTAL - DESPESAS OPERATIVAS')
        lista_categorias_dre.append('TOTAL - DESPESAS OPERATIVAS')
        
        # EBTIDA e EBIT
        total_despesas_operativas = df_final[df_final['Categoria'] == 'TOTAL - DESPESAS OPERATIVAS'][colunas_meses].sum() 
        margem_bruta_contribuicao = df_final[df_final['Categoria'] == 'MARGEM BRUTA DE CONTRIBUIÇÃO'][colunas_meses].sum() 
        ebitda = margem_bruta_contribuicao - total_despesas_operativas
        df_final = insere_nova_linha(df_final, colunas_meses, ebitda, 'TOTAL - DESPESAS OPERATIVAS', 'Categoria', 'EBITDA')
        lista_categorias_dre.append('EBITDA')
        
        ebit = ebitda
        df_final = insere_nova_linha(df_final, colunas_meses, ebit, 'EBITDA', 'Categoria', 'EBIT')

<<<<<<< Updated upstream
        # RECEITAS/DESPESAS FINANCEIRAS - taxa por casa (correto mesmo agregando múltiplas casas em "Todas as Casas")
        receitas_despesas_financeiras = pd.Series(0.0, index=colunas_meses)
        for casa_nome, linha_faturamento in faturamento_bruto_por_casa.iterrows():
            taxa = TAXA_DESPESAS_FINANCEIRAS_EXCECOES.get(casa_nome, TAXA_DESPESAS_FINANCEIRAS_PADRAO)
            receitas_despesas_financeiras = receitas_despesas_financeiras - linha_faturamento[colunas_meses] * taxa
=======
        # RECEITAS/DESPESAS FINANCEIRAS
        taxa_despesas_financeiras = TAXA_DESPESAS_FINANCEIRAS_EXCECOES.get(casa, TAXA_DESPESAS_FINANCEIRAS_PADRAO)
        receitas_despesas_financeiras = -(faturamento_bruto * taxa_despesas_financeiras)
>>>>>>> Stashed changes
        df_final = insere_nova_linha(df_final, colunas_meses, receitas_despesas_financeiras, 'EBIT', 'Categoria', 'Receitas/Despesas Financeiras')

        # RESULTADO ANTES DO IR
        resultado_antes_ir = ebit + receitas_despesas_financeiras + patrocinio_liquido
        df_final = insere_nova_linha(df_final, colunas_meses, resultado_antes_ir, 'Patrocínio', 'Categoria', 'Resultado Antes do IR')

        # RESULTADO LÍQUIDO
        impostos = df_final[df_final['Categoria'] == 'Imposto de Renda'][colunas_meses].sum()
        resultado_liquido = resultado_antes_ir - impostos
        df_final = insere_nova_linha(df_final, colunas_meses, resultado_liquido, 'Imposto de Renda', 'Categoria', 'Resultado Líquido')

        # % sobre Receita Bruta - Resultado Líquido
        porc_receita_bruta_resultado_liquido = (resultado_liquido / faturamento_bruto)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_bruta_resultado_liquido, 'Resultado Líquido', 'Categoria', '% sobre Receita Bruta')

        # OUTRAS VARIAÇÕES NO FLUXO DE CAIXA (valores gravados sempre positivos no upload - despesas, entram negativas)
        outras_variacoes_fluxo_caixa = -(
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Remuneração Variável'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Dividendos'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Endividamento Geral'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Processo Judicial'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Processo Civil'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Recurso Processual'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Empréstimos Gerais'][colunas_meses].sum()
        )
        df_final = insere_nova_linha(df_final, colunas_meses, outras_variacoes_fluxo_caixa, 'Investimento - CAPEX', 'Categoria', 'Outras variações no fluxo de caixa')

        # TOTAL - VARIAÇÕES S/ RESULTADO LÍQUIDO
        capex = df_final[df_final['Categoria'] == 'Investimento - CAPEX'][colunas_meses].sum()
        total_variacoes_resultado_liquido = capex + outras_variacoes_fluxo_caixa
        df_final = insere_nova_linha(df_final, colunas_meses, total_variacoes_resultado_liquido, 'Outras variações no fluxo de caixa', 'Categoria', 'Total - Variações s/ Resultado Líquido')

        # FCF
        fcf = resultado_liquido + total_variacoes_resultado_liquido
        df_final = insere_nova_linha(df_final, colunas_meses, fcf, 'Total - Variações s/ Resultado Líquido', 'Categoria', 'FCF')

        # Calcula % sobre Receita Bruta de cada categoria
        for categoria in lista_categorias_dre:
            # Casos específicos (não pedem o cálculo ou foram calculados acima)
            if categoria not in ['Faturamento Bruto', 'Custo Mercadoria Vendida', 'Impostos sobre Venda', 'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Patrocínio', 'Imposto de Renda', 'Investimento - CAPEX', 'Dividendos e Remunerações Variáveis', 'Endividamento']:
                custos_categoria = df_final[df_final['Categoria'] == categoria][colunas_meses].sum()
                porc_faturamento_bruto_categoria = (custos_categoria / faturamento_bruto)
                if categoria == 'PESSOAL':
                    apos_linha = 'Mão de Obra - Benefícios'
                else:
                    apos_linha = categoria
                df_final = insere_nova_linha(df_final, colunas_meses, porc_faturamento_bruto_categoria, apos_linha, 'Categoria', '% sobre Receita Bruta')

    elif tipo == 'DRE Real': # Já tem valores definidos
        lista_categorias_dre.append('PESSOAL')
        lista_categorias_dre.append('EBITDA')
        lista_categorias_dre.append('MARGEM BRUTA DE CONTRIBUIÇÃO')
        lista_categorias_dre.append('TOTAL - DESPESAS OPERATIVAS')
        lista_categorias_dre.append('Resultado Líquido')

        # Define valores mais usados
        cmv = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == '(-) Custo Mercadoria Vendida'][colunas_meses].sum()
        custos_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == '(-) Custos Artístico Geral'][colunas_meses].sum()
        faturamento_artistico = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Artístico (couvert/shows)'][colunas_meses].sum()
        faturamento_bruto = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'FATURAMENTO BRUTO'][colunas_meses].sum()
        custos_eventos = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == '(-) Custos de Eventos'][colunas_meses].sum()

        # RECEITA LIQUIDA
        receita_liquida = df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'RECEITA LÍQUIDA'][colunas_meses].sum()

        # % sobre Receita Bruta - CMV
        receita_bruta = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Alimentação'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Bebida'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Delivery'][colunas_meses].sum()
        )
        porc_receita_bruta_cmv = (cmv / receita_bruta)
        apos_linha = mapa_posicao_percentual.get('(-) Custo Mercadoria Vendida')
        df_final = insere_nova_linha(df_orcamentos_concatenados, colunas_meses, porc_receita_bruta_cmv, apos_linha, 'Categoria', '% sobre Receita Bruta')
        
        # % sobre Receita Líquida - CMV
        porc_receita_liquida_cmv = (cmv / receita_liquida)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_liquida_cmv, '% sobre Receita Bruta', 'Categoria', '% sobre Receita Líquida')

        # % sobre Receita Artístico
        porc_receita_artistico = (custos_artistico / faturamento_artistico)
        apos_linha = mapa_posicao_percentual.get('(-) Custos Artístico Geral')
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_artistico, apos_linha, 'Categoria', '% sobre Receita Artístico')

        # % sobre Receita de Eventos
        faturamento_eventos = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Locações'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Couvert'][colunas_meses].sum()
        )
        porc_receita_eventos = (custos_eventos / faturamento_eventos.replace(0, np.nan))
        apos_linha = mapa_posicao_percentual.get('(-) Custos de Eventos')
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_eventos, apos_linha, 'Categoria', '% sobre Receita de Eventos')

        # Calcula % sobre Receita Bruta de cada categoria
        for categoria in lista_categorias_dre:
            # Casos específicos (não pedem o cálculo ou foram calculados acima)
            if categoria not in ['FATURAMENTO BRUTO', '(-) Custo Mercadoria Vendida', '(-) Impostos sobre Venda', 'PJ', 'MDO CLT - Salário', 'Mão de Obra Extra', 'Encargos e Provisões', 'Benefícios', 'Outros B', '(+) Receitas de Patrocínio']:
                custos_categoria = df_final[df_final['Categoria'] == categoria][colunas_meses].sum()
                porc_faturamento_bruto_categoria = (custos_categoria / faturamento_bruto)

                apos_linha = mapa_posicao_percentual.get(categoria, categoria)
                df_final = insere_nova_linha(df_final, colunas_meses, porc_faturamento_bruto_categoria, apos_linha, 'Categoria', '% sobre Receita Bruta')

    df_final = df_final.fillna(0)
    return df_final


# Funções de estilos (cores) e formatações numéricas - Orçamento e Real DRE
def highlight_secoes_dre(row):
    if row['Categoria'] in [
        'Desconto sobre Venda', '(-) Desconto sobre Venda', 'Custo Mercadoria Vendida', '(-) Custo Mercadoria Vendida', 
        'Impostos sobre Venda', '(-) Impostos sobre Venda', 'Custos Artístico Geral', '(-) Custos Artístico Geral', 
        'Custos de Eventos', '(-) Custos Eventos', 'Gorjeta', '(-) Dedução da Gorjeta', 'Deduções sobre Venda', '(-) Deduções sobre Venda', 
        'PESSOAL', 'Custo de Ocupação', 'Utilidades', 'Informática e TI', 'Manutenção', 'Despesas Gerais', 'Marketing', 
        'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias', 'TOTAL - DESPESAS OPERATIVAS', '(-) Depreciação/Amortização',
        '(+/-) Receitas/Despesas Financeiras', 'Despesas Financeiras', 'Receitas/Despesas Financeiras', 'Patrocínio', '(+) Receitas de Patrocínio', '(-) Despesas de Patrocínio', '(-) Impostos', 'Impostos',
        '(-) CAPEX (Investimentos)', 'Investimento - CAPEX', 'CAPEX (Investimentos)', '(+/-) Outras variações no fluxo de caixa', 'Outras variações no fluxo de caixa', 'Total - Variações s/ Resultado Líquido'
        ]:
        return ['background-color: rgba(255, 165, 0, 0.05); color: #993300; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['Faturamento', 'FATURAMENTO BRUTO', 'RECEITA LÍQUIDA', 'MARGEM BRUTA DE CONTRIBUIÇÃO', 'EBITDA', 'EBIT', 'Resultado Antes do IR', 'Resultado Líquido']:
        return ['background-color: #E8F2FC; color: black; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['% sobre Receita Bruta', '% sobre Receita Líquida', '% sobre Receita Artístico', '% sobre Receita de Eventos', 'Saldo Operacional']:
        return ['background-color: #FFFFFF; color: black; font-weight: 500'] * len(row)

    elif row['Categoria'] == 'FCF':
        return ['background-color: #D4F5EC; color: black; font-weight: 500'] * len(row)

    elif row['Categoria'] in [
        'Custos Artístico', 'Custos Ténico de Som', 'MDO', 'Serviços de Terceiros - Eventos', 'Material de Consumo',
        'Manutenção Geral', 'Transportes', 'Locações', 'Repasses Locação de Espaço',
        'Mão de Obra - PJ', 'PJ', 'Mão de Obra - Salários', 'Salários', 'MDO CLT - Salário', 'Mão de Obra - Extra', 'E-Staff', 
        'Mão de Obra - Encargos e Provisões', 'Encargos e Provisões', 'Mão de Obra - Benefícios', 'Benefícios', 'Outros B']:
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
    else:
        return f"{valor * 100:,.2f}%".replace(".", ",")
    

# Real DRE - caso específico
def altera_pos_item_lista(lista, ref, item_para_mover):
    # Remove o item da posição atual e guarda ele
    indice_atual = lista.index(item_para_mover)
    item = lista.pop(indice_atual)
    
    # Descobre a nova posição do item de referência
    posicao_ref = lista.index(ref)
    
    # Insere após a referência
    lista.insert(posicao_ref + 1, item)
    return lista


def prepara_secoes_headcount(df_inicial, colunas_meses, casa):
    # Squad
    if casa == 'Terraço Notie':
        df_squad = fatia_por_categoria(df_inicial, 'CARGO', 'Líder de Squad', 'Coordenador de Hospitalidade')
    else:
        df_squad = fatia_por_categoria(df_inicial, 'CARGO', 'Líder de Squad', 'Chefe de Manutenção')
    total_meses = df_squad[colunas_meses].sum()
    df_squad = insere_apos_header(df_squad, colunas_meses, total_meses, 'CARGO', '- Squad')

    # Operação
    df_operacao = fatia_por_categoria(df_inicial, 'CARGO', '- Gerente', '- Hostess')
    total_meses = df_operacao[colunas_meses].sum()
    df_operacao = insere_apos_header(df_operacao, colunas_meses, total_meses, 'CARGO', 'Operação')

    # Quadro/Função
    if casa == 'Riviera Bar':
        df_quadro_funcao = fatia_por_categoria(df_inicial, 'CARGO', '-  Maitre', '-  Aprendiz') # Segunda ocorrência
    else:
        df_quadro_funcao = fatia_por_categoria(df_inicial, 'CARGO', '-  Maitre', '-  Operador de Delivery') # Segunda ocorrência
    total_meses = df_quadro_funcao[colunas_meses].sum()
    df_quadro_funcao = insere_apos_header(df_quadro_funcao, colunas_meses, total_meses, 'CARGO', 'Quadro/Função')

    # PJ - Concatena Squad e Operação
    df_pj = pd.concat([df_squad, df_operacao])
    total_meses = df_pj[df_pj['CARGO'].isin(['- Squad', 'Operação'])][colunas_meses].sum()
    df_pj = insere_apos_header(df_pj, colunas_meses, total_meses, 'CARGO', 'PJ')

    df_final = pd.concat([df_pj, df_quadro_funcao]).reset_index(drop=True)
    return df_final


def highlight_secoes_headcount(row):
    if row['CARGO'] in ['PJ', 'Quadro/Função']:
        return ['background-color: rgba(255, 165, 0, 0.05); color: black; font-weight: 500'] * len(row)
    elif row['CARGO'] in ['- Squad', 'Operação']:
        return ['color: black; font-weight: 500'] * len(row)


# --- Helpers compartilhados para separar análises de Headcount/Remuneração por CLT x PJ ---
# Um cargo CLT é diferente de um cargo PJ mesmo com o mesmo nome: essas funções garantem que
# pivot/groupby nunca misturem (soma/média) linhas de modelos de contrato diferentes. Cargos só
# se cruzam entre Aprovado/Efetivo/Orçado/Real quando têm o MESMO nome (após normaliza_nomes_cargo
# do lado Aprovado) — níveis diferentes (ex: "HOSTESS" e "HOSTESS I") NÃO são unificados, contam
# como cargos distintos.

def monta_cruzamento(df_a, df_b, rotulo_a, rotulo_b, colunas_periodo):
    """Substitui o bloco reindex+concat+swaplevel+MultiIndex hoje duplicado entre headcount
    (Aprovado x Efetivo) e remuneração (Orçado x Real). df_a/df_b: DataFrames indexados por
    CARGO, colunas = colunas_periodo, já remapeados/filtrados pro mesmo modelo de contrato.
    Retorna df_comparativo com colunas MultiIndex [(período, rotulo_a), (período, rotulo_b),
    (período, 'Diferença')] e uma coluna 'CARGO'."""
    todos_cargos = df_a.index.union(df_b.index)
    df_a = df_a.reindex(todos_cargos)
    df_b = df_b.reindex(todos_cargos)
    diferenca = df_b.fillna(0) - df_a.fillna(0)

    df_comparativo = pd.concat({rotulo_a: df_a, rotulo_b: df_b, 'Diferença': diferenca}, axis=1).swaplevel(axis=1)
    colunas_comparativo = pd.MultiIndex.from_product([colunas_periodo, [rotulo_a, rotulo_b, 'Diferença']])
    df_comparativo = df_comparativo[colunas_comparativo]
    df_comparativo.index.name = 'CARGO'
    return df_comparativo.reset_index()


def normaliza_nomes_cargo(serie_cargo):
    serie_cargo = serie_cargo.str.replace('^-+\s*', '', regex=True).str.strip().str.upper()
    serie_cargo = serie_cargo.str.replace('GARÇON', 'GARÇOM', regex=True)
    serie_cargo = serie_cargo.str.replace('AJUD LIMPEZA', 'AUXILIAR DE LIMPEZA', regex=True)
    serie_cargo = serie_cargo.str.replace('AJUD COZINHA', 'AJUDANTE DE COZINHA', regex=True)
    serie_cargo = serie_cargo.str.replace('CUMIN', 'CUMIM', regex=True)
    serie_cargo = serie_cargo.str.replace('BAR BACK', 'BARBACK', regex=True)
    serie_cargo = serie_cargo.str.replace('CHEFE DA PORTARIA', 'CHEFE DE PORTARIA', regex=True)
    serie_cargo = serie_cargo.str.replace('^PIA$', 'AJUDANTE DE COZINHA (PIA)', regex=True)
    return serie_cargo


def constroi_aprovado(df_num_colaboradores_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo):
    """Retorna (df_exibicao com linha de TOTAL, df_styled, height, df_para_cruzamento indexado
    por CARGO normalizado — sem a linha de TOTAL, pra não entrar em duplicidade nos cruzamentos)."""
    df_filtrado = df_num_colaboradores_raw[df_num_colaboradores_raw['Modelo Contrato'] == modelo_contrato]
    pivot = df_filtrado.pivot_table(index='CARGO', columns='Mês', values='Valor', aggfunc='sum', sort=False).reset_index()
    pivot = pivot.rename(columns=nomes_meses)
    for col in colunas_meses:
        if col not in pivot.columns:
            pivot[col] = pd.NA
    df_final = pivot[['CARGO', *colunas_meses]]

    df_cruzamento = df_final.copy()
    df_cruzamento['CARGO'] = normaliza_nomes_cargo(df_cruzamento['CARGO'])
    df_cruzamento = df_cruzamento.set_index('CARGO')[colunas_meses_efetivo] if colunas_meses_efetivo else df_cruzamento.set_index('CARGO')[[]]

    # Remove cargos sem headcount aprovado do display (cruzamento mantém todos)
    df_final = df_final[
        df_final[colunas_meses].apply(pd.to_numeric, errors='coerce').fillna(0).any(axis=1)
    ].reset_index(drop=True)

    if not df_final.empty:
        linha_total = df_final[colunas_meses].sum().to_frame().T
        linha_total.insert(0, 'CARGO', 'TOTAL')
        df_final = pd.concat([df_final, linha_total], ignore_index=True)

    df_styled = (
        df_final.style
        .format({col: (lambda x: '' if x == 0 else format_brazilian_without_decimal(x)) for col in colunas_meses})
        .apply(destaca_linha_total_simples, axis=1)
    )
    height = (len(df_final) + 1) * 35
    return df_final, df_styled, height, df_cruzamento


def constroi_efetivo(df_funcionarios_ativos_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo):
    """Retorna (df_exibicao com linha de TOTAL, df_styled, height, df_para_cruzamento indexado
    por CARGO normalizado — sem a linha de TOTAL, pra não entrar em duplicidade nos cruzamentos)."""
    df = df_funcionarios_ativos_mes[df_funcionarios_ativos_mes['Vínculo'] == modelo_contrato]

    if df.empty:
        df_exibicao = pd.DataFrame(columns=['CARGO', *colunas_meses_efetivo])
    else:
        pivot = df.pivot_table(index='Cargo', columns='MES', values='Nº Funcionários Ativos', aggfunc='sum', fill_value=0)
        pivot = pivot.rename(columns=nomes_meses).reset_index().rename(columns={'Cargo': 'CARGO'})
        for col in colunas_meses_efetivo:
            if col not in pivot.columns:
                pivot[col] = 0
        pivot['CARGO'] = pivot['CARGO'].str.upper()
        df_exibicao = pivot[['CARGO', *colunas_meses_efetivo]] if colunas_meses_efetivo else pivot[['CARGO']]

    df_cruzamento = df_exibicao.set_index('CARGO')[colunas_meses_efetivo] if colunas_meses_efetivo else df_exibicao.set_index('CARGO')[[]]

    if not df_exibicao.empty and colunas_meses_efetivo:
        linha_total = df_exibicao[colunas_meses_efetivo].sum().to_frame().T
        linha_total.insert(0, 'CARGO', 'TOTAL')
        df_exibicao = pd.concat([df_exibicao, linha_total], ignore_index=True)

    df_styled = df_exibicao.style.apply(destaca_linha_total_simples, axis=1)
    height = (len(df_exibicao) + 1) * 35
    return df_exibicao, df_styled, height, df_cruzamento


def constroi_remuneracao_orcada(df_remuneracao_raw, modelo_contrato, nomes_meses, colunas_meses, colunas_meses_efetivo, df_num_colaboradores_raw=None):
    """Retorna (df_exibicao, df_styled, height, df_para_cruzamento indexado por CARGO normalizado).
    Se df_num_colaboradores_raw for fornecido, células onde headcount aprovado = 0 ficam em branco."""
    df_filtrado = df_remuneracao_raw[df_remuneracao_raw['Modelo Contrato'] == modelo_contrato].copy()
    df_filtrado['Valor'] = df_filtrado['Valor'].replace(0, pd.NA)  # zeros não entram no denominador da média
    pivot = df_filtrado.pivot_table(index='CARGO', columns='Mês', values='Valor', sort=False).reset_index()
    pivot = pivot.rename(columns=nomes_meses)
    for col in colunas_meses:
        if col not in pivot.columns:
            pivot[col] = pd.NA
    df_final = pivot[['CARGO', *colunas_meses]]

    # Zera remuneração orçada nos meses em que o headcount aprovado é 0
    if df_num_colaboradores_raw is not None and not df_final.empty:
        df_hc = df_num_colaboradores_raw[df_num_colaboradores_raw['Modelo Contrato'] == modelo_contrato]
        if not df_hc.empty:
            pivot_hc = df_hc.pivot_table(index='CARGO', columns='Mês', values='Valor', aggfunc='sum', fill_value=0, sort=False)
            pivot_hc = pivot_hc.rename(columns=nomes_meses)
            df_final_indexed = df_final.set_index('CARGO')
            for col in colunas_meses:
                if col in df_final_indexed.columns and col in pivot_hc.columns:
                    hc_no_mes = pivot_hc[col].reindex(df_final_indexed.index, fill_value=0)
                    df_final_indexed.loc[hc_no_mes == 0, col] = pd.NA
            df_final = df_final_indexed.reset_index()

    # Converte colunas numéricas: None → 0
    for col in colunas_meses:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    # Exibe apenas linhas com pelo menos um mês com valor
    df_final = df_final[df_final[colunas_meses].any(axis=1)].reset_index(drop=True)

    def _fmt(x):
        if pd.isna(x) or x == 0:
            return ''
        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    df_styled = df_final.style.format(_fmt, subset=colunas_meses)

    height = (len(df_final) + 1) * 35
    df_cruzamento = df_final.copy()
    df_cruzamento['CARGO'] = normaliza_nomes_cargo(df_cruzamento['CARGO'])
    df_cruzamento = df_cruzamento.set_index('CARGO').reindex(columns=colunas_meses_efetivo)
    return df_final, df_styled, height, df_cruzamento


def constroi_remuneracao_real(df_remuneracao_real_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo):
    """Retorna df_exibicao indexada por CARGO (média salarial, sem remapeamento de nível —
    igual à tabela Efetivo, o remapeamento só entra na etapa de cruzamento)."""
    df = df_remuneracao_real_mes[df_remuneracao_real_mes['Vínculo'] == modelo_contrato]

    if df.empty:
        return pd.DataFrame(columns=['CARGO', *colunas_meses_efetivo])

    media = df.dropna(subset=['Salário']).groupby(['MES', 'Cargo'])['Salário'].mean().reset_index()
    pivot = media.pivot_table(index='Cargo', columns='MES', values='Salário', sort=False).reset_index().rename(columns={'Cargo': 'CARGO'})
    pivot = pivot.rename(columns=nomes_meses)
    for col in colunas_meses_efetivo:
        if col not in pivot.columns:
            pivot[col] = pd.NA
    pivot['CARGO'] = pivot['CARGO'].str.upper()
    return pivot[['CARGO', *colunas_meses_efetivo]] if colunas_meses_efetivo else pivot[['CARGO']]


def remapeia_headcount(df_aprovado_cru, df_efetivo_cru):
    """Consolida linhas cujo CARGO (já normalizado/uppercased) é EXATAMENTE igual — não unifica
    níveis diferentes (ex: "HOSTESS" e "HOSTESS I" contam como cargos distintos)."""
    df_aprovado = df_aprovado_cru.groupby(level=0).sum()
    df_efetivo = df_efetivo_cru.groupby(level=0).sum()
    todos_cargos = df_aprovado.index.union(df_efetivo.index)
    return df_aprovado.reindex(todos_cargos).fillna(0), df_efetivo.reindex(todos_cargos).fillna(0)


def remapeia_remuneracao(df_orcado_cru, df_remuneracao_real_mes, modelo_contrato, nomes_meses, colunas_meses_efetivo, df_num_colaboradores_raw=None, df_remuneracao_raw=None):
    """Orçado: média ponderada pelo headcount aprovado quando df_num_colaboradores_raw e
    df_remuneracao_raw forem fornecidos (consistente com o Real, que já é ponderado por pessoa);
    caso contrário, média simples entre casas. Real: média dos salários individuais por cargo/mês."""
    if df_num_colaboradores_raw is not None and df_remuneracao_raw is not None:
        df_orcado = pondera_remuneracao_orcada_por_headcount(
            df_num_colaboradores_raw, df_remuneracao_raw, modelo_contrato, nomes_meses, colunas_meses_efetivo
        )
    else:
        df_orcado = df_orcado_cru.replace(0, pd.NA).groupby(level=0).mean()

    df_pessoas = df_remuneracao_real_mes[df_remuneracao_real_mes['Vínculo'] == modelo_contrato].copy()
    df_pessoas['Cargo'] = df_pessoas['Cargo'].str.upper()
    df_real = (
        df_pessoas.dropna(subset=['Salário']).groupby(['MES', 'Cargo'])['Salário'].mean()
        .reset_index().pivot_table(index='Cargo', columns='MES', values='Salário', sort=False)
        .rename(columns=nomes_meses).reindex(columns=colunas_meses_efetivo)
    )

    todos_cargos = df_orcado.index.union(df_real.index)
    return df_orcado.reindex(todos_cargos), df_real.reindex(todos_cargos)


def pondera_remuneracao_orcada_por_headcount(df_num_colaboradores_raw, df_remuneracao_raw, modelo_contrato, nomes_meses, colunas_meses_efetivo):
    """Salário orçado médio ponderado pelo Aprovado de cada casa (Tipo Dado = 'Nº COLABORADORES'),
    usado só no Impacto Financeiro — garante que Custo Orçado = Aprovado x Orçado bata com a soma
    do custo calculado casa a casa, em vez de usar a média simples entre casas (que distorce
    quando o aprovado ou o salário variam bastante de uma casa pra outra)."""
    df_aprovado = df_num_colaboradores_raw[df_num_colaboradores_raw['Modelo Contrato'] == modelo_contrato][['ID Casa', 'CARGO', 'Mês', 'Valor']].copy()
    df_aprovado['CARGO'] = normaliza_nomes_cargo(df_aprovado['CARGO'])
    # Soma linhas com o MESMO CARGO dentro da MESMA casa (mesmo critério de remapeia_headcount)
    df_aprovado = df_aprovado.groupby(['ID Casa', 'CARGO', 'Mês'], as_index=False)['Valor'].sum().rename(columns={'Valor': 'Aprovado'})

    df_orcado = df_remuneracao_raw[df_remuneracao_raw['Modelo Contrato'] == modelo_contrato][['ID Casa', 'CARGO', 'Mês', 'Valor']].copy()
    df_orcado['CARGO'] = normaliza_nomes_cargo(df_orcado['CARGO'])
    # Tira média das linhas com o MESMO CARGO dentro da MESMA casa (0 não entra na média, mesmo critério de remapeia_remuneracao)
    df_orcado['Valor'] = df_orcado['Valor'].replace(0, pd.NA)
    df_orcado = df_orcado.groupby(['ID Casa', 'CARGO', 'Mês'], as_index=False)['Valor'].mean().rename(columns={'Valor': 'Orcado'})

    df_merge = df_aprovado.merge(df_orcado, on=['ID Casa', 'CARGO', 'Mês'], how='inner')
    df_merge['Custo'] = df_merge['Aprovado'] * df_merge['Orcado']

    agrupado = df_merge.groupby(['CARGO', 'Mês'])[['Custo', 'Aprovado']].sum()
    ponderado = (agrupado['Custo'] / agrupado['Aprovado'].replace(0, pd.NA)).rename('OrcadoPonderado').reset_index()

    pivot = ponderado.pivot_table(index='CARGO', columns='Mês', values='OrcadoPonderado', sort=False)
    pivot = pivot.rename(columns=nomes_meses).reindex(columns=colunas_meses_efetivo)
    return pivot


def destaca_diferenca(valor):
    if valor > 0:
        return 'background-color: rgba(42, 120, 214, 0.18); color: #0d366b; font-weight: 600'
    elif valor < 0:
        return 'background-color: rgba(227, 73, 72, 0.18); color: #7a1f1f; font-weight: 600'
    return 'font-weight: 600'


def destaca_linha_total(row):
    if row[('CARGO', '')] == 'TOTAL':
        return ['font-weight: 700; border-top: 2px solid #898781'] * len(row)
    return [''] * len(row)


def destaca_linha_total_simples(row):
    if row['CARGO'] == 'TOTAL':
        return ['font-weight: 700; border-top: 2px solid #898781'] * len(row)
    return [''] * len(row)


def monta_impacto_financeiro(df_aprovado, df_efetivo, df_orcado_sal, df_real_sal, colunas_periodo):
    """Custo = Headcount x Remuneração média, decomposto em efeito Headcount (variação de
    gente, ao salário orçado) e efeito Remuneração (variação de salário, ao headcount
    efetivo). Convenção: positivo = economia (Real < Orçado). Todos os DataFrames de entrada
    já devem estar reindexados pro mesmo conjunto de cargos e mesmas colunas_periodo."""
    df_custo_orcado = (df_aprovado * df_orcado_sal).where(df_aprovado != 0, 0)
    df_custo_real = (df_efetivo * df_real_sal).where(df_efetivo != 0, 0)
    df_diferenca_custo = df_custo_orcado.fillna(0) - df_custo_real.fillna(0)

    df_efeito_headcount = (df_aprovado - df_efetivo) * df_orcado_sal.fillna(0)
    df_efeito_remuneracao = (df_orcado_sal.fillna(0) - df_real_sal.fillna(0)) * df_efetivo

    df_comparativo_impacto = pd.concat(
        {'Orçado': df_custo_orcado, 'Real': df_custo_real, 'Diferença': df_diferenca_custo}, axis=1
    ).swaplevel(axis=1)
    colunas_comparativo_impacto = pd.MultiIndex.from_product([colunas_periodo, ['Orçado', 'Real', 'Diferença']])
    df_comparativo_impacto = df_comparativo_impacto[colunas_comparativo_impacto]
    for col in colunas_comparativo_impacto:
        df_comparativo_impacto[col] = pd.to_numeric(df_comparativo_impacto[col], errors='coerce')
    df_comparativo_impacto.index.name = 'CARGO'
    df_comparativo_impacto = df_comparativo_impacto.reset_index()

    return df_comparativo_impacto, df_custo_orcado, df_custo_real, df_efeito_headcount, df_efeito_remuneracao

