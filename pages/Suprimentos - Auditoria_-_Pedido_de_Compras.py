import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico_fichas_tecnicas import *
from utils.queries_compras import *
from datetime import date, datetime, timedelta

st.set_page_config(
    page_icon="🛒",
    page_title="Auditoria - Pedido de Compras",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

def main():
    
    # Sidebar
    config_sidebar()
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title(":shopping_cart: Auditoria - Pedido de Compras")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    st.divider()
    
    # Seletores
    periodo = input_periodo_datas(key='data_inicio')
    data_inicio = periodo[0]
    data_fim = periodo[1]
    
    # Validação de data
    if data_inicio > data_fim:
        st.warning('📅 Data Inicio deve ser menor que Data Final')
    else:
        # Puxando a base de empresas
        companies_ = companies(data_inicio, data_fim)
        # Filtro de Casas
        df_companies_selected = input_multiselecao_casas(lista_casas_retirar=[], key='casas_pedido_compras')
        companies_selected = df_companies_selected['Casa'].to_list()
        # Caso nenhum esteja selecionado mostra todos
        if not companies_selected:
            st.warning('Nenhuma casa selecionada')
            st.stop()

        with st.expander('Compras Sem Pedido', expanded=True):
            st.warning('Não devem ocorrer')
            st.markdown('---')

            # Puxando a base de Compras Sem Pedido
            purchasesWithoutOrders = purchases_without_orders(data_inicio, data_fim)
            purchasesWithoutOrders = purchasesWithoutOrders[purchasesWithoutOrders['Casa'].isin(companies_selected)]

            # Agrupar e somar (antes de formatar!)
            purchasesWithoutOrders_grouped = (
                purchasesWithoutOrders.groupby('Casa')
                .agg(
                    Valor_Original=('Valor Original', 'sum'),
                    Valor_Liquido=('Valor Liquido', 'sum'),
                    Quantidade_Despesas=('Valor Original', 'count')
                )
                .reset_index()
            )
            purchasesWithoutOrders_grouped.rename(
                columns={
                    'Valor_Original': 'Valor Original',
                    'Valor_Liquido': 'Valor Liquido',
                    'Quantidade_Despesas': 'Quantidade Despesas'
                },
                inplace=True
            )
            # Criar coluna de Percentual
            purchasesWithoutOrders_grouped['Percentual'] = (
                purchasesWithoutOrders_grouped['Valor Original'] / purchasesWithoutOrders_grouped['Valor Original'].sum() * 100
            ).round(1)

            purchasesWithoutOrders_grouped = function_format_number_columns(
                purchasesWithoutOrders_grouped,
                columns_money=['Valor Original', 'Valor Liquido']
            )

            st.markdown('### Compras Sem Pedido')
            # Exibir com as colunas configuradas
            st.dataframe(
                purchasesWithoutOrders_grouped[['Casa', 'Quantidade Despesas', 'Valor Original', 'Valor Liquido', 'Percentual']],
                column_config={
                    "Quantidade Despesas": st.column_config.TextColumn("Qtd. Despesas"),
                    "Valor Original": st.column_config.TextColumn("Valor Original (R$)"),
                    "Valor Liquido": st.column_config.TextColumn("Valor Líquido (R$)"),
                    "Percentual": st.column_config.ProgressColumn(
                        "Percentual do Total",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    )
                },
                hide_index=True,
                width='stretch'
            )

            purchasesWithoutOrders = purchasesWithoutOrders.sort_values(
                by=['Casa', 'Valor Original'],
                ascending=[True, False]
            )
            purchasesWithoutOrders = function_format_number_columns(
                purchasesWithoutOrders,
                columns_money=['Valor Original', 'Valor Liquido']
            )
            st.markdown('### Base Sem Pedido Completa')
            dataframe_aggrid(purchasesWithoutOrders, 'Base Sem Pedido Completa')
            function_copy_dataframe_as_tsv(purchasesWithoutOrders)

        st.markdown('---')

        with st.expander('Distorções (Valor da Despesa - Valor dos Insumos)', expanded=True):
            st.markdown('---')
            
            # Puxando a base de insumos nas despesas
            bluemeWithOrder = blueme_with_order(data_inicio, data_fim)
            bluemeWithOrder = bluemeWithOrder[bluemeWithOrder['Casa'].isin(companies_selected)]

            # Calcular divergência
            bluemeWithOrder['Divergencia'] = bluemeWithOrder['Valor Original'] - bluemeWithOrder['Valor Cotação']
            bluemeWithOrder = bluemeWithOrder[bluemeWithOrder['Divergencia'] != 0]
            
            # Ordenar por Casa (ascendente) e Divergência (decrescente)
            bluemeWithOrder = bluemeWithOrder.sort_values(
                by=['Casa', 'Divergencia'],
                ascending=[True, False]
            )                   

            if bluemeWithOrder.empty:
                st.warning("Nenhum dado com distorção encontrado.")
            else:
                col1, col2 = st.columns([3, 1.5]) 
                with col1:
                    assocExpenseItems = assoc_expense_items(data_inicio, data_fim)
                    bluemeWithOrder['Data Competencia'] = bluemeWithOrder['Data Competencia'].astype(str)
                    bluemeWithOrder['Data Vencimento'] = bluemeWithOrder['Data Vencimento'].astype(str)
                    bluemeWithOrder_copy = bluemeWithOrder.copy()
                    assocExpenseItems['Data Competencia'] = assocExpenseItems['Data Competencia'].astype(str)
                    bluemeWithOrder = function_format_number_columns(
                        bluemeWithOrder,
                        columns_money=['Divergencia', 'Valor Original', 'Valor Liquido', 'Valor Cotação']
                    )
                    assocExpenseItems = function_format_number_columns(
                        assocExpenseItems,
                        columns_money=['Valor Unitario', 'Valor Total'],
                        columns_number=['Quantidade Insumo']
                    )
                    st.markdown('### Detalhamento das Distorções')
                    dataframe_aggrid(
                        bluemeWithOrder,
                        'Detalhamento das Distorções',
                        df_details=assocExpenseItems,
                        coluns_merge_details='ID Despesa',
                        coluns_name_details='Casa',
                        key="grid_distorcoes"
                    )
                
                with col2:
                    # Agrupar por casa e calcular quantidade e valor total da divergência
                    bluemeWithOrder_divergence = (
                        bluemeWithOrder_copy.groupby('Casa')
                        .agg(
                            Quantidade=('Divergencia', 'count'),
                            Valor_Total_Distorcido=('Divergencia', 'sum')
                        )
                        .reset_index()
                        .sort_values(by='Valor_Total_Distorcido', ascending=False)
                    )
                    bluemeWithOrder_divergence.rename(
                        columns={'Valor_Total_Distorcido': 'Valor Total Distorcido'},
                        inplace=True
                    )
                    bluemeWithOrder_divergence = function_format_number_columns(
                        bluemeWithOrder_divergence,
                        columns_money=['Valor Total Distorcido']
                    )

                    bluemeWithOrder_style = bluemeWithOrder_divergence.style.map(
                        function_highlight_value,
                        ['Valor Total Distorcido']
                    )
                    st.markdown('### Resumo por Casa')
                    st.dataframe(bluemeWithOrder_style, hide_index=True)

if __name__ == '__main__':
    main()
