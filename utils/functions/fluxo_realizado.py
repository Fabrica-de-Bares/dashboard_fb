import streamlit as st
import pandas as pd
import numpy as np
from utils.functions.general_functions_conciliacao import format_brazilian


# Filtra df por casas selecionadas e data
def filtra_df(df, col_data, ids_casas_selecionadas, start_date, end_date, entradas_mutuos=False, saidas_mutuos=False):
    if not entradas_mutuos and not saidas_mutuos:
        df_filtrado = df[df['ID_Casa'].isin(ids_casas_selecionadas)]
    if entradas_mutuos:
        df_filtrado = df[df['ID_Casa_Entrada'].isin(ids_casas_selecionadas)]
    if saidas_mutuos:
        df_filtrado = df[df['ID_Casa_Saida'].isin(ids_casas_selecionadas)]

    df_filtrado = df_filtrado[(df_filtrado[col_data] >= start_date) & (df_filtrado[col_data] <= end_date)]
    return df_filtrado


# Converte numeros em string para float para cálculos
def converte_string_float(df, col_valor):
    valores_float = ( # transforma valores em float
        df[col_valor]
        .str.replace(".", "", regex=False)   # remove separador de milhar
        .str.replace(",", ".", regex=False)  # vírgula decimal para ponto
        .replace('', np.nan)                  # strings vazias → NaN
        .astype(float)
    )
    return valores_float


# Exibe card de valor total de contagem do df
def total_valores_filtrados(df_aggrid, tam_df_aggrid, col_valor, despesa_com_parc=False):
    if not despesa_com_parc:
        if not df_aggrid.empty and col_valor in df_aggrid.columns:
            valores_filtrados = converte_string_float(df_aggrid, col_valor) # transforma valores em float
            total_filtrado = valores_filtrados.sum()
            total_filtrado_fmt = format_brazilian(total_filtrado)

            st.markdown(f"""
            <div style="
                background-color: transparent; 
                border: 1px solid #d78f18; 
                border-radius: 4px; 
                padding: 8px 12px; 
                margin: 5px 0; 
                text-align: center;
                display: inline-block;
            ">
                <span style="color: #d78f18; font-weight: bold;">💰 Total: R$ {total_filtrado_fmt}</span>
                <span style="color: black; margin-left: 10px;">({tam_df_aggrid} registros)</span>
            </div>
            """, unsafe_allow_html=True)
        
    else:
        if not df_aggrid.empty:
            if col_valor in df_aggrid.columns:
                valores_parcelas = converte_string_float(df_aggrid, col_valor) # transforma valores em float
                total_parcelas = valores_parcelas.sum()
                total_parcelas_fmt = format_brazilian(total_parcelas)
            
            if "Valor_Original" in df_aggrid.columns:
                valores_originais = converte_string_float(df_aggrid, 'Valor_Original') # transforma valores em float
                total_original = valores_originais.sum()
                total_original_fmt = format_brazilian(total_original)
            
            st.markdown(f"""
            <div style="
                background-color: transparent; 
                border: 1px solid #d78f18; 
                border-radius: 4px; 
                padding: 8px 12px; 
                margin: 5px 0; 
                text-align: center;
                display: inline-block;
            ">
                <span style="color: #d78f18; font-weight: bold;">💰 Parcelas: R$ {total_parcelas_fmt}</span>
                <span style="color: black; margin-left: 10px;">| Original: R$ {total_original_fmt}</span>
                <span style="color: black; margin-left: 10px;">({tam_df_aggrid} registros)</span>
            </div>
            """, unsafe_allow_html=True)


