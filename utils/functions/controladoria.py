import pandas as pd
import streamlit as st
import pymysql


def mysql_connection_write():
    mysql_config = st.secrets["mysql_write"]

    conn_write = pymysql.connect(
        host=mysql_config['host'],
        port=mysql_config['port'],
        database=mysql_config['database'],
        user=mysql_config['username'],
        password=mysql_config['password']
    )
    
    return conn_write


# Descontos - DRE #
def mapeamento_centro_custo(df):
    regras_globais_centro_custo = {
        'CONSUMO GERÊNCIA|CONSUMO GERENCIA|DESCONTO FUNCIONÁRIOS 30%|CONSUMO GERENCIAL|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS': '  -  Alimentação Funcionário',
        'MÚSICOS|REUNIÃO - ARTÍSTICO|TÉCNICO DE SOM|ARTÍSTICO': 'Alimentação e Transporte',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|\[Ação de Marketing\] - Captação|\[Ação de Marketing\] - Influencer|PERMUTA': 'Eventos de Marketing', # Não considero [Ação de Marketing]
        'REUNIÃO - TI|REUNIÃO - T.I.': 'Sistemas Gerais - Operacionais',
        'CONTROLE DE EVENTOS': 'FATURAMENTO', # Não considero [Evento]
        'PROMOÇÃO': 'Ferramentas de Marketing',
        'FOTOS E VIDEOS MKT': 'Produção Gráfica e Material Institucional',
        'INFLUENCER|INFLUENCERS|\[Ação de Marketing\] - Influencers Delivery': 'Influenciadores', # Granja
    }

    # Sobrescreve essas categorias para essas casas
    regras_por_casa_centro_custo = {
        (110, 131): {  # Blue Note - São Paulo, BNSP
            'REUNIÃO - EVENTOS': 'Brindes e Confraternizações - Eventos'
        },

        (156, 160): {  # Girondino, CCBB
            'REUNIÃO - EVENTOS': 'Serviços Terceirizados - Eventos'
        },

        (105,): {  # Jacaré
            'Captação|Shooting|FOTOS E VIDEOS MKT': 'Sessão de Fotos/Captação de Vídeo'
        },

        (115,): {  # Riviera Bar
            '\[Ação de Marketing\] - Captação': 'Produção Gráfica e Material Institucional'
        },

        (104,): { # Orfeu
            '\[Ação de Marketing\] - Captação': None
        }
    }

    df_categorias_mes_centro_custo = df.copy()
    
    # Aplica regras globais
    for padrao, categoria in regras_globais_centro_custo.items():
        cond = df_categorias_mes_centro_custo["CATEGORIA"].str.contains(padrao, na=False, regex=True)
        df_categorias_mes_centro_custo.loc[cond, "Centro de Custo"] = categoria

    # Aplica regras específicas por casa
    for casas, regras in regras_por_casa_centro_custo.items():
        df_casa = df_categorias_mes_centro_custo["FK_CASA"].isin(casas)

        for padrao, categoria in regras.items():
            cond = df_categorias_mes_centro_custo["CATEGORIA"].str.contains(padrao, na=False, regex=True)
            df_categorias_mes_centro_custo.loc[df_casa & cond, "Centro de Custo"] = categoria
    
    return df_categorias_mes_centro_custo


