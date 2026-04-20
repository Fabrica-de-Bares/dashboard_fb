import streamlit as st
import pandas as pd
import pymysql
from utils.functions.general_functions import config_sidebar, mysql_connection_fb
from utils.functions.controladoria_descontos_dre import *
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download, seletor_ano

pd.set_option('future.no_silent_downcasting', True)


# Conexão com o banco de dados
conn = mysql_connection_fb()
c = conn.cursor(buffered=True)


st.set_page_config(
    page_title="DRE e Orçamento - Input no Sistema",
    page_icon="⬆️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("⬆️ DRE e Orçamento - Input no Sistema")
st.write("Aba que formata a planilha de Orçamento Operacional anual e as colunas de 'Real' para inserção automática no EPM.")
st.divider()

# Seletor do tipo de formatação
lista_formatacoes = ['Inputar - Orçamentos', 'Inputar - Real DRE']
tipo_formatacao = st.selectbox("Selecione o tipo de formatação:", lista_formatacoes)
st.divider()

# Seletor de casa e ano
if tipo_formatacao == 'Inputar - Real DRE':
    col1, col2, col3 = st.columns(3)
else: 
    col1, col2 = st.columns(2)

with col1:
    df_casas = GET_CASAS()
    casas = df_casas['Casa'].tolist()
    casas = [casa for casa in casas if casa not in ['Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ']]
    casa = st.selectbox("Selecione a casa referente ao arquivo:", casas)
    if casa == 'Blue Note - São Paulo':
        nome_casa = 'Blue Note SP'
    elif casa == 'Ultra Evil Premium Ltda ':
        nome_casa = 'Ultra Evil'
    else:
        nome_casa = casa

    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"])) # Recupera id da casa
    id_casa = mapeamento_casas[casa] 

with col2:
    ano = seletor_ano(2026, 2026, 'ano', 'Selecione o ano refente ao arquivo:')

if tipo_formatacao == 'Inputar - Real DRE':
    with col3:
        lista_meses = [
                    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
                    '1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre'
                ]
        mes = st.selectbox('Selecione o mês/período que deseja inputar:', lista_meses, help='1º Trimestre é para inputar os meses de Jan, Fev e Mar. E assim por diante.')
        meses = {
            "Janeiro": 1,
            "Fevereiro": 2,
            "Março": 3,
            "Abril": 4,
            "Maio": 5,
            "Junho": 6,
            "Julho": 7,
            "Agosto": 8,
            "Setembro": 9,
            "Outubro": 10,
            "Novembro": 11,
            "Dezembro": 12
        }
        if mes not in ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre']: 
            mes_selecionado = meses[mes]
        else:
            mes_selecionado = mes

st.divider()

# Dar upload em arquivo de orçamento ou planilha DRE
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if tipo_formatacao == 'Inputar - Orçamentos':
    if not uploaded_file:
        st.write("Adicione um arquivo .xlsx de Orçamento para transformá-lo")

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        st.divider()
        df_transformado = df.copy()

        # Removendo colunas e linhas desnecessárias 
        df_transformado = df_transformado[['Unnamed: 0', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']]
        df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])
        
        indice = df_transformado[df_transformado['Unnamed: 0'] == '(-) Impostos'].index # Remove todas as linhas abaixo disso
        if not indice.empty:
            df_transformado = df_transformado.loc[:indice[0] - 1]
        df_transformado = df_transformado.iloc[:-1]

        df_transformado = limpeza_linhas(df_transformado, casa)

        # Aplica tratamentos numéricos
        df_transformado = df_transformado.fillna(0)
        colunas_numericas = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        for col in colunas_numericas:
            df_transformado[col] = pd.to_numeric(df_transformado[col], errors='coerce')
            df_transformado[col] = df_transformado[col].abs() # Transforma valores negativos em positivos
        
        lista_class_cont_2_primeira_coluna = df_transformado['Unnamed: 0'].tolist()

        # Realiza consulta no banco para recuperar class. cont. 1 correspondente de cada class. cont. 2
        query_class_cont = f'''
            SELECT 
            tccg1.ID AS ID_CLASS_CONT_1,
            tccg1.DESCRICAO AS Descricao_1,
            tccg2.ID AS ID_CLASS_CONT_2
            FROM T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2
            LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tccg2.FK_GRUPO_1 = tccg1.ID)
            WHERE tccg2.DESCRICAO = %s
            AND tccg1.FK_VERSAO_PLANO_CONTABIL = 103
        '''
        
        for item in lista_class_cont_2_primeira_coluna:
            c.execute(query_class_cont, (item,))
            resultado_query = c.fetchone()
            
            if resultado_query:
                fk_class_cont_1 = resultado_query[0]
                descricao_class_cont_1 = resultado_query[1]
                fk_class_cont_2 = resultado_query[2]
            else:  # 'Não encontrado'
                fk_class_cont_1 = None
                descricao_class_cont_1 = None 
                fk_class_cont_2 = None

            condicao = df_transformado['Unnamed: 0'] == item
            df_transformado.loc[condicao, 'Classificacao 1'] = descricao_class_cont_1
            df_transformado.loc[condicao, 'FK_CLASSIFICACAO_1'] = fk_class_cont_1
            df_transformado.loc[condicao, 'FK_CLASSIFICACAO_2'] = fk_class_cont_2

            # Renomeia class. cont. 1 específicas
            if item == 'MDO Terceirizada - Artístico':
                df_transformado.loc[condicao, 'Classificacao 1'] = 'Mão de Obra - PJ'
                df_transformado.loc[condicao, 'FK_CLASSIFICACAO_1'] = 256
                df_transformado.loc[condicao, 'FK_CLASSIFICACAO_2'] = 1008
            
            if item == 'MDO Terceirizada - Eventos':
                df_transformado.loc[condicao, 'Classificacao 1'] = 'Mão de Obra - PJ'
        
        # Transforma formato do df
        df_layout_final = df_transformado.melt(
            id_vars=['Classificacao 1', 'Classificacao 2', 'FK_CLASSIFICACAO_1', 'FK_CLASSIFICACAO_2'],
            value_vars=colunas_numericas,
            var_name='Mes',
            value_name='Valor'
        )
        
        # Cria e organiza colunas para corresponder a T_ORCAMENTOS
        df_layout_final['FK_EMPRESA'] = id_casa
        df_layout_final['ANO'] = ano
        df_layout_final['IS_VALID'] = 1
        df_layout_final['FK_PLANO_DE_CONTAS'] = 103

        mapa_meses = {
            'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
            'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
            'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
        }

        df_layout_final['Mes'] = df_layout_final['Mes'].map(mapa_meses) # Transforma meses em número

        df_layout_final = df_layout_final.rename(columns={
            'Mes': 'MES',
            'Valor': 'VALOR'
        })

        df_layout_final_ids = df_layout_final.copy()
        df_layout_final = df_layout_final[['FK_EMPRESA', 'Classificacao 1', 'Classificacao 2', 'MES','ANO', 'VALOR', 'FK_PLANO_DE_CONTAS', 'IS_VALID']]
        st.subheader('Tabela para verificação') 
        st.dataframe(df_layout_final, hide_index=True)
        st.divider()

        # Mostra o resultado
        df_layout_final_ids = df_layout_final_ids[['FK_EMPRESA', 'FK_CLASSIFICACAO_1', 'FK_CLASSIFICACAO_2', 'MES','ANO', 'VALOR', 'FK_PLANO_DE_CONTAS', 'IS_VALID']]
        df_layout_final_ids['FK_CLASSIFICACAO_1'] = pd.to_numeric(df_layout_final_ids['FK_CLASSIFICACAO_1'], errors='coerce').astype('Int64')
        df_layout_final_ids['FK_CLASSIFICACAO_2'] = pd.to_numeric(df_layout_final_ids['FK_CLASSIFICACAO_2'], errors='coerce').astype('Int64')

        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela transformada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_layout_final_ids, f"Orçamentos_{nome_casa}", f"Orçamentos - {nome_casa}")

        st.dataframe(df_layout_final_ids, hide_index=True)
    
