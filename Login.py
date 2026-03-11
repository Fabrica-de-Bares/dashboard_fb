import streamlit as st
from utils.user import *
from utils.queries_eventos import *
from utils.functions.general_functions import *

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Login",
    page_icon="🔑",
    layout="centered",
)

ABAS = {
    123: {'nome_aba': '🛠️ Ajustes', 'page_link': 'pages/Conciliação - Ajustes.py'},
    105: {'nome_aba': '🍴 Análise de Consumo', 'page_link': 'pages/Faturamento - Análise de Consumo.py'},
    131: {'nome_aba': '💲 Análise de Preços', 'page_link': 'pages/Suprimentos - Análise_de_Preços.py'},
    129: {'nome_aba': '🎵 Artístico', 'page_link': 'pages/Operacional - Artístico.py'},
    132: {'nome_aba': '🛒 Auditoria - Pedido de Compras', 'page_link': 'pages/Suprimentos - Auditoria_-_Pedido_de_Compras.py'},
    115: {'nome_aba': '🚫 Auditoria de Eventos - Confirmados', 'page_link': 'pages/Eventos - Eventos_Auditoria_de_Eventos_Confirmados.py'},
    114: {'nome_aba': '🧾 Auditoria de Eventos - Preenchimento dos Lançamentos', 'page_link': 'pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py'},
    116: {'nome_aba': '🛍️ Auditoria Externa - Gazit - Shopping Light', 'page_link': 'pages/Eventos - Gazit.py'},
    108: {'nome_aba': '📆 Calendário de Eventos - Gazit', 'page_link': 'pages/Eventos - Calendário_Gazit.py'},
    107: {'nome_aba': '📆 Calendário de Eventos Confirmados', 'page_link': 'pages/Eventos - Calendário_de_Eventos_Confirmados.py'},
    106: {'nome_aba': '📆 Calendário Geral de Eventos', 'page_link': 'pages/Eventos - Calendário_Geral_de_Eventos.py'},
    128: {'nome_aba': '⚖️ CMV Real', 'page_link': 'pages/CMV - CMV_Real.py'},
    127: {'nome_aba': '📋 CMV Teórico - Análise de Fichas Técnicas', 'page_link': 'pages/CMV - CMV_Teórico_-_Análise_de_Fichas_Técnicas.py'},
    121: {'nome_aba': '💰 Conciliação por Casa', 'page_link': 'pages/Conciliação - Conciliações.py'},
    110: {'nome_aba': '↔️ Contas a Receber - Conciliação de Parcelas de Eventos', 'page_link': 'pages/Eventos - Conciliação_de_Parcelas_Eventos.py'},
    125: {'nome_aba': '💸 Controle de Despesas Gerais', 'page_link': 'pages/Financeiro - Despesas.py'},
    122: {'nome_aba': '📊 Farol de Conciliação', 'page_link': 'pages/Conciliação - Farol_de_Conciliação.py'},
    102: {'nome_aba': '💵 Faturamento - Outras Receitas', 'page_link': 'pages/Faturamento - Outras_Receitas.py'},
    109: {'nome_aba': '💰 Faturamento Bruto de Eventos', 'page_link': 'pages/Eventos - Faturamento_Bruto_de_Eventos.py'},
    100: {'nome_aba': '💰 Faturamento Zigpay', 'page_link': 'pages/Financeiro - Faturamento_Zigpay.py'},
    101: {'nome_aba': '💰 Faturamento Zigpay - Média por dia da semana', 'page_link': 'pages/Faturamento - Faturamento ZigPay - Média por dia da semana.py'},
    120: {'nome_aba': '🔮 Fluxo Futuro', 'page_link': 'pages/Conciliação - Fluxo_Futuro.py'},
    119: {'nome_aba': '🪙 Fluxo Realizado', 'page_link': 'pages/Conciliação - Fluxo_Realizado.py'},
    124: {'nome_aba': '📈 Forecast - Previsão de Resultado - Tendência', 'page_link': 'pages/Financeiro - Forecast.py'},
    117: {'nome_aba': '🔎 Informações de Eventos', 'page_link': 'pages/Eventos - Informações_de_Eventos.py'},
    112: {'nome_aba': '📊 KPI\'s de Vendas - Cálculo da Comissão de Eventos', 'page_link': 'pages/Eventos - Acompanhamento_de_Comissão.py'},
    111: {'nome_aba': '📈 KPI\'s de Vendas - Conversão de Eventos', 'page_link': 'pages/Eventos - KPIs_Conversao_Eventos_Priceless.py'},
    113: {'nome_aba': '👥 KPI\'s de Vendas - Histórico e Recorrência de Clientes', 'page_link': 'pages/Eventos - KPIs_Historico_Clientes_Eventos.py'},
    126: {'nome_aba': '📊 Painel de CMV', 'page_link': 'pages/CMV - Painel_CMV.py'},
    103: {'nome_aba': '🪙 Previsão de Faturamento', 'page_link': 'pages/Fluxo_de_Caixa - Previsão_de_Faturamento.py'},
    118: {'nome_aba': '🧾 Projeção - Despesas', 'page_link': 'pages/Fluxo_de_Caixa - Projeção.py'},
    130: {'nome_aba': '📦 Relatório de Insumos - Suprimentos', 'page_link': 'pages/Suprimentos - Relatório_de_Insumos.py'},
    104: {'nome_aba': '🛍️ Relatório de Vendas', 'page_link': 'pages/Faturamento - Relatório de Vendas.py'},
    133: {'nome_aba': '📝 Categorização - Descontos', 'page_link': 'pages/Auditoria - Descontos.py'},
    134: {'nome_aba': '📝 Formatar - Promoções', 'page_link': 'pages/Auditoria - Promoções.py'},
    135: {'nome_aba': '⬆️ Colunas - DRE (Orçamentos / Real)', 'page_link': 'pages/Controladoria - Colunas_DRE.py'},
    136: {'nome_aba': '🏷️ Descontos - DRE', 'page_link': 'pages/Controladoria - Descontos_DRE.py'},
    #137: {'nome_aba': '🪙 Cálculo de Gorjeta', 'page_link': 'pages/Operacional - Cálculo_Gorjeta.py'}
}

