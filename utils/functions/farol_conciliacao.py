import streamlit as st
import pandas as pd
import datetime
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import cores_casas
from utils.functions.conciliacoes import *
from utils.functions.farol_conciliacao import *
from utils.queries_conciliacao import *
from streamlit_echarts import st_echarts


ano_atual = datetime.datetime.now().year

hoje = pd.Timestamp.today().normalize()
ontem = hoje - pd.Timedelta(days=1)
inicio_mes = hoje.replace(day=1)
dias_ate_ontem = (ontem - inicio_mes).days + 1


# Cria tabela de conciliação para cada casa
def conciliacao_casa(df, casa, datas_completas):
    df_copia = df.copy()

    # # Extrato Zig (Saques) #
    df_extrato_zig = GET_EXTRATO_ZIG()
    df_extrato_zig_farol = df_extrato_zig[df_extrato_zig['Casa'] == casa]
    if 'Extrato Zig (Saques)' not in df_copia.columns:
        df_copia['Extrato Zig (Saques)'] = somar_por_data(
            df_extrato_zig_farol[df_extrato_zig_farol['Descricao'].isin(["Saque", "Antecipação"])],
            "Data_Liquidacao", "Valor", datas_completas
        ) * (-1)

    # Faturam dinheiro #
    if 'Faturam dinheiro' not in df_copia.columns:
        df_copia['Faturam dinheiro'] = 0 # stand-by

    # Receitas Extraordinárias #
    df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
    df_parc_receit_extr_farol = df_parc_receit_extr[df_parc_receit_extr['Casa'] == casa]

    cond_eventos = df_parc_receit_extr_farol["Classif_Receita"].str.lower() == "eventos"
    cond_intervalo = (
        (df_parc_receit_extr_farol["Recebimento_Parcela"] >= "2025-09-01") &
        (df_parc_receit_extr_farol["Recebimento_Parcela"] < "2026-01-01")
    )
    df_parc_receit_extr_farol = df_parc_receit_extr_farol[~(cond_eventos & cond_intervalo)]

    if 'Receitas Extraordinárias' not in df_copia.columns:
        df_copia['Receitas Extraordinárias'] = somar_por_data(
            df_parc_receit_extr_farol, "Recebimento_Parcela", "Valor_Parcela", datas_completas
        )

    # Eventos (desmembrar de Receitas Extraordinárias) #
    df_eventos = GET_EVENTOS()
    df_eventos_farol = df_eventos[(df_eventos['Casa'] == casa)]
    
    if 'Eventos' not in df_copia.columns:
        df_copia['Eventos'] = somar_por_data(
            df_eventos_farol, "Recebimento_Parcela", "Valor_Parcela", datas_completas
        )

    # Entradas Mutuos #
    df_mutuos = GET_MUTUOS()
    df_mutuos_farol = df_mutuos[(df_mutuos['Casa_Saida'] == casa) | (df_mutuos['Casa_Entrada'] == casa)] 
    if 'Entradas Mútuos' not in df_copia.columns:
        df_copia['Entradas Mútuos'] = somar_por_data(
            df_mutuos_farol[df_mutuos_farol['Casa_Entrada'] == casa], 
            "Data_Mutuo", "Valor", datas_completas
        )

    # Desbloqueios Judiciais #
    df_bloqueios_judiciais = GET_BLOQUEIOS_JUDICIAIS()
    df_bloqueios_judiciais_farol = df_bloqueios_judiciais[df_bloqueios_judiciais['Casa'] == casa]
    if 'Desbloqueios Judiciais' not in df_copia.columns:
        df_copia['Desbloqueios Judiciais'] = somar_por_data(
            df_bloqueios_judiciais_farol[df_bloqueios_judiciais_farol['Valor'] > 0],
            "Data_Transacao", "Valor", datas_completas
        )

    # Extrato Bancário (Crédito) #
    df_extratos_bancarios = GET_EXTRATOS_BANCARIOS()
    df_extratos_bancarios_farol = df_extratos_bancarios[df_extratos_bancarios['Casa'] == casa]
    if 'Extrato Bancário (Crédito)' not in df_copia.columns:
        df_filtrado = df_extratos_bancarios_farol.copy()
        df_filtrado['Data_Somente'] = pd.to_datetime(df_filtrado['Data_Transacao']).dt.date

        df_copia['Extrato Bancário (Crédito)'] = somar_por_data(
            df_filtrado[df_filtrado['Tipo_Credito_Debito'] == "CREDITO"],
            "Data_Somente",  # ainda usamos a coluna original com hora para somar por data
            "Valor", datas_completas
        )

    # Diferenças (Contas a Receber) #
    if 'Diferenças (Contas a Receber)' not in df.columns:
        df_copia['Diferenças (Contas a Receber)'] = calcula_diferencas(
            df_copia, "Extrato Bancário (Crédito)", ['Extrato Zig (Saques)', 'Faturam dinheiro', 'Receitas Extraordinárias', 'Eventos', 'Entradas Mútuos', 'Desbloqueios Judiciais']
        )

    # Custos sem parcelamento #
    df_custos_blueme_sem_parcelam = GET_CUSTOS_BLUEME_SEM_PARC()
    df_custos_blueme_sem_parcelam_farol = df_custos_blueme_sem_parcelam[df_custos_blueme_sem_parcelam['Casa'] == casa]
    if 'Custos sem Parcelamento' not in df_copia.columns:
        df_copia['Custos sem Parcelamento'] = somar_por_data(
            df_custos_blueme_sem_parcelam_farol, "Realizacao_Pgto", "Valor", datas_completas
        ) * (-1)

    # Custos com parcelamento #
    df_custos_blueme_com_parcelam = GET_CUSTOS_BLUEME_COM_PARC()
    df_custos_blueme_com_parcelam_farol = df_custos_blueme_com_parcelam[df_custos_blueme_com_parcelam['Casa'] == casa]
    if 'Custos com Parcelamento' not in df_copia.columns:
        df_copia['Custos com Parcelamento'] = somar_por_data(
            df_custos_blueme_com_parcelam_farol, "Realiz_Parcela", "Valor_Parcela", datas_completas
        ) * (-1)

    # Saidas Mutuos #
    if 'Saídas Mútuos' not in df_copia.columns:
        df_copia['Saídas Mútuos'] = somar_por_data(
            df_mutuos_farol[df_mutuos_farol['Casa_Saida'] == casa],
            "Data_Mutuo", "Valor", datas_completas
        ) * (-1)

    # Bloqueios Judiciais #
    if 'Bloqueios Judiciais' not in df_copia.columns:
        df_copia['Bloqueios Judiciais'] = somar_por_data(
            df_bloqueios_judiciais_farol[df_bloqueios_judiciais_farol['Valor'] < 0],
            "Data_Transacao", "Valor", datas_completas
        )

    # Extrato Bancário (Débito) #
    if 'Extrato Bancário (Débito)' not in df_copia.columns:
        df_filtrado = df_extratos_bancarios_farol.copy()
        df_filtrado['Data_Transacao'] = pd.to_datetime(df_filtrado['Data_Transacao']).dt.date

        df_copia['Extrato Bancário (Débito)'] = somar_por_data(
            df_filtrado[df_filtrado['Tipo_Credito_Debito'] == "DEBITO"],
            "Data_Transacao", "Valor", datas_completas
        )

    # Diferenças (Contas a pagar) #
    if 'Diferenças (Contas a Pagar)' not in df_copia.columns:
        df_copia['Diferenças (Contas a Pagar)'] = calcula_diferencas(
            df_copia, "Extrato Bancário (Débito)", ['Custos sem Parcelamento', 'Custos com Parcelamento', 'Saídas Mútuos', 'Bloqueios Judiciais']
        )

    # Ajustes #
    df_ajustes_conciliacao = GET_AJUSTES()
    df_ajustes_conciliacao_farol = df_ajustes_conciliacao[df_ajustes_conciliacao['Casa'] == casa]
    if 'Ajustes Conciliação' not in df_copia.columns:
        df_copia['Ajustes Conciliação'] = somar_por_data(
            df_ajustes_conciliacao_farol, "Data_Ajuste", "Valor", datas_completas
        )

    # Conciliação # 
    if 'Conciliação' not in df_copia.columns:
        df_copia['Conciliação'] = df_copia['Diferenças (Contas a Pagar)'] + df_copia['Diferenças (Contas a Receber)'] - df_copia['Ajustes Conciliação']
    
        # Garante que é float
        df_copia['Conciliação'] = pd.to_numeric(df_copia['Conciliação'], errors='coerce')

        # Zera valores muito pequenos 
        df_copia['Conciliação'] = df_copia['Conciliação'].apply(lambda x: 0.0 if abs(x) < 0.005 else x)

    return df_copia


