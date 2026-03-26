import streamlit as st
from utils.components import input_selecao_casas, seletor_ano, seletor_mes
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import *
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.queries_forecast import *


st.set_page_config(
    page_title="Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title("📈 Forecast")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()


# Dados - Faturamento Diário
(df_faturamento_zig, df_faturamento_agregado_dia, 
 df_faturamento_eventos_inicial, df_faturamento_eventos, 
 df_parc_receitas_extr_categoria, df_parc_receit_extr_dia) = GET_TODOS_FATURAMENTOS_DIA()

# Dados - Descontos e Promoções
df_descontos = GET_DESCONTOS()
df_promocoes = GET_PROMOCOES()

# Dados - Faturamento e Orçamento Mensal
df_orcamentos = GET_ORCAMENTOS()
df_faturamento_agregado_mes = GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_agregado_dia, df_descontos, df_promocoes, df_faturamento_eventos_inicial)

# Dados - Despesas por classificação contábil
df_aut_blue_me_sem_pedido = GET_AUT_BLUE_ME_SEM_PEDIDO()

# Dados - Folha/Gorjeta
df_aut_folha = GET_AUT_FOLHA_PAGAMENTO()

# Filtrando Datas
datas = calcular_datas()


# Seletores de casa e data
col1, col2, col3 = st.columns(3)
with col1:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Todas as Casas']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
with col2:
    mes_selecionado = int(seletor_mes('Selecione um mês', 'mes_forecast'))
with col3:
    ano_selecionado = seletor_ano(2025, datas['ano_atual'], 'ano_forecast')
st.divider()

if casa == 'Arcos': st.info('Observação: Arcos sem operação às segundas-feiras.')

###################### PROJEÇÃO DE FATURAMENTO - MÊS CORRENTE ###################### 

# Prepara df de faturamento agregado diário para a casa selecionada
df_faturamento_agregado_mes_corrente = prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, datas['fim_mes_atual'], datas['inicio_dois_meses_antes'])
if casa == 'Arcos': 
    # Não abre de segunda-feira: zera segundas com faturamento de A&B para não impactar na projeção (vêm de Eventos)
    condicao = (df_faturamento_agregado_mes_corrente['Casa'] == 'Arcos') & (df_faturamento_agregado_mes_corrente['Dia Semana'] == 'Segunda-feira')
    df_faturamento_agregado_mes_corrente.loc[condicao, 'Valor Bruto'] = 0

# --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(
    datas['ano_atual'], datas['mes_atual'], 
    df_faturamento_agregado_mes_corrente)

# Gera projeção para prox dias do mês corrente por dia da semana
df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias)

if mes_selecionado == datas['mes_atual']:
    df_dias_mes = df_dias_futuros_com_categorias[df_dias_futuros_com_categorias['Categoria'] != 'Serviço']
    df_dias_mes = df_dias_mes[['Data Evento', 'Categoria']]
    pivot_faturamento_mes_corrente = aplica_layout_mes_corrente(df_dias_futuros_mes, df_faturamento_eventos, df_parc_receit_extr_dia, df_dias_mes, id_casa, casa, mes_selecionado, ano_selecionado)
    height = (len(pivot_faturamento_mes_corrente) + 1) * 35 # Define altura sem rolagem 

    # Formata colunas numéricas
    df_mes_corrente_estilizado = function_format_number_columns(
        pivot_faturamento_mes_corrente,
        columns_money=[col for col in pivot_faturamento_mes_corrente if col not in ['Data Evento', 'Dia Semana']]
    )

    df_mes_corrente_estilizado = pivot_faturamento_mes_corrente.style.apply(destaca_dias_futuros_mes_corrente, axis=1)

    st.subheader('Faturamento - mês corrente')
    st.dataframe(df_mes_corrente_estilizado, hide_index=True, width='stretch')
    # Exibe legenda
    st.markdown(f'''
        <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
            <span style="font-size: 14px">Média de faturamento projetado (não real) para dias futuros.</span>
        </div>
    ''', unsafe_allow_html=True)
    st.write("")
    # Premissas
    st.markdown(f'''
        <div style="display:flex; flex-direction:column; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <p><strong>Premissas</strong></p>
            <span style="font-size: 14px">- Para Alimentos, Bebidas, Couvert, Delivery e Gifts: por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</span>
            <span style="font-size: 14px">- Para Eventos: considerar os lançamentos com competência para o dia correspondete.</span>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()

# # Container que exibe projeção dos prox dias do mês corrente
# with st.container(border=True):
#     st.markdown(f'''
#         <h4>Faturamentos por categoria</h4>
#         <p><strong>Premissa</strong> (para todas as categorias de faturamento, exceto 'Eventos' e 'Outras Receitas'): por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</p>
#         ''', unsafe_allow_html=True)

#     exibe_faturamento_categoria_mes_corrente('A&B', df_dias_futuros_mes, 'dias seguintes', datas)
#     exibe_faturamento_categoria_mes_corrente('Gifts', df_dias_futuros_mes, 'dias seguintes', datas)
#     exibe_faturamento_categoria_mes_corrente('Delivery', df_dias_futuros_mes, 'dias seguintes', datas)
#     exibe_faturamento_categoria_mes_corrente('Couvert', df_dias_futuros_mes, 'dias seguintes', datas)
#     exibe_faturamento_eventos(df_faturamento_eventos, id_casa, datas)
#     exibe_faturamento_outras_receitas(df_parc_receit_extr_dia, df_parc_receitas_extr_categoria, id_casa, datas)

# # Container que exibe faturamento real e projetado dos dias anteriores do mês corrente
# with st.container(border=True):
#     exibe_faturamento_categoria_mes_corrente('Dias anteriores', df_dias_futuros_mes, 'dias anteriores', datas)


###################### PROJEÇÃO DE FATURAMENTO - PRÓXIMOS MESES ###################### 

# Prepara df de faturamento agregado mensal para a casa selecionada
df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, datas['ano_passado'], datas['ano_atual'])
lista_itens_faturamento = df_faturamento_orcamento['Categoria'].unique().tolist() # Para exibir todos os itens de faturamento, mesmo que não haja valor para a casa

