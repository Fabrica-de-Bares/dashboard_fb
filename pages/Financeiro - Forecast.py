import streamlit as st
from utils.components import input_selecao_casas, seletor_ano, seletor_mes
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import *
from utils.functions.controladoria_planejamento_anual import highlight_secoes_dre
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

# Seletores de casa e data
col1, col2, col3 = st.columns(3)
with col1: # Casas sem DRE
    lista_retirar_casas = ['Todas as Casas', 'Bar Brahma Paulista', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Terraço Notie', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
with col2:
    mes_selecionado = int(seletor_mes('Selecione um mês', 'mes_forecast'))
with col3:
    ano_selecionado = seletor_ano(2025, datas['ano_atual'], 'ano_forecast')
st.divider()

if casa == 'Arcos': st.info('Observação: Arcos sem operação às segundas-feiras.')


# Dados - Faturamento Diário
(df_faturamento_zig, 
 df_faturamento_agregado_dia, 
 df_faturamento_eventos_inicial, 
 df_faturamento_eventos, 
 df_parc_receitas_extr) = GET_TODOS_FATURAMENTOS_DIA(id_casa)

# Dados - Receitas Extraordinárias (apenas Patrocínios)
df_parc_receitas_extr_patrocinio = GET_RECEITAS_EXTR_PATROCINIO()

# Dados - Descontos e Promoções
df_descontos = GET_DESCONTOS()
df_promocoes = GET_PROMOCOES()

# Dados - Faturamento e Orçamento Mensal
df_orcamentos = GET_ORCAMENTOS()
df_faturamento_agregado_mes = GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_agregado_dia, df_descontos, df_promocoes, df_faturamento_eventos_inicial)

df_aut_blue_me_sem_pedido = GET_AUT_BLUE_ME_SEM_PEDIDO() # Dados - Despesas por classificação contábil
df_aut_folha = GET_AUT_FOLHA_PAGAMENTO() 
df_ajustes_manuais = GET_AJUSTES_MANUAIS_DRE() 
df_consumo_cartao_black = GET_CONSUMO_CARTAO_BLACK() 

# Filtrando Datas
datas = calcular_datas()

# Constantes - Impostos (iguais para todas as casas)
PORC_ISS = 0.05
PORC_PIS = 0.0065
PORC_COFINS = 0.03
PORC_ICMS = 0.04


###################### PROJEÇÃO DE FATURAMENTO - MÊS CORRENTE ###################### 

# # Prepara df de faturamento agregado diário para a casa selecionada
# df_faturamento_agregado_mes_corrente = prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, datas['fim_mes_atual'], datas['inicio_dois_meses_antes'])
# if casa == 'Arcos': 
#     # Não abre de segunda-feira: zera segundas com faturamento de A&B para não impactar na projeção (vêm de Eventos)
#     condicao = (df_faturamento_agregado_mes_corrente['Casa'] == 'Arcos') & (df_faturamento_agregado_mes_corrente['Dia Semana'] == 'Segunda-feira')
#     df_faturamento_agregado_mes_corrente.loc[condicao, 'Valor Bruto'] = 0

# # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
# df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(datas['ano_atual'], df_faturamento_agregado_mes_corrente)

# # Gera projeção para prox dias do mês corrente por dia da semana
# df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias)
# df_dias_mes = df_dias_futuros_com_categorias[df_dias_futuros_com_categorias['Categoria'] != 'Serviço'].copy()
# df_dias_mes = df_dias_mes[['Data Evento', 'Categoria']]

# # Aplica layout
# pivot_faturamento_mes_corrente = aplica_layout_mes_corrente(df_dias_futuros_mes, df_faturamento_eventos, df_parc_receitas_extr, df_dias_mes, id_casa, casa, mes_selecionado, ano_selecionado)
# height = (len(pivot_faturamento_mes_corrente) + 1) * 35 # Define altura sem rolagem 

# # Formata colunas numéricas
# df_mes_corrente_estilizado = function_format_number_columns(
#     pivot_faturamento_mes_corrente,
#     columns_money=[col for col in pivot_faturamento_mes_corrente if col not in ['Data Evento', 'Dia Semana']]
# )

