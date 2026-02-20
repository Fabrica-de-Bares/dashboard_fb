import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from st_aggrid import ColumnsAutoSizeMode
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import mapeamento_class_cont
from utils.functions.general_functions import config_sidebar
from utils.functions.fluxo_realizado import *
from utils.queries_conciliacao import *
from utils.components import dataframe_aggrid, input_multiselecao_casas


st.set_page_config(
    page_title="Fluxo Realizado",
    page_icon=":material/currency_exchange:",
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
    st.title(":material/currency_exchange: Fluxo Realizado")
with col2:
    st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
st.divider()

# Recuperando dados
df_casas = GET_CASAS()
df_extrato_zig = GET_EXTRATO_ZIG()
df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
df_eventos = GET_EVENTOS()
df_mutuos = GET_MUTUOS()
df_bloqueios = GET_BLOQUEIOS_JUDICIAIS()
df_custos_blueme_sem_parcelam = GET_CUSTOS_BLUEME_SEM_PARC()
df_custos_blueme_com_parcelam = GET_CUSTOS_BLUEME_COM_PARC()


# Calculando Datas
datas = calcular_datas()
min_data = datetime.date(2024, 1, 1)
max_data = datetime.date(datas['ano_atual'] + 1, 12, 31)


# Filtrando por casa(s) e data
casas = df_casas['Casa'].tolist()

# Troca o valor na lista
casas = ["Todas as casas" if c == "All bar" else c for c in casas]


# Criando colunas para o seletor de casas e o botão
col_casas, col_botao = st.columns([4, 1])

with col_casas:
    # Usando session_state se disponível, senão usa o valor padrão
    default_casas = st.session_state.get('casas_selecionadas', [casas[1]] if casas else []) # default: Arcos
    lista_casas_retirar = ['Todas as Casas']
    df_casas_selecionadas = input_multiselecao_casas(lista_casas_retirar, key="casas_artistico")
    casas_selecionadas = df_casas_selecionadas['Casa'].tolist()

with col_botao:
    st.markdown("<br>", unsafe_allow_html=True)  # para alinhar o botão com os widgets
    if st.button(
        "🏢 Sem Sócios Externos", 
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
    if casa == "Todas as casas":
        # pega todos os IDs exceto o "All bar"
        todas_ids = df_casas.loc[df_casas["Casa"] != "All bar", "ID_Casa"].tolist()
        ids_casas_selecionadas.extend(todas_ids)
    else:
        ids_casas_selecionadas.append(mapeamento_lojas[casa])

# Usando session_state se disponível, senão usa o valor padrão
default_value = st.session_state.get('date_input', (datas['jan_ano_atual'], datas['fim_mes_atual']))

# Campos de seleção de data
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Data de início", 
        value=datas['jan_ano_atual'], 
        min_value=min_data, 
        max_value=max_data, 
        format="DD/MM/YYYY")
with col2:
    end_date = st.date_input(
        "Data de fim", 
        value=datas['fim_mes_atual'], 
        min_value=min_data, 
        max_value=max_data, 
        format="DD/MM/YYYY")

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

if not casas_selecionadas:
    st.warning("Por favor, selecione pelo menos uma casa.")
    st.stop()

st.divider()

## Receitas ##
st.markdown("""
    <h2 style="color: green; font-weight: bold;">Receitas</h2>
    """, unsafe_allow_html=True)

## Zig_Extrato
st.subheader("Extrato Zig")
df_extrato_zig_filtrada = filtra_df(df_extrato_zig, 'Data_Liquidacao', ids_casas_selecionadas, start_date, end_date)
df_extrato_zig_filtrada = df_extrato_zig_filtrada[['ID_Extrato','ID_Casa','Casa','Descricao','Data_Liquidacao','Data_Transacao','Valor']]

# Exibe df com aggrid
df_extrato_zig_filtrada_aggrid, tam_df_extrato_zig_filtrada_aggrid = dataframe_aggrid(
    df=df_extrato_zig_filtrada, 
    name='Extrato Zig', 
    num_columns=["Valor"],
    date_columns=['Data_Liquidacao', 'Data_Transacao'],
    key='teste_extrato_zig',
    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    fit_columns_on_grid_load=True
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_extrato_zig_filtrada_aggrid, tam_df_extrato_zig_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_extrato_zig_filtrada_aggrid)

st.divider()

## Parcelas Receitas Extraordinárias
st.subheader("Parcelas Receitas Extraordinárias")
df_parc_receit_extr_filtrada = filtra_df(df_parc_receit_extr, 'Recebimento_Parcela', ids_casas_selecionadas, start_date, end_date)

df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada.copy()
df_parc_receit_extr_filtrada_copia["Recebimento_Parcela"] = pd.to_datetime(df_parc_receit_extr_filtrada_copia["Recebimento_Parcela"], errors="coerce")
df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada_copia[
    ~(
        (df_parc_receit_extr_filtrada_copia["Classif_Receita"].str.lower() == "eventos") &
        (df_parc_receit_extr_filtrada_copia["Recebimento_Parcela"].dt.month >= 9)
    )
]

df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada_copia[['ID_Receita','ID_Casa','Casa','Cliente','Data_Ocorrencia','Vencimento_Parcela','Recebimento_Parcela','Valor_Parcela','Classif_Receita','Status_Pgto','Observacoes']]

# Exibe df com aggrid
df_parc_receit_extr_filtrada_aggrid, tam_df_parc_receit_extr_filtrada_aggrid = dataframe_aggrid(
    df=df_parc_receit_extr_filtrada_copia,
    name="Parcelas Receitas Extraordinárias",
    num_columns=["Valor_Parcela"],     
    date_columns=['Data_Ocorrencia', 'Vencimento_Parcela', 'Recebimento_Parcela'],             
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_parc_receit_extr_filtrada_aggrid, tam_df_parc_receit_extr_filtrada_aggrid, 'Valor_Parcela')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_parc_receit_extr_filtrada_aggrid)