# Calcula porcentagem de dias não conciliados por mês de cada casa
def lista_dias_nao_conciliados_casa(df_casa, ano_farol, df_meses, mes_atual):
    df_dias_nao_conciliados = df_casa[df_casa['Data'].dt.year == ano_farol]
    df_dias_nao_conciliados = df_dias_nao_conciliados[df_dias_nao_conciliados['Conciliação'] != 0.0]

    # EXCLUI O DIA DE HOJE SE FOR O MÊS/ANO ATUAL
    if ano_farol == ano_atual:
        df_dias_nao_conciliados = df_dias_nao_conciliados[
            ~(
                (df_dias_nao_conciliados['Data'].dt.month == mes_atual) &
                (df_dias_nao_conciliados['Data'] > ontem)
            )
        ]
    df_dias_nao_conciliados['Data'] = df_dias_nao_conciliados['Data'].dt.month # Mês dos dias não conciliados
    
    # Contagem de dias não conciliados por mês
    df_qtd_dias_nao_conciliados_mes = df_dias_nao_conciliados.groupby(['Data'])['Conciliação'].count().reset_index()
    df_qtd_dias_nao_conciliados_mes = df_qtd_dias_nao_conciliados_mes.merge(df_meses, left_on='Data', right_on='Mes', how='right')
    
    # MÊS ATUAL NO ANO ATUAL
    mask_mes_atual = (df_qtd_dias_nao_conciliados_mes['Mes'] == mes_atual) & (ano_farol == ano_atual)
    df_qtd_dias_nao_conciliados_mes.loc[mask_mes_atual, 'Porcentagem'] = (
        df_qtd_dias_nao_conciliados_mes.loc[mask_mes_atual, 'Conciliação'] / dias_ate_ontem
    )

    # MESES COMPLETOS (anos anteriores ou meses passados)
    mask_outros_meses = ~mask_mes_atual
    df_qtd_dias_nao_conciliados_mes.loc[mask_outros_meses, 'Porcentagem'] = (
        df_qtd_dias_nao_conciliados_mes.loc[mask_outros_meses, 'Conciliação'] / df_qtd_dias_nao_conciliados_mes.loc[mask_outros_meses, 'Qtd_dias']
    )
    
    df_qtd_dias_nao_conciliados_mes['Porcentagem'] = df_qtd_dias_nao_conciliados_mes['Porcentagem'].fillna(0) # Preenche meses None com zero (tem todos os dias conciliados ou meses depois do atual)
    
    # Lista com meses (0-11) e a porcentagem de dias não conciliados
    porc_dias_nao_conciliados = df_qtd_dias_nao_conciliados_mes['Porcentagem'].tolist()
    
    lista_dias_nao_conciliados = []
    for i, dia in enumerate(porc_dias_nao_conciliados):
        if (i <= mes_atual - 1) and (ano_farol == ano_atual):
            dia = dia * 100  # 2 casas decimais
        elif (i > mes_atual - 1) and (ano_farol == ano_atual):
            dia = 0 # meses depois do atual: 0 conciliação
        else:
            dia = dia * 100  # para anos anteriores, sempre multiplica
        dia = round(dia, 2)
        lista_dias_nao_conciliados.append(dia)
   
    # lista_dias_nao_conciliados = [v if v != 0 else None for v in lista_dias_nao_conciliados]  # None não é plotado
    return lista_dias_nao_conciliados


