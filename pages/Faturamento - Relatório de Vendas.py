import streamlit as st
import pandas as pd
from utils.queries_financeiro import *
from utils.functions.financeiro_faturamento_zigpay import *
from utils.functions.produtos_relatorio_vendas import *
from utils.functions.general_functions import *
from utils.components import *
from utils.user import logout
from datetime import time

st.set_page_config(
  layout = 'wide',
  page_title = 'Relatório de Vendas',
  page_icon='🛍️',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')


def grafico_linhas_faturamento_tipos(df, coluna_soma: str, key):
    
    df = df.copy()

    # Mapeamento de inglês → abreviado em português sem acento
    dias_semana_abrev = {
        "Monday": "Seg",
        "Tuesday": "Ter",
        "Wednesday": "Qua",
        "Thursday": "Qui",
        "Friday": "Sex",
        "Saturday": "Sab",
        "Sunday": "Dom"
    }

    df['Data_Evento'] = pd.to_datetime(df['Data_Evento'])
    df[coluna_soma] = df[coluna_soma].astype(float)

    # Cria uma coluna com o dia da semana abreviado
    df['Dia da Semana'] = df['Data_Evento'].dt.day_name().map(dias_semana_abrev)

    # Formatar rótulo Data + Dia
    df.loc[:, 'Data_Label'] = df['Data_Evento'].dt.strftime("%Y-%m-%d") + " (" + df['Dia da Semana'] + ")"

    df = df.groupby(['Data_Evento', 'Tipo', 'Data_Label']).agg({
      coluna_soma: 'sum',
      'Dia da Semana': 'first'
    }).reset_index()
  
    todas_datas = df['Data_Evento'].unique()
    todos_tipos = df['Tipo'].unique()

    idx = pd.MultiIndex.from_product(
        [todas_datas, todos_tipos],
        names=['Data_Evento', 'Tipo']
    )

    # Reindexar preenchendo zeros
    df = (
        df.set_index(['Data_Evento', 'Tipo'])
          .reindex(idx, fill_value=0)
          .reset_index()
    )

    # Recriar a coluna Data_Label depois do reindex
    df['Data_Label'] = df['Data_Evento'].dt.strftime("%Y-%m-%d") + " (" + df['Data_Evento'].dt.day_name().map(dias_semana_abrev) + ")"

    # Preparar séries de dados para o gráfico
    datas = df.drop_duplicates('Data_Evento').sort_values('Data_Evento')['Data_Label'].tolist()
    series = []
    for tipo in todos_tipos:
        serie_categoria = df[df['Tipo'] == tipo].sort_values('Data_Evento')
        series.append({
            "name": tipo,
            "type": "line",
            "stack": "Total",
            "areaStyle": {},
            "emphasis": {"focus": "series"},
            "data": serie_categoria[coluna_soma].astype(float).tolist(),
        })

    # Configurações do gráfico
    options = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
        },
        "legend": {"data": todos_tipos.tolist()},
        "toolbox": {"feature": {"saveAsImage": {}}},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": [{"type": "category", "boundaryGap": False, "data": datas}],
        "yAxis": [{"type": "value"}],
        "series": series,
    }

    # Renderizar no Streamlit
    return st_echarts(options=options, height="400px", key=key)

def classificacao_momento_consumo(row):
  if pd.notna(row['Data da Venda']):
    hora_venda = pd.to_datetime(row['Data da Venda']).time()

    if hora_venda <= time(6, 0):
      return 'Madrugada'
    elif hora_venda <= time(11, 0):
      return 'Manhã'
    elif hora_venda <= time(15, 0):
      return 'Almoço'
    elif hora_venda <= time(19, 0):
      return 'Happy Hour'
    else:
      return 'Jantar'
  return None
  
    

