import streamlit as st
from utils.components import input_selecao_casas, seletor_ano, seletor_mes
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.cmv_teorico_fichas_tecnicas import function_format_number_columns
from utils.functions.controladoria_planejamento_anual import highlight_secoes_dre
from utils.queries_forecast import *
from utils.queries_dre_download import *
import os
import traceback


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
    lista_retirar_casas = ['Todas as Casas', 'Bar Brahma - Paulista', 'Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Bar Brahma - Paulista', 'Brahminha', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Terraço Notie', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
with col2:
    mes_selecionado = int(seletor_mes('Selecione um mês', 'mes_forecast'))
with col3:
    ano_selecionado = seletor_ano(2026, datas['ano_atual'], 'ano_forecast')
st.divider()

if casa == 'Arcos': st.info('Observação: Arcos sem operação às segundas-feiras.')


# Dados - Faturamento Diário
(df_faturamento_zig, 
 df_faturamento_agregado_dia, 
 df_faturamento_eventos_inicial, 
 df_faturamento_eventos, 
 df_receitas_extr_gifts_oleo) = GET_TODOS_FATURAMENTOS_DIA(id_casa)

# Dados - Receitas Extraordinárias (apenas Patrocínios)
df_demais_receitas_extr = GET_DEMAIS_RECEITAS_EXTR() # Patrocínio, Eventos Rebate Fornecedores (Priceless) e itens (Blue Note) 

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
df_parametros_impostos = GET_PARAMETROS_IMPOSTOS() # Parâmetros e taxas - Impostos e Encargos e Provisões
df_aliquotas_imp_simples = GET_IMPOSTO_SIMPLES() # Faixas e alíquotas - Simples Nacional

# Filtrando Datas
datas = calcular_datas()

# Calculado para casas 100% FB
PORC_FEE_GESTAO = 0.05 


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
# pivot_faturamento_mes_corrente = aplica_layout_mes_corrente(df_dias_futuros_mes, df_faturamento_eventos, df_receitas_extr_gifts_oleo, df_dias_mes, id_casa, casa, mes_selecionado, ano_selecionado)
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

# if mes_selecionado == datas['mes_atual'] and ano_selecionado == datas['ano_atual']: # Exibe legenda
#     st.markdown(f'''
#         <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
#             <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
#             <span style="font-size: 14px">Média de faturamento projetado (não real) para próximos dias do mês.</span>
#         </div>
#     ''', unsafe_allow_html=True)
#     st.write("")

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
df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, df_demais_receitas_extr, df_ajustes_manuais, datas['ano_passado'], datas['ano_atual'], ano_selecionado)
lista_itens_faturamento = df_faturamento_orcamento['Categoria'].unique().tolist() # Para exibir todos os itens de faturamento, mesmo que não haja valor para a casa

# Faturamento Bruto do mês e Fee Gestão
df_faturamento_mes_casa['Valor Bruto'] = pd.to_numeric(df_faturamento_mes_casa['Valor Bruto'], errors='coerce')
valor_fat_bruto_mes = (df_faturamento_mes_casa[
    (df_faturamento_mes_casa['Ano'] == ano_selecionado) &
    (df_faturamento_mes_casa['Mês'] == mes_selecionado)
])['Valor Bruto'].sum()

df_faturamento_mes_casa['Valor Bruto'] = pd.to_numeric(df_faturamento_mes_casa['Valor Bruto'], errors='coerce')
df_valor_fee_gestao = df_faturamento_mes_casa.groupby(['ID_Casa', 'Casa', 'Mês', 'Ano'], as_index=False)['Valor Bruto'].sum()
df_valor_fee_gestao['Valor Bruto'] = df_valor_fee_gestao['Valor Bruto'] * PORC_FEE_GESTAO
df_valor_fee_gestao['Classificacao_Contabil_1'] = 'Sistema de Franquias'
df_valor_fee_gestao['Classificacao_Contabil_2'] = 'Fee Gestão FB'

# Cria combinação das categorias de faturamento com meses do ano (desde 2025)
df_meses_futuros_com_categorias = lista_meses_ano(lista_itens_faturamento)

