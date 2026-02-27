import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import timedelta
from utils.functions.general_functions_conciliacao import formata_df, traduz_semana_mes
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.queries_cmv import GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO, GET_TRANSF_ESTOQUE, GET_PERDAS_E_CONSUMO_AGRUPADOS
from utils.queries_forecast import GET_VALORACAO_ESTOQUE, GET_VALORACAO_PRODUCAO, GET_EVENTOS_CMV, GET_AUT_BLUE_ME_COM_PEDIDO
from utils.components import dataframe_aggrid
from st_aggrid import ColumnsAutoSizeMode

pd.set_option('future.no_silent_downcasting', True)

############################################ PROJEÇÕES MÊS CORRENTE ############################################

# Prepara df de faturamento agregado diário para a casa selecionada
def prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, fim_do_mes_atual, dois_meses_antes):
    # Filtra por casa
    df_faturamento_agregado_casa = df_faturamento_agregado_dia[
        (df_faturamento_agregado_dia['ID_Casa'] == id_casa) &
        df_faturamento_agregado_dia['Categoria'].isin(['Alimentos', 'Bebidas', 'Couvert', 'Delivery', 'Gifts', 'Eventos A&B', 'Eventos Couvert', 'Eventos Locações', 'Outras Receitas'])
    ].copy()
    df_faturamento_agregado_casa['Data Evento'] = pd.to_datetime(df_faturamento_agregado_casa['Data Evento'], errors='coerce')
    
    # Traduz dia da semana para português
    df_faturamento_agregado_casa['Dia Semana'] = df_faturamento_agregado_casa['Data Evento'].dt.strftime('%A')
    df_faturamento_agregado_casa['Dia Semana'] = df_faturamento_agregado_casa['Dia Semana'].apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )
    
    df_faturamento_agregado_casa['Dia_Mes'] = pd.to_datetime(df_faturamento_agregado_casa['Data Evento'], errors='coerce').dt.day

    # Filtra por casa e mês (anterior e corrente) - para utilizar no cálculo de projeção
    df_faturamento_agregado_mes_corrente = df_faturamento_agregado_casa[
        (df_faturamento_agregado_casa['Data Evento'] >= dois_meses_antes) &
        (df_faturamento_agregado_casa['Data Evento'] <= fim_do_mes_atual)]
    
    return df_faturamento_agregado_mes_corrente


# --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
def criar_df_dias(ano, mes):
    """Cria DataFrame com dias do mês, Data_Evento e Dia Semana traduzido."""
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dias = pd.DataFrame({'Dia_Mes': range(1, ultimo_dia + 1)})

    dias['Data Evento'] = pd.to_datetime({
        'year': ano,
        'month': mes,
        'day': dias['Dia_Mes']
    })

    dias['Dia Semana'] = dias['Data Evento'].dt.strftime('%A').apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )
    return dias

def criar_df_dias_intervalo(ano_inicio, mes_inicio, ano_fim, mes_fim):
    datas = pd.period_range(
        start=f"{ano_inicio}-{mes_inicio:02d}",
        end=f"{ano_fim}-{mes_fim:02d}",
        freq="M"
    )

    lista_df = []

    for periodo in datas:
        ano = periodo.year
        mes = periodo.month
        lista_df.append(criar_df_dias(ano, mes))

    return pd.concat(lista_df, ignore_index=True)

def lista_dias_mes_anterior_atual(ano_atual, mes_atual, df_faturamento_agregado_mes_corrente):
    # Ajusta mês inicial (mês anterior ao atual)
    if mes_atual == 1:
        ano_inicio = ano_atual - 1
        mes_inicio = 12
    elif mes_atual == 2:
        ano_inicio = ano_atual - 1
        mes_inicio = 12
    else:
        ano_inicio = ano_atual
        mes_inicio = mes_atual - 1

    ano_fim = ano_atual + 1
    mes_fim = 12
    
    df_dias_mes = criar_df_dias_intervalo(
        ano_inicio=ano_inicio,
        mes_inicio=mes_inicio, # Por enquanto, só temos dados de faturamento agregado até nov/2025
        ano_fim=ano_fim,
        mes_fim=mes_fim
    )
    
    categorias = (
        df_faturamento_agregado_mes_corrente['Categoria']
        .dropna()
        .unique()
    )
    df_categorias = pd.DataFrame({'Categoria': categorias})

    df_resultado = df_dias_mes.merge(df_categorias, how='cross')
    return df_resultado


# Função para cálculo da projeção - mês corrente
def cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias):
    # Merge com df do mês completo para gerar projeção dos prox dias
    df_dias_futuros_mes = df_faturamento_agregado_mes_corrente.merge(
        df_dias_futuros_com_categorias, 
        how='right', 
        on=['Data Evento', 'Dia Semana', 'Categoria'])
    
    df_dias_futuros_mes['Faturamento Projetado'] = None

    # Loop por categoria
    for categoria in df_dias_futuros_mes['Categoria'].unique():
        df_cat = None
        if categoria not in ('Eventos A&B', 'Eventos Locações', 'Eventos Couvert', 'Outras Receitas'): 
            df_cat = df_dias_futuros_mes[df_dias_futuros_mes['Categoria'] == categoria]
        
        if df_cat is not None and not df_cat.empty:
            for i, row in df_cat.iterrows():
                data = row['Data Evento']

                # if data > today:  # apenas dias futuros 
                # -> estou fazendo para todos os dias (desde o mês anterior) para comparar projetado/real
                dia_semana = row['Dia Semana']

                # pega histórico das duas semanas anteriores MESMO DIA DA SEMANA e MESMA CATEGORIA
                duas_semanas_atras = data - timedelta(days=14)

                historico = df_dias_futuros_mes[
                    (df_dias_futuros_mes['Categoria'] == categoria) &
                    (df_dias_futuros_mes['Dia Semana'] == dia_semana) &
                    (df_dias_futuros_mes['Data Evento'] >= duas_semanas_atras) &
                    (df_dias_futuros_mes['Data Evento'] < data)
                ].copy()

                # usa o Valor_Bruto (real) quando existir, senão a Projeção (que pode vir de dias anteriores)
                # historico['Faturamento Projetado'] = historico['Faturamento Projetado'].fillna(0) # Para dias sem faturamento e sem projeção
                valores_para_media = historico['Valor Bruto'].fillna(historico['Faturamento Projetado']).astype(float)
                
                if not valores_para_media.empty:
                    media = valores_para_media.mean()
                    df_dias_futuros_mes.at[i, 'Faturamento Projetado'] = media
                    df_dias_futuros_mes['Faturamento Projetado'] = df_dias_futuros_mes['Faturamento Projetado'].fillna(0) # Para dias sem faturamento e sem projeção

    # Define valor final
    df_dias_futuros_mes['Valor Final'] = df_dias_futuros_mes['Valor Bruto'].fillna(df_dias_futuros_mes['Faturamento Projetado'])
    return df_dias_futuros_mes


