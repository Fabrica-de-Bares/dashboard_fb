import streamlit as st
import pandas as pd
from st_aggrid import ColumnsAutoSizeMode
from utils.functions.general_functions_conciliacao import *
from utils.functions.fluxo_futuro import *
from utils.functions.general_functions import config_sidebar
from utils.components import dataframe_aggrid, input_multiselecao_casas
from utils.queries_conciliacao import *


st.set_page_config(
    page_title="Fluxo Futuro",
    page_icon="🔮",
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
    st.title("🔮 Fluxo Futuro")
with col2:
    st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
st.divider()

# Recuperando dados
df_casas = GET_CASAS()
df_orcamentos = GET_ORCAMENTOS()
df_faturamento_agregado = GET_FATURAMENTO_AGREGADO()
df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
df_eventos_faturam_agregado = GET_EVENTOS_FATURAM_AGREGADO()
df_despesas_sem_parcelamento = GET_CUSTOS_BLUEME_SEM_PARC()
df_despesas_com_parcelamento = GET_CUSTOS_BLUEME_COM_PARC()
df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()


# Calculando datas
datas = calcular_datas()
min_data = datetime.date(2024, 1, 1)
max_data = datetime.date(datas['ano_atual'] + 1, 12, 31)

# Filtrando por casa(s) e data
casas = df_casas['Casa'].tolist()

# Troca o valor na lista
casas = ["Todas as casas" if c == "All bar" else c for c in casas]


# Criando colunas para o seletor de casas e o botão
col_casas, col_botao = st.columns([4, 2])

with col_casas:
    # Usando session_state se disponível, senão usa o valor padrão
    default_casas = st.session_state.get('casas_selecionadas', [casas[1]] if casas else [])
    lista_casas_retirar = ['Todas as Casas']
    df_casas_selecionadas = input_multiselecao_casas(lista_casas_retirar, key="casas_artistico")
    casas_selecionadas = df_casas_selecionadas['Casa'].tolist()

with col_botao:
    st.markdown("<br>", unsafe_allow_html=True)  # para alinhar o botão com os widgets
    if st.button("🏢 Sem Sócios Externos", 
                 help="Seleciona automaticamente todas as casas que não possuem sócios externos (Bit_Socios_Externos = 0)", 
                 width='stretch'):
        
        # Filtrando casas sem sócios externos
        casas_sem_socios_externos = df_casas[df_casas['Bit_Socios_Externos'] == 0]['Casa'].tolist()
        casas_sem_socios_externos = [c for c in casas_sem_socios_externos if c != 'All bar']

        # Atualizando o multiselect através do session_state
        st.session_state['casas_selecionadas'] = casas_sem_socios_externos

        # Limpando a chave do multiselect para forçar a atualização
        if 'casas_multiselect' in st.session_state:
            del st.session_state['casas_multiselect']
        st.rerun()
    
    # Mostrando informação sobre casas sem sócios externos
    total_casas_sem_socios = len(df_casas[df_casas['Bit_Socios_Externos'] == 0]) - 1
    st.caption(f"📊 {total_casas_sem_socios} casas sem sócios externos")

# Definindo um dicionário para mapear nomes de casas a IDs de casas
mapeamento_lojas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

# Obtendo os IDs das casas selecionadas
ids_casas_selecionadas = []
casas_selecionadas = [casa for casa in casas_selecionadas if casa not in ['Blue Note SP (Sala 2)', 'Terraço Notie']]
for casa in casas_selecionadas:
    if casa == "Todas as Casas":
        # pega todos os IDs exceto o "All bar"
        todas_ids = df_casas.loc[df_casas["Casa"] != "All bar", "ID_Casa"].tolist()
        ids_casas_selecionadas.extend(todas_ids)
    else:
        ids_casas_selecionadas.append(mapeamento_lojas[casa])
st.divider()

# Campos de seleção de data
col1, col2 = st.columns(2)
with col1:
    if datas['mes_atual'] == 12:
        value_inicio=datas['inicio_mes_atual']
    else:
        value_inicio=datas['mes_seguinte']
    start_date = st.date_input(
        "Data de início", 
        value=value_inicio, 
        min_value=min_data, 
        max_value=max_data, 
        format="DD/MM/YYYY",
        key='start_date')
with col2:
    end_date = st.date_input(
        "Data de fim", 
        value=datas['ultimo_dia_ano'], 
        min_value=min_data, 
        max_value=max_data, 
        format="DD/MM/YYYY",
        key='end_date')

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

if not casas_selecionadas:
    st.warning("Por favor, selecione pelo menos uma casa.")
    st.stop()

st.divider()

## Exibe Orçamentos e Faturamento com eventos
df_orcamentos, df_orcamentos_filtrada, df_faturamento_com_eventos = exibe_orcamentos_e_faturamento(
    df_orcamentos, 
    df_faturamento_agregado, df_eventos_faturam_agregado, 
    ids_casas_selecionadas, start_date, end_date
)

st.divider()

## Configuração do Fator de Ajuste
st.subheader("📅 Configuração do Fator de Ajuste")

col1, col2 = st.columns(2)
with col1:
    fator_ajuste_data_inicio = st.date_input(
        "Data de início para cálculo do fator de ajuste:",
        value=datas['jan_ano_atual'],
        min_value=datas['jan_ano_passado'],
        max_value=datas['ultimo_dia_mes_anterior'],
        format="DD/MM/YYYY",
        key="fator_ajuste_start_date_input_widget"    
    )
    
with col2:
    fator_ajuste_data_fim = st.date_input(
        "Data de fim para cálculo do fator de ajuste:",
        value=datas['ultimo_dia_mes_anterior'],
        min_value=datas['jan_ano_passado'],
        max_value=datas['ultimo_dia_mes_anterior'],
        format="DD/MM/YYYY",
        key="fator_ajuste_end_date_input_widget",
        help="Selecione o período histórico que será usado para calcular o fator de ajuste baseado no desempenho orçado vs realizado."
    )

data_inicio_analise = pd.to_datetime(fator_ajuste_data_inicio)
data_limite_analise = pd.to_datetime(fator_ajuste_data_fim)
st.write("")

## Análise Comparativa: Orçado vs Realizado
with st.container(border=True):
    st.markdown(f"""
        <h3 style="color: #1f77b4; font-weight: bold;">Análise Comparativa: Orçado vs Realizado</h3>
        <h5 style="color: #1f77b4;">{data_inicio_analise.strftime('%d/%m/%Y')} a {data_limite_analise.strftime('%d/%m/%Y')}</h5>
        """, unsafe_allow_html=True)

    percentual_medio, fator_ajuste = analise_orcado_realizado(
        df_orcamentos, df_faturamento_com_eventos, 
        data_inicio_analise, data_limite_analise, 
        casas_selecionadas
    )
    
st.divider()

## Projeção de Receitas de Patrocínios 
with st.container(border=True):
    st.markdown(f"""
        <h3 style="color: #1f77b4; font-weight: bold;">Projeção de Receitas (com Patrocínios)</h3>
        <h5 style="color: #1f77b4;">{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</h5>
        """, unsafe_allow_html=True)

    df_orcamentos_futuros, patrocinios_mensais = projecao_receitas_patrocinios(
        df_parc_receit_extr, df_orcamentos, 
        percentual_medio, fator_ajuste,
        ids_casas_selecionadas, start_date, end_date
    )

st.divider()

## Projeção de Despesas Futuras - Por Tipo de Fluxo
with st.container(border=True):
    st.markdown(f"""
        <h3 style="color: #1f77b4; font-weight: bold;">Projeção de Despesas Futuras - Por Tipo de Fluxo</h3>
        <h5 style="color: #1f77b4;">{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</h5>
        """, unsafe_allow_html=True)
    
    df_projecoes_consolidadas = projecao_despesas_futuras(
        df_despesas_sem_parcelamento, df_despesas_com_parcelamento, df_orcamentos,
        df_tipo_class_cont_2, fator_ajuste,
        ids_casas_selecionadas, start_date, end_date)

st.divider()

## Projeção Avançada por Mês - Receitas vs Despesas
with st.container(border=True):
    st.markdown(f"""
            <h3 style="color: #1f77b4; font-weight: bold;">Projeção Avançada por Mês - Receitas vs Despesas</h3>
            <h5 style="color: #1f77b4;">{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</h5>
            """, unsafe_allow_html=True)

    projecao_avancada_receitas_despesas(
        df_projecoes_consolidadas, df_orcamentos_futuros, df_orcamentos_filtrada,
        patrocinios_mensais, casas_selecionadas
    )

st.divider()

## Fatores de Ajuste por Casa
col1, col2 = st.columns([6, 1])
with col1:
    st.subheader("Fatores de Ajuste por Casa")
    st.markdown("**Análise de Performance: Orçado vs Realizado**")

# Calculando fatores de ajuste por casa individual
fatores_por_casa = []

for casa in casas_selecionadas:
    if casa == 'Todas as casas':
        casas_para_processar = list(mapeamento_lojas.keys())  # todas as casas do mapeamento
        casas_para_processar = [c for c in casas_para_processar if c != 'All bar']
    else:
        casas_para_processar = [casa]

    for c in casas_para_processar:
        casa_id = mapeamento_lojas[c]
        casas_ids = [casa_id]  # lista com o(s) ID(s) para filtro
        casa_label = c  # label da casa para exibir na tabela
    
        # Filtrando dados de orçamento para esta casa usando o filtro de data personalizado
        data_inicio_analise_casa = data_inicio_analise
        data_limite_analise_casa = data_limite_analise
        
        df_orcamentos_casa = df_orcamentos[
            (df_orcamentos['ID_Casa'].isin(casas_ids)) &
            (df_orcamentos['Data_Orcamento'] >= data_inicio_analise_casa) &
            (df_orcamentos['Data_Orcamento'] <= data_limite_analise_casa) &
            (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
        ]
        
        # Filtrando dados de faturamento para esta casa
        df_faturamento_casa = df_faturamento_com_eventos[
            (df_faturamento_com_eventos['ID_Casa'].isin(casas_ids))
        ]
        
        if not df_orcamentos_casa.empty and not df_faturamento_casa.empty:
            # Agrupando orçamentos por mês para esta casa
            orcamentos_casa_mensais = df_orcamentos_casa.groupby(['Ano_Orcamento', 'Mes_Orcamento'])['Valor_Orcamento'].sum().reset_index()
            orcamentos_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                orcamentos_casa_mensais['Ano_Orcamento'].astype(str) + '-' + 
                orcamentos_casa_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
            )
            
            # Agrupando faturamento por mês para esta casa
            faturamento_casa_mensais = df_faturamento_casa.groupby('Ano_Mes')['Valor_Bruto'].sum().reset_index()
            faturamento_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                faturamento_casa_mensais['Ano_Mes'] + '-01'
            )
            
            # Merge dos dados para comparação desta casa
            df_comparacao_casa = pd.merge(
                orcamentos_casa_mensais[['Data_Comparacao', 'Valor_Orcamento']],
                faturamento_casa_mensais[['Data_Comparacao', 'Valor_Bruto']],
                on='Data_Comparacao',
                how='left'
            ).fillna(0)
            
            # Calculando percentual realizado para esta casa
            df_comparacao_casa['Percentual_Realizado'] = df_comparacao_casa.apply(
                lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
                axis=1
            ).fillna(0)
            
            # Calculando métricas para esta casa
            total_orcado_casa = df_comparacao_casa['Valor_Orcamento'].sum()
            total_realizado_casa = df_comparacao_casa['Valor_Bruto'].sum()
            percentual_medio_casa = df_comparacao_casa['Percentual_Realizado'].mean()
            
            # Calculando fator de ajuste para esta casa
            if percentual_medio_casa > 0:
                fator_ajuste_casa = min(percentual_medio_casa / 100, 1.0)
            else:
                fator_ajuste_casa = 1.0
            
            # Classificando performance
            if percentual_medio_casa >= 110:
                classificacao = "🟢 Excelente"
                cor_classificacao = "green"
            elif percentual_medio_casa >= 100:
                classificacao = "🟡 Boa"
                cor_classificacao = "orange"
            elif percentual_medio_casa >= 90:
                classificacao = "🟠 Atenção"
                cor_classificacao = "red"
            else:
                classificacao = "🔴 Crítica"
                cor_classificacao = "darkred"
            
            # Adicionando à lista de fatores
            fatores_por_casa.append({
                'Casa': casa_label,
                'Total_Orcado': total_orcado_casa,
                'Total_Realizado': total_realizado_casa,
                'Percentual_Realizado': percentual_medio_casa,
                'Fator_Ajuste': fator_ajuste_casa,
                'Classificacao': classificacao,
                'Meses_Analisados': len(df_comparacao_casa)
            })
        else:
            # Caso não haja dados suficientes
            fatores_por_casa.append({
                'Casa': casa_label,
                'Total_Orcado': 0,
                'Total_Realizado': 0,
                'Percentual_Realizado': 0,
                'Fator_Ajuste': 1.0,
                'Classificacao': "⚪ Sem dados",
                'Meses_Analisados': 0
            })

