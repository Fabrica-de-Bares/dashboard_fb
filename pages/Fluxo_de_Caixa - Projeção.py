import streamlit as st
import pandas as pd
from utils.queries_fluxo_de_caixa import *
from utils.functions.general_functions import *
from utils.functions.fluxo_de_caixa_projecao import *
from datetime import datetime
from utils.components import button_download


st.set_page_config(
    page_title="Projeção - Despesas", 
    page_icon="🧾", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

config_sidebar()

col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment='center')
with col1:
    st.title("🧾 Projeção - Despesas")
with col2:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
    
st.write("")
seletor_status_despesa = st.segmented_control(
    label="Selecione o Status das Despesas:",
    options=["Apenas Aprovadas", "Todas Previstas"],
    selection_mode="single",
    default="Apenas Aprovadas",
    help='"Previstas" envolve as despesas aprovadas e pendentes'
)
st.divider()

# Bares exibidos nos seletores baseado no cargo do usuário
cargo_usuario = st.session_state['cargo_usuario']
nome_usuario = st.session_state['nome_usuario']

# Grupo de bares agrupados
if (cargo_usuario != 'Sócio') or (cargo_usuario == 'Sócio' and (nome_usuario == 'Caire' or nome_usuario == 'Alvaro Aoas')):
    df_bares_agrupados = GET_BARES_AGRUPADOS() # Vê todos os bares agrupados (como antes)
elif cargo_usuario == 'Sócio' and nome_usuario != 'Caire' and nome_usuario != 'Alvaro Aoas': # Sócios de casas específicas
    df_bares_agrupados = pd.DataFrame(st.session_state['casas_permitidas'], columns=["Loja"])
    df_bares_agrupados = df_bares_agrupados.rename(columns={'Loja': 'Empresa'})

lojasAgrupadas = df_bares_agrupados['Empresa'].tolist()

# Lojas com dados
if (cargo_usuario != 'Sócio') or (cargo_usuario == 'Sócio' and (nome_usuario == 'Caire' or nome_usuario == 'Alvaro Aoas')):
    lojasComDados = preparar_dados_lojas_user_projecao_fluxo() # Vê todos as casas (como antes)
elif cargo_usuario == 'Sócio' and nome_usuario != 'Caire' and nome_usuario != 'Alvaro Aoas': # Sócios de casas específicas
    df_lojas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["Loja"])
    df_lojas = df_lojas.rename(columns={'Loja': 'Empresa'})
    lojasComDados = df_lojas['Empresa'].tolist()

lojasComDados = sorted(lojasComDados)
if 'Arcos' in lojasComDados: # Para não ficar 'All bar' como default nos seletors
    lojasComDados.remove('Arcos')
    lojasComDados.insert(0, 'Arcos')

# Recuperando dados
df_saldos_bancarios = GET_SALDOS_BANCARIOS()                    # saldo inicio do dia atual de cada casa
df_valor_liquido = GET_VALOR_LIQUIDO_RECEBIDO()                 # valor liquido de receitas do dia atual de cada casa
df_projecao_zig = GET_PROJECAO_ZIG()                            # projecao faturamento da zig de cada casa para a semana
df_receitas_extraord_proj = GET_RECEITAS_EXTRAORD_FLUXO_CAIXA() # receit. extr. lançadas de cada casa para duas semanas
df_receitas_eventos_proj = GET_EVENTOS_FLUXO_CAIXA()            # eventos lançados de cada casa para duas semanas

# Despesas Pendentes e Pagas
df_despesas_aprovadas_previstas_pendentes = GET_DESPESAS_PENDENTES() # despesas pendentes (aprovadas ou não)
df_despesas_pagas_previstas_pendentes = GET_DESPESAS_PAGAS()         # despesas pagas (aprovadas ou não)

# Dados para despesas provisionadas
df_despesas_provisionadas_padrao = GET_DESPESAS_PROVISIONADAS_MENSAIS()
df_despesas_rapidas_para_provisao = GET_DESPESAS_RAPIDAS_PREVISTAS()
df_provisoes_nao_lancadas, df_valor_provisionadas_nao_lancadas = despesas_provisionadas_lancadas(df_despesas_provisionadas_padrao, df_despesas_rapidas_para_provisao)

# Filtra de acordo com o seletor (aprovadas/previstas)
df_categoria_despesas_pendentes = filtra_categoria_despesas(df_despesas_aprovadas_previstas_pendentes, seletor_status_despesa, 'pendentes')
df_categoria_despesas_pagas = filtra_categoria_despesas(df_despesas_pagas_previstas_pendentes, seletor_status_despesa, 'pagas')

