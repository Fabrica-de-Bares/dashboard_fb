import streamlit as st
import pandas as pd
from utils.functions.general_functions import *
from utils.components import *
from utils.queries_clientes import *

st.set_page_config(
    page_title="Clientes e Ticket Médio",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

config_sidebar()

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment='center')
with col1:
    st.title("👥 Clientes e Ticket Médio")
with col3:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
st.divider()

DIAS_SEMANA_ORDEM = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']


def formata_duracao(minutos):
    if pd.isna(minutos):
        return '—'
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f'{horas}h {mins:02d}m'


# Paleta categórica fixa — uma cor por análise, nunca reaproveitada por ranking/estado
COR_TICKET_MEDIO_PERIODO = '#2a78d6'      # azul
COR_TICKET_MEDIO_DIA_SEMANA = '#eb6834'   # laranja
COR_PERMANENCIA = '#1baf7a'               # água

COR_GRID = '#e1e0d9'
COR_EIXO = '#c3c2b7'
COR_LABEL_EIXO = '#898781'


def opcoes_grafico_linha(labels_x, valores, nome_serie, cor, nome_eixo_y):
    return {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "line", "lineStyle": {"color": COR_EIXO}}},
        "grid": {"left": "60", "right": "4%", "bottom": "20%", "containLabel": True},
        "xAxis": [{
            "type": "category",
            "data": labels_x,
            "axisLabel": {"rotate": 45, "fontSize": 10, "color": COR_LABEL_EIXO},
            "axisLine": {"lineStyle": {"color": COR_EIXO}},
        }],
        "yAxis": [{
            "type": "value",
            "name": nome_eixo_y,
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"color": COR_LABEL_EIXO},
            "splitLine": {"lineStyle": {"color": COR_GRID}},
        }],
        "series": [{
            "name": nome_serie,
            "type": "line",
            "data": valores,
            "lineStyle": {"width": 2, "color": cor},
            "itemStyle": {"color": cor},
            "symbol": "circle",
            "symbolSize": 8,
            "areaStyle": {"color": cor, "opacity": 0.1},
        }],
    }


col1, col2 = st.columns([1, 2])
with col1:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless', 'Todas as Casas']
    id_casa, casa, id_zigpay = input_selecao_casas(
        lista_retirar_casas, key='seletor_casa_clientes_ticket_medio', adicionar_delivery=True
    )
with col2:
    periodo = input_periodo_datas(key='periodo_clientes_ticket_medio')

if not periodo or len(periodo) != 2:
    st.warning('Selecione um período válido (data de início e data de fim).')
    st.stop()

data_inicio, data_fim = periodo

st.divider()

# Seções 1 e 2 compartilham a mesma query de ticket médio
df_ticket_medio = GET_TICKET_MEDIO_ZIGPAY(id_casa, data_inicio, data_fim)

