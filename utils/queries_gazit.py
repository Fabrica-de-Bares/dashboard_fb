import pandas as pd
from utils.functions.general_functions import dataframe_query

def GET_FATURAMENTO_NOTIE(data_inicio, data_fim):
    return dataframe_query(f'''
        SELECT
            tiv.TRANSACTION_ID 'ID Transação',
            tiv.PRODUCT_SKU AS 'SKU',
            tiv.TRANSACTION_DATE AS 'Data',
            tiv.UNIT_VALUE AS 'Preço',
            tiv.COUNT AS 'Quantidade',
            tiv.DISCOUNT_VALUE AS 'Desconto',
            (tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE AS 'Valor Total'
        FROM T_ITENS_VENDIDOS tiv
            LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
            LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID AND tivc2.ID NOT IN (102, 105, 104)
            INNER JOIN T_EMPRESAS te ON te.ID_ZIGPAY = tiv.LOJA_ID
        WHERE te.ID IN (162, 161, 179)
            AND tiv.EVENT_DATE >= '{data_inicio}'
            AND tiv.EVENT_DATE <= '{data_fim}'
            AND PRODUCT_SKU <> '9999999999997'
    ''')