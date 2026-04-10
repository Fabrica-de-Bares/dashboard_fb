from datetime import timedelta
import streamlit as st
import pandas as pd
from utils.functions.date_functions import *
from utils.queries_cmv import *
from utils.functions.cmv import *
from utils.functions.general_functions import *
from utils.components import *
from utils.user import logout

st.set_page_config(
  layout = 'wide',
  page_title = 'CMV Real',
  page_icon='⚖️',
  initial_sidebar_state="collapsed"
)  
pd.set_option('future.no_silent_downcasting', True)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')


def highlight_rows_cmv_dre(linha):
  linhas = [
    'CMV Alimentos',
    'CMV Bebidas',
    'CMV Geral'
  ]

  linhas_entrada = [
    '(+) Estoque inicial Alimento',
    '(+) Estoque inicial Bebida',
    '(+) Estoque inicial Produção Alimentos',
    '(+) Estoque inicial Produção Bebidas',
    '(+) Compra de Alimento',
    '(+) Compra de Bebida',
    '(+) Entradas transferência Alimentos',
    '(+) Entradas transferência Bebidas',
  ]

  linhas_saida = [
    '(-) Saídas transferência Alimentos',
    '(-) Saídas transferência Bebidas',
    '(-) Quebras e perdas',
    '(-) Estoque final Alimentos',
    '(-) Estoque final Bebidas',
    '(-) Fechamento Produção Alimentos',
    '(-) Fechamento Produção Bebidas',
  ]

  linhas_amarelo = [
    '(-) Consumo Funcionário',
  ]

  linhas_cinza = [
    '(=) Custo Alimento Vendido',
    '(=) Custo Bebida Vendida',
    'Somatório de A&B',
  ]

  if linha['Descrição'] in linhas_cinza:
    return ['background-color: #E6EAF1'] * len(linha)
  elif linha['Descrição'] in linhas_amarelo:
    return ['background-color: #FFFCE7'] * len(linha)
  elif linha['Descrição'] in linhas_entrada:
    return ['background-color: #E8F2FC'] * len(linha)
  elif linha['Descrição'] in linhas_saida:
    return ['background-color: #FFEDED'] * len(linha)
  else:
    return

config_sidebar()
col, col2, col3 = st.columns([6, 1, 1])
with col:
  st.title('⚖️ CMV Real')
with col2:
  st.button(label="Atualizar", on_click = st.cache_data.clear)
st.divider()


data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
lojas_selecionadas, data_inicio, data_fim = criar_seletores_cmv(data_inicio_default, data_fim_default)
st.divider()

data_inicio_mes_anterior = (data_inicio.replace(day=1) - timedelta(days=1)).replace(day=1)
data_fim_mes_anterior = data_inicio.replace(day=1) - timedelta(days=1)

df_faturamento_delivery, df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_alimentos_delivery, faturamento_bebidas_delivery = config_faturamento_bruto_zig(data_inicio, data_fim, lojas_selecionadas)
df_faturamento_eventos, faturamento_alimentos_eventos, faturamento_bebidas_eventos = config_faturamento_eventos(data_inicio, data_fim, lojas_selecionadas, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
df_compras, compras_alimentos, compras_bebidas = config_compras(data_inicio, data_fim, lojas_selecionadas)
df_valoracao_estoque_atual = config_valoracao_estoque(data_inicio, data_fim, lojas_selecionadas)
df_valoracao_estoque_mes_anterior = config_valoracao_estoque(data_inicio_mes_anterior, data_fim_mes_anterior, lojas_selecionadas)
df_diferenca_estoque, df_diferenca_estoque_download = config_diferenca_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior)
df_variacao_estoque, variacao_estoque_alimentos, variacao_estoque_bebidas = config_variacao_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior)
df_insumos_sem_pedido = config_insumos_blueme_sem_pedido(data_inicio, data_fim, lojas_selecionadas)
df_insumos_com_pedido = config_insumos_blueme_com_pedido(data_inicio, data_fim, lojas_selecionadas)
df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas = config_transferencias_gastos(data_inicio, data_fim, lojas_selecionadas)
df_transf_entradas, df_transf_saidas = config_transferencias_detalhadas(data_inicio, data_fim, lojas_selecionadas)
df_producao_alimentos, df_producao_bebidas, valor_producao_alimentos, valor_producao_bebidas = config_valoracao_producao(data_inicio, lojas_selecionadas)
df_producao_alimentos_mes_anterior, df_producao_bebidas_mes_anterior, valor_producao_alimentos_mes_anterior, valor_producao_bebidas_mes_anterior = config_valoracao_producao(data_inicio_mes_anterior, lojas_selecionadas)
df_diferenca_producao_alimentos = config_diferenca_producao(df_producao_alimentos, df_producao_alimentos_mes_anterior)
df_diferenca_producao_bebidas = config_diferenca_producao(df_producao_bebidas, df_producao_bebidas_mes_anterior)
df_producao_total = config_producao_agregada(df_producao_alimentos, df_producao_bebidas, df_producao_alimentos_mes_anterior, df_producao_bebidas_mes_anterior)

