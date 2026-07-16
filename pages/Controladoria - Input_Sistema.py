import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar, mysql_connection_fb
from utils.functions.controladoria_descontos_dre import limpeza_linhas
from utils.functions.controladoria_input_sistema import prepara_partes_headcount, prepara_colunas_real_dre
from utils.queries_conciliacao import GET_CASAS
from utils.queries_controladoria import GET_PLATAFORMAS_BILHETERIA
from utils.components import button_download, seletor_ano, seletor_mes
from utils.constants.general_constants import casas_validas

pd.set_option('future.no_silent_downcasting', True)


# Conexão com o banco de dados
conn = mysql_connection_fb()
c = conn.cursor(buffered=True)


st.set_page_config(
    page_title="Conversão de Arquivos - Input no Sistema",
    page_icon="⬆️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("⬆️ Conversão de Arquivos - Input no Sistema")
st.markdown("""
    Aba para formatar e inputar no EPM os seguintes arquivos:        
    - Orçamentos definidos para o ano
    - Real DRE (arquivo finalizado pós fechamento)
    - Headcount de Pessoas definido para o ano
    - Bilheterias
    """)
st.divider()

# Seletor do tipo de formatação
lista_formatacoes = ['Orçamentos', 'Real DRE', 'Headcount de Pessoas', 'Bilheteria']
tipo_formatacao = st.selectbox("Selecione o tipo de formatação", lista_formatacoes)
st.divider()

if tipo_formatacao in ['Real DRE', 'Bilheteria']:
    col1, col2, col3 = st.columns(3)
else: 
    col1, col2 = st.columns(2)

with col1: # Seletor de casa
    df_casas = GET_CASAS()
    casas = df_casas['Casa'].tolist()

    if tipo_formatacao == 'Bilheteria':
        casas = [casa for casa in casas_validas if casa in ['Bar Brahma - Centro', 'Bar Brahma - Granja', 'Ultra Evil Premium Ltda ']] # Revisar
    else:
        casas = [casa for casa in casas_validas if casa not in ['Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Edificio Rolim', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ']]
    
    casa = st.selectbox("Selecione a casa referente ao arquivo", casas)

    if casa == 'Blue Note - São Paulo': nome_casa = 'Blue Note SP'
    elif casa == 'Ultra Evil Premium Ltda ': nome_casa = 'Ultra Evil'
    else: nome_casa = casa

    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"])) # Recupera id da casa
    id_casa = mapeamento_casas[casa] 

with col2: # Seletor de ano
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano refente ao arquivo')

if tipo_formatacao == 'Real DRE': # Cria terceira coluna de mês/trimestre
    with col3:
        lista_meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
            '1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre'
        ]
        mes = st.selectbox('Selecione o mês/período que deseja inputar', lista_meses, help='1º Trimestre é para inputar os meses de Jan, Fev e Mar. E assim por diante.')
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

if tipo_formatacao == 'Bilheteria': # Terceira coluna de mês simples
    with col3:
        mes_selecionado = seletor_mes('Selecione o mês referente ao arquivo', 'mes_bilheteria')

st.divider()

# Dar upload em arquivo
uploaded_file = st.file_uploader("Selecione um arquivo XLSX ou CSV do seu computador", type=["xlsx", "csv"])

if tipo_formatacao == 'Orçamentos':
    if not uploaded_file:
        st.write("Adicione um arquivo XLSX de Orçamento para transformá-lo")

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        st.divider()
        df_transformado = df.copy()

        # Removendo colunas e linhas desnecessárias 
        df_transformado = df_transformado[['Unnamed: 0', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']]
        df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])
        
        indice = df_transformado[df_transformado['Unnamed: 0'] == '(-) CAPEX (Investimentos)'].index # Remove todas as linhas abaixo disso
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
    

elif tipo_formatacao == 'Real DRE':
    if not uploaded_file:
        st.write("Adicione um arquivo XLSX para formatá-lo")
        if casa in ['Girondino', 'Girondino - CCBB']:
            st.warning(f'O sistema lê apenas a primeira aba da planilha anexada. Certifique-se de que a DRE do {casa} esteja na primeira aba do arquivo.')

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        df_transformado = df.copy()
        st.divider()

        # Seleciona e prepara colunas corretas
        df_transformado, colunas_meses = prepara_colunas_real_dre(df, casa, ano, mes_selecionado)
        df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])
            
        # Remove todas as linhas abaixo disso (só considera até Saldo Operacional)
        indice = df_transformado[df_transformado['Unnamed: 0'] == 'Premissas e parâmetros usados...'].index 
        if not indice.empty:
            df_transformado = df_transformado.loc[:indice[0] - 1]
        df_transformado = df_transformado.iloc[:-1]

        # Remove linha 'Eventos A&B' inclusa no CMV para não conflitar com a do Faturamento Bruto
        mask = df_transformado['Unnamed: 0'] == 'Eventos A&B'
        df_transformado = df_transformado[~(mask & mask.cumsum().gt(1))]

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

        df_layout_final.loc[mask_mes, 'Mes_atualizado'] = pd.to_datetime({
            'year': int(ano),
            'month': df_layout_final.loc[mask_mes, 'Mes_datetime'].dt.month,
            'day': df_layout_final.loc[mask_mes, 'Mes_datetime'].dt.day
        })

        # Organiza e renomeia colunas
        df_layout_final['FK_EMPRESA'] = id_casa
        df_layout_final = df_layout_final.rename(columns={
            'Unnamed: 0': 'CATEGORIA',
            'Mes_atualizado': 'MES',
            'Valor': 'VALOR'
        })
        df_layout_final = df_layout_final[['FK_EMPRESA', 'MES', 'CATEGORIA', 'VALOR']]
        df_layout_final['MES'] = df_layout_final['MES'].dt.date
        df_download = df_layout_final.copy()

        # Mostra o resultado
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela formatada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_download, f"Real_{nome_casa}_{ano}", f"Real_{nome_casa}_{ano}")

        st.dataframe(df_download, hide_index=True)
        