def mapeamento_descontos_dre(casa, df):
    regras_globais_descontos_dre = {
        'EVENTO': 'Faturamento - Eventos',
        'COTA|OPERAÇÕES|REUNIÃO|MÚSICOS|REUNIÃO - ARTÍSTICO|REUNIÃO - TI|OUTROS|CLIENTE - DUO GOURMET|ASSINADA SÓCIOS E DIRETOR|ASSINADA SÓCIO FACUNDO|CORTESIA|CONVÊNIO|REUNIÃO - SUPRIMENTOS|RETIRADA / REDUÇÃO DE SERVIÇO|TREINAMENTO|LUCIANO PERES - SOCIO|LUCIANO PERES - SÓCIO|REUNIÃO - FABLAB|TESTE|TÉCNICO DE SOM|POLÍCIA|REUNIÃO - OPERAÇÕES|SEM JUSTIFICATIVA|PROMOÇÕES|OPERACIONAL|SERVIÇO|PERMUTA|OUTRO|REUNIÃO - OPERACIONAL|CONTA ASSINADA|10% LOJISTAS - CPF|10% CONVENIADOS - CPF|PROMOO': 'Descontos - Operação',
        'CONSUMO GERÊNCIA|CONSUMO GERENCIAL|DESCONTO FUNCIONÁRIO|CONSUMO COLABORADOR|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS|30% FÁBRICA DE BARES|CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|30% DIVERTI - CPF|DIVERT 30%|30% FB - ORFEU|CONTA ASSINADA - FDB|CONTA ASSINADA - FACUNDO|REUNIÃO - EVENTOS|REUNIÃO - COMPRAS|30% FB - ORFEU': 'Desconto - Alimentação Escritório',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|PROMOÇÃO|FOTOS E VIDEOS MKT|INFLUENCER|\[Ação de Marketing\]': 'Descontos - Marketing',
        '\[Event\]|\[Evento\]|PACOTE': 'Faturamento de Eventos - Promoções Utilizadas',
        '\[Evento\] - Confraternização FB': 'Descontos - Promoções Utilizadas' # Bar Léo
    }

    # Sobrescreve essas categorias para essas casas
    regras_por_casa_descontos_dre = {
        (122, 104, 116, 105, 128, 115): {  # Arcos, Orfeu, Bar Léo - Centro, Jacaré, Love Cabaret, Riviera Bar
            'EVENTO|\[Evento\] - Aniversário Cairê': 'FATURAMENTO'
        },

        (114,): {  # Bar Brahma - Centro
            'CONSUMO GERENCIAL|30% ESHOWS - RG': 'Descontos - Operação',
            'CONTA ASSINADA': 'Desconto - Alimentação Escritório'
        },

        (148,): {  # Bar Brahma - Granja
            '30% FÁBRICA DE BARES': 'Descontos - Operação',
            'CORTESIA - GERENCIAL': 'Desconto - Alimentação Escritório'
        },

        (110, 131): { # Blue Note - São Paulo
            'ASSINADA SÓCIOS E DIRETORIA|LUCIANO PERES - SOCIO|REUNIÃO - FINANCEIRO|CONTA ASSINADA - FLÁVIO|CONTA ASSINADA - CALAINHO|CONTA ASSINADA - MEGALE|REUNIÃO - T.I.': 'Desconto - Alimentação Escritório', 
            'CONVÊNIO': '(-) Despesas de Patrocínio',
            'PERMUTA|Members Club Blue Note São Paulo_Categoria Premium|Members Club Blue Note São Paulo_Categoria Comum': 'Descontos - Marketing'
        },

        (156, 160): { # Girondino
            'CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|CONSUMO GERENCIAL|REUNIÃO - EVENTOS|30% FÁBRICA DE BARES': 'Descontos - Operação',
            'PROMOÇÕES': 'Descontos - Marketing'
        },

        (105,): { # Jacaré
            'CLIENTE MASTERCARD|REUNIÃO - EVENTOS|30% DIVERT - CPF|30% ESHOWS - CPF': 'Descontos - Operação'
        },

        (128,): { # Love Cabaret
            '30 % promoção colaborador|CONTA ASSINADA - JOÃO|CONTA ASSINADA - CAIRÊ|CURADOR|DEVOLUÇÃO PAGAMENTO ANTECIPADO|DESCONTO LOVERS|10% Sócios|MARKETING|ARTÍSTICO|CONTA ASSINADA - LILY': 'Descontos - Operação'
        },

        (104,): { # Orfeu
            '30% DIVERTI - CPF|10% CONVENIADOS GRUPO ENJOEI': 'Descontos - Operação'
        },

        (162,): {  # Terraço Notiê
            'CONVÊNIO|CLIENTE MASTERCARD|CARTAO MASTER 10%|COTA|Descontos - Marketing|\[Reunião\] - Eventos|\[Reunião\] - Marketing': 'Desconto - Marketing',
            'CLIENTE - BEM SP|FUNCIONÁRIOS MASTERCARD|30% TERRAÇO NOTIÊ|\[Convênio\] - 50% BEM SP|\[Convênio\] - 30% BEM SP|CLIENTE - MASTECARD|COTA - MASTERCARD|\[Cota\] - MASTERCARD|Descontos - Operação|\[Convidados\] - Karina Mota|CONTA ASSINADA|\[BemSP\]': 'Descontos - Operação',
            'REUNIÃO - AUDITORIA|REUNIÃO - T.I.': 'Desconto - Alimentação Escritório',
            'EVENTO|\[Evento\]|PRO_240874 Bem SP-Itau 100 anos': 'Faturamento Eventos - Promoções Utilizadas'
        },

        (115,): { # Riviers Bar
            'CONTA ASSINANDA - CAIRÊ': 'Desconto - Alimentação Escritório',
            '30% DIVERTI - CPF|30% FÁBRICA DE BARES': 'Desconto - Operação',
            '\[Evento\]': 'Faturamento Eventos - Promoções Utilizadas'
        }
    }

    df_categorias_mes_descontos_dre = df.copy()
    
    # Aplica regras globais
    for padrao, categoria in regras_globais_descontos_dre.items():
        cond = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False, regex=True)
        df_categorias_mes_descontos_dre.loc[cond, "Descontos - DRE"] = categoria

    # Aplica regras específicas por casa
    for casas, regras in regras_por_casa_descontos_dre.items():
        df_casa = df_categorias_mes_descontos_dre["FK_CASA"].isin(casas)

        for padrao, categoria in regras.items():
            cond = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False, regex=True)
            df_categorias_mes_descontos_dre.loc[df_casa & cond, "Descontos - DRE"] = categoria
    
    return df_categorias_mes_descontos_dre