# Cria combinação das categorias de faturamento com meses do ano (desde 2025)
df_meses_futuros_com_categorias = lista_meses_ano(lista_itens_faturamento)

# Gera projeção para prox meses do ano
df_faturamento_meses_futuros = projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'], datas['mes_atual'])
df_faturamento_meses_futuros = projecao_faturamento_servico_meses_seguintes(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

# # Container que exibe projeção dos prox meses
# with st.container(border=True):
#     st.markdown(f'''
#         <h4>Faturamentos por categoria</h4>
#         <p><strong>Premissa</strong> (para todas as categorias de faturamento): média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</p>
#         ''', unsafe_allow_html=True)

#     exibe_categoria_faturamento_prox_meses('A&B', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
#     exibe_categoria_faturamento_prox_meses('Gifts', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
#     exibe_categoria_faturamento_prox_meses('Delivery', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
#     exibe_categoria_faturamento_prox_meses('Couvert', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
#     exibe_categoria_faturamento_prox_meses('Eventos', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
#     exibe_categoria_faturamento_prox_meses('Outras Receitas', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

# st.divider()

# # Container que exibe faturamento e CMV real e projetado dos meses anteriores 
# with st.container(border=True):
#     exibe_faturamento_meses_anteriores(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])


###################### DESPESAS - PRÓXIMOS MESES ###################### 
# with tab3:
#     st.markdown(f'''
#         <h3>Projeções - {casa} - Próximos meses</h3>
#         ''', unsafe_allow_html=True)
#     st.divider()

#     # Prepara e exibe projeção de custos por categoria dos prox meses
#     with st.container(border=True):
#         st.markdown(f'''
#             <h4>Despesas por categoria</h4>
#             <p><strong>Premissa:</strong></p>
#         ''', unsafe_allow_html=True)

# CMV 
df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery = config_faturamento_bruto_zig(df_faturamento_agregado_dia, datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_faturamento_eventos = config_faturamento_eventos(datas['jan_ano_passado'], datas['dez_ano_atual'], casa, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
df_compras, df_aut_blue_me_com_pedido, compras_alimentos, compras_bebidas = config_compras(datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_valoracao_estoque = config_valoracao_estoque_ou_producao('estoque', datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas = config_transferencias_gastos(datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_valoracao_producao = config_valoracao_estoque_ou_producao('producao', datas['jan_ano_passado'], datas['dez_ano_atual'], casa)

# Cálculo CMV e Faturamento Geral para meses anteriores
df_calculo_cmv = merge_e_calculo_para_cmv(
    df_faturamento_zig, 
    df_compras, 
    df_valoracao_estoque, 
    df_transf_e_gastos, 
    df_valoracao_producao, 
    df_faturamento_eventos
)

df_cmv_meses_anteriores_seguintes = calcula_cmv_proximos_meses(df_faturamento_meses_futuros, df_calculo_cmv, datas['ano_atual'], datas['mes_atual'])
# exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, 'meses seguintes', datas['mes_atual'], datas['ano_atual'])

# Cria lista com todos dfs de despesas projetadas
lista_df_projecao_despesas = [] 

lista_categorias_despesas = [
    'Desconto sobre Venda',
    'Custos Artístico Geral',
    'Custos de Eventos',
    'Gorjeta',
    'Deduções sobre Venda',
    'Mão de Obra - PJ',
    'Mão de Obra - Salários',
    'Mão de Obra - Extra',
    'Mão de Obra - Encargos e Provisões',
    'Mão de Obra - Benefícios',
    'Custo de Ocupação',
    'Utilidades',
    'Informática e TI',
    'Manutenção', # Despesas Gerais
    'Marketing',
    'Serviços de Terceiros',
    'Locação de Equipamentos',
    'Sistema de Franquias'
]

lista_df_projecao_despesas = loop_prepara_dados_despesas(
    lista_categorias_despesas,
    df_descontos, 
    df_aut_blue_me_sem_pedido, 
    df_aut_blue_me_com_pedido,
    df_faturamento_meses_futuros, 
    df_aut_folha, 
    df_orcamentos, 
    lista_df_projecao_despesas, 
    casa, 
    mes_selecionado, 
    ano_selecionado
)


st.subheader('Real vs Tendência do mês - Faturamento e Despesas')
df_despesas_concatenadas = pd.concat(lista_df_projecao_despesas, ignore_index=True)

df_layout_dre = aplica_layout_dre(df_faturamento_meses_futuros, df_cmv_meses_anteriores_seguintes, df_despesas_concatenadas, mes_selecionado, ano_selecionado)
height = (len(df_layout_dre) + 1) * 35 # Define altura sem rolagem

# Formata colunas numéricas
df_layout_dre = function_format_number_columns(
    df_layout_dre,
    columns_money=['Orçamento', 'Valor Projetado', 'Valor Real'],
    columns_percent=['Percentual Projetado (do Orçamento)', 'Percentual Real (do Orçamento)']
)

df_layout_dre.loc[df_layout_dre['Orçamento'] == 'R$ nan', 'Orçamento'] = '-'
df_layout_dre.loc[(df_layout_dre['Percentual Projetado (do Orçamento)'] == '') | (df_layout_dre['Percentual Projetado (do Orçamento)'] == '0,00%'), 'Percentual Projetado (do Orçamento)'] = '-'
df_layout_dre.loc[df_layout_dre['Valor Projetado'] == 'R$ nan', 'Valor Projetado'] = '-'
df_layout_dre.loc[df_layout_dre['Valor Real'] == 'R$ 0,00', 'Valor Real'] = '-'
df_layout_dre.loc[(df_layout_dre['Percentual Real (do Orçamento)'] == '') | (df_layout_dre['Percentual Real (do Orçamento)'] == '0,00%'), 'Percentual Real (do Orçamento)'] = '-'

# Destaca linhas de título
df_layout_dre = df_layout_dre.reset_index(drop=True)
df_layout_dre_styled = df_layout_dre.style.apply(highlight_titulos_dre, axis=1) 
st.dataframe(df_layout_dre_styled, hide_index=True, width='stretch', height=height)

# Premissas
# Falta ajustar Benefícios e Outros B (Mão de Obra - Benefícios)
st.markdown(f'''
    <div style="display:flex; flex-direction:column; padding:10px; border:1px solid #ccc; border-radius:8px";>
        <p><strong>Premissas</strong></p>
        <span style="font-size: 14px">- Para os itens de faturamento (exceto Serviço): calcula a média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</span>
        <span style="font-size: 14px">- Para Serviço: calcula 13% do Faturamento Projetado para o mês.</span>
        <span style="font-size: 14px">- Para CMV, Desconto sobre Venda, Custos Artístico Geral, Custos Eventos, Gorjeta, Deduções sobre Venda, Mão de Obra - Extra, Mão de Obra - Encargos e Provisões, Utilidades, Manutenção e Marketing: média da % da despesa em relação ao Faturamento Real dos últimos 2 meses x o Faturamento Projetado para o mês.</span>
        <span style="font-size: 14px">- Para Mão de Obra - PJ, Mão de Obra - Salários, Custos de Ocupação, Informática e TI, Serviços de Terceiros e Locação de Equipamentos: Valor Fixo, considerar o valor do mês anterior.</span>
        <span style="font-size: 14px">- Para Sistema de Franquias: calcula 5% do Faturamento Projetado para o mês.</span>
    </div>
''', unsafe_allow_html=True)


