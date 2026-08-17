import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query, execute_query


@st.cache_data
def get_casas_validas():
    # Casa é considerada válida quando pertence ao grupo Fábrica de Bares
    # (FK_GRUPO_EMPRESA = 100) e teve faturamento nas últimas 4 semanas —
    # isso já exclui automaticamente holdings/entidades jurídicas sem
    # faturamento e casas fechadas, sem precisar de lista de nomes fixa.
    result, column_names = execute_query("""
		SELECT DISTINCT
			te.ID AS ID_Casa,
			te.NOME_FANTASIA AS Casa,
			te.ID_ZIGPAY AS ID_Zigpay
		FROM T_EMPRESAS te
		INNER JOIN T_ZIG_FATURAMENTO tzf ON tzf.FK_LOJA = te.ID
		WHERE te.FK_GRUPO_EMPRESA = 100
			AND tzf.DATA >= DATE_SUB(CURDATE(), INTERVAL 4 WEEK)
			AND tzf.VALOR > 0
		"""
	)
    df_casas = pd.DataFrame(result, columns=column_names)
    return df_casas


@st.cache_data
def get_casas_delivery():
    result, column_names = execute_query("""
		SELECT
			CASE 
				WHEN te.ID = 117 THEN 118
				ELSE te.ID							 							 
			END AS 'ID Loja',
			CASE
				WHEN te.ID = 117 THEN 'Delivery Brahma Centro'
				ELSE te.NOME_FANTASIA						 
			END AS 'Loja',
			CASE
				WHEN te.ID = 117 THEN '862812de-a2cd-4de4-987e-0e738403b800'
				ELSE te.ID_ZIGPAY 
			END AS 'ID Zigpay'
		FROM T_EMPRESAS te
		WHERE te.ID IN (103, 112, 117, 118, 139, 169, 181)								 
		"""
	)
    df_casas_delivery = pd.DataFrame(result, columns=column_names)
    return df_casas_delivery


# Dados de Eventos
@st.cache_data
def GET_EVENTOS_E_ADITIVOS_PRICELESS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Evento',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	''')


def GET_EVENTOS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Evento',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	WHERE tep.IS_ADITIVO = 0
	''')

@st.cache_data
def GET_ADITIVOS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Aditivo',
		tep.FK_EVENTO_DO_ADITIVO AS 'ID Evento do Aditivo',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Aditivo',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	WHERE tep.IS_ADITIVO = 1
	''')	


@st.cache_data
def GET_PARCELAS_EVENTOS_PRICELESS():
   	return dataframe_query(f'''
		SELECT
			tpep.ID AS 'ID Parcela',
			tpep.FK_EVENTO_PRICELESS AS 'ID Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tep.NOME_EVENTO AS 'Nome Evento',
			tsep.DESCRICAO AS 'Status Evento',
			tcep.DESCRICAO AS 'Categoria Parcela',
			tpep.VALOR_PARCELA as 'Valor Parcela',
			tpep.DATA_VENCIMENTO_PARCELA AS 'Data Vencimento',
			tsp.DESCRICAO AS 'Status Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA AS 'Data Recebimento' 
		FROM T_PARCELAS_EVENTOS_PRICELESS tpep 
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
		ORDER BY tep.ID DESC, tpep.ID DESC
	''')