elif tipo_formatacao == 'Headcount de Pessoas':
    if not uploaded_file:
        st.write("Adicione um arquivo XLSX para formatá-lo")

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        df_transformado = df.copy()
        st.divider()

        lista_cols_manter = []
        for i in range(26):
            lista_cols_manter.append(f'Unnamed: {i}')
        
        for col in df_transformado.columns:
            if col not in lista_cols_manter:
                df_transformado = df_transformado.drop(columns=[col])

        # Divide o df em dois (num. colaboradores à esquerda e remuneração à direita)
        df_primeira_parte = df_transformado.iloc[:, 0:13]
        df_primeira_parte = prepara_partes_headcount(df_primeira_parte, 'Nº COLABORADORES', ano)
        df_segunda_parte = df_transformado.iloc[:, 13:26]
        df_segunda_parte = prepara_partes_headcount(df_segunda_parte, 'REMUNERAÇÃO', ano)

        df_final = pd.concat([df_primeira_parte, df_segunda_parte])
        df_final['ID Casa'] = id_casa

        # Adiciona coluna de flag PJ/CLT
        condicao = df_final['Cargo'].isin(
            ['Líder de Squad','Gerente Financeiro','Analista Financeiro - Squad','Assistente Financeiro','Gerente de Eventos',
	        'Coordenador de Eventos','Analista de Eventos','Assistente de Eventos','Produtor de Eventos','Gerente de Marketing',
	        'Coordenador de Marketing','Analista de Marketing','Assistente de Marketing','Curador Artístico','Produtor Artístico',
	        'Chefe de Manutenção','- Gerente','- Subgerente','- Coordenador','- Administrativa','- Chefe de Cozinha','- Chefe de Bar',
  	        '- Sub Chefe de Cozinha','- Sub Chefe De Bar','- Maitre','- Chefe de Fila','- Hostess','Coordenador de Hospitalidade', 'Coordenador de A&B'])

        df_final.loc[condicao, 'MODELO_CONTRATACAO'] = 'PJ'
        df_final.loc[~condicao, 'MODELO_CONTRATACAO'] = 'CLT'

        # Prepara para download
        df_download = df_final.rename(columns={
            'ID Casa': 'FK_EMPRESA',
            'Cargo': 'CARGO',
            'Mês': 'MES',
            'Ano': 'ANO',
            'Valor': 'VALOR',
            'Tipo de Dado': 'TIPO_DADO'
        })
        df_download = df_download[['FK_EMPRESA', 'MES', 'ANO', 'CARGO', 'VALOR', 'TIPO_DADO', 'MODELO_CONTRATACAO']]

        # Mostra o resultado
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela formatada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_download, f"Input Headcount_{nome_casa}", f"Input Headcount_{nome_casa}")

        st.dataframe(df_download, hide_index=True)


