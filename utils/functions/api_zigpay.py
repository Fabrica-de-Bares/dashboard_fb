import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time
import calendar
import http
import json
import uuid

def get_compradores_zigpay_api(data_inicio, data_fim, id_zigpay):

    headers = {
            'Authorization': st.secrets["api_zigpay"]["token"],
    }  

    url = "https://api.zigcore.com.br/integration/erp/compradores"
    df = pd.DataFrame()
    
    params = {
        "dtinicio": pd.to_datetime(data_inicio).strftime("%Y-%m-%d"),
        "dtfim": pd.to_datetime(data_fim).strftime("%Y-%m-%d"),
        "loja": f"{id_zigpay}"
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        compradores = response.json()
        df = pd.DataFrame(compradores)
        
    else:
        print(f"Erro {response.status_code} na requisição de compradores.")

    return df


def df_compradores_zigpay_mes(mes, ano, id_zigpay):
    data_inicio = pd.Timestamp(f"{ano}-{mes:02d}-01")

    if datetime.now().month == mes and datetime.now().year == ano:
        data_fim = pd.Timestamp(datetime.now())
    else:
        data_fim = pd.Timestamp(datetime(ano, mes, calendar.monthrange(ano, mes)[1]))
    
    print(data_inicio, data_fim)
    df = pd.DataFrame()
    
    # Usar intervalo de 3 dias para garantir que fica dentro do limite de 5
    for data in pd.date_range(start=data_inicio, end=data_fim, freq='3D'):
        data_inicio_requisicao = data
        data_fim_requisicao = min(data + pd.DateOffset(days=2), data_fim)  # 3 dias completos
        
        if data_inicio_requisicao <= data_fim_requisicao:
            print(data_inicio_requisicao, data_fim_requisicao)
            df_resultado = get_compradores_zigpay_api(data_inicio_requisicao, data_fim_requisicao, id_zigpay)
            df = pd.concat([df, df_resultado], ignore_index=True)

    if df.empty:
        df = pd.DataFrame(columns=["userDocument", "userName", "transactionId"])

    return df

# Relatório Zigpay - Ranking de vendas 
def request_getSellerReportForPlace_zigpay(id_zigpay, data_inicio, data_fim):
    import http.client
    import json
    import uuid

    data_inicio = pd.to_datetime(data_inicio).strftime("%Y-%m-%d")
    data_fim = data_fim + pd.DateOffset(days=1)
    data_fim = pd.to_datetime(data_fim).strftime("%Y-%m-%d")

    deviceId = st.secrets["zigpay_api_scrapping"]["deviceInfoId"]

    conn = http.client.HTTPSConnection('api.zigcore.com.br')
    headers = {
        'accept': '*/*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/sdkgen',
        'origin': 'https://dashboard.zigpay.com.br',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.zigpay.com.br/',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    }

    # args -> since = dia inicial T03:00:00.000
    # args -> until = dia posterior ao dia final T02:59:59.999
    conn.request(
        'POST',
        '/enterprise-postgres/getSellerReportForPlace',
        f'{{"args":{{"placeId":"{id_zigpay}","since":"{data_inicio}T03:00:00.000","until":"{data_fim}T02:59:59.999","sources":null}},"deviceInfo":{{"id":"{deviceId}","language":"pt-BR","platform":{{"browserUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"}},"timezone":"America/Sao_Paulo","type":"web","version":"/prod.chunk.8ea8b631bf8281962b43.js"}},"extra":{{"tz":"America/Sao_Paulo","lng":"pt-BR"}},"requestId": "{uuid.uuid4().hex}","name":"getSellerReportForPlace","version":3}}',
        headers
    )

    response = conn.getresponse()
    raw = response.read()
    data = json.loads(raw.decode('utf-8'))

    # Converter para DataFrame
    df = pd.DataFrame(data['result'])

    # Os valores estão em centavos — converter para reais
    df['soldValue'] = df['soldValue'] / 100
    df['tip'] = df['tip'] / 100

    # Ordenar por maior valor vendido
    df = df.sort_values('soldValue', ascending=False)
    return df


# Painel do Evento - Zigpay
def request_getTotalReceipt_zigpay(id_zigpay, data_inicio, data_fim):

    data_inicio = pd.to_datetime(data_inicio).strftime("%Y-%m-%d")
    data_fim = data_fim + pd.DateOffset(days=1)
    data_fim = pd.to_datetime(data_fim).strftime("%Y-%m-%d")

    deviceId = st.secrets["zigpay_api_scrapping"]["deviceInfoId"]

    conn = http.client.HTTPSConnection('api.zigcore.com.br')
    headers = {
        'accept': '*/*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/sdkgen',
        'origin': 'https://dashboard.zigpay.com.br',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.zigpay.com.br/',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    }

    # args -> since = dia inicial T03:00:00.000
    # args -> until = dia posterior ao dia final T02:59:59.999
    conn.request(
        'POST',
        '/enterprise-postgres/getTotalReceipt',
        f'{{"args":{{"placeId":"{id_zigpay}","since":"{data_inicio}T03:00:00.000","until":"{data_fim}T02:59:59.999","sources":null}},"deviceInfo":{{"id":"{deviceId}","language":"pt-BR","platform":{{"browserUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"}},"timezone":"America/Sao_Paulo","type":"web","version":"/prod.chunk.8ea8b631bf8281962b43.js"}},"extra":{{"tz":"America/Sao_Paulo","lng":"pt-BR"}},"requestId": "{uuid.uuid4().hex}","name":"getSellerReportForPlace","version":3}}',
        headers
    )

    response = conn.getresponse()
    raw = response.read()
    data = json.loads(raw.decode('utf-8'))

    # Converter para DataFrame
    df = pd.DataFrame(data['result'])

    # Os valores estão em centavos — converter para reais
    df['soldValue'] = df['soldValue'] / 100
    df['tip'] = df['tip'] / 100

    # Ordenar por maior valor vendido
    df = df.sort_values('soldValue', ascending=False)
    return df

def id_casa_para_ids_zigpay(id_casa, id_zigpay):
    lista_ids_zigpay = st.secrets['ids_zigpay'][f"{id_casa}"] if f"{id_casa}" in st.secrets['ids_zigpay'] else [id_zigpay]
    return lista_ids_zigpay


# API oficial de integração (ERP) — substitui a API do painel (enterprise-postgres), que passou a
# bloquear requisições simulando navegador.
# Com dtinicio = dtfim = dia, a saida-produtos traz os itens do evento aberto naquele dia (o mesmo
# dia de abertura do evento no painel). Valores em centavos. A API recusa mais de 5 eventos por chamada, por isso um
# dia por requisição.
def request_saida_produtos_dia_zigpay_erp(id_zigpay, dia, token):
    url = "https://api.zigcore.com.br/integration/erp/saida-produtos"
    headers = {'Authorization': token, 'Accept': 'application/json'}
    params = {"dtinicio": dia, "dtfim": dia, "loja": f"{id_zigpay}"}

    for tentativa in range(1, 6):
        response = requests.get(url, headers=headers, params=params, timeout=120)
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(3 * tentativa)
            continue
        if response.status_code != 200:
            raise RuntimeError(f"Zigpay saida-produtos {dia}: HTTP {response.status_code} — {response.text[:200]}")
        return response.json()

    raise RuntimeError(f"Zigpay saida-produtos {dia}: HTTP {response.status_code} após 5 tentativas")


@st.cache_data
def request_faturamento_dia_zigpay_erp(id_zigpay, month, year, produtos_fora=()):
    """Faturamento bruto, desconto e líquido por dia de evento no mês, em reais. Sem gorjeta (Tip),
    sem ingresso (Entrance) — que o relatório de produtos do painel não contava — e sem os produtos
    de produtos_fora. Dia sem venda não entra."""
    primeiro_dia = date(year, month, 1)
    ultimo_dia = min(date(year, month, calendar.monthrange(year, month)[1]), datetime.now().date())
    if ultimo_dia < primeiro_dia:
        return pd.DataFrame()

    token = st.secrets["api_zigpay"]["token"]
    dias = [d.date().isoformat() for d in pd.date_range(primeiro_dia, ultimo_dia)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        respostas = list(executor.map(lambda dia: request_saida_produtos_dia_zigpay_erp(id_zigpay, dia, token), dias))

    produtos_fora = {str(p) for p in produtos_fora}
    linhas = []
    for dia, itens in zip(dias, respostas):
        if not itens:
            continue
        bruto = desconto = 0
        for item in itens:
            if item.get('productType') in ('Tip', 'Entrance') or str(item.get('productId')) in produtos_fora:
                continue
            bruto += round((item.get('unitValue') or 0) * (item.get('count') or 0))
            desconto += item.get('discountValue') or 0
        linhas.append({
            'Data Evento': date.fromisoformat(dia),
            'valor_total': round(bruto / 100, 2),
            'desconto': round(desconto / 100, 2),
            'valor_liquido': round((bruto - desconto) / 100, 2),
        })

    return pd.DataFrame(linhas)
