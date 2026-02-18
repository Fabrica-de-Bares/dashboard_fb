import streamlit as st
import pandas as pd
from utils.queries_financeiro import *
from utils.functions.financeiro_despesas import *
from utils.functions.general_functions import *
from utils.components import *
from utils.user import logout

st.set_page_config(
  layout = 'wide',
  page_title = 'Controle de Despesas Gerais',
  page_icon=':money_with_wings:',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')



config_sidebar()
col, col2, col3 = st.columns([6, 1, 1])
with col:
  st.title(':money_with_wings: Controle de Despesas Gerais')
with col2:
  st.button(label="Atualizar", on_click = st.cache_data.clear)

st.divider()
lojasComDados = preparar_dados_lojas_user_financeiro()
data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
# Seletores
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    # Filtro de casa:
  lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Edificio Rolim', 'Priceless', 'Todas as Casas']
  id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='calendario')
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
st.divider()

despesasDetalhadas = GET_DESPESAS()
despesasDetalhadas = filtrar_por_datas(despesasDetalhadas, data_inicio, data_fim, 'Data_Emissao')
despesasDetalhadas = filtrar_por_classe_selecionada(despesasDetalhadas, 'Loja', lojas_selecionadas)

Despesas2 = GET_DESPESAS().drop_duplicates()
Orcamentos = GET_ORCAMENTOS_DESPESAS().drop_duplicates()
Despesas = pd.merge(Despesas2, Orcamentos, on=['Primeiro_Dia_Mes', 'Loja', 'Classificacao_Contabil_1', 'Classificacao_Contabil_2'], how='outer')
Despesas['Data_Emissao'] = Despesas['Data_Emissao'].fillna(Despesas['Primeiro_Dia_Mes'])
Despesas = filtrar_por_datas(Despesas, data_inicio, data_fim, 'Data_Emissao')
Despesas = filtrar_por_classe_selecionada(Despesas, 'Loja', lojas_selecionadas)
despesasConfig = config_despesas_por_classe(Despesas)

tab1, tab2 = st.tabs(['Despesas Gerais', 'Despesas Detalhadas'])

with tab1:
    with st.container(border=True):
        col0, col1, col2 = st.columns([1, 15, 1])
        with col1:
            
            col1, col2= st.columns([4, 1], vertical_alignment='center')
            with col1:
              st.write("")
              st.markdown("## Despesas Gerais")
              st.write("")
            with col2:
              exibir_detalhamento = st.toggle(label='Exibir Detalhamento', key='toggle_despesas', value=True)
            
            exibir_despesas(despesasConfig, exibir_detalhamento=exibir_detalhamento)

                

despesaDetalhadaConfig = config_despesas_detalhado(despesasDetalhadas)

classificacoes1 = obter_valores_unicos_ordenados(despesaDetalhadaConfig, 'Class. Contábil 1')

permissoes, user_name, email = config_permissoes_user()
if 'GERENTE DE SUPRIMENTOS' in permissoes:
  classificacoes1 = ['Custo Mercadoria Vendida', 'Utilidades', 'Manutenção']

with tab2:
  with st.container(border=True):
    st.write("")
    col0, col1, col2 = st.columns([1, 15, 1])
    with col1:
      col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1], vertical_alignment='center')
      with col3:
        st.markdown("## Despesas Detalhadas")
      with col4:
        if 'Acesso Financeiro 2' in permissoes:
          classificacoes_1_selecionadas = st.multiselect(label='Selecione Classificação Contábil 1', options=classificacoes1, default=classificacoes1)
        else:
          classificacoes_1_selecionadas = st.multiselect(label='Selecione Classificação Contábil 1', options=classificacoes1)
        
      despesaDetalhadaConfig = filtrar_por_classe_selecionada(despesaDetalhadaConfig, 'Class. Contábil 1', classificacoes_1_selecionadas)
      with col5:
        classificacoes2 = obter_valores_unicos_ordenados(despesaDetalhadaConfig, 'Class. Contábil 2')
        classificacoes_2_selecionadas = st.multiselect(label='Selecione Classificação Contábil 2', options=classificacoes2)
      despesaDetalhadaConfig = filtrar_por_classe_selecionada(despesaDetalhadaConfig, 'Class. Contábil 2', classificacoes_2_selecionadas)
      with col6:
        fornecedores = obter_valores_unicos_ordenados(despesaDetalhadaConfig, 'Fornecedor')
        fornecedores_selecionados = st.multiselect(label='Selecione Fornecedores', options=fornecedores)
      despesaDetalhadaConfig = filtrar_por_classe_selecionada(despesaDetalhadaConfig, 'Fornecedor', fornecedores_selecionados)

      st.write("")
      valorTotal = despesaDetalhadaConfig['Valor'].sum()
      valorTotal = format_brazilian(valorTotal)
      despesaDetalhadaConfig = format_columns_brazilian(despesaDetalhadaConfig, ['Valor'])
      despesaDetalhadaConfig = despesaDetalhadaConfig.rename(columns={'Doc_Serie': 'Doc. Série'})
      despesaDetalhadaConfig = despesaDetalhadaConfig[['ID Despesa', 'Loja', 'Class. Contábil 1', 'Class. Contábil 2',  'Fornecedor', 'Doc. Série', 'Data Emissão', 'Data Vencimento', 'Descrição', 'Status',  'Valor' ]]
      st.dataframe(despesaDetalhadaConfig, height=500, width='stretch', hide_index=True)
      st.markdown(f"**Valor Total = R$ {valorTotal}**")