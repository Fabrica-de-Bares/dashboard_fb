import pandas as pd
import streamlit as st
import io
from utils.functions.date_functions import *
from utils.queries_eventos import *
from utils.queries_produto import *
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid import GridUpdateMode, JsCode, StAggridTheme
from streamlit_echarts import st_echarts
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utils.queries_cmv import *

def input_selecao_casas(lista_casas_retirar, key, adicionar_delivery=None):
    # Mostra apenas as casas que o usuário tem acesso
    df_permissao_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
    
    # Remove casas da lista_casas_retirar
    df_permissao_casas = df_permissao_casas[~df_permissao_casas["Loja"].isin(lista_casas_retirar)].sort_values(by="Loja").reset_index(drop=True)

    lista_ids_casas_permissao = df_permissao_casas["ID Loja"].unique().tolist()
    
    # Adiciona casas de Delivery nas abas que pedirem
    if adicionar_delivery == True:
        df_casas_delivery = get_casas_delivery()
        if 114 in lista_ids_casas_permissao: # BBC
            df_permissao_casas = pd.concat([df_permissao_casas, df_casas_delivery[df_casas_delivery['ID Loja'] == 118]])
        if 148 in lista_ids_casas_permissao: # BBG
            df_permissao_casas = pd.concat([df_permissao_casas, df_casas_delivery[df_casas_delivery['ID Loja'] == 169]])
        if 116 in lista_ids_casas_permissao: # Bar Léo
            df_permissao_casas = pd.concat([df_permissao_casas, df_casas_delivery[df_casas_delivery['ID Loja'] == 103]])
        if 104 in lista_ids_casas_permissao: # Orfeu
            df_permissao_casas = pd.concat([df_permissao_casas, df_casas_delivery[df_casas_delivery['ID Loja'] == 112]])
        if 105 in lista_ids_casas_permissao: # Jacaré
            df_permissao_casas = pd.concat([df_permissao_casas, df_casas_delivery[df_casas_delivery['ID Loja'] == 139]])
    
    lista_casas_validas = df_permissao_casas['Loja'].unique().tolist()
    # Adiciona opção Todas as casas
    if 'Todas as Casas' not in lista_casas_retirar:
        lista_casas_validas.insert(0, "Todas as Casas")

    lista_casas_validas.sort()
    casa = st.selectbox("Casa", lista_casas_validas, key=key)

    if casa == "Todas as Casas":
        id_casa = -1  # Valor padrão para "Todas as Casas"
        casa = "Todas as Casas"
        id_zigpay = -1
    else:
        # Obtendo o ID da casa selecionada
        id_casa = df_permissao_casas[df_permissao_casas["Loja"] == casa]["ID Loja"].values[0]
        # Obtendo o ID da Zigpay correspondente ao ID da casa
        id_zigpay = df_permissao_casas[df_permissao_casas["Loja"] == casa]["ID Zigpay"].values[0]

    return id_casa, casa, id_zigpay