# Cria dataframe com dias não conciliados da casa clicada no mês específico
def dias_nao_conciliados_casa_mes(df_conciliacao_farol, casa_selecionada, mes_selecionado, ano_farol, datas_completas):
    # Gera tabela de conciliação da casa
    df_conciliacao_casa = conciliacao_casa(df_conciliacao_farol, casa_selecionada, datas_completas) 

    # Filtra por ano do farol e mês
    df_dias_nao_conciliados_casa = df_conciliacao_casa[
    (df_conciliacao_casa['Data'].dt.year == ano_farol) &
    (df_conciliacao_casa['Data'].dt.month == (mes_selecionado + 1))
    ]
    
    # Filtra por dias com conciliação != 0
    df_dias_nao_conciliados_casa = df_dias_nao_conciliados_casa[df_dias_nao_conciliados_casa['Conciliação'] != 0.0]
    qtd_dias_nao_conciliados = df_dias_nao_conciliados_casa['Conciliação'].count()
    return df_dias_nao_conciliados_casa, qtd_dias_nao_conciliados


# Gráfico com todos os meses e todas as casas (default)
def grafico_dias_nao_conciliados(casas_validas, nomes_meses, lista_casas):
    
    # Define as séries (barras) do eixo x (uma para cada casa)
    series = [
        {
            "name": nome,
            "type": "bar",
            "barGap": "10%",
            "data": lista_casas[i],
            "itemStyle": {"color": cores_casas[i]}
        }
        for i, nome in enumerate(casas_validas)
    ]

    grafico_dias_nao_conciliados = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": casas_validas,
            "orient": "vertical",   # legenda em coluna
            "right": "0%",        
            "top": "center",
            "backgroundColor": "#ffffff55",
        },
        "grid": {
            "left": "2%", 
            "right": "23%", 
            "bottom": "0%", 
            "containLabel": True},
        "xAxis": [{
            "type": "category", 
            "axisTick": {"show": True}, 
            "data": nomes_meses}],
        "yAxis": [
            {
            "type": "value", 
            # "min": 0,
            # "max": 50,
            # "interval": 10,
            "axisLabel": {"formatter": "{value} %"}
            }
        ],
        "series": series
    }

    # Evento de clique - abre o mês
    # events = {
    #     "click": "function(params) { return params.name; }"
    # }
    
    # mes_selecionado = st_echarts(options=grafico_dias_nao_conciliados, events=events, height="600px", width="100%")
    st_echarts(options=grafico_dias_nao_conciliados, height="600px", width="100%")


