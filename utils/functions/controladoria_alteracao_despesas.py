import pandas as pd
import streamlit as st
from io import BytesIO


def destacar_alteracoes(df, colunas_comparar):
    colunas_ignorar = [ # as alterações nesses campos não precisam ser destacadas
        'Data Alteração',
        'Nome Usuário',
        'Email Usuário'
    ]
    def highlight_group(group):
        referencia = group.iloc[0] # primeira despesa criada
        estilos = pd.DataFrame(
            '',
            index=group.index,
            columns=group.columns
        )
        for i, row in group.iterrows():
            if i == group.index[0]:  # primeira linha → verde
                estilos.loc[i, :] = 'background-color: rgba(33,195,84,0.1)'
                continue
            for col in colunas_comparar: # comparar colunas desejadas
                if col in colunas_ignorar:
                    continue
                if row[col] != referencia[col]:
                    estilos.loc[i, col] = 'background-color: rgba(255,255,224)' # amarelo
        return estilos
    return df.style.apply(lambda _: df.groupby('ID Despesa', group_keys=False).apply(highlight_group), axis=None)


def filtragem_inicial_despesas(df_log_despesas_inicial, id_casa):
    df_log_despesas_filtrado = df_log_despesas_inicial[df_log_despesas_inicial['ID Casa'] == id_casa].copy() 

    df_log_despesas_filtrado.sort_values(by=['ID Despesa', 'Data Alteração'], inplace=True)

    # Define tipos de dados do dataframe de log de despesas alteradas
    tipos_de_dados_despesas = {
        'ID Casa': int,
        'Valor Original': float,
        'Valor Liquido': float,  
    }
    df_log_despesas_filtrado = df_log_despesas_filtrado.astype(tipos_de_dados_despesas, errors='ignore')
    df_log_despesas_filtrado['Data Competência'] = pd.to_datetime(df_log_despesas_filtrado['Data Competência'], errors='coerce')
    df_log_despesas_filtrado['Data Vencimento'] = pd.to_datetime(df_log_despesas_filtrado['Data Vencimento'], errors='coerce')

    return df_log_despesas_filtrado


def filtragem_classificacao_contabil(df_log_despesas, lista_class_cont_1_selecionadas, lista_class_cont_2_selecionadas):
    df_log_despesas_filtrado = df_log_despesas.copy()
    if lista_class_cont_1_selecionadas or lista_class_cont_2_selecionadas:
        df_log_despesas_alteradas = df_log_despesas_filtrado[ # Despesas alteradas para a class. cont. selecionada
            (df_log_despesas_filtrado['Class. Cont. 1'].isin(lista_class_cont_1_selecionadas)) |
            (df_log_despesas_filtrado['Class. Cont. 2'].isin(lista_class_cont_2_selecionadas))
        ].copy()
        lista_ids_alteracao_classif_selecionada = df_log_despesas_alteradas['ID Despesa'].tolist()
        df_log_despesas_filtrado = df_log_despesas_filtrado[df_log_despesas_filtrado['ID Despesa'].isin(lista_ids_alteracao_classif_selecionada)].copy()

    return df_log_despesas_filtrado


def filtragem_mes_ano_competencia(df, mes_competencia_selecionado, ano_competencia_selecionado, tipo_alteracao, data_fechamento):
    df_filtrado = df.copy()
    df_filtrado['Data Competência'] = pd.to_datetime(df_filtrado['Data Competência'], errors='coerce')
    df_filtrado['Data Vencimento'] = pd.to_datetime(df_filtrado['Data Vencimento'], errors='coerce')
    
    if tipo_alteracao == 'Criadas':
        df_filtrado = df_filtrado[
            (df_filtrado['Data Competência'].dt.month == int(mes_competencia_selecionado)) &
            (df_filtrado['Data Competência'].dt.year == ano_competencia_selecionado)
        ].copy()

    elif tipo_alteracao == 'Ajustes Fechamento':
        data_inicio_periodo_ajuste = pd.Timestamp(day=1, month=data_fechamento.month, year=data_fechamento.year).date()
        df_despesas_alteradas = df_filtrado[ # Despesas com data de competência selecionada
            (df_filtrado['Data Competência'].dt.month == mes_competencia_selecionado) &
            (df_filtrado['Data Competência'].dt.year == ano_competencia_selecionado)
        ].copy()
        lista_ids_alteracao = df_despesas_alteradas['ID Despesa'].tolist()
        df_filtrado = df_filtrado[df_filtrado['ID Despesa'].isin(lista_ids_alteracao)].copy()

        df_despesas_alteracao = df_filtrado[ # Despesas com data de alteração dentro do período de ajuste
            (df_filtrado['Data Alteração'].dt.date >= data_inicio_periodo_ajuste) &
            (df_filtrado['Data Alteração'].dt.date <= data_fechamento)
        ].copy()
        lista_ids_alteracao = df_despesas_alteracao['ID Despesa'].tolist()
        df_filtrado = df_filtrado[df_filtrado['ID Despesa'].isin(lista_ids_alteracao)].copy()

    else:
        df_despesas_alteradas = df_filtrado[ # Despesas com data de competência selecionada
            (df_filtrado['Data Competência'].dt.month == mes_competencia_selecionado) &
            (df_filtrado['Data Competência'].dt.year == ano_competencia_selecionado)
        ].copy()
        lista_ids_alteracao_mes_selecionado = df_despesas_alteradas['ID Despesa'].tolist()
        df_filtrado = df_filtrado[df_filtrado['ID Despesa'].isin(lista_ids_alteracao_mes_selecionado)].copy()

        df_despesas_alteracao = df_filtrado[ # Despesas com data de alteração > data de fechamento
            df_filtrado['Data Alteração'].dt.date > data_fechamento.date()
        ].copy()
        lista_ids_alteracao = df_despesas_alteracao['ID Despesa'].tolist()
        df_filtrado = df_filtrado[df_filtrado['ID Despesa'].isin(lista_ids_alteracao)].copy()

    return df_filtrado