st.divider()

## Eventos
st.subheader("Eventos")
df_eventos_filtrada = filtra_df(df_eventos, 'Recebimento_Parcela', ids_casas_selecionadas, start_date, end_date)
df_eventos_filtrada = df_eventos_filtrada[['ID_Evento', 'Nome_Evento', 'ID_Casa', 'Casa', 'ID_Parcela', 'Valor_Parcela', 'Vencimento_Parcela', 'Recebimento_Parcela', 'Status_Pgto', 'Forma_Pgto', 'Observacoes']]

# Exibe df com aggrid
df_eventos_filtrada_aggrid, tam_df_eventos_filtrada_aggrid = dataframe_aggrid(
    df=df_eventos_filtrada,
    name="Eventos",
    num_columns=["Valor_Parcela"],      
    date_columns=['Vencimento_Parcela', 'Recebimento_Parcela'],              
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_eventos_filtrada_aggrid, tam_df_eventos_filtrada_aggrid, 'Valor_Parcela')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_eventos_filtrada_aggrid)

st.divider()

## Desbloqueios Judiciais
st.subheader("Desbloqueios Judiciais")
df_desbloqueios_filtrada = filtra_df(df_bloqueios, 'Data_Transacao', ids_casas_selecionadas, start_date, end_date)
df_desbloqueios_filtrada = df_desbloqueios_filtrada[df_desbloqueios_filtrada['Valor'] > 0]
df_desbloqueios_filtrada = df_desbloqueios_filtrada[['ID_Bloqueio', 'ID_Casa', 'Casa', 'Data_Transacao', 'Valor', 'Observacao']]

# Exibe df com aggrid
df_desbloqueios_filtrada_aggrid, tam_df_desbloqueios_filtrada_aggrid = dataframe_aggrid(
    df=df_desbloqueios_filtrada,
    name="Desbloqueios Judiciais",
    num_columns=["Valor"],      
    date_columns=['Data_Transacao'],
    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    fit_columns_on_grid_load=True              
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_desbloqueios_filtrada_aggrid, tam_df_desbloqueios_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_desbloqueios_filtrada_aggrid)

st.divider()

## Despesas ## 
st.markdown("""
    <h2 style="color: #DC143C; font-weight: bold;">Despesas</h2>
    """, unsafe_allow_html=True)

## Custos BlueMe Sem Parcelamento
st.subheader("Despesas BlueMe Sem Parcelamento")
df_custos_blueme_sem_parcelam_filtrada = filtra_df(df_custos_blueme_sem_parcelam, 'Realizacao_Pgto', ids_casas_selecionadas, start_date, end_date)
df_custos_blueme_sem_parcelam_filtrada = df_custos_blueme_sem_parcelam_filtrada[['ID_Despesa','ID_Casa','Casa','Fornecedor','Valor','Data_Vencimento','Previsao_Pgto','Realizacao_Pgto','Data_Competencia','Class_Cont_1','Class_Cont_2','Status_Pgto']]

# Exibe df com aggrid
df_custos_blueme_sem_parcelam_filtrada_aggrid, tam_df_custos_blueme_sem_parcelam_filtrada_aggrid = dataframe_aggrid(
    df=df_custos_blueme_sem_parcelam_filtrada,
    name="Despesas BlueMe Sem Parcelamento",
    num_columns=["Valor"],      
    date_columns=['Data_Vencimento', 'Previsao_Pgto', 'Realizacao_Pgto', 'Data_Competencia'],
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_custos_blueme_sem_parcelam_filtrada_aggrid, tam_df_custos_blueme_sem_parcelam_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_custos_blueme_sem_parcelam_filtrada_aggrid)

st.divider()

