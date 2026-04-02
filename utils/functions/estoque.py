import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar
import http
import json
import uuid

def login_zigpay():
    conn = http.client.HTTPSConnection('api.zigcore.com.br')
    deviceId = st.secrets["zigpay_api_scrapping"]["deviceInfoId"]

    organization = st.secrets["zigpay_api_scrapping"]["organization"]
    username = st.secrets["zigpay_api_scrapping"]["username"]
    password = st.secrets["zigpay_api_scrapping"]["password"]
    
    payload = json.dumps({
        "args": {
            "username": username,
            "password": password,
            "organizationUsername": organization
        },
        "deviceInfo": {
            "id": deviceId,
            "language": "pt-BR",
            "platform": {"browserUserAgent": "Mozilla/5.0"},
            "timezone": "America/Sao_Paulo",
            "type": "web",
            "version": ""
        },
        "extra": {"tz": "America/Sao_Paulo", "lng": "pt-BR"},
        "name": "logIn",
        "requestId": uuid.uuid4().hex,
        "version": 3
    })

    headers = {
        'accept': '*/*',
        'content-type': 'application/sdkgen',
        'origin': 'https://dashboard.zigpay.com.br',
        'referer': 'https://dashboard.zigpay.com.br/',
        'user-agent': 'Mozilla/5.0',
    }

    conn.request('POST', '/enterprise-postgres/logIn', payload, headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode('utf-8'))
    return data


def id_casa_para_ids_zigpay(id_casa, id_zigpay):
    lista_ids_zigpay = st.secrets['ids_zigpay'][f"{id_casa}"] if f"{id_casa}" in st.secrets['ids_zigpay'] else [id_zigpay]
    return lista_ids_zigpay


@st.cache_data
def request_getProductsSoldAtEventInPeriodV2_zigpay(
    event_id,
    place_id=None,
    since=None,
    until=None,
    sources=None
):
    """
    Faz requisição para obter produtos vendidos em um evento em um período específico.
    
    Args:
        event_id (str): ID do evento (obrigatório)
        device_id (str): ID do dispositivo (obrigatório)
        place_id (str, optional): ID do local
        since (str, optional): Data inicial (formato: YYYY-MM-DD ou timestamp)
        until (str, optional): Data final (formato: YYYY-MM-DD ou timestamp)
        sources (list, optional): Lista de fontes de dados
    
    Returns:
        pd.DataFrame: DataFrame com os produtos vendidos
    """
    device_id = st.secrets["zigpay_api_scrapping"]["deviceInfoId"]
    conn = http.client.HTTPSConnection('api.zigcore.com.br')
    
    headers = {
        'accept': '*/*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/sdkgen',
        'origin': 'https://dashboard.zigpay.com.br',
        'priority': 'u=1, i',
        'referer': 'https://dashboard.zigpay.com.br/',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="146", "Chromium";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    }
    
    # Construir o payload com os argumentos
    payload = {
        "args": {
            "eventId": event_id,
            "placeId": place_id,
            "since": since,
            "until": until,
            "sources": sources
        },
        "deviceInfo": {
            "id": device_id,
            "language": "pt-BR",
            "platform": {
                "browserUserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            },
            "timezone": "America/Sao_Paulo",
            "type": "web",
            "version": "/prod.chunk.2c3325a42d601ea2b4b5.js"
        },
        "extra": {
            "tz": "America/Sao_Paulo",
            "lng": "pt-BR"
        },
        "name": "getProductsSoldAtEventInPeriodV2",
        "requestId": uuid.uuid4().hex,
        "version": 3
    }
    
    # Fazer a requisição
    conn.request(
        'POST',
        '/enterprise-postgres/getProductsSoldAtEventInPeriodV2',
        json.dumps(payload),
        headers
    )
    
    response = conn.getresponse()
    raw = response.read()
    
    # Verificar se a resposta está vazia
    if not raw or raw.strip() == b'':
        print("Erro: Resposta vazia da API")
        return pd.DataFrame()
    
    try:
        data = json.loads(raw.decode('utf-8'))
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
        print(f"Conteúdo da resposta: {raw.decode('utf-8', errors='replace')}")
        return pd.DataFrame()
    
    # Verificar se houve erro na resposta
    if data.get('error') is not None:
        print(f"Erro na requisição: {data['error']}")
        return pd.DataFrame()
    
    # A resposta é uma lista direta de produtos (não dentro de 'result')
    products = data.get('result', [])
    
    # Se não há produtos, retorna DataFrame vazio
    if not products or len(products) == 0:
        print("Nenhum produto encontrado")
        return pd.DataFrame()
    
    # Extrair apenas os campos necessários
    products_simplified = []
    for product in products:
        products_simplified.append({
            'evento': event_id,
            'id_produto': product.get('id'),
            'nome': product.get('name'),
            'categoria': product.get('category'),
            'quantidade': product.get('count'),
            'tipo_produto': product.get('kind', {}).get('name'),
            'categoria_mestre': product.get('kind', {}).get('masterKind'),
        })
    
    # Converter para DataFrame
    df = pd.DataFrame(products_simplified)
        
    return df


@st.cache_data
def request_getEvents_zigpay(id_zigpay, month, year):
    import http.client
    import json
    import uuid

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

    conn.request(
        'POST',
        '/enterprise-postgres/getEvents',
        f'{{"args":{{"placeId":"{id_zigpay}","month":{month - 1},"year":{year}}},"deviceInfo":{{"id":"{deviceId}","language":"pt-BR","platform":{{"browserUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"}},"timezone":"America/Sao_Paulo","type":"web","version":""}},"extra":{{"tz":"America/Sao_Paulo","lng":"pt-BR"}},"requestId": "{uuid.uuid4().hex}","name":"getEvents","version":3}}',
        headers
    )

    response = conn.getresponse()
    raw = response.read()
    data = json.loads(raw.decode('utf-8'))

    # Extrair apenas os eventos
    events = data['result']['events']
    
    # Se não há eventos, retorna DataFrame vazio
    if not events or len(events) == 0:
        return pd.DataFrame()
    
    # Converter para DataFrame
    df = pd.DataFrame(events)
    
    # Converter valores em centavos para reais (se a coluna existir)
    if 'income' in df.columns:
        df['income'] = df['income'] / 100
    
    if 'averageTicket' in df.columns:
        df['averageTicket'] = df['averageTicket'] / 100

    return df
