import streamlit as st
import pandas as pd
import pymysql
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download, seletor_ano

pd.set_option('future.no_silent_downcasting', True)


# Conexão com o banco de dados
conn = pymysql.connect(
    host='homolog.cvuwkhnpr3rt.us-east-2.rds.amazonaws.com',
    user='fb_catarina_scabelli',
    password='wwAcH2xEFk2P3aUW',
    port=6303,
    database='EPM_FB',
    autocommit=True
)
c = conn.cursor()

# Consulta para recuperar class. cont. 1 de cada class_cont_2 da primeira coluna de forma confiável
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

# Função para inserir no banco os valores reais de cada ano de DRE
def inserir_df_no_banco(df, conn):
    sql_insert = """
        INSERT INTO T_VALORES_REAIS_DRE
        (FK_EMPRESA, MES, CATEGORIA, VALOR)
        VALUES (%s, %s, %s, %s)
    """

    # garante tipos corretos
    df = df.copy()
    df['VALOR'] = df['VALOR'].astype(float)

    dados = df[
        [
            'FK_EMPRESA',
            'MES',
            'CATEGORIA',
            'VALOR'
        ]
    ].values.tolist()

    with conn.cursor() as c:
        c.executemany(sql_insert, dados)
        conn.commit()

    st.success("Dados inseridos com sucesso na tabela 'T_VALORES_REAIS_DRE'")


st.set_page_config(
    page_title="Subir Colunas - DRE",
    page_icon=":material/list:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/list: Subir Colunas - DRE")
st.write("Aba que formata a planilha de Orçamento Operacional anual e as colunas de 'Real' para inserção automática no EPM.")
st.divider()

# Seletor do tipo de formatação
lista_formatacoes = ['Subir Orçamentos', 'Coluna "Real" DRE']
tipo_formatacao = st.selectbox("Selecione o tipo de formatação:", lista_formatacoes)
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    df_casas = GET_CASAS()
    casas = df_casas['Casa'].tolist()
    casa = st.selectbox("Selecione a casa referente ao arquivo:", casas)
    if casa == 'Blue Note - São Paulo':
        nome_casa = 'Blue Note SP'
    elif casa == 'Ultra Evil Premium Ltda ':
        nome_casa = 'Ultra Evil'
    else:
        nome_casa = casa

    # Recupera id da casa
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
    id_casa = mapeamento_casas[casa]
    
with col2:
    ano = seletor_ano(2024, 2026, 'ano', 'Selecione o ano refente ao arquivo:')

st.divider()