# Gráfico exibido ao selecionar um mês 
def grafico_dias_nao_conciliados_mes(casas_validas, lista_casas, mes_selecionado, df_conciliacao_farol, ano_farol, datas_completas):
    for i, casa in enumerate(lista_casas):
        for j, valor in enumerate(casa):
            if valor is None:
                lista_casas[i][j] = 0

    nomes_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    for mes in nomes_meses:
        if mes_selecionado == mes:
            nome_mes = mes
            mes_selecionado = nomes_meses.index(mes)

    lista_mes = []
    for casa in lista_casas:
        lista_mes.append(casa[mes_selecionado])
    
    # Define as séries (barras) do eixo x (uma para cada casa)
    series = [
        {
            "name": nome,
            "type": "bar",
            "barGap": "10%",
            "data": [lista_mes[i]],
            "backgroundStyle": {
                "color": 'rgba(180, 180, 180, 0.2)'
            },
            "itemStyle": {"color": cores_casas[i]},
            "label": {
                "show": True,
                "position": "top" 
            }
        }
        for i, nome in enumerate(casas_validas)
    ]

    grafico_dias_nao_conciliados_mes = {
        "tooltip": {
            "trigger": "axis", 
            "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": casas_validas,
            "orient": "vertical",   # legenda em coluna
            "right": "0%",        
            "top": "center",
            "backgroundColor": "#ffffff55",
        },
        "grid": {
            "left": "2%", 
            "right": "23%", 
            "bottom": "0%", 
            "containLabel": True
        },
        "xAxis": {
            "type": 'category',
            "data": [nome_mes]
        },
        "yAxis": {
            "type": 'value',
            "axisLabel": {"formatter": "{value} %"}
        },
        "series": series
    }

    # Evento de clique - seleciona a casa
    events = {
        "click": "function(params) { return params.seriesName; }"
    }
    
    resultado_clique = st_echarts(options=grafico_dias_nao_conciliados_mes, events=events, height="550px", width="100%")
    # st_echarts embrulha o retorno do evento num objeto tipo-dict (chave 'chart_event')
    # nessa versão do Streamlit; em versões mais antigas o retorno já vem "cru"
    casa_selecionada = resultado_clique.get('chart_event') if hasattr(resultado_clique, 'get') else resultado_clique

    if not casa_selecionada:
        st.info("Selecione uma casa para visualizar os dias não conciliados")
    else:
        # Exibe dataframe dos dias não conciliados da casa no mês
        st.divider()
        st.subheader(f"Dias não conciliados - {casa_selecionada}")
        df_dias_nao_conciliados_casa, qtd_dias_nao_conciliados = dias_nao_conciliados_casa_mes(df_conciliacao_farol, casa_selecionada, mes_selecionado, ano_farol, datas_completas)
        df_dias_nao_conciliados_casa_fmt = formata_df(df_dias_nao_conciliados_casa)
        st.dataframe(df_dias_nao_conciliados_casa_fmt, hide_index=True)
        st.write(f'**Quantidade de dias não conciliados:** {qtd_dias_nao_conciliados}')