df_projecao_bares_geral = config_projecao_bares(
    seletor_status_despesa,
    df_saldos_bancarios, 
    df_valor_liquido, 
    df_projecao_zig, 
    df_receitas_extraord_proj,
    df_receitas_eventos_proj,  
    df_categoria_despesas_pendentes, 
    df_categoria_despesas_pagas,
    df_valor_provisionadas_nao_lancadas
)

# Projeção Agrupada
with st.container(border=True):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader(f"Projeção de bares agrupados - {seletor_status_despesa}")
    with col2:
        data_fim = seletor_data_fim_padrao(key='date_input2') # Data de fim padrão dos seletores: uma semana à frente do dia atual
    with col3:
        multiplicador = st.number_input("Selecione um multiplicador", value=1.0, key="multiplicador_input2")
    
    lista_bares_agrupados = sorted(lojasAgrupadas)
    texto = ", ".join(lista_bares_agrupados)
    st.markdown(f"{texto}")
    df_projecao_bares = df_projecao_bares_geral

    # Aplica data e multiplicador selecionados
    df_projecao_bares = filtra_soma_saldo_final(seletor_status_despesa, df_projecao_bares, data_fim, multiplicador)
    
    # Aplica as casas agrupadas
    df_projecao_grouped = config_grouped_projecao(df_projecao_bares, lojasAgrupadas)
    df_projecao_grouped_com_soma = somar_total(df_projecao_grouped)

    # Organiza colunas
    df_projecao_grouped_com_soma = organiza_colunas(df_projecao_grouped_com_soma, 'bares agrupados', seletor_status_despesa=seletor_status_despesa)

    # Ordena por data
    df_projecao_grouped_com_soma = ordena_por_data(df_projecao_grouped_com_soma)
    df_projecao_grouped_styled = df_projecao_grouped_com_soma.style.apply(highlight_total_row, axis=1)
    st.dataframe(df_projecao_grouped_styled, width='stretch', hide_index=True)
    button_download(df_projecao_grouped_com_soma, f"Projeção de bares agrupados", f"Projeção de bares agrupados")

    if seletor_status_despesa == 'Todas Previstas':
        exibe_provisoes_pendentes(df_provisoes_nao_lancadas, data_fim, lojasAgrupadas)

st.divider()

# Projeção casa a casa (selecionadas)
with st.container(border=True):
    st.subheader(f"Projeção casa a casa - {seletor_status_despesa}")
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1], vertical_alignment='bottom')

    # Adiciona seletores
    with col1:
        bares_selecionados = st.multiselect("Selecione casas", lojasComDados, default=lojasComDados[0])
    with col2:
        checkbox_agrupa = st.checkbox(label="Agrupar casas selecionadas", key="checkbox_agrupa_lojas_selecionadas")
    with col3:
        # Data de fim padrão dos seletores: uma semana à frente do dia atual
        data_fim = seletor_data_fim_padrao(key='date_input')
    with col4:
        multiplicador = st.number_input(
            "Selecione um multiplicador", value=1.0, key="multiplicador_input"
        )

    # Mensagem de aviso - Delivery
    if 'Bar Brahma - Centro' in bares_selecionados: st.write(f'Para visualizar o Delivery do Bar Brahma - Centro, selecione "Delivery Fabrica de Bares" no campo acima.')
    if 'Bar Léo - Granja' in bares_selecionados: st.write(f'Para visualizar o Delivery do Bar Brahma - Granja, selecione "Delivery Brahma Granja Viana" no campo acima.')
    if 'Bar Léo - Centro' in bares_selecionados: st.write(f'Para visualizar o Delivery do Bar Léo - Centro, selecione "Delivery Bar Leo Centro" no campo acima.')
    if 'Jacaré' in bares_selecionados: st.write(f'Para visualizar o Delivery do Jacaré, selecione "Delivery Jacaré" no campo acima.')
    if 'Orfeu' in bares_selecionados: st.write(f'Para visualizar o Delivery do Orfeu, selecione "Delivery Orfeu" no campo acima.')

    df_projecao_bares = df_projecao_bares_geral

    # Aplica data e multiplicador selecionados
    df_projecao_bares = filtra_soma_saldo_final(seletor_status_despesa, df_projecao_bares, data_fim, multiplicador)
    
    # Filtra para as casas selecionadas
    if 'Todas as casas' in bares_selecionados:
        df_projecao_bar = filtrar_por_classe_selecionada(df_projecao_bares, "Empresa", lojasComDados)
    else: 
        df_projecao_bar = filtrar_por_classe_selecionada(df_projecao_bares, "Empresa", bares_selecionados)

    if checkbox_agrupa: # Agrupa casas selecionadas se checkbox ativo
        colunas = [
            'Saldo_Inicio_Dia',
            'Valor_Liquido_Recebido',
            'Valor_Projetado_Zig',
            'Receita_Projetada_Extraord',
            'Receita_Projetada_Eventos',
            'Despesas_Aprovadas_Pendentes',
            'Despesas_Pagas',
            'Saldo_Final'
        ]

        if seletor_status_despesa == 'Todas Previstas':
            colunas.insert(-1, 'Provisões Pendentes')

        agg_dict = {col: 'sum' for col in colunas}
        df_projecao_bar_agrupados = df_projecao_bar.groupby('Data', as_index=False).agg(agg_dict)

        nome_agrupado = "Agrupamento"
        df_projecao_bar_agrupados['Empresa'] = nome_agrupado
        df_projecao_exibida = df_projecao_bar_agrupados
    
    else: # Se não, exibe cada casa individualmente
        df_projecao_exibida = df_projecao_bar

    # Cria linha de Total
    df_projecao_bar_com_soma = somar_total(df_projecao_exibida)
   
    # Organiza colunas
    df_projecao_bar_com_soma = organiza_colunas(df_projecao_bar_com_soma, 'projeção casa a casa', seletor_status_despesa=seletor_status_despesa)

    df_projecao_bar_com_soma = ordena_por_data(df_projecao_bar_com_soma)
    df_projecao_bar_styled = df_projecao_bar_com_soma.style.apply(highlight_total_row, axis=1)
    st.dataframe(df_projecao_bar_styled, width='stretch', hide_index=True)
    button_download(df_projecao_bar_com_soma, f"Projeção casa a casa", f"Projeção casa a casa")

    if seletor_status_despesa == 'Todas Previstas':
        exibe_provisoes_pendentes(df_provisoes_nao_lancadas, data_fim, bares_selecionados)