# Layout DRE
valoracao_estoque_atual_alimentos, valoracao_estoque_atual_bebidas, valoracao_estoque_mes_anterior_alimentos, valoracao_estoque_mes_anterior_bebidas = config_valoracao_estoque_valores(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior)
st.write(faturamento_bruto_alimentos)

df_producao_alimentos.drop(columns=['ID_Loja', 'Loja'], inplace=True)
df_producao_bebidas.drop(columns=['ID_Loja', 'Loja'], inplace=True)
df_valoracao_estoque_atual.drop(columns=['ID_Loja', 'Loja'], inplace=True)

df_valoracao_estoque_atual = df_valoracao_estoque_atual.rename(columns={
    'ID_Insumo': 'ID Insumo',
    'Valor_em_Estoque': 'Valor em Estoque',
    'Unidade_Medida': 'Unidade de Medida'
})
df_valoracao_estoque_atual = df_valoracao_estoque_atual[['Categoria', 'ID Insumo', 'Insumo', 'Unidade de Medida', 'Quantidade', 'Valor em Estoque']]

# Salva valores para download
df_valoracao_estoque_atual_download = df_valoracao_estoque_atual.copy()
df_producao_total_download = df_producao_total.copy()

df_faturamento_total = config_faturamento_total(df_faturamento_delivery, df_faturamento_zig, df_faturamento_eventos)
df_valoracao_estoque_atual = format_columns_brazilian(df_valoracao_estoque_atual, ['Valor em Estoque', 'Quantidade'])
df_producao_alimentos = format_columns_brazilian(df_producao_alimentos, ['Valor_Total', 'Quantidade', 'Valor_Unidade_Medida'])
df_producao_bebidas = format_columns_brazilian(df_producao_bebidas, ['Valor_Total', 'Quantidade', 'Valor_Unidade_Medida'])
df_producao_total = format_columns_brazilian(df_producao_total, ['Valor Produção Mês Anterior', 'Valor Produção Atual'])
diferenca_producao_alimentos = valor_producao_alimentos - valor_producao_alimentos_mes_anterior
diferenca_producao_bebidas = valor_producao_bebidas - valor_producao_bebidas_mes_anterior

cmv_alimentos = compras_alimentos - variacao_estoque_alimentos - saida_alimentos + entrada_alimentos - consumo_interno - diferenca_producao_alimentos
cmv_bebidas = compras_bebidas - variacao_estoque_bebidas - saida_bebidas + entrada_bebidas - diferenca_producao_bebidas
cmv_alimentos_e_bebidas = cmv_alimentos + cmv_bebidas
faturamento_total_alimentos = faturamento_bruto_alimentos + faturamento_alimentos_delivery + faturamento_alimentos_eventos
faturamento_total_bebidas = faturamento_bruto_bebidas + faturamento_bebidas_delivery + faturamento_bebidas_eventos

if faturamento_total_alimentos != 0:
  cmv_percentual_alim = (cmv_alimentos / faturamento_total_alimentos) * 100
else:
  cmv_percentual_alim = 0

if faturamento_total_bebidas != 0:
  cmv_percentual_bebidas = (cmv_bebidas / faturamento_total_bebidas) * 100
else:
  cmv_percentual_bebidas = 0

if faturamento_total_alimentos + faturamento_total_bebidas != 0:
  cmv_percentual_geral = ((cmv_alimentos + cmv_bebidas)/(faturamento_total_alimentos + faturamento_total_bebidas)) * 100
else:
  cmv_percentual_geral = 0