# Preparando dados para o gráfico - Fluxo de Caixa Consolidado por Mês
def prepare_monthly_data(
        df_extrato_zig_filtrada, 
        df_parc_receit_extr_filtrada, 
        df_eventos_filtrada, 
        df_desbloqueios_filtrada,
        df_custos_blueme_sem_parcelam_filtrada,
        df_custos_blueme_com_parcelam_filtrada,
        df_bloqueios_filtrada):
    
    ## Receitas - Extrato Zig
    receitas_zig = df_extrato_zig_filtrada.copy()
    receitas_zig['Data_Liquidacao'] = pd.to_datetime(receitas_zig['Data_Liquidacao'], errors='coerce', dayfirst=True)

    # Converte Valor para float (tratando vírgula como separador decimal)
    # receitas_zig['Valor'] = converte_string_float(receitas_zig, 'Valor') # transforma valores em float
    receitas_zig['Valor'] = pd.to_numeric(receitas_zig['Valor'], errors='coerce')

    mask_extrato_zig = receitas_zig['Descricao'].isin(["Saque", "Antecipação"])
    receitas_zig = receitas_zig[mask_extrato_zig]
    receitas_zig['Valor'] = receitas_zig['Valor'] * (-1)  # Saques são negativos no Zig → positivo = caixa recebido
    receitas_zig['Mes_Ano'] = receitas_zig['Data_Liquidacao'].dt.to_period('M')
    receitas_zig['Tipo'] = 'Extrato Zig'
    receitas_zig_monthly = receitas_zig.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()
    
    ## Receitas - Parcelas Extraordinárias 
    receitas_extr = df_parc_receit_extr_filtrada.copy()
    receitas_extr['Recebimento_Parcela'] = pd.to_datetime(receitas_extr['Recebimento_Parcela'], errors='coerce', dayfirst=True)
    
    # Converte Valor para float 
    # receitas_extr['Valor_Parcela'] = converte_string_float(receitas_extr, 'Valor_Parcela') # transforma valores em float
    receitas_extr['Valor_Parcela'] = pd.to_numeric(receitas_extr['Valor_Parcela'], errors='coerce')

    receitas_extr['Mes_Ano'] = receitas_extr['Recebimento_Parcela'].dt.to_period('M')
    receitas_extr['Tipo'] = 'Extraordinária'
    receitas_extr_monthly = receitas_extr.groupby(['Mes_Ano', 'Tipo'])['Valor_Parcela'].sum().reset_index()
    receitas_extr_monthly.rename(columns={'Valor_Parcela': 'Valor'}, inplace=True)

    ## Receitas - Eventos
    receitas_eventos = df_eventos_filtrada.copy()
    receitas_eventos['Recebimento_Parcela'] = pd.to_datetime(receitas_eventos['Recebimento_Parcela'], errors='coerce', dayfirst=True)
    
    # Converte Valor para float 
    # receitas_eventos['Valor_Parcela'] = converte_string_float(receitas_eventos, 'Valor_Parcela') # transforma valores em float
    receitas_eventos['Valor_Parcela'] = pd.to_numeric(receitas_eventos['Valor_Parcela'], errors='coerce')

    receitas_eventos['Mes_Ano'] = receitas_eventos['Recebimento_Parcela'].dt.to_period('M')
    receitas_eventos['Tipo'] = 'Eventos'
    receitas_eventos_monthly = receitas_eventos.groupby(['Mes_Ano', 'Tipo'])['Valor_Parcela'].sum().reset_index()
    receitas_eventos_monthly.rename(columns={'Valor_Parcela': 'Valor'}, inplace=True)
    
    ## Receitas - Desbloqueios Judiciais
    desbloqueios_judiciais = df_desbloqueios_filtrada.copy()
    desbloqueios_judiciais['Data_Transacao'] = pd.to_datetime(desbloqueios_judiciais['Data_Transacao'], errors='coerce', dayfirst=True)
    
    # Converte Valor para float 
    # desbloqueios_judiciais['Valor'] = converte_string_float(desbloqueios_judiciais, 'Valor') # transforma valores em float
    desbloqueios_judiciais['Valor'] = pd.to_numeric(desbloqueios_judiciais['Valor'], errors='coerce')

    desbloqueios_judiciais['Mes_Ano'] = desbloqueios_judiciais['Data_Transacao'].dt.to_period('M')
    desbloqueios_judiciais['Tipo'] = 'Desbloqueios'
    desbloqueios_judiciais_monthly = desbloqueios_judiciais.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()    

    ## Despesas - BlueMe Sem Parcelamento 
    despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
    despesas_sem_parc['Realizacao_Pgto'] = pd.to_datetime(despesas_sem_parc['Realizacao_Pgto'], errors='coerce', dayfirst=True)

    # Converte Valor para float
    # despesas_sem_parc['Valor'] = converte_string_float(despesas_sem_parc, 'Valor') # transforma valores em float
    despesas_sem_parc['Valor'] = pd.to_numeric(despesas_sem_parc['Valor'], errors='coerce')

    despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
    despesas_sem_parc['Tipo'] = 'Sem Parcelamento'
    despesas_sem_parc_monthly = despesas_sem_parc.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()
    
    ## Despesas - BlueMe Com Parcelamento 
    despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
    despesas_com_parc['Realiz_Parcela'] = pd.to_datetime(despesas_com_parc['Realiz_Parcela'], errors='coerce', dayfirst=True)

    # despesas_com_parc['Valor_Parcela'] = converte_string_float(despesas_com_parc, 'Valor_Parcela') # transforma valores em float
    despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')

    despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
    despesas_com_parc['Tipo'] = 'Com Parcelamento'
    despesas_com_parc_monthly = despesas_com_parc.groupby(['Mes_Ano', 'Tipo'])['Valor_Parcela'].sum().reset_index()
    despesas_com_parc_monthly.rename(columns={'Valor_Parcela': 'Valor'}, inplace=True)
    
    ## Despesas - Bloqueios Judiciais
    bloqueios_judiciais = df_bloqueios_filtrada.copy()
    bloqueios_judiciais['Data_Transacao'] = pd.to_datetime(bloqueios_judiciais['Data_Transacao'], errors='coerce', dayfirst=True)

    # bloqueios_judiciais['Valor'] = converte_string_float(bloqueios_judiciais, 'Valor') # transforma valores em float
    bloqueios_judiciais['Valor'] = pd.to_numeric(bloqueios_judiciais['Valor'], errors='coerce')
    bloqueios_judiciais['Valor'] = bloqueios_judiciais['Valor'] * (-1)

    bloqueios_judiciais['Mes_Ano'] = bloqueios_judiciais['Data_Transacao'].dt.to_period('M')
    bloqueios_judiciais['Tipo'] = 'Bloqueios'
    bloqueios_judiciais_monthly = bloqueios_judiciais.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()
    

    # Combinando dados de receitas
    receitas_data = pd.concat([receitas_zig_monthly, receitas_extr_monthly, receitas_eventos_monthly, desbloqueios_judiciais_monthly], ignore_index=True)
    receitas_data['Categoria'] = 'Receitas'
    
    # Combinando dados de despesas
    despesas_data = pd.concat([despesas_sem_parc_monthly, despesas_com_parc_monthly, bloqueios_judiciais_monthly], ignore_index=True)
    despesas_data['Categoria'] = 'Despesas'
    
    # Combinando todos os dados
    all_data = pd.concat([receitas_data, despesas_data], ignore_index=True)
    
    # Convertendo Mes_Ano para string para melhor visualização (formato MM/YYYY)
    all_data['Mes_Ano_Str'] = all_data['Mes_Ano'].dt.strftime('%m/%Y')
    
    return all_data


