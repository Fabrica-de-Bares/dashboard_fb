import pandas as pd


# Tira o log igual ao imediatamente anterior da mesma chave (save sem alteração). Diferente do
# drop_duplicates, mantém a volta a um estado que já existiu, como a reconfirmação de um evento
# que o Financeiro liberou para edição. O df precisa vir ordenado pela chave e pela Data/Hora Log.
def remove_logs_repetidos_em_sequencia(df, chave, colunas):
	df = df.copy()
	valores = df[colunas].astype(str)
	anteriores = valores.shift()
	mesma_chave = df[chave].eq(df[chave].shift())
	repetido = mesma_chave & (valores == anteriores).all(axis=1)
	return df[~repetido]


# Remove logs de eventos com apenas o primeiro log (de confirmação)
def remove_logs_eventos_sem_alteração(df):
	df = df.copy()
	df_contador = df[['ID Evento', 'Data/Hora Log']].groupby('ID Evento').count()
	df_contador.rename(columns={'Data/Hora Log': 'Quantidade de Logs'}, inplace=True)

	df = df.merge(df_contador, how='left', on='ID Evento')
	df = df[df['Quantidade de Logs'] > 1]

	return df


def remove_logs_parcelas_sem_alteração(df):
    df = df.copy()
    df_contador = df[['ID Parcela', 'Data/Hora Log']].groupby('ID Parcela').count()
    df_contador.rename(columns={'Data/Hora Log': 'Quantidade de Logs'}, inplace=True)

    df = df.merge(df_contador, how='left', on='ID Parcela')
    df = df[df['Quantidade de Logs'] > 1]

    df = df.drop(['Quantidade de Logs'], axis=1)
    return df


def highlight_event_log_changes(df):
	df = df.reset_index(drop=True)

	# Convertendo colunas para o tipo correto
	if 'ID Casa' in df.columns:
		df["ID Casa"] = pd.to_numeric(df["ID Casa"], errors="coerce").astype("Int64")
		
	styles = pd.DataFrame('', index=df.index, columns=df.columns)
	for i in range(len(df)):
		if df.iloc[i]["Confirmação"] == 1:
			styles.iloc[i, :] = 'background-color: rgba(33, 195, 84, 0.1)'
		else:
			if i > 0:
				for col in df.columns:
					if col != "Confirmação":
						val_atual = df.loc[i, col]
						val_ant   = df.loc[i-1, col]
						# Comparação segura com tratamento de NA
						if (pd.isna(val_atual) and not pd.isna(val_ant)) or \
							(not pd.isna(val_atual) and pd.isna(val_ant)) or \
							(pd.notna(val_atual) and pd.notna(val_ant) and val_atual != val_ant):
							styles.loc[i, col] = 'background-color: rgba(255, 43, 43, 0.09)'

	# Remover colunas para visualização
	cols_remover = ["Confirmação", 'Quantidade de Logs']

	# Ordem das colunas
	primeiras_cols = ['ID Evento', 'Data/Hora Log', 'Data Confirmação']
	col_order = primeiras_cols + [col for col in df.columns if col not in primeiras_cols]
	df = df[col_order]

	return df.drop(columns=cols_remover).style.apply(lambda _: styles.drop(columns=cols_remover), axis=None)


def highlight_parcelas_log_changes(df):
	df = df.reset_index(drop=True)

	# Garante que ID Parcela seja numérico (se existir)
	if "ID Parcela" in df.columns:
		df["ID Parcela"] = pd.to_numeric(df["ID Parcela"], errors="coerce").astype("Int64")

	if 'ID Evento' in df.columns:
		df['ID Evento'] = pd.to_numeric(df['ID Evento'], errors="coerce").astype("Int64")

	if 'ID Casa' in df.columns:
		df['ID Casa'] = pd.to_numeric(df['ID Casa'], errors="coerce").astype("Int64")

	styles = pd.DataFrame('', index=df.index, columns=df.columns)

	for i in range(len(df)):
		if i == 0 or df.loc[i, "ID Parcela"] != df.loc[i-1, "ID Parcela"]:
			# Primeiro log da parcela → linha inteira verde
			styles.iloc[i, :] = 'background-color: rgba(33, 195, 84, 0.1)'
		else:
			# Para os demais logs, compara com a linha anterior da mesma parcela
			for col in df.columns:
				if col not in ["ID Parcela", "Data/Hora Log"]:
					val_atual = df.loc[i, col]
					val_ant   = df.loc[i-1, col]
					# Comparação segura tratando NaN
					if (pd.isna(val_atual) and not pd.isna(val_ant)) or \
					   (not pd.isna(val_atual) and pd.isna(val_ant)) or \
					   (pd.notna(val_atual) and pd.notna(val_ant) and val_atual != val_ant):
						styles.loc[i, col] = 'background-color: rgba(255, 43, 43, 0.09)'

	return df.style.apply(lambda _: styles, axis=None)