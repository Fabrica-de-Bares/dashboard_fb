import streamlit as st
import pandas as pd
from utils.components import *
import math

def calcular_repasses_gazit(df):
    # Dataframe com valores de repasse para Gazit

	df['Total Gazit Aroos'] = (
		df['Valor Locação Aroo 1'] * 0.7 +
		df['Valor Locação Aroo 2'] * 0.7 +
		df['Valor Locação Aroo 3'] * 0.7
	)

	df['Total Gazit Anexo'] = df['Valor Locação Anexo'] * 0.3

	df['Total Gazit'] = (
		df['Valor Locação Aroo 1'] * 0.7 +
		df['Valor Locação Aroo 2'] * 0.7 +
		df['Valor Locação Aroo 3'] * 0.7 +
		df['Valor Locação Anexo'] * 0.3
	)

	return df


def drop_colunas_eventos(df):
	df.drop(columns=[
		'Casa',
		'ID Evento',
		'Comercial Responsavel',
		'Status_Evento',
		'Observacoes',
		'Motivo_Declinio',
		'Nome Evento',
		'Valor AB',
		'Num_Pessoas',
		'Tipo_Evento',
		'Modelo_Evento'
	], inplace=True, axis=1)
	return df

def rename_colunas_eventos(df):
	df.rename(columns={
		'ID_Evento': 'ID Evento',
		'ID_Nome_Evento': 'Evento',
		'Comercial_Responsavel': 'Comercial Responsável',
		'Data Contratação': 'Data Contratação',
		'Data_Evento': 'Data Evento',
		'Modelo_Evento': 'Modelo Evento',
		'Num_Pessoas': 'Num Pessoas',
		'Valor AB': 'Valor A&B',
		'Valor Locação Notie': 'Valor Locação Notiê',
		'Valor Imposto': 'Imposto',
		'Valor Total Locação': 'Total Locação',
		'Valor Total': 'Valor Total',
		'Status_Evento': 'Status Evento',
		'Observacoes': 'Observações',
		'Motivo_Declinio': 'Motivo Declínio'
	}, inplace=True)
	return df

def rename_colunas_parcelas(df):
	if df is not None and not df.empty:
		df = df.copy()
		df.rename(columns={
			'ID_Parcela': 'ID Parcela',
			'ID_Evento': 'ID Evento',
			'Nome Evento': 'Nome Evento',
			'Categoria Parcela': 'Categoria Parcela',
			'Valor Parcela': 'Valor Parcela',
			'Data Vencimento': 'Data Vencimento',
			'Status_Pagamento': 'Status Pagamento',
			'Data Recebimento': 'Data Recebimento',
			'Repasse_Gazit_Bruto': 'Valor Total Bruto Gazit',
			'Repasse_Gazit_Liquido': 'Valor Total Líquido Gazit',
			'Valor Total Locação': 'Total Locação',
			'Repasse Gazit Bruto Aroos': 'AROO Valor Bruto Gazit',
			'Repasse Gazit Liquido Aroos': 'AROO Valor Líquido Gazit',
			'Repasse Gazit Bruto Anexo': 'ANEXO Valor Bruto Gazit',
			'Repasse Gazit Liquido Anexo': 'ANEXO Valor Líquido Gazit'
		}, inplace=True)
		return df
	else:
		return None
	

def calcular_repasses_gazit_parcelas(df_parcelas, df_eventos):
    df_eventos['Valor Locacao Total Aroos'] = (
        df_eventos['Valor Locação Aroo 1'] +
        df_eventos['Valor Locação Aroo 2'] +
        df_eventos['Valor Locação Aroo 3']
    )
    df_parcelas = df_parcelas.merge(
        df_eventos[[
            'ID Evento', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo',
            'Valor Total Locação', 'Valor Locacao Total Aroos',
            'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante'
        ]],
        how='inner', on='ID Evento'
    )

    colunas_float = [
        'Repasse_Gazit_Bruto', 'Repasse_Gazit_Liquido',
        'Repasse Gazit Bruto Aroos', 'Repasse Gazit Liquido Aroos',
        'Repasse Gazit Bruto Anexo', 'Repasse Gazit Liquido Anexo',
        'Valor Parcela AROO', 'Valor Parcela ANEXO',
        'Valor Parcela Notie', 'Valor Parcela Mirante'
    ]
    for col in colunas_float:
        if col not in df_parcelas.columns:
            df_parcelas[col] = 0.0

    for idx, row in df_parcelas.iterrows():
        if row['Categoria Parcela'] == 'Locação':
            if row['Valor Total Locação'] != 0:
                porcentagem = df_parcelas.loc[idx, 'Valor Parcela'] / df_parcelas.loc[idx, 'Valor Total Locação']
                porcentagem_aroo = df_parcelas.loc[idx, 'Valor Locacao Total Aroos'] / df_parcelas.loc[idx, 'Valor Total Locação']
                porcentagem_anexo = df_parcelas.loc[idx, 'Valor Locação Anexo'] / df_parcelas.loc[idx, 'Valor Total Locação']
                porcentagem_notie = df_parcelas.loc[idx, 'Valor Locação Notie'] / df_parcelas.loc[idx, 'Valor Total Locação']
                porcentagem_mirante = df_parcelas.loc[idx, 'Valor Locação Mirante'] / df_parcelas.loc[idx, 'Valor Total Locação']
                df_parcelas.at[idx, 'Valor Parcela AROO'] = round(row['Valor Parcela'] * porcentagem_aroo, 2)
                df_parcelas.at[idx, 'Valor Parcela ANEXO'] = round(row['Valor Parcela'] * porcentagem_anexo, 2)
                df_parcelas.at[idx, 'Valor Parcela Notie'] = round(row['Valor Parcela'] * porcentagem_notie, 2)
                df_parcelas.at[idx, 'Valor Parcela Mirante'] = round(row['Valor Parcela'] * porcentagem_mirante, 2)
                df_parcelas.at[idx, 'Repasse_Gazit_Bruto'] = round(row['Total Gazit'] * porcentagem, 2)
                df_parcelas.at[idx, 'Repasse Gazit Bruto Aroos'] = round(row['Total Gazit Aroos'] * porcentagem, 2)
                df_parcelas.at[idx, 'Repasse Gazit Bruto Anexo'] = round(row['Total Gazit Anexo'] * porcentagem, 2)
        else:
            df_parcelas.at[idx, 'Repasse_Gazit_Bruto'] = 0.0
            df_parcelas.at[idx, 'Repasse Gazit Bruto Aroos'] = 0.0
            df_parcelas.at[idx, 'Repasse Gazit Bruto Anexo'] = 0.0
            df_parcelas.at[idx, 'Valor Parcela AROO'] = 0.0
            df_parcelas.at[idx, 'Valor Parcela ANEXO'] = 0.0
            df_parcelas.at[idx, 'Valor Parcela Notie'] = 0.0
            df_parcelas.at[idx, 'Valor Parcela Mirante'] = 0.0

    mask = df_parcelas['Categoria Parcela'] == 'Locação'
    df_parcelas.loc[mask, 'Repasse_Gazit_Liquido'] = (df_parcelas.loc[mask, 'Repasse_Gazit_Bruto'] * 0.8547).round(2)
    df_parcelas.loc[mask, 'Repasse Gazit Liquido Aroos'] = (df_parcelas.loc[mask, 'Repasse Gazit Bruto Aroos'] * 0.8547).round(2)
    df_parcelas.loc[mask, 'Repasse Gazit Liquido Anexo'] = (df_parcelas.loc[mask, 'Repasse Gazit Bruto Anexo'] * 0.8547).round(2)

    return df_parcelas
   