# Preparando dados para Tabelas Dinâmicas - Class_Cont_0, Class_Cont_1 e Class_Cont_2
def prepare_pivot_data_class_despesas(df_custos_blueme_sem_parcelam_filtrada, df_custos_blueme_com_parcelam_filtrada, mapeamento_class_cont, classe=None):
    if classe == 0 or classe == 1:
        group_by = ['Class_Cont_1', 'Mes_Ano']
        columns = ['Class_Cont_1', 'Mes_Ano', 'Valor']

    if classe == 2:
        group_by = ['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano']
        columns = ['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano', 'Valor']

    ## Despesas - BlueMe Sem Parcelamento 
    despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
    despesas_sem_parc["Realizacao_Pgto"] = pd.to_datetime(despesas_sem_parc["Realizacao_Pgto"], errors="coerce", dayfirst=True)
    despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
    # despesas_sem_parc['Valor'] = converte_string_float(despesas_sem_parc, 'Valor') # transforma valores em float
    despesas_sem_parc['Valor'] = pd.to_numeric(despesas_sem_parc['Valor'], errors='coerce')

    ## Despesas - BlueMe Com Parcelamento
    despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
    despesas_com_parc["Realiz_Parcela"] = pd.to_datetime(despesas_com_parc["Realiz_Parcela"], errors="coerce", dayfirst=True)
    despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
    # despesas_com_parc['Valor_Parcela'] = converte_string_float(despesas_com_parc, 'Valor_Parcela') # transforma valores em float
    despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')

    # Combinando dados
    if not despesas_sem_parc.empty:
        despesas_sem_parc_grouped = despesas_sem_parc.groupby(group_by)['Valor'].sum().reset_index()
    else:
        despesas_sem_parc_grouped = pd.DataFrame(columns=columns)
        
    if not despesas_com_parc.empty:
        despesas_com_parc_grouped = despesas_com_parc.groupby(group_by)['Valor_Parcela'].sum().reset_index()
        despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
    else:
        despesas_com_parc_grouped = pd.DataFrame(columns=columns)
    
    # Combinando os resultados
    all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)

    if classe == 0: # class_cont_0
        # Agrupando novamente para consolidar
        if not all_despesas.empty:
            despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
            
            # Adicionando Class_Cont_0 baseado no mapeamento
            despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_1'].map(mapeamento_class_cont)
            
            # Para Class_Cont_1 não mapeadas, usar a própria Class_Cont_1
            despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_0'].fillna(despesas_consolidadas['Class_Cont_1'])
            
            # Agrupando por Class_Cont_0
            despesas_class = despesas_consolidadas.groupby(['Class_Cont_0', 'Mes_Ano'])['Valor'].sum().reset_index()
            return despesas_class
        else:
            return pd.DataFrame()
    
    if classe == 1: # class_cont_1
        # Agrupando novamente para consolidar
        if not all_despesas.empty:
            despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
            
            # Criando tabela dinâmica usando pivot
            pivot_table = despesas_consolidadas.pivot(
                index='Class_Cont_1',
                columns='Mes_Ano',
                values='Valor'
            ).fillna(0)
            
            # Convertendo índices de coluna para string
            pivot_table.columns = pivot_table.columns.astype(str)
            
            # Adicionando coluna de total
            pivot_table['Total'] = pivot_table.sum(axis=1)
            
            # Ordenando por total (maior para menor)
            pivot_table = pivot_table.sort_values('Total', ascending=False)
            
            # Resetando o índice para incluir Class_Cont_1 como coluna
            pivot_table = pivot_table.reset_index()
            return pivot_table
        else:
            return pd.DataFrame()
        
    if classe == 2: # class_cont_2
        # Agrupando novamente para consolidar
        if not all_despesas.empty:
            despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
            return despesas_consolidadas
        else:
            return pd.DataFrame()
    
    