with st.container(border=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('### 📈 Ticket Médio no Período')
    with col2:
        filtros_selecionados = st.pills(
            label='',
            options=['🚫 Remover outliers'],
            selection_mode='multi',
            key='pill_remover_outliers_ticket_medio'
        )

    if df_ticket_medio.empty:
        st.warning('Sem dados de ticket médio para a casa e período selecionados.')
    else:
        df_ticket_medio['Ticket Médio'] = pd.to_numeric(df_ticket_medio['Ticket Médio'], errors='coerce')
        mediana_bruta = df_ticket_medio['Ticket Médio'].median()
        limite_superior_outlier = mediana_bruta * 3
        limite_inferior_outlier = mediana_bruta * 0.2

        df_outliers = df_ticket_medio[
            ~df_ticket_medio['Ticket Médio'].between(limite_inferior_outlier, limite_superior_outlier)
        ]

        # A remoção de outliers vale apenas para esta análise (Ticket Médio no Período) —
        # a seção de Ticket Médio por Dia da Semana usa sempre o df_ticket_medio original.
        if '🚫 Remover outliers' in (filtros_selecionados or []):
            df_ticket_medio_periodo = df_ticket_medio[
                df_ticket_medio['Ticket Médio'].between(limite_inferior_outlier, limite_superior_outlier)
            ]
        else:
            df_ticket_medio_periodo = df_ticket_medio

        if df_ticket_medio_periodo.empty:
            st.info('Todos os dias do período foram removidos como outliers.')

    if not df_ticket_medio.empty and not df_ticket_medio_periodo.empty:
        media_periodo = df_ticket_medio_periodo['Ticket Médio'].mean()
        _, col_kpi_periodo, _ = st.columns([1, 1, 1])
        with col_kpi_periodo:
            st.metric(label='Ticket Médio do Período', value=f'R$ {format_brazilian(media_periodo)}' if pd.notna(media_periodo) else '—', border=True)

        df_ticket_medio_ordenado = df_ticket_medio_periodo.sort_values('Data Evento')
        options_ticket_medio = opcoes_grafico_linha(
            df_ticket_medio_ordenado['Data Evento'].astype(str).tolist(),
            df_ticket_medio_ordenado['Ticket Médio'].round(2).tolist(),
            'Ticket Médio',
            COR_TICKET_MEDIO_PERIODO,
            'R$',
        )
        st.caption('Evolução do ticket médio diário no período selecionado')
        st_echarts(options=options_ticket_medio, height="400px", key='echarts_ticket_medio_periodo')

        with st.expander(f'Ver outliers identificados ({len(df_outliers)})'):
            if df_outliers.empty:
                st.caption('Nenhum outlier identificado no período selecionado.')
            else:
                st.write(escape_dolar(
                    'Outliers: Dias em que o Ticket Médio foi maior que 300% da mediana ou menor que 20% '
                    f'da mediana dos tickets médios do período (fora da faixa de R$ {format_brazilian(limite_inferior_outlier)} '
                    f'a R$ {format_brazilian(limite_superior_outlier)}).'
                ))
                df_outliers_tabela = df_outliers[['Data Evento', 'Dia Semana', 'Ticket Médio']].sort_values('Data Evento').copy()
                df_outliers_tabela['Ticket Médio'] = df_outliers_tabela['Ticket Médio'].apply(lambda v: f'R$ {format_brazilian(v)}')
                col_vazio, col_download = st.columns([5, 1])
                with col_download:
                    button_download(df_outliers_tabela, 'outliers_ticket_medio_periodo', 'download_outliers_ticket_medio_periodo')
                st.dataframe(df_outliers_tabela, hide_index=True, width='stretch')

        with st.expander('Ver dados em tabela'):
            df_ticket_medio_tabela = df_ticket_medio_ordenado[['Data Evento', 'Dia Semana', 'Ticket Médio']].copy()
            df_ticket_medio_tabela['Ticket Médio'] = df_ticket_medio_tabela['Ticket Médio'].apply(lambda v: f'R$ {format_brazilian(v)}')
            col_vazio, col_download = st.columns([5, 1])
            with col_download:
                button_download(df_ticket_medio_tabela, 'ticket_medio_periodo', 'download_ticket_medio_periodo')
            st.dataframe(df_ticket_medio_tabela, hide_index=True, width='stretch')

st.divider()

with st.container(border=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('### 📅 Ticket Médio por Dia da Semana')
    with col2:
        filtros_selecionados_dia_semana = st.pills(
                label='',
                options=['🚫 Remover outliers'],
                selection_mode='multi',
                key='pill_remover_outliers_dia_semana'
            )
    if df_ticket_medio.empty:
        st.warning('Sem dados de ticket médio para a casa e período selecionados.')
    else:
        dia_semana_selecionado = st.selectbox('Selecione o dia da semana', DIAS_SEMANA_ORDEM, key='seletor_dia_semana_ticket_medio')
        df_dia_semana = df_ticket_medio[df_ticket_medio['Dia Semana'] == dia_semana_selecionado].sort_values('Data Evento')

        if df_dia_semana.empty:
            st.warning(f'Sem dados de ticket médio para {dia_semana_selecionado} no período selecionado.')
        else:
            mediana_dia_semana_bruta = df_dia_semana['Ticket Médio'].median()
            limite_superior_outlier_dia_semana = mediana_dia_semana_bruta * 3
            limite_inferior_outlier_dia_semana = mediana_dia_semana_bruta * 0.2

            df_outliers_dia_semana = df_dia_semana[
                ~df_dia_semana['Ticket Médio'].between(limite_inferior_outlier_dia_semana, limite_superior_outlier_dia_semana)
            ]

            if '🚫 Remover outliers' in (filtros_selecionados_dia_semana or []):
                df_dia_semana_filtrado = df_dia_semana[
                    df_dia_semana['Ticket Médio'].between(limite_inferior_outlier_dia_semana, limite_superior_outlier_dia_semana)
                ]
            else:
                df_dia_semana_filtrado = df_dia_semana

            if df_dia_semana_filtrado.empty:
                st.info(f'Todos os dias de {dia_semana_selecionado} do período foram removidos como outliers.')
            else:
                media_dia_semana = df_dia_semana_filtrado['Ticket Médio'].mean()
                _, col_kpi_dia_semana, _ = st.columns([1, 1, 1])
                with col_kpi_dia_semana:
                    st.metric(label=f'Ticket Médio - {dia_semana_selecionado}', value=f'R$ {format_brazilian(media_dia_semana)}' if pd.notna(media_dia_semana) else '—', border=True)

                options_ticket_medio_dia_semana = opcoes_grafico_linha(
                    df_dia_semana_filtrado['Data Evento'].astype(str).tolist(),
                    df_dia_semana_filtrado['Ticket Médio'].round(2).tolist(),
                    f'Ticket Médio - {dia_semana_selecionado}',
                    COR_TICKET_MEDIO_DIA_SEMANA,
                    'R$',
                )
                st.caption(f'Evolução do ticket médio às {dia_semana_selecionado}s no período selecionado')
                st_echarts(options=options_ticket_medio_dia_semana, height="400px", key='echarts_ticket_medio_dia_semana')

                with st.expander(f'Ver outliers identificados ({len(df_outliers_dia_semana)})'):
                    if df_outliers_dia_semana.empty:
                        st.caption('Nenhum outlier identificado para esse dia da semana no período selecionado.')
                    else:
                        st.write(escape_dolar(
                            'Outliers: Dias em que o Ticket Médio foi maior que 300% da mediana ou menor que 20% '
                            f'da mediana dos tickets médios de {dia_semana_selecionado} no período (fora da faixa de '
                            f'R$ {format_brazilian(limite_inferior_outlier_dia_semana)} a R$ {format_brazilian(limite_superior_outlier_dia_semana)}).'
                        ))
                        df_outliers_dia_semana_tabela = df_outliers_dia_semana[['Data Evento', 'Dia Semana', 'Ticket Médio']].sort_values('Data Evento').copy()
                        df_outliers_dia_semana_tabela['Ticket Médio'] = df_outliers_dia_semana_tabela['Ticket Médio'].apply(lambda v: f'R$ {format_brazilian(v)}')
                        col_vazio, col_download = st.columns([5, 1])
                        with col_download:
                            button_download(df_outliers_dia_semana_tabela, 'outliers_ticket_medio_dia_semana', 'download_outliers_ticket_medio_dia_semana')
                        st.dataframe(df_outliers_dia_semana_tabela, hide_index=True, width='stretch')

                with st.expander('Ver dados em tabela'):
                    df_dia_semana_tabela = df_dia_semana_filtrado[['Data Evento', 'Dia Semana', 'Ticket Médio']].copy()
                    df_dia_semana_tabela['Ticket Médio'] = df_dia_semana_tabela['Ticket Médio'].apply(lambda v: f'R$ {format_brazilian(v)}')
                    col_vazio, col_download = st.columns([5, 1])
                    with col_download:
                        button_download(df_dia_semana_tabela, 'ticket_medio_dia_semana', 'download_ticket_medio_dia_semana')
                    st.dataframe(df_dia_semana_tabela, hide_index=True, width='stretch')

st.divider()

# Seção 3: Tempo de Permanência
with st.container(border=True):
    st.markdown('### ⏱️ Tempo de Permanência dos Clientes')
    df_checkins = GET_CHECKINS_CLIENTES_PERIODO(id_casa, data_inicio, data_fim)

    if df_checkins.empty:
        st.warning('Sem dados de check-in/check-out para a casa e período selecionados.')
    else:
        df_checkins['Check-in'] = pd.to_datetime(df_checkins['Check-in'], errors='coerce')
        df_checkins['Check-out'] = pd.to_datetime(df_checkins['Check-out'], errors='coerce')

        num_sem_checkout = df_checkins['Check-out'].isna().sum()
        df_permanencia = df_checkins[df_checkins['Check-out'].notna()].copy()

        if num_sem_checkout > 0:
            st.info(f'{num_sem_checkout} check-in(s) sem checkout registrado no período — não entram na média de permanência.')

        if df_permanencia.empty:
            st.warning('Nenhum check-in com checkout registrado para calcular a permanência no período selecionado.')
        else:
            df_permanencia['Duração'] = df_permanencia['Check-out'] - df_permanencia['Check-in']
            # Corrige casos em que o checkout ocorre após a virada do dia
            duracao_negativa = df_permanencia['Duração'] < pd.Timedelta(0)
            df_permanencia.loc[duracao_negativa, 'Duração'] += pd.Timedelta(days=1)
            df_permanencia['Duração (min)'] = df_permanencia['Duração'].dt.total_seconds() / 60

            media_permanencia_min = df_permanencia['Duração (min)'].mean()
            _, col_kpi_permanencia, _ = st.columns([1, 1, 1])
            with col_kpi_permanencia:
                st.metric(label='Permanência Média', value=formata_duracao(media_permanencia_min), border=True)

            df_permanencia_dia = df_permanencia.groupby('Data Evento')['Duração (min)'].mean().reset_index().sort_values('Data Evento')
            options_permanencia = opcoes_grafico_linha(
                df_permanencia_dia['Data Evento'].astype(str).tolist(),
                df_permanencia_dia['Duração (min)'].round(1).tolist(),
                'Permanência Média (min)',
                COR_PERMANENCIA,
                'Minutos',
            )
            st.caption('Permanência média dos clientes por dia, no período selecionado')
            st_echarts(options=options_permanencia, height="400px", key='echarts_permanencia_dia')

            df_permanencia_tabela = df_permanencia[['Cliente', 'CPF', 'Telefone', 'Data Evento', 'Check-in', 'Check-out']].copy()
            df_permanencia_tabela['Duração'] = df_permanencia['Duração (min)'].apply(formata_duracao)
            df_permanencia_tabela['Check-in'] = df_permanencia_tabela['Check-in'].dt.strftime('%d/%m/%Y %H:%M')
            df_permanencia_tabela['Check-out'] = df_permanencia_tabela['Check-out'].dt.strftime('%d/%m/%Y %H:%M')

            datas_disponiveis_permanencia = ['Todos os dias'] + [str(d) for d in df_permanencia_dia['Data Evento'].tolist()]
            data_selecionada_permanencia = st.selectbox(
                'Filtrar detalhamento por dia', datas_disponiveis_permanencia, key='seletor_data_detalhamento_permanencia'
            )
            if data_selecionada_permanencia != 'Todos os dias':
                df_permanencia_tabela = df_permanencia_tabela[
                    df_permanencia['Data Evento'].astype(str) == data_selecionada_permanencia
                ]

            col1, col2 = st.columns([4, 1], vertical_alignment='center')
            with col1:
                st.markdown('#### Detalhamento por cliente')
            with col2:
                button_download(df_permanencia_tabela, 'permanencia_clientes', 'download_permanencia_clientes')
            st.dataframe(df_permanencia_tabela, hide_index=True, width='stretch')
