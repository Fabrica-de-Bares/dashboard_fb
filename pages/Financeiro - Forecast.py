import streamlit as st
from utils.components import input_selecao_casas
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import *
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import *


st.set_page_config(
    page_title="Forecast",
    page_icon=":material/event_upcoming:",
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
    st.title(":material/event_upcoming: Forecast")
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


# Seletor de casa
lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Todas as Casas']
id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
  
tab1, tab2, tab3 = st.tabs(['Projeção Faturamento - Mês corrente', 'Projeção Faturamento - Próximos meses', 'Projeção - Despesas'])

###################### PROJEÇÃO DE FATURAMENTO - MÊS CORRENTE ###################### 
with tab1:
    st.markdown(f'''
        <h3>Projeções - {casa} - {datas['amanha'].strftime('%d/%m/%Y')} a {datas['fim_mes_atual'].strftime('%d/%m/%Y')}</h3>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado diário para a casa selecionada
    df_faturamento_agregado_mes_corrente = prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, datas['fim_mes_atual'], datas['inicio_dois_meses_antes'])
    
    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
    df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(
        datas['ano_atual'], datas['mes_atual'], 
        df_faturamento_agregado_mes_corrente)
    
    # Gera projeção para prox dias do mês corrente por dia da semana
    df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias)
    
    # Container que exibe projeção dos prox dias do mês corrente
    with st.container(border=True):
        st.markdown(f'''
            <h4>Faturamentos por categoria</h4>
            <p><strong>Premissa</strong> (para todas as categorias de faturamento, exceto 'Eventos' e 'Outras Receitas'): por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</p>
            ''', unsafe_allow_html=True)

        exibe_faturamento_categoria_mes_corrente('A&B', df_dias_futuros_mes, 'dias seguintes', datas)
        exibe_faturamento_categoria_mes_corrente('Gifts', df_dias_futuros_mes, 'dias seguintes', datas)
        exibe_faturamento_categoria_mes_corrente('Delivery', df_dias_futuros_mes, 'dias seguintes', datas)
        exibe_faturamento_categoria_mes_corrente('Couvert', df_dias_futuros_mes, 'dias seguintes', datas)
        exibe_faturamento_eventos(df_faturamento_eventos, id_casa, datas)
        exibe_faturamento_outras_receitas(df_parc_receit_extr_dia, df_parc_receitas_extr_categoria, id_casa, datas)

    st.divider()
        
    # Container que exibe faturamento real e projetado dos dias anteriores do mês corrente
    with st.container(border=True):
        exibe_faturamento_categoria_mes_corrente('Dias anteriores', df_dias_futuros_mes, 'dias anteriores', datas)


###################### PROJEÇÃO DE FATURAMENTO - PRÓXIMOS MESES ###################### 
with tab2:    
    st.markdown(f'''
        <h3>Projeções - {casa} - Próximos meses</h3>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado mensal para a casa selecionada
    df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, datas['ano_passado'], datas['ano_atual'])

    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x MESES (ano corrente) ---
    df_meses_futuros_com_categorias = lista_meses_ano(df_faturamento_mes_casa, datas['ano_atual'], datas['ano_passado'])
    
    # Gera projeção para prox meses do ano
    df_faturamento_meses_futuros = projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'], datas['mes_atual'])
    
    # Container que exibe projeção dos prox meses
    with st.container(border=True):
        st.markdown(f'''
            <h4>Faturamentos por categoria</h4>
            <p><strong>Premissa</strong> (para todas as categorias de faturamento): média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</p>
            ''', unsafe_allow_html=True)

        exibe_categoria_faturamento_prox_meses('A&B', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Gifts', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Delivery', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Couvert', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Eventos', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Outras Receitas', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    st.divider()
   
    # Container que exibe faturamento e CMV real e projetado dos meses anteriores 
    with st.container(border=True):
        exibe_faturamento_meses_anteriores(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

###################### DESPESAS - PRÓXIMOS MESES ###################### 
with tab3:
    st.markdown(f'''
        <h3>Projeções - {casa} - Próximos meses</h3>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara e exibe projeção de custos por categoria dos prox meses
    with st.container(border=True):
        st.markdown(f'''
            <h4>Despesas por categoria</h4>
            <p><strong>Premissa:</strong></p>
        ''', unsafe_allow_html=True)

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
        exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, 'meses seguintes', datas['mes_atual'], datas['ano_atual'])

        # Desconto sobre Venda (vem dos Descontos)
        df_descontos_mensais_passados = prepara_dados_custos_mensais(df_descontos, df_faturamento_meses_futuros, casa, 'Desconto sobre Venda')
        df_projecao_descontos_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_descontos_mensais_passados, 'Desconto sobre Venda', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_descontos_meses_anteriores_seguintes, 'Desconto sobre Venda', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Custos Artístico Geral
        df_custos_artistico_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Custos Artístico Geral', df_tabela_secundaria=df_descontos)
        df_projecao_custos_artistico_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_artistico_faturamentos_mensais_passados, 'Custos Artístico Geral', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_artistico_meses_anteriores_seguintes, 'Custos Artístico Geral', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Custos Eventos
        df_custos_eventos_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Custos de Eventos')
        df_projecao_custos_eventos_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_eventos_faturamentos_mensais_passados, 'Custos Eventos', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_eventos_meses_anteriores_seguintes, 'Custos de Eventos', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Dedução da Gorjeta
        df_deducao_gorjeta_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Gorjeta', df_tabela_secundaria=df_aut_folha)
        df_projecao_deducao_gorjeta_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_deducao_gorjeta_faturamentos_mensais_passados, 'Dedução da Gorjeta', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_deducao_gorjeta_meses_anteriores_seguintes, 'Dedução da Gorjeta', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Deduções sobre Venda
        df_deducoes_venda_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Deduções sobre Venda')
        df_projecao_deducoes_venda_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_deducoes_venda_faturamentos_mensais_passados, 'Deduções sobre Venda', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_deducoes_venda_meses_anteriores_seguintes, 'Deduções sobre Venda', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # PJ
        df_custos_pj_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Mão de Obra - PJ')
        df_projecao_custos_pj_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_pj_faturamentos_mensais_passados, 'PJ', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_pj_meses_anteriores_seguintes, 'Mão de Obra - PJ', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Salários
        df_custos_salarios_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Mão de Obra - Salários', df_tabela_secundaria=df_aut_folha)
        df_projecao_custos_salarios_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_salarios_faturamentos_mensais_passados, 'Salários', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_salarios_meses_anteriores_seguintes, 'Mão de Obra - Salários', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # E-Staff
        df_custos_estaff_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Mão de Obra - Extra')
        df_projecao_custos_estaff_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_estaff_faturamentos_mensais_passados, 'Mão de Obra - Extra', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_estaff_meses_anteriores_seguintes, 'E-Staff', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Custo de Ocupação
        df_custos_ocupacao_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Custo de Ocupação')
        df_projecao_custos_ocupacao_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_ocupacao_faturamentos_mensais_passados, 'Custo de Ocupação', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_ocupacao_meses_anteriores_seguintes, 'Custo de Ocupação', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Utilidades
        df_custos_utilidades_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Utilidades', df_aut_blue_me_com_pedido=df_aut_blue_me_com_pedido)
        df_projecao_custos_utilidades_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_utilidades_faturamentos_mensais_passados, 'Utilidades', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_utilidades_meses_anteriores_seguintes, 'Utilidades', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Informática e TI
        df_custos_informatica_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Informática e TI')
        df_projecao_custos_informatica_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_informatica_faturamentos_mensais_passados, 'Informática e TI', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_informatica_meses_anteriores_seguintes, 'Informática e TI', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Despesas Gerais (Manutenção)
        df_custos_manutencao_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Manutenção')
        df_projecao_custos_manutencao_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_manutencao_faturamentos_mensais_passados, 'Manutenção', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_manutencao_meses_anteriores_seguintes, 'Despesas Gerais (Manutenção)', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Marketing
        df_custos_marketing_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Marketing', df_tabela_secundaria=df_descontos)
        df_projecao_custos_marketing_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_marketing_faturamentos_mensais_passados, 'Marketing', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_marketing_meses_anteriores_seguintes, 'Marketing', 'meses seguintes', datas['ano_atual'], datas['mes_atual'])

        # Serviços de Terceiros
        df_custos_terceiros_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Serviços de Terceiros')
        df_projecao_custos_terceiros_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_terceiros_faturamentos_mensais_passados, 'Serviços de Terceiros', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_terceiros_meses_anteriores_seguintes, 'Serviços de Terceiros', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Locação de Equipamentos
        df_custos_equipamentos_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Locação de Equipamentos')
        df_projecao_custos_equipamentos_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_equipamentos_faturamentos_mensais_passados, 'Locação de Equipamentos', datas['ano_atual'], datas['mes_atual'])
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_equipamentos_meses_anteriores_seguintes, 'Locação de Equipamentos', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Sistema de Franquias
        df_custos_franquias_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_aut_blue_me_sem_pedido, df_faturamento_meses_futuros, casa, 'Sistema de Franquias')
        df_projecao_custos_franquias_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_franquias_faturamentos_mensais_passados, 'Sistema de Franquias', datas['ano_atual'], datas['mes_atual'])
        if casa == 'Blue Note - São Paulo':
            exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_franquias_meses_anteriores_seguintes, 'Sistema de Franquias', 'meses seguintes', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

    st.divider()

    # Prepara para exibir a projeção de custos dos meses anteriores - comparação
    with st.container(border=True):
        st.markdown(f'''
                <h4>Meses anteriores - Comparação: Custos Projetados e Custos Reais</h4>
            ''', unsafe_allow_html=True)
        
        # CMV
        exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, 'meses anteriores', datas['mes_atual'], datas['ano_atual'])
        
        # Desconto sobre Venda
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_descontos_meses_anteriores_seguintes, 'Desconto sobre Venda', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Custos Artístico Geral
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_artistico_meses_anteriores_seguintes, 'Custos Artístico Geral', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Custos Eventos
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_eventos_meses_anteriores_seguintes, 'Custos de Eventos', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Dedução da Gorjeta
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_deducao_gorjeta_meses_anteriores_seguintes, 'Dedução da Gorjeta', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Deduções sobre Venda
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_deducoes_venda_meses_anteriores_seguintes, 'Deduções sobre Venda', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # PJ
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_pj_meses_anteriores_seguintes, 'Mão de Obra - PJ', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Salários
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_salarios_meses_anteriores_seguintes, 'Mão de Obra - Salários', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # E-Staff
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_estaff_meses_anteriores_seguintes, 'E-Staff', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])
        
        # Custo de Ocupação
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_ocupacao_meses_anteriores_seguintes, 'Custo de Ocupação', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Utilidades
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_utilidades_meses_anteriores_seguintes, 'Utilidades', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Salários
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_informatica_meses_anteriores_seguintes, 'Informática e TI', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Despesas Gerais (Manutenção)
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_manutencao_meses_anteriores_seguintes, 'Despesas Gerais (Manutenção)', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Marketing
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_marketing_meses_anteriores_seguintes, 'Marketing', 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

        # Serviços de Terceiros
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_terceiros_meses_anteriores_seguintes, 'Serviços de Terceiros', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Locação de Equipamentos
        exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_equipamentos_meses_anteriores_seguintes, 'Locação de Equipamentos', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

        # Sistema de Franquias
        if casa == 'Blue Note - São Paulo':
            exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_franquias_meses_anteriores_seguintes, 'Sistema de Franquias', 'meses anteriores', datas['ano_atual'], datas['mes_atual'], igual_mes_anterior=True)