# Dar upload em arquivo de orçamento ou planilha DRE
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if tipo_formatacao == 'Subir Orçamentos':
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

        # Remove linhas que não são de orçamento / apenas títulos
        col = (df_transformado['Unnamed: 0'])
    
        excecoes_parenteses = {
            '(-) Despesas de Patrocínio',
            '(+) Receitas de Patrocínio'
        }
        contem_parenteses_negativo = col.str.contains(r'\(-\)', na=False) &  ~col.isin(excecoes_parenteses)
        contem_parenteses_positivo = col.str.contains(r'\(\+\)', na=False) &  ~col.isin(excecoes_parenteses)
        contem_cargos = col.str.contains(
            r'squad|chef|gerente|coord|maitre|hostess|garçon|chop|cumin|barista|bartender|bar back|cozinheiro|ajud cozinha|saladeiro|pia|confeiteiro|copeiro|pizza|boqueta|churras|ajud limpeza|estoquista|aux|porteiro|bilheteiro|caixa|operador',
            case=False,
            na=False
        )

        excluir_exatos = {
            'FATURAMENTO BRUTO',
            'Eventos',
            '% sobre Receita Bruta',
            'RECEITA LÍQUIDA',
            '% sobre Receita Líquida',
            'Custos Artístico',
            'Custos Ténico de Som',
            '% sobre Receita Artístico',
            'MDO',
            'Serviços de Terceiros - Eventos',
            'Material de Consumo',
            'Manutenção Geral',
            'Transportes',
            'Locações',
            'Repasses Locação de Espaço',
            '% sobre Receita de Eventos',
            'MARGEM BRUTA DE CONTRIBUIÇÃO',
            '% sobre Receita',
            'PESSOAL',
            'E-Staff',
            '% sobre Receita c/ Squad', 
            '% sobre Receita s/ Squad',
            'Custo de Ocupação',
            'Utilidades',
            'Informática e TI',
            'Despesas Gerais',
            'Marketing',
            'Serviços de Terceiros',
            'Locação de Equipamentos',
            'Sistema de Franquias',
            'Encargos e Provisões',
            'Benefícios', 
            'Outros B',
            '  - Administrativa',
            'Viagens e Estadias',
            'TOTAL - DESPESAS OPERATIVAS',
            'EBITDA', 'EBIT',
            '(+/-) Receitas/Despesas Financeiras',
        }

        # Regra especial para o Blue Note
        if casa == 'Blue Note - São Paulo':
            excluir_exatos.discard('Viagens e Estadias')  # não exclui

        df_transformado = df_transformado[
            (~col.isin(excluir_exatos)) &    # remove títulos
            (~contem_parenteses_negativo) &  # remove (-)
            (~contem_parenteses_positivo) &  # remove (+)
            (~contem_cargos)                 # remove cargos de PJ e Salários
        ]

        # Aplica tratamentos numéricos
        df_transformado = df_transformado.fillna(0)
        colunas_numericas = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        for col in colunas_numericas:
            df_transformado[col] = pd.to_numeric(df_transformado[col], errors='coerce')
            df_transformado[col] = df_transformado[col].abs() # Transforma valores negativos em positivos

        # Renomeia nomes da planilha para class. cont. 2 correspondente no banco
        condicao = df_transformado['Unnamed: 0'] == 'Alimentação D'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Alimentos'

        condicao = df_transformado['Unnamed: 0'] == 'Bebida D'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Bebidas'

        condicao = df_transformado['Unnamed: 0'] == 'Embalagens'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Embalagens'

        condicao = df_transformado['Unnamed: 0'] == 'PJ'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'MDO PJ Fixo'

        condicao = df_transformado['Unnamed: 0'] == 'Salários'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'MDO CLT - Salário'

        condicao = df_transformado['Unnamed: 0'] == 'Brindes e Confraternizações'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'Brindes e Confraternizações - Marketing'
        
        condicao = df_transformado['Unnamed: 0'] == 'Custas Cartório'
        df_transformado.loc[condicao, 'Unnamed: 0'] = 'Custas Cartório / Operação'

        idx = df_transformado[df_transformado['Unnamed: 0'] == 'Eventos A&B'].index # Caso de dois 'Eventos A&B' (Faturamento Bruto e Custo Mercadoria Vendida)
        df_transformado.loc[idx[1], 'Unnamed: 0'] = 'Insumos - Eventos A&B'
        df_transformado.loc[idx[1], 'Classificacao 1'] = 'Custo Mercadoria Vendida'

        if casa == 'Blue Note - São Paulo': # Realoca essas duas categorias de Faturamento Bruto
            condicao = df_transformado['Unnamed: 0'] == 'Viagens e Estadias' # Não excluí: Renomeia para mapear para a class. cont. 1
            df_transformado.loc[condicao, 'Unnamed: 0'] = 'Viagens e Estadias - Artístico'

            condicao = df_transformado['Unnamed: 0'] == 'Eventos Rebate Fornecedores - Premium Corp'
            df_transformado.loc[condicao, 'Unnamed: 0'] = 'Eventos Locações'

            condicao = df_transformado['Unnamed: 0'] == 'Membership'
            df_transformado.loc[condicao, 'Unnamed: 0'] = 'Outras Receitas'
            df_transformado = df_transformado.groupby('Unnamed: 0', as_index=False)[['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']].sum()
        
        # Cria coluna de class. cont. 2
        df_transformado['Classificacao 2'] = df_transformado['Unnamed: 0']
        
        lista_class_cont_2_primeira_coluna = df_transformado['Unnamed: 0'].tolist()

        # Realiza consulta no banco para recuperar class. cont. 1 correspondente de cada class. cont. 2
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
    
elif tipo_formatacao == 'Coluna "Real" DRE':
    if not uploaded_file:
        st.write("Adicione um arquivo .xlsx para formatá-lo")

    # Se arquivo adicionado, prossegue
    else:
        # Lê o arquivo adicionado
        df = pd.read_excel(uploaded_file, skiprows=3)
        df_transformado = df.copy()
        st.divider()
        
        # Removendo colunas e linhas desnecessárias 
        df_transformado.drop(columns=['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6'], inplace=True)
        for col in df_transformado.columns:
            if col in ['Unnamed: 20', 'Unnamed: 21']: 
                df_transformado.drop(columns=col, inplace=True)
        df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])

        # Remove todas as linhas abaixo disso (só considera até Saldo Operacional)
        indice = df_transformado[df_transformado['Unnamed: 0'] == 'Premissas e parâmetros usados...'].index 
        if not indice.empty:
            df_transformado = df_transformado.loc[:indice[0] - 1]
        df_transformado = df_transformado.iloc[:-1]

        # Aplica tratamentos numéricos
        df_transformado = df_transformado.fillna(0)

        # Muda formato do df
        colunas_meses = df_transformado.columns[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]]
        df_layout_final = df_transformado.melt(
            id_vars=['Unnamed: 0'],
            value_vars=colunas_meses,
            var_name='Mes',
            value_name='Valor'
        )
        df_layout_final['Valor'] = df_layout_final['Valor'].astype(float)

        # Cria coluna de data
        condicao = (df_layout_final['Mes'] == 'ANO') | (df_layout_final['Mes'] == 'ANO 2025')
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

        # Organiza e renomeia colunas
        df_layout_final['FK_EMPRESA'] = id_casa
        df_layout_final = df_layout_final.rename(columns={
            'Unnamed: 0': 'CATEGORIA',
            'Mes_atualizado': 'MES',
            'Valor': 'VALOR'
        })
        df_layout_final = df_layout_final[['FK_EMPRESA', 'MES', 'CATEGORIA', 'VALOR']]
        df_download = df_layout_final.copy()

        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader('Tabela formatada') 
            st.write('Adaptada para inserção no EPM.')
        with col2:
            button_download(df_download, f"Real_{nome_casa}_{ano}", f"Real_{nome_casa}_{ano}")

        st.dataframe(df_download, hide_index=True)

        if st.button("Inserir dados no banco", type='primary'):
            inserir_df_no_banco(df_download, conn)