@st.cache_data
def GET_EVENTOS_ADITIVOS_AGRUPADOS_CALENDARIO():
   	return dataframe_query(f'''
		SELECT
			COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) AS 'ID Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tee.NOME_COMPLETO AS 'Comercial Responsável',
			tee.ID AS 'ID Responsavel Comercial',
			tep2.NOME_EVENTO AS 'Nome Evento',
			trec.NOME AS 'Cliente',
			tep2.DATA_ENVIO_PROPOSTA AS 'Data Envio Proposta',
			tep2.DATA_CONTRATACAO AS 'Data Contratação',
			tep2.DATA_RECEBIMENTO_LEAD AS 'Data Recebimento Lead',
			tep2.DATA_EVENTO AS 'Data Evento',
			tte.DESCRICAO AS 'Tipo Evento',
			tme.DESCRICAO AS 'Modelo Evento',
			SUM(tep.VALOR_TOTAL_EVENTO) AS 'Valor Total Evento',
			SUM(tep.NUM_CLIENTES) AS 'Num Pessoas',
			SUM(tep.VALOR_AB) AS 'Valor AB',
			SUM(COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_ESPACO)) AS 'Valor Locação Total',
			SUM(tep.VALOR_CONTRATACAO_ARTISTICO) AS 'Valor Contratação Artístico',
			SUM(tep.VALOR_CONTRATACAO_TECNICO_SOM) AS 'Valor Contratação Técnico de Som',
			SUM(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO) AS 'Valor Contratação Bilheteria/Couvert Artístico',
			SUM(tep.VALOR_IMPOSTO) AS 'Valor Imposto',
			SUM(tep.VALOR_LOCACAO_GERADOR) AS 'Valor Locação Gerador',
			SUM(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO) AS 'Valor Locação Mobiliário',
			SUM(tep.VALOR_LOCACAO_UTENSILIOS) AS 'Valor Locação Utensílios',
			SUM(tep.VALOR_MAO_DE_OBRA_EXTRA) AS 'Valor Mão de Obra Extra',
			SUM(tep.VALOR_TAXA_ADMINISTRATIVA) AS 'Valor Taxa Administrativa',
			SUM(tep.VALOR_COMISSAO_BV) AS 'Valor Comissão BV',
			SUM(tep.VALOR_EXTRAS_GERAIS) AS 'Valor Extras Gerais',
			SUM(tep.VALOR_TAXA_SERVICO) AS 'Valor Taxa Serviço',
			SUM(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO) AS 'Valor Acréscimo Forma de Pagamento',
			tsep.DESCRICAO AS 'Status Evento',
			tep2.OBSERVACOES AS 'Observações',
			temd.DESCRICAO AS 'Motivo Declínio',
			tep2.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio',
			tep2.IS_ADITIVO AS 'Is Aditivo'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EVENTOS_PRICELESS tep2 ON COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) = tep2.ID # tep2 = evento pai
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep2.FK_CLIENTE = trec.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep2.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep2.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EMPRESAS te ON (tep2.FK_EMPRESA = te.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep2.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep2.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep2.FK_EXECUTIVA_EVENTOS = tee.ID)
		GROUP BY COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID)
	''')


@st.cache_data
def GET_EVENTOS_ADITIVOS_AGRUPADOS():
   	
	return dataframe_query(f'''
		SELECT
			COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) AS 'ID Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tee.NOME_COMPLETO AS 'Comercial Responsável',
			tee.ID AS 'ID Responsavel Comercial',
			tep2.NOME_EVENTO AS 'Nome Evento',
			trec.NOME AS 'Cliente',
			tep2.DATA_ENVIO_PROPOSTA AS 'Data Envio Proposta',
			tep2.DATA_CONTRATACAO AS 'Data de Contratação',
			tep2.DATA_RECEBIMENTO_LEAD AS 'Data Recebimento Lead',
			tep2.DATA_EVENTO AS 'Data do Evento',
			tte.DESCRICAO AS 'Tipo do Evento',
			tme.DESCRICAO AS 'Modelo do Evento',
			SUM(tep.VALOR_TOTAL_EVENTO) AS 'Valor Total',
			SUM(tep.NUM_CLIENTES) AS 'Número de Pessoas',
			SUM(tep.VALOR_AB) AS 'Valor AB',
			SUM(COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_ESPACO)) AS 'Valor Locação Total',
			SUM(tep.VALOR_CONTRATACAO_ARTISTICO) AS 'Valor Contratação Artístico',
			SUM(tep.VALOR_CONTRATACAO_TECNICO_SOM) AS 'Valor Contratação Técnico de Som',
			SUM(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO) AS 'Valor Contratação Bilheteria/Couvert Artístico',
			SUM(tep.VALOR_IMPOSTO) AS 'Valor Imposto',
			SUM(tep.VALOR_LOCACAO_GERADOR) AS 'Valor Locação Gerador',
			SUM(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO) AS 'Valor Locação Mobiliário',
			SUM(tep.VALOR_LOCACAO_UTENSILIOS) AS 'Valor Locação Utensílios',
			SUM(tep.VALOR_MAO_DE_OBRA_EXTRA) AS 'Valor Mão de Obra Extra',
			SUM(tep.VALOR_TAXA_ADMINISTRATIVA) AS 'Valor Taxa Administrativa',
			SUM(tep.VALOR_COMISSAO_BV) AS 'Valor Comissão BV',
			SUM(tep.VALOR_EXTRAS_GERAIS) AS 'Valor Extras Gerais',
			SUM(tep.VALOR_TAXA_SERVICO) AS 'Valor Taxa Serviço',
			SUM(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO) AS 'Valor Acréscimo Forma de Pagamento',
			tsep.DESCRICAO AS 'Status do Evento',
			tep2.OBSERVACOES AS 'Observações',
			temd.DESCRICAO AS 'Motivo do Declínio',
			tep2.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio',
			tep2.IS_ADITIVO AS 'Is Aditivo'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EVENTOS_PRICELESS tep2 ON COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) = tep2.ID # tep2 = evento pai
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep2.FK_CLIENTE = trec.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep2.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep2.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EMPRESAS te ON (tep2.FK_EMPRESA = te.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep2.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep2.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep2.FK_EXECUTIVA_EVENTOS = tee.ID)
		GROUP BY COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID)
	''')