# # Pinta os dias apenas se for selecionado o mês corrente
# if mes_selecionado == datas['mes_atual'] and ano_selecionado == datas['ano_atual']:
#     df_mes_corrente_estilizado = pivot_faturamento_mes_corrente.style.apply(destaca_dias_futuros_mes_corrente, axis=1)
# else:
#     df_mes_corrente_estilizado = pivot_faturamento_mes_corrente 
#     df_mes_corrente_estilizado = df_mes_corrente_estilizado.style.apply(
#         lambda col: ['background-color: #f0f2f6; color: black;' if col.name == 'Total' else '' for _ in col],
#         axis=0
#     )   

# if mes_selecionado == datas['mes_atual'] and ano_selecionado == datas['ano_atual']:
#     st.subheader('Faturamento diário - mês corrente')
# else:
#     st.subheader('Faturamento diário - mês selecionado')

# st.dataframe(df_mes_corrente_estilizado, hide_index=True, width='stretch')
# # Exibe legenda
# st.markdown(f'''
#     <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
#         <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
#         <span style="font-size: 14px">Média de faturamento projetado (não real) para dias futuros.</span>
#     </div>
# ''', unsafe_allow_html=True)
# st.write("")
# # Premissas
# st.markdown(f'''
#     <div style="display:flex; flex-direction:column; padding:10px; border:1px solid #ccc; border-radius:8px";>
#         <p><strong>Premissas</strong></p>
#         <span style="font-size: 14px">- Para Alimentos, Bebidas, Couvert, Delivery e Gifts: por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</span>
#         <span style="font-size: 14px">- Para Eventos e Outras Receitas (coleta de óleo): considerar os lançamentos com competência para o dia correspondente.</span>
#     </div>
# ''', unsafe_allow_html=True)
# st.divider()


###################### PROJEÇÃO DE FATURAMENTO - DRE ###################### 

# Prepara df de faturamento agregado mensal para a casa selecionada
df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, datas['ano_passado'], datas['ano_atual'])
lista_itens_faturamento = df_faturamento_orcamento['Categoria'].unique().tolist() # Para exibir todos os itens de faturamento, mesmo que não haja valor para a casa
valor_fat_bruto_mes = (df_faturamento_mes_casa[
    (df_faturamento_mes_casa['Ano'] == ano_selecionado) &
    (df_faturamento_mes_casa['Mês'] == mes_selecionado)
])['Valor Bruto'].sum()

# Cria combinação das categorias de faturamento com meses do ano (desde 2025)
df_meses_futuros_com_categorias = lista_meses_ano(lista_itens_faturamento)