## Custos BlueMe Com Parcelamento
st.subheader("Despesas BlueMe Com Parcelamento")
df_custos_blueme_com_parcelam_filtrada = filtra_df(df_custos_blueme_com_parcelam, 'Realiz_Parcela', ids_casas_selecionadas, start_date, end_date)
df_custos_blueme_com_parcelam_filtrada = df_custos_blueme_com_parcelam_filtrada[['ID_Parcela','ID_Despesa','Casa','ID_Casa','Fornecedor','Qtd_Parcelas','Num_Parcela','Valor_Parcela','Vencimento_Parcela','Realiz_Parcela','Valor_Original','Class_Cont_1','Class_Cont_2','Status_Pgto']]

# Exibe df com aggrid
df_custos_blueme_com_parcelam_filtrada_aggrid, tam_df_custos_blueme_com_parcelam_filtrada_aggrid = dataframe_aggrid(
    df=df_custos_blueme_com_parcelam_filtrada,
    name="Despesas Com Parcelamento",
    num_columns=["Valor_Parcela", "Valor_Original"],      
    date_columns=['Vencimento_Parcela', 'Realiz_Parcela'],
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calculando total dos valores filtrados
    total_valores_filtrados(df_custos_blueme_com_parcelam_filtrada_aggrid, tam_df_custos_blueme_com_parcelam_filtrada_aggrid, 'Valor_Parcela', despesa_com_parc=True)
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_custos_blueme_com_parcelam_filtrada_aggrid)

st.divider()

## Bloqueios Judiciais
st.subheader("Bloqueios Judiciais")
df_bloqueios_filtrada = filtra_df(df_bloqueios, 'Data_Transacao', ids_casas_selecionadas, start_date, end_date)
df_bloqueios_filtrada = df_bloqueios_filtrada[df_bloqueios_filtrada['Valor'] < 0]
df_bloqueios_filtrada = df_bloqueios_filtrada[['ID_Bloqueio', 'ID_Casa', 'Casa', 'Data_Transacao', 'Valor', 'Observacao']]

df_bloqueios_filtrada_aggrid, tam_df_bloqueios_filtrada_aggrid = dataframe_aggrid(
    df=df_bloqueios_filtrada,
    name="Bloqueios Judiciais",
    num_columns=["Valor"],      
    date_columns=['Data_Transacao'],
    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    fit_columns_on_grid_load=True              
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_bloqueios_filtrada_aggrid, tam_df_bloqueios_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_bloqueios_filtrada_aggrid)

st.divider()

## Mutuos ##
st.markdown("""
    <h2 style="color: orange; font-weight: bold;">Mútuos</h2>
    """, unsafe_allow_html=True)

## Entradas Mútuos
st.subheader("Entradas Mútuos")
df_entradas_mutuos_filtrada = filtra_df(df_mutuos, 'Data_Mutuo', ids_casas_selecionadas, start_date, end_date, entradas_mutuos=True)
df_entradas_mutuos_filtrada = df_entradas_mutuos_filtrada[['Mutuo_ID', 'ID_Casa_Entrada', 'Casa_Entrada', 'ID_Casa_Saida', 'Casa_Saida', 'Data_Mutuo', 'Valor', 'Observacoes']]

# Exibe df com aggrid
df_entradas_mutuos_filtrada_aggrid, tam_df_entradas_mutuos_filtrada_aggrid = dataframe_aggrid(
    df=df_entradas_mutuos_filtrada,
    name="Entradas Mútuos",
    num_columns=["Valor"],      
    date_columns=['Data_Mutuo'],
    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    fit_columns_on_grid_load=True              
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_entradas_mutuos_filtrada_aggrid, tam_df_entradas_mutuos_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_entradas_mutuos_filtrada_aggrid)

st.divider()

## Saidas Mútuos
st.subheader("Saídas Mútuos")
df_saidas_mutuos_filtrada = filtra_df(df_mutuos, 'Data_Mutuo', ids_casas_selecionadas, start_date, end_date, saidas_mutuos=True)
df_saidas_mutuos_filtrada = df_saidas_mutuos_filtrada[['Mutuo_ID', 'ID_Casa_Entrada', 'Casa_Entrada', 'ID_Casa_Saida', 'Casa_Saida', 'Data_Mutuo', 'Valor', 'Observacoes']]

# Exibe df com aggrid
df_saidas_mutuos_filtrada_aggrid, tam_df_saidas_mutuos_filtrada_aggrid = dataframe_aggrid(
    df=df_saidas_mutuos_filtrada,
    name="Saídas Mútuos",
    num_columns=["Valor"],      
    date_columns=['Data_Mutuo'],
    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    fit_columns_on_grid_load=True              
)

col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    # Calcula total dos valores filtrados
    total_valores_filtrados(df_saidas_mutuos_filtrada_aggrid, tam_df_saidas_mutuos_filtrada_aggrid, 'Valor')