def input_selecao_casas_agregadas(lista_casas_retirar, key):

    # Mostra apenas as casas que o usuário tem acesso
    df_permissao_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja", "Loja", 'ID Zigpay'])
    
    # Remove casas da lista_casas_retirar
    df_permissao_casas = df_permissao_casas[~df_permissao_casas["Loja"].isin(lista_casas_retirar)].sort_values(by="Loja").reset_index(drop=True)
    lista_casas_validas = df_permissao_casas["Loja"].to_list()
    lista_ids_casas_validas = df_permissao_casas["ID Loja"].to_list()

    blue_note_ids = [110, 131, 178]
    the_cavern_ids = [176, 177]
    girondino_ids = [156, 160]

    # Se algum Blue Note está na permissão, adiciona Blue Note - Agregado
    if any(num in blue_note_ids for num in lista_ids_casas_validas):
        if 'Blue Note - Agregado' not in lista_casas_retirar:
            lista_casas_validas.insert(0, "Blue Note - Agregado")
            lista_casas_validas.remove("Blue Note - São Paulo")
            lista_casas_validas.remove("Blue Note SP (Novo)")
            lista_casas_validas.remove("Blue Note SP (Sala 2)")

    # Se algum The Cavern está na permissão, adiciona The Cavern - Agregado
    if any(num in the_cavern_ids for num in lista_ids_casas_validas):
        if 'The Cavern - Agregado' not in lista_casas_retirar:
            lista_casas_validas.insert(0, "The Cavern - Agregado")
            lista_casas_validas.remove("The Cavern")
            lista_casas_validas.remove("The Cavern - Almoço")
    
    # Se algum Girondino está na permissão, adiciona Girondino - Agregado
    if any(num in girondino_ids for num in lista_ids_casas_validas):
        if 'Girondino - Agregado' not in lista_casas_retirar:
            lista_casas_validas.insert(0, "Girondino - Agregado")
            lista_casas_validas.remove("Girondino")
            lista_casas_validas.remove("Girondino - CCBB")

    lista_casas_validas.sort()

    # Adiciona opção Todas as casas
    if 'Todas as Casas' not in lista_casas_retirar:
        lista_casas_validas.insert(0, "Todas as Casas")

    casa = st.selectbox("Casa", lista_casas_validas, key=key)

    if casa == "Todas as Casas":
        id_casa = -1  # Valor padrão para "Todas as Casas"
        casa = "Todas as Casas"
        id_zigpay = -1
    else:
        # Obtendo o ID da casa agregada
        if casa == "Blue Note - Agregado":
            id_casa = df_permissao_casas[df_permissao_casas["Loja"] == 'Blue Note - São Paulo']["ID Loja"].values[0]
            id_zigpay = df_permissao_casas[df_permissao_casas["Loja"] == 'Blue Note SP (Novo)']["ID Zigpay"].values[0]
        elif casa == "The Cavern - Agregado":
            id_casa = df_permissao_casas[df_permissao_casas["Loja"] == 'The Cavern']["ID Loja"].values[0]
            id_zigpay = df_permissao_casas[df_permissao_casas["Loja"] == 'The Cavern - Almoço']["ID Zigpay"].values[0]
        elif casa == "Girondino - Agregado":
            id_casa = df_permissao_casas[df_permissao_casas["Loja"] == 'Girondino']["ID Loja"].values[0]
            id_zigpay = df_permissao_casas[df_permissao_casas["Loja"] == 'Girondino - CCBB']["ID Zigpay"].values[0]
        # Obtendo o ID de casa não agregada
        else:
            id_casa = df_permissao_casas[df_permissao_casas["Loja"] == casa]["ID Loja"].values[0]
            # Obtendo o ID da Zigpay correspondente ao ID da casa
            id_zigpay = df_permissao_casas[df_permissao_casas["Loja"] == casa]["ID Zigpay"].values[0]

    return id_casa, casa, id_zigpay

def input_multiselecao_casas(lista_casas_retirar, key, adicionar_delivery=None):
    # Dataframe com IDs e nomes das casas
    df_casas = get_casas_validas()
    # Remove casas da lista_casas_retirar
    df_casas = df_casas[~df_casas["Casa"].isin(lista_casas_retirar)].sort_values(by="Casa").reset_index(drop=True)

    # Se o usuário não tem acesso a todas as casas, mostra apenas as casas que ele tem acesso
    df_permissao_casas = pd.DataFrame(st.session_state['casas_permitidas'], columns=["ID Loja"])
    lista_ids_casas_acesso = df_permissao_casas["ID Loja"].to_list()
    
    # Adiciona casas de Delivery nas abas que pedirem
    if adicionar_delivery == True:
        if 105 in lista_ids_casas_acesso: # Jacaré
            lista_ids_casas_acesso.append(139)
        if 114 in lista_ids_casas_acesso: # BBC
            lista_ids_casas_acesso.append(118)
        if 104 in lista_ids_casas_acesso: # Orfeu
            lista_ids_casas_acesso.append(112)
        if 148 in lista_ids_casas_acesso: # BBG
            lista_ids_casas_acesso.append(169)
        if 116 in lista_ids_casas_acesso: # Bar Léo
            lista_ids_casas_acesso.append(103)
    
    df_casas = df_casas[df_casas["ID_Casa"].isin(lista_ids_casas_acesso)].sort_values(by="Casa").reset_index(drop=True)
    lista_casas_validas = df_casas["Casa"].to_list()

    # Adiciona opção Todas as casas
    if 'Todas as Casas' not in lista_casas_retirar:
        lista_casas_validas.insert(0, "Todas as Casas")

    lista_casas = st.multiselect("Casa", lista_casas_validas, key=key, default=lista_casas_validas[0])
    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    df_validas = df_validas[df_validas["Casa"].isin(lista_casas)].sort_values(by="Casa").reset_index(drop=True)

    if lista_casas and lista_casas[0] == 'Todas as Casas':
        df_result = df_casas
    else:
        df_result = df_casas.merge(df_validas, on="Casa", how="inner")
    return df_result