# Criando DataFrame de referência: Tabela de Referência - Mapeamento Class_Cont_0 ↔ Class_Cont_1
def create_mapping_reference(mapeamento_class_cont, df_custos_blueme_sem_parcelam_filtrada, df_custos_blueme_com_parcelam_filtrada):
    # Criando lista de mapeamentos
    mapping_list = []
    for class_cont_1, class_cont_0 in mapeamento_class_cont.items():
        mapping_list.append({
            'Class_Cont_0': class_cont_0,
            'Class_Cont_1': class_cont_1,
            'Status': 'Mapeado'
        })
    
    # Verificando Class_Cont_1 que aparecem nos dados mas não estão mapeadas
    all_class_cont_1 = set()
    
    # Despesas sem parcelamento
    if not df_custos_blueme_sem_parcelam_filtrada.empty:
        # Filtrando valores não nulos
        class_cont_1_sem_parc = df_custos_blueme_sem_parcelam_filtrada['Class_Cont_1'].dropna().unique()
        all_class_cont_1.update(class_cont_1_sem_parc)
    
    # Despesas com parcelamento
    if not df_custos_blueme_com_parcelam_filtrada.empty:
        # Filtrando valores não nulos
        class_cont_1_com_parc = df_custos_blueme_com_parcelam_filtrada['Class_Cont_1'].dropna().unique()
        all_class_cont_1.update(class_cont_1_com_parc)
    
    # Verificando quais não estão mapeadas
    unmapped = all_class_cont_1 - set(mapeamento_class_cont.keys())
    
    for class_cont_1 in sorted(unmapped):
        mapping_list.append({
            'Class_Cont_0': class_cont_1,  # Usa a própria Class_Cont_1
            'Class_Cont_1': class_cont_1,
            'Status': 'Não Mapeado'
        })
    
    return pd.DataFrame(mapping_list)


# Preparando dados para Tabela - Receitas por Categoria
# def prepare_pivot_data_class_receitas(df_extrato_zig, df_receitas_extr, df_eventos, df_desbloqueios):
#     ## Receitas - Extrato Zig
#     extrato_zig = df_extrato_zig.copy()
#     extrato_zig["Data_Liquidacao"] = pd.to_datetime(extrato_zig["Data_Liquidacao"], errors="coerce", dayfirst=True)
#     extrato_zig['Mes_Ano'] = extrato_zig['Data_Liquidacao'].dt.to_period('M')
#     extrato_zig['Valor'] = converte_string_float(extrato_zig, 'Valor') # transforma valores em float
#     extrato_zig['Valor'] = pd.to_numeric(extrato_zig['Valor'], errors='coerce')
#     extrato_zig['Valor'] = extrato_zig['Valor'] * (-1) 
#     st.write(extrato_zig)

#     ## Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
#     despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
#     despesas_com_parc["Realiz_Parcela"] = pd.to_datetime(despesas_com_parc["Realiz_Parcela"], errors="coerce", dayfirst=True)
#     despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
#     despesas_com_parc['Valor_Parcela'] = converte_string_float(despesas_com_parc, 'Valor_Parcela') # transforma valores em float
#     despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')