# Cálculos por trimestre #
def lista_dias_nao_conciliados_casa_trim(df_casa, ano_farol, df_trimestres, trim_selecionado):
    df_dias_nao_conciliados = df_casa[df_casa['Data'].dt.year == ano_farol]
    df_dias_nao_conciliados = df_dias_nao_conciliados[df_dias_nao_conciliados['Conciliação'] != 0.0]
    df_dias_nao_conciliados['Mes'] = df_dias_nao_conciliados['Data'].dt.month # Mês dos dias não conciliados

    # Contagem de dias não conciliados por mês
    df_dias_nao_conciliados_trim = df_dias_nao_conciliados.merge(df_trimestres, left_on='Mes', right_on='Mes', how='right')
    
    # Porcentagem de dias não conciliados por trimestre
    df_qtd_dias_nao_conciliados_trim = df_dias_nao_conciliados_trim.groupby(['Trimestre'])['Conciliação'].count().reset_index()
    df_qtd_dias_nao_conciliados_trim = df_qtd_dias_nao_conciliados_trim.merge(df_trimestres, right_on='Trimestre', left_on='Trimestre', how='left')
    df_unico_por_trimestre = df_qtd_dias_nao_conciliados_trim.drop_duplicates(subset=['Trimestre'], keep='first').copy()
    df_unico_por_trimestre['Porcentagem'] = (df_unico_por_trimestre['Conciliação'] / df_unico_por_trimestre['Qtd_dias_y']) 
    
    porc_dias_nao_conciliados_trim = df_unico_por_trimestre['Porcentagem'].tolist()

    # Lista com trimestres (0-3) e a porcentagem de dias não conciliados 
    lista_dias_nao_conciliados_trim = []
    for i in porc_dias_nao_conciliados_trim:
        i = round((i*100), 2)
        lista_dias_nao_conciliados_trim.append(i)

    if trim_selecionado == '1º Trimestre':
        return lista_dias_nao_conciliados_trim[0] 
    elif trim_selecionado == '2º Trimestre':
        return lista_dias_nao_conciliados_trim[1]
    elif trim_selecionado == '3º Trimestre':
        return lista_dias_nao_conciliados_trim[2]
    elif trim_selecionado == '4º Trimestre':
        return lista_dias_nao_conciliados_trim[3]
    