# Criando DataFrame com os fatores
df_fatores_ajuste = pd.DataFrame(fatores_por_casa)

if not df_fatores_ajuste.empty:
    # Formatando colunas para exibição
    df_fatores_display = df_fatores_ajuste.copy()
    df_fatores_display['Fator_Ajuste'] = df_fatores_display['Fator_Ajuste'].apply(lambda x: f"{x:.3f}")
    
    # Renomeando colunas
    df_fatores_display.columns = [
        'Casa', 
        'Total Orçado (R$)', 
        'Total Realizado (R$)', 
        'Realizado/Orçado (%)', 
        'Fator de Ajuste', 
        'Classificação', 
        'Meses Analisados'
    ]
    
    # Exibindo tabela 
    fatores_aggrid, tam_fatores_aggrid = dataframe_aggrid(
        df=df_fatores_display,
        name="Fatores de Ajuste por Casa",
        num_columns=["Total Orçado (R$)", "Total Realizado (R$)"],
        percent_columns=["Realizado/Orçado (%)"],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True
    )
    
    with col2:
        function_copy_dataframe_as_tsv(fatores_aggrid)

    st.divider()
    
    # Métricas resumidas
    st.subheader(":material/heap_snapshot_large: Métricas gerais")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        media_percentual = df_fatores_ajuste['Percentual_Realizado'].mean()
        media_percentual_fmt = format_brazilian(media_percentual)
        st.metric("Média Realizado/Orçado", f"{media_percentual_fmt}%")
    
    with col2:
        media_fator = df_fatores_ajuste['Fator_Ajuste'].mean()
        media_fator_fmt = format_brazilian(media_fator)
        st.metric("Fator de Ajuste Médio", f"{media_fator_fmt}")
    
    with col3:
        casas_excelentes = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] >= 110])
        total_casas = len(df_fatores_ajuste)
        st.metric("Casas Excelentes", f"{casas_excelentes}/{total_casas}")
    
    with col4:
        casas_criticas = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] < 90])
        st.metric("Casas Críticas", f"{casas_criticas}/{total_casas}")
    
    st.divider()

    # Legenda das classificações
    st.markdown("**📝 Legenda das Classificações:**")
    st.markdown("""
    - 🟢 **Excelente**: Realizado ≥ 110% do orçado
    - 🟡 **Boa**: Realizado entre 100% e 109% do orçado  
    - 🟠 **Atenção**: Realizado entre 90% e 99% do orçado
    - 🔴 **Crítica**: Realizado < 90% do orçado
    - ⚪ **Sem dados**: Dados insuficientes para análise
    """)
    
    # Explicação do fator de ajuste
    st.markdown("**💡 Sobre o Fator de Ajuste:**")
    st.markdown("""
    O fator de ajuste é calculado com base no histórico de realização vs orçamento de cada casa no período selecionado. 
    - **Fator = 1.000**: Casa atingiu 100% ou mais do orçado (projeção otimista mantida)
    - **Fator < 1.000**: Casa realizou menos que 100% do orçado (projeção ajustada para baixo)
    
    Este fator é aplicado nas projeções futuras para tornar as estimativas mais realistas.
    O período histórico usado para o cálculo pode ser configurado na seção "Configuração do Fator de Ajuste".
    """)

else:
    st.warning("Não foi possível calcular os fatores de ajuste para as casas selecionadas.")