df_cmv_dre_download = pd.DataFrame({
  '(+) Estoque inicial Alimento': [valoracao_estoque_mes_anterior_alimentos],
  '(+) Estoque inicial Bebida': [valoracao_estoque_mes_anterior_bebidas],
  '(+) Estoque inicial Produção Alimentos': [valor_producao_alimentos_mes_anterior],
  '(+) Estoque inicial Produção Bebidas': [valor_producao_bebidas_mes_anterior],
  '(+) Compra de Alimento': [compras_alimentos],
  '(+) Compra de Bebida': [compras_bebidas],
  '(+) Entradas transferência Alimentos': [entrada_alimentos],
  '(+) Entradas transferência Bebidas': [entrada_bebidas],
  '(-) Saídas transferência Alimentos': [saida_alimentos],
  '(-) Saídas transferência Bebidas': [saida_bebidas],
  '(-) Consumo Funcionário': [consumo_interno],
  '(-) Quebras e perdas': [quebras_e_perdas],
  '(-) Estoque final Alimentos': [valoracao_estoque_atual_alimentos],
  '(-) Estoque final Bebidas': [valoracao_estoque_atual_bebidas],
  '(-) Fechamento Produção Alimentos': [valor_producao_alimentos],
  '(-) Fechamento Produção Bebidas': [valor_producao_bebidas],
  '(=) Custo Alimento Vendido': [cmv_alimentos],
  '(=) Custo Bebida Vendida': [cmv_bebidas],
  'Somatório de A&B': [cmv_alimentos_e_bebidas],
  'CMV Alimentos': [f'{cmv_percentual_alim} %'],
  'CMV Bebidas': [f'{cmv_percentual_bebidas} %'],
  'CMV Geral': [f'{cmv_percentual_geral} %']
})

# Transpor o DataFrame
df_cmv_dre_download = df_cmv_dre_download.T.reset_index()
df_cmv_dre_download = df_cmv_dre_download.copy()
df_cmv_dre_download.columns = ['Descrição', 'Valor']

faturamento_bruto_alimentos = format_brazilian(faturamento_bruto_alimentos)
faturamento_bruto_bebidas = format_brazilian(faturamento_bruto_bebidas)
faturamento_alimentos_delivery = format_brazilian(faturamento_alimentos_delivery)
faturamento_bebidas_delivery = format_brazilian(faturamento_bebidas_delivery)
faturamento_alimentos_eventos = format_brazilian(faturamento_alimentos_eventos)
faturamento_bebidas_eventos = format_brazilian(faturamento_bebidas_eventos)
compras_alimentos = format_brazilian(compras_alimentos)
compras_bebidas = format_brazilian(compras_bebidas)
variacao_estoque_alimentos = format_brazilian(variacao_estoque_alimentos)
variacao_estoque_bebidas = format_brazilian(variacao_estoque_bebidas) 
cmv_alimentos = format_brazilian(cmv_alimentos)
cmv_bebidas = format_brazilian(cmv_bebidas)
cmv_alimentos_e_bebidas = format_brazilian(cmv_alimentos_e_bebidas)
cmv_percentual_alim = format_brazilian(cmv_percentual_alim)
cmv_percentual_bebidas = format_brazilian(cmv_percentual_bebidas)
cmv_percentual_geral = format_brazilian(cmv_percentual_geral)
entrada_alimentos = format_brazilian(entrada_alimentos)
entrada_bebidas = format_brazilian(entrada_bebidas)
saida_alimentos = format_brazilian(saida_alimentos)
saida_bebidas = format_brazilian(saida_bebidas)
consumo_interno = format_brazilian(consumo_interno)
diferenca_producao_alimentos = format_brazilian(diferenca_producao_alimentos)
diferenca_producao_bebidas = format_brazilian(diferenca_producao_bebidas)

quebras_e_perdas = format_brazilian(quebras_e_perdas)
valoracao_estoque_mes_anterior_alimentos = format_brazilian(valoracao_estoque_mes_anterior_alimentos)
valoracao_estoque_mes_anterior_bebidas = format_brazilian(valoracao_estoque_mes_anterior_bebidas)
valoracao_estoque_atual_alimentos = format_brazilian(valoracao_estoque_atual_alimentos)
valoracao_estoque_atual_bebidas = format_brazilian(valoracao_estoque_atual_bebidas)
valor_producao_alimentos = format_brazilian(valor_producao_alimentos)
valor_producao_bebidas = format_brazilian(valor_producao_bebidas)
valor_producao_alimentos_mes_anterior = format_brazilian(valor_producao_alimentos_mes_anterior)
valor_producao_bebidas_mes_anterior = format_brazilian(valor_producao_bebidas_mes_anterior)

