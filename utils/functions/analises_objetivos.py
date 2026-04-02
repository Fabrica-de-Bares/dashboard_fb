import streamlit as st


# Análise SWOT
def render_swot_box(titulo, classe, lista, casa):
    itens = "".join([f"<li>{item}</li>" for item in lista])
    if casa == 'Arcos' or casa == 'Girondino' or casa == 'Jacaré' or casa == 'Ultra Evil Premium Ltda ':
        height = '18em'
    elif casa == 'Bar Léo - Centro':
        height = '32em'
    elif casa == 'Blue Note - São Paulo':
        if classe == 'fraquezas' or classe == 'ameacas': height = '30em'
        else: height = '34em'
    else: height = '26em'

    return f"""
<div class="swot-box" style="height: {height}">
    <div class="swot-title {classe}">{titulo}</div>
    <ul class="swot-list">
        {itens}
    </ul>
</div>
"""

def render_swot(dados, casa):
    col1, col2 = st.columns(2)

    # FORÇAS + OPORTUNIDADES
    with col1:
        st.markdown('<h6 style="text-align: center;">FATORES INTERNOS</h6>', unsafe_allow_html=True)
        st.markdown(render_swot_box("FORÇAS", "forcas", dados["forcas"], casa), unsafe_allow_html=True)

    with col2:
        st.markdown('<h6 style="text-align: center;">FATORES EXTERNOS</h6>', unsafe_allow_html=True)
        st.markdown(render_swot_box("OPORTUNIDADES", "oportunidades", dados["oportunidades"], casa), unsafe_allow_html=True)

    st.divider()

    col3, col4 = st.columns(2)

    # FRAQUEZAS + AMEAÇAS
    with col3:
        st.markdown(render_swot_box("FRAQUEZAS", "fraquezas", dados["fraquezas"], casa), unsafe_allow_html=True)
        st.markdown('<h6 style="text-align: center; margin-top: 15px;">FATORES INTERNOS</h6>', unsafe_allow_html=True)

    with col4:
        st.markdown(render_swot_box("AMEAÇAS", "ameacas", dados["ameacas"], casa), unsafe_allow_html=True)
        st.markdown('<h6 style="text-align: center; margin-top: 15px;">FATORES EXTERNOS</h6>', unsafe_allow_html=True)

