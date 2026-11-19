"""Corte do Concierge nas tabelas padrão (Gabriel, 19/11/2026).

Até 18/11/2026 o Concierge lançava em T_EVENTOS_CONCIERGE / T_PARCELAS_EVENTOS_CONCIERGE.
Desde 19/11/2026 lança na BlueMe, em T_EVENTOS_PRICELESS com FK_CONCIERGE preenchido (casa 149),
e os eventos com data a partir do corte foram migrados para lá (UDF concierge/migrar-eventos).
As consultas do Concierge leem as duas fontes: a antiga só com DATA_EVENTO antes do corte, a
padrão com FK_CONCIERGE. O mesmo corte está na UDF e no warehouse, para nada contar em dobro.
"""
import pandas as pd

CORTE_CONCIERGE = '2026-11-19'


def juntar_concierge(novo, antigo):
	"""Eventos novos primeiro (datas a partir do corte), depois o histórico."""
	partes = [df for df in (novo, antigo) if df is not None and not df.empty]
	if not partes:
		return novo if novo is not None else antigo
	return pd.concat(partes, ignore_index=True)