colA, colB = st.columns([1, 6])
  
with colA:
  with st.container():
      title_card_cmv('Faturamento')
  st.write('')
  with st.container():
      title_card_cmv('Estoque e Produção')
  st.write('')
  with st.container():
      title_card_cmv('Compras, Entradas e Saídas de A&B')
  st.write('')
  with st.container():
      title_card_cmv('CMV')


with colB:
  col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1], vertical_alignment='center')
  with col1:
    card_cmv('Faturamento Alimentos', f'R$ {faturamento_bruto_alimentos}', is_estoque=False)
  with col2:
    card_cmv('Faturamento Bebidas', f'R$ {faturamento_bruto_bebidas}', is_estoque=False)
  with col3:
    card_cmv('Faturam. Alim. Delivery', f'R$ {faturamento_alimentos_delivery}', is_estoque=False)
  with col4:
    card_cmv('Faturam. Beb. Delivery', f'R$ {faturamento_bebidas_delivery}', is_estoque=False)
  with col5:
    card_cmv('Faturam. Alim. Eventos', f'R$ {faturamento_alimentos_eventos}', is_estoque=False)
  with col6:
    card_cmv('Faturam. Beb. Eventos', f'R$ {faturamento_bebidas_eventos}', is_estoque=False)

  st.write('')

  col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1], vertical_alignment='center')
  with col1:
      card_cmv('Δ Estoque Alimentos', f'R$ {variacao_estoque_alimentos}', is_estoque=True)
  with col2:
      card_cmv('Δ Estoque Bebidas', f'R$ {variacao_estoque_bebidas}', is_estoque=True)
  with col3:
      card_cmv('Δ Produção Alimentos', f'R$ {diferenca_producao_alimentos}', is_estoque=True)
  with col4:
      card_cmv('Δ Produção Bebidas', f'R$ {diferenca_producao_bebidas}', is_estoque=True)
  with col5:
      card_cmv('Consumo Interno', f'R$ {consumo_interno}', is_estoque=True)

  st.write('')

  col1, col2, col3, col4, col5, col6 = st.columns(6)
  with col1:
    card_cmv('Compras Alimentos', f'R$ {compras_alimentos}', is_estoque=False)
  with col2:
    card_cmv('Compras Bebidas', f'R$ {compras_bebidas}', is_estoque=False)
  with col3:
    card_cmv('Entrada Alimentos', f'R$ {entrada_alimentos}', is_estoque=False)
  with col4:
    card_cmv('Saída Alimentos', f'R$ {saida_alimentos}', is_estoque=False)
  with col5:
    card_cmv('Entrada Bebidas', f'R$ {entrada_bebidas}', is_estoque=False)
  with col6:
    card_cmv('Saída Bebidas', f'R$ {saida_bebidas}', is_estoque=False)

  st.write('')

  col1, col2, col3, col4, col5 = st.columns(5)
  with col1:
    card_cmv('CMV Alimentos', f'R$ {cmv_alimentos}', is_estoque=False)
  with col2:
    card_cmv('CMV Bebidas', f'R$ {cmv_bebidas}', is_estoque=False)
  with col3:
    card_cmv('CMV Percentual Alimentos', f'{cmv_percentual_alim} %', is_estoque=False)
  with col4:
    card_cmv('CMV Percentual Bebidas', f'{cmv_percentual_bebidas} %', is_estoque=False)
  with col5:
    card_cmv('CMV Percentual Geral', f'{cmv_percentual_geral} %', is_estoque=False)

st.divider()
st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)