def filtra_df(df_descontos, df_promocoes, mes, ano, id_casa):
    df_descontos_filtrado = df_descontos.copy()
    df_descontos_filtrado['DATA'] = pd.to_datetime(df_descontos_filtrado['DATA'], errors='coerce')
    df_descontos_filtrado = df_descontos_filtrado[
        (df_descontos_filtrado['DATA'].dt.month == int(mes)) &
        (df_descontos_filtrado['DATA'].dt.year == ano)
    ].copy()

    df_promocoes_filtrado = df_promocoes.copy()
    df_promocoes_filtrado['DATA'] = pd.to_datetime(df_promocoes_filtrado['DATA'], errors='coerce')
    df_promocoes_filtrado = df_promocoes_filtrado[
        (df_promocoes_filtrado['DATA'].dt.month == int(mes)) &
        (df_promocoes_filtrado['DATA'].dt.year == ano)
    ].copy()

    # Se selecionou uma casa específica, filtra
    if id_casa is not None:
        df_descontos_filtrado = df_descontos_filtrado[
            df_descontos_filtrado['FK_CASA'] == id_casa
        ].copy()

        df_promocoes_filtrado = df_promocoes_filtrado[
            df_promocoes_filtrado['FK_CASA'] == id_casa
        ].copy()

    return df_descontos_filtrado, df_promocoes_filtrado


def prepara_consolidado(df_descontos_filtrado, df_promocoes_filtrado):
    # Descontos - soma total por categoria
    df_descontos_mes = df_descontos_filtrado.groupby(['FK_CASA', 'DATA', 'CATEGORIA'], as_index=False).agg({
        'DESCONTO': 'sum',
        'DATA': 'first',
    })

    # Promoções - soma total por categoria
    df_promocoes_mes = df_promocoes_filtrado.groupby(['FK_CASA', 'DATA', 'PROMOCAO'], as_index=False).agg({
        'DESCONTO_TOTAL': 'sum',
        'DATA': 'first',
    })
    
    df_promocoes_mes = df_promocoes_mes.rename(columns={
        'PROMOCAO': 'CATEGORIA',
        'DESCONTO_TOTAL': 'DESCONTO'
    })

    df_concatenado = pd.concat([df_descontos_mes, df_promocoes_mes]).reset_index(drop=True)

    return df_descontos_mes, df_promocoes_mes, df_concatenado


# Colunas - DRE (Subir Orçamentos e Real) #
# Remove linhas que não são de orçamento / apenas títulos
def limpeza_linhas(df, casa):
    df_transformado = df.copy()
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
    return df_transformado


# Função para inserir no banco os valores reais de cada ano de DRE
def inserir_df_no_banco(df, conn, id_casa, mes_formatado, casa, ano):
    c = conn.cursor()
    query_insercao = """
        INSERT INTO T_VALORES_REAIS_DRE
        (FK_EMPRESA, MES, CATEGORIA, VALOR)
        VALUES (%s, %s, %s, %s)
    """

    query_verifica_ja_existe = """
        SELECT tvrdre.ID
        FROM T_VALORES_REAIS_DRE tvrdre
        WHERE tvrdre.FK_EMPRESA = %s -- varia de acordo com a casa
        AND tvrdre.MES = %s -- varia de acordo com o mês
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

    # Verifica se, para a casa e mês selecionados, os dados já foram inseridos
    c.execute(query_verifica_ja_existe, (id_casa, mes_formatado))
    dados_encontrados = c.fetchall()
    if not dados_encontrados: 
        c.executemany(query_insercao, dados) # Insere os dados atuais
        st.success("Dados inseridos com sucesso na tabela 'T_VALORES_REAIS_DRE'")
    else:
        st.warning(f'Dados já inseridos para {casa} - {ano}')
    
    conn.commit()