def busca_despesas_criadas(df_log_despesas_inicial, id_casa, data_fechamento):
    # Cria df com despesas criadas depois da data limite
    df_log_despesas_criadas = df_log_despesas_inicial[
        df_log_despesas_inicial.groupby('ID Despesa')['Data Alteração']
        .transform('min').dt.date > data_fechamento.date() # data do primeiro log é maior que a data de fechamento
    ].copy()
    
    df_log_despesas_criadas = df_log_despesas_criadas[(df_log_despesas_criadas['Bit Cancelada'] == 0) & (df_log_despesas_criadas['ID Casa'] == id_casa)].copy()
    df_log_despesas_criadas.drop_duplicates(subset=['ID Despesa'], keep='first', inplace=True) # mantém apenas o primeiro registro da despesa (criação)
    
    return df_log_despesas_criadas


def despesas_alteradas_por_campo(df_log_despesas, colunas_comparar):
    df_alteracao = df_log_despesas.copy()

    # Seleciona e ordena as colunas para melhor visualização
    if colunas_comparar == ['Data Competência'] or colunas_comparar == ['Data Vencimento'] or colunas_comparar == ['Valor Original', 'Valor Liquido']:
        df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Real/Provisão', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Class. Cont. 1', 'Class. Cont. 2', 'Bit Cancelada']]
    elif colunas_comparar == ['Class. Cont. 1', 'Class. Cont. 2']:
        df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Real/Provisão', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Class. Cont. 1', 'Class. Cont. 2', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Bit Cancelada']]
    # elif colunas_comparar == ['Status Aprovação Operação']: # stand-by
    #     df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Real/Provisão', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Status Aprovação Operação', 'Status Aprovação Diretoria', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Class. Cont. 1', 'Class. Cont. 2', 'Bit Cancelada']]
    elif colunas_comparar == ['Real/Provisão']:
        df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Real/Provisão', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Class. Cont. 1', 'Class. Cont. 2', 'Bit Cancelada']]
    elif colunas_comparar == ['Bit Cancelada']:
        df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Real/Provisão', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Bit Cancelada', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Class. Cont. 1', 'Class. Cont. 2']]
    elif colunas_comparar == ['Casa']:
        df_alteracao = df_alteracao[['ID Casa', 'Casa', 'ID Despesa', 'Real/Provisão', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Class. Cont. 1', 'Class. Cont. 2', 'Bit Cancelada']]

    ids_com_alteracao = (
        df_alteracao
            .groupby('ID Despesa')[colunas_comparar]
            .nunique()
            .gt(1)        
            .any(axis=1) 
    )

    # Lista de despesas com alteração nos campos definidos
    ids_com_alteracao = ids_com_alteracao[ids_com_alteracao].index
    df_alteracao = df_alteracao[df_alteracao['ID Despesa'].isin(ids_com_alteracao)].copy()
    
    # Remove logs sem alteração em campos relevantes
    if 'Status Aprovação Operação' not in colunas_comparar:
        colunas_verificar_duplicatas = [col for col in df_alteracao if (col not in ['Data Alteração', 'Nome Usuário', 'Email Usuário'] and col in colunas_comparar + ['ID Despesa'])]
    else:
        colunas_verificar_duplicatas = [col for col in df_alteracao if (col not in ['Data Alteração', 'Nome Usuário', 'Email Usuário'])]
    
    df_alteracao = df_alteracao.drop_duplicates(subset=colunas_verificar_duplicatas, keep='first') # mantém o primeiro registro da alteração (para ver se ele foi depois do fechamento)
    
    if colunas_comparar != ['Bit Cancelada']: # Não considerar alteração de despesas canceladas
        ids_com_cancelamento = ( 
            df_alteracao.groupby('ID Despesa')['Bit Cancelada']
            .nunique()
            .loc[lambda x: x > 1]
            .index
        )
        df_alteracao = df_alteracao[~df_alteracao['ID Despesa'].isin(ids_com_cancelamento)].copy()
    #     df_alteracao.drop(columns=['Bit Cancelada'], inplace=True)
    
    return df_alteracao


def exibe_contagem_despesas(df, exibe_res=True):
    lista_ids_despesas = df['ID Despesa'].unique().tolist()
    contagem_ids = len(lista_ids_despesas)

    if exibe_res:
        if contagem_ids == 0:
            st.success('Sem registros!')
        else:
            st.write(f'**Quantidade:** {contagem_ids}')
    return contagem_ids


def exibe_legenda():
    st.markdown(
        f"""
        <div style="display: flex; gap: 2em; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; background-color: rgba(33,195,84,0.1); border: 1px solid #ccc; margin-right: 10px;"></div>
                <span style="font-size: 14px">Primeira despesa criada (referência)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 15px; height: 15px; background-color: rgba(255,255,224); border: 1px solid #ccc; margin-right: 10px;"></div>
                <span style="font-size: 14px">Campos alterados em relação à despesa de referência</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")


# Função que gera excel com cada df em uma aba
def gerar_excel(dfs):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nome_aba, df in dfs.items():
            df.to_excel(writer, sheet_name=nome_aba[:31], index=False)

    output.seek(0)
    return output


def button_download(dfs_exportar):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nome_aba, df in dfs_exportar.items():
            df.to_excel(writer, sheet_name=nome_aba[:31], index=False)
    output.seek(0)

    st.download_button(
        label=":material/download: Download Excel",
        data=output,
        file_name=f"Despesas Alteradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width=200,
        type="primary",
        use_container_width=True
    )