# Layout Novo - Parecido com a DRE
df_cmv_dre = pd.DataFrame({
  '(+) Estoque inicial Alimento': [valoracao_estoque_mes_anterior_alimentos],
  '(+) Estoque inicial Bebida': [valoracao_estoque_mes_anterior_bebidas],
  '(+) Estoque inicial Produção Alimentos': [valor_producao_alimentos_mes_anterior],
  '(+) Estoque inicial Produção Bebidas': [valor_producao_bebidas_mes_anterior],
  '(+) Compra de Alimento': [compras_alimentos],
  '(+) Compra de Bebida': [compras_bebidas],
  '(+) Entradas transferência Alimentos': [entrada_alimentos],
  '(+) Entradas transferência Bebidas': [entrada_bebidas],
  '(-) Saídas transferência Alimentos': [saida_alimentos],
  '(-) Saídas transferência Bebidas': [saida_bebidas],
  '(-) Consumo Funcionário': [consumo_interno],
  '(-) Quebras e perdas': [quebras_e_perdas],
  '(-) Estoque final Alimentos': [valoracao_estoque_atual_alimentos],
  '(-) Estoque final Bebidas': [valoracao_estoque_atual_bebidas],
  '(-) Fechamento Produção Alimentos': [valor_producao_alimentos],
  '(-) Fechamento Produção Bebidas': [valor_producao_bebidas],
  '(=) Custo Alimento Vendido': [cmv_alimentos],
  '(=) Custo Bebida Vendida': [cmv_bebidas],
  'Somatório de A&B': [cmv_alimentos_e_bebidas],
  'CMV Alimentos': [f'{cmv_percentual_alim} %'],
  'CMV Bebidas': [f'{cmv_percentual_bebidas} %'],
  'CMV Geral': [f'{cmv_percentual_geral} %']
})
# Transpor o DataFrame
df_cmv_dre = df_cmv_dre.T.reset_index()
df_cmv_dre.columns = ['Descrição', 'Valor']

# Calcula a altura do dataframe
num_linhas = len(df_cmv_dre)
altura_cmv_dre = 35 * num_linhas + 38

# Aplica estilos no dataframe
df_cmv_dre_styled = df_cmv_dre.style.apply(highlight_rows_cmv_dre, axis=1)
col1, col2 = st.columns([6, 1], vertical_alignment="center")
with col2:
  button_download(df_cmv_dre_download, f"cmv_{format_date(data_inicio)}-{format_date(data_fim)}", key=f'download_{format_date(data_inicio)}-{format_date(data_fim)}')
st.dataframe(df_cmv_dre_styled, height=altura_cmv_dre, hide_index=True, width='stretch')