#     # Combinando dados
#     if not despesas_sem_parc.empty:
#         despesas_sem_parc_grouped = despesas_sem_parc.groupby(group_by)['Valor'].sum().reset_index()
#     else:
#         despesas_sem_parc_grouped = pd.DataFrame(columns=columns)
        
#     if not despesas_com_parc.empty:
#         despesas_com_parc_grouped = despesas_com_parc.groupby(group_by)['Valor_Parcela'].sum().reset_index()
#         despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
#     else:
#         despesas_com_parc_grouped = pd.DataFrame(columns=columns)
    
#     # Combinando os resultados
#     all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)

#     if classe == 0: # class_cont_0
#         # Agrupando novamente para consolidar
#         if not all_despesas.empty:
#             despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
            
#             # Adicionando Class_Cont_0 baseado no mapeamento
#             despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_1'].map(mapeamento_class_cont)
            
#             # Para Class_Cont_1 não mapeadas, usar a própria Class_Cont_1
#             despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_0'].fillna(despesas_consolidadas['Class_Cont_1'])
            
#             # Agrupando por Class_Cont_0
#             despesas_class = despesas_consolidadas.groupby(['Class_Cont_0', 'Mes_Ano'])['Valor'].sum().reset_index()
#             return despesas_class
#         else:
#             return pd.DataFrame()
    
#     if classe == 1: # class_cont_1
#         # Agrupando novamente para consolidar
#         if not all_despesas.empty:
#             despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
            
#             # Criando tabela dinâmica usando pivot
#             pivot_table = despesas_consolidadas.pivot(
#                 index='Class_Cont_1',
#                 columns='Mes_Ano',
#                 values='Valor'
#             ).fillna(0)
            
#             # Convertendo índices de coluna para string
#             pivot_table.columns = pivot_table.columns.astype(str)
            
#             # Adicionando coluna de total
#             pivot_table['Total'] = pivot_table.sum(axis=1)
            
#             # Ordenando por total (maior para menor)
#             pivot_table = pivot_table.sort_values('Total', ascending=False)
            
#             # Resetando o índice para incluir Class_Cont_1 como coluna
#             pivot_table = pivot_table.reset_index()
#             return pivot_table
#         else:
#             return pd.DataFrame()
        
#     if classe == 2: # class_cont_2
#         # Agrupando novamente para consolidar
#         if not all_despesas.empty:
#             despesas_consolidadas = all_despesas.groupby(group_by)['Valor'].sum().reset_index()
#             return despesas_consolidadas
#         else:
#             return pd.DataFrame()
    
    
# # Criando DataFrame de referência: Tabela de Referência - Mapeamento Class_Cont_0 ↔ Class_Cont_1
# def create_mapping_reference(mapeamento_class_cont, df_custos_blueme_sem_parcelam_filtrada, df_custos_blueme_com_parcelam_filtrada):
#     # Criando lista de mapeamentos
#     mapping_list = []
#     for class_cont_1, class_cont_0 in mapeamento_class_cont.items():
#         mapping_list.append({
#             'Class_Cont_0': class_cont_0,
#             'Class_Cont_1': class_cont_1,
#             'Status': 'Mapeado'
#         })
    
#     # Verificando Class_Cont_1 que aparecem nos dados mas não estão mapeadas
#     all_class_cont_1 = set()
    
#     # Despesas sem parcelamento
#     if not df_custos_blueme_sem_parcelam_filtrada.empty:
#         # Filtrando valores não nulos
#         class_cont_1_sem_parc = df_custos_blueme_sem_parcelam_filtrada['Class_Cont_1'].dropna().unique()
#         all_class_cont_1.update(class_cont_1_sem_parc)
    
#     # Despesas com parcelamento
#     if not df_custos_blueme_com_parcelam_filtrada.empty:
#         # Filtrando valores não nulos
#         class_cont_1_com_parc = df_custos_blueme_com_parcelam_filtrada['Class_Cont_1'].dropna().unique()
#         all_class_cont_1.update(class_cont_1_com_parc)
    
#     # Verificando quais não estão mapeadas
#     unmapped = all_class_cont_1 - set(mapeamento_class_cont.keys())
    
#     for class_cont_1 in sorted(unmapped):
#         mapping_list.append({
#             'Class_Cont_0': class_cont_1,  # Usa a própria Class_Cont_1
#             'Class_Cont_1': class_cont_1,
#             'Status': 'Não Mapeado'
#         })
    
#     return pd.DataFrame(mapping_list)