# Cria tabela com dias não conciliados de cada casa por trimestre
def dias_nao_conciliados_casa_trim(df_conciliacao_farol, casa_selecionada, trim_selecionado, ano_farol, datas_completas):
    
    # Gera tabela de conciliação da casa
    df_conciliacao_casa = conciliacao_casa(df_conciliacao_farol, casa_selecionada, datas_completas) 

    # Filtra por ano do farol e trimestre
    if trim_selecionado == '1º Trimestre':
        df_dias_nao_conciliados_casa = df_conciliacao_casa[
        (df_conciliacao_casa['Data'].dt.year == ano_farol) &
        (df_conciliacao_casa['Data'].dt.month >= (1)) &
        (df_conciliacao_casa['Data'].dt.month <= (3))
        ]

    elif trim_selecionado == '2º Trimestre':
        df_dias_nao_conciliados_casa = df_conciliacao_casa[
        (df_conciliacao_casa['Data'].dt.year == ano_farol) &
        (df_conciliacao_casa['Data'].dt.month >= (4)) &
        (df_conciliacao_casa['Data'].dt.month <= (6))
        ]

    elif trim_selecionado == '3º Trimestre':
        df_dias_nao_conciliados_casa = df_conciliacao_casa[
        (df_conciliacao_casa['Data'].dt.year == ano_farol) &
        (df_conciliacao_casa['Data'].dt.month >= (7)) &
        (df_conciliacao_casa['Data'].dt.month <= (9))
        ]

    elif trim_selecionado == '4º Trimestre':
        df_dias_nao_conciliados_casa = df_conciliacao_casa[
        (df_conciliacao_casa['Data'].dt.year == ano_farol) &
        (df_conciliacao_casa['Data'].dt.month >= (10)) &
        (df_conciliacao_casa['Data'].dt.month <= (12))
        ]
    
    # Filtra por dias com conciliação != 0
    df_dias_nao_conciliados_casa = df_dias_nao_conciliados_casa[df_dias_nao_conciliados_casa['Conciliação'] != 0.0]
    qtd_dias_nao_conciliados = df_dias_nao_conciliados_casa['Conciliação'].count()
    return df_dias_nao_conciliados_casa, qtd_dias_nao_conciliados


# Gráfico de dias não conciliados por casa e trimestre
def grafico_dias_nao_conciliados_trim(df_conciliacao_farol, casas_validas, trimestre, lista_casas_trim, ano_farol, datas_completas):
    
    # Define as séries (barras) do eixo x (uma para cada casa)
    series = [
        {
            "name": nome,
            "type": "bar",
            "barGap": "10%",
            "data": [lista_casas_trim[i]],
            "label": {
                "show": True,
                "position": "top" 
            },
            "itemStyle": {"color": cores_casas[i]}
        }
        for i, nome in enumerate(casas_validas)
    ]

    grafico_dias_nao_conciliados_trim = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "data": casas_validas,
            "orient": "vertical",   # legenda em coluna
            "right": "0%",        
            "top": "center",
            "backgroundColor": "#ffffff55",
        },
        "grid": {
            "left": "2%", 
            "right": "23%", 
            "bottom": "0%", 
            "containLabel": True},
        "xAxis": [{
            "type": "category", 
            "axisTick": {"show": True}, 
            "data": [trimestre]}],
        "yAxis": [
            {
            "type": "value", 
            "axisLabel": {"formatter": "{value} %"}
            }
        ],
        "series": series
    }

    # Evento de clique - seleciona a casa
    events = {
        "click": "function(params) { return params.seriesName; }"
    }
    
    resultado_clique = st_echarts(options=grafico_dias_nao_conciliados_trim, events=events, height="550px", width="100%")
    # st_echarts embrulha o retorno do evento num objeto tipo-dict (chave 'chart_event')
    # nessa versão do Streamlit; em versões mais antigas o retorno já vem "cru"
    casa_selecionada = resultado_clique.get('chart_event') if hasattr(resultado_clique, 'get') else resultado_clique

    if not casa_selecionada:
        st.info("Selecione uma casa para visualizar os dias não conciliados")
    else:
        # Exibe dataframe dos dias não conciliados da casa no trimestre
        st.divider()
        st.subheader(f"Dias não conciliados - {casa_selecionada}")
        df_dias_nao_conciliados_casa, qtd_dias_nao_conciliados = dias_nao_conciliados_casa_trim(df_conciliacao_farol, casa_selecionada, trimestre, ano_farol, datas_completas)
        df_dias_nao_conciliados_casa_fmt = formata_df(df_dias_nao_conciliados_casa)
        st.dataframe(df_dias_nao_conciliados_casa_fmt, hide_index=True)
        st.write(f'**Quantidade de dias não conciliados:** {qtd_dias_nao_conciliados}')