def main():
  config_sidebar()
  col, col2, col3 = st.columns([6, 1, 1])
  with col:
    st.title('🛍️ Relatório de Vendas')
  with col2:
    st.button(label="Atualizar", on_click = st.cache_data.clear)
  st.divider()

  data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
  # Seletores
  col1, col2, col3 = st.columns([2, 1, 1])
  with col1:
     # Filtro de casa:
    lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless', 'Todas as Casas']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='calendario', adicionar_delivery=True)
    lojas_selecionadas = [casa]
  with col2:
    data_inicio = st.date_input(
        'Data de Início',
        value=data_inicio_default,
        key='data_inicio_input',
        format="DD/MM/YYYY"
    )
  with col3:
    data_fim = st.date_input(
        'Data de Fim',
        value=data_fim_default,
        key='data_fim_input',
        format="DD/MM/YYYY"
    )

    # Converte as datas selecionadas para o formato Timestamp
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)
  
  max_dias = 31*4
  if data_fim - data_inicio > pd.Timedelta(days=max_dias):
    st.error(f'O intervalo de datas deve ser menor ou igual a {max_dias} dias para esta análise.')
    st.stop()

  OrcamentoFaturamento = config_orcamento_faturamento(lojas_selecionadas, data_inicio, data_fim) 
  orcamfatformatado = OrcamentoFaturamento.copy()
  categorias_desejadas = ['Alimentos', 'Bebidas', 'Couvert', 'Gifts']
  soma_valor_bruto = orcamfatformatado.loc[orcamfatformatado['Categoria'].isin(categorias_desejadas), 'Valor Bruto'].sum()
  soma_valor_bruto = format_brazilian(soma_valor_bruto)
  orcamfatformatado = format_columns_brazilian(orcamfatformatado, ['Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido', 'Faturam - Orçamento'])
  orcamfatformatado.loc[orcamfatformatado['Orçamento'] == '0,00', 'Atingimento %'] = '-'
  
  st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)

  FaturamentoZig = config_Faturamento_zig(lojas_selecionadas, data_inicio, data_fim)


  with st.container(border=True):
    col0, col1, col2 = st.columns([0.1, 2.6, 0.1])
    with col1:
      # Filtro por categoria desejada
      st.markdown("## Análise por Categorias")
      col1, col2 = st.columns([1, 1])
      with col1:
        categoria = st.selectbox(label='Selecione Categoria', options=categorias_desejadas)
      FaturamentoZigClasse = filtrar_por_classe_selecionada(FaturamentoZig, 'Categoria', [categoria]).copy()
      FaturamentoZigMomentoConsumo = FaturamentoZig.copy()
      classificacoes = obter_valores_unicos_ordenados(FaturamentoZigClasse, 'Tipo')
      with col2:
        classificacoes_selecionadas = st.multiselect(label='Selecione Tipos', options=classificacoes)
      FaturamentoZigClasse = filtrar_por_classe_selecionada(FaturamentoZigClasse, 'Tipo', classificacoes_selecionadas)
      FaturamentoZigClasseAgrupado = FaturamentoZigClasse.copy().groupby(['Data_Evento', 'ID Produto', 'Nome Produto']).agg({
        'Loja': 'first',
        'Categoria': 'first',
        'Tipo': 'first',
        'Preço Unitário': 'first',
        'Quantia comprada': 'sum',
        'Desconto': 'sum',
        'Valor Bruto Venda': 'sum',
        'Valor Líquido Venda': 'sum'
      }).reset_index()
      st.write('')

      st.subheader("Curva de Faturamento por Tipo de Produto")
      grafico_linhas_faturamento_tipos(FaturamentoZigClasse, 'Valor Bruto Venda', 'grafico_linhas_faturamento_tipos')
      st.write('')
      st.subheader(f"Número de Vendas de {categoria} por Tipo")
      grafico_linhas_faturamento_tipos(FaturamentoZigClasse, 'Quantia comprada', 'grafico_linhas_quantias_tipos')

      # Itens Vendidos Detalhado por Transação - Categoria de Produto
      col1, col2 = st.columns([4, 1], vertical_alignment = "center")
      with col1:
          st.markdown('### Itens Vendidos Detalhado por Transação')
      FaturamentoZigClasse['Momento Consumo'] = FaturamentoZigClasse.apply(
        classificacao_momento_consumo, axis=1
      )
      with col2:
          button_download(FaturamentoZigClasse, f'itens', f'download_itens')
      dias_map = {
          'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
          'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
      }
      FaturamentoZigClasse['Data da Venda'] = pd.to_datetime(FaturamentoZigClasse['Data da Venda'])
      FaturamentoZigClasse['Dia da Semana'] = FaturamentoZigClasse['Data da Venda'].dt.day_name().map(dias_map)

      FaturamentoZigClasseFormatado = FaturamentoZigClasse.copy()
      FaturamentoZigClasseFormatado['Data da Venda'] = pd.to_datetime(
      FaturamentoZigClasse['Data da Venda'], 
          format='%d-%m-%Y %H:%M:%S'
      )
      FaturamentoZigClasseFormatado = format_columns_brazilian(FaturamentoZigClasseFormatado, ['Valor Bruto Venda', 'Valor Líquido Venda', 'Preço Unitário'])
      
      FaturamentoZigClasseFormatado = FaturamentoZigClasseFormatado[['ID Venda', 'Loja', 'Data da Venda', 'Data_Evento', 'Dia da Semana', 'Momento Consumo', 'ID Produto', 'Nome Produto', 'Preço Unitário', 'Quantia comprada', 'Desconto', 'Categoria', 'Tipo', 'Valor Bruto Venda', 'Valor Líquido Venda']]
      dataframe_aggrid(
          df=FaturamentoZigClasseFormatado,
          name="Itens Vendidos Detalhado por Transação",
          num_columns=["Preço Unitário", "Quantia comprada", "Desconto", "Valor Bruto Venda", "Valor Líquido Venda"],
          date_columns=["Data_Evento"],
          datetime_columns=["Data da Venda"],
          height=500,
          fit_columns=ColumnsAutoSizeMode.FIT_CONTENTS,
          fit_columns_on_grid_load=True
      )

      # Itens Vendidos Agrupados por Data
      col1, col2 = st.columns([4, 1], vertical_alignment = "center")
      with col1:
          st.markdown('### Itens Vendidos Agrupados por Data')
      with col2:
          button_download(FaturamentoZigClasseAgrupado, f'itens_agrupados', f'download_itens_agrupados')
      FaturamentoZigClasseAgrupado = format_columns_brazilian(FaturamentoZigClasseAgrupado, ['Valor Bruto Venda', 'Valor Líquido Venda', 'Preço Unitário', 'Desconto'])
      st.dataframe(FaturamentoZigClasseAgrupado, width='stretch', hide_index=True)

  # with st.container(border=True):
  #   col0, col1, col2 = st.columns([0.1, 2.6, 0.1])
  #   with col1:
  #     st.markdown('## Análise de Faturamento')
  #     # Faturamento por Dia da Semana e Momento de Consumo
  #     col1, col2 = st.columns([4, 1], vertical_alignment = "center")
  #     with col1:
  #         st.markdown('### Média por Dia da Semana e Momento de Consumo')
      
  #     FaturamentoZigClasseMomentoConsumoDia = FaturamentoZig.copy()
  #     FaturamentoZigClasseMomentoConsumoDia['Momento Consumo'] = FaturamentoZigClasseMomentoConsumoDia.apply(
  #       classificacao_momento_consumo, axis=1
  #     )
  #     FaturamentoZigClasseMomentoConsumoDia['Data_Evento'] = pd.to_datetime(FaturamentoZigClasseMomentoConsumoDia['Data_Evento'])
  #     FaturamentoZigClasseMomentoConsumoDia['Dia da Semana'] = FaturamentoZigClasseMomentoConsumoDia['Data_Evento'].dt.day_name().map(dias_map)
  #     FaturamentoZigClasseMomentoConsumoDia['Mes-Ano'] = FaturamentoZigClasseMomentoConsumoDia['Data_Evento'].dt.strftime('%m/%Y')
  #     df_por_dia = FaturamentoZigClasseMomentoConsumoDia.groupby(
  #         ['Data_Evento', 'Dia da Semana', 'Mes-Ano', 'Momento Consumo']
  #     ).agg({
  #         'Quantia comprada': 'sum',
  #         'Desconto': 'sum',
  #         'Valor Bruto Venda': 'sum',
  #         'Valor Líquido Venda': 'sum'
  #     }).reset_index()

  #     # Etapa 2: média por dia da semana + momento de consumo + mês
  #     df_media_dia_semana = df_por_dia.groupby(
  #         ['Mes-Ano', 'Dia da Semana', 'Momento Consumo']
  #     ).agg({
  #         'Quantia comprada': 'mean',
  #         'Desconto': 'mean',
  #         'Valor Bruto Venda': 'mean',
  #         'Valor Líquido Venda': 'mean'
  #     }).reset_index()

  #     # Renomeia colunas
  #     df_media_dia_semana.rename(columns={
  #         'Quantia comprada': 'N° Médio de Itens Vendidos',
  #         'Desconto': 'Valor Médio de Descontos',
  #         'Valor Bruto Venda': 'Faturamento Bruto Médio',
  #         'Valor Líquido Venda': 'Faturamento Líquido Médio'
  #     }, inplace=True)
      
  #     df_media_dia_semana_download = df_media_dia_semana.copy()
  #     df_media_dia_semana = format_columns_brazilian(df_media_dia_semana, ['N° Médio de Itens Vendidos', 'Valor Médio de Descontos', 'Faturamento Bruto Médio', 'Faturamento Líquido Médio'])

  #     with col2:
  #       button_download(df_media_dia_semana_download, f'media_dia_semana', f'download_media_dia_semana')

  #     dataframe_aggrid(
  #         df=df_media_dia_semana,
  #         name="Média de Faturamento por Dia da Semana e Momento de Consumo",
  #         num_columns=["N° Médio de Itens Vendidos", "Valor Médio de Descontos", "Faturamento Bruto Médio", "Faturamento Líquido Médio"],
  #         date_columns=["Data_Evento"],
  #         datetime_columns=["Data da Venda"],
  #         height=500,
  #         fit_columns=ColumnsAutoSizeMode.FIT_CONTENTS,
  #         fit_columns_on_grid_load=True
  #     )

  #     with st.container(border=True):
  #       momentos = [
  #           ("🌅", "Manhã", "6h–11h"),
  #           ("☀️", "Almoço", "11h–15h"),
  #           ("🍹", "Happy Hour", "15h–19h"),
  #           ("🌙", "Jantar", "19h–00h"),
  #           ("🌃", "Madrugada", "00h–06h"),
  #       ]
  #       items_html = "".join([
  #           f'<div style="display:flex; align-items:center; gap:6px; white-space:nowrap;">'
  #           f'<span>{emoji}</span>'
  #           f'<span style="font-weight:600; font-size:0.82rem;">{titulo}</span>'
  #           f'<span style="font-size:0.78rem; color:#999;">{horario}</span>'
  #           f'</div>'
  #           for emoji, titulo, horario in momentos
  #       ])
  #       st.markdown(f"""
  #           <div style="display:flex; flex-wrap:wrap; gap:16px 24px; align-items:center; justify-content:center; padding: 4px 0;">
  #               {items_html}
  #           </div>
  #       """, unsafe_allow_html=True)




if __name__ == '__main__':
  main()
