import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.analises_objetivos import *
from utils.constants.analise_swot import SWOT_CASAS_2026
from utils.components import button_download, seletor_ano, input_selecao_casas

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Análises e Objetivos",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("📜 Análises e Objetivos")
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    lista_casas_retirar = ['Todas as Casas', 'Bar Brahma Paulista', 'Blue Note SP (Novo)', 'Blue Note SP (Sala 2)', 'Brahminha', 'Edificio Rolim', 'Priceless', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'The Cavern - Almoço']
    id_casa, casa, id_zigpay = input_selecao_casas(lista_casas_retirar, 'casa')
    
with col2:
    ano = seletor_ano(2026, 2026, 'ano')
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(['Análise SWOT', 'Análise Interna', 'Exemplo de Rotinas Gerais', 'Planejamento de Marketing'])

# Análise SWOT
with tab1:
    st.markdown("""
        <style>
        .swot-box {
            border: 1px solid #000;
            padding: 16px;
            # height: 26em;
        }
        .swot-title {
            font-weight: 700;
            text-align: center;
            padding: 6px;
            margin: -16px -16px 12px -16px;
            color: white;
        }
        .forcas { background-color: #8BC34A; }
        .fraquezas { background-color: #FF9800; }
        .oportunidades { background-color: #0070C0; }
        .ameacas { background-color: #F44336; color: white; }

        .swot-list li {
            margin-bottom: 6px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.subheader("Análise SWOT")
    st.divider()

    if ano == 2026:
        dados_swot = SWOT_CASAS_2026.get(id_casa) # recupera as informações da casa selecionada
    if dados_swot:
        render_swot(dados_swot, casa)
        
        st.divider()
        # Legenda
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap:1em; padding:10px; border:1px solid #ccc; border-radius:8px";>
                <span style="font-size: 16px"><b>Interno:</b> diz respeito ao que está dentro da empresa — aquilo que ela <b>controla</b> (pessoas, processos, estrutura, marca, finanças).</span>
                <span style="font-size: 16px"><b>Externo: </b> são fatores fora do controle direto — o <b>mercado, concorrência, economia, comportamento do consumidor</b>, etc.</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning(f'{casa} sem dados para Análise SWOT.')

    
# Análise Interna
with tab2:
    st.subheader('Análise da Operação')
    if casa != 'The Cavern' and casa != 'Escritório Fabrica de Bares':
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap:1em; padding:10px; border:1px solid #ccc; border-radius:8px";>
                <span style="font-size: 16px"><b>1.</b> Análisar se essas responsabilidades são atendidas hoje pela área na FB</span>
                <span style="font-size: 16px"><b>2.</b> Analisar e definir se esse ponto levantado é ou não um objetivo que deve ser buscado pela área em {ano}</span>
            </div>
            """, unsafe_allow_html=True)
        st.divider()
        
        with st.container(horizontal_alignment="center"):
            st.image(f"assets/images/2026/{id_casa}_Analise_Interna.png")
    else: st.warning(f'{casa} sem dados para Análise Interna.')
