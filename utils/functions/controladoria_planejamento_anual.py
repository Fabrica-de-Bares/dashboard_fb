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
    pos = df.index.get_loc(indice)

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
def define_linhas_calculadas(df_orcamentos_resumo, df_orcamentos_concatenados, lista_categorias_dre, colunas_meses, tipo, mapa_posicao_percentual=None):
    if tipo == 'Orçamento':
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
        df_final = insere_nova_linha(df_orcamentos_resumo, colunas_meses, receita_liquida, 'Impostos sobre Venda', 'Categoria', 'RECEITA LÍQUIDA')

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
        porc_receita_liquida_cmv = (cmv / receita_liquida).round(2)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_liquida_cmv, '% sobre Receita Bruta', 'Categoria', '% sobre Receita Líquida')

        # % sobre Receita Artístico
        porc_receita_artistico = (custos_artistico / faturamento_artistico).round(2)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_artistico, 'Custos Artístico Geral', 'Categoria', '% sobre Receita Artístico')

        # % sobre Receita de Eventos
        faturamento_eventos = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Locações'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Couvert'][colunas_meses].sum() 
        )
        porc_receita_eventos = (custos_eventos / faturamento_eventos.replace(0, np.nan)).round(2)
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

        # Calcula % sobre Receita Bruta de cada categoria
        for categoria in lista_categorias_dre:
            # Casos específicos (não pedem o cálculo ou foram calculados acima)
            if categoria not in ['Faturamento Bruto', 'Custo Mercadoria Vendida', 'Impostos sobre Venda', 'Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Patrocínio']:
                custos_categoria = df_final[df_final['Categoria'] == categoria][colunas_meses].sum()
                porc_faturamento_bruto_categoria = (custos_categoria / faturamento_bruto).round(2)
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
        porc_receita_liquida_cmv = (cmv / receita_liquida).round(2)
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_liquida_cmv, '% sobre Receita Bruta', 'Categoria', '% sobre Receita Líquida')

        # % sobre Receita Artístico
        porc_receita_artistico = (custos_artistico / faturamento_artistico).round(2)
        apos_linha = mapa_posicao_percentual.get('(-) Custos Artístico Geral')
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_artistico, apos_linha, 'Categoria', '% sobre Receita Artístico')

        # % sobre Receita de Eventos
        faturamento_eventos = (
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos A&B'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Locações'][colunas_meses].sum() +
            df_orcamentos_concatenados[df_orcamentos_concatenados['Categoria'] == 'Eventos Couvert'][colunas_meses].sum() 
        )
        porc_receita_eventos = (custos_eventos / faturamento_eventos.replace(0, np.nan)).round(2)
        apos_linha = mapa_posicao_percentual.get('(-) Custos de Eventos')
        df_final = insere_nova_linha(df_final, colunas_meses, porc_receita_eventos, apos_linha, 'Categoria', '% sobre Receita de Eventos')

        # Calcula % sobre Receita Bruta de cada categoria
        for categoria in lista_categorias_dre:
            # Casos específicos (não pedem o cálculo ou foram calculados acima)
            if categoria not in ['FATURAMENTO BRUTO', '(-) Custo Mercadoria Vendida', '(-) Impostos sobre Venda', 'PJ', 'MDO CLT - Salário', 'Mão de Obra Extra', 'Encargos e Provisões', 'Benefícios', 'Outros B', '(+) Receitas de Patrocínio']:
                custos_categoria = df_final[df_final['Categoria'] == categoria][colunas_meses].sum()
                porc_faturamento_bruto_categoria = (custos_categoria / faturamento_bruto).round(2)
                
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
        '(+/-) Receitas/Despesas Financeiras', 'Patrocínio', '(+) Receitas de Patrocínio', '(-) Despesas de Patrocínio', '(-) Impostos', 
        '(-) CAPEX (Investimentos)', '(+/-) Outras variações no fluxo de caixa', 'Total - Variações s/ Resultado Líquido'
        ]:
        return ['background-color: rgba(255, 165, 0, 0.05); color: #993300; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['FATURAMENTO BRUTO', 'RECEITA LÍQUIDA', 'MARGEM BRUTA DE CONTRIBUIÇÃO', 'EBITDA', 'EBIT', 'Resultado Antes do IR', 'Resultado Líquido']:
        return ['background-color: #E8F2FC; color: black; font-weight: 500'] * len(row)
    
    elif row['Categoria'] in ['% sobre Receita Bruta', '% sobre Receita Líquida', '% sobre Receita Artístico', '% sobre Receita de Eventos', 'FCF', 'Saldo Operacional']:
        return ['background-color: #FFFFFF; color: black; font-weight: 500'] * len(row)

    elif row['Categoria'] in [
        'Custos Artístico', 'Custos Ténico de Som', 'MDO', 'Serviços de Terceiros - Eventos', 'Material de Consumo',
        'Manutenção Geral', 'Transportes', 'Locações', 'Repasses Locação de Espaço',
        'Mão de Obra - PJ', 'PJ', 'Mão de Obra - Salários', 'MDO CLT - Salário', 'Mão de Obra - Extra', 'E-Staff', 
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
    elif valor < 0:
        return f"{valor * (-100):,.2f}%".replace(".", ",")
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