def input_selecao_casas_analise_produtos(lista_casas_retirar, key):
    # Dataframe com IDs e nomes das casas
    df_casas = GET_CASAS_VALIDAS_ANALISE_PRODUTOS()
    # Remove casas da lista_casas_retirar
    df_casas = df_casas[~df_casas["Casa"].isin(lista_casas_retirar)].sort_values(by="Casa").reset_index(drop=True)
    lista_casas_validas = df_casas["Casa"].to_list()

    # Se o usuário não tem acesso a todas as casas, mostra apenas as casas que ele tem acesso
    user_login = st.session_state['user_login']
    lista_ids_casas_acesso = st.secrets["user_access"][user_login]
    if -1 not in lista_ids_casas_acesso:
        df_casas = df_casas[df_casas["ID_Casa"].isin(lista_ids_casas_acesso)].sort_values(by="Casa").reset_index(drop=True)
        lista_casas_validas = df_casas["Casa"].to_list()

    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    casa = st.selectbox("Casa", lista_casas_validas, key=key)

    if casa == "Todas as Casas":
        id_casa = -1  # Valor padrão para "Todas as Casas"
        casa = "Todas as Casas"
        id_zigpay = -1
    else:
        df = df_casas.merge(df_validas, on="Casa", how="inner")
        # Definindo um dicionário para mapear nomes de casas a IDs de casas
        mapeamento_ids = dict(zip(df["Casa"], df["ID_Casa"]))
        # Definindo um dicionário para mapear IDs de casas a IDs da Zigpay
        mapeamento_zigpay = dict(zip(df["Casa"], df["ID_Zigpay"]))

        # Obtendo o ID da casa selecionada
        id_casa = mapeamento_ids[casa]
        # Obtendo o ID da Zigpay correspondente ao ID da casa
        id_zigpay = mapeamento_zigpay[casa]

    return id_casa, casa, id_zigpay


def input_periodo_datas(key, label='Período'):
    today = get_today()
    jan_this_year = get_jan_this_year(today)
    first_day_this_month_this_year = get_first_day_this_month_this_year(today)
    last_day_this_month_this_year = get_last_day_this_month_this_year(today)

    # Inicializa o input com o mês atual
    date_input = st.date_input(label,
                            value=(first_day_this_month_this_year, last_day_this_month_this_year),
                            format="DD/MM/YYYY",
                            key=key
                            )
    return date_input


def seletor_mes(label, key):
  # Dicionário para mapear os meses
  meses = {
      "Janeiro": "01",
      "Fevereiro": "02",
      "Março": "03",
      "Abril": "04",
      "Maio": "05",
      "Junho": "06",
      "Julho": "07",
      "Agosto": "08",
      "Setembro": "09",
      "Outubro": "10",
      "Novembro": "11",
      "Dezembro": "12"
  }

  # Obter o mês atual para defini-lo como padrão
  mes_atual_num = get_today().month
  nomes_meses = list(meses.keys())
  mes_atual_nome = nomes_meses[mes_atual_num - 1]

  # Seletor de mês
  mes = st.selectbox(label, nomes_meses, index=nomes_meses.index(mes_atual_nome), key=key)

  # Obter o mês correspondente ao mês selecionado
  mes_selecionado = meses[mes]

  return mes_selecionado


def seletor_mes_produtos(key, label='Mês', help=None):
    # Dicionário para mapear os meses
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
        "Dezembro": 12,
    }

    # Obter o mês atual para defini-lo como padrão
    mes_atual_num = get_today().month
    nomes_meses = list(meses.keys())
    mes_atual_nome = nomes_meses[mes_atual_num - 1]

    # Seletor de mês
    nome_mes_selecionado = st.selectbox(
        label, nomes_meses, index=nomes_meses.index(mes_atual_nome), key=key, help=help
    )

    # Obter o mês correspondente ao mês selecionado
    num_mes_selecionado = meses[nome_mes_selecionado]

    return nome_mes_selecionado, num_mes_selecionado