elif tipo_formatacao == 'Bilheteria':
    if not uploaded_file:
        st.write("Adicione um arquivo CSV para formatá-lo") # Futuro - Verificar formato dos arquivos de Bilheteria das outras casas

    # Se arquivo adicionado, prossegue
    else:
        df_plataformas_bilheteria = GET_PLATAFORMAS_BILHETERIA() 

        uploaded_file.seek(0) 
        linhas = uploaded_file.readlines() # Lê todas as linhas do arquivo

        # Procura a linha que contém "Detalhe por sessao"
        linha_inicio = next(
            i for i, linha in enumerate(linhas)
            if "Detalhe por sessao" in linha.decode("latin1")
        )
        uploaded_file.seek(0) # Volta o ponteiro do arquivo para o início

        # Lê o CSV a partir dessa linha
        df = pd.read_csv(uploaded_file, skiprows=linha_inicio+1, sep=";", encoding="latin1" ) # Pula uma linha para excluir a de 'Detalhe por sessao' 
        df_transformado = df.copy()
        st.divider()

        # Mantém apenas colunas necessárias
        df_transformado = df_transformado[['Data', 'Experiencia/Evento', 'Pessoas pagas', 'Valor unitario', 'Bruto', 'Taxas', 'Liquido']]
        
        df_transformado['FK_EMPRESA'] = id_casa
        df_transformado['DATA_COMPETENCIA'] = pd.to_datetime(df_transformado['Data'], errors='coerce', dayfirst=True)
        df_transformado['Valor unitario'] = pd.to_numeric(df_transformado['Valor unitario'].str.replace(",", ".", regex=False), errors="coerce")        
        df_transformado['Bruto'] = pd.to_numeric(df_transformado['Bruto'].str.replace(",", ".", regex=False), errors="coerce")        
        df_transformado['Taxas'] = pd.to_numeric(df_transformado['Taxas'].str.replace(",", ".", regex=False), errors="coerce")        

        df_transformado = df_transformado.rename(columns={
            'Experiencia/Evento': 'DESCRICAO',
            'Pessoas pagas': 'QUANTIDADE',
            'Valor unitario': 'VALOR_INGRESSO',
            'Bruto': 'VALOR_BRUTO',
            'Taxas': 'VALOR_DESCONTOS',
        })
        
        df_transformado = pd.merge( # Cria coluna com FK da plataforma de venda da casa
            df_transformado,
            df_plataformas_bilheteria[['FK_PLATAFORMA_VENDA', 'ID_Casa']], 
            left_on=['FK_EMPRESA'],
            right_on=['ID_Casa'],
            how='left'
        )
        df_transformado = df_transformado[['FK_EMPRESA', 'FK_PLATAFORMA_VENDA', 'DATA_COMPETENCIA', 'QUANTIDADE', 'VALOR_INGRESSO', 'DESCRICAO', 'VALOR_DESCONTOS', 'VALOR_BRUTO']]
        df_download = df_transformado.copy()
        # As colunas de DATA_COMPRA e REBATE são tratadas na UDF - Revisar

        # Mostra o resultado
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela formatada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_download, f"Input Bilheteria_{nome_casa}", f"Input Bilheteria_{nome_casa}")

        st.dataframe(df_download, hide_index=True)