with st.container(border=True):
  col0, col1, col2 = st.columns([1, 12, 1])
  with col1:
    col1, col2 = st.columns([6, 1], vertical_alignment="center")
    with col1:
      st.subheader('Compras')
    with col2:
      button_download(df_compras, f'compras_{lojas_selecionadas}', f'compras_{lojas_selecionadas}')
    df_compras = format_columns_brazilian(df_compras, ['BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas'])
    st.dataframe(df_compras, hide_index=True)
    classificacoes = obter_valores_unicos_ordenados(df_insumos_sem_pedido, 'Classificacao')
    fornecedores_com_pedido = obter_valores_unicos_ordenados(df_insumos_com_pedido, 'Fornecedor') 
    with st.expander("Detalhes Insumos BlueMe Sem Pedido"):
      col3, col4, col5 = st.columns(3)
      with col4:
        classificacoes_selecionadas = st.multiselect(label='Selecione Classificação', options=classificacoes, key=1)
        df_insumos_sem_pedido = filtrar_por_classe_selecionada(df_insumos_sem_pedido, 'Classificacao', classificacoes_selecionadas)
      with col5:
        fornecedores_sem_pedido = obter_valores_unicos_ordenados(df_insumos_sem_pedido, 'Fornecedor') 
        fornecedores_selecionados = st.multiselect(label='Selecione Fornecedores', options=fornecedores_sem_pedido, key=3)
      df_insumos_sem_pedido = filtrar_por_classe_selecionada(df_insumos_sem_pedido, 'Fornecedor', fornecedores_selecionados)
      valor_total = df_insumos_sem_pedido['Valor'].sum()
      df_insumos_sem_pedido_download = df_insumos_sem_pedido.copy()
      df_insumos_sem_pedido = format_columns_brazilian(df_insumos_sem_pedido, ['Valor'])
      valor_total = format_brazilian(valor_total)
      st.dataframe(df_insumos_sem_pedido, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="center")
      with col1:
        st.write('Valor Total = **R$**', f'**{valor_total}**')
      with col2:
        button_download(df_insumos_sem_pedido_download, f'ins_s_pedido', f'ins_s_pedido')
    with st.expander("Detalhes Insumos BlueMe Com Pedido"):
      col3, col4, col5 = st.columns(3)
      with col5:
        fornecedores_selecionados = st.multiselect(label='Selecione Fornecedores', options=fornecedores_com_pedido, key=2)
      df_insumos_com_pedido = filtrar_por_classe_selecionada(df_insumos_com_pedido, 'Fornecedor', fornecedores_selecionados)
      valor_total_com_pedido = df_insumos_com_pedido['Valor Líquido'].sum()
      valor_alimentos = df_insumos_com_pedido['Valor Líq. Alimentos'].sum()
      valor_bebidas = df_insumos_com_pedido['Valor Líq. Bebidas'].sum()
      valor_hig = df_insumos_com_pedido['Valor Líq. Hig/Limp.'].sum()
      valor_gelo = df_insumos_com_pedido['Valor Líq Gelo/Gas/Carvão/Velas'].sum()
      valor_utensilios = df_insumos_com_pedido['Valor Líq. Utensilios'].sum()
      valor_outros = df_insumos_com_pedido['Valor Líq. Outros'].sum()

      valor_total_com_pedido = format_brazilian(valor_total_com_pedido)
      valor_alimentos = format_brazilian(valor_alimentos)
      valor_bebidas = format_brazilian(valor_bebidas) 
      valor_hig = format_brazilian(valor_hig) 
      valor_gelo = format_brazilian(valor_gelo)
      valor_utensilios = format_brazilian(valor_utensilios)
      valor_outros = format_brazilian(valor_outros)
      df_insumos_com_pedido_download = df_insumos_com_pedido.copy()
      df_insumos_com_pedido = format_columns_brazilian(df_insumos_com_pedido, ['Valor Líquido', 'Valor Cotação', 'Insumos - V. Líq', 'Valor Líq. Alimentos','Valor Líq. Bebidas',
                                        'Valor Líq. Hig/Limp.', 'Valor Líq Gelo/Gas/Carvão/Velas', 'Valor Líq. Utensilios', 'Valor Líq. Outros'])
      st.dataframe(df_insumos_com_pedido, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="top")
      with col1:
        st.write(
          f"Valor Total = **R\\$ {valor_total_com_pedido}**  \n"
          f"Valor Alimentos = **R\\$ {valor_alimentos}**  \n"
          f"Valor Bebidas = **R\\$ {valor_bebidas}**  \n"
          f"Valor Hig/Limp. = **R\\$ {valor_hig}**  \n"
          f"Valor Gelo = **R\\$ {valor_gelo}**  \n"
          f"Valor Utensílios = **R\\$ {valor_utensilios}**  \n"
          f"Valor Outros = **R\\$ {valor_outros}**"
        )
      with col2:
        button_download(df_insumos_com_pedido_download, f'ins_c_pedido', f'ins_c_pedido')


