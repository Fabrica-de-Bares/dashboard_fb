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
    st.write("Baixe a planilha de DRE já configurada e preenchida para a casa selecionada.")
with col2:
    st.button(label='Atualizar dados', key='atualizar_dre', on_click=st.cache_data.clear)
st.divider()

with st.container(border=True): 
    # Seletor de casa
    df_casas = GET_CASAS()
    casas = [casa for casa in casas_validas if casa not in ['Blue Note SP (Novo)', 'Escritório Fabrica de Bares', 'Edificio Rolim', 'Girondino', 'Girondino - CCBB', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ']]
    casas.append('Girondino - Consolidado')
    casas.append('Terraço Notie')
    casas.sort()
    casa = st.selectbox("Selecione uma casa", casas)
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"])) # Recupera id da casa

    if casa == 'Girondino - Consolidado': id_casa = 156
    elif casa == 'Terraço Notie': id_casa = 149
    # GET_CASAS normaliza ID 178 para 110 (mesma empresa bruta), então não existe linha
    # própria para 178 em df_casas/mapeamento_casas — precisa do hardcode aqui.
    elif casa == 'Blue Note SP (Sala 2)': id_casa = 178
    else: id_casa = mapeamento_casas[casa]


    ###################### EXPORTANDO DRE EM EXCEL ###################### 

    # st.divider()
    st.write("")
    # st.subheader(f'Fazer download - Excel DRE: {casa}')
    excel_filename = f'assets/sheets/Base_DRE - {id_casa}.xlsx'

    # st.write("Arquivo:", excel_filename) # Verificação do arquivo
    # st.write("Existe:", os.path.exists(excel_filename))
    # st.write("Tamanho:", os.path.getsize(excel_filename))

    # try:
    #     wb = openpyxl.load_workbook(excel_filename)
    # except Exception:
    #     st.code(traceback.format_exc())

    # Casas com mais de um place
    # 2026-08-14: Blue Note SP (Sala 2) (178) separado do Blue Note - São Paulo (110+131)
    # para ter DRE próprio — antes as 3 empresas brutas eram agregadas num único download.
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
    elif casa == 'Girondino - Consolidado': ids_casa_delivery = [181]
    else: ids_casa_delivery = None

    if st.button('Atualizar e baixar arquivo', type='secondary', icon=":material/progress_activity:"):
        status = st.empty()
        status.warning('Preperando dados do arquivo...')

        # Carrega dados das abas
        ## Faturamento
        df_aut_faturamento_zig = DRE_AUT_FATURAMENTO_ZIG(ids_casa_query)
        df_aut_receitas_extraord = DRE_AUT_RECEITAS_EXTRAORD(ids_casa_query)
        if casa in ['Priceless', 'Terraço Notie']: df_bd_eventos_novo = DRE_BD_EVENTOS_NOVO_PRICELESS(ids_casa_query)
        else: df_bd_eventos_novo = DRE_BD_EVENTOS_NOVO(ids_casa_query)
        ## Ajustes manuais
        df_aut_ajustes_manuais = DRE_AJUSTES_MANUAIS(ids_casa_query)
        ## Despesas
        df_aut_blue_me_sem_pedido = DRE_AUT_BLUE_ME_SEM_PEDIDO(ids_casa_query)
        df_aut_blue_me_com_pedido = DRE_AUT_BLUE_ME_COM_PEDIDO(ids_casa_query)
        df_aut_folha = DRE_AUT_FOLHA(ids_casa_query)
        df_aut_descontos = DRE_AUT_DESCONTOS(ids_casa_query)
        df_aut_promocoes = DRE_AUT_PROMOCOES_UTILIZADAS(ids_casa_query)
        df_aut_endividamentos = DRE_AUT_ENDIVIDAMENTOS(ids_casa_query)
        ## CMV
        df_aut_contagem = DRE_AUT_CONTAGEM(ids_casa_query)
        df_aut_precos_insumos = DRE_AUT_PRECOS_INSUMOS(ids_casa_query)
        if casa == 'Love Cabaret': df_aut_valor_estoque = DRE_AUT_VALOR_ESTOQUE_LOVE(ids_casa_query)
        else: df_aut_valor_estoque = DRE_AUT_VALOR_ESTOQUE(ids_casa_query)
        # Fix 2026-08-11 revertido em 2026-09-02 (decisão do usuário, mesmo racional de
        # utils/functions/cmv.py::config_valoracao_estoque): as duas queries trazem a
        # linha crua sem dedupe. Até aqui, linhas com mesma loja+insumo+quantidade+valor
        # (achado real: Blue Note - São Paulo, jul/2026, "LA CAMPANA SELECCION DE
        # TERROIR 750ML", IDs de contagem 99745/103983) eram tratadas como reenvio
        # duplicado da mesma contagem e descartadas automaticamente antes do SUMIFS de
        # "Estoque Inicial/Final" (aba CMV_Manual). Com múltiplas contagens por casa em
        # pontos de estoque diferentes (BlueMe), essa combinação pode ser 2 contagens
        # físicas legítimas — decidir sozinho ficou arriscado demais, agora soma tudo
        # como está. Se for de fato reenvio, a correção é excluir a contagem errada em
        # T_CONTAGEM_INSUMOS (ver flag no script Mini_Gabu/BlueMe Dashboard) e reapurar.
        df_aut_precos_consolidados = DRE_AUT_PRECOS_CONSOLIDADOS(ids_casa_query)
        df_aut_eventos_aeb = DRE_AUT_EVENTOS_AEB(ids_casa_query)
        df_aut_transferencias = DRE_AUT_TRANSFERENCIAS(ids_casa_query)
        df_aut_consumo_func = DRE_AUT_CONSUMO_FUNCIONARIOS(ids_casa_query)
        df_aut_insumos_prod = DRE_AUT_INSUMOS_PRODUCAO(ids_casa_query)
        ## Orçamento (alimenta a coluna ORÇADO da aba DRE via SUMIFS)
        df_t_orcamentos = DRE_ORCAMENTO_OPERACIONAL(ids_casa_query)
        df_t_headcount = DRE_HEADCOUNT_ORCADO(ids_casa_query)

        abas = {
            'T_ORCAMENTOS': df_t_orcamentos,
            'T_HEADCOUNT': df_t_headcount,
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
        if casa in ['Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Jacaré', 'Orfeu', 'Girondino - Consolidado']: # Delivery - Incluir 'Bar Brahma - Paulista'
            ids_casa_delivery = ",".join(map(str, ids_casa_delivery))
            abas['Aut_Faturamento_Zig_Delivery'] = DRE_AUT_FATURAMENTO_ZIG_DELIVERY(ids_casa_delivery)

        if casa in ['Priceless', 'Terraço Notie']: # Eventos Concierge
            abas['BD_Eventos_Concierge'] = DRE_EVENTOS_CONCIERGE(ids_casa_query)
            abas['BD_Eventos Geral'] = DRE_BD_EVENTOS_GERAL_PRICELESS()

        if casa not in ['Arcos', 'Blue Note - São Paulo', 'Blue Note SP (Sala 2)', 'Love Cabaret']: # Cartão Black - Adicionar 'Ultra Evil Premium Ltda '
            abas['Aut_Consumo_Cartao_Black'] = DRE_CONSUMO_CARTAO_BLACK(ids_casa_query)

        if casa in ['Love Cabaret', 'Ultra Evil Premium Ltda ']: # Bilheteria Automatizada - Adicionar casas restantes
            abas['Aut_Bilheteria'] = DRE_BILHETERIA_AUTOMATIZADA(ids_casa_query)

        if os.path.exists(excel_filename):
            wb = openpyxl.load_workbook(excel_filename) # Carrega Excel da casa
            for sheet_name, df in abas.items(): # Cria abas
                export_to_excel(wb, df, sheet_name)

            # Reorganiza a ordem das abas
            ordem = [
                'Rateio Despesas Compartilhadas',
                'DRE',
                'DRE CCBB',
                'DRE GIRONDINO',
                'Aut_BlueMe_Sem_Pedido',
                'Aut_BlueMe_Com_Pedido',
                'Aut_Ajustes_Manuais',
                'Aut_Faturamento_Zig',
                'Aut_Faturamento_Zig_Delivery',
                'Aut_Consumo_Cartao_Black',
                'Aut_Bilheteria',
                'Aut_Receitas_Extraord',
                'BD_Eventos_Novo',
                'BD_Eventos_Concierge',
                'BD_Eventos Geral',
                'CMV_Manual',
                'Aut_Folha',
                'Aut_Descontos',
                'Aut_Promocoes_Utilizadas',
                'Fiscal',
                'Aut_Endividamentos',
                'Aut_Contagem',
                'Aut_Precos_Insumos',
                'Aut_Valor_Estoque',
                'Aut_Precos_Consolidados_Mes',
                'Aut_Eventos_AeB',
                'Aut_Transferencias',
                'Aut_Consumo_Funcionarios',
                'Aut_Insumos_Producao',
                'T_ORCAMENTOS',
                'T_HEADCOUNT',
                'T_REAL'
            ]

            for i, nome in enumerate(ordem):
                if nome in wb.sheetnames:
                    ws = wb[nome]       # Guarda a referência antes
                    wb._sheets.remove(ws)
                    wb._sheets.insert(i, ws)

            wb.save(excel_filename) # Salva configurações do Excel
        
        status.success('Arquivo atualizado com sucesso!')
        with open(excel_filename, "rb") as file:
            file_content = file.read()
            st.download_button( # Botão de Download 
                label="Baixar Excel",
                icon=":material/download:",
                data=file_content,
                file_name=f"DRE - {casa}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type='secondary'
            )