@st.cache_data
def GET_ORCAMENTOS_EVENTOS():
	return dataframe_query(f'''
		SELECT 
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			to2.ANO AS 'Ano',
			to2.MES AS 'Mês',
			CASE
				WHEN tccg2.DESCRICAO = 'Eventos A&B' THEN 'A&B'
				WHEN tccg2.DESCRICAO = 'Eventos Couvert' THEN 'Couvert'
				WHEN tccg2.DESCRICAO = 'Eventos Locações' THEN 'Locação'
				WHEN tccg2.DESCRICAO = 'Eventos Rebate Fornecedores' THEN 'Repasse Fornecedores'
			END AS 'Categoria Orcamento',
			to2.VALOR AS 'Valor'
		FROM T_ORCAMENTOS_META_EVENTOS to2
			INNER JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON to2.FK_CLASSIFICACAO_1 = tccg.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
		WHERE tccg.DESCRICAO = 'Faturamento Bruto' AND tccg2.ID IN (939, 940, 942, 943)
		GROUP BY te.NOME_FANTASIA, to2.ANO, to2.MES, to2.FK_CLASSIFICACAO_2
	''')


@st.cache_data
def GET_RECEBIMENTOS_EVENTOS():
	return dataframe_query(f'''
		SELECT 
			CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO) AS 'ID - Responsavel',
			tee.ID AS 'ID Responsavel',
			tee.CARGO AS 'Cargo',
			tee.COMISSAO_COM_META_ATINGIDA AS 'Comissão Com Meta Atingida',
			tee.COMISSAO_SEM_META_ATINGIDA AS 'Comissão Sem Meta Atingida',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tep.ID AS 'ID Evento',
			tep.NOME_EVENTO AS 'Nome Evento',
			DATE(tpep.DATA_VENCIMENTO_PARCELA) AS 'Data Vencimento',
			DATE(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Data Recebimento',
			YEAR(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Ano Recebimento',
			MONTH(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Mês Recebimento',
			tpep.ID AS 'ID Parcela',
			tpep.VALOR_PARCELA AS 'Valor da Parcela',
			CASE
				WHEN tep.VALOR_TOTAL_EVENTO IS NOT NULL AND tep.VALOR_TOTAL_EVENTO <> 0
					THEN tep.VALOR_TOTAL_EVENTO
				ELSE (
					COALESCE(tep.VALOR_AB, 0) +
					COALESCE(tep.VALOR_IMPOSTO, 0) +
					COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) +
					COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) +
					COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) +
					COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) +
					COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) +
					COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) +
					COALESCE(tep.VALOR_LOCACAO_BAR, 0) +
					COALESCE(tep.VALOR_TAXA_SERVICO, 0) +
					COALESCE(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO, 0) +
					COALESCE(tep.VALOR_LOCACAO_GERADOR, 0) +
					COALESCE(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO, 0) +
					COALESCE(tep.VALOR_LOCACAO_UTENSILIOS, 0) +
					COALESCE(tep.VALOR_MAO_DE_OBRA_EXTRA, 0) +
					COALESCE(tep.VALOR_TAXA_ADMINISTRATIVA, 0) +
					COALESCE(tep.VALOR_COMISSAO_BV, 0) +
					COALESCE(tep.VALOR_EXTRAS_GERAIS, 0) +
					COALESCE(tep.VALOR_LOCACAO_ESPACO, 0) +
					COALESCE(tep.VALOR_CONTRATACAO_ARTISTICO, 0) +
					COALESCE(tep.VALOR_CONTRATACAO_TECNICO_SOM, 0) +
					COALESCE(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO, 0)
				)
			END AS 'Valor Total Evento',
			tep.VALOR_IMPOSTO AS 'Valor Total Imposto',
			tcep.DESCRICAO AS 'Categoria Parcela'
		FROM T_EVENTOS_PRICELESS tep 
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			INNER JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON tpep.FK_EVENTO_PRICELESS = tep.ID
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
		GROUP BY tpep.ID, CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO), te.ID, DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%Y'), DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%m'), tcep.DESCRICAO
		ORDER BY YEAR(tpep.DATA_RECEBIMENTO_PARCELA), MONTH(tpep.DATA_RECEBIMENTO_PARCELA)
''')