def seletor_ano(ano_inicio, ano_fim, key, label='Selecionar Ano', help=None):
   anos = list(range(ano_inicio, ano_fim + 1))
   anos_ordenados = sorted(anos, reverse=True)
   ano_atual = datetime.datetime.now().year 
   index_padrao = anos_ordenados.index(ano_atual)
   ano = st.selectbox(label, anos_ordenados, index=index_padrao,key=key, help=help)
   return ano


def button_download(df, file_name, key):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=f"{file_name}")
    excel_data = output.getvalue()

    st.download_button(
        label=":material/download: Download Excel",
        data=excel_data,
        file_name=f"{file_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
        type="tertiary",
        key=f'{key}'
    )


def seletor_vendedor(label, df_vendedores, key):
    
    lista_vendedores = df_vendedores['ID - Responsavel'].tolist()
    lista_vendedores.insert(0, "Todos os vendedores")

    vendedor = st.selectbox(label, lista_vendedores, key=key)
    if vendedor == "Todos os vendedores":
        id_vendedor = -1  # Valor padrão para "Todos"
        nome_vendedor = "Todos os vendedores"
    else:
        # Extrai o ID do vendedor selecionado
        id_vendedor = int(vendedor.split(" - ")[0])
        nome_vendedor = vendedor.split(" - ")[1]
    return id_vendedor, nome_vendedor


def seletor_vendedor_logado(label, df_vendedores, lista_vendedores_logado, key):

    # Recupera o email do usuário
    user_login = st.session_state["user_login"]

    # Verifica se o usuário tem acesso a todos os vendedores
    if user_login in st.secrets["comissions_total_access"]["users"]:
        lista_vendedores = df_vendedores['ID - Responsavel'].tolist()
        lista_vendedores.insert(0, "Todos os vendedores")
    else:
        # Filtra somente o vendedor logado
        lista_vendedores = lista_vendedores_logado

    # Seletor de vendedor
    vendedor = st.selectbox(label, lista_vendedores, key=key)
    if vendedor == "Todos os vendedores":
        id_vendedor = -1  # Valor padrão para "Todos"
        nome_vendedor = "Todos os vendedores"
    else:
        # Extrai o ID do vendedor selecionado
        if vendedor:
            id_vendedor = int(vendedor.split(" - ")[0])
            nome_vendedor = vendedor.split(" - ")[1]
        else:
            id_vendedor = int(lista_vendedores[0].split(" - ")[0])
            nome_vendedor = lista_vendedores[0].split(" - ")[1]

    return id_vendedor, nome_vendedor