with col2:
    # Botão para excel
    function_copy_dataframe_as_tsv(df_saidas_mutuos_filtrada_aggrid)

st.divider()

# Preparando dados para os gráficos - Fluxo de Caixa por Mês e Fluxo Líquido por Mês
df_consolidado = prepare_monthly_data(
    df_extrato_zig_filtrada, 
    df_parc_receit_extr_filtrada_copia, 
    df_eventos_filtrada, 
    df_desbloqueios_filtrada,
    df_custos_blueme_sem_parcelam_filtrada,
    df_custos_blueme_com_parcelam_filtrada,
    df_bloqueios_filtrada
)

## Gráfico Consolidado - Fluxo de Caixa por Mês
# st.subheader("Fluxo de Caixa Consolidado por Mês")

with st.container(border=True):
    col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment="center")
    with col2:
        st.write("")
        st.markdown("""
        <h2 style="color: #1f77b4; font-weight: bold;">Fluxo de Caixa Consolidado por Mês</h2>
        """, unsafe_allow_html=True)

        # Criando o gráfico
        try:
            if not df_consolidado.empty:
                # Criando gráfico de barras personalizado
                fig = go.Figure()
                
                # Obtendo todos os meses únicos
                meses_unicos = sorted(df_consolidado['Mes_Ano_Str'].unique())

                # Adicionando barras de receitas
                receitas_data = df_consolidado[df_consolidado['Categoria'] == 'Receitas']
                for tipo in receitas_data['Tipo'].unique():
                    dados_tipo = receitas_data[receitas_data['Tipo'] == tipo]
                    valores = []
                    for mes in meses_unicos:
                        valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                        valores.append(valor)
                        
                    if tipo == 'Extrato Zig': 
                        cor = "#245b3b" 
                        name = 'Receitas - Extrato Zig'
                    if tipo == 'Extraordinária': 
                        cor = "#2e8b57"
                        name = 'Receitas Extraordinárias'
                    if tipo == 'Eventos': 
                        cor = "#9ac5a8"
                        name = 'Receitas - Eventos'
                    if tipo == 'Desbloqueios': 
                        cor = '#32CD32'
                        name = 'Receitas - Desbloqueios Judiciais'

                    fig.add_trace(go.Bar(
                        x=meses_unicos,
                        y=valores,
                        name=name,
                        marker_color=cor,
                        offsetgroup='Receitas'
                    ))
                
                # Adicionando barras de despesas
                despesas_data = df_consolidado[df_consolidado['Categoria'] == 'Despesas']
                for tipo in despesas_data['Tipo'].unique():
                    dados_tipo = despesas_data[despesas_data['Tipo'] == tipo]
                    valores = []
                    for mes in meses_unicos:
                        valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                        valores.append(valor)
                    
                    if tipo == 'Sem Parcelamento': 
                        cor = "#b51b33" 
                        name = 'Despesas Sem Parcelamento'
                    if tipo == 'Com Parcelamento': 
                        cor = '#e95159'
                        name = 'Despesas Com Parcelamento'
                    if tipo == 'Bloqueios': 
                        cor = "#fa9b98"
                        name = 'Despesas - Bloqueios Judiciais'

                    fig.add_trace(go.Bar(
                        x=meses_unicos,
                        y=valores,
                        name=name,
                        marker_color=cor,
                        offsetgroup='Despesas'
                    ))

                # Personalizando o layout
                casas_titulo = ', '.join(casas_selecionadas) if len(casas_selecionadas) <= 3 else f"{len(casas_selecionadas)} casas selecionadas"
                fig.update_layout(
                    title=f'Fluxo de Caixa Consolidado - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
                    xaxis_title="Mês/Ano",
                    yaxis_title="Valor (R$)",
                    barmode='stack',
                    height=600,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    bargap=0.3,  # Espaço entre grupos de barras (meses)
                    bargroupgap=0.0  # Sem espaço entre barras do mesmo grupo (receitas e despesas do mesmo mês)
                )
                
                # Formatando eixo Y para moeda brasileira
                fig.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
                
                # Exibindo o gráfico
                st.plotly_chart(fig, width='stretch')
            
            else:
                st.warning("Não há dados disponíveis para o período e casas selecionadas.")

        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {str(e)}")

        st.divider()        

        ## Gráfico Consolidado - Fluxo Líquido por Mês
        # st.subheader("Fluxo Líquido por Mês")

        # Calculando fluxo líquido
        receitas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Receitas'].groupby('Mes_Ano_Str')['Valor'].sum()
        despesas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Despesas'].groupby('Mes_Ano_Str')['Valor'].sum()

        fluxo_liquido = pd.concat(
            [receitas_mensais.rename("Receitas"), despesas_mensais.rename("Despesas")],
            axis=1
        ).fillna(0).reset_index()

        fluxo_liquido['Fluxo_Liquido'] = fluxo_liquido['Receitas'] - fluxo_liquido['Despesas']
        # fluxo_liquido['Receitas'] = fluxo_liquido['Receitas'].fillna(0)
        # fluxo_liquido['Despesas'] = fluxo_liquido['Despesas'].fillna(0)

        # Gráfico de linha para fluxo líquido
        fig_liquido = go.Figure()

        fig_liquido.add_trace(go.Scatter(
            x=fluxo_liquido['Mes_Ano_Str'],
            y=fluxo_liquido['Fluxo_Liquido'],
            mode='lines+markers',
            name='Fluxo Líquido',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))

        fig_liquido.add_trace(go.Scatter(
            x=fluxo_liquido['Mes_Ano_Str'],
            y=fluxo_liquido['Receitas'],
            mode='lines+markers',
            name='Receitas Totais',
            line=dict(color='#2E8B57', width=2, dash='dash'),
            marker=dict(size=6)
        ))

        fig_liquido.add_trace(go.Scatter(
            x=fluxo_liquido['Mes_Ano_Str'],
            y=fluxo_liquido['Despesas'],
            mode='lines+markers',
            name='Despesas Totais',
            line=dict(color='#DC143C', width=2, dash='dash'),
            marker=dict(size=6)
        ))

        # Adicionando linha horizontal em y=0
        fig_liquido.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        fig_liquido.update_layout(
            title=f'Fluxo Líquido Mensal - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig_liquido.update_yaxes(tickformat=",.0f", tickprefix="R$ ")

        st.plotly_chart(fig_liquido, width='stretch')

        st.divider()


        ## Tabela - Receitas por Categoria
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Receitas por Categoria")
        
        df_receitas_categoria = df_consolidado[df_consolidado['Categoria'] == 'Receitas']
        df_receitas_categoria = df_receitas_categoria.drop(['Mes_Ano_Str', 'Categoria'], axis=1)

        if not df_receitas_categoria.empty:
            # Criando tabela dinâmica para Receitas por Categoria
            df_receitas_categoria = df_receitas_categoria.pivot(
                index='Tipo',
                columns='Mes_Ano',
                values='Valor'
            ).fillna(0)

        # Corrige nomes de colunas (se forem Period, converte para string)
        df_receitas_categoria.columns = df_receitas_categoria.columns.astype(str)

        # Adicionando coluna de total por categoria
        df_receitas_categoria['Total_Categoria'] = df_receitas_categoria.sum(axis=1)
        
        # Ordenando por total (maior para menor)
        df_receitas_categoria = df_receitas_categoria.sort_values('Total_Categoria', ascending=False)

        # Resetando o índice para incluir Tipo como coluna
        df_receitas_categoria = df_receitas_categoria.reset_index()

        colunas_numericas_receitas = [col for col in df_receitas_categoria.columns if col != 'Tipo']

        # Exibindo tabela
        df_receitas_categoria_aggrid, tam_df_receitas_categoria_aggrid = dataframe_aggrid(
            df=df_receitas_categoria,
            name="Receitas por Categoria",
            num_columns=colunas_numericas_receitas,
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        with col2:
            # Botão para copiar dados 
            function_copy_dataframe_as_tsv(df_receitas_categoria_aggrid)

        st.divider()

        ## Tabela Dinâmica - Despesas Class_Cont_0
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Despesas por Classificação")
            st.write('Considera Classificação Contábil (Class_Cont_0). Inclui bloqueios judiciais, se houver.')

        # Preparando dados para Class_Cont_0
        df_class0_data = prepare_pivot_data_class_despesas(
            df_custos_blueme_sem_parcelam_filtrada, 
            df_custos_blueme_com_parcelam_filtrada, 
            mapeamento_class_cont,
            classe=0
        )

        if not df_class0_data.empty:
            # Criando tabela dinâmica para Class_Cont_0
            pivot_table_class0 = df_class0_data.pivot(
                index='Class_Cont_0',
                columns='Mes_Ano',
                values='Valor'
            ).fillna(0)
            
            # Convertendo índices de coluna para string
            pivot_table_class0.columns = pivot_table_class0.columns.astype(str)
            
            # Adicionando coluna de total
            pivot_table_class0['Total'] = pivot_table_class0.sum(axis=1)
            
            # Ordenando por total (maior para menor)
            pivot_table_class0 = pivot_table_class0.sort_values('Total', ascending=False)
            
            # Resetando o índice para incluir Class_Cont_0 como coluna
            pivot_table_class0 = pivot_table_class0.reset_index()
            
            # Separando colunas numéricas das de texto
            colunas_numericas_class0 = [col for col in pivot_table_class0.columns if col != 'Class_Cont_0']
            pivot_table_class0 = pivot_table_class0.rename(columns={'Class_Cont_0':'Classificacao'})


            # Incluido bloqueios judiciais nas despesas
            df_despesas_bloqueios = df_bloqueios_filtrada.copy()
            df_despesas_bloqueios['Mes_Ano'] = df_despesas_bloqueios['Data_Transacao'].dt.strftime('%Y-%m')
            df_despesas_bloqueios['Valor'] *= (-1)
            df_despesas_bloqueios_mensais = df_despesas_bloqueios.groupby('Mes_Ano', as_index=False)['Valor'].sum()
            df_despesas_bloqueios_mensais['Classificacao'] = 'Bloqueios Judiciais'

            pivot_despesas_bloqueios_mensais = df_despesas_bloqueios_mensais.pivot(
                index='Classificacao',
                columns='Mes_Ano',
                values='Valor'
            ).fillna(0)

            # Adicionando coluna de total
            pivot_despesas_bloqueios_mensais['Total'] = pivot_despesas_bloqueios_mensais.sum(axis=1)

            # Resetando o índice para incluir Class_Cont_0 como coluna
            pivot_despesas_bloqueios_mensais = pivot_despesas_bloqueios_mensais.reset_index()

            df_todas_despesas = pd.concat([pivot_table_class0, pivot_despesas_bloqueios_mensais]).fillna(0)
            colunas_numericas_despesas = [c for c in df_todas_despesas if c != 'Classificacao']

            df_todas_despesas_aggrid, tam_df_todas_despesas_aggrid = dataframe_aggrid(
                df=df_todas_despesas,
                name="Despesas por Classificação (inclui bloqueios)",
                num_columns=colunas_numericas_class0,
                fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                fit_columns_on_grid_load=True,
                height = 800
            )

            with col2:
                # Botão para copiar dados de Class_Cont_0
                function_copy_dataframe_as_tsv(df_todas_despesas_aggrid)

        st.divider()
       
        # Calcula diferença entre receitas e despesas
        # st.subheader(":material/arrow_downward: Diferença: Receitas - Despesas")
        # st.write('Diferença bruta entre receitas e despesas mês a mês.')
        receitas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Receitas'].groupby('Mes_Ano')['Valor'].sum()
        despesas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Despesas'].groupby('Mes_Ano')['Valor'].sum()
        
        df_fluxo_liquido = pd.concat(
            [receitas_mensais.rename("Receitas"), despesas_mensais.rename("Despesas")],
            axis=1
        ).fillna(0).reset_index()

        df_fluxo_liquido['Diferença'] = df_fluxo_liquido['Receitas'] - df_fluxo_liquido['Despesas']

        # pivot_fluxo = df_fluxo_liquido.melt(
        #     id_vars='Mes_Ano',
        #     value_vars=['Receitas', 'Despesas', 'Diferença'],
        #     var_name='Categoria',
        #     value_name='Valor'
        # ).pivot(
        #     index='Categoria',
        #     columns='Mes_Ano',
        #     values='Valor'
        # ).fillna(0).reindex(['Receitas', 'Despesas', 'Diferença'])

        # # Convertendo índices de coluna para string
        # pivot_fluxo.columns = pivot_fluxo.columns.astype(str)

        # # Resetando o índice para incluir Class_Cont_0 como coluna
        # pivot_fluxo = pivot_fluxo.reset_index()

        # colunas_numericas_fluxo = [col for col in pivot_fluxo if col != 'Categoria']

        # # Exibindo tabela
        # df_pivot_fluxo_aggrid, tam_df_pivot_fluxo_aggrid = dataframe_aggrid(
        #     df=pivot_fluxo,
        #     name="Tabela - Receitas-Despesas",
        #     num_columns=colunas_numericas_fluxo,  
        #     highlight_rows=['Diferença'],
        #     fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        #     fit_columns_on_grid_load=True
        # )
        

        # Calcula saldo/fluxo de caixa
        st.subheader(":material/arrow_downward: Fluxo de Caixa")
        st.markdown("""
                    <h6>Receita ajustada = Receita total + Saldo do mês anterior</h6>
                    """, unsafe_allow_html=True)
        # st.write('O saldo de um mês é considerado no caixa do mês seguinte.')

        # Inicializa listas e saldo anterior
        df_saldo = df_fluxo_liquido.copy()
        saldo_anterior = 0.0
        receitas_ajustadas = []
        saldos = []

        # Loop iterativo mês a mês
        for _, row in df_saldo.iterrows():
            receita = row['Receitas'] + saldo_anterior
            despesa = row['Despesas']
            saldo = receita - despesa

            receitas_ajustadas.append(receita)
            saldos.append(saldo)

            # o saldo atual vira o saldo anterior pro próximo mês
            saldo_anterior = saldo

        # Adiciona as novas colunas
        df_saldo['Receitas Ajustadas'] = receitas_ajustadas
        df_saldo['Saldo'] = saldos

        # Mantém a ordem
        df_saldo = df_saldo.rename(columns={'Receitas':'Receitas Totais', 'Despesas':'Despesas Totais'})
        df_saldo = df_saldo[['Mes_Ano', 'Receitas Totais', 'Diferença', 'Receitas Ajustadas', 'Despesas Totais', 'Saldo']]

        pivot_saldo = df_saldo.melt(
            id_vars='Mes_Ano',
            value_vars=['Receitas Totais', 'Receitas Ajustadas', 'Despesas Totais', 'Saldo'],
            var_name='Categoria',
            value_name='Valor'
        ).pivot(
            index='Categoria',
            columns='Mes_Ano',
            values='Valor'
        ).fillna(0).reindex(['Receitas Totais', 'Receitas Ajustadas', 'Despesas Totais', 'Saldo'])

        # Convertendo índices de coluna para string
        pivot_saldo.columns = pivot_saldo.columns.astype(str)

        # Resetando o índice para incluir Class_Cont_0 como coluna
        pivot_saldo = pivot_saldo.reset_index()

        colunas_numericas_saldo = [col for col in pivot_saldo if col != 'Categoria']
    
        # Exibindo tabela
        df_pivot_saldo, tam_df_pivot_saldo_aggrid = dataframe_aggrid(
            df=pivot_saldo,
            name="Saldo/Fluxo de caixa",
            num_columns=colunas_numericas_saldo,  
            highlight_rows=['Saldo'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        st.divider()

        # Resumo estatístico
        st.subheader(":material/heap_snapshot_large: Resumo Estatístico - Todos os meses")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_receitas = df_consolidado[df_consolidado['Categoria'] == 'Receitas']['Valor'].sum()
            total_receitas_fmt = format_brazilian(total_receitas)
            st.metric("Total Receitas", f"R$ {total_receitas_fmt}")

        with col2:
            total_despesas = df_consolidado[df_consolidado['Categoria'] == 'Despesas']['Valor'].sum()
            total_despesas_fmt = format_brazilian(total_despesas)
            st.metric("Total Despesas", f"R$ {total_despesas_fmt}")

        with col3:
            fluxo_liquido_total = total_receitas - total_despesas
            fluxo_liquido_total_fmt = format_brazilian(fluxo_liquido_total)
            st.metric("Fluxo Líquido", f"R$ {fluxo_liquido_total_fmt}")

        with col4:
            if total_receitas > 0:
                margem = (fluxo_liquido_total / total_receitas) * 100
                margem_fmt = format_brazilian(margem)
                st.metric("Margem (%)", f"{margem_fmt}%")
            else:
                st.metric("Margem (%)", "N/A")
    st.write("")
            
st.divider()


# Tabela Dinâmica - Class_Cont_1 (Detalhamento)
col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    st.subheader("Despesas por Classificação Contábil (Class_Cont_1)")

# Preparando dados para a tabela dinâmica
pivot_table = prepare_pivot_data_class_despesas(
    df_custos_blueme_sem_parcelam_filtrada, 
    df_custos_blueme_com_parcelam_filtrada, 
    mapeamento_class_cont, 
    classe=1)

# Criando a tabela dinâmica
try:   
    if not pivot_table.empty:
        # Separando colunas numéricas das de texto
        colunas_numericas = [col for col in pivot_table.columns if col != 'Class_Cont_1']
        
        # Exibindo tabela dinâmica
        df_pivot_aggrid, tam_df_pivot_aggrid = dataframe_aggrid(
            df=pivot_table,
            name="Tabela Dinâmica - Despesas por Classificação e Mês",
            num_columns=colunas_numericas, 
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        with col2:
            # Botão para copiar dados
            function_copy_dataframe_as_tsv(df_pivot_aggrid)
        
        # Tabela Dinâmica - Detalhamento por Class_Cont_2
        st.write("")
        col1, col2 = st.columns([6, 1], vertical_alignment='center')
        with col1:
            st.subheader(":material/arrow_downward: Detalhamento por Subclassificação Contábil")
      
        # Preparando dados para Class_Cont_2
        df_class2_data = prepare_pivot_data_class_despesas(
            df_custos_blueme_sem_parcelam_filtrada, 
            df_custos_blueme_com_parcelam_filtrada, 
            mapeamento_class_cont, 
            classe=2)
        
        if not df_class2_data.empty:
            # Obtendo lista de Class_Cont_1 disponíveis
            classificacoes_disponiveis = sorted(df_class2_data['Class_Cont_1'].unique())
            
            # Selectbox para escolher a classificação
            classificacao_selecionada = st.selectbox(
                "Selecione uma Classificação Contábil da tabela acima para ver os detalhes:",
                classificacoes_disponiveis,
                index=0
            )
            st.write("")
            
            # Filtrando dados para a classificação selecionada
            df_class2_filtrado = df_class2_data[df_class2_data['Class_Cont_1'] == classificacao_selecionada]
            
            if not df_class2_filtrado.empty:
                # Criando tabela dinâmica para Class_Cont_2
                pivot_table_class2 = df_class2_filtrado.pivot(
                    index='Class_Cont_2',
                    columns='Mes_Ano',
                    values='Valor'
                ).fillna(0)
                
                # Convertendo índices de coluna para string
                pivot_table_class2.columns = pivot_table_class2.columns.astype(str)
                
                # Adicionando coluna de total
                pivot_table_class2['Total'] = pivot_table_class2.sum(axis=1)
                
                # Ordenando por total (maior para menor)
                pivot_table_class2 = pivot_table_class2.sort_values('Total', ascending=False)
                
                # Resetando o índice para incluir Class_Cont_2 como coluna
                pivot_table_class2 = pivot_table_class2.reset_index()
                
                # Separando colunas numéricas das de texto
                colunas_numericas_class2 = [col for col in pivot_table_class2.columns if col != 'Class_Cont_2']
            
                # Exibindo tabela dinâmica de Class_Cont_2
                df_pivot_class2_aggrid, tam_df_pivot_class2_aggrid = dataframe_aggrid(
                    df=pivot_table_class2,
                    name=f"Detalhamento - {classificacao_selecionada}",
                    num_columns=colunas_numericas_class2,
                    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                    fit_columns_on_grid_load=True
                )
                
                with col2:
                    # Botão para copiar dados de Class_Cont_2
                    function_copy_dataframe_as_tsv(df_pivot_class2_aggrid)
                
            else:
                st.warning(f"Não há dados de subclassificação disponíveis para {classificacao_selecionada}")
        else:
            st.warning("Não há dados de subclassificação disponíveis para o período e casas selecionadas.")
    else:
        st.warning("Não há dados de despesas disponíveis para o período e casas selecionadas.")
        
except Exception as e:
    st.error(f"Erro ao gerar tabela dinâmica: {str(e)}")

st.divider()


# Tabela de Referência - Mapeamento Class_Cont_0 ↔ Class_Cont_1
col1, col2 = st.columns([6, 1], vertical_alignment='center')
with col1:
    st.subheader("Tabela de Referência - Mapeamento de Classificações")
    st.write("Mapeamento Class_Cont_0 ↔ Class_Cont_1")

# Criando DataFrame de referência
df_mapping_ref = create_mapping_reference(
    mapeamento_class_cont, 
    df_custos_blueme_sem_parcelam_filtrada, 
    df_custos_blueme_com_parcelam_filtrada
)

# Criando e exibindo tabela de referência
try:
    if not df_mapping_ref.empty:
        # Ordenando por Class_Cont_0 e depois por Class_Cont_1
        # Tratando valores None na ordenação
        df_mapping_ref = df_mapping_ref.sort_values(['Class_Cont_0', 'Class_Cont_1'], na_position='last')
        
        # Exibindo tabela de referência
        df_mapping_ref_aggrid, tam_df_mapping_ref_aggrid = dataframe_aggrid(
            df=df_mapping_ref,
            name="Mapeamento Class_Cont_0 ↔ Class_Cont_1",
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        with col2:
            # Botão para copiar dados de referência
            function_copy_dataframe_as_tsv(df_mapping_ref_aggrid)

        st.divider()
        
        # Resumo estatístico
        st.subheader(":material/heap_snapshot_large: Resumo Estatístico")
        total_mapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Mapeado'])
        total_unmapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Não Mapeado'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Classificações", len(df_mapping_ref))
        with col2:
            percentual_mapeadas = total_mapped/len(df_mapping_ref)*100 if len(df_mapping_ref) > 0 else "N/A"
            percentual_mapeadas_fmt = format_brazilian(percentual_mapeadas)
            st.metric("Mapeadas", total_mapped, delta=f"{percentual_mapeadas_fmt}%")
        with col3:
            percentual_nao_mapeadas = total_unmapped/len(df_mapping_ref)*100 if len(df_mapping_ref) > 0 else "N/A"
            percentual_nao_mapeadas_fmt = format_brazilian(percentual_nao_mapeadas)
            st.metric("Não Mapeadas", total_unmapped, delta=f"{percentual_nao_mapeadas_fmt}%")
        
        # Aviso sobre classificações não mapeadas
        if total_unmapped > 0:
            st.warning(f"⚠️ **Atenção**: {total_unmapped} classificação(ões) não possuem mapeamento definido e serão tratadas como Class_Cont_0 próprias.")
    else:
        st.info("Nenhuma classificação encontrada nos dados.")
        
except Exception as e:
    st.error(f"Erro ao gerar tabela de referência: {str(e)}")