@st.cache_data
def GET_EVENTOS_COMISSOES():
	return dataframe_query(f'''
		SELECT 
			tep.ID as 'ID Evento',
			te.NOME_FANTASIA as 'Casa',
			te.ID as 'ID Casa',	
			tee.NOME_COMPLETO as 'Comercial Responsável',
			tep.NOME_EVENTO as 'Nome Evento',
			trec.NOME as 'Cliente',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratacao',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			tep.VALOR_TOTAL_EVENTO as 'Valor Total',
			tep.VALOR_AB as 'Valor AB',
			tep.VALOR_IMPOSTO as 'Valor Imposto',
			tsep.DESCRICAO as 'Status Evento',
			temd.DESCRICAO as 'Motivo Declínio'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
''')


def GET_ACESSOS_COMISSOES():
	return dataframe_query(f'''
		SELECT
			CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO) AS 'ID - Responsavel',
			au.LOGIN as 'Login',
			tee.CARGO AS 'Cargo',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa'
		FROM T_ASSOCIATIVA_CASAS_EXECUTIVAS_EVENTOS tacee
			JOIN T_EXECUTIVAS_EVENTOS tee ON (tee.ID = tacee.FK_EXECUTIVAS_EVENTOS)
			JOIN T_EMPRESAS te ON (te.ID = tacee.CASA)
			JOIN ADMIN_USERS au ON (au.ID= tacee.EMAIL)	
		WHERE tee.IS_ATIVO = 1			
	''')	


def GET_EVENTOS_AUDITORIA():
	return dataframe_query(f'''
		SELECT
			tep.ID AS 'ID Evento',
			tep.NOME_EVENTO AS 'Nome Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tsep.DESCRICAO AS 'Status',
			temd.DESCRICAO AS 'Motivo Declínio',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
			tep.VALOR_AB AS 'Valor AB',
			tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
			tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
			tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
			tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Couvert Artístico',			
			tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
			tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
			tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
			tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
			tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
			tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
			tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
			tep.VALOR_IMPOSTO AS 'Valor Imposto',
			tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
			tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
			tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
			tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
			tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
			tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
			tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
			tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
			tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
			tep.OBSERVACOES AS 'Observações',
			trec.NOME AS 'Cliente',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			DATE(tep.DATA_RECEBIMENTO_LEAD) AS 'Data Recebimento Lead',
			DATE(tep.DATA_ENVIO_PROPOSTA) AS 'Data Envio Proposta',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratação'
		FROM T_EVENTOS_PRICELESS tep
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON temd.ID = tep.FK_MOTIVO_DECLINIO
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
	''')


