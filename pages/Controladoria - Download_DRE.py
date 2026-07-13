import streamlit as st
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import *
from utils.queries_dre_download import *
from utils.components import input_selecao_casas, seletor_ano, seletor_mes
import os
import traceback


st.set_page_config(
    page_title="Download - DRE",
    page_icon="📥",
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
    st.title("📥 Download - DRE")
    st.write("Baixe a planilha de DRE já configurada para a casa selecionada.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_dre', on_click=st.cache_data.clear)
st.divider()

# Seletores de casa e data
col1, col2, col3 = st.columns(3)
# with col1: 
df_casas = GET_CASAS()
casas = [casa for casa in casas_validas if casa not in ['Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Escritório Fabrica de Bares', 'Edificio Rolim', 'Girondino', 'Girondino - CCBB', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ']]
casas.append('Girondino - Consolidado')
casas.append('Terraço Notie')
casas.sort()
casa = st.selectbox("Selecione uma casa", casas)
mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"])) # Recupera id da casa
    
if casa == 'Girondino - Consolidado': id_casa = 156
elif casa == 'Terraço Notie': id_casa = 149
else: id_casa = mapeamento_casas[casa] 

# with col2:
#     mes_selecionado = int(seletor_mes('Selecione um mês', 'mes_forecast'))
# with col3:
#     ano_selecionado = seletor_ano(2026, datas['ano_atual'], 'ano_forecast')
st.divider()


###################### EXPORTANDO DRE EM EXCEL ###################### 

with st.container(border=True): # Exportando em Excel
    st.subheader(f'Fazer download - Excel DRE: {casa}')
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
    elif casa in ['Priceless', 'Terraço Notie']: ids_casa_query = [149, 161, 162, 179]
    elif casa == 'Girondino - Consolidado': ids_casa_query = [156, 160]
    else: ids_casa_query = [id_casa]

    ids_casa_query = ",".join(map(str, ids_casa_query)) # Formata para utilizar na query

    # Casas com delivery
    if casa == 'Bar Brahma - Centro': ids_casa_delivery = [117, 118]
    elif casa == 'Bar Léo - Centro': ids_casa_delivery = [103]
    elif casa == 'Bar Brahma - Granja': ids_casa_delivery = [169]
    # elif casa == 'Bar Brahma - Paulista': ids_casa_delivery = [] # A definir
    elif casa == 'Jacaré': ids_casa_delivery = [139]
    elif casa == 'Orfeu': ids_casa_delivery = [112]
    else: ids_casa_delivery = None

    if st.button('Atualizar e baixar arquivo'):
        status = st.empty()
        status.warning('Preperando dados do arquivo...')

        # Carrega dados das abas
        df_aut_blue_me_sem_pedido = DRE_AUT_BLUE_ME_SEM_PEDIDO(ids_casa_query)
        df_aut_blue_me_com_pedido = DRE_AUT_BLUE_ME_COM_PEDIDO(ids_casa_query)
        df_aut_faturamento_zig = DRE_AUT_FATURAMENTO_ZIG(ids_casa_query)
        df_aut_receitas_extraord = DRE_AUT_RECEITAS_EXTRAORD(ids_casa_query)
        if casa in ['Priceless', 'Terraço Notie']: df_bd_eventos_novo = DRE_BD_EVENTOS_NOVO_PRICELESS(ids_casa_query)
        else: df_bd_eventos_novo = DRE_BD_EVENTOS_NOVO(ids_casa_query)
        df_aut_folha = DRE_AUT_FOLHA(ids_casa_query)
        df_aut_descontos = DRE_AUT_DESCONTOS(ids_casa_query)
        df_aut_promocoes = DRE_AUT_PROMOCOES_UTILIZADAS(ids_casa_query)
        df_aut_endividamentos = DRE_AUT_ENDIVIDAMENTOS(ids_casa_query)
        df_aut_contagem = DRE_AUT_CONTAGEM(ids_casa_query)
        df_aut_precos_insumos = DRE_AUT_PRECOS_INSUMOS(ids_casa_query)
        if casa == 'Love Cabaret': df_aut_valor_estoque = DRE_AUT_VALOR_ESTOQUE_LOVE(ids_casa_query)
        else: df_aut_valor_estoque = DRE_AUT_VALOR_ESTOQUE(ids_casa_query)
        df_aut_precos_consolidados = DRE_AUT_PRECOS_CONSOLIDADOS(ids_casa_query)
        df_aut_eventos_aeb = DRE_AUT_EVENTOS_AEB(ids_casa_query)
        df_aut_transferencias = DRE_AUT_TRANSFERENCIAS(ids_casa_query)
        df_aut_consumo_func = DRE_AUT_CONSUMO_FUNCIONARIOS(ids_casa_query)
        df_aut_insumos_prod = DRE_AUT_INSUMOS_PRODUCAO(ids_casa_query)
        df_aut_ajustes_manuais = DRE_AJUSTES_MANUAIS(ids_casa_query)

        abas = {
            'Aut_BlueMe_Sem_Pedido': df_aut_blue_me_sem_pedido,
            'Aut_BlueMe_Com_Pedido': df_aut_blue_me_com_pedido,
            'Aut_Faturamento_Zig': df_aut_faturamento_zig,
            'Aut_Receitas_Extraord': df_aut_receitas_extraord,
            'BD_Eventos_Novo': df_bd_eventos_novo,
            'Aut_Folha': df_aut_folha,
            'Aut_Descontos': df_aut_descontos,
            'Aut_Promocoes_Utilizadas': df_aut_promocoes,
            'Aut_Endividamentos': df_aut_endividamentos,
            'Aut_Contagem': df_aut_contagem,
            'Aut_Precos_Insumos': df_aut_precos_insumos,
            'Aut_Valor_Estoque': df_aut_valor_estoque,
            'Aut_Precos_Consolidados_Mes': df_aut_precos_consolidados,
            'Aut_Eventos_AeB': df_aut_eventos_aeb,
            'Aut_Transferencias': df_aut_transferencias,
            'Aut_Consumo_Funcionarios': df_aut_consumo_func,
            'Aut_Insumos_Producao': df_aut_insumos_prod,
            'Aut_Ajustes_Manuais': df_aut_ajustes_manuais,
        }

        # Casos específicos
        if casa in ['Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Jacaré', 'Orfeu']: # Delivery - Incluir 'Bar Brahma - Paulista'
            ids_casa_delivery = ",".join(map(str, ids_casa_delivery))
            abas['Aut_Faturamento_Zig_Delivery'] = DRE_AUT_FATURAMENTO_ZIG_DELIVERY(ids_casa_delivery)

        if casa in ['Priceless', 'Terraço Notie']: # Eventos Concierge
            abas['BD_Eventos_Concierge'] = DRE_EVENTOS_CONCIERGE(ids_casa_query)
            abas['BD_Eventos Geral'] = DRE_BD_EVENTOS_GERAL_PRICELESS()

        if casa not in ['Arcos', 'Blue Note - São Paulo', 'Love Cabaret']: # Cartão Black - Adicionar 'Ultra Evil Premium Ltda '
            abas['Aut_Consumo_Cartao_Black'] = DRE_CONSUMO_CARTAO_BLACK(ids_casa_query)

        if casa in ['Love Cabaret']: # Bilheteria Automatizada - por enquanto só Love
            abas['Aut_Bilheteria'] = DRE_BILHETERIA_AUTOMATIZADA(ids_casa_query)

        if os.path.exists(excel_filename):
            wb = openpyxl.load_workbook(excel_filename) # Carrega Excel da casa
            for sheet_name, df in abas.items(): # Cria abas
                export_to_excel(wb, df, sheet_name)

            wb.save(excel_filename) # Salva configurações do Excel
        
        status.success('Arquivo atualizado com sucesso!')
        with open(excel_filename, "rb") as file:
            file_content = file.read()
            st.download_button( # Botão de Download 
            label="Baixar Excel",
            data=file_content,
            file_name=f"DRE - {casa}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
