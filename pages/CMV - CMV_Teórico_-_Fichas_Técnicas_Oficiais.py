import streamlit as st
import pandas as pd

from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico import *
from utils.queries_cmv_teorico_fichas_oficiais import *
from utils.functions.cmv_teorico_fichas_oficiais import (
    _mes_corte,
    resolver_preco_insumo_estoque,
    resolver_preco_item_producao,
    calcular_custo_composicao,
    montar_custo_por_ficha,
    montar_mix_venda,
    montar_painel_insumos,
    montar_painel_producao,
)

st.set_page_config(
    page_icon="🧪",
    page_title="CMV Teórico - Fichas Técnicas Oficiais",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')


def main():
    config_sidebar()
    permissoes, user_name, email = config_permissoes_user()

    col1, col2 = st.columns([6, 2], vertical_alignment="center")
    with col1:
        st.title("🧪 CMV Teórico - Fichas Técnicas Oficiais")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear, icon='🔄', width='stretch')
    st.divider()

    # Seletores
    col_casa, col_mes, col_ano = st.columns([2, 1, 1])
    with col_casa:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Escritório Fabrica de Bares', 'Todas as Casas']
        id_casa, casa, id_zigpay = input_selecao_casas_agregadas(lista_retirar_casas, 'selecao_casa_fichas_oficiais')
    with col_mes:
        nome_mes, mes = seletor_mes_produtos('mes_fichas_oficiais', 'Mês de Apuração')
    with col_ano:
        ano = seletor_ano(2024, 2026, 'ano_fichas_oficiais', 'Ano de Apuração')

    st.divider()

    ids_brutos = tuple(ids_brutos_da_casa(id_casa))

    df_fichas = GET_FICHAS_OFICIAIS_FICHAS_TECNICAS(ids_brutos)
    if df_fichas.empty:
        st.info(f'Esta casa ({casa}) ainda não tem fichas técnicas cadastradas no módulo BlueMe.')
        st.stop()

    # Carga
    df_vendas = GET_FICHAS_OFICIAIS_VENDAS_MES(ids_brutos, ano, mes)
    df_comp_insumos = GET_FICHAS_OFICIAIS_COMPOSICAO_INSUMOS(ids_brutos)
    df_comp_producao = GET_FICHAS_OFICIAIS_COMPOSICAO_PRODUCAO(ids_brutos)
    df_precos_insumos = GET_FICHAS_OFICIAIS_PRECOS_INSUMOS_ESTOQUE(ids_brutos)
    df_precos_producao = GET_FICHAS_OFICIAIS_PRECOS_ITENS_PRODUCAO(ids_brutos)
    df_rendimento = GET_FICHAS_OFICIAIS_RENDIMENTO_PRODUCAO(ids_brutos)

    if df_vendas.empty:
        st.warning(f'Sem vendas registradas para {casa} em {nome_mes}/{ano}.')
        st.stop()

    # Resolução de preço + custo
    mes_corte = _mes_corte(ano, mes)
    df_precos_insumos_resolvidos = resolver_preco_insumo_estoque(df_precos_insumos, mes_corte)
    df_precos_producao_resolvidos = resolver_preco_item_producao(df_precos_producao, df_rendimento, mes_corte)

    df_insumos_custeados = calcular_custo_composicao(df_comp_insumos, df_precos_insumos_resolvidos, "FK_ITEM_ESTOQUE")
    df_producao_custeada = calcular_custo_composicao(df_comp_producao, df_precos_producao_resolvidos, "FK_ITEM_PRODUCAO")
    df_custo_ficha = montar_custo_por_ficha(df_insumos_custeados, df_producao_custeada)

    df_mix = montar_mix_venda(df_vendas, df_fichas, df_custo_ficha)
    if df_mix.empty:
        st.warning(f'Sem pratos vendidos (excluindo gorjeta) para {casa} em {nome_mes}/{ano}.')
        st.stop()

    df_painel_insumos = montar_painel_insumos(df_insumos_custeados, df_fichas)
    df_painel_producao = montar_painel_producao(df_producao_custeada, df_fichas)

    # ==========================================================================
    # SEÇÃO 1 — KPIs
    # ==========================================================================
    # Linha 1 — Visão Geral (todos os pratos vendidos no período, sem depender de cadastro
    # de ficha técnica: Faturamento/Desconto são sempre corretos, vêm direto da venda).
    faturamento_bruto = float(df_mix['Faturamento_Bruto'].sum())
    desconto = float(df_mix['Desconto'].sum())
    faturamento_liquido = float(df_mix['Faturamento_Liquido'].sum())

    col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment='center')
    with col1:
        kpi_card_cmv_teorico('Faturamento Bruto', f'R$ {format_brazilian(faturamento_bruto)}', background_color="#FFFFFF", title_color="#333", value_color="#000")
    with col2:
        kpi_card_cmv_teorico('Desconto', f'R$ {format_brazilian(desconto)}', background_color="#FFFFFF", title_color="#333", value_color="#000")
    with col3:
        kpi_card_cmv_teorico('Faturamento Líquido', f'R$ {format_brazilian(faturamento_liquido)}', background_color="#FFFFFF", title_color="#333", value_color="#000")

    # Linha 2 — CMV Real: só pratos ✅ OK (custo validado) entram no numerador E no
    # denominador — antes o denominador somava TODOS os pratos (inclusive pendências, cujo
    # custo é 0 por regra de nunca inventar número), o que diluía o CMV% para baixo sem
    # nenhuma indicação visual disso. Cobertura explicita quanto do faturamento está de fato
    # coberto por esse cálculo (achado corrigido em 14/08/2026, mesma correção replicada no
    # relatório HTML de diretoria).
    df_mix_ok = df_mix[df_mix['Status'] == '✅ OK']
    faturamento_bruto_ok = float(df_mix_ok['Faturamento_Bruto'].sum())
    custo_total_ok = float(df_mix_ok['Custo_Total_Vendido'].sum())
    cmv_percent_geral = round((custo_total_ok / faturamento_bruto_ok * 100), 2) if faturamento_bruto_ok else 0
    cobertura_percent = round((faturamento_bruto_ok / faturamento_bruto * 100), 1) if faturamento_bruto else 0

    col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment='center')
    with col1:
        kpi_card_cmv_teorico('Custo Total (só pratos com custo validado)', f'R$ {format_brazilian(custo_total_ok)}', background_color="#FFFFFF", title_color="#333", value_color="#000")
    with col2:
        cor_cmv = cor_porcentagem_cmv(cmv_percent_geral)
        kpi_card_cmv_teorico('CMV % (só pratos com custo validado)', f'{format_brazilian(cmv_percent_geral)} %', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=f'{cmv_percent_geral}', color_percentual=cor_cmv)
    with col3:
        cor_cobertura = 'verde' if cobertura_percent >= 80 else 'amarelo' if cobertura_percent >= 60 else 'vermelho'
        kpi_card_cmv_teorico('Cobertura do Faturamento', f'{format_brazilian(cobertura_percent)} %', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=cobertura_percent, color_percentual=cor_cobertura)

    st.caption('CMV% e Custo Total desta linha somam apenas os pratos com ficha técnica única e preço resolvido (status ✅ OK) — pratos sem ficha, com ficha ambígua ou sem preço ficam fora do numerador e do denominador. Cobertura do Faturamento mostra quanto do Faturamento Bruto (linha acima) está de fato representado nesse cálculo.')

    qtde_total = len(df_mix)
    qtde_ok = int((df_mix['Status'] == '✅ OK').sum())
    qtde_sem_ficha = int(df_mix['Sem_Ficha_Tecnica'].sum())
    qtde_ambigua = int(df_mix['Ficha_Ambigua'].sum())
    qtde_sem_preco = int(df_mix['Sem_Preco_Ficha'].sum())

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], vertical_alignment='center')
    with col1:
        kpi_card_cmv_teorico('✅ Pratos OK', f'{qtde_ok}', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=round(qtde_ok / qtde_total * 100, 1), color_percentual='verde')
    with col2:
        kpi_card_cmv_teorico('🚫 Sem Ficha Técnica', f'{qtde_sem_ficha}', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=round(qtde_sem_ficha / qtde_total * 100, 1), color_percentual='vermelho')
    with col3:
        kpi_card_cmv_teorico('⚠️ Ficha Ambígua', f'{qtde_ambigua}', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=round(qtde_ambigua / qtde_total * 100, 1), color_percentual='amarelo')
    with col4:
        kpi_card_cmv_teorico('❓ Sem Preço Resolvido', f'{qtde_sem_preco}', background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=round(qtde_sem_preco / qtde_total * 100, 1), color_percentual='amarelo')

    st.write('')

    # ==========================================================================
    # SEÇÃO 2 — Painéis de pendência de cadastro
    # ==========================================================================
    st.markdown('## Pendências de Cadastro')
    st.caption('Ordenado por faturamento — priorize corrigir no BlueMe pelos itens do topo de cada lista.')

    with st.expander(f'🚫 Pratos sem Ficha Técnica ({qtde_sem_ficha})', expanded=False):
        st.caption('Casa mostra de qual loja física veio a venda — em casa agregada, cada loja tem catálogo ZigPay próprio: o mesmo prato pode ter a ficha cadastrada em uma loja e não na outra (não é duplicata nem prato fantasma).')
        df_sem_ficha = df_mix[df_mix['Sem_Ficha_Tecnica'] == 1][
            ['Produto', 'PRODUCT_ID', 'Casa', 'Categoria', 'Quantidade', 'Faturamento_Bruto']
        ].rename(columns={'PRODUCT_ID': 'ID Zigpay', 'Faturamento_Bruto': 'Faturamento Bruto'})
        if not df_sem_ficha.empty:
            button_download(df_sem_ficha, f'sem_ficha_{casa}'[:31], f'sem_ficha_{casa}'[:31])
            st.dataframe(format_columns_brazilian(df_sem_ficha, ['Faturamento Bruto']), width='stretch', hide_index=True)
        else:
            st.write('Nenhum prato pendente.')

    with st.expander(f'⚠️ Fichas Técnicas Ambíguas ({qtde_ambigua})', expanded=False):
        df_ambiguas = df_mix[df_mix['Ficha_Ambigua'] == 1][
            ['Produto', 'PRODUCT_ID', 'Casa', 'N_Fichas_Ambiguas', 'Faturamento_Bruto']
        ].rename(columns={'PRODUCT_ID': 'ID Zigpay', 'N_Fichas_Ambiguas': 'Nº Fichas Ativas', 'Faturamento_Bruto': 'Faturamento Bruto'})
        if not df_ambiguas.empty:
            button_download(df_ambiguas, f'ambiguas_{casa}'[:31], f'ambiguas_{casa}'[:31])
            st.dataframe(format_columns_brazilian(df_ambiguas, ['Faturamento Bruto']), width='stretch', hide_index=True)
            st.caption('Detalhe das fichas conflitantes por prato — desativar no BlueMe todas menos a correta:')
            ids_zigpay_ambiguos = df_ambiguas['ID Zigpay'].unique().tolist()
            df_fichas_conflitantes = df_fichas[df_fichas['ID_ZIGPAY'].astype(str).isin(ids_zigpay_ambiguos)][
                ['ID_ZIGPAY', 'ID_Ficha_Tecnica', 'Ficha_Tecnica', 'PRECO_VENDA', 'Custo_Total_Cadastrado']
            ].sort_values(['ID_ZIGPAY', 'ID_Ficha_Tecnica'])
            st.dataframe(df_fichas_conflitantes, width='stretch', hide_index=True)
        else:
            st.write('Nenhuma ficha ambígua.')

    with st.expander(f'❓ Fichas com Preço Incompleto ({qtde_sem_preco})', expanded=False):
        df_sem_preco = df_mix[df_mix['Sem_Preco_Ficha'] == 1][
            ['Produto', 'PRODUCT_ID', 'Casa', 'ID_Ficha_Tecnica', 'Faturamento_Bruto']
        ].rename(columns={'PRODUCT_ID': 'ID Zigpay', 'ID_Ficha_Tecnica': 'ID Ficha Técnica', 'Faturamento_Bruto': 'Faturamento Bruto'})
        if not df_sem_preco.empty:
            button_download(df_sem_preco, f'sem_preco_{casa}'[:31], f'sem_preco_{casa}'[:31])
            st.dataframe(format_columns_brazilian(df_sem_preco, ['Faturamento Bruto']), width='stretch', hide_index=True)
        else:
            st.write('Nenhuma ficha com preço incompleto.')

    st.write('')

    # ==========================================================================
    # SEÇÃO 3 — Mix de Venda
    # ==========================================================================
    col1, col2 = st.columns([3, 1], vertical_alignment='bottom', gap='large')
    with col1:
        st.markdown(f'## Mix de Venda ({casa} — {nome_mes}/{ano})')

    col3, col4, col5 = st.columns([1, 1, 1], vertical_alignment='top', gap='large')
    with col3:
        lista_status = df_mix['Status'].unique().tolist()
        status_selecionados = st.multiselect('Status', options=lista_status, default=lista_status, key='filtro_status_fichas_oficiais')
    with col4:
        lista_categorias = df_mix['Categoria'].dropna().unique().tolist()
        categorias_selecionadas = st.multiselect('Categoria', options=lista_categorias, default=lista_categorias, key='filtro_categoria_fichas_oficiais')
    with col5:
        abc_selecionados = st.multiselect('Curva ABC', options=['A', 'B', 'C'], default=['A', 'B', 'C'], key='filtro_abc_fichas_oficiais')

    df_mix_filtrado = df_mix[
        df_mix['Status'].isin(status_selecionados)
        & df_mix['Categoria'].isin(categorias_selecionadas)
        & df_mix['ABC'].isin(abc_selecionados)
    ]

    colunas_exibir = ['Produto', 'PRODUCT_ID', 'Casa', 'Categoria', 'ABC', 'Status', 'Quantidade',
                       'Preco_Medio', 'Faturamento_Bruto', 'Desconto', 'Faturamento_Liquido',
                       'Custo_Unitario_Ficha', 'Custo_Total_Vendido', 'CMV_Percent',
                       'Meta_CMV_Percent', 'Delta_CMV_PP']
    df_mix_exibir = df_mix_filtrado[colunas_exibir].rename(columns={
        'PRODUCT_ID': 'ID Zigpay', 'Preco_Medio': 'Preço Médio',
        'Faturamento_Bruto': 'Venda Bruta', 'Faturamento_Liquido': 'Venda Líquida',
        'Custo_Unitario_Ficha': 'Custo Unitário', 'Custo_Total_Vendido': 'Custo Total',
        'CMV_Percent': 'CMV %', 'Meta_CMV_Percent': 'Meta CMV %', 'Delta_CMV_PP': 'Delta (p.p.)',
    })

    if df_mix_exibir.empty:
        st.warning('Nenhum prato encontrado para os filtros selecionados.')
    else:
        col1, col2 = st.columns([6, 1], vertical_alignment='bottom', gap='large')
        with col2:
            button_download(df_mix_exibir, f'mix_venda_{casa}'[:31], f'mix_venda_{casa}'[:31])
        st.dataframe(
            df_mix_exibir,
            column_config={
                'CMV %': st.column_config.ProgressColumn('CMV %', format='percent', min_value=0, max_value=1),
                'Meta CMV %': st.column_config.NumberColumn('Meta CMV %', format='percent'),
                'Delta (p.p.)': st.column_config.NumberColumn('Delta (p.p.)', format='percent'),
                'Preço Médio': st.column_config.NumberColumn('Preço Médio', format='R$ %.2f'),
                'Venda Bruta': st.column_config.NumberColumn('Venda Bruta', format='R$ %.2f'),
                'Desconto': st.column_config.NumberColumn('Desconto', format='R$ %.2f'),
                'Venda Líquida': st.column_config.NumberColumn('Venda Líquida', format='R$ %.2f'),
                'Custo Unitário': st.column_config.NumberColumn('Custo Unitário', format='R$ %.2f'),
                'Custo Total': st.column_config.NumberColumn('Custo Total', format='R$ %.2f'),
            },
            height=568,
            width='stretch',
            hide_index=True,
        )

    # ==========================================================================
    # SEÇÃO 4 — Drill-down por prato
    # ==========================================================================
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment='bottom', gap='large')
        with col2:
            df_lista_produtos = df_mix[df_mix['ID_Ficha_Tecnica'].notna()][['ID_Ficha_Tecnica', 'Produto']].drop_duplicates()
            df_lista_produtos['ID - Produto'] = df_lista_produtos['ID_Ficha_Tecnica'].astype(int).astype(str) + ' - ' + df_lista_produtos['Produto']
            lista_produtos = df_lista_produtos['ID - Produto'].tolist()

            if not lista_produtos:
                st.info('Nenhum prato com ficha técnica resolvida (única) para detalhar composição.')
            else:
                produto_selecionado = st.selectbox('Selecione um prato para ver a composição da ficha técnica', lista_produtos, key='drilldown_fichas_oficiais')
                id_ficha_selecionada = int(produto_selecionado.split(' - ')[0])
                linha_prato = df_mix[df_mix['ID_Ficha_Tecnica'] == id_ficha_selecionada].iloc[0]

                col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment='center')
                with col1:
                    kpi_card_cmv_teorico('Preço de Venda (médio)', f"R$ {format_brazilian(linha_prato['Preco_Medio'])}", background_color="#FFFFFF", title_color="#333", value_color="#000", height=90)
                with col2:
                    kpi_card_cmv_teorico('Custo do Item', f"R$ {format_brazilian(linha_prato['Custo_Unitario_Ficha'])}", background_color="#FFFFFF", title_color="#333", value_color="#000", height=90)
                with col3:
                    cmv_pct_prato = round(linha_prato['CMV_Percent'] * 100, 2) if pd.notna(linha_prato['CMV_Percent']) else 0
                    kpi_card_cmv_teorico('CMV %', f'{format_brazilian(cmv_pct_prato)} %', background_color="#FFFFFF", title_color="#333", value_color="#000", height=90)

                st.write('')
                st.markdown(f'### Composição — {produto_selecionado}')

                df_insumos_prato = df_painel_insumos[df_painel_insumos['ID_Ficha_Tecnica'] == id_ficha_selecionada][
                    ['Insumo', 'Unidade_Medida_Nome', 'Quantidade_Convertida', 'Preco_Unitario', 'Custo_Total', 'Fonte_Preco', 'Sem_Preco']
                ].rename(columns={'Unidade_Medida_Nome': 'Unidade', 'Quantidade_Convertida': 'Quantidade', 'Preco_Unitario': 'Preço Unitário', 'Custo_Total': 'Custo Total', 'Fonte_Preco': 'Fonte do Preço'})
                df_producao_prato = df_painel_producao[df_painel_producao['ID_Ficha_Tecnica'] == id_ficha_selecionada][
                    ['Item_Producao', 'Unidade_Medida_Nome', 'Quantidade_Convertida', 'Preco_Unitario', 'Custo_Total', 'Fonte_Preco', 'Sem_Preco']
                ].rename(columns={'Item_Producao': 'Item de Produção', 'Unidade_Medida_Nome': 'Unidade', 'Quantidade_Convertida': 'Quantidade', 'Preco_Unitario': 'Preço Unitário', 'Custo_Total': 'Custo Total', 'Fonte_Preco': 'Fonte do Preço'})

                st.markdown('##### Insumos de Estoque')
                if not df_insumos_prato.empty:
                    st.dataframe(df_insumos_prato, width='stretch', hide_index=True)
                else:
                    st.write('Sem insumos de estoque diretos nesta ficha.')

                st.markdown('##### Itens de Produção')
                if not df_producao_prato.empty:
                    st.dataframe(df_producao_prato, width='stretch', hide_index=True)
                else:
                    st.write('Sem itens de produção diretos nesta ficha.')

    # ==========================================================================
    # SEÇÃO 5 — Premissas
    # ==========================================================================
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment='bottom', gap='large')
        with col2:
            st.markdown('## Premissas')
            st.markdown('### Preço vigente dos insumos/itens de produção')
            st.markdown(
                '- Preço médio (`MEDIA_MES`) do mês anterior ao período apurado; \n'
                '- Se ausente, usa o preço mais recente informado localmente (`ULTIMA_LOCAL`); \n'
                '- Preço é resolvido por empresa — a mesma casa agregada pode ter preços distintos para o mesmo insumo entre suas empresas satélite; \n'
                '- Quantidades em gramas/mililitros são convertidas para quilo/litro quando o preço cadastrado do insumo é por KG/L.'
            )
            st.markdown('### CMV %')
            st.markdown(
                '- Calculado sobre o **Faturamento Bruto** (preço de tabela × quantidade), não o Líquido — desconto dado por gerente de casa é uma linha própria de custo/despesa na DRE, não deve reduzir o denominador do CMV teórico; \n'
                '- Só é calculado para pratos com ficha técnica única e todos os componentes com preço resolvido (status ✅ OK).'
            )
            st.markdown('### Pendências de cadastro')
            st.markdown(
                '- **🚫 Sem Ficha Técnica**: o prato foi vendido mas não tem nenhuma ficha técnica ativa cadastrada no BlueMe para o código Zigpay — ação: cadastrar a ficha; \n'
                '- **⚠️ Ficha Ambígua**: existe mais de 1 ficha técnica ativa simultânea para o mesmo código Zigpay — ação: desativar no BlueMe todas as fichas redundantes, deixando 1 só ativa; \n'
                '- **❓ Sem Preço Resolvido**: a ficha existe e é única, mas algum insumo ou item de produção da composição não tem preço `MEDIA_MES` nem `ULTIMA_LOCAL` cadastrado — ação: cadastrar o preço do insumo/item.'
            )
            st.markdown('### Escopo')
            st.markdown('Piloto — hoje só Girondino tem cadastro robusto de fichas técnicas no módulo BlueMe. Outras casas aparecem vazias até o rollout do módulo avançar; a página funciona para qualquer casa sem precisar de novo deploy.')
        st.write('')


if __name__ == '__main__':
    main()