# Gera projeção para prox meses do ano
df_faturamento_meses_futuros = projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'], datas['mes_atual'])
df_faturamento_meses_futuros = projecao_faturamento_servico_meses_seguintes(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

# Calcula Impostos sobre Venda
df_faturamento_para_impostos = df_faturamento_meses_futuros.copy()
df_parametros_impostos_venda = df_parametros_impostos[(df_parametros_impostos['Casa'] == casa) & (df_parametros_impostos['Classificacao_Contabil_1'] == 'Impostos sobre Venda')].copy()
lista_impostos_venda = df_parametros_impostos_venda['Classificacao_Contabil_2'].unique().tolist()
lista_impostos_venda = lista_impostos_venda + ['PIS / COFINS']
# Coloca ICMS na segunda posição
lista_impostos_venda.remove('ICMS')
lista_impostos_venda.insert(1, 'ICMS') 
df_impostos_meses_futuros = lista_meses_ano(lista_impostos_venda)

df_projecao_impostos_venda = projecao_impostos_venda(df_faturamento_para_impostos, lista_impostos_venda, df_impostos_meses_futuros, df_parametros_impostos_venda, casa)
df_impostos_venda_dre = formata_impostos_para_dre(df_projecao_impostos_venda, df_orcamentos, casa, mes_selecionado, ano_selecionado, 'Impostos sobre Venda')

# Calcula Impostos de Renda
df_faturamento_para_impostos = df_faturamento_meses_futuros.copy()
df_parametros_impostos_renda = df_parametros_impostos[(df_parametros_impostos['Casa'] == casa) & (df_parametros_impostos['Classificacao_Contabil_1'] == 'Imposto de Renda')].copy()
lista_impostos_renda = df_parametros_impostos_renda['Classificacao_Contabil_2'].unique().tolist()
lista_impostos_renda = lista_impostos_renda + ['IRPJ Total', 'CSLL Total']
df_impostos_meses_futuros = lista_meses_ano(lista_impostos_renda)

df_projecao_impostos_renda = projecao_impostos_renda(df_faturamento_para_impostos, lista_impostos_renda, df_impostos_meses_futuros, df_parametros_impostos_renda, casa)
df_impostos_renda_dre = formata_impostos_para_dre(df_projecao_impostos_renda, df_orcamentos, casa, mes_selecionado, ano_selecionado, 'Imposto de Renda')


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

df_parametros_mdo_casa = df_parametros_impostos[
    (df_parametros_impostos['Casa'] == casa) & 
    (df_parametros_impostos['Classificacao_Contabil_1'] == 'Mão de Obra - Encargos e Provisões')
].copy()

lista_df_projecao_despesas, df_gorjeta, df_salarios = loop_prepara_dados_despesas(
    lista_categorias_despesas,
    df_descontos, 
    df_consumo_interno_cmv,
    df_consumo_cartao_black,
    df_aut_blue_me_sem_pedido, 
    df_aut_blue_me_com_pedido,
    df_faturamento_meses_futuros, 
    df_aut_folha, 
    df_orcamentos, 
    df_demais_receitas_extr,
    df_ajustes_manuais,
    df_parametros_mdo_casa,
    df_valor_fee_gestao,
    lista_df_projecao_despesas, 
    casa, 
    mes_selecionado, 
    ano_selecionado
)

# Atualiza layout dos impostos de renda: inclui SIMPLES no df 
if casa not in ['Arcos', 'Love Cabaret', 'Ultra Evil Premium Ltda ']: # Não calculam SIMPLES
    df_impostos_renda_dre = projecao_imposto_simples(df_gorjeta, df_salarios, df_faturamento_para_impostos, df_aliquotas_imp_simples, df_impostos_renda_dre, mes_selecionado, ano_selecionado, casa)
# Recalcula total da categoria incluido o SIMPLES
df_impostos_renda_dre = df_impostos_renda_dre[df_impostos_renda_dre['Categoria'] != 'Imposto de Renda'].copy()
df_impostos_renda_dre = df_impostos_renda_dre.sort_values(by=['Categoria'], ascending=True)
df_impostos_renda_dre = calcula_linha_total(df_impostos_renda_dre, 'Categoria', 'Imposto de Renda', 'Valor Projetado', 'Valor Real')


# Prepara layout DRE
df_despesas_concatenadas = pd.concat(lista_df_projecao_despesas, ignore_index=True)

df_layout_dre = aplica_layout_dre(
    df_faturamento_meses_futuros, 
    df_impostos_venda_dre, 
    df_impostos_renda_dre,
    df_cmv_meses_anteriores_seguintes, 
    df_despesas_concatenadas, 
    mes_selecionado, 
    ano_selecionado
)

# Remove linhas que não quero exibir ou renomeia
df_layout_dre = df_layout_dre[~df_layout_dre['Categoria'].isin(['Patrocínio', 'Endividamento', 'Custas Cartório / Operação'])].reset_index(drop=True)
df_layout_dre['Categoria'] = df_layout_dre['Categoria'].replace({
    'Dividendos e Remunerações Variáveis': '(+/-) Outras variações no fluxo de caixa',
    'Despesas Financeiras': '(+/-) Receitas/Despesas Financeiras',
    'Investimento - CAPEX': '(-) CAPEX (Investimentos)',
    'Imposto de Renda': '(-) Impostos',
})

mapa_insercao = { # Mapeamentos manuais         
    'PESSOAL': '  -  Vale-transporte', 
    'RECEITA LÍQUIDA': 'ISS',                                     
}

# Mapeia automaticamente última linha de cada class. cont. 1 para inserção das linhas de '% sobre Receita'
for df in lista_df_projecao_despesas:
    lista_class_cont_1 = df[~df['Classificacao_Contabil_2'].isna()]['Classificacao_Contabil_2'].unique().tolist()
    if lista_class_cont_1:
        class_cont_1 = lista_class_cont_1[0] # Nome da class. cont. 1
        
        if class_cont_1 not in ['Mão de Obra - PJ', 'Mão de Obra - Salários', 'Mão de Obra - Extra', 'Mão de Obra - Encargos e Provisões', 'Mão de Obra - Benefícios', 'Patrocínio', 'Despesas Financeiras', 'Investimento - CAPEX']:
            ordem_class_cont_2 = df['Classificacao_Contabil_2'].unique().tolist()
            ordem_class_cont_2 = [class_cont_2 for class_cont_2 in ordem_class_cont_2 if class_cont_2 != class_cont_1]
            ordem_class_cont_2.sort() # Ordena lista de class. cont. 2
            mapa_insercao[class_cont_1] = ordem_class_cont_2[-1] # Última class. cont. 2

colunas_valores = (df_layout_dre.select_dtypes(include='number').drop(columns=['Percentual Real (do Orçamento)']).columns)
df_layout_dre = define_linhas_calculadas(df_layout_dre, colunas_valores, lista_categorias_despesas, mapa_insercao)

# Formata colunas numéricas
colunas_moeda_variavel = ['Orçamento', 'Valor Projetado', 'Valor Real']
colunas_percentuais = ['Percentual Projetado', 'Percentual Real (do Orçamento)']
linhas_percentual = df_layout_dre['Categoria'].str.contains('%', na=False) & (df_layout_dre['Categoria'] != 'IRPJ 10%')

df_layout_dre_styled = ( # Aplica formatações e estilos
    df_layout_dre.style
    .format(formatar_colunas_porcentagem, subset=colunas_percentuais)
    .format(formatar_linhas_porcentagem, subset=pd.IndexSlice[linhas_percentual, colunas_moeda_variavel])
    .format(formatar_colunas_moeda_br,subset=pd.IndexSlice[~linhas_percentual, colunas_moeda_variavel])
    .apply(highlight_secoes_dre, axis=1) # Destaca linhas de título
)

height = (len(df_layout_dre) + 1) * 35 # Define altura do df sem rolagem

with st.container(border=True): # Expprtando em Excel
    st.subheader(f'Fazer download - Excel DRE {casa}')
    excel_filename = f'assets/sheets/Base_DRE - {id_casa}.xlsx'

    # st.write("Arquivo:", excel_filename) # Verificação do arquivo
    # st.write("Existe:", os.path.exists(excel_filename))
    # st.write("Tamanho:", os.path.getsize(excel_filename))

    # try:
    #     wb = openpyxl.load_workbook(excel_filename)
    # except Exception:
    #     st.code(traceback.format_exc())

    # Casas com mais de um place
    if casa == 'Blue Note - São Paulo': ids_casa_query = [110, 131]
    elif casa == 'Priceless': ids_casa_query = [149, 161, 162, 179]
    elif casa == 'Girondino': ids_casa_query = [156, 160]
    else: ids_casa_query = [id_casa]

    ids_casa_query = ",".join(map(str, ids_casa_query)) # Formata para utilizar na query

    # Casas com delivery
    if casa == 'Bar Brahma - Centro': ids_casa_delivery = [117, 118]
    elif casa == 'Bar Léo - Centro': ids_casa_delivery = [103]
    elif casa == 'Bar Brahma - Granja': ids_casa_delivery = [169]
    elif casa == 'Jacaré': ids_casa_delivery = [139]
    elif casa == 'Orfeu': ids_casa_delivery = [112]
    else: ids_casa_delivery = None

    arquivo_pronto = prepara_download_excel(casa, ids_casa_query, excel_filename, ids_casa_delivery=ids_casa_delivery)
    if arquivo_pronto and os.path.exists(excel_filename):
        st.success('Arquivo atualizado com sucesso!')
        with open(excel_filename, "rb") as file:
            file_content = file.read()
            st.download_button( # Botão de Download 
            label="Baixar Excel",
            data=file_content,
            file_name=f"DRE - {casa}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Exibe df de Forecast no layout DRE            
st.divider()
st.subheader('Real vs Tendência do mês - Faturamento e Despesas')
st.dataframe(df_layout_dre_styled, hide_index=True, width='stretch', height=height)

# Premissas
# Falta ajustar Benefícios e Outros B (Mão de Obra - Benefícios)
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

