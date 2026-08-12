# Lojas agrupadas da aba de projeção - Não está sendo utilizado
lojasAgrupadas = [
    "All bar",
    "Bar Brahma Aeroclube",
    "Brahma Aricanduva",
    "Bardassê",
    "Bar Léo - Vila Madalena",
    "FDB DIGITAL PARTICIPACOES LTDA",
    "FDB HOLDING INFERIOR LTDA",
    "FDB HOLDING SUPERIOR LTDA",
    "Ilha das Flores ",
    'Lojinha - Brahma', 
    'Navarro',
    'Patizal ', 
    'Tundra',
    "Bar Brahma - Centro",
    "Bar Brahma - Granja",
    "Bar Brahma - Paulista",
    "Brahma - Ribeirão",
    "Bar Léo - Centro",
    "Bar Brasilia - Aeroporto",
    "Delivery Bar Leo Centro",
    "Delivery Fabrica de Bares",
    "Delivery Orfeu",
    "Edificio Rolim",
    "Escritório Fabrica de Bares",
    "Girondino - CCBB",
    "Girondino", 
    "Hotel Maraba",
    "Jacaré",
    "Notiê - Priceless",
    "Orfeu",
    "Priceless",  
    "Riviera Bar",
    "Tempus Fugit  Ltda ",
    "Terraço Notie"
]


# Todas as casas de df_casas menos 'All bar'
casas_validas = [
    'Arcos', 
    'Bar Brahma - Centro', 
    'Bar Brahma - Granja', 
    'Bar Brahma - Paulista', 
    'Bar Léo - Centro', 
    'Blue Note - São Paulo', 
    'Blue Note SP (Novo)', 
    'Blue Note SP (Sala 2)',
    'Edificio Rolim', 
    'Escritório Fabrica de Bares', 
    'Girondino', 
    'Girondino - CCBB', 
    'Jacaré', 
    'Love Cabaret', 
    'Orfeu', 
    'Priceless', 
    'Riviera Bar', 
    'Sanduiche comunicação LTDA ', 
    'Tempus Fugit  Ltda ', 
    # 'The Cavern',
    # 'The Cavern - Almoço',
    'Ultra Evil Premium Ltda ',
    'Nuv Gastrobar'
]


cores_casas = [
    "#582310", # Arcos
    "#DF2526", # Bar Brahma - Centro
    "#84161f", # Bar Brahma - Granja
    "#1C6EBA", # Bar Brahma - Paulista
    "#E9A700", # Bar Leo - Centro
    "#081F5C", # Blue Note São Paulo
    "#004080", # Blue Note (Novo)
    "#336699", # Edificio Rolim
    "#6699CC", # Escritorio FB
    "#4A5129", # Girondino
    "#8CA706", # Girondino CCBB
    "#0CA22E", # Jacaré
    "#E799BB", # Love Cabaret
    "#006E77", # Orfeu
    "#000000", # Priceless
    "#C2185B", # Riviera
    "#FF6600", # Sanduiche
    "#9933CC", # Tempus
    # "#03420D", # The Cavern
    # "#D6B98C", # The Cavern - Almoço
    "#3D5771", # Ultra Evil
]


# Mapeamentos manuais: fornecedor da despesa:descrição do extrato
exceptions={
    "emporio mel": ["cia do whisky", "PAGAMENTO DE BOLETO - CIA DO WHISKY"], 
    "ministerio da fazenda": "receita federal",
    "abrasel sao paulo": "Associacao Brasileira de Bares",
    "PSS - CENTRAL DA LIMPEZA LTDA": "Psss Ltda",
    "PSS – CENTRAL DA LIMPEZA LTDA": "Psss Ltda",
    "HORTIFRUTI DO CHEF LTDA": ["Ng27 Consultoria e Gestao Empr", "PAGAMENTO DE BOLETO - NG27 CONSULTORIA E GESTAO EMPR"],
    "AROMIZY LOCACAO E DISTRIBUICAO LTDA.": "Purifikar Sp Locacao",
    "CAROLINA AMANCIO": "Nu Pagamentos Sa",
    "CASANDRA DEVOTTO": "Pagseguro Internet I.P. S.A.",
    "ICE4": "Ice4pros Fabrica de Gelo Ltda",
    "MEXBRA ALIMENTOS LTDA": "Pagcerto Instituicao de Pagamento L",
    "DE LA CROIX VINHOS": "Geoffroy Alain Marie de La Cro",
    "FAMIGERADA COMERCIO E EXPORTACAO DE BEBIDAS LTDA": "Pagcerto Instituicao de Pagamento L",
    "FACUNDO GUERRA RIVERO": "PIX - ENVIADO - 25/08 11:10 ARCOS B RESTAURANTE LTDA",
    "ANDREIA SANTOS FREITAS DUARTE": "Distribuicoes e Representacoes Dede",
    "PIS": ["Receita Federal", "Ministerio da Fazenda"],
    "INSS": ["Receita Federal", "Ministerio da Fazenda", "IMPOSTOS - RFB-DARF CODIGO DE BARRAS"],
    "ISS": ["Receita Federal", "Municipio de Sao Paulo", "IMPOSTOS - PREF MUN SAO PAULO 02"],
    "ICMS": ["Receita Federal", "Ministerio da Fazenda", "Municipio de Sao Paulo", "Estado de Sao Paulo", "IMPOSTOS - SEFAZ/SP-AMBIENTEPAG"],
    "IRRF": ["Receita Federal", "Ministerio da Fazenda", "IMPOSTOS - RFB-DARF CODIGO DE BARRAS"],
    "FGTS": "CAIXA ECONOMICA FEDERAL",
    "MUTUO ELAINE": ["TRANSF CC PARA CC PJ TEMPUS FUGIT PARTICIPACOES E. LT", "Tempus"],
    "MINISTERIO DA FAZENDA": ["Receita Federal", "Ministerio da Fazenda", "IMPOSTOS - RFB-DARF CODIGO DE BARRAS"],
    "BATALHA FABRICA DE PAES LTDA": "PAGAMENTO DE BOLETO - ZOOP BRASIL",
    "VILA OLIMPIA MASSAS": "Pagseguro Internet I.P. S.A.",
    "BATARD PADARIA ARTESANAL LTDA": "PAGAMENTO DE BOLETO - CELCOIN INSTITUICAO DE PAGAMEN",
    "TELEFONICA BRASIL S/A": ["PIX - ENVIADO - 16/07 14:57 CARLOS EDUARDO SANTOS DIB", "PIX - ENVIADO - 18/06 13:44 CARLOS EDUARDO SANTOS DIB", "PIX - ENVIADO - 21/05 11:26 CARLOS EDUARDO SANTOS DIB", "PIX - ENVIADO - 16/04 13:38 CARLOS EDUARDO SANTOS DIB", "PIX - ENVIADO - 26/03 15:30 CARLOS EDUARDO SANTOS DIB"]
}  