# Gera projeção para prox meses do ano
df_faturamento_meses_futuros = projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'], datas['mes_atual'])
df_faturamento_meses_futuros = projecao_faturamento_servico_meses_seguintes(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

# Calcula Impostos sobre Venda
df_faturamento_para_impostos = df_faturamento_meses_futuros.copy()
lista_itens_impostos = ['ISS', 'ICMS', 'PIS', 'COFINS', 'PIS / COFINS'] 
df_impostos_meses_futuros = lista_meses_ano(lista_itens_impostos)

df_projecao_impostos = projecao_impostos(df_faturamento_para_impostos, lista_itens_impostos, df_impostos_meses_futuros, PORC_ISS, PORC_ICMS, PORC_PIS, PORC_COFINS)
df_impostos_dre = formata_impostos_para_dre(df_projecao_impostos, df_orcamentos, casa, mes_selecionado, ano_selecionado)


# Itens CMV 
df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery = config_faturamento_bruto_zig(df_faturamento_agregado_dia, datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_faturamento_eventos = config_faturamento_eventos(datas['jan_ano_passado'], datas['dez_ano_atual'], casa, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
df_compras, df_aut_blue_me_com_pedido, compras_alimentos, compras_bebidas = config_compras(datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_valoracao_estoque = config_valoracao_estoque_ou_producao('estoque', datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_transf_e_gastos = config_transferencias_gastos(datas['jan_ano_passado'], datas['dez_ano_atual'], casa)
df_valoracao_producao = config_valoracao_estoque_ou_producao('producao', datas['jan_ano_passado'], datas['dez_ano_atual'], casa)

# Consumo Interno - merge com Mão de Obra - Benefícios
df_consumo_interno_cmv = df_transf_e_gastos.copy()
df_consumo_interno_cmv['Mês'] = pd.to_datetime(df_consumo_interno_cmv['Mes_Ano'], errors='coerce').dt.month
df_consumo_interno_cmv['Ano'] = pd.to_datetime(df_consumo_interno_cmv['Mes_Ano'], errors='coerce').dt.year
df_consumo_interno_cmv = df_consumo_interno_cmv[['ID_Casa', 'Casa', 'Mês', 'Ano', 'Consumo Interno']]

# Cálculo CMV meses anteriores
df_calculo_cmv = merge_e_calculo_para_cmv(
    df_faturamento_zig, 
    df_compras, 
    df_valoracao_estoque, 
    df_transf_e_gastos, 
    df_valoracao_producao, 
    df_faturamento_eventos,
    df_ajustes_manuais,
    casa, ano_selecionado
)

# Projeção CMV próximos meses
df_cmv_meses_anteriores_seguintes = calcula_cmv_proximos_meses(df_faturamento_meses_futuros, df_calculo_cmv, datas['ano_atual'], datas['mes_atual'])

# Merge com CMV Orçado
df_orcamentos_cmv = df_orcamentos[
    (df_orcamentos['Casa'] == casa) &
    (df_orcamentos['Classificacao_Contabil_1'] == 'Custo Mercadoria Vendida') 
].copy()
df_orcamentos_cmv = df_orcamentos_cmv.groupby(['Casa', 'Ano', 'Mês'], as_index=False)['Orçamento'].sum()

df_cmv_meses_anteriores_seguintes = pd.merge(
    df_cmv_meses_anteriores_seguintes,
    df_orcamentos_cmv,
    on=['Casa', 'Mês', 'Ano'],
    how='left'
)

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
    'Sistema de Franquias',                
    'Despesas Financeiras', # (+/-) Receitas/Despesas Financeiras
    'Patrocínio',
    'Investimento - CAPEX',
    'Dividendos e Remunerações Variáveis', # (+/-) Outras variações no fluxo de caixa
]

lista_df_projecao_despesas = loop_prepara_dados_despesas(
    lista_categorias_despesas,
    df_descontos, 
    df_consumo_interno_cmv,
    df_consumo_cartao_black,
    df_aut_blue_me_sem_pedido, 
    df_aut_blue_me_com_pedido,
    df_faturamento_meses_futuros, 
    df_aut_folha, 
    df_orcamentos, 
    df_parc_receitas_extr_patrocinio,
    df_ajustes_manuais,
    lista_df_projecao_despesas, 
    casa, 
    mes_selecionado, 
    ano_selecionado
)

st.subheader('Real vs Tendência do mês - Faturamento e Despesas')
df_despesas_concatenadas = pd.concat(lista_df_projecao_despesas, ignore_index=True)

df_layout_dre = aplica_layout_dre(df_faturamento_meses_futuros, df_impostos_dre, df_cmv_meses_anteriores_seguintes, df_despesas_concatenadas, mes_selecionado, ano_selecionado)

# Remove linhas que não quero exibir ou renomeia
df_layout_dre = df_layout_dre[~df_layout_dre['Categoria'].isin(['Patrocínio', 'Endividamento'])].reset_index(drop=True)
df_layout_dre['Categoria'] = df_layout_dre['Categoria'].replace({
    'Dividendos e Remunerações Variáveis': '(+/-) Outras variações no fluxo de caixa',
    'Despesas Financeiras': '(+/-) Receitas/Despesas Financeiras',
    'Investimento - CAPEX': '(-) CAPEX (Investimentos)',
})

mapa_insercao = { # Mapa inserção das linhas de '% sobre Receita' de cada classificação contábil
    'Desconto sobre Venda': 'Descontos - Operação',              
    'Custos Artístico Geral': 'Viagens e Estadias - Artístico',             
    'Custos de Eventos': 'Viagens e Estadias - Eventos',                 
    'Gorjeta': '  -  Comissões e Gorjeta',                            
    'Deduções sobre Venda': 'Outros D',               
    'PESSOAL': '  -  Vale-transporte',                             
    'Custo de Ocupação': 'Taxas publicas administrativas - Ocupação',                  
    'Utilidades': 'Utensilios',                         
    'Informática e TI': 'Telefone',                   
    'Manutenção': 'Viagens e Estadias - Operação', # Despesas Gerais       
    'Marketing': 'Sessão de Fotos/Captação de Vídeo',                          
    'Serviços de Terceiros': 'Valet/Motoboy',              
    'Locação de Equipamentos': 'Locações de Equipamentos - Operacionais',            
    'Sistema de Franquias': 'Royalties',             
}
colunas_valores = (df_layout_dre.select_dtypes(include='number').drop(columns=['Percentual Real (do Orçamento)']).columns)
df_layout_dre = define_linhas_calculadas(df_layout_dre, colunas_valores, lista_categorias_despesas, mapa_insercao)

# Formata colunas numéricas
colunas_moeda_variavel = [
    'Orçamento',
    'Valor Projetado',
    'Valor Real'
]
colunas_percentuais = [
    'Percentual Projetado',
    'Percentual Real (do Orçamento)'
]
linhas_percentual = df_layout_dre['Categoria'].str.contains('%', na=False) 

df_layout_dre_styled = (
    df_layout_dre.style
    .format(formatar_colunas_porcentagem, subset=colunas_percentuais)
    .format(formatar_linhas_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_moeda_variavel])
    .format(formatar_colunas_moeda_br,subset=pd.IndexSlice[~linhas_percentual, colunas_moeda_variavel])
    .apply(highlight_secoes_dre, axis=1) # Destaca linhas de título
)

height = (len(df_layout_dre) + 1) * 35 # Define altura sem rolagem
st.dataframe(df_layout_dre_styled, hide_index=True, width='stretch', height=height)

# # Premissas
# # Falta ajustar Benefícios e Outros B (Mão de Obra - Benefícios)
# st.markdown(f'''
#     <div style="display:flex; flex-direction:column; padding:10px; border:1px solid #ccc; border-radius:8px";>
#         <p><strong>Premissas</strong></p>
#         <span style="font-size: 14px">- Para os itens de faturamento (exceto Serviço): calcula a média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</span>
#         <span style="font-size: 14px">- Para Serviço: calcula 13% do Faturamento Projetado para o mês.</span>
#         <span style="font-size: 14px">- Para CMV, Desconto sobre Venda, Custos Artístico Geral, Custos Eventos, Gorjeta, Deduções sobre Venda, Mão de Obra - Extra, Mão de Obra - Encargos e Provisões, Utilidades, Manutenção e Marketing: média da % da despesa em relação ao Faturamento Real dos últimos 2 meses x o Faturamento Projetado para o mês.</span>
#         <span style="font-size: 14px">- Para imposto ISS: soma Faturamento de Eventos e Gifts e aplica taxa de {PORC_ISS*100}%.</span>
#         <span style="font-size: 14px">- Para imposto ICMS: soma Faturamento de A&B, Artístico/Couvert e Delivery e aplica taxa de {PORC_ICMS*100}%.</span>
#         <span style="font-size: 14px">- Para imposto PIS: aplica diferença entre Faturamento Bruto e ICMS aplica taxa de {PORC_PIS*100}%.</span>
#         <span style="font-size: 14px">- Para imposto COFINS: aplica diferença entre Faturamento Bruto e ICMS aplica taxa de {PORC_COFINS*100}%.</span>
#         <span style="font-size: 14px">- Para Mão de Obra - PJ, Mão de Obra - Salários, Custos de Ocupação, Informática e TI, Serviços de Terceiros e Locação de Equipamentos: Valor Fixo, considerar o valor do mês anterior.</span>
#         <span style="font-size: 14px">- Para Mão de Obra - Benefícios: média da % da despesa em relação ao Salário Real dos últimos 2 meses x o Salário Projetado para o mês.</span>
#         <span style="font-size: 14px">- Para Sistema de Franquias: calcula 5% do Faturamento Projetado para o mês.</span>
#     </div>
# ''', unsafe_allow_html=True)