st.divider()

with st.container(border=True):
    st.subheader(f"Despesas do dia - {seletor_status_despesa}")
    col1, col2, col3, col4 = st.columns([5, 3, 4, 4], vertical_alignment='center')

    # Adiciona seletores
    with col1:
        lojasSelecionadas = st.multiselect(label="Selecione casas", options=lojasComDados, key="lojas_multiselect", default=lojasComDados[0])
    with col2:
        checkbox = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_despesas")
        if checkbox: # Lojas agrupadas
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas.extend(lojasAgrupadas)
        
        checkbox2 = st.checkbox(label="Apenas Pendentes", key="checkbox_despesas_pendentes") # Apenas despesas pendentes
        checkbox3 = st.checkbox(label="Apenas Pagas", key="checkbox_despesas_pagas") # Apenas despesas pagas
    
    with col3:
        dataSelecionada = st.date_input(
            "Data de Início (da previsão de pagamento)",
            value=datetime.today(),
            key="data_inicio_input",
            format="DD/MM/YYYY",
        )
    with col4:
        dataSelecionada2 = st.date_input(
            "Data de Fim (da previsão de pagamento)",
            value=datetime.today(),
            key="data_fim_input3",
            format="DD/MM/YYYY",
        )

    if not checkbox:
        # Mensagem de aviso - Delivery
        if 'Bar Brahma - Centro' in lojasSelecionadas: st.write(f'Para visualizar o Delivery do Bar Brahma - Centro, selecione "Delivery Fabrica de Bares" no campo acima.')
        if 'Bar Léo - Granja' in lojasSelecionadas: st.write(f'Para visualizar o Delivery do Bar Brahma - Granja, selecione "Delivery Brahma Granja Viana" no campo acima.')
        if 'Bar Léo - Centro' in lojasSelecionadas: st.write(f'Para visualizar o Delivery do Bar Léo - Centro, selecione "Delivery Bar Leo Centro" no campo acima.')
        if 'Jacaré' in lojasSelecionadas: st.write(f'Para visualizar o Delivery do Jacaré, selecione "Delivery Jacaré" no campo acima.')
        if 'Orfeu' in lojasSelecionadas: st.write(f'Para visualizar o Delivery do Orfeu, selecione "Delivery Orfeu" no campo acima.')

    data_inicio = pd.to_datetime(dataSelecionada)
    data_fim = pd.to_datetime(dataSelecionada2)

    despesas_pendentes_pagas = GET_DETALHES_DESPESAS_PENDENTES()
    df_despesas_pendentes_pagas = filtra_detalhes_despesas(seletor_status_despesa, despesas_pendentes_pagas, data_inicio, data_fim)

    # Filtra para as casas selecionadas
    if 'Todas as casas' in lojasSelecionadas:  
        df_despesas_pendentes_pagas = filtrar_por_classe_selecionada(df_despesas_pendentes_pagas, 'Loja', lojasComDados)
    else:
        df_despesas_pendentes_pagas = filtrar_por_classe_selecionada(df_despesas_pendentes_pagas, 'Loja', lojasSelecionadas)

    if checkbox2:
        df_despesas_pendentes_pagas = filtrar_por_classe_selecionada(df_despesas_pendentes_pagas, "Status_Pgto", ["Pendente"])
    if checkbox3:
        df_despesas_pendentes_pagas = filtrar_por_classe_selecionada(df_despesas_pendentes_pagas, "Status_Pgto", ["Pago"])

    # Formata exibição
    valorTotal = df_despesas_pendentes_pagas["Valor"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(df_despesas_pendentes_pagas, ["Valor"])
    df = df_format_date_brazilian(df, 'Previsao_Pgto')
    df = df_format_date_brazilian(df, 'Data_Vencimento')
    df = df.sort_values(by=["Loja", "Previsao_Pgto"])

    # Organiza colunas
    df = organiza_colunas(df, 'despesas do dia')

    st.dataframe(df, width='stretch', hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das despesas selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Despesas do dia", f"Despesas do dia")


with st.container(border=True):
    st.subheader("Receitas Extraordinárias do Dia")
    col1, col2, col3 = st.columns([5, 2, 3], vertical_alignment='bottom')

    # Adiciona seletores
    with col1:
        lojasSelecionadas2 = st.multiselect(label="Selecione casas", options=lojasComDados, key="lojas_multiselect2", default=lojasComDados[0])

    with col2:
        checkboxLojas = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_extraord")
        if checkboxLojas: # Lojas agrupadas
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas2.extend(lojasAgrupadas)
    
    with col3:
        dataSelecionada2 = st.date_input(
            "Selecione uma Data",
            value=datetime.today(),
            key="data_inicio_input2",
            format="DD/MM/YYYY",
        )

    df = GET_RECEITAS_EXTRAORD_DO_DIA()

    # Filtra para as casas e data selecionadas
    if 'Todas as casas' in lojasSelecionadas2:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasComDados)
    else:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasSelecionadas2)
    
    dataSelecionada2 = pd.to_datetime(dataSelecionada2)
    df = filtrar_por_datas(df, dataSelecionada2, dataSelecionada2, "Data_Vencimento_Parcela")

    # Formata para exibição
    valorTotal = df["Valor_Parcela"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(df, ["Valor_Parcela"])
    df = df_format_date_columns_brazilian(df, ['Data_Vencimento_Parcela'])
    df = df.sort_values(by=["Empresa"])
    
    # Organiza colunas
    df = organiza_colunas(df, 'receitas extraordinárias')

    st.dataframe(df, width='stretch', hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das receitas extraordinárias selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Receitas Extraord do dia", f"Receitas Extraord do dia")
    
    
with st.container(border=True):
    st.subheader("Receitas de Eventos do Dia")
    col1, col2, col3 = st.columns([5, 2, 3], vertical_alignment='bottom')

    # Adiciona seletores
    with col1:
        lojasSelecionadas2 = st.multiselect(label="Selecione Lojas", options=lojasComDados, key="lojas_multiselect3", default=lojasComDados[0])

    with col2: # Lojas agrupadas
        checkboxLojas = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_eventos")
        if checkboxLojas:
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas2.extend(lojasAgrupadas)
    
    with col3:
        dataSelecionada2 = st.date_input(
            "Selecione uma Data",
            value=datetime.today(),
            key="data_inicio_input3",
            format="DD/MM/YYYY",
        )

    df = GET_RECEITAS_EVENTOS_DO_DIA()

    # Filtra por casas e data selecionadas
    if 'Todas as casas' in lojasSelecionadas2:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasComDados)
    else:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasSelecionadas2)
    
    dataSelecionada2 = pd.to_datetime(dataSelecionada2)
    df = filtrar_por_datas(df, dataSelecionada2, dataSelecionada2, "Data_Vencimento_Parcela")
    
    # Formata para exibição
    valorTotal = df["Valor_Parcela"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(df, ["Valor_Parcela"])
    df = df_format_date_columns_brazilian(df, ['Data_Vencimento_Parcela'])
    df = df.sort_values(by=["Empresa"])
   
    # Organiza colunas
    df = organiza_colunas(df, 'receitas de eventos')

    st.dataframe(df, width='stretch', hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das receitas de eventos selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Receitas Eventos do dia", f"Receitas Eventos do dia")
