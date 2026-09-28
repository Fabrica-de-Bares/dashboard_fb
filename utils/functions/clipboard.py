import re
from decimal import Decimal

import numpy as np
import pandas as pd


# Textos já formatados no padrão BR, ex.: "R$ 1.234,56", "R$ -10,00", "1.234,56", "-0,5"
# Sem "R$", exige vírgula decimal para não confundir com códigos/IDs como "1.234"
_RE_MOEDA_BR = re.compile(r'^\s*(-?)\s*R\$\s*(-?)\s*(\d{1,3}(?:\.\d{3})*|\d+)(,\d+)?\s*$')
_RE_NUMERO_BR = re.compile(r'^\s*(-?)(\d{1,3}(?:\.\d{3})+|\d+),(\d+)\s*$')


def _valor_para_planilha(x):
    # Converte um valor para texto que a planilha (pt-BR) reconhece como número:
    # sem separador de milhar, vírgula decimal e sem notação científica
    if x is None or isinstance(x, bool):
        return x
    if isinstance(x, Decimal):
        if not x.is_finite():
            return ''
        return format(x, 'f').replace('.', ',')
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, (float, np.floating)):
        if not np.isfinite(x):
            return ''
        # Arredonda para eliminar ruído de ponto flutuante (ex.: 0.30000000000000004)
        return np.format_float_positional(round(float(x), 10), trim='-').replace('.', ',')
    if isinstance(x, str):
        m = _RE_MOEDA_BR.match(x)
        if m:
            sinal = '-' if (m.group(1) or m.group(2)) else ''
            return f"{sinal}{m.group(3).replace('.', '')}{m.group(4) or ''}"
        m = _RE_NUMERO_BR.match(x)
        if m:
            return f"{m.group(1)}{m.group(2).replace('.', '')},{m.group(3)}"
    return x


def dataframe_to_tsv_planilha(df: pd.DataFrame) -> str:
    # Gera o TSV para colar na planilha com números prontos para cálculo
    df_copy = pd.DataFrame(
        {i: df.iloc[:, i].astype(object).map(_valor_para_planilha) for i in range(df.shape[1])},
        index=df.index,
    )
    df_copy.columns = df.columns
    return df_copy.to_csv(index=False, sep='\t')
