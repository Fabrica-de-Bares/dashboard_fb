import streamlit as st
import pandas as pd
from utils.functions.general_functions_conciliacao import *
from utils.functions.conciliacoes_conta import cria_tabs_contas
from utils.functions.conciliacoes_conta import *
from utils.queries_conciliacao import *

# Função auxiliar para somar valores agrupados por data
def somar_por_data(df, col_data, col_valor, datas):
    s = df.groupby(col_data)[col_valor].sum()
    # s.index = pd.to_datetime(s.index).date  # garante que o índice é só data
    return s.reindex(datas, fill_value=0).reset_index(drop=True).astype(float)


# Função auxiliar para calcular diferenças de contas a pagar e receber
def calcula_diferencas(df, coluna_principal, colunas_valores):
    soma = 0
    diferenca = 0
    soma = sum(df[col] for col in colunas_valores)
    diferenca = df[coluna_principal] - soma
    return diferenca


# Função para conciliação geral inicial
def conciliacao_inicial(id_casa, casa, start_date, end_date, tab):
    ## Definindo Bases - Filtra por casa e data ##
    
    ## Extratos Zig
    df_extrato_zig = GET_EXTRATO_ZIG()
    df_extrato_zig_filtrada, df_extrato_zig_formatada = filtra_formata_df(df_extrato_zig, "Data_Liquidacao", id_casa, start_date, end_date)
    
    ## Zig_Faturamento
    df_zig_faturam = GET_ZIG_FATURAMENTO()
    df_zig_faturam_filtrada, df_zig_faturam_formatada= filtra_formata_df(df_zig_faturam, "Data_Venda", id_casa, start_date, end_date)

    ## Parcelas Receitas Extraordinarias
    df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
    df_parc_receit_extr_filtrada, df_parc_receit_extr_formatada = filtra_formata_df(df_parc_receit_extr, "Recebimento_Parcela", id_casa, start_date, end_date)
    df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada.copy()

    df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada_copia[ # não vou exibir eventos a partir de setembro/2025
        ~(
            (df_parc_receit_extr_filtrada_copia["Classif_Receita"].str.lower() == "eventos") &
            ((df_parc_receit_extr_filtrada_copia["Recebimento_Parcela"].dt.month >= 9) &
             (df_parc_receit_extr_filtrada_copia["Recebimento_Parcela"].dt.year >= 2025))
        )
    ]
    if id_casa == 110: # Blue Note
        df_parc_receit_extr_filtrada_copia = df_parc_receit_extr_filtrada_copia[ # não vou exibir essa receita com status_pgto = 'Desconto' - ajuste pedido 18/02/26
            df_parc_receit_extr_filtrada_copia["Status_Pgto"] != 'Desconto'
        ]
    df_parc_receit_extr_formatada = formata_df(df_parc_receit_extr_filtrada_copia)

    ## Custos BlueMe Sem Parcelamento
    df_custos_blueme_sem_parcelam = GET_CUSTOS_BLUEME_SEM_PARC()
    df_custos_blueme_sem_parcelam_filtrada, df_custos_blueme_sem_parcelam_formatada = filtra_formata_df(df_custos_blueme_sem_parcelam, "Realizacao_Pgto", id_casa, start_date, end_date)

    ## Custos BlueMe Com Parcelamento
    df_custos_blueme_com_parcelam = GET_CUSTOS_BLUEME_COM_PARC()
    df_custos_blueme_com_parcelam_filtrada, df_custos_blueme_com_parcelam_formatada = filtra_formata_df(df_custos_blueme_com_parcelam, "Realiz_Parcela", id_casa, start_date, end_date)
    
    ## Extratos Bancarios
    df_extratos_bancarios = GET_EXTRATOS_BANCARIOS()
    df_extratos_bancarios_filtrada, df_extratos_bancarios_formatada = filtra_formata_df(df_extratos_bancarios, "Data_Transacao", id_casa, start_date, end_date)
    
    ## Mutuos
    df_mutuos = GET_MUTUOS()
    df_mutuos_filtrada = df_mutuos[(df_mutuos['ID_Casa_Saida'] == id_casa) | (df_mutuos['ID_Casa_Entrada'] == id_casa)] 
    df_mutuos_filtrada = df_mutuos_filtrada[(df_mutuos_filtrada["Data_Mutuo"] >= start_date) & (df_mutuos_filtrada["Data_Mutuo"] <= end_date)] 

    # Copia para formatação brasileira de colunas numéricas 
    df_mutuos_formatada = df_mutuos_filtrada.copy() 
    
    # Aplica formatação brasileira em colunas numéricas 
    for col in df_mutuos_formatada.select_dtypes(include='object').columns: 
        if col != "Doc_NF":
            df_mutuos_formatada[col] = df_mutuos_formatada[col].apply(format_brazilian) 
    
    # Aplica formatação brasileira em colunas de data 
    for col in df_mutuos_formatada.select_dtypes(include='datetime').columns: 
        df_mutuos_formatada[col] = pd.to_datetime(df_mutuos_formatada[col]).dt.strftime('%d-%m-%Y %H:%M') 
    
    ## Tesouraria
    df_tesouraria = GET_TESOURARIA()
    df_tesouraria_filtrada, df_tesouraria_formatada = filtra_formata_df(df_tesouraria, "Data_Transacao", id_casa, start_date, end_date)

    ## Ajustes Conciliação
    df_ajustes_conciliacao = GET_AJUSTES()
    df_ajustes_conciliacao_filtrada, df_ajustes_conciliacao_formatada = filtra_formata_df(df_ajustes_conciliacao, "Data_Ajuste", id_casa, start_date, end_date)

    ## Bloqueios Judiciais
    df_bloqueios_judiciais = GET_BLOQUEIOS_JUDICIAIS()
    df_bloqueios_judiciais_filtrada, df_bloqueios_judiciais_formatada = filtra_formata_df(df_bloqueios_judiciais, "Data_Transacao", id_casa, start_date, end_date)

    ## Eventos
    df_eventos = GET_EVENTOS()
    df_eventos = df_eventos[~(df_eventos['Forma_Pgto'] == 'Permuta')] # Desconsdera eventos pagos com 'Permuta'
    if id_casa == 110: # Blue Note
        df_eventos = df_eventos[ # não vou exibir essa receita com status_pgto = 'Desconto' - ajuste pedido 24/03/26
            df_eventos["Status_Pgto"] != 'Desconto'
        ]
    df_eventos_filtrada, df_eventos_formatada = filtra_formata_df(df_eventos, "Recebimento_Parcela", id_casa, start_date, end_date)

    ## Contas Bancárias
    df_contas = GET_CONTAS_BANCARIAS()


    if tab == 'Geral': # Exibe todos os dfs
        st.subheader("Extrato Zig")
        st.dataframe(df_extrato_zig_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Zig Faturamento")
        st.dataframe(df_zig_faturam_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Parcelas Receitas Extraordinárias")
        st.dataframe(df_parc_receit_extr_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Eventos")
        st.dataframe(df_eventos_formatada, width='stretch', hide_index=True)
        st.divider()
        
        st.subheader("Despesas BlueMe Sem Parcelamento")
        st.dataframe(df_custos_blueme_sem_parcelam_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Despesas BlueMe Com Parcelamento")
        st.dataframe(df_custos_blueme_com_parcelam_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Extratos Bancários")
        st.dataframe(df_extratos_bancarios_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Mútuos")
        st.dataframe(df_mutuos_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Tesouraria")
        st.dataframe(df_tesouraria_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Ajustes Conciliação")
        st.dataframe(df_ajustes_conciliacao_formatada, width='stretch', hide_index=True)
        st.divider()

        st.subheader("Bloqueios Judiciais")
        st.dataframe(df_bloqueios_judiciais_formatada, width='stretch', hide_index=True)
        st.divider()   

        
        ## df de Conciliação
        st.subheader("Conciliação")

        # Criar um DataFrame com a data selecionada
        df_conciliacao = pd.DataFrame()
        st.session_state['df_conciliacao'] = None

        if 'Data' not in df_conciliacao.columns:
            datas = pd.date_range(start=start_date, end=end_date)
            df_conciliacao['Data'] = datas
        
        # Colunas 
        # Extrato Zig (Saques) #
        if 'Extrato Zig (Saques)' not in df_conciliacao.columns:
            df_conciliacao['Extrato Zig (Saques)'] = somar_por_data(
                df_extrato_zig_filtrada[df_extrato_zig_filtrada['Descricao'].isin(["Saque", "Antecipação"])],
                "Data_Liquidacao", "Valor", datas
            ) * (-1)

        # Faturam dinheiro #
        if 'Faturam dinheiro' not in df_conciliacao.columns:
            df_conciliacao['Faturam dinheiro'] = 0 # stand-by

        # Receitas Extraordinárias #
        # Data limite (eventos)
        data_limite = pd.Timestamp("2025-09-01")

        # Se data >= setembro, desconsidera eventos como receita extraordinária
        if 'Receitas Extraordinárias' not in df_conciliacao.columns:
            # aplica regra condicional
            df_parc_receit_extr_filtrada = df_parc_receit_extr_filtrada[
                (
                    (df_parc_receit_extr_filtrada['Recebimento_Parcela'] < data_limite) |
                    (df_parc_receit_extr_filtrada['Classif_Receita'] != 'Eventos')
                )
            ]

            # não vai considerar na soma essa receita com status_pgto = 'Desconto' - ajuste pedido 18/02/26
            if id_casa == 110: # Blue Note
                df_parc_receit_extr_filtrada = df_parc_receit_extr_filtrada[
                    (df_parc_receit_extr_filtrada['Status_Pgto'] != 'Desconto')
                ]

            # soma final
            df_conciliacao['Receitas Extraordinárias'] = somar_por_data(
                df_parc_receit_extr_filtrada, "Recebimento_Parcela", "Valor_Parcela", datas
            )

        # Eventos (desmembrar de Receitas Extraordinárias) #
        if 'Eventos' not in df_conciliacao.columns:
            if id_casa == 110: # Blue Note
                df_eventos_filtrada = df_eventos_filtrada[ # não vou exibir essa receita com status_pgto = 'Desconto' - ajuste pedido 24/03/26
                    df_eventos_filtrada["Status_Pgto"] != 'Desconto'
                ]

            df_conciliacao['Eventos'] = somar_por_data(
                df_eventos_filtrada, "Recebimento_Parcela", "Valor_Parcela", datas
            )

        # Entradas Mutuos #
        if 'Entradas Mútuos' not in df_conciliacao.columns:
            df_conciliacao['Entradas Mútuos'] = somar_por_data(
                df_mutuos_filtrada[df_mutuos_filtrada['ID_Casa_Entrada'] == id_casa], 
                "Data_Mutuo", "Valor", datas
            )

        # Desbloqueios Judiciais #
        if 'Desbloqueios Judiciais' not in df_conciliacao.columns:
            df_conciliacao['Desbloqueios Judiciais'] = somar_por_data(
                df_bloqueios_judiciais_filtrada[df_bloqueios_judiciais_filtrada['Valor'] > 0],
                "Data_Transacao", "Valor", datas
            )

        # Extrato Bancário (Crédito) #
        if 'Extrato Bancário (Crédito)' not in df_conciliacao.columns:
            df_filtrado = df_extratos_bancarios_filtrada.copy()
            df_filtrado['Data_Somente'] = pd.to_datetime(df_filtrado['Data_Transacao']).dt.date

            df_conciliacao['Extrato Bancário (Crédito)'] = somar_por_data(
                df_filtrado[df_filtrado['Tipo_Credito_Debito'] == "CREDITO"],
                "Data_Somente",  # ainda usamos a coluna original com hora para somar por data
                "Valor", datas
            )
        
        # Diferenças (Contas a Receber) #
        if 'Diferenças (Contas a Receber)' not in df_conciliacao.columns:
            df_conciliacao['Diferenças (Contas a Receber)'] = calcula_diferencas(
                df_conciliacao, "Extrato Bancário (Crédito)", ['Extrato Zig (Saques)', 'Faturam dinheiro', 'Receitas Extraordinárias', 'Eventos', 'Entradas Mútuos', 'Desbloqueios Judiciais']
            )

        # Custos sem parcelamento #
        if 'Custos sem Parcelamento' not in df_conciliacao.columns:
            df_conciliacao['Custos sem Parcelamento'] = somar_por_data(
                df_custos_blueme_sem_parcelam_filtrada, "Realizacao_Pgto", "Valor", datas
            ) * (-1)

        # Custos com parcelamento #
        if 'Custos com Parcelamento' not in df_conciliacao.columns:
            df_conciliacao['Custos com Parcelamento'] = somar_por_data(
                df_custos_blueme_com_parcelam_filtrada, "Realiz_Parcela", "Valor_Parcela", datas
            ) * (-1)

        # Saidas Mutuos #
        if 'Saídas Mútuos' not in df_conciliacao.columns:
            df_conciliacao['Saídas Mútuos'] = somar_por_data(
                df_mutuos_filtrada[df_mutuos_filtrada['ID_Casa_Saida'] == id_casa],
                "Data_Mutuo", "Valor", datas
            ) * (-1)

        # Bloqueios Judiciais #
        if 'Bloqueios Judiciais' not in df_conciliacao.columns:
            df_conciliacao['Bloqueios Judiciais'] = somar_por_data(
                df_bloqueios_judiciais_filtrada[df_bloqueios_judiciais_filtrada['Valor'] < 0],
                "Data_Transacao", "Valor", datas
            )

        # Extrato Bancário (Débito) #
        if 'Extrato Bancário (Débito)' not in df_conciliacao.columns:
            df_filtrado = df_extratos_bancarios_filtrada.copy()
            df_filtrado['Data_Transacao'] = pd.to_datetime(df_filtrado['Data_Transacao']).dt.date

            df_conciliacao['Extrato Bancário (Débito)'] = somar_por_data(
                df_filtrado[df_filtrado['Tipo_Credito_Debito'] == "DEBITO"],
                "Data_Transacao", "Valor", datas
            )

        # Diferenças (Contas a pagar) #
        if 'Diferenças (Contas a Pagar)' not in df_conciliacao.columns:
            df_conciliacao['Diferenças (Contas a Pagar)'] = calcula_diferencas(
                df_conciliacao, "Extrato Bancário (Débito)", ['Custos sem Parcelamento', 'Custos com Parcelamento', 'Saídas Mútuos', 'Bloqueios Judiciais']
            )

        # Ajustes #
        if 'Ajustes Conciliação' not in df_conciliacao.columns:
            df_conciliacao['Ajustes Conciliação'] = somar_por_data(
                df_ajustes_conciliacao_filtrada, "Data_Ajuste", "Valor", datas
            )

        # Conciliação # 
        if 'Conciliação' not in df_conciliacao.columns:
            df_conciliacao['Conciliação'] = df_conciliacao['Diferenças (Contas a Pagar)'] + df_conciliacao['Diferenças (Contas a Receber)'] - df_conciliacao['Ajustes Conciliação']
            
            # Garante que é float
            df_conciliacao['Conciliação'] = pd.to_numeric(df_conciliacao['Conciliação'], errors='coerce')

            # Zera valores muito pequenos 
            df_conciliacao['Conciliação'] = df_conciliacao['Conciliação'].apply(lambda x: 0.0 if abs(x) < 0.005 else x)


        # Copia para formatação brasileira de colunas numéricas
        df_formatado = df_conciliacao.copy()

        # Aplica formatação brasileira em colunas numéricas
        for col in df_formatado.select_dtypes(include='number').columns:
            df_formatado[col] = df_formatado[col].apply(format_brazilian)

        # Aplica formatação brasileira em colunas de data
        for col in df_formatado.select_dtypes(include='datetime').columns:
            df_formatado[col] = pd.to_datetime(df_formatado[col]).dt.strftime('%d-%m-%Y')

        # Estiliza linhas não conciliadas e exibe df de conciliação
        df_styled = df_formatado.style.apply(colorir_conciliacao, axis=1)
        st.dataframe(df_styled, width='stretch', hide_index=True)
        exibir_legenda("conciliacao")
        
        st.divider()

        ## Exportando em Excel
        excel_filename = 'Conciliacao_FB.xlsx'
        
        if casa != 'All bar':
            if st.button('Atualizar Planilha Excel'):
                sheet_name_zig = 'df_extrato_zig'
                export_to_excel(df_extrato_zig_filtrada, sheet_name_zig, excel_filename)

                sheet_name_zig = 'df_zig_faturam'
                export_to_excel(df_zig_faturam_filtrada, sheet_name_zig, excel_filename)  

                sheet_name_view_parc_agrup = 'view_parc_agrup'
                export_to_excel(df_parc_receit_extr_filtrada, sheet_name_view_parc_agrup, excel_filename)

                sheet_name_eventos = 'df_eventos'
                export_to_excel(df_eventos_filtrada, sheet_name_eventos, excel_filename)

                sheet_name_custos_blueme_sem_parcelamento = 'df_blueme_sem_parcelamento'
                export_to_excel(df_custos_blueme_sem_parcelam_filtrada, sheet_name_custos_blueme_sem_parcelamento, excel_filename)

                sheet_name_custos_blueme_com_parcelamento = 'df_blueme_com_parcelamento'
                export_to_excel(df_custos_blueme_com_parcelam_filtrada, sheet_name_custos_blueme_com_parcelamento, excel_filename)

                sheet_name_extratos = 'df_extratos'
                export_to_excel(df_extratos_bancarios_filtrada, sheet_name_extratos, excel_filename)

                df_mutuos_filtrada['Valor_Entrada'] = df_mutuos_filtrada.apply(lambda row: row['Valor'] if row['ID_Casa_Entrada'] == id_casa else 0, axis=1)
                df_mutuos_filtrada['Valor_Saida'] = df_mutuos_filtrada.apply(lambda row: row['Valor'] if row['ID_Casa_Saida'] == id_casa else 0, axis=1)
                df_mutuos_filtrada = df_mutuos_filtrada.drop('Valor', axis=1)
                sheet_name_mutuos = 'df_mutuos'
                export_to_excel(df_mutuos_filtrada, sheet_name_mutuos, excel_filename)

                sheet_name_tesouraria = 'df_tesouraria_trans'
                export_to_excel(df_tesouraria_filtrada, sheet_name_tesouraria, excel_filename)

                sheet_name_ajustes_conciliacao = 'df_ajustes_conciliaco'
                export_to_excel(df_ajustes_conciliacao_filtrada, sheet_name_ajustes_conciliacao, excel_filename)
                
                sheet_name_bloqueios_judiciais = 'df_bloqueios_judiciais'
                export_to_excel(df_bloqueios_judiciais_filtrada, sheet_name_bloqueios_judiciais, excel_filename)  

                st.success('Arquivo atualizado com sucesso!')


            # Botão de Download Direto
            if os.path.exists(excel_filename):
                with open(excel_filename, "rb") as file:
                    file_content = file.read()
                    st.download_button(
                    label="Baixar Excel",
                    data=file_content,
                    file_name=f"Conciliacao_FB - {casa}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif tab == 'Contas a Pagar':
        st.markdown(f":material/arrow_downward: **Contas Bancárias - {casa}**")
        st.write("")
        df_extratos_bancarios_filtrada = df_extratos_bancarios_filtrada[df_extratos_bancarios_filtrada['Tipo_Credito_Debito'] == 'DEBITO']
        df_bloqueios_judiciais_filtrada = df_bloqueios_judiciais_filtrada[df_bloqueios_judiciais_filtrada['Valor'] < 0]
        df_saidas_mutuos_filtrada = df_mutuos_filtrada[df_mutuos_filtrada['Casa_Saida'] == casa]

        cria_tabs_contas(
            df_contas, 
            id_casa, 
            df_custos_blueme_sem_parcelam_filtrada, df_custos_blueme_sem_parcelam_formatada, 
            df_custos_blueme_com_parcelam_filtrada, df_custos_blueme_com_parcelam_formatada, 
            df_saidas_mutuos_filtrada, df_mutuos_formatada, 
            df_bloqueios_judiciais_filtrada,
            df_extratos_bancarios_filtrada, df_extratos_bancarios_formatada)

    elif tab == "Contas a Receber":
        st.warning("A fazer")