def main():

    st.markdown(
        """
    <style>
      section[data-testid="stSidebar"][aria-expanded="true"]{
        display: none;
      }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if "loggedIn" not in st.session_state:
        st.session_state["loggedIn"] = False

    if not st.session_state["loggedIn"]:
        st.title(":bar_chart: Dashboard - FB")
        st.write("")

        with st.container(border=True):
            login = st.text_input(
                label="Login", value="", placeholder="nome@email.com"
            )
            password = st.text_input(
                label="Senha", value="", placeholder="senha", type="password"
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.button(
                    "Login",
                    on_click=handle_login,
                    args=(login, password),
                    type="primary",
                    width='stretch',
                )
    else:
        cargo, Nomeuser, login = config_permissoes_user()
        cargo = cargo[0]
        st.session_state["cargo_usuario"] = cargo
        st.session_state["nome_usuario"] = Nomeuser

        st.write("Você está logado!")
        st.markdown("Redirecionando...")

        # Recupera a permissao de casas
        df_lojas_user = GET_LOJAS_USER(login)
        casas_permitidas = df_lojas_user.to_dict("records")
        if not casas_permitidas and cargo == "Gazit":
            casas_permitidas = [
                {"ID Loja": 149, "Loja": "Priceless"},
            ]
        elif not casas_permitidas:
            print("Nenhuma permissão de casas encontrada")
            st.error("Nenhuma permissão de casas encontrada")
            st.stop()
        st.session_state["casas_permitidas"] = casas_permitidas

        cargo_abas = GET_ABAS_CARGOS(cargo)
        abas_permitidas = cargo_abas.to_dict("records")
        for aba in abas_permitidas:
            if aba["ID Aba"] in ABAS.keys():
                aba["page_link"] = ABAS[aba["ID Aba"]]["page_link"]
                aba["Aba"] = ABAS[aba["ID Aba"]]["nome_aba"]
        st.session_state["abas_permitidas"] = abas_permitidas

        # Verifica a primeira permissão do usuário
        if not abas_permitidas:
            redirect_page = "Login.py" # Gazit
            st.switch_page(redirect_page)
        else:
            abas_permitidas = sorted(abas_permitidas, key=lambda x: x["ID Aba"])
            id_aba = abas_permitidas[0]["ID Aba"]
            redirect_page = ABAS[id_aba]["page_link"]
            st.switch_page(redirect_page)

if __name__ == "__main__":
    main()
