"""
Consolida as planilhas oficiais do INEP (CPC, IGC e Enade 2025) em bases únicas.

Uso:
    python etl/consolidar.py

Os arquivos são descobertos automaticamente pelo ano no nome (ex.: "CPC 2019 - ok.xlsx"):
    ../Resultados/Resultados CPC/        -> CPC (um ano por arquivo)
    ../Resultados/Resultados IGC/        -> IGC (todas as abas de IES são juntadas)
    ../Resultados/Enade Licenciaturas/   -> Conceito Enade das licenciaturas (2025 em diante)
    ../Resultados/Enade Medicina/        -> Conceito Enade de Medicina (2025 em diante)

A aba certa de cada arquivo também é encontrada sozinha (a que tem as colunas esperadas e mais linhas).

Grava em dados/:
    cpc.parquet     -> um registro por curso avaliado em cada ano
    igc.parquet     -> um registro por IES em cada ano
    enade_novo.parquet -> um registro por curso nas avaliações novas (licenciaturas / medicina)
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RESULTADOS = RAIZ.parent / "Resultados"
SAIDA = RAIZ / "dados"

PASTA_CPC = RESULTADOS / "Resultados CPC"
PASTA_IGC = RESULTADOS / "Resultados IGC"
PASTAS_ENADE_NOVO = {
    "licenciaturas": RESULTADOS / "Enade Licenciaturas",
    "medicina": RESULTADOS / "Enade Medicina",
}

UF_REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}
UF_NOME = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA", "CEARA": "CE",
    "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA", "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP",
    "SERGIPE": "SE", "TOCANTINS": "TO",
}


def norm(txt) -> str:
    """minúsculas, sem acento, sem pontuação, espaços simples."""
    s = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9%]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def nota(h, *termos):
    """Cabeçalho de nota padronizada (não bruta, não percentual) contendo um dos termos."""
    return (h.startswith("nota") or "padronizada" in h) and "bruta" not in h and any(t in h for t in termos)


# Cada coluna padronizada -> função que reconhece o cabeçalho normalizado.
# A ordem importa: a primeira regra que casar vence; cada alvo é usado uma vez.
REGRAS_CPC = [
    ("ano", lambda h: h in ("ano", "ano enade")),
    ("cod_area", lambda h: h.startswith("cod") and "area" in h),
    ("area", lambda h: "area" in h and not h.startswith("cod")),
    ("cod_ies", lambda h: h.startswith("cod") and "ies" in h),
    ("ies_nome", lambda h: (h.startswith("nome") and "ies" in h) or h == "ies"),
    ("ies_sigla", lambda h: (h.startswith("sigla") and "ies" in h) or h == "sigla"),
    ("org_academica", lambda h: h.startswith("org")),
    ("cat_administrativa", lambda h: h.startswith("categ")),
    ("cod_curso", lambda h: h.startswith("codigo do curso")),
    ("n_cursos_unidade", lambda h: h.startswith(("nr cursos", "numero cursos", "numero de cursos"))),
    ("modalidade", lambda h: h.startswith("modalidade")),
    ("cod_municipio", lambda h: h.startswith("cod") and "municipio" in h),
    ("municipio", lambda h: h.startswith("municipio")),
    ("uf", lambda h: h.startswith(("uf", "sigla da uf", "sigla uf"))),
    ("regiao_orig", lambda h: h.startswith("regiao")),
    ("inscritos", lambda h: "inscritos" in h and ("conclu" in h or "conluintes" in h)),
    ("participantes_nota", lambda h: "com nota" in h),
    ("participantes", lambda h: "participantes" in h and "conclu" in h and "proporcao" not in h),
    ("prop_participantes_nota", lambda h: h.startswith("proporcao") and "conclu" in h),
    ("fg_bruta", lambda h: h in ("nota bruta fg", "media fg conc", "nota bruta de formacao geral")),
    ("fg_padronizada", lambda h: h in ("nota padronizada fg", "nota padronizada de formacao geral")),
    ("ce_bruta", lambda h: h in ("nota bruta ce", "media ce conc", "nota bruta de componente especifico")),
    ("ce_padronizada", lambda h: h in ("nota padronizada ce", "nota padronizada de componente especific")),
    ("geral_bruta", lambda h: h == "nota bruta geral"),
    ("enade_faixa_orig", lambda h: h == "conceito enade faixa"),
    ("enade_continuo", lambda h: ("enade" in h and "continu" in h) or h in ("nota enade concluintes", "nota de concluintes")),
    ("idd_bruta", lambda h: h.startswith("nota bruta") and "idd" in h),
    ("idd", lambda h: nota(h, "idd")),
    ("odp_bruta", lambda h: h.startswith("nota bruta") and "org" in h),
    ("odp", lambda h: nota(h, "org", "pedag")),
    ("infra_bruta", lambda h: h.startswith("nota bruta") and "infra" in h),
    ("infra", lambda h: nota(h, "infra")),
    ("oaf_bruta", lambda h: h.startswith("nota bruta") and "oport" in h),
    ("oaf", lambda h: nota(h, "oport")),
    ("mestres_bruta", lambda h: (h.startswith("nota bruta") and "mestres" in h) or h == "% de mestres"),
    ("mestres", lambda h: nota(h, "mestr")),
    ("doutores_bruta", lambda h: (h.startswith("nota bruta") and "doutores" in h) or h == "% de doutores"),
    ("doutores", lambda h: nota(h, "doutor")),
    ("regime_bruta", lambda h: (h.startswith("nota bruta") and "regime" in h) or h.startswith(("% regime", "% de regime"))),
    ("regime", lambda h: nota(h, "regime")),
    ("cpc_continuo", lambda h: h.startswith("cpc") and "continuo" in h),
    ("cpc_faixa", lambda h: h.startswith("cpc") and "faixa" in h),
    ("observacao", lambda h: h.startswith("observ")),
]

REGRAS_IGC = [
    ("cod_ies", lambda h: (h.startswith("cod") and "ies" in h) or h == "co ies"),
    ("ies_nome", lambda h: (h.startswith("nome") and "ies" in h) or h in ("ies", "no ies")),
    ("ies_sigla", lambda h: (h.startswith("sigla") and "ies" in h) or h in ("sigla", "sg ies")),
    ("org_academica", lambda h: h.startswith("org") or h == "no orgacad"),
    ("cat_administrativa", lambda h: h.startswith(("categ", "dependencia")) or h == "no categad"),
    ("uf", lambda h: h.startswith(("uf", "sigla da uf")) or h == "sg uf"),
    ("n_cursos_cpc", lambda h: "cursos com cpc" in h or "cursos cpc" in h),
    ("alfa", lambda h: h.startswith("alfa") or "graduandos" in h),
    ("conceito_graduacao", lambda h: ("medio" in h and "gradua" in h) or h == "g ies"),
    ("beta", lambda h: h.startswith("beta") or "mestrandos" in h),
    ("conceito_mestrado", lambda h: ("medio" in h and "mestrado" in h) or h == "m"),
    ("gama", lambda h: h.startswith("gama") or "doutorandos" in h),
    ("conceito_doutorado", lambda h: ("medio" in h and "doutorado" in h) or h == "d"),
    ("igc_continuo", lambda h: (h.startswith("igc") and "continuo" in h) or h == "igc"),
    ("igc_faixa", lambda h: (h.startswith("igc") and "faixa" in h) or h == "fx igc"),
]

REGRAS_ENADE_NOVO = [
    ("ano", lambda h: h == "ano"),
    ("cod_area", lambda h: h.startswith("cod") and "area" in h),
    ("area", lambda h: "area" in h and not h.startswith("cod")),
    ("grau", lambda h: h.startswith("grau")),
    ("cod_ies", lambda h: h.startswith("cod") and "ies" in h),
    ("ies_nome", lambda h: h.startswith("nome") and "ies" in h),
    ("ies_sigla", lambda h: h.startswith("sigla") and "ies" in h),
    ("org_academica", lambda h: h.startswith("org")),
    ("cat_administrativa", lambda h: h.startswith("categ")),
    ("cod_curso", lambda h: h.startswith("codigo do curso")),
    ("modalidade", lambda h: h.startswith("modalidade")),
    ("cod_municipio", lambda h: h.startswith("cod") and "municipio" in h),
    ("municipio", lambda h: h.startswith("municipio")),
    ("uf", lambda h: h.startswith(("uf", "sigla da uf"))),
    ("inscritos", lambda h: "inscritos" in h and "conclu" in h),
    ("participantes", lambda h: "participantes" in h and "conclu" in h),
    ("n_acima", lambda h: h.startswith("total")),
    ("pct_acima", lambda h: h.startswith("percentual")),
    ("enade_faixa", lambda h: "conceito enade" in h and "faixa" in h),
    ("cebas", lambda h: h.startswith("cebas")),
]

NUMERICAS_CPC = [
    "inscritos", "participantes", "participantes_nota", "prop_participantes_nota",
    "fg_bruta", "fg_padronizada", "ce_bruta", "ce_padronizada", "geral_bruta", "enade_continuo",
    "idd_bruta", "idd", "odp_bruta", "odp", "infra_bruta", "infra", "oaf_bruta", "oaf",
    "mestres_bruta", "mestres", "doutores_bruta", "doutores", "regime_bruta", "regime", "cpc_continuo",
]
NUMERICAS_IGC = [
    "n_cursos_cpc", "alfa", "conceito_graduacao", "beta", "conceito_mestrado",
    "gama", "conceito_doutorado", "igc_continuo",
]


# ---------------------------------------------------------------- leitura
def descobrir(pasta: Path) -> dict[int, Path]:
    """{ano: arquivo} para as planilhas da pasta com exatamente um ano (20xx) no nome."""
    achados: dict[int, list[Path]] = {}
    if not pasta.exists():
        return {}
    for p in pasta.iterdir():
        if p.suffix.lower() not in (".xls", ".xlsx") or p.name.startswith("~$"):
            continue
        anos = set(re.findall(r"(?<!\d)(20\d{2})(?!\d)", p.stem))
        if len(anos) == 1:
            achados.setdefault(int(anos.pop()), []).append(p)
    escolhidos = {}
    for ano, arqs in sorted(achados.items()):
        arqs.sort(key=lambda a: a.stat().st_mtime, reverse=True)
        if len(arqs) > 1:
            print(f"  ! {ano}: {len(arqs)} arquivos na pasta {pasta.name}; usando o mais recente: {arqs[0].name}")
        escolhidos[ano] = arqs[0]
    return escolhidos


def mapear_colunas(df: pd.DataFrame, regras) -> pd.DataFrame:
    novos, usados = {}, set()
    for col in df.columns:
        h = norm(col)
        for alvo, teste in regras:
            if alvo not in usados and teste(h):
                novos[col] = alvo
                usados.add(alvo)
                break
    return df[list(novos)].rename(columns=novos)


def abas_validas(arquivo: Path, regras, obrigatorias: set[str]) -> list[tuple[str, pd.DataFrame]]:
    """Abas cujo cabeçalho contém as colunas obrigatórias (já com colunas padronizadas)."""
    todas = pd.read_excel(arquivo, sheet_name=None)
    validas = []
    for nome, df in todas.items():
        m = mapear_colunas(df, regras)
        if obrigatorias <= set(m.columns):
            validas.append((nome, m))
    return validas


# ---------------------------------------------------------------- utilitários
def numero(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def inteiro_txt(s: pd.Series) -> pd.Series:
    """Códigos (IES, curso, município) como texto sem '.0'."""
    n = pd.to_numeric(s, errors="coerce")
    return n.map(lambda v: "" if pd.isna(v) else str(int(v))).astype("string")


def faixa_enade(x: float):
    """Faixa do Conceito Enade a partir da nota contínua (regra INEP)."""
    if pd.isna(x):
        return "SC"
    if x < 0.945:
        return "1"
    if x < 1.945:
        return "2"
    if x < 2.945:
        return "3"
    if x < 3.945:
        return "4"
    return "5"


def faixa_texto(s: pd.Series) -> pd.Series:
    """Faixa 1–5 como texto; qualquer outra coisa (vazio, 'SC', observações) vira 'SC'."""
    def f(v):
        try:
            n = int(float(str(v).strip()))
            return str(n) if 1 <= n <= 5 else "SC"
        except ValueError:
            return "SC"
    return s.map(f)


def limpar_nome(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.upper()


def sigla_uf(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.strip().str.upper()
    return t.map(lambda v: v if pd.isna(v) or len(v) == 2 else UF_NOME.get(norm(v).upper(), v)).astype("string")


# Nomes antigos (2010–2012) ou variantes -> nome usado nas edições recentes.
ALIAS_AREA = {
    "ENGENHARIA DA COMPUTAÇÃO": "ENGENHARIA DE COMPUTAÇÃO",
    "ENGENHARIA DE COMPUTAÇÃO I": "ENGENHARIA DE COMPUTAÇÃO",
    "BIOLOGIA (BACHARELADO)": "CIÊNCIAS BIOLÓGICAS (BACHARELADO)",
    "BIOLOGIA (LICENCIATURA)": "CIÊNCIAS BIOLÓGICAS (LICENCIATURA)",
    "COMPUTAÇÃO (BACHARELADO)": "CIÊNCIA DA COMPUTAÇÃO (BACHARELADO)",
    "COMPUTAÇÃO (LICENCIATURA)": "CIÊNCIA DA COMPUTAÇÃO (LICENCIATURA)",
    "COMPUTAÇÃO (SISTEMAS DE INFORMAÇÃO)": "SISTEMAS DE INFORMAÇÃO",
    "COMPUTAÇÃO (ENGENHARIA DE COMPUTAÇÃO)": "ENGENHARIA DE COMPUTAÇÃO",
    "LETRAS-INGLÊS": "LETRAS-INGLÊS (LICENCIATURA)",
}


def normalizar_area(a: str) -> str:
    a = re.sub(r"\s+", " ", str(a).strip().upper())
    a = a.replace("( ", "(").replace(" )", ")")
    # 2010–2012: "ENGENHARIA (GRUPO I) - ENGENHARIA CIVIL" -> "ENGENHARIA CIVIL"
    m = re.match(r"ENGENHARIA \(GRUPO [IVX]+\) - (.+)", a)
    if m:
        a = m.group(1)
    a = re.sub(r"\s*-\s*", "-", a)
    return ALIAS_AREA.get(a, a)


def normalizar_modalidade(s: pd.Series) -> pd.Series:
    def f(m):
        t = norm(m)
        if "dist" in t or t == "ead":
            return "Educação a Distância"
        return "Educação Presencial"
    return s.map(f)


# ---------------------------------------------------------------- CPC
def consolidar_cpc() -> pd.DataFrame:
    partes = []
    for ano, arq in descobrir(PASTA_CPC).items():
        validas = abas_validas(arq, REGRAS_CPC, {"area", "ies_nome", "cpc_continuo"})
        if not validas:
            print(f"  ! CPC {ano}: nenhuma aba reconhecida em {arq.name}; arquivo ignorado")
            continue
        aba, df = max(validas, key=lambda v: len(v[1]))
        df = df[df["ies_nome"].notna() & df["area"].notna()].copy()
        df["ano"] = ano
        df = df.drop_duplicates()  # a planilha de 2017 traz cada curso duas vezes
        df["arquivo_origem"] = arq.name
        print(f"CPC {ano}: {len(df):>6} linhas  ← {arq.name} [{aba}]")
        partes.append(df)
    cpc = pd.concat(partes, ignore_index=True)

    for c in NUMERICAS_CPC:
        cpc[c] = numero(cpc[c]) if c in cpc else np.nan
    for c in ("cod_ies", "cod_curso", "cod_area", "cod_municipio"):
        cpc[c] = inteiro_txt(cpc[c]) if c in cpc else pd.Series("", index=cpc.index, dtype="string")
    for c in ("ies_nome", "ies_sigla", "municipio", "org_academica", "cat_administrativa", "modalidade", "observacao"):
        if c not in cpc:
            cpc[c] = pd.NA
        cpc[c] = cpc[c].astype("string").str.strip()
    cpc["ies_nome"] = limpar_nome(cpc["ies_nome"])
    cpc["municipio"] = limpar_nome(cpc["municipio"])
    cpc["uf"] = sigla_uf(cpc["uf"])
    cpc["regiao"] = cpc["uf"].map(UF_REGIAO)
    cpc["area"] = cpc["area"].map(normalizar_area)
    cpc["modalidade"] = normalizar_modalidade(cpc["modalidade"])

    cpc["cpc_faixa"] = faixa_texto(cpc["cpc_faixa"])
    # Faixa do Enade: a oficial quando a planilha traz (2010–2011); senão, calculada da nota contínua.
    derivada = cpc["enade_continuo"].map(faixa_enade)
    if "enade_faixa_orig" in cpc:
        oficial = faixa_texto(cpc["enade_faixa_orig"])
        cpc["enade_faixa"] = oficial.where(cpc["enade_faixa_orig"].notna(), derivada)
        cpc = cpc.drop(columns="enade_faixa_orig")
    else:
        cpc["enade_faixa"] = derivada
    cpc["taxa_participacao"] = cpc["participantes"] / cpc["inscritos"]
    return cpc


# ---------------------------------------------------------------- IGC
def consolidar_igc() -> pd.DataFrame:
    partes = []
    for ano, arq in descobrir(PASTA_IGC).items():
        validas = abas_validas(arq, REGRAS_IGC, {"cod_ies", "ies_nome", "igc_continuo"})
        if not validas:
            print(f"  ! IGC {ano}: nenhuma aba reconhecida em {arq.name}; arquivo ignorado")
            continue
        df = pd.concat([d for _, d in validas], ignore_index=True)
        df = df[pd.to_numeric(df["cod_ies"], errors="coerce").notna()].copy()
        df["ano"] = ano
        print(f"IGC {ano}: {len(df):>6} linhas  ← {arq.name} [{', '.join(n for n, _ in validas)}]")
        partes.append(df)
    igc = pd.concat(partes, ignore_index=True)
    for c in NUMERICAS_IGC:
        igc[c] = numero(igc[c]) if c in igc else np.nan
    igc["cod_ies"] = inteiro_txt(igc["cod_ies"])
    igc["ies_nome"] = limpar_nome(igc["ies_nome"])
    for c in ("ies_sigla", "org_academica", "cat_administrativa"):
        igc[c] = igc[c].astype("string").str.strip()
    igc["uf"] = sigla_uf(igc["uf"])
    igc["regiao"] = igc["uf"].map(UF_REGIAO)
    igc["igc_faixa"] = faixa_texto(igc["igc_faixa"])
    igc = igc.drop_duplicates(["ano", "cod_ies"])
    return igc


# ---------------------------------------------------------------- Enade das licenciaturas / Medicina
def consolidar_enade_novo() -> pd.DataFrame:
    partes = []
    for programa, pasta in PASTAS_ENADE_NOVO.items():
        for ano, arq in descobrir(pasta).items():
            validas = abas_validas(arq, REGRAS_ENADE_NOVO, {"area", "ies_nome", "enade_faixa"})
            if not validas:
                print(f"  ! Enade {programa} {ano}: nenhuma aba reconhecida em {arq.name}")
                continue
            aba, df = max(validas, key=lambda v: len(v[1]))
            df = df[df["ies_nome"].notna() & pd.to_numeric(df["ano"], errors="coerce").notna()].copy()
            df["ano"] = ano
            df["programa"] = programa
            print(f"Enade {programa} {ano}: {len(df):>6} linhas  ← {arq.name} [{aba}]")
            partes.append(df)
    if not partes:
        return pd.DataFrame()
    e = pd.concat(partes, ignore_index=True)
    for c in ("inscritos", "participantes", "n_acima", "pct_acima"):
        e[c] = numero(e[c])
    for c in ("cod_ies", "cod_curso", "cod_area", "cod_municipio"):
        e[c] = inteiro_txt(e[c])
    e["ies_nome"] = limpar_nome(e["ies_nome"])
    e["municipio"] = limpar_nome(e["municipio"])
    for c in ("ies_sigla", "org_academica", "cat_administrativa"):
        e[c] = e[c].astype("string").str.strip()
    e["uf"] = sigla_uf(e["uf"])
    e["regiao"] = e["uf"].map(UF_REGIAO)
    e["modalidade"] = normalizar_modalidade(e["modalidade"])
    # Área no mesmo padrão das planilhas de CPC: "MATEMÁTICA (LICENCIATURA)".
    area = e["area"].map(normalizar_area)
    grau = e.get("grau", pd.Series("", index=e.index)).fillna("").astype(str).str.strip().str.upper()
    e["area"] = [a if (g != "LICENCIATURA" or "(" in a) else f"{a} (LICENCIATURA)" for a, g in zip(area, grau)]
    e["enade_faixa"] = faixa_texto(e["enade_faixa"])
    e["taxa_participacao"] = e["participantes"] / e["inscritos"]
    e["ies_id"] = e["cod_ies"]
    e["curso_chave"] = e["ies_id"] + "|" + e["area"] + "|" + e["municipio"].fillna("").map(norm) + "|" + e["modalidade"].map(norm)
    return e


# ---------------------------------------------------------------- cruzamentos
def completar_ies(cpc: pd.DataFrame, igc: pd.DataFrame) -> pd.DataFrame:
    """Preenche o código da IES pelo nome e padroniza categoria/organização pela informação mais recente."""
    ref = pd.concat([
        cpc.loc[cpc["cod_ies"] != "", ["ano", "ies_nome", "cod_ies", "cat_administrativa", "org_academica"]],
        igc[["ano", "ies_nome", "cod_ies", "cat_administrativa", "org_academica"]],
    ])
    por_nome = ref.sort_values("ano").drop_duplicates("ies_nome", keep="last").set_index("ies_nome")

    sem_cod = cpc["cod_ies"] == ""
    cpc.loc[sem_cod, "cod_ies"] = cpc.loc[sem_cod, "ies_nome"].map(por_nome["cod_ies"]).fillna("")

    # Categoria e organização: a classificação mais recente da IES (os anos antigos usam outros nomes).
    por_cod = ref.dropna(subset=["cat_administrativa"]).sort_values("ano").drop_duplicates("cod_ies", keep="last").set_index("cod_ies")
    for c in ("cat_administrativa", "org_academica"):
        novo = cpc["cod_ies"].map(por_cod[c])
        cpc[c] = novo.where(novo.notna(), cpc[c])
        novo_igc = igc["cod_ies"].map(por_cod[c])
        igc[c] = novo_igc.where(novo_igc.notna(), igc[c])

    # Identificador estável da IES: código quando existir; senão o próprio nome.
    cpc["ies_id"] = cpc["cod_ies"].where(cpc["cod_ies"] != "", "N:" + cpc["ies_nome"].fillna(""))
    recente = cpc.sort_values("ano").drop_duplicates("ies_id", keep="last").set_index("ies_id")
    cpc["ies_nome_atual"] = cpc["ies_id"].map(recente["ies_nome"])
    cpc["ies_sigla_atual"] = cpc["ies_id"].map(recente["ies_sigla"])

    # Chave para acompanhar o mesmo curso ao longo dos anos (o código do curso só existe a partir de 2016).
    cpc["curso_chave"] = (
        cpc["ies_id"] + "|" + cpc["area"] + "|" + cpc["municipio"].fillna("").map(norm) + "|" + cpc["modalidade"].map(norm)
    )

    sem = (cpc["cod_ies"] == "").sum()
    print(f"Registros CPC sem código de IES após cruzamento: {sem} ({sem / len(cpc):.1%})")
    return cpc


def main():
    SAIDA.mkdir(exist_ok=True)
    cpc = consolidar_cpc()
    igc = consolidar_igc()
    cpc = completar_ies(cpc, igc)
    novo = consolidar_enade_novo()

    igc["ies_id"] = igc["cod_ies"]
    cpc.to_parquet(SAIDA / "cpc.parquet", index=False)
    igc.to_parquet(SAIDA / "igc.parquet", index=False)
    print(f"\nGravado: cpc.parquet ({len(cpc)} linhas, {cpc['ano'].min()}–{cpc['ano'].max()})")
    print(f"Gravado: igc.parquet ({len(igc)} linhas, {igc['ano'].min()}–{igc['ano'].max()})")
    if not novo.empty:
        novo.to_parquet(SAIDA / "enade_novo.parquet", index=False)
        print(f"Gravado: enade_novo.parquet ({len(novo)} linhas)")


if __name__ == "__main__":
    sys.exit(main())