def GET_PARCELAS_EVENTOS_AUDITORIA():
	return dataframe_query(f'''
		SELECT
			tpep.ID AS 'ID Parcela',
			tpep.FK_EVENTO_PRICELESS AS 'ID Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tep.NOME_EVENTO AS 'Nome Evento',
			tsep.DESCRICAO AS 'Status Evento',
			tcep.DESCRICAO AS 'Categoria Parcela',
			tpep.VALOR_PARCELA as 'Valor Parcela',
			tpep.DATA_VENCIMENTO_PARCELA AS 'Data Vencimento',
			tsp.DESCRICAO AS 'Status Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA AS 'Data Recebimento' 
		FROM T_PARCELAS_EVENTOS_PRICELESS tpep 
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
	''')


def GET_CLIENTES_EVENTOS():
	return dataframe_query(f'''
		SELECT
			trec.ID AS 'ID Cliente',
			trec.NOME AS 'Cliente',
			trec.RAZAO_SOCIAL AS 'Razão Social',
			tsece.DESCRICAO_SETOR AS 'Setor Empresa',
			trec.DOCUMENTO AS 'Documento',
			trec.EMAIL AS 'Email',
			trec.TELEFONE AS 'Telefone',
			trec.PESSOA_DE_CONTATO AS 'Pessoa de Contato',
			trec.ENDERECO_COMPLETO AS 'Endereço',
			trec.CEP AS 'CEP',	
			COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) AS 'ID Evento',
			tep2.NOME_EVENTO AS 'Nome Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tsep.DESCRICAO AS 'Status',
			SUM(tep.VALOR_TOTAL_EVENTO) AS 'Valor Total Evento',
			SUM(tep.VALOR_AB) AS 'Valor AB',
			SUM(tep.VALOR_LOCACAO_AROO_1) AS 'Valor Locação Aroo 1',
			SUM(tep.VALOR_LOCACAO_AROO_2) AS 'Valor Locação Aroo 2',
			SUM(tep.VALOR_LOCACAO_AROO_3) AS 'Valor Locação Aroo 3',
			SUM(tep.VALOR_LOCACAO_ANEXO) AS 'Valor Locação Anexo',
			SUM(tep.VALOR_LOCACAO_NOTIE) AS 'Valor Locação Notie',
			SUM(tep.VALOR_LOCACAO_MIRANTE) AS 'Valor Locação Mirante',
			SUM(tep.VALOR_LOCACAO_BAR) AS 'Valor Locação Bar',
			SUM(tep.VALOR_LOCACAO_ESPACO) AS 'Valor Locação Espaço',
			SUM(tep.VALOR_IMPOSTO) AS 'Valor Imposto',
			tep2.OBSERVACOES AS 'Observações',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			DATE(tep.DATA_RECEBIMENTO_LEAD) AS 'Data Recebimento Lead',
			DATE(tep.DATA_ENVIO_PROPOSTA) AS 'Data Envio Proposta',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratação',
			tep.IS_ADITIVO AS 'Is Aditivo'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EVENTOS_PRICELESS tep2 ON COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) = tep2.ID
			INNER JOIN T_EMPRESAS te ON te.ID = tep2.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep2.FK_EXECUTIVA_EVENTOS
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep2.FK_CLIENTE = trec.ID)
			LEFT JOIN T_SETOR_EMPRESA_CLIENTES_EVENTOS tsece ON tsece.ID = trec.FK_SETOR_CLIENTE 
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep2.FK_STATUS_EVENTO
		WHERE tsep.DESCRICAO = 'Confirmado' AND trec.ID IS NOT NULL
		GROUP BY COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID)
	''')


# Auditora de Eventos - Alteração de Confirmados