# Mapeamento Class_Cont_1 para Class_Cont_0
mapeamento_class_cont = {
    'Custo Mercadoria Vendida': 'Custo Mercadoria Vendida',
    'Custos Artístico Geral': 'Custos Artístico Geral',
    'Gorjeta': 'Mão de Obra',
    'Utilidades': 'Utilidades',
    'Impostos sobre Venda': 'Impostos',
    'Custo de Ocupação': 'Ocupação',
    'Mão de Obra - Salários': 'Mão de Obra',
    'Mão de Obra - PJ': 'Mão de Obra',
    'Mão de Obra - Extra': 'Mão de Obra',
    'Mão de Obra - Benefícios': 'Mão de Obra',
    'MAO DE OBRA FIXA/ TEMPORARIOS': 'Mão de Obra',
    'Mão de Obra - Pro Labores': 'Mão de Obra',
    'Mão de obra': 'Mão de Obra',
    'Endividamento': 'Endividamento',
    'CUSTO ARTISTICO': 'Custos Artístico Geral',
    'Serviços de Terceiros': 'Serviços de Terceiros',
    'Investimento - CAPEX': 'Investimento - Capex',
    'Marketing': 'Marketing',
    'INSUMOS': 'Custo Mercadoria Vendida',
    'UTILIDADES': 'Utilidades',
    'IMPOSTOS SOBRE VENDA': 'Impostos',
    'Manutenção': 'Manutenção',
    'Mão de Obra - Encargos e Provisões': 'Mão de Obra',
    'ENDIVIDAMENTO': 'Endividamento',
    'Dividendos e Remunerações Variáveis': 'Dividendos e Remunerações Variáveis',
    'Locação de Equipamentos': 'Locação de Equipamentos',
    'SERVICOS DE TERCEIROS': 'Serviços de Terceiros',
    'CUSTOS COM MARKETING': 'Marketing',
    'Informática e TI': 'Informática e TI',
    'CUSTOS DE EVENTOS': 'Custos de Eventos',
    'INVESTIMENTOS': 'Investimento - Capex',
    'Despesas Financeiras': 'Despesas Financeiras',
    'DESPESAS GERAIS': 'Utilidades',
    'Custos de Eventos': 'Custos de Eventos',
    'ADIANTAMENTO A FORNECEDORES': 'Custo Mercadoria Vendida',
    'Deduções sobre Venda': 'Deduções sobre Venda',
    'IMPOSTOS/ TRIBUTOS': 'Impostos',
    'LOCACOES': 'Locação de Equipamentos',
    'SISTEMAS/ T.I': 'Informática e TI',
    'Despesas com Transporte / Hospedagem': 'Despesas com Transporte / Hospedagem',
    'DESPESAS BANCARIAS': 'Despesas Financeiras',
    'CUSTO DA MERCADORIA VENDIDA': 'Custo Mercadoria Vendida',
    'CUSTO DE OCUPACAO': 'Ocupação',
    'CUSTOS DE MANUTENCAO': 'Manutenção',
    'DEDUCOES SOBRE VENDA': 'Deduções sobre Venda',
    'Imposto de Renda': 'Impostos',
    'Patrocínio': 'Despesas com Patrocínio',
    'Sistema de Franquias': 'Sistema de Franquias',
    'Adiantamento a Fornecedores': 'Custo Mercadoria Vendida',
    'Deduções sobre Receita': 'Deduções sobre Receita',
    'Insumos - A&B': 'Custo Mercadoria Vendida', # ???
    'Investimento - Capex': 'Investimento - Capex',
    'Locações': 'Locação de Equipamentos',
    'Eventos': 'Custos de Eventos',
    'Impostos e Taxas': 'Impostos',
    'Locação de Equipamentos Eventos': 'Locação de Equipamentos',
    # Faturamento Bruto
}


# Receitas/Despesas Financeiras (Orçamento Operacional) - taxa estimada sobre Faturamento Bruto
TAXA_DESPESAS_FINANCEIRAS_PADRAO = 0.0015  # 0,15%
TAXA_DESPESAS_FINANCEIRAS_EXCECOES = {
    # 'Nome da Casa': taxa,  # preencher conforme o usuário for passando as exceções
}