# Exibe projeção por categoria (A&B, delivery, gifts e couvert) - mês corrente (dias anteriores e seguintes)
def exibe_faturamento_categoria_mes_corrente(categoria, df_dias_futuros_mes, tipo, datas):
    df_dias_futuros_mes['Faturamento Projetado'] = df_dias_futuros_mes['Faturamento Projetado'].fillna(0)
    df_dias_futuros_mes['Valor Bruto'] = df_dias_futuros_mes['Valor Bruto'].fillna(0)
    df_dias_futuros_mes['Desconto'] = df_dias_futuros_mes['Desconto'].fillna(0)
    df_dias_futuros_mes['Valor Liquido'] = df_dias_futuros_mes['Valor Liquido'].fillna(0)
    titulo = categoria

    if tipo == 'dias seguintes':
        # Filtra por categoria para exibir próximos dias do mês corrente 
        if categoria == 'A&B':
            df_projecao_faturamento_mes_corrente = df_dias_futuros_mes[
                ((df_dias_futuros_mes['Categoria'] == 'Alimentos') |
                (df_dias_futuros_mes['Categoria'] == 'Bebidas')) & 
                (df_dias_futuros_mes['Data Evento'] >= datas['today']) &
                (df_dias_futuros_mes['Data Evento'] <= datas['fim_mes_atual'])
            ]
            
        else:
            df_projecao_faturamento_mes_corrente = df_dias_futuros_mes[
                (df_dias_futuros_mes['Categoria'] == categoria) &
                (df_dias_futuros_mes['Data Evento'] >= datas['today']) &
                (df_dias_futuros_mes['Data Evento'] <= datas['fim_mes_atual'])
            ]

            if categoria == 'Couvert':
                titulo = 'Artístico (Couvert)'

        # Colunas a serem exibidas
        df_projecao_faturamento_mes_corrente = df_projecao_faturamento_mes_corrente[['Categoria', 'Data Evento', 'Dia Semana', 'Faturamento Projetado']]
        num_columns_dataframe = ['Faturamento Projetado']

        # Exibe titulo
        st.markdown(f'''
                <h4 style="color: #1f77b4;">{titulo}</h4>
            ''', unsafe_allow_html=True)

    if tipo == 'dias anteriores':
        # Filtra para exibir dias anteriores do mês corrente - para comparação projeção/real
        df_projecao_faturamento_mes_corrente = df_dias_futuros_mes[
            (df_dias_futuros_mes['Data Evento'] >= datas['inicio_mes_atual']) &
            (df_dias_futuros_mes['Data Evento'] < datas['today']) &
            (df_dias_futuros_mes['Categoria'] != 'Serviço')
        ]

        # Colunas a serem exibidas
        df_projecao_faturamento_mes_corrente = df_projecao_faturamento_mes_corrente[['Categoria', 'Data Evento', 'Dia Semana', 'Faturamento Projetado', 'Valor Bruto', 'Desconto', 'Valor Liquido']]
        df_projecao_faturamento_mes_corrente = df_projecao_faturamento_mes_corrente.sort_values(by=['Categoria', 'Data Evento'])
        df_projecao_faturamento_mes_corrente = df_projecao_faturamento_mes_corrente.rename(columns={'Valor Bruto':'Faturamento Real', 'Valor Liquido':'Faturamento Liquido'})
        num_columns_dataframe = ['Faturamento Projetado', 'Faturamento Real', 'Desconto', 'Faturamento Liquido']

        st.markdown(f'''
            <h4>{titulo} - {datas['inicio_mes_atual'].strftime('%d/%m/%y')} a {datas['today'].strftime('%d/%m/%y')}</h4>
            <h5>Comparação: Faturamento Projetado e Faturamento Real</h5>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_mes_corrente.empty:
        st.info('Não há dados de faturamento para essa categoria.')
    
    else: 
        df_projecao_faturamento_mes_corrente_exibe = function_format_number_columns(df_projecao_faturamento_mes_corrente, columns_money=num_columns_dataframe)
        dataframe_aggrid(
            df=df_projecao_faturamento_mes_corrente_exibe,
            name=f"Projeção - {titulo}",
            date_columns=['Data Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    
    st.divider()


# Exibe projeção de Eventos - mês corrente
def exibe_faturamento_eventos(df_faturamento_eventos, id_casa, datas):
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Eventos</h4>
            <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>        
        ''', unsafe_allow_html=True)

    df_faturamento_eventos_futuros = df_faturamento_eventos[
        (df_faturamento_eventos['ID_Casa'] == id_casa) &
        (df_faturamento_eventos['Data Evento'] >= datas['today']) &
        (df_faturamento_eventos['Data Evento'] <= datas['fim_mes_atual']) 
    ]

    df_faturamento_eventos_futuros = df_faturamento_eventos_futuros[['Categoria', 'Data Evento', 'Valor Bruto', 'Desconto', 'Valor Liquido']]
   
    if not df_faturamento_eventos_futuros.empty:
        df_faturamento_eventos_futuros_exibe = function_format_number_columns(df_faturamento_eventos_futuros, columns_money=['Valor Bruto', 'Desconto', 'Valor Liquido'])
        dataframe_aggrid(
            df=df_faturamento_eventos_futuros_exibe,
            name=f"Projeção - Faturamento Eventos",
            date_columns=['Data Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    else:
        st.info(f"Não há informações de eventos para os próximos dias de {datas['nome_mes_atual_pt']}.")
    st.divider()


# Exibe projeção de Outras Receitas - mês corrente
def exibe_faturamento_outras_receitas(df_parc_receit_extr_dia, df_parc_receitas_extr, id_casa, datas):
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Outras Receitas</h4>
            <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>
        ''', unsafe_allow_html=True)

    # Filtra por casa e dias futuros
    df_parc_receitas_extr_futuras = df_parc_receit_extr_dia[
        (df_parc_receit_extr_dia['ID_Casa'] == id_casa) &
        (df_parc_receit_extr_dia['Data Evento'] >= datas['today']) &
        (df_parc_receit_extr_dia['Data Evento'] <= datas['fim_mes_atual']) 
    ]

    if not df_parc_receitas_extr_futuras.empty:
        # Merge para exibir categorias específicas no expander
        df_detalha_outras_receitas = df_parc_receitas_extr_futuras.merge(
            df_parc_receitas_extr,
            how='left',
            left_on=['Casa', 'Data Evento'],
            right_on=['Casa', 'Data Evento']
        )

        df_detalha_outras_receitas = df_detalha_outras_receitas[['Categoria_x', 'Data Evento', 'Categoria_y', 'Valor Bruto_y']]
        df_detalha_outras_receitas = df_detalha_outras_receitas.rename(columns={'Categoria_y':'Classificacao Receita', 'Categoria_x':'Categoria', 'Valor Bruto_y':'Valor Parcela'})

        # Exibe df de 'Outras Receitas'
        df_parc_receitas_extr_futuras = df_parc_receitas_extr_futuras[['Categoria', 'Data Evento', 'Valor Bruto', 'Desconto', 'Valor Liquido']]
        
        df_parc_receitas_extr_futuras_exibe = function_format_number_columns(df_parc_receitas_extr_futuras, columns_money=['Valor Bruto', 'Desconto', 'Valor Liquido'])
        dataframe_aggrid(
            df=df_parc_receitas_extr_futuras_exibe,
            name=f"Projeção - Faturamento Outras Receitas",
            date_columns=['Data Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )

        with st.expander('Detalhamento', icon=":material/chevron_right:"):
            df_detalha_outras_receitas_fmt = formata_df(df_detalha_outras_receitas)
            st.dataframe(df_detalha_outras_receitas_fmt, hide_index=True)
        
    else:
        st.info(f"Não há informações de receitas extraordinárias para os próximos dias de {datas['nome_mes_atual_pt']}.")

############################################ PROJEÇÕES PRÓXIMOS MESES ############################################

# Une faturamentos e orçamentos mensais para calcular histórico de atingimento (%)
def prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, ano_passado, ano_atual):
    # Filtra por casa e período (ano passado e atual)
    df_orcamentos_casa = df_orcamentos[
        (df_orcamentos['ID_Casa'] == id_casa) &
        (df_orcamentos['Ano'] >= ano_passado) &
        (df_orcamentos['Ano'] <= ano_atual) &
        (df_orcamentos['Categoria'] != 'Eventos Rebate Fornecedores')
    ]
    
    df_faturamento_mes_casa = df_faturamento_agregado_mes[
        (df_faturamento_agregado_mes['ID_Casa'] == id_casa) &
        (df_faturamento_agregado_mes['Ano'] >= ano_passado) &
        (df_faturamento_agregado_mes['Ano'] <= ano_atual)
    ]
    
    df_faturamento_mes_casa = df_faturamento_mes_casa.groupby(['ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mês'], as_index=False)[['Valor Bruto', 'Desconto', 'Valor Liquido']].sum()

    # Merge para calcular faturamento/orçamento
    df_faturamento_orcamento = pd.merge(
        df_faturamento_mes_casa[['Categoria', 'Ano', 'Mês', 'Valor Bruto']],
        df_orcamentos_casa[['Categoria', 'Ano', 'Mês', 'Orçamento']],
        how='right',
        on=['Mês', 'Ano', 'Categoria']
    )
    
    # Calcula Faturamento / Orçamento
    df_faturamento_orcamento['Atingimento Real'] = (
        (df_faturamento_orcamento['Valor Bruto'].astype(float) /
        df_faturamento_orcamento['Orçamento'].replace(0, np.nan).astype(float)) * 100
    )

    return df_faturamento_mes_casa, df_faturamento_orcamento


# --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x MESES (ano corrente) ---
def lista_meses_ano(df_faturamento_agregado, ano_atual, ano_passado):
    lista_meses_ano_anterior = list(range(1, 13))
    df_meses_ano_anterior = pd.DataFrame({'Meses_Ano':lista_meses_ano_anterior, 'Ano': ano_passado})

    lista_meses_ano_atual = list(range(1, 13))
    df_meses_ano_atual = pd.DataFrame({'Meses_Ano':lista_meses_ano_atual, 'Ano': ano_atual})

    # Concatena ano anterior e atual
    df_meses_anos = pd.concat([df_meses_ano_anterior, df_meses_ano_atual])

    # Agora faz o cross com categorias 
    categorias = df_faturamento_agregado['Categoria'].dropna().unique()
    df_categorias = pd.DataFrame({'Categoria': categorias})
    df_meses_futuros_com_categorias = df_meses_anos.merge(df_categorias, how='cross')

    df_meses_futuros_com_categorias['Data'] = pd.to_datetime({
        'year': df_meses_futuros_com_categorias['Ano'],
        'month': df_meses_futuros_com_categorias['Meses_Ano'],
        'day': 1
    })
    
    return df_meses_futuros_com_categorias


# Função para cálculo da projeção - meses seguintes
def projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, ano_atual, mes_atual):
    # Merge com df que contém todos os meses (ano anterior e corrente)
    df_meses_seguintes = df_faturamento_orcamento.merge(
        df_meses_futuros_com_categorias, 
        how='right', 
        left_on=['Ano', 'Mês', 'Categoria'],
        right_on=['Ano', 'Meses_Ano', 'Categoria']
    )
   
    df_meses_seguintes['Projeção Atingimento'] = None
    df_meses_seguintes['Valor Projetado'] = None
    
    # Loop por categoria
    for categoria in df_meses_seguintes['Categoria'].unique():
        df_cat = None
        df_cat = df_meses_seguintes[df_meses_seguintes['Categoria'] == categoria]
        
        if df_cat is not None and not df_cat.empty:
            for i, row in df_cat.iterrows():
                # data = row['Data']
                ano = row['Ano']

                # if ano >= ano_atual:  # apenas meses do ano atual
                mes = row['Data']

                # pega histórico dos dois meses atrás
                dois_meses_atras = mes - pd.DateOffset(months=2)

                historico = df_meses_seguintes[
                    (df_meses_seguintes['Categoria'] == categoria) &
                    (df_meses_seguintes['Data'] >= dois_meses_atras) &
                    (df_meses_seguintes['Data'] < mes)
                ].copy()

                # Define colunas auxiliares conforme o mês
                historico["Atingimento_Usado"] = np.where(
                    (historico["Mês"] >= mes_atual) & (historico['Ano'] == ano_atual),
                    historico["Projeção Atingimento"],       # usa o projetado se mês >= atual
                    historico["Atingimento Real"]            # senão usa o real
                )
                
                # historico["Faturamento_Usado"] = np.where(
                #     historico["Mês"] >= mes_atual,
                #     historico["Valor Projetado"],          # usa o projetado se mês >= atual
                #     historico["Valor Bruto"]               # senão usa o real
                # )

                # usa o Atingimento (real) quando existir, senão a Projecao (que pode vir de meses anteriores)
                valores_para_media = historico['Atingimento_Usado'].fillna(historico['Projeção Atingimento']).astype(float)

                if not valores_para_media.empty:
                    media = valores_para_media.mean()
                    df_meses_seguintes.at[i, 'Projeção Atingimento'] = media

    # Define valor de faturamento projetado baseado na projeção (%) de atingimento do orçamento
    df_meses_seguintes['Valor Projetado'] = (
        df_meses_seguintes['Orçamento'].astype(float) * (df_meses_seguintes['Projeção Atingimento'].astype(float) / 100)
    )
    return df_meses_seguintes


# Função para exibição da projeção por categoria - mês corrente
def exibe_categoria_faturamento_prox_meses(categoria, df_meses_futuros, ano_atual, mes_atual):
    df_meses_futuros['Valor Bruto'] = df_meses_futuros['Valor Bruto'].fillna(0)
    df_meses_futuros['Atingimento Real'] = df_meses_futuros['Atingimento Real'].fillna(0)
    df_meses_futuros['Projeção Atingimento'] = df_meses_futuros['Projeção Atingimento'].fillna(0)
    df_meses_futuros['Valor Projetado'] = df_meses_futuros['Valor Projetado'].fillna(0)
    
    titulo = categoria

    if categoria == 'A&B':
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            ((df_meses_futuros['Categoria'] == 'Alimentos') | (df_meses_futuros['Categoria'] == 'Bebidas')) & 
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mês'] >= mes_atual)
        ]

    elif categoria == 'Eventos':
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            (df_meses_futuros['Categoria'].isin(['Eventos A&B', 'Eventos Locações', 'Eventos Couvert'])) & 
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mês'] >= mes_atual)
        ]
        
    else:
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            (df_meses_futuros['Categoria'] == categoria) &
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mês'] >= mes_atual)
        ]

        if categoria == 'Couvert':
            titulo = 'Artístico (Couvert)'


    df_projecao_faturamento_categoria_prox_meses = df_projecao_faturamento_categoria_prox_meses[['Categoria', 'Ano', 'Mês', 'Orçamento', 'Projeção Atingimento', 'Valor Projetado']]
    
    # Exibe titulo
    st.markdown(f'''
            <h4 style="color: #1f77b4;">{titulo}</h4>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_categoria_prox_meses.empty:
        st.info('Não há dados de faturamento para essa categoria.')

    else: # Exibe df com aggrid
        df_projecao_faturamento_categoria_prox_meses_exibe = function_format_number_columns(df_projecao_faturamento_categoria_prox_meses, columns_money=['Orçamento', 'Valor Projetado'], columns_percent=['Projeção Atingimento'])
        dataframe_aggrid(
            df=df_projecao_faturamento_categoria_prox_meses_exibe,
            name=f"Projeção próximos meses - {titulo}",
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    
    if titulo != 'Outras Receitas':
        st.divider()


# Exibe meses anteriores - para comparação projeção/real
def exibe_faturamento_meses_anteriores(df_faturamento_meses_futuros, ano_atual, mes_atual):
    if mes_atual == 1:   
        df_faturamento_meses_anteriores = df_faturamento_meses_futuros[
            (df_faturamento_meses_futuros['Ano'] == ano_atual - 1) &
            (df_faturamento_meses_futuros['Categoria'] != 'Serviço')
        ]
        ano_exibido = ano_atual - 1
    else:
        df_faturamento_meses_anteriores = df_faturamento_meses_futuros[
        (df_faturamento_meses_futuros['Ano'] == ano_atual) &
        (df_faturamento_meses_futuros['Mês'] < mes_atual) &
        (df_faturamento_meses_futuros['Categoria'] != 'Serviço')
    ]
        ano_exibido = ano_atual

    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores[['Categoria', 'Mês', 'Orçamento', 'Valor Bruto', 'Atingimento Real', 'Projeção Atingimento', 'Valor Projetado']]
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.rename(columns={'Valor Projetado':'Faturamento Projetado'})
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.sort_values(by=['Categoria', 'Mês'])

    st.markdown(f'''
            <h4>Meses anteriores - {ano_exibido}</h4>
            <h5>Comparação Faturamento: Atingimento Projetado e Atingimento Real</h5>
        ''', unsafe_allow_html=True)

    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.rename(columns={'Valor Bruto':'Faturamento Real'})
    df_faturamento_meses_anteriores_exibe = function_format_number_columns(df_faturamento_meses_anteriores, columns_money=['Orçamento', 'Faturamento Real', 'Faturamento Projetado'], columns_percent=['Atingimento Real', 'Projeção Atingimento'])
    dataframe_aggrid(
        df=df_faturamento_meses_anteriores_exibe,
        name=f"Projeção - Faturamento Meses Anteriores",
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True,
    )
    
############################################ PROJEÇÃO CMV - PRÓXIMOS MESES ############################################

# Soma faturamento de Alimentos, Bebidas e Delivery por casa e mês
def config_faturamento_bruto_zig(df, data_inicio, data_fim, casa):
    df['Valor Bruto'] = df['Valor Bruto'].astype(float)
    df['Data Evento'] = pd.to_datetime(df['Data Evento'], errors='coerce')
    df['Mes_Ano'] = df['Data Evento'].dt.strftime('%Y-%m')
    df = df[
        df['Categoria'].isin(['Alimentos', 'Bebidas', 'Delivery']) &
        (df['Casa'] == casa) &
        (df['Data Evento'] >= data_inicio) &
        (df['Data Evento'] <= data_fim)
    ]

    df = df.groupby(['ID_Casa', 'Casa', 'Mes_Ano', 'Categoria']).agg({
        'Valor Bruto': 'sum',
        'Desconto': 'sum',
        'Valor Liquido': 'sum',
        'Data Evento': 'first'
    }).reset_index()

    faturamento_bruto_alimentos = df[(df['Categoria'] == 'Alimentos')]['Valor Bruto'].sum()
    faturamento_bruto_bebidas = df[(df['Categoria'] == 'Bebidas')]['Valor Bruto'].sum()
    faturamento_delivery = df[(df['Categoria'] == 'Delivery')]['Valor Bruto'].sum()

    return df, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery


def config_compras(data_inicio, data_fim, loja):
    df1 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO()  
    df1 = df1.rename(columns={'Loja':'Casa'})
    df1['Primeiro_Dia_Mes'] = pd.to_datetime(df1['Primeiro_Dia_Mes'], errors='coerce')
    df1['Mes_Ano'] = df1['Primeiro_Dia_Mes'].dt.strftime('%Y-%m')
    
    # df2 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO()
    df2 = GET_AUT_BLUE_ME_COM_PEDIDO()
    df_aut_blue_me_com_pedido = df2.copy()
    df2['Data_Emissao'] = pd.to_datetime(df2['Data_Emissao'], errors='coerce')
    df2['Mes_Ano'] = df2['Data_Emissao'].dt.strftime('%Y-%m')
    df2 = df2.groupby(['Casa', 'Mes_Ano'], as_index=False)[['Valor_Liquido', 'Valor_Cotacao', 'Valor_Liq_Alimentos', 'Valor_Liq_Bebidas', 'Valor_Liq_Descart_Hig_Limp', 'Valor_Gelo_Gas_Carvao_Velas', 'Valor_Utensilios', 'Valor_Liq_Outros']].sum()
    
    df_compras = pd.merge(df2, df1, on=['Casa', 'Mes_Ano'], how='outer')
    df_compras['Primeiro_Dia_Mes'] = pd.to_datetime(df_compras['Primeiro_Dia_Mes'], errors='coerce')
    # df_compras['Mes_Ano'] = df_compras['Primeiro_Dia_Mes'].dt.strftime('%Y-%m')
    
    df_compras = df_compras[
        (df_compras['Casa'] == loja) &
        (df_compras['Primeiro_Dia_Mes'] >= data_inicio) &
        (df_compras['Primeiro_Dia_Mes'] <= data_fim)
    ]
    
    df_compras = df_compras.groupby(['Casa', 'Mes_Ano']).agg(
        {'BlueMe_Sem_Pedido_Alimentos': 'sum', 
        'BlueMe_Sem_Pedido_Bebidas': 'sum', 
        'Valor_Liq_Alimentos': 'sum', 
        'Valor_Liq_Bebidas': 'sum'}).reset_index()

    Compras_Alimentos = df_compras['BlueMe_Sem_Pedido_Alimentos'].sum() + df_compras['Valor_Liq_Alimentos'].sum()
    Compras_Bebidas = df_compras['BlueMe_Sem_Pedido_Bebidas'].sum() + df_compras['Valor_Liq_Bebidas'].sum()

    Compras_Alimentos = float(Compras_Alimentos)
    Compras_Bebidas = float(Compras_Bebidas)

    df_compras['Compras Alimentos'] = df_compras['Valor_Liq_Alimentos'] + df_compras['BlueMe_Sem_Pedido_Alimentos']
    df_compras['Compras Bebidas'] = df_compras['Valor_Liq_Bebidas'] + df_compras['BlueMe_Sem_Pedido_Bebidas']
    df_compras = df_compras.rename(columns={'Valor_Liq_Alimentos': 'BlueMe c/ Pedido Alim.', 'Valor_Liq_Bebidas': 'BlueMe c/ Pedido Bebidas', 'BlueMe_Sem_Pedido_Alimentos': 'BlueMe s/ Pedido Alim.', 'BlueMe_Sem_Pedido_Bebidas': 'BlueMe s/ Pedido Bebidas'})

    df_compras = df_compras[['Casa', 'Mes_Ano', 'BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']]
    
    return df_compras, df_aut_blue_me_com_pedido, Compras_Alimentos, Compras_Bebidas


def processar_transferencias(df, casa_col, loja, data_inicio, data_fim):
    # Filtrar pelo nome da loja e pelo intervalo de datas
    df['Data_Transferencia'] = pd.to_datetime(df['Data_Transferencia'], errors='coerce')
    df['Mes_Ano'] = df['Data_Transferencia'].dt.strftime('%Y-%m')
    df = df[
        (df[casa_col] == loja) &
        (df['Data_Transferencia'] >= data_inicio) &
        (df['Data_Transferencia'] <= data_fim)
    ]
    
    # Agrupar por casa e categoria, somando os valores
    df_grouped = df.groupby([casa_col, 'Categoria', 'Mes_Ano']).agg({
        'Valor_Transferencia': 'sum'
    }).reset_index()
    
    # Ajustar categoria para formato capitalizado
    df_grouped['Categoria'] = df_grouped['Categoria'].str.capitalize()
    
    # Pivotar para transformar categorias em colunas
    df_pivot = df_grouped.pivot_table(
        index=[casa_col, 'Mes_Ano'],
        columns='Categoria',
        values='Valor_Transferencia',
        fill_value=0
    ).reset_index()
    
    # Renomear colunas para refletir o tipo de operação
    operacao = 'Entrada' if casa_col == 'Casa_Entrada' else 'Saída'
    df_pivot.columns = [
        'Loja' if col == casa_col else col if col == 'Mes_Ano' else f'{operacao} {col}'
        for col in df_pivot.columns
    ]    
    return df_pivot

def config_transferencias_gastos(data_inicio, data_fim, loja):
    df_transf_estoque = GET_TRANSF_ESTOQUE()
    df_entradas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Entrada', loja, data_inicio, data_fim)
    df_saidas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Saida', loja, data_inicio, data_fim)
    
    df_perdas_e_consumo = GET_PERDAS_E_CONSUMO_AGRUPADOS()
    df_perdas_e_consumo['Primeiro_Dia_Mes'] = pd.to_datetime(df_perdas_e_consumo['Primeiro_Dia_Mes'], errors='coerce')
    df_perdas_e_consumo['Mes_Ano'] = df_perdas_e_consumo['Primeiro_Dia_Mes'].dt.strftime('%Y-%m')
    df_perdas_e_consumo = df_perdas_e_consumo[
        (df_perdas_e_consumo['Loja'] == loja) &
        (df_perdas_e_consumo['Primeiro_Dia_Mes'] >= data_inicio) &
        (df_perdas_e_consumo['Primeiro_Dia_Mes'] <= data_fim)
    ]
    df_perdas_e_consumo.fillna(0, inplace=True)

    df_transf_e_gastos = pd.merge(df_entradas_pivot, df_saidas_pivot, on=['Loja', 'Mes_Ano'], how='outer')
    df_transf_e_gastos = pd.merge(df_transf_e_gastos, df_perdas_e_consumo, on=['Loja', 'Mes_Ano'], how='outer')
    df_transf_e_gastos = df_transf_e_gastos.rename(columns={
        'ID_Loja': 'ID_Casa',
        'Loja': 'Casa',
        'Consumo_Interno': 'Consumo Interno',
        'Quebras_e_Perdas': 'Quebras e Perdas'
    })
    cols = ['ID_Casa', 'Casa', 'Mes_Ano', 'Entrada Alimentos', 'Entrada Bebidas', 'Saída Alimentos', 'Saída Bebidas', 'Consumo Interno', 'Quebras e Perdas']
    for col in cols:
        if col not in df_transf_e_gastos.columns:
            df_transf_e_gastos[col] = 0

    df_transf_e_gastos = df_transf_e_gastos[cols]

    # Conversão para float para evitar erros de tipo
    saida_alimentos = float(df_saidas_pivot['Saída Alimentos'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Alimentos' in df_saidas_pivot.columns else 0.0
    saida_bebidas = float(df_saidas_pivot['Saída Bebidas'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Bebidas' in df_saidas_pivot.columns else 0.0
    entrada_alimentos = float(df_entradas_pivot['Entrada Alimentos'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Alimentos' in df_entradas_pivot.columns else 0.0
    entrada_bebidas = float(df_entradas_pivot['Entrada Bebidas'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Bebidas' in df_entradas_pivot.columns else 0.0
    consumo_interno = float(df_transf_e_gastos['Consumo Interno'].iloc[0]) if not df_perdas_e_consumo.empty and 'Consumo Interno' in df_transf_e_gastos.columns else 0.0
    quebras_e_perdas = float(df_transf_e_gastos['Quebras e Perdas'].iloc[0]) if not df_perdas_e_consumo.empty and 'Quebras e Perdas' in df_transf_e_gastos.columns else 0.0

    return df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas


def config_valoracao_estoque_ou_producao(tipo, data_inicio, data_fim, loja):
    # Pega os dados
    if tipo == 'estoque':
        df_valoracao = GET_VALORACAO_ESTOQUE(data_inicio, data_fim)
        col_data = 'DATA_CONTAGEM'
        col_valor = 'Valor_em_Estoque'
    if tipo == 'producao':
        df_valoracao = GET_VALORACAO_PRODUCAO(data_inicio, data_fim)
        col_data = 'Data_Contagem'
        col_valor = 'Valor_Total'
    
    df_valoracao = df_valoracao[
       (df_valoracao['Loja'] == loja) &
       (df_valoracao['Categoria'].isin(['ALIMENTOS', 'BEBIDAS']))
    ]
    
    # Agrupar por mês, loja e categoria
    df_valoracao = (
        df_valoracao
        .groupby(['Loja', 'Categoria', col_data], as_index=False)
        .agg({col_valor: 'sum'})
    )
    
    # Criar todas as datas do período
    todas_datas = pd.date_range(start=data_inicio, end=data_fim, freq='MS')
    
    # Todas combinações de Loja, Categoria e DATA_CONTAGEM
    lojas_categorias = df_valoracao[['Loja', 'Categoria']].drop_duplicates()
    todas_combinacoes = (
        lojas_categorias
        .merge(pd.DataFrame({col_data: todas_datas}), how='cross')
    )
    
    df_valoracao[col_data] = pd.to_datetime(df_valoracao[col_data], errors='coerce')

    # Merge com o dataframe real
    df_valoracao = todas_combinacoes.merge(
        df_valoracao,
        on=['Loja', 'Categoria', col_data],
        how='left'
    )
    
    # Preencher valores ausentes com 0
    df_valoracao[col_valor] = df_valoracao[col_valor].fillna(0)
    
    # Calcular variação mensal
    df_valoracao['Variação_Mensal'] = (
        df_valoracao
        .groupby(['Loja', 'Categoria'])[col_valor]
        .diff()
        .fillna(0)
    )
    
    # Coluna DATA_MES_ANTERIOR
    df_valoracao['DATA_MES_ANTERIOR'] = df_valoracao[col_data] - pd.DateOffset(months=1)
    df_valoracao['Mes_Ano'] = df_valoracao['DATA_MES_ANTERIOR'].dt.strftime("%Y-%m")
    df_valoracao = df_valoracao.rename(columns={'Loja': 'Casa'})

    return df_valoracao


def config_faturamento_eventos(data_inicio, data_fim, loja, faturamento_bruto_alimentos, faturamento_bruto_bebidas):
    df_eventos = GET_EVENTOS_CMV(data_inicio=data_inicio, data_fim=data_fim)
    
    df_eventos = df_eventos[df_eventos['Loja'] == loja]
    df_eventos['Valor_AB'] = df_eventos['Valor_AB'].astype(float)
    df_eventos['Data'] = pd.to_datetime(df_eventos['Data'], errors='coerce')
    df_eventos['Mes_Ano'] = df_eventos['Data'].dt.strftime('%Y-%m')
    df_eventos = df_eventos.rename(columns={'ID_Loja': 'ID_Casa', 'Loja': 'Casa'})

    return df_eventos


def merge_e_calculo_para_cmv(df_faturamento_zig, df_compras, df_valoracao_estoque, df_transf_e_gastos, df_valoracao_producao, df_faturamento_eventos):
    # Faturamento Bruto (alimentos + bebidas + delivery) mensal
    df_faturamento_zig_geral = df_faturamento_zig.copy()
    df_faturamento_zig_geral = df_faturamento_zig_geral.groupby(['ID_Casa', 'Casa', 'Mes_Ano'], as_index=False)['Valor Bruto'].sum()
    df_faturamento_zig_geral = df_faturamento_zig_geral.rename(columns={'Valor Bruto':'Faturamento Bruto'})

    # Compras (alimentos + bebidas) mensais
    df_compras_geral = df_compras.copy()
    df_compras_geral['Compras Geral'] = df_compras_geral['Compras Alimentos'] + df_compras_geral['Compras Bebidas']
    df_compras_geral = df_compras_geral[['Casa', 'Mes_Ano', 'Compras Geral']]

    # Valoração estoque (alimentos + bebidas) mensal
    df_valoracao_estoque_geral = df_valoracao_estoque.copy()
    df_valoracao_estoque_geral = df_valoracao_estoque_geral.groupby(['Casa', 'Mes_Ano'], as_index=False)['Variação_Mensal'].sum()

    # Transferências e gastos (entrada alimentos + bebidas, saidas alimentos + bebidas, consumo interno, quebras e perdas)
    df_transf_e_gastos_geral = df_transf_e_gastos.copy()
    df_transf_e_gastos_geral['Entradas Geral'] = df_transf_e_gastos_geral['Entrada Alimentos'] + df_transf_e_gastos_geral['Entrada Bebidas']
    df_transf_e_gastos_geral['Saídas Geral'] = df_transf_e_gastos_geral['Saída Alimentos'] + df_transf_e_gastos_geral['Saída Bebidas']
    df_transf_e_gastos_geral = df_transf_e_gastos_geral[['ID_Casa', 'Casa', 'Mes_Ano', 'Entradas Geral', 'Saídas Geral', 'Consumo Interno', 'Quebras e Perdas']]

    # Valoração produção (alimentos + bebidas) mensal
    df_valoracao_producao_geral = df_valoracao_producao.copy()
    df_valoracao_producao_geral = df_valoracao_producao_geral.groupby(['Casa', 'Mes_Ano'], as_index=False)['Variação_Mensal'].sum()

    # Faturamento eventos (A&B) mensal
    df_faturamento_eventos_geral = df_faturamento_eventos.copy()
    df_faturamento_eventos_geral = df_faturamento_eventos_geral.groupby(['ID_Casa', 'Casa', 'Mes_Ano'], as_index=False)['Valor_AB'].sum()

    # Merge passo a passo para cálculo do cmv
    df_cmv = (
        df_compras_geral
            .merge(df_valoracao_estoque_geral, on=['Casa', 'Mes_Ano'], how='left')
            .merge(df_transf_e_gastos_geral, on=['Casa', 'Mes_Ano'], how='left')
            .merge(df_valoracao_producao_geral, on=['Casa', 'Mes_Ano'], how='left')
    ).fillna(0)
    df_cmv = df_cmv.rename(columns={'Variação_Mensal_x':'Variacao_Estoque', 'Variação_Mensal_y':'Variacao_Producao'})
    
    # Fauramento geral (bruto + eventos)
    df_merge_faturamento = df_faturamento_zig_geral.merge(
        df_faturamento_eventos_geral,
        on=['Casa', 'Mes_Ano'],
        how='left'
    ).fillna(0)
    df_merge_faturamento['Faturamento_Geral'] = df_merge_faturamento['Faturamento Bruto'] + df_merge_faturamento['Valor_AB']
    
    df_merge_cmv = pd.merge(
        df_cmv[['Casa', 'Mes_Ano', 'Compras Geral', 'Variacao_Estoque', 'Entradas Geral', 'Saídas Geral', 'Consumo Interno', 'Quebras e Perdas', 'Variacao_Producao']],
        df_merge_faturamento[['Casa', 'Mes_Ano', 'Faturamento_Geral']],
        on=['Casa', 'Mes_Ano'],
        how='left'
    )

    # Cálculo do cmv e porcentagem cmv
    df_calculo_cmv = df_merge_cmv.copy()
    df_calculo_cmv['Compras Geral'] = df_calculo_cmv['Compras Geral'].astype(float)
    df_calculo_cmv['Variacao_Estoque'] = df_calculo_cmv['Variacao_Estoque'].astype(float)
    df_calculo_cmv['Entradas Geral'] = df_calculo_cmv['Entradas Geral'].astype(float)
    df_calculo_cmv['Saídas Geral'] = df_calculo_cmv['Saídas Geral'].astype(float)
    df_calculo_cmv['Consumo Interno'] = df_calculo_cmv['Consumo Interno'].astype(float)
    df_calculo_cmv['Variacao_Producao'] = df_calculo_cmv['Variacao_Producao'].astype(float)
    # st.write(df_calculo_cmv) Para verificar valores que não batem com a planilha

    df_calculo_cmv['CMV Real'] = df_calculo_cmv['Compras Geral'] - df_calculo_cmv['Variacao_Estoque'] + df_calculo_cmv['Entradas Geral'] - df_calculo_cmv['Saídas Geral'] - df_calculo_cmv['Consumo Interno'] - df_calculo_cmv['Variacao_Producao']
    df_calculo_cmv['CMV Real Percentual'] = (df_calculo_cmv['CMV Real'] / df_calculo_cmv['Faturamento_Geral']) * 100
    df_calculo_cmv = df_calculo_cmv[['Casa', 'Mes_Ano', 'Faturamento_Geral', 'CMV Real', 'CMV Real Percentual']]

    return df_calculo_cmv


# Utiliza o df de faturamento projetado criado anteriormente (para projetar o cmv para os prox meses)
def calcula_cmv_proximos_meses(df_faturamento_meses_futuros, df_calculo_cmv, ano_atual, mes_atual):
    df_resgata_faturamento_meses_futuros = df_faturamento_meses_futuros[
        (df_faturamento_meses_futuros['Ano'] >= ano_atual - 1) &
        (df_faturamento_meses_futuros['Categoria'].isin(['Alimentos', 'Bebidas', 'Delivery', 'Eventos A&B']))
    ]
    
    # Resgata faturamentos projetados por mês
    df_resgata_faturamento_meses_futuros = df_resgata_faturamento_meses_futuros.groupby(['Ano', 'Mês'], as_index=False)[['Valor Bruto', 'Valor Projetado']].sum()
    df_resgata_faturamento_meses_futuros['Mês'] = df_resgata_faturamento_meses_futuros['Mês'].astype(int)
    df_resgata_faturamento_meses_futuros['Mes_Ano'] = (df_resgata_faturamento_meses_futuros['Ano'].astype(int).astype(str) + '-' + df_resgata_faturamento_meses_futuros['Mês'].astype(int).astype(str).str.zfill(2))    
    df_merge_meses_anteriores_seguintes = pd.merge(
        df_calculo_cmv,
        df_resgata_faturamento_meses_futuros[['Ano', 'Mês', 'Mes_Ano', 'Valor Projetado']],
        on='Mes_Ano',
        how='right'
    )
    df_merge_meses_anteriores_seguintes['Data'] = pd.to_datetime(df_merge_meses_anteriores_seguintes['Mes_Ano'], format='%Y-%m')
    
    # Cria coluna para CMV projetado de cada mês
    df_merge_meses_anteriores_seguintes['CMV Percentual Projetado'] = None
    df_merge_meses_anteriores_seguintes['CMV Projetado'] = None
    
    for mes_ano in df_merge_meses_anteriores_seguintes['Mes_Ano'].unique():
        df_mes_ano = df_merge_meses_anteriores_seguintes[df_merge_meses_anteriores_seguintes['Mes_Ano'] == mes_ano]
        data = df_mes_ano['Data'].iloc[0]

        # pega histórico dos dois meses atrás
        dois_meses_atras = data - pd.DateOffset(months=2)
        
        historico = df_merge_meses_anteriores_seguintes[
            (df_merge_meses_anteriores_seguintes['Data'] >= dois_meses_atras) &
            (df_merge_meses_anteriores_seguintes['Data'] < data)
        ].copy()
        
        # Faz Projecao = (CMV1 + CMV2) / (Faturamento_Geral1 + Faturamento_Geral2)
        # Define colunas auxiliares conforme o mês
        historico["CMV_Usado"] = np.where(
            (historico["Mês"] >= mes_atual) & (historico['Ano'] == ano_atual),
            historico["CMV Projetado"],       # usa o projetado se mês >= atual
            historico["CMV Real"]                  # senão usa o real
        )

        historico["Faturamento_Usado"] = np.where(
           (historico["Mês"] >= mes_atual) & (historico['Ano'] == ano_atual),
            historico["Valor Projetado"],          # usa o projetado se mês >= atual
            historico["Faturamento_Geral"]         # senão usa o real
        )
        
        valores_para_soma_cmvs = historico['CMV_Usado'].fillna(historico['CMV Projetado']).astype(float)
        valores_para_soma_faturamento = historico['Faturamento_Usado'].fillna(historico['Valor Projetado']).astype(float)

        soma_cmvs = valores_para_soma_cmvs.sum()
        soma_faturamentos = valores_para_soma_faturamento.sum()
        
        if soma_faturamentos and not pd.isna(soma_faturamentos) and soma_faturamentos != 0:
            cmv_projetado = (soma_cmvs / soma_faturamentos) * 100
        else:
            cmv_projetado = 0 

        # Atribui o valor à coluna correta
        df_merge_meses_anteriores_seguintes.loc[
            df_merge_meses_anteriores_seguintes['Mes_Ano'] == mes_ano, 
            'CMV Percentual Projetado'
        ] = cmv_projetado

        # Define valor de CMV Projetado em Reais
        df_merge_meses_anteriores_seguintes['CMV Projetado'] = (df_merge_meses_anteriores_seguintes['CMV Percentual Projetado'] / 100) * df_merge_meses_anteriores_seguintes['Valor Projetado']

    return df_merge_meses_anteriores_seguintes


def exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, tipo, mes_atual, ano_atual):
    df_cmv = df_cmv_meses_anteriores_seguintes.copy()
    df_cmv = df_cmv.fillna(0)
    df_cmv = df_cmv.rename(columns={
        'Valor Projetado':'Faturamento AB Projetado',
        'Faturamento_Geral':'Faturamento AB Real',
    })

    if tipo == 'meses seguintes':
        df_cmv = df_cmv[(df_cmv['Mês'] >= mes_atual) & (df_cmv['Ano'] == ano_atual)]
        colunas = ['Mês', 'Ano', 'Faturamento AB Projetado', 'CMV Percentual Projetado', 'CMV Projetado']
        colunas_num_dataframe = ['Faturamento AB Projetado', 'CMV Projetado']
        colunas_percent_dataframe = ['CMV Percentual Projetado']

    if tipo == 'meses anteriores':
        if mes_atual == 1:
            df_cmv = df_cmv[df_cmv['Ano'] == ano_atual - 1]
        else:
            df_cmv = df_cmv[(df_cmv['Mês'] < mes_atual) & (df_cmv['Ano'] == ano_atual)]
        colunas = ['Mês', 'Ano', 'Faturamento AB Real', 'CMV Real', 'CMV Real Percentual', 'Faturamento AB Projetado', 'CMV Percentual Projetado', 'CMV Projetado']
        colunas_num_dataframe = ['Faturamento AB Real', 'CMV Real', 'Faturamento AB Projetado', 'CMV Projetado']
        colunas_percent_dataframe = ['CMV Real Percentual', 'CMV Percentual Projetado']

    df_cmv = df_cmv[colunas]

    st.markdown(f'''
            <h4 style="color: #1f77b4;">Custo Mercadoria Vendida (CMV)</h4>
        ''', unsafe_allow_html=True)
    
    df_cmv_exibe = function_format_number_columns(df_cmv, columns_money=colunas_num_dataframe, columns_percent=colunas_percent_dataframe)
    dataframe_aggrid(
        df=df_cmv_exibe,
        name=f"Projeção CMV - {tipo}",
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True   
    )
    st.divider()

############################################ PROJEÇÃO DESPESAS - PRÓXIMOS MESES ############################################
def merge_despesas_complexas(df_tabela_primaria, df_tabela_secundaria, casa, class_cont):
    df_tabela_secundaria_filtrada = df_tabela_secundaria[df_tabela_secundaria['Casa'] == casa].copy()

    if class_cont in ['Custos Artístico Geral', 'Marketing']: 
        df_tabela_secundaria_filtrada = df_tabela_secundaria_filtrada.groupby(['Casa', 'Mês', 'Ano', 'Centro de Custo'], as_index=False)['Aloca no Centro de Custo'].sum()

        df_tabela_resultante = pd.merge(
            df_tabela_primaria,
            df_tabela_secundaria_filtrada,
            left_on=['Casa', 'Mês', 'Ano', 'Classificacao_Contabil_2'],
            right_on=['Casa', 'Mês', 'Ano', 'Centro de Custo'],
            how='outer'
        )
        
        if class_cont == 'Custos Artístico Geral':
            condicao = (
                df_tabela_resultante['Centro de Custo'].isin(['Alimentação e Transporte']) &
                df_tabela_resultante['Classificacao_Contabil_2'].isna()
            )
        elif class_cont == 'Marketing':
            condicao = (
                df_tabela_resultante['Centro de Custo'].isin(['Eventos de Marketing', 'Produção Gráfica e Material Institucional']) &
                df_tabela_resultante['Classificacao_Contabil_2'].isna()
            )

        df_tabela_resultante.loc[condicao, 'Classificacao_Contabil_2'] = df_tabela_resultante['Centro de Custo']
        df_tabela_resultante['Custo Real'].fillna(0, inplace=True)
        df_tabela_resultante['Aloca no Centro de Custo'].fillna(0, inplace=True)

        condicao = df_tabela_resultante['Classificacao_Contabil_2'].isin(['Alimentação e Transporte', 'Eventos de Marketing', 'Produção Gráfica e Material Institucional'])
        df_tabela_resultante.loc[condicao, 'Custo Real'] = df_tabela_resultante['Custo Real'] + df_tabela_resultante['Aloca no Centro de Custo']
        df_tabela_resultante.drop(columns=['Centro de Custo', 'Aloca no Centro de Custo'], inplace=True)
        df_tabela_resultante.dropna(subset=['Classificacao_Contabil_2'], inplace=True)

    elif class_cont in ['Gorjeta', 'Mão de Obra - Salários']: 
        df_tabela_secundaria_filtrada = df_tabela_secundaria_filtrada.groupby(['Casa', 'Mês', 'Ano'], as_index=False)['Valor'].sum()

        df_tabela_resultante = pd.merge(
            df_tabela_primaria,
            df_tabela_secundaria_filtrada,
            on=['Casa', 'Mês', 'Ano'],
            how='left'
        ).fillna(0)

        if class_cont == 'Gorjeta':
            df_tabela_resultante['Custo Real'] = df_tabela_resultante['Custo Real'] + df_tabela_resultante['Valor']
        elif class_cont == 'Mão de Obra - Salários':
            df_tabela_resultante['Custo Real'] = df_tabela_resultante['Custo Real'] - df_tabela_resultante['Valor']
        
        df_tabela_resultante.drop(columns=['Valor'], inplace=True)
    
    return df_tabela_resultante


def prepara_dados_custos_mensais(df_custos_gerais, df_faturamento_meses_futuros, casa, class_cont, df_aut_blue_me_com_pedido=None, df_tabela_secundaria=None):
    # Filtra por class. cont. 1 e casa
    if class_cont == 'Custos de Eventos':
        df_custos_filtrado = df_custos_gerais[
            (df_custos_gerais['Casa'] == casa) &
            ((df_custos_gerais['Classificacao_Contabil_1'] == class_cont) |
            # (df_custos_gerais['Classificacao_Contabil_2'] == 'MDO Terceirizada - Eventos') | # inclui essa class. cont. 2 da class. cont. 1 de PJ
            (df_custos_gerais['Cargo_DRE'] == 'MDO Terceirizada - Eventos')) 
        ].copy()

        # Faz a renomeação por conta da filtragem por Cargo_DRE
        df_custos_filtrado['Classificacao_Contabil_2'] = df_custos_filtrado['Classificacao_Contabil_2'].replace(
            'MDO PJ Fixo',
            'MDO Terceirizada - Eventos'
        )

    elif class_cont == 'Mão de Obra - Salários':
        df_custos_filtrado = df_custos_gerais[
            (df_custos_gerais['Casa'] == casa) &
            ((df_custos_gerais['Classificacao_Contabil_1'] == class_cont) |
            (df_custos_gerais['Classificacao_Contabil_2'] == '  -  INSS Segurados') |
            (df_custos_gerais['Classificacao_Contabil_2'] == 'IRRF - MDO CLT - Salário')) 
        ].copy()

        # Faz a renomeação por conta das class. cont. 2 que foram selecionadas que não são iguais as da class.cont. 1 de salários
        df_custos_filtrado['Classificacao_Contabil_2'] = (df_custos_filtrado['Classificacao_Contabil_2'].replace({
                '  -  INSS Segurados': 'MDO CLT - Salário',
                'IRRF - MDO CLT - Salário': 'MDO CLT - Salário'
            })
        )

    elif class_cont == 'Mão de Obra - PJ':
        df_custos_filtrado = df_custos_gerais[
            (df_custos_gerais['Casa'] == casa) &
            ((df_custos_gerais['Classificacao_Contabil_1'] == class_cont) &
            # (df_custos_gerais['Classificacao_Contabil_2'] == 'MDO PJ Fixo') # desconsidera outras class. cont. 2 que não 'MDO PJ Fixo'
            (df_custos_gerais['Cargo_DRE'] != 'MDO Terceirizada - Eventos') & 
            (df_custos_gerais['Cargo_DRE'] != '  - Analista') & 
            (df_custos_gerais['Cargo_DRE'] != '  - Diretoria')) 
        ].copy()

    elif class_cont == 'Desconto sobre Venda':
        df_descontos_filtrado = df_custos_gerais[
            (df_custos_gerais['Casa'] == casa) &
            (df_custos_gerais['Descontos - DRE'].isin(['Descontos - Operação', 'Desconto - Alimentação Escritório', 'Descontos - Marketing']))
        ].copy()

        # Renomeia essa coluna para poder aplicar o código abaixo e cria coluna de data
        df_descontos_filtrado = df_descontos_filtrado.rename(columns={'Descontos - DRE': 'Classificacao_Contabil_2'})
        df_descontos_filtrado['Data_Competencia'] = pd.to_datetime(
            dict(
                year=df_descontos_filtrado['Ano'],
                month=df_descontos_filtrado['Mês'],
                day=1
            )
        )
        df_custos_filtrado = df_descontos_filtrado.copy()
        
    else:
        df_custos_filtrado = df_custos_gerais[
            (df_custos_gerais['Casa'] == casa) &
            (df_custos_gerais['Classificacao_Contabil_1'] == class_cont) 
        ].copy()
    
    if class_cont == 'Utilidades': # A class. cont.2 Utensílios usa 'Valor_Liquido'
        col_valor = 'Valor_Liquido'
    elif class_cont == 'Desconto sobre Venda':
        col_valor = 'Permanece no Desconto'
    else:
        col_valor = 'Valor_Pagamento'

    # Cria colunas de mês e ano e soma o total mensal para cada class. cont. 2
    df_custos_filtrado['Data_Competencia'] = pd.to_datetime(df_custos_filtrado['Data_Competencia'], errors='coerce')
    df_custos_filtrado['Ano'] = df_custos_filtrado['Data_Competencia'].dt.year
    df_custos_filtrado['Mês'] = df_custos_filtrado['Data_Competencia'].dt.month
    df_custos_filtrado_mensal = df_custos_filtrado.groupby(['Casa', 'Mês', 'Ano', 'Classificacao_Contabil_2'], as_index=False)[col_valor].sum()
    df_custos_filtrado_mensal = df_custos_filtrado_mensal.rename(columns={col_valor:'Custo Real'})

    # Casos em que o custo mensal não depende apenas da aut_blue_me_sem_pedido: merge com outra tabela
    if class_cont in ['Mão de Obra - Salários', 'Gorjeta', 'Custos Artístico Geral', 'Marketing']: 
        df_custos_filtrado_mensal = merge_despesas_complexas(df_custos_filtrado_mensal, df_tabela_secundaria, casa, class_cont)

    # --- Ajuste especial para Bar Brahma (+3000/mês quando for MDO PJ Fixo) ---
    if casa == 'Bar Brahma - Centro':  # ajuste o nome exato da sua tabela
        cond = df_custos_filtrado_mensal['Classificacao_Contabil_2'] == 'MDO PJ Fixo'
        df_custos_filtrado_mensal.loc[cond, 'Custo Real'] += 3000

    if class_cont == 'Utilidades':
        df_aut_filtrado = df_aut_blue_me_com_pedido[
            (df_aut_blue_me_com_pedido['Casa'] == casa)
        ].copy()
        
        # Cria colunas de mês e ano e soma o total mensal para cada class. cont. 2
        df_aut_filtrado['Data_Emissao'] = pd.to_datetime(df_aut_filtrado['Data_Emissao'], errors='coerce')
        df_aut_filtrado['Ano'] = df_aut_filtrado['Data_Emissao'].dt.year
        df_aut_filtrado['Mês'] = df_aut_filtrado['Data_Emissao'].dt.month
        df_aut_filtrado = df_aut_filtrado.groupby(['Casa', 'Mês', 'Ano'], as_index=False)[['Valor_Liq_Alimentos', 'Valor_Liq_Bebidas', 'Valor_Liq_Descart_Hig_Limp', 'Valor_Gelo_Gas_Carvao_Velas', 'Valor_Utensilios', 'Valor_Liq_Outros']].sum()

        df_custos_base = df_custos_filtrado_mensal[['Casa', 'Classificacao_Contabil_2']].drop_duplicates()
        df_combinado = df_custos_base.merge(df_aut_filtrado[['Ano', 'Mês', 'Valor_Liq_Alimentos', 'Valor_Liq_Bebidas', 'Valor_Liq_Descart_Hig_Limp', 'Valor_Gelo_Gas_Carvao_Velas', 'Valor_Utensilios', 'Valor_Liq_Outros']], how='cross')

        # Agora junta novamente com os custos reais (para pegar valores quando existirem)
        df_merge = pd.merge(
            df_combinado,
            df_custos_filtrado_mensal[['Casa', 'Ano', 'Mês', 'Classificacao_Contabil_2', 'Custo Real']],
            on=['Casa', 'Ano', 'Mês', 'Classificacao_Contabil_2'],
            how='left'
        )

        df_merge = df_merge.fillna(0)
        conditions = [
            df_merge['Classificacao_Contabil_2'] == 'Higiene e Limpeza',
            df_merge['Classificacao_Contabil_2'] == 'Material de Escritorio',
            df_merge['Classificacao_Contabil_2'] == 'Utensilios',
            df_merge['Classificacao_Contabil_2'] == 'Material de Consumo - Gelo/ Gas CO2/ Carvao /Velas'
        ]

        choices = [
            df_merge['Custo Real'] + df_merge['Valor_Liq_Descart_Hig_Limp'],
            df_merge['Custo Real'] + df_merge['Valor_Liq_Outros'],
            df_merge['Custo Real'] + df_merge['Valor_Utensilios'],
            df_merge['Custo Real'] + df_merge['Valor_Gelo_Gas_Carvao_Velas']
        ]

        df_merge['Custo Real'] = np.select(
            conditions,
            choices,
            default=df_merge['Custo Real']  # mantém o valor original se nenhuma condição for atendida
        )
        df_custos_filtrado_mensal = df_merge[['Casa', 'Mês', 'Ano', 'Classificacao_Contabil_2', 'Custo Real']]

    # Resgata faturamentos projetados por mês
    df_resgata_faturamento_meses_futuros = df_faturamento_meses_futuros[df_faturamento_meses_futuros['Categoria'] != 'Serviço']
    df_resgata_faturamento_meses_futuros = df_resgata_faturamento_meses_futuros.groupby(['Ano', 'Mês'], as_index=False)[['Valor Bruto', 'Valor Projetado']].sum()
    df_resgata_faturamento_meses_futuros = df_resgata_faturamento_meses_futuros.rename(columns={'Valor Bruto':'Faturamento Real', 'Valor Projetado':'Faturamento Projetado'})
    
    # Merge da tabela de custos passados com a de faturamentos - obter combinação de cada class. cont. 2 com todos os meses do ano para projetar
    df_custos = df_custos_filtrado_mensal.copy()
    df_fat = df_resgata_faturamento_meses_futuros.copy()
    
    # Pega apenas colunas de identificação de categoria
    df_custos_base = df_custos[['Casa', 'Classificacao_Contabil_2']].drop_duplicates()

    # Faz o produto cartesiano: cada categoria × cada mês/ano
    df_combinado = df_custos_base.merge(df_fat[['Ano', 'Mês', 'Faturamento Real', 'Faturamento Projetado']], how='cross')
    
    # Agora junta novamente com os custos reais (para pegar valores quando existirem)
    df_custos_faturamentos_mensais_passados = pd.merge(
        df_combinado,
        df_custos[['Casa', 'Ano', 'Mês', 'Classificacao_Contabil_2', 'Custo Real']],
        on=['Casa', 'Ano', 'Mês', 'Classificacao_Contabil_2'],
        how='left'
    )
    return df_custos_faturamentos_mensais_passados


def projecao_custos_proximos_meses(df_merge_custos_faturamentos_mensais, class_cont_custo, ano_atual, mes_atual):
    # Cria coluna da porcentagem custo/faturamento a ser projetada
    df_merge_custos_faturamentos_mensais['Custo Percentual Projetado'] = None
    df_merge_custos_faturamentos_mensais['Custo Projetado'] = None

    # Cria colunas auxiliares de data
    df_merge_custos_faturamentos_mensais['Mês'] = df_merge_custos_faturamentos_mensais['Mês'].astype(int)
    df_merge_custos_faturamentos_mensais['Mes_Ano'] = (df_merge_custos_faturamentos_mensais['Ano'].astype(int).astype(str) + '-' + df_merge_custos_faturamentos_mensais['Mês'].astype(int).astype(str).str.zfill(2))    
    df_merge_custos_faturamentos_mensais['Data'] = pd.to_datetime(df_merge_custos_faturamentos_mensais['Mes_Ano'], format='%Y-%m')
    
    # Premissa 1: Outras class. cont. de custos (custo1 + custo2 / fat1 + fat2)
    if class_cont_custo not in ['PJ', 'Salários', 'Custo de Ocupação', 'Informática e TI', 'Serviços de Terceiros', 'Locação de Equipamentos', 'Sistema de Franquias']:
        # Loop por classificação contábil 2
        for class_cont in df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'].dropna().unique():
            df_class_cont = df_merge_custos_faturamentos_mensais[df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'] == class_cont]
            
            if df_class_cont is not None and not df_class_cont.empty:
                for i, row in df_class_cont.iterrows():
                    data = row['Data']
                    ano = row['Ano']

                    # if ano >= ano_atual:  # apenas meses do ano atual
                    # pega histórico dos dois meses atrás
                    dois_meses_atras = data - pd.DateOffset(months=2)

                    historico = df_merge_custos_faturamentos_mensais[
                        (df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'] == class_cont) &
                        (df_merge_custos_faturamentos_mensais['Data'] >= dois_meses_atras) &
                        (df_merge_custos_faturamentos_mensais['Data'] < data)
                    ].copy()

                    # Faz Projecao = (Custo1 + Custo2) / (Faturamento_Geral1 + Faturamento_Geral2)
                    # Define colunas auxiliares conforme o mês
                    historico["Custo_Usado"] = np.where(
                        (historico["Mês"] >= mes_atual) & (historico['Ano'] == ano_atual),
                        historico["Custo Projetado"],       # usa o projetado se mês >= atual
                        historico["Custo Real"]             # senão usa o real
                    )

                    historico["Faturamento_Usado"] = np.where(
                        (historico["Mês"] >= mes_atual) & (historico['Ano'] == ano_atual),
                        historico["Faturamento Projetado"],          # usa o projetado se mês >= atual
                        historico["Faturamento Real"]                # senão usa o real
                    )
                    
                    valores_para_soma_custos = historico['Custo_Usado'].fillna(0).astype(float)
                    valores_para_soma_faturamento = historico['Faturamento_Usado'].fillna(historico['Faturamento Projetado']).astype(float)

                    soma_custos = valores_para_soma_custos.sum()
                    soma_faturamentos = valores_para_soma_faturamento.sum()
                    
                    if soma_faturamentos and not pd.isna(soma_faturamentos) and soma_faturamentos != 0:
                        custo_projetado = (soma_custos / soma_faturamentos) * 100
                    else:
                        custo_projetado = 0 

                    # Atribui o valor à coluna correta
                    df_merge_custos_faturamentos_mensais.at[i, 'Custo Percentual Projetado'] = custo_projetado
                    
                    # Define valor de Custo Projetado em Reais - QUESTÃO dos valores arredondados na exibição do 'Custo Percentual Projetado'
                    df_merge_custos_faturamentos_mensais['Custo Projetado'] = (df_merge_custos_faturamentos_mensais['Custo Percentual Projetado'] / 100) * df_merge_custos_faturamentos_mensais['Faturamento Projetado']

    # Premissa 3: 5% do Faturamento Estimado - Sistema de Franquias
    elif class_cont_custo == 'Sistema de Franquias':
        df_merge_custos_faturamentos_mensais['Custo Projetado'] = 0.05 * df_merge_custos_faturamentos_mensais['Faturamento Projetado']

    # Premissa 2: Igual ao mês anterior - PJ, Salários, Custo de Ocupação, Informática e TI, Serviços de Terceiros, Locação de Equipamentos
    else:
        for class_cont in df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'].dropna().unique():
            df_class_cont = df_merge_custos_faturamentos_mensais[df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'] == class_cont]
            for mes_ano in df_class_cont['Mes_Ano'].unique():
                df_mes_ano = df_class_cont[df_class_cont['Mes_Ano'] == mes_ano]
                data = df_mes_ano['Data'].iloc[0]

                # pega o valor do custo do mês anterior
                mes_anterior = data - pd.DateOffset(months=1)
                dado_mes_anterior = df_class_cont[df_class_cont['Data'] == mes_anterior]
                
                if not dado_mes_anterior.empty:
                    mes_anterior = dado_mes_anterior['Data'].iloc[0].month
                    custo_usado = dado_mes_anterior['Custo Real'].iloc[0]

                    if not custo_usado or mes_anterior == mes_atual: # Caso o mês ainda não tenha o valor lançado
                        custo_usado = dado_mes_anterior['Custo Projetado'].iloc[0] # Usa a projeção do mês anterior em vez do real
                    
                    # Atribui o valor à coluna correta
                    df_merge_custos_faturamentos_mensais.loc[
                        (df_merge_custos_faturamentos_mensais['Mes_Ano'] == mes_ano) &
                        (df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'] == class_cont),
                        'Custo Projetado'
                    ] = custo_usado   

                    # Recarrega o DataFrame atualizado para que o próximo loop "veja" as mudanças
                    df_class_cont = df_merge_custos_faturamentos_mensais[
                        df_merge_custos_faturamentos_mensais['Classificacao_Contabil_2'] == class_cont
                    ]

    return df_merge_custos_faturamentos_mensais


def exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_meses_anteriores_seguintes, titulo, tipo, ano_atual, mes_atual, igual_mes_anterior=False):
    df_projecao_custos = df_projecao_custos_meses_anteriores_seguintes.copy()

    df_projecao_custos = df_projecao_custos.rename(columns={
        'Classificacao_Contabil_2': 'Class. Contábil 2',
        'Faturamento Real': 'Faturamento Real Mês',
        'Faturamento Projetado': 'Faturamento Projetado Mês',
    })
    
    # Prepara colunas para exibir projeção prox meses
    if tipo == 'meses seguintes':
        df_projecao_custos = df_projecao_custos[(df_projecao_custos['Mês'] >= mes_atual) & (df_projecao_custos['Ano'] == ano_atual)]
        colunas_num_dataframe = ['Faturamento Projetado Mês', 'Custo Projetado', 'Custo Real']
        if igual_mes_anterior == False:
            colunas = ['Class. Contábil 2', 'Ano', 'Mês', 'Faturamento Projetado Mês', 'Custo Percentual Projetado', 'Custo Projetado', 'Custo Real']
            colunas_percent_dataframe = ['Custo Percentual Projetado']
        else:
            colunas = ['Class. Contábil 2', 'Ano', 'Mês', 'Faturamento Projetado Mês', 'Custo Projetado', 'Custo Real']
            colunas_percent_dataframe = None

    # Prepara colunas para exibir projeção meses anteriores
    if tipo == 'meses anteriores':
        if mes_atual == 1:
            df_projecao_custos = df_projecao_custos[df_projecao_custos['Ano'] == ano_atual - 1]
        else:
            df_projecao_custos = df_projecao_custos[(df_projecao_custos['Mês'] < mes_atual) & (df_projecao_custos['Ano'] == ano_atual)]
        colunas = ['Class. Contábil 2', 'Mês', 'Ano', 'Faturamento Real Mês', 'Custo Percentual Projetado', 'Custo Projetado', 'Custo Real']
        colunas_num_dataframe = ['Faturamento Real Mês', 'Custo Projetado', 'Custo Real']
        if igual_mes_anterior == False:
            colunas = ['Class. Contábil 2', 'Mês', 'Ano', 'Faturamento Real Mês', 'Custo Percentual Projetado', 'Custo Projetado', 'Custo Real']
            colunas_percent_dataframe = ['Custo Percentual Projetado']
        else:
            colunas = ['Class. Contábil 2', 'Mês', 'Ano', 'Faturamento Real Mês', 'Custo Projetado', 'Custo Real']
            colunas_percent_dataframe = None

    df_projecao_custos = df_projecao_custos[colunas]
    df_projecao_custos['Custo Real'] = df_projecao_custos['Custo Real'].fillna(0)
    df_projecao_custos['Custo Projetado'] = df_projecao_custos['Custo Projetado'].fillna(0)
    
    st.markdown(f'''
            <h4 style="color: #1f77b4;">{titulo}</h4>
        ''', unsafe_allow_html=True)
    
    df_projecao_custos_exibe = function_format_number_columns(df_projecao_custos, columns_money=colunas_num_dataframe, columns_percent=colunas_percent_dataframe)
    dataframe_aggrid(
        df=df_projecao_custos_exibe,
        name=f"Projeção Custos - {titulo} - {tipo}",
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True,
    )
    st.divider()