def GET_LOGS_EVENTOS():
	return dataframe_query('''
		SELECT
			tep.ID AS 'ID Evento',
			tep.LOG_DATE as 'Data/Hora Log',
			DATE(tep.LOG_DATE) AS 'Data Log',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			au.FULL_NAME as 'Nome Usuário',
			au.EMAIL as 'Email Usuário',
			tee.NOME_COMPLETO AS 'Comercial Responsável',
			tep.NOME_EVENTO AS 'Nome Evento',
			trec.NOME AS 'Cliente',
			tep.DATA_CONTRATACAO AS 'Data Contratação',
			tep.DATA_EVENTO AS 'Data Evento',
			tte.DESCRICAO AS 'Tipo Evento',
			tme.DESCRICAO AS 'Modelo Evento',
			tse.DESCRICAO AS 'Segmento Evento',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
			tep.NUM_CLIENTES AS 'Num Pessoas',
			tep.VALOR_AB AS 'Valor AB',
			tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
			tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
			tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
			tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
			tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
			tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
			tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
			tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
			tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
			tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
			tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
			tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
			tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
			tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
			tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
			tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
			tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
			tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
			tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
			tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
			tep.VALOR_IMPOSTO AS 'Valor Imposto',
			tsep.DESCRICAO AS 'Status Evento',
			tep.OBSERVACOES AS 'Observações',
			temd.DESCRICAO AS 'Motivo Declínio',
			tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
		FROM ZLOG_T_EVENTOS_PRICELESS tep 
			INNER JOIN ADMIN_USERS au ON (tep.LOG_USER = au.ID)
			LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	''')


def GET_EVENTOS_CONFIRMADOS():
	return dataframe_query('''
		SELECT
			tep.ID AS 'ID Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tee.NOME_COMPLETO AS 'Comercial Responsável',
			tep.NOME_EVENTO AS 'Nome Evento',
			trec.NOME AS 'Cliente',
			tep.DATA_CONTRATACAO AS 'Data Contratação',
			tep.DATA_EVENTO AS 'Data Evento',
			tte.DESCRICAO AS 'Tipo Evento',
			tme.DESCRICAO AS 'Modelo Evento',
			tse.DESCRICAO AS 'Segmento Evento',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
			tep.NUM_CLIENTES AS 'Num Pessoas',
			tep.VALOR_AB AS 'Valor AB',
			tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
			tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
			tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
			tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
			tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
			tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
			tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
			tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
			tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
			tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
			tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
			tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
			tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
			tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
			tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
			tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
			tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
			tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
			tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
			tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
			tep.VALOR_IMPOSTO AS 'Valor Imposto',
			tsep.DESCRICAO AS 'Status Evento',
			tep.OBSERVACOES AS 'Observações',
			temd.DESCRICAO AS 'Motivo Declínio',
			tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
		WHERE tsep.DESCRICAO = 'Confirmado'
	''')


def GET_LOGS_PARCELAS_EVENTOS():
	return dataframe_query('''
		SELECT
			tep.ID as 'ID Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			ztpep.ID as 'ID Parcela',
			ztpep.LOG_DATE as 'Data/Hora Log',
			DATE(ztpep.LOG_DATE) as 'Data Log',
			au.FULL_NAME as 'Nome Usuário',
			au.EMAIL as 'Email Usuário',
			tep.NOME_EVENTO as 'Nome do Evento',
			tcep.DESCRICAO as 'Categoria Parcela',
			ztpep.VALOR_PARCELA as 'Valor Parcela',
			ztpep.DATA_VENCIMENTO_PARCELA as 'Data Vencimento',
			tsp.DESCRICAO as 'Status Pagamento',
			ztpep.DATA_RECEBIMENTO_PARCELA as 'Data Recebimento',
			tcb.NOME_DA_CONTA as 'Conta Bancária',
			tfdp.DESCRICAO AS 'Forma de Pagamento'
		FROM ZLOG_T_PARCELAS_EVENTOS_PRICELESS ztpep
			INNER JOIN ADMIN_USERS au ON (ztpep.LOG_USER = au.ID)
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (ztpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_EMPRESAS te ON tep.FK_EMPRESA = te.ID
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (ztpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (ztpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_CONTAS_BANCARIAS tcb ON tcb.ID = ztpep.FK_CONTA_BANCARIA	
			LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON tfdp.ID = ztpep.FK_FORMA_PAGAMENTO 
	''')