# Tabela de resumo conciliação
def df_farol_conciliacao_mes(lista_casas_mes, df, ano_farol, mes_atual):
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_copia = df.copy()
    
    # Para cada mês, montar a lista com o valor de todas as casas
    for i, mes in enumerate(meses):
        coluna_mes = []
        coluna_mes_fmt = []
        for lista in lista_casas_mes:  # percorre a lista de porc de dias não conciliados de cada casa
            if (i == mes_atual - 1) and (ano_farol == ano_atual): # para mês e ano atual
                if lista[i] != 0: # se há dias não conciliados, faz 100 - qtd
                    porc_dias_conciliados = 100 - lista[i]
                else: porc_dias_conciliados = 100
            elif (i < mes_atual - 1) and (ano_farol == ano_atual): # para meses anteriores ao atual e ano atual
                porc_dias_conciliados = 100 - lista[i] # pega o mês i dessa casa
            elif (i > mes_atual - 1) and (ano_farol == ano_atual): # para meses posteriores ao atual e ano atual
                porc_dias_conciliados = 0
            else: # para anos anterioes
                porc_dias_conciliados = 100 - lista[i]   
            coluna_mes.append(porc_dias_conciliados)
            porc_dias_conciliados_fmt = f"{format_brazilian(porc_dias_conciliados)} %"
            coluna_mes_fmt.append(porc_dias_conciliados_fmt)

        # adiciona essa lista como coluna no df (20 valores)
        df[f'{mes}/{ano_farol}'] = coluna_mes
        df_copia[f'{mes}/{ano_farol}'] = coluna_mes_fmt
    
    return df_copia


# Estilo para células por porcentagem de conciliação 
def estilos_celulas(val, ano_atual, ano_farol, mes_atual, mes_farol):
    # Tenta tratar apenas valores que parecem porcentagem
    try:
        # remove '%' e converte para float
        numero = float(str(val).replace('%', '').replace(',', '.').strip())
    except:
        # se não der para converter (é texto), não pinta
        return ""
    
    if numero == 100:
        return "background-color: #b5e3bd; color: #216233;"
    elif numero != 0:
        return "background-color: #ffeeba; color: #e68700;"
    elif numero == 0 and ano_farol != ano_atual:
        return "background-color: #ff7b5a; color: #7a1b0c;"
    else:
        return ""

    
def df_farol_conciliacao_casa_mes(df_conciliacao_farol, casa_selecionada, lista_casas_mes, casas_validas, ano_farol, datas_completas):
    nomes_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    # Pega o indice da casa selecionada 
    for i, casa in enumerate(casas_validas):
        if casa_selecionada == casa:
            indice_casa = i

    # Cria a lista de indices dos meses nao conciliados de cada casa
    lista_meses_nao_conciliados_casa = []  
    for casa in lista_casas_mes:  
        lista_indices = [i for i, valor in enumerate(casa) if valor != 0]  
        lista_meses_nao_conciliados_casa.append(lista_indices)  

    for mes_nao_conciliado in lista_meses_nao_conciliados_casa[indice_casa]:
        st.markdown(f"<h4>{nomes_meses[mes_nao_conciliado]}</h4>", unsafe_allow_html=True)
        df_dias_nao_conciliados_casa, qtd_dias_nao_conciliados = dias_nao_conciliados_casa_mes(df_conciliacao_farol, casa_selecionada, mes_nao_conciliado, ano_farol, datas_completas)
        df_dias_nao_conciliados_casa_fmt = formata_df(df_dias_nao_conciliados_casa)
        st.dataframe(df_dias_nao_conciliados_casa_fmt, hide_index=True)
        st.write(f'**Quantidade de dias não conciliados:** {qtd_dias_nao_conciliados}')
        st.divider()
