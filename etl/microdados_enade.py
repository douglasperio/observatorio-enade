"""
Resume os microdados do Enade (INEP) em notas por curso, para médias exatas de
Formação Geral (FG), Componente Específico (CE) e Resultado Geral.

Uso:
    python etl/microdados_enade.py <pasta com os arquivos baixados do INEP>

A pasta deve conter os arquivos como o INEP distribui (microdados_enade_AAAA*.zip ou .rar;
o .rar precisa ser extraído antes numa subpasta "extraido_AAAA"). Os arquivos não precisam
ficar guardados depois: o resultado vai para dados/notas_microdados.parquet (poucos MB).

Para cada curso e ano grava: nº de estudantes presentes com prova válida e as somas das notas.
Com somas e contagens, o app calcula médias de estudantes (curso, UF, região, Brasil) idênticas
às dos Relatórios do INEP.

Critério do INEP para "presentes": TP_PRES = 555 (presente) e TP_PR_GER = 555 (prova válida).
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "notas_microdados.parquet"

COLS_CURSO = ["CO_CURSO", "CO_IES", "CO_CATEGAD", "CO_ORGACAD", "CO_GRUPO", "CO_MODALIDADE",
              "CO_MUNIC_CURSO", "CO_UF_CURSO", "CO_REGIAO_CURSO"]
COLS_NOTA = ["CO_CURSO", "TP_PRES", "TP_PR_GER", "NT_GER", "NT_FG", "NT_CE"]


def localizar(pasta: Path, ano: int, arq: str):
    """Abre o arquivo arqN do ano, dentro do zip ou da pasta extraída."""
    for z in pasta.glob(f"microdados_enade_{ano}*.zip"):
        zf = zipfile.ZipFile(z)
        nome = next(n for n in zf.namelist() if re.search(rf"_{arq}\.txt$", n))
        return zf.open(nome)
    extraido = pasta / f"extraido_{ano}"
    caminho = next(extraido.rglob(f"*_{arq}.txt"))
    return open(caminho, "rb")


def ler(pasta, ano, arq, cols):
    with localizar(pasta, ano, arq) as h:
        return pd.read_csv(h, sep=";", usecols=cols, decimal=",", encoding="latin-1", low_memory=False)


def resumir_ano(pasta: Path, ano: int) -> pd.DataFrame:
    cursos = ler(pasta, ano, "arq1", COLS_CURSO).drop_duplicates("CO_CURSO")
    notas = ler(pasta, ano, "arq3", COLS_NOTA)
    for c in ("NT_GER", "NT_FG", "NT_CE"):
        notas[c] = pd.to_numeric(notas[c], errors="coerce")
    validos = notas[(notas["TP_PRES"] == 555) & (notas["TP_PR_GER"] == 555)]
    g = validos.groupby("CO_CURSO").agg(
        n=("NT_GER", "size"),
        n_ger=("NT_GER", "count"), soma_ger=("NT_GER", "sum"),
        n_fg=("NT_FG", "count"), soma_fg=("NT_FG", "sum"),
        n_ce=("NT_CE", "count"), soma_ce=("NT_CE", "sum"),
    ).reset_index()
    inscritos = notas.groupby("CO_CURSO").size().rename("inscritos_micro").reset_index()
    out = cursos.merge(g, on="CO_CURSO", how="left").merge(inscritos, on="CO_CURSO", how="left")
    out.insert(0, "ano", ano)
    print(f"{ano}: {len(out):>6} cursos | {int(out['n'].sum()):>8} estudantes presentes com prova válida")
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    pasta = Path(sys.argv[1])
    anos = sorted({int(m.group(1)) for p in pasta.iterdir() if (m := re.match(r"microdados_enade_(\d{4})", p.name))}
                  | {int(m.group(1)) for p in pasta.iterdir() if (m := re.match(r"extraido_(\d{4})", p.name))})
    partes = [resumir_ano(pasta, a) for a in anos]
    df = pd.concat(partes, ignore_index=True)
    df.columns = [c.lower() for c in df.columns]
    for c in ("co_curso", "co_ies", "co_grupo", "co_munic_curso"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64").astype("string")
    if SAIDA.exists():  # mantém anos já resumidos que não estão na pasta atual
        antigo = pd.read_parquet(SAIDA)
        df = pd.concat([antigo[~antigo["ano"].isin(df["ano"])], df], ignore_index=True)
    df.to_parquet(SAIDA, index=False)
    print(f"\nGravado: {SAIDA} ({len(df)} linhas, anos {sorted(df['ano'].unique())})")


if __name__ == "__main__":
    sys.exit(main())