def kpi_card(title, value, background_color="#FFFFFF", title_color="#333", value_color="#000"):
    html = f"""
    <div style="
        background-color: {background_color};
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 10px;
        padding: 16px;
        height: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: none;
        margin: 0px;
        cursor: default;
        transition: none;
    ">
        <div style="font-size: 14px; color: {title_color}; font-weight: normal; margin-bottom: 6px;">
            {title}
        </div>
        <div style="font-size: 24px; color: {value_color}; font-weight: bold;">
            {value}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def kpi_card_cmv_teorico(title, value, background_color="#FFFFFF", title_color="#333", value_color="#000", valor_percentual=None, color_percentual=None):

    if color_percentual:
        if color_percentual == 'verde':
            color_percentual = 'rgb(9, 171, 59)'
            background_color_percentual = 'rgba(9, 171, 59, 0.1)'
        elif color_percentual == 'amarelo':
            color_percentual = 'rgb(255, 165, 0)'
            background_color_percentual = 'rgba(255, 196, 0, 0.15)'
        elif color_percentual == 'vermelho':
            color_percentual = 'rgb(255, 75, 75)'
            background_color_percentual = 'rgba(255, 75, 75, 0.1)'
    else:
        color_percentual = 'rgb(128, 128, 128)'
        background_color_percentual = 'rgba(128, 128, 128, 0.1)'

    if valor_percentual:
        html = f"""
        <div style="
            background-color: {background_color};
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 10px;
            padding: 16px;
            height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: none;
            margin: 0px;
            cursor: default;
            transition: none;
        ">
            <div style="font-size: 14px; color: {title_color}; font-weight: normal; margin-bottom: 4px;">
                {title}
            </div>
            <div style="font-size: 24px; color: {value_color}; font-weight: bold;">
                {value}
            </div>
            <div style="
                background-color: {background_color_percentual};
                color: {color_percentual};
                border-radius: 20px;
                padding: 2px 8px;
                font-size: 18px;
                font-weight: 500;
            ">
                {valor_percentual} %
            </div>
        </div>
        """
    else:
        html = f"""
        <div style="
            background-color: {background_color};
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 10px;
            padding: 16px;
            height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: none;
            margin: 0px;
            cursor: default;
            transition: none;
        ">
            <div style="font-size: 14px; color: {title_color}; font-weight: normal; margin-bottom: 6px;">
                {title}
            </div>
            <div style="font-size: 24px; color: {value_color}; font-weight: bold;">
                {value}
            </div>
        </div>
        """

    st.markdown(html, unsafe_allow_html=True)


def format_numeric_column(df, col):
    if col not in df.columns:
        return df
    
    df = df.copy()

    num_col = f"{col}_NUM"
    
    def parse_br_number(x):
        try:
            # Remove tudo que não é dígito, vírgula ou ponto
            s = str(x).replace("R$", "").replace(" ", "")
            # Substitui vírgula decimal
            if s.count(",") == 1 and s.count(".") == 0:
                s = s.replace(",", ".")
            # Remove pontos de milhar
            elif s.count(".") > 0 and s.count(",") == 1:
                s = s.replace(".", "")
                s = s.replace(",", ".")
            return Decimal(s)
        except (InvalidOperation, ValueError):
            return None
    
    df.loc[:, num_col] = df[col].apply(parse_br_number)
    
    # Formatação BR
    def format_br(x):
        if x is None:
            return ""
        x = x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        s = f"{x:,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    
    df[col] = df[num_col].apply(format_br).astype("string")
    
    return df


def format_percent_column(df, col):
    """Converte coluna percentual com limpeza e formata %."""
    if col not in df.columns:
        return df

    num_col = f"{col}_NUM"
    df[num_col] = (
        df[col].astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("−", "-", regex=False)
        .str.replace("–", "-", regex=False)
        .str.replace(r"[^\d\.\-]", "", regex=True)
    )
    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    # Formatação BR com Decimal
    df[col] = df[num_col].apply(
        lambda x: f"{Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
                  .replace(",", "X").replace(".", ",").replace("X", ".")
        if pd.notnull(x) else ""
    )
    return df


def format_date_column(df, col, fmt="%d/%m/%Y"):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(fmt)
    return df

def format_datetime_column(df, col, fmt="%d/%m/%Y %H:%M:%S"):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(fmt)
    return df


def get_cellstyle_code(style=None):
    """Código JS para colorir valores positivos/negativos."""
    if style == 'monetary inverse':
        return JsCode("""
            function(params) {
                const value = params.data[params.colDef.field + '_NUM'];
                if (value === null || value === undefined || isNaN(value)) return {};
                if (value < 0) return { color: 'green', fontWeight: 'bold' };
                if (value > 0) return { color: 'red', fontWeight: 'bold' };
                return {};
            }
        """)
    else:               
        return JsCode("""
            function(params) {
                const value = params.data[params.colDef.field + '_NUM'];
                if (value === null || value === undefined || isNaN(value)) return {};
                if (value < 0) return { color: 'red', fontWeight: 'bold' };
                if (value > 0) return { color: 'green', fontWeight: 'bold' };
                return {};
            }
        """)


def apply_master_detail(df, df_details, coluns_merge_details, coluns_name_details,
                        num_columns, percent_columns, cellstyle_code, grid_options):
    """Configuração de MasterDetail no AgGrid."""
    df["detail"] = df[coluns_merge_details].apply(
        lambda i: df_details[df_details[coluns_merge_details] == i].to_dict("records")
    )

    special_column = {
        "field": coluns_name_details,
        "cellRenderer": "agGroupCellRenderer",
        "checkboxSelection": False,
    }

    other_columns = []
    for col in df.columns:
        if col in [coluns_name_details, "detail"]:
            continue
        col_def = {"field": col}
        if col in num_columns + percent_columns:
            col_def["cellStyle"] = cellstyle_code
        other_columns.append(col_def)

    detail_columnDefs = [{"field": c} for c in df_details.columns]

    grid_options.update({
        "masterDetail": True,
        "columnDefs": [special_column] + other_columns,
        "detailCellRendererParams": {
            "detailGridOptions": {
                "columnDefs": detail_columnDefs,
                "suppressColumnVirtualisation": True,
                "onFirstDataRendered": JsCode("""
                    function(params) {
                        var allColumnIds = [];
                        params.columnApi.getAllColumns().forEach(
                            function(c){ allColumnIds.push(c.getColId()); }
                        );
                        params.columnApi.autoSizeColumns(allColumnIds, false);
                    }
                """),
            },
            "getDetailRowData": JsCode("function(params) {params.successCallback(params.data.detail);}"),
        },
        "rowData": df.to_dict("records"),
        "enableRangeSelection": True,
        "suppressRowClickSelection": True,
        "cellSelection": True,
        "rowHeight": 40,
        "defaultColDef": {"minWidth": 100, "autoHeight": False, "filter": True},
    })
    return df, grid_options


def dataframe_aggrid(df, name, num_columns=None, percent_columns=None,
                     date_columns=None, datetime_columns=None, df_details=None, coluns_merge_details=None,
                     coluns_name_details=None, key="default", highlight_rows=None,
                     fit_columns=None, fit_columns_on_grid_load=None, height=None, num_cel_style=None, num_columns_style=None):
    '''
    Docstring for dataframe_aggrid
    
    :param num_columns_style: Seleciona as colunas numéricas a serem estilizadas
    :param num_cel_style: Seleciona o estilo das colunas numéricas
        monetary -> positivo = verde, negativo = vermelho
        monetary inverse -> positivo = vermelho, negativo = verde
    '''
    num_columns = num_columns or []
    percent_columns = percent_columns or []
    date_columns = date_columns or []
    datetime_columns = datetime_columns or []
    highlight_rows = highlight_rows or []
    fit_columns = fit_columns or ColumnsAutoSizeMode.FIT_CONTENTS
    fit_columns_on_grid_load = fit_columns_on_grid_load or False
    num_columns_style = num_columns_style or []

    # 1. Formatação de colunas numéricas e percentuais
    for col in num_columns:
        df = format_numeric_column(df, col)
    for col in percent_columns:
        df = format_percent_column(df, col)
    for col in date_columns:
        df = format_date_column(df, col)
    for col in datetime_columns:
        df = format_datetime_column(df, col)

    # 2. CellStyle para colunas numéricas
    if num_cel_style == 'monetary' or num_cel_style == 'monetary inverse':
        cellstyle_code = get_cellstyle_code(num_cel_style)
    else:
        cellstyle_code = get_cellstyle_code()

    # 3. GridOptionsBuilder base
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=True, sortable=True, filterable=True)

    for col in num_columns + percent_columns:
        if f"{col}_NUM" in df.columns:
            gb.configure_column(f"{col}_NUM", hide=True, type=["numericColumn"])
    if "detail" in df.columns:
        gb.configure_column("detail", hide=True)

    # substitui columnDefs do gb / grid_options
    grid_options = gb.build()

    column_defs = []

    for col in df.columns:
        if f"{col}_NUM" in df.columns and not col.endswith("_NUM"):
            col_def = {
                "field": col,
                "type": ["numericColumn"],
                "valueGetter": JsCode(f"""
                    function(params) {{
                        return params.data['{col}_NUM'];
                    }}
                """),
                "valueFormatter": JsCode(f"""
                    function(params) {{
                        if (params.data && params.data['{col}']) {{
                            return params.data['{col}'];
                        }}
                        if (params.value == null) return '';
                        return new Intl.NumberFormat('pt-BR', {{ style: 'currency', currency: 'BRL' }}).format(params.value);
                    }}
                """),
                "comparator": JsCode("""
                    function(a, b) {
                        if (a == null && b == null) return 0;
                        if (a == null) return -1;
                        if (b == null) return 1;
                        return a - b;
                    }
                """),
            }
            # Só aplica cor se a coluna estiver na lista de colunas estilizadas
            if col in num_columns_style:
                col_def["cellStyle"] = cellstyle_code

            column_defs.append(col_def)

        elif col.endswith("_NUM"):
            column_defs.append({
                "field": col,
                "hide": True,
                "type": ["numericColumn"]
            })

        else:
            column_defs.append({
                "field": col
            })


    # ✅ agora é seguro substituir
    grid_options["columnDefs"] = column_defs

    grid_options.update({
        "columnDefs": column_defs,
        "suppressSizeToFit": True,
        "suppressColumnVirtualisation": True,
        "onGridReady": JsCode("""
            function(params) {
                params.api.sizeColumnsToFit();
            }
        """),
    })

    # 4. MasterDetail se necessário
    if df_details is not None:
        df, grid_options = apply_master_detail(
            df, df_details, coluns_merge_details, coluns_name_details,
            num_columns, percent_columns, cellstyle_code, grid_options
        )
    else:
        grid_options.update({
            "enableRangeSelection": True,
            "suppressRowClickSelection": False,
            "cellSelection": False,
            "rowHeight": 40,
            "defaultColDef": {"minWidth": 100, "autoHeight": False, "filter": True},
        })

    # 5. DataFrame final (sem colunas técnicas)
    df_to_show = df.drop(columns=[c for c in df.columns if c.endswith("_NUM") or c == "detail"], errors="ignore")


    # 6. Tema e zebra
    if st.session_state.get("base_theme") == "dark":
        custom_theme = StAggridTheme(base="balham").withParams().withParts("colorSchemeDark")
        zebra_style = JsCode(f"""
        function(params) {{
            if ({str(highlight_rows)}.includes(params.data.Categoria)) {{
                return {{ fontWeight: 'bold', background: '#444', color: '#fff' }};
            }}
            return (params.node.rowIndex % 2 === 0)
                ? {{ background: '#222', color: '#fff' }}
                : {{ background: '#333', color: '#fff' }};
        }}
        """)
    else:
        custom_theme = StAggridTheme(base="balham").withParams()
        zebra_style = JsCode(f"""
        function(params) {{
            if ({str(highlight_rows)}.includes(params.data.Categoria)) {{
                return {{ fontWeight: 'bold', background: '#e6e6e6', color: '#111' }};
            }}
            return (params.node.rowIndex % 2 === 0)
                ? {{ background: '#fff', color: '#111' }}
                : {{ background: '#e6e6e6', color: '#111' }};
        }}
        """)

    grid_options["getRowStyle"] = zebra_style

    # 7. Render AgGrid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=fit_columns,
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        allow_unsafe_jscode=True,
        key=f"aggrid_{name}_{key}",
        theme=custom_theme,
        height=height or min(len(df_to_show)*40+34+11, 399),
        custom_css={
            ".ag-root-wrapper": {
                "border-radius": "10px",
                "overflow": "hidden",
                "border": "1px solid #ddd",
            },
            ".ag-cell": {
                "font-family": "'Source Sans Pro', sans-serif",
                "font-size": "14px",
                "display": "flex",
                "align-items": "center",
            },
            ".ag-header-cell-text": {
                "font-family": "'Source Sans Pro', sans-serif",
                "font-size": "15px",
                "font-weight": "600",
            },
        },
    )

    filtered_df = grid_response["data"]
    filtered_df = filtered_df.drop(columns=[c for c in filtered_df.columns if c.endswith("_NUM")], errors="ignore")
    return filtered_df, len(filtered_df)


def component_plotPizzaChart(labels, sizes, name, max_columns=8):
    chart_key = f"{labels}_{sizes}_{name}_"
    
    # Organize os dados para mostrar apenas um número limitado de categorias
    if len(labels) > max_columns:
        # Ordenar os dados e pegar os "max_columns" maiores
        sorted_data = sorted(zip(sizes, labels), reverse=True)[:max_columns]
        
        # Dados dos "Outros"
        others_value = sum(size for size, label in zip(sizes, labels) if (size, label) not in sorted_data)
        sorted_data.append((others_value, "Outros"))
        
        # Desempacotar os dados para labels e sizes
        sizes, labels = zip(*sorted_data)
    else:
        # Caso contrário, use todos os dados
        sizes, labels = sizes, labels

    # Preparar os dados para o gráfico
    data = [{"value": size, "name": label} for size, label in zip(sizes, labels)]
    
    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} ({d}%)"
        },
        "legend": {
            "orient": "vertical",
            "left": "65%",
            "top": "middle",
            "type": "scroll",  # Adiciona rolagem se muitos itens
            "height": 200,
            "textStyle": {
                "fontWeight": "normal",
                "fontSize": 10,
                "color": "#444"
        }
    },
        "grid": {  
            "left": "50%", 
            "right": "50%", 
            "containLabel": True
        },
    # "color": [
    #     "#8b0000", "#910d0d", "#971a1a", "#9d2828", "#a33535",
    #     "#a94343", "#af5050", "#b65e5e", "#bc6b6b", "#c27979",
    #     "#c88686", "#ce9494", "#d4a1a1", "#dbafaf", "#e1bcbc",
    #     "#e7caca", "#edd7d7", "#f3e5e5", "#f9f2f2", "#ffffff"
    #     ],
        "series": [
        {
            "name": "Quantidade",
            "type": "pie",
            "radius": ["40%", "75%"],
            "center": ["30%", "50%"],  # Gráfico mais à esquerda 
                "data": data,
                "label": {
                    "show": False  # Garante que os rótulos não apareçam nas fatias
                },
                "labelLine": {
                    "show": False  # Remove as linhas que puxam os rótulos
                },
                "minAngle": 5,  
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#fff",
                    "borderWidth": 2  
                },
                "selectedMode": "single",
                "selectedOffset": 8,  
                "emphasis": {
                    "label": {
                        "show": False  # Impede que o rótulo apareça ao passar o mouse
                    },
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    
    st_echarts(options=options, height="350px", key=chart_key)


def criar_seletores(LojasComDados, data_inicio_default, data_fim_default):
    col1, col2, col3 = st.columns([2, 1, 1])

    # Adiciona seletores
    with col1:
        lojas_selecionadas = st.multiselect(
            label='Selecione Lojas',
            options=LojasComDados,
            key='lojas_multiselect'
        )
    with col2:
        data_inicio = st.date_input(
            'Data de Início',
            value=data_inicio_default,
            key='data_inicio_input',
            format="DD/MM/YYYY"
        )
    with col3:
        data_fim = st.date_input(
            'Data de Fim',
            value=data_fim_default,
            key='data_fim_input',
            format="DD/MM/YYYY"
        )

    # Converte as datas selecionadas para o formato Timestamp
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

    return lojas_selecionadas, data_inicio, data_fim


def card_cmv(titulo, valor, is_estoque=False, is_percentual=False):

  if valor.startswith('R$ -') and is_estoque:
    html = f"""
    <div style="
        border: 1px solid #4A2F8C;
        border-radius: 12px;
        padding: 16px;
        width: 100%;
        background-color: #f9f9f9;
        color: #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        min-height: 129px;
        text-align: center;
    ">
        <div style="font-size: 16px; font-weight: bold;">{titulo}</div>
        <div style="font-size: 20px; font-weight: 500; margin-top: 4px; color: red">{valor}</div>
    </div>
    """

  elif is_estoque:
    html = f"""
    <div style="
        border: 1px solid #4A2F8C;
        border-radius: 12px;
        padding: 16px;
        width: 100%;
        background-color: #f9f9f9;
        color: #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        min-height: 129px;
        text-align: center;
    ">
        <div style="font-size: 16px; font-weight: bold;">{titulo}</div>
        <div style="font-size: 20px; font-weight: 500; margin-top: 4px; color: green">{valor}</div>
    </div>
    """
  else:
    html = f"""
    <div style="
        border: 1px solid #4A2F8C;
        border-radius: 12px;
        padding: 16px;
        width: 100%;
        background-color: #f9f9f9;
        color: #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        min-height: 129px;
        text-align: center;
    ">
        <div style="font-size: 16px; font-weight: bold;">{titulo}</div>
        <div style="font-size: 20px; font-weight: 500; margin-top: 4px;">{valor}</div>
    </div>
    """
  st.markdown(html, unsafe_allow_html=True)


def title_card_cmv(titulo):
  # HTML + CSS customizado
  html = f"""
  <div style="
      border: 1px solid #4A2F8C;
      border-radius: 12px;
      padding: 16px;
      width: 100%;
      background-color: #4A2F8C;
      color: #333;
      box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
      justify-content: center;
      min-height: 129px;
  ">
      <div style="font-size: 20px; font-weight: bold; margin: auto 0; color: #f9f9f9">
        {titulo}
      </div>
  </div>
  """
  st.markdown(html, unsafe_allow_html=True)