with st.container(border=True):
  col0, col1, col2 = st.columns([1, 12, 1])
  with col1:
    col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
    with col1:
      st.subheader('Valoração e Variação de Estoque')
    with col2:
      button_download(df_variacao_estoque, f'val_var_estoque', f'val_var_estoque')
    df_variacao_estoque = format_columns_brazilian(df_variacao_estoque, ['Estoque Mes Anterior', 'Estoque Atual'])
    st.dataframe(df_variacao_estoque, width='stretch', hide_index=True)
    with st.expander("Detalhes Valoração Estoque Atual"):
      st.dataframe(df_valoracao_estoque_atual, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col2:
        button_download(df_valoracao_estoque_atual_download, f'val_estoque_atual', f'val_estoque_atual')
    with st.expander("Diferença de Estoque"):
      st.dataframe(df_diferenca_estoque, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col2:
        button_download(df_diferenca_estoque_download, f'dif_estoque', f'dif_estoque')

df_producao_alimentos = df_producao_alimentos.rename(columns={
    'Item_Produzido': 'Item Produzido',
    'Unidade_Medida': 'Unidade de Medida',
    'Valor_Unidade_Medida': 'Valor Unidade de Medida',
    'Valor_Total': 'Valor Total'
})
df_producao_alimentos = df_producao_alimentos[['Categoria', 'Item Produzido', 'Unidade de Medida', 'Valor Unidade de Medida', 'Quantidade', 'Valor Total']]
df_producao_bebidas = df_producao_bebidas.rename(columns={
    'Item_Produzido': 'Item Produzido',
    'Unidade_Medida': 'Unidade de Medida',
    'Valor_Unidade_Medida': 'Valor Unidade Medida',
    'Valor_Total': 'Valor Total'
})
df_producao_bebidas = df_producao_bebidas[['Categoria', 'Item Produzido', 'Unidade de Medida', 'Valor Unidade Medida', 'Quantidade', 'Valor Total']]

df_diferenca_producao_alimentos = df_diferenca_producao_alimentos.rename(columns={
    'Item_Produzido': 'Item Produzido'
})
df_diferenca_producao_alimentos = df_diferenca_producao_alimentos[['Categoria', 'Item Produzido', 'Unidade de Medida', 'Quantidade Anterior', 'Valor Total Anterior', 'Quantidade Atual', 'Valor Total Atual', 'Diferença Quantidade', 'Diferença Valor Total']]
df_diferenca_producao_bebidas = df_diferenca_producao_bebidas.rename(columns={
    'Item_Produzido': 'Item Produzido'
})
df_diferenca_producao_bebidas = df_diferenca_producao_bebidas[['Categoria', 'Item Produzido', 'Unidade de Medida', 'Quantidade Anterior', 'Valor Total Anterior', 'Quantidade Atual', 'Valor Total Atual', 'Diferença Quantidade', 'Diferença Valor Total']]

# Salva para download
df_producao_alimentos_download = df_producao_alimentos.copy()
df_producao_bebidas_download = df_producao_bebidas.copy()
df_diferenca_producao_alimentos_download = df_diferenca_producao_alimentos.copy()
df_diferenca_producao_bebidas_download = df_diferenca_producao_bebidas.copy()

with st.container(border=True):
  col0, col1, col2 = st.columns([1, 12, 1])
  with col1:
    col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
    with col1:
      st.subheader('Inventário de Produção')
    with col2:
      button_download(df_producao_total_download, f'inv_producao', f'inv_producao')
    st.dataframe(df_producao_total, width='stretch', hide_index=True)
    with st.expander("Detalhes Valoração Estoque Atual"):
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col1:
        st.subheader('Valoração de Produção Alimentos')
      with col2:
        button_download(df_producao_alimentos_download, f'val_producao_alimentos', f'val_producao_alimentos')
      st.dataframe(df_producao_alimentos, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col1:
        st.subheader('Valoração de Produção Bebidas')
      with col2:
        button_download(df_producao_bebidas_download, f'val_producao_bebidas', f'val_producao_bebidas')
      st.dataframe(df_producao_bebidas, width='stretch', hide_index=True)
    with st.expander("Diferença de Valoração de Produção"):
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col1:
        st.subheader('Diferença de Produção Alimentos')
      with col2:
        button_download(df_diferenca_producao_alimentos_download, f'dif_producao_alimentos', f'dif_producao_alimentos')
      st.dataframe(df_diferenca_producao_alimentos, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col1:
        st.subheader('Diferença de Produção Bebidas')
      with col2:
        button_download(df_diferenca_producao_bebidas_download, f'dif_producao_bebidas', f'dif_producao_bebidas')
      st.dataframe(df_diferenca_producao_bebidas, width='stretch', hide_index=True)

with st.container(border=True):
  col0, col1, col2 = st.columns([1, 12, 1])
  with col1:
    col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
    with col1:
      st.subheader('Transferências e Gastos Extras')
    with col2:
      button_download(df_transf_e_gastos, f'transf_e_gastos', f'transf_e_gastos')
    df_transf_e_gastos = format_columns_brazilian(df_transf_e_gastos, ['Entrada Alimentos', 'Entrada Bebidas', 'Saída Alimentos', 'Saída Bebidas', 'Consumo Interno', 'Quebras e Perdas'])
    st.dataframe(df_transf_e_gastos, width='stretch', hide_index=True) 
    with st.expander("Detalhes Transferências Entradas"):
      df_transf_entradas_download = df_transf_entradas.copy()
      df_tranf_entradas = format_columns_brazilian(df_transf_entradas, ['Valor Transferência'])
      st.dataframe(df_transf_entradas, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col2:
        button_download(df_transf_entradas_download, f'transf_entradas', f'transf_entradas')
    with st.expander("Detalhes Transferências Saídas"):
      df_transf_saidas_download = df_transf_saidas.copy()
      df_transf_saidas = format_columns_brazilian(df_transf_saidas, ['Valor Transferência'])
      st.dataframe(df_transf_saidas, width='stretch', hide_index=True)
      col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
      with col2:
        button_download(df_transf_saidas_download, f'transf_saidas', f'transf_saidas')