def GET_DATETIME_CONFIRMACAO_EVENTOS():
	return dataframe_query('''
		SELECT
			t.ID_Evento AS 'ID Evento',
			t.LOG_DATE AS 'Data Confirmação'
		FROM (
			SELECT
				tep.ID AS ID_Evento,
				tep.LOG_DATE,
				tep.FK_STATUS_EVENTO,
				LAG(tep.FK_STATUS_EVENTO) OVER (
					PARTITION BY tep.ID 
					ORDER BY tep.LOG_DATE
				) AS Status_Anterior
			FROM ZLOG_T_EVENTOS_PRICELESS tep
		) t
		WHERE t.FK_STATUS_EVENTO = 101
		AND (t.Status_Anterior IS NULL OR t.Status_Anterior <> 101)
		ORDER BY t.ID_Evento, t.LOG_DATE
	''')

@st.cache_data
def GET_EVENTOS_CONCIERGE():
   	return dataframe_query(f'''
	SELECT 
		CONCAT('C-', tep.ID) AS 'ID Evento',
		CASE 
			WHEN te.NOME_FANTASIA = 'Terraço Notie' THEN 'Priceless'
			ELSE te.NOME_FANTASIA
		END AS `Casa`,
		CASE 
			WHEN te.NOME_FANTASIA = 'Terraço Notie' THEN 149
			ELSE te.ID
		END AS `ID Casa`,
		tc.NOME AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_CONCIERGE tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_CONCIERGES tc ON (tc.ID = tep.FK_CONCIERGE)
	''')

@st.cache_data
def GET_PARCELAS_EVENTOS_CONCIERGE():
   	return dataframe_query(f'''
		SELECT
			CONCAT('C-', tpep.ID) AS 'ID Parcela',
			CONCAT('C-', tpep.FK_EVENTO_CONCIERGE) AS 'ID Evento',
			CASE 
				WHEN te.NOME_FANTASIA = 'Terraço Notie' THEN 'Priceless'
				ELSE te.NOME_FANTASIA
			END AS Casa,
			CASE 
				WHEN te.NOME_FANTASIA = 'Terraço Notie' THEN 149
				ELSE te.ID
			END AS `ID Casa`,
			tep.NOME_EVENTO AS 'Nome Evento',
			tsep.DESCRICAO AS 'Status Evento',
			tcep.DESCRICAO AS 'Categoria Parcela',
			tpep.VALOR_PARCELA as 'Valor Parcela',
			tpep.DATA_VENCIMENTO_PARCELA AS 'Data Vencimento',
			tsp.DESCRICAO AS 'Status Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA AS 'Data Recebimento' 
		FROM T_PARCELAS_EVENTOS_CONCIERGE tpep 
			LEFT JOIN T_EVENTOS_CONCIERGE tep ON (tpep.FK_EVENTO_CONCIERGE = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
		ORDER BY `ID Casa` DESC, tpep.ID DESC
	''')

@st.cache_data
def GET_ORCAMENTOS_EVENTOS_CONCIERGE():
	return dataframe_query(f'''
		SELECT 
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			to2.ANO AS 'Ano',
			to2.MES AS 'Mês',
			CASE
				WHEN tccg2.DESCRICAO = 'Eventos A&B' THEN 'A&B'
				WHEN tccg2.DESCRICAO = 'Eventos Couvert' THEN 'Couvert'
				WHEN tccg2.DESCRICAO = 'Eventos Locações' THEN 'Locação'
				WHEN tccg2.DESCRICAO = 'Eventos Rebate Fornecedores' THEN 'Repasse Fornecedores'
			END AS 'Categoria Orcamento',
			to2.VALOR AS 'Valor'
		FROM T_ORCAMENTOS_META_EVENTOS_CONCIERGE to2
			INNER JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON to2.FK_CLASSIFICACAO_1 = tccg.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
		WHERE tccg.DESCRICAO = 'Faturamento Bruto' AND tccg2.ID IN (939, 940, 942, 943)
		GROUP BY te.NOME_FANTASIA, to2.ANO, to2.MES, to2.FK_CLASSIFICACAO_2
	''')
