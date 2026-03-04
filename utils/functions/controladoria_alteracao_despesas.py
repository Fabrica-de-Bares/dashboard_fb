import pandas as pd
import streamlit as st


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


def despesas_alteradas_por_campo(df_log_despesas, colunas_comparar):
    ids_com_alteracao = (
        df_log_despesas
            .groupby('ID Despesa')[colunas_comparar]
            .nunique()
            .gt(1)        
            .any(axis=1) 
    )

    # Lista de despesas com alteração nos campos definidos
    ids_com_alteracao = ids_com_alteracao[ids_com_alteracao].index
    df_alteracao = df_log_despesas[df_log_despesas['ID Despesa'].isin(ids_com_alteracao)].copy()

    # Remove logs sem alteração em campos relevantes
    colunas_verificar_duplicatas = [col for col in df_alteracao if (col not in ['Data Alteração', 'Nome Usuário', 'Email Usuário'])]
    df_alteracao = df_alteracao.drop_duplicates(subset=colunas_verificar_duplicatas, keep='first')
    df_alteracao = df_alteracao[['Casa', 'ID Despesa', 'Data Alteração', 'Nome Usuário', 'Email Usuário', 'Data Competência', 'Data Vencimento', 'Valor Original', 'Valor Liquido', 'Status Pagamento', 'Fornecedor', 'Class. Cont. 1', 'Class. Cont. 2']]

    return df_alteracao


def exibe_contagem_ids_alterados(df):
    df_contador = df.groupby('ID Despesa').size().reset_index(name='Contagem')
    contagem_ids = len(df_contador['ID Despesa'].tolist())
    if contagem_ids == 0:
        st.success('Sem despesas alteradas!')
    else:
        st.write(f'**Total de despesas com alteração:** {contagem_ids}')


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