elif tipo_formatacao == 'Inputar - Real DRE':
    if not uploaded_file:
        st.write("Adicione um arquivo .xlsx para formatá-lo")

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        df_transformado = df.copy()
        st.divider()

        # Removendo colunas e linhas desnecessárias - seleciona pelo índice da coluna em vez do nome
        if ano == 2023: # Planilha personalizada - JÁ INSERIDOS
            df_transformado = df_transformado.iloc[:, [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 24]]
            df_transformado.rename(columns={'Unnamed: 24': 'ANO'}, inplace=True) # Renomeia para ter referência do mês
            colunas_meses = df_transformado.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]] # Define quais são as colunas de meses e acumulado do ano

        elif ano == 2024 and casa != 'Girondino': # 2024 vem do arquivo de Jan/2025  - JÁ INSERIDOS
            df_transformado = df_transformado.iloc[:, [0, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 46]]
            colunas_meses = df_transformado.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]] # Define quais são as colunas de meses e acumulado do ano
        
        elif ano == 2025 or (ano == 2024 and casa == 'Girondino'): # 2025 vem do arquivo de Dez/2025  - JÁ INSERIDOS
            df_transformado = df_transformado.iloc[:, [0, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 48]]
            df_transformado.rename(columns={ # Renomeia para ter referência do mês
                        'Unnamed: 9': f'{ano}-01-01 00:00:00',
                        'Unnamed: 12': f'{ano}-02-01 00:00:00',
                        'Unnamed: 15': f'{ano}-03-01 00:00:00',
                        'Unnamed: 18': f'{ano}-04-01 00:00:00',
                        'Unnamed: 21': f'{ano}-05-01 00:00:00',
                        'Unnamed: 24': f'{ano}-06-01 00:00:00',
                        'Unnamed: 27': f'{ano}-07-01 00:00:00',
                        'Unnamed: 30': f'{ano}-08-01 00:00:00',
                        'Unnamed: 33': f'{ano}-09-01 00:00:00',
                        'Unnamed: 36': f'{ano}-10-01 00:00:00',
                        'Unnamed: 39': f'{ano}-11-01 00:00:00',
                        'Unnamed: 42': f'{ano}-12-01 00:00:00',
                        'Unnamed: 48': 'ANO'
                    }, inplace=True)
            colunas_meses = df_transformado.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]] # Define quais são as colunas de meses e acumulado do ano
            
        elif ano >= 2026: 
            df_transformado.rename(columns={ # Renomeia para ter referência do mês
                'Unnamed: 9': f'{ano}-01-01 00:00:00',
                'Unnamed: 12': f'{ano}-02-01 00:00:00',
                'Unnamed: 15': f'{ano}-03-01 00:00:00',
                'Unnamed: 18': f'{ano}-04-01 00:00:00',
                'Unnamed: 21': f'{ano}-05-01 00:00:00',
                'Unnamed: 24': f'{ano}-06-01 00:00:00',
                'Unnamed: 27': f'{ano}-07-01 00:00:00',
                'Unnamed: 30': f'{ano}-08-01 00:00:00',
                'Unnamed: 33': f'{ano}-09-01 00:00:00',
                'Unnamed: 36': f'{ano}-10-01 00:00:00',
                'Unnamed: 39': f'{ano}-11-01 00:00:00',
                'Unnamed: 42': f'{ano}-12-01 00:00:00',
                'Unnamed: 48': 'ANO'
            }, inplace=True)

            # Seleção dinâmica das colunas correspondentes ao mês selecionado
            if mes_selecionado not in ['1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre']: 
                coluna_mes = 9 + (mes_selecionado - 1) * 3
                df_transformado = df_transformado.iloc[:, [0, coluna_mes]]
                colunas_meses = df_transformado.columns[[1]]
            else:
                if mes_selecionado == '1º Trimestre':
                    df_transformado = df_transformado.iloc[:, [0, 9, 12, 15]]
                elif mes_selecionado == '2º Trimestre':
                    df_transformado = df_transformado.iloc[:, [0, 18, 21, 24]]
                elif mes_selecionado == '3º Trimestre':
                    df_transformado = df_transformado.iloc[:, [0, 27, 30, 33]]
                elif mes_selecionado == '4º Trimestre':
                    df_transformado = df_transformado.iloc[:, [0, 36, 39, 42]]
                colunas_meses = df_transformado.columns[[1, 2, 3]]    
        
        df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])
            
        # Remove todas as linhas abaixo disso (só considera até Saldo Operacional)
        indice = df_transformado[df_transformado['Unnamed: 0'] == 'Premissas e parâmetros usados...'].index 
        if not indice.empty:
            df_transformado = df_transformado.loc[:indice[0] - 1]
        df_transformado = df_transformado.iloc[:-1]

        # Aplica tratamentos numéricos
        df_transformado = df_transformado.fillna(0)

        # Muda formato do df
        df_layout_final = df_transformado.melt(
            id_vars=['Unnamed: 0'],
            value_vars=colunas_meses,
            var_name='Mes',
            value_name='Valor'
        )
        df_layout_final['Valor'] = df_layout_final['Valor'].replace('              -  ', 0) # Caso Girondino/2024
        df_layout_final['Valor'] = df_layout_final['Valor'].astype(float)

        # Cria coluna de data
        condicao = (df_layout_final['Mes'] == 'ANO') | (df_layout_final['Mes'] == 'ANO 2025') | (df_layout_final['Mes'] == 'Ano 2024')
        df_layout_final.loc[condicao, 'Mes_atualizado'] = pd.Timestamp(
            year=int(ano),
            month=12,
            day=31
        )

        df_layout_final['Mes_datetime'] = pd.to_datetime(df_layout_final['Mes'], errors='coerce')
        mask_mes = df_layout_final['Mes_datetime'].notna()

        df_layout_final.loc[mask_mes, 'Mes_atualizado'] = pd.to_datetime(
            {
                'year': int(ano),
                'month': df_layout_final.loc[mask_mes, 'Mes_datetime'].dt.month,
                'day': df_layout_final.loc[mask_mes, 'Mes_datetime'].dt.day
            }
        )
        # mes_junho = pd.Timestamp( # Bug 2025
        #     year=ano,
        #     month=6,
        #     day=1
        # )
        # df_layout_final['Mes_atualizado'] = df_layout_final['Mes_atualizado'].fillna(mes_junho)

        # Organiza e renomeia colunas
        df_layout_final['FK_EMPRESA'] = id_casa
        df_layout_final = df_layout_final.rename(columns={
            'Unnamed: 0': 'CATEGORIA',
            'Mes_atualizado': 'MES',
            'Valor': 'VALOR'
        })
        df_layout_final = df_layout_final[['FK_EMPRESA', 'MES', 'CATEGORIA', 'VALOR']]
        df_download = df_layout_final.copy()

        # Mostra o resultado
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela formatada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_download, f"Real_{nome_casa}_{ano}", f"Real_{nome_casa}_{ano}")

        st.dataframe(df_download, hide_index=True)
        
        