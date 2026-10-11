"""
Observatório ENADE — dashboard de Enade, CPC e IGC
Executar:  streamlit run app.py
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

DADOS = Path(__file__).parent / "dados"

st.set_page_config(page_title="Observatório ENADE", page_icon="🎓", layout="wide")

# ---------------------------------------------------------------- constantes
INDICADORES = [
    ("enade_continuo", "Conceito Enade"),
    ("idd", "IDD"),
    ("odp", "Org. didático-pedagógica"),
    ("infra", "Infraestrutura"),
    ("oaf", "Oport. de ampliação da formação"),
    ("mestres", "Mestres"),
    ("doutores", "Doutores"),
    ("regime", "Regime de trabalho"),
    ("cpc_continuo", "CPC contínuo"),
]

# Paleta categórica (ordem fixa) e rampa ordinal para faixas 1–5.
COR_SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
COR_CURSO, COR_UF, COR_BR = COR_SERIE[0], COR_SERIE[1], COR_SERIE[2]
FAIXAS = ["1", "2", "3", "4", "5", "SC"]
COR_FAIXA = {"1": "#86b6ef", "2": "#5598e7", "3": "#2a78d6", "4": "#1c5cab", "5": "#104281", "SC": "#c3c2b7"}
COR_NEUTRA = "#cfd3dc"
TINTA, TINTA_2, GRADE = "#0f1f3d", "#4a5670", "rgba(15,31,61,0.07)"
FONTE = "Instrument Sans, Segoe UI, sans-serif"

UNILAVRAS = "3372"

# ---------------------------------------------------------------- estilo
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400&family=Instrument+Sans:wght@400;500;600;700&display=swap');
:root{--ink:#0f1f3d;--ink-2:#4a5670;--muted:#7d8597;--paper:#f4f2ec;--card:#fff;--line:rgba(15,31,61,.09);
--accent:#2a78d6;--gold:#f0c46b;--shadow:0 1px 2px rgba(15,31,61,.04),0 14px 34px -22px rgba(15,31,61,.28)}
html,body,.stApp,.stApp p,.stApp label,.stApp li,.stApp input,.stApp button,.stApp textarea,[data-baseweb]{font-family:'Instrument Sans',sans-serif}
.stApp{background:radial-gradient(1100px 520px at 100% -8%,rgba(42,120,214,.10),transparent 60%),
radial-gradient(800px 400px at -10% 110%,rgba(240,196,107,.12),transparent 60%),var(--paper)}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stAppDeployButton"],#MainMenu,footer{display:none!important}
.block-container,[data-testid="stMainBlockContainer"]{padding-top:1.6rem!important;padding-bottom:3rem!important;max-width:1480px}

/* barra lateral */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1830 0%,#13305c 100%)!important;border-right:none}
section[data-testid="stSidebar"] *{color:#dbe3f1}
[data-testid="stSidebarNavLink"]{border-radius:12px;padding:9px 12px;margin:3px 0;transition:background .2s}
[data-testid="stSidebarNavLink"]:hover{background:rgba(255,255,255,.07)}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:rgba(255,255,255,.13);box-shadow:inset 3px 0 0 var(--gold)}
[data-testid="stSidebarNavLink"] span{font-size:15px;font-weight:500}
[data-testid="stNavSectionHeader"],[data-testid="stNavSectionHeader"] *{color:var(--gold)!important;font-size:11.5px!important;font-weight:700!important;
letter-spacing:.14em;text-transform:uppercase}
[data-testid="stNavSectionHeader"]{margin-top:10px!important;padding:8px 10px 8px 12px!important;border-radius:10px;cursor:pointer;
display:flex!important;align-items:center;justify-content:space-between;transition:background .2s}
[data-testid="stNavSectionHeader"]:hover{background:rgba(255,255,255,.07)}
[data-testid="stNavSectionHeader"]>div{opacity:1!important;visibility:visible!important;display:flex!important}
[data-testid="stNavSectionHeader"] [data-testid="stIconMaterial"]{font-size:20px!important;color:var(--gold)!important;letter-spacing:0}
.brand{display:flex;gap:12px;align-items:center;margin:18px 4px 6px;padding-top:18px;border-top:1px solid rgba(255,255,255,.12)}
.brand-mark{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:linear-gradient(135deg,var(--gold),#e39b2d);
color:#0b1830!important;font-family:Fraunces,serif;font-weight:700;font-size:22px}
.brand-t{font-family:Fraunces,serif;font-size:18px;font-weight:600;line-height:1.1;color:#fff!important}
.brand-s{font-size:12px;opacity:.65;margin-top:3px}
.side-note{font-size:12px;opacity:.6;margin:14px 4px;line-height:1.5}

/* cabeçalho */
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.hero{position:relative;overflow:hidden;border-radius:26px;padding:30px 36px 58px;color:#fff;animation:rise .55s ease both;
background:radial-gradient(520px 260px at 92% 0%,rgba(240,196,107,.30),transparent 62%),linear-gradient(130deg,#0b1830 0%,#173a6e 58%,#2a64b0 100%);
box-shadow:0 24px 48px -28px rgba(11,24,48,.75)}
.hero:before{content:"";position:absolute;inset:0;pointer-events:none;
background-image:linear-gradient(rgba(255,255,255,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.055) 1px,transparent 1px);
background-size:34px 34px;-webkit-mask-image:linear-gradient(100deg,transparent 25%,#000 85%);mask-image:linear-gradient(100deg,transparent 25%,#000 85%)}
.hero-num{position:absolute;right:26px;bottom:-40px;font-family:Fraunces,serif;font-weight:700;font-size:clamp(110px,13vw,200px);line-height:1;letter-spacing:-6px;
color:rgba(255,255,255,.08);pointer-events:none}
.hero .eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);font-weight:700}
.hero h1{font-family:Fraunces,serif!important;font-weight:600!important;font-size:clamp(30px,3.6vw,48px)!important;line-height:1.04!important;margin:8px 0 8px!important;
padding:0!important;color:#fff!important;letter-spacing:-.5px;max-width:960px}
.hero h1 em{font-style:italic;font-weight:400;color:var(--gold)}
.hero p{color:rgba(255,255,255,.78)!important;font-size:16px;margin:0;max-width:760px}
.chips{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
.chips span{padding:5px 12px;border-radius:999px;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);font-size:13px;backdrop-filter:blur(4px)}

/* filtros sobrepostos ao cabeçalho */
[class*="st-key-filtros"]{margin:-38px 22px 6px;width:calc(100% - 44px)!important;box-sizing:border-box;position:relative;z-index:2;
background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:18px;padding:14px 14px 6px;box-shadow:var(--shadow);animation:rise .6s .08s ease both}
[class*="st-key-painel"]{background:rgba(255,255,255,.88);border:1px solid var(--line);border-radius:18px;padding:14px 18px 6px;box-shadow:var(--shadow);margin-top:12px}
[data-testid="stWidgetLabel"] p{font-size:11.5px!important;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)!important;font-weight:700!important}
[data-baseweb="select"]>div{border-radius:12px!important;background:#fff!important;border-color:var(--line)!important}
[data-baseweb="tag"]{border-radius:8px!important}

/* colunas de conteúdo quebram em telas estreitas */
[data-testid="stHorizontalBlock"]{flex-wrap:wrap}
[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:min(400px,100%)}
[class*="st-key-filtros"] [data-testid="stColumn"],[class*="st-key-painel"] [data-testid="stColumn"],
[class*="st-key-card_"] [data-testid="stColumn"]{min-width:0}
[class*="st-key-filtros"] [data-testid="stHorizontalBlock"],[class*="st-key-card_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap}

/* cartões */
[class*="st-key-card_"]{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:20px 22px 10px;box-shadow:var(--shadow);animation:rise .6s .12s ease both}
.sec{margin-bottom:4px}
.sec-ey{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--accent);font-weight:700}
.sec-t{font-family:Fraunces,serif;font-size:21px;font-weight:600;color:var(--ink);margin-top:2px;line-height:1.2}
.sec-n{font-size:13px;color:var(--muted);margin-top:3px}
.titulo-bloco{display:flex;align-items:baseline;gap:14px;margin:26px 2px 10px}
.titulo-bloco h2{font-family:Fraunces,serif!important;font-size:28px!important;font-weight:600!important;color:var(--ink)!important;margin:0!important;padding:0!important}
.titulo-bloco span{color:var(--muted);font-size:14px}
.titulo-bloco:after{content:"";flex:1;height:1px;background:var(--line);transform:translateY(-6px)}

/* indicadores */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:14px;margin:6px 0 4px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:20px;padding:16px 18px 15px;box-shadow:var(--shadow);animation:rise .55s ease both;position:relative;overflow:hidden}
.kpi:nth-child(2){animation-delay:.05s}.kpi:nth-child(3){animation-delay:.1s}.kpi:nth-child(4){animation-delay:.15s}.kpi:nth-child(5){animation-delay:.2s}.kpi:nth-child(6){animation-delay:.25s}
.kpi.destaque{background:linear-gradient(150deg,#fff 30%,#e9f1fc)}
.kpi.destaque:after{content:"";position:absolute;right:-30px;top:-30px;width:90px;height:90px;border-radius:50%;background:rgba(42,120,214,.08)}
.k-label{font-size:11.5px;color:var(--muted);font-weight:700;letter-spacing:.09em;text-transform:uppercase}
.k-val{font-family:Fraunces,serif;font-size:clamp(26px,2.4vw,34px);font-weight:600;color:var(--ink);line-height:1.1;margin-top:8px;display:flex;align-items:center;gap:10px}
.k-of{font-family:'Instrument Sans',sans-serif;font-size:13px;color:var(--muted);font-weight:500;line-height:1.25}
.k-delta{display:inline-block;margin-top:9px;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px}
.k-delta.up{background:#e3f4ea;color:#0d7340}.k-delta.down{background:#fdebe2;color:#b03c0c}.k-delta.flat{background:#eef0f4;color:var(--ink-2)}
.k-sub{font-size:12.5px;color:var(--muted);margin-top:7px}
.badge{display:inline-grid;place-items:center;width:48px;height:48px;border-radius:15px;font-size:27px;font-weight:700;box-shadow:inset 0 -3px 0 rgba(0,0,0,.12)}

/* ranking */
.rank-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin:14px 0 4px}
.rank{background:#fff;border:1px solid var(--line);border-radius:20px;padding:18px 20px;box-shadow:var(--shadow);display:flex;gap:20px;align-items:center;animation:rise .6s .1s ease both}
.rank-pos{font-family:Fraunces,serif;font-size:48px;font-weight:600;color:var(--ink);line-height:1;white-space:nowrap}
.rank-pos small{font-family:'Instrument Sans',sans-serif;font-size:14px;color:var(--muted);font-weight:500;margin-left:4px;letter-spacing:0}
.rank-info{flex:1}
.rank-lbl{font-size:11.5px;color:var(--muted);font-weight:700;letter-spacing:.09em;text-transform:uppercase}
.rank-bar{height:8px;border-radius:99px;background:#ecebe5;overflow:hidden;margin:9px 0 6px}
.rank-bar span{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#86b6ef,#2a78d6 60%,#104281)}
.rank-sub{font-size:13px;color:var(--ink-2)}

/* situação dos cursos */
.st{margin:6px 0 8px}
.st-row{display:grid;grid-template-columns:minmax(140px,38%) 1fr 42px 30px;gap:12px;align-items:center;min-height:34px;border-radius:8px}
.st-row:not(.st-cab):hover{background:#f6f4ef}
.st-nome{font-size:13px;color:var(--ink);font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.st-nome small{color:var(--muted);font-size:11px;margin-left:6px;font-weight:500}
.st-track{position:relative;height:14px;border-radius:99px;background:repeating-linear-gradient(90deg,#efede6 0 calc(20% - 1px),#fff calc(20% - 1px) 20%)}
.st-track span{position:absolute;left:0;top:0;bottom:0;border-radius:99px}
.st-track i{position:absolute;top:50%;width:11px;height:11px;background:#1baf7a;border:2px solid #fff;border-radius:2px;
transform:translate(-50%,-50%) rotate(45deg);box-shadow:0 1px 3px rgba(0,0,0,.25)}
.st-v{font-size:13px;font-weight:700;color:var(--ink);text-align:right;font-variant-numeric:tabular-nums}
.st-row .badge{width:28px;height:28px;font-size:14px;border-radius:8px;font-family:Fraunces,serif}
.st-cab{min-height:18px}
.st-row.st-dest{background:#eaf2fc;box-shadow:inset 3px 0 0 #2a78d6}
.st-row.st-dest .st-nome{font-weight:700;color:#1c5cab}
.st-ticks{position:relative;height:14px}
.st-ticks span{position:absolute;transform:translateX(-50%);font-size:11px;color:var(--muted);font-weight:600}

/* barras divergentes */
.dv{margin:8px 0 6px}
.dv-row{display:grid;grid-template-columns:minmax(150px,34%) 1fr 1fr;align-items:center;min-height:30px;border-radius:8px}
.dv-row:not(.dv-cab):hover{background:#f6f4ef}
.dv-nome{font-size:13px;color:var(--ink);padding-right:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500}
.dv-neg,.dv-pos{display:flex;align-items:center;height:100%;gap:6px}
.dv-neg{justify-content:flex-end;flex-direction:row-reverse;border-right:1.5px solid rgba(15,31,61,.35)}
.dv-neg{justify-content:flex-start}
.dv-neg span,.dv-pos span{display:block;height:16px}
.dv-pos span{background:#2a78d6;border-radius:0 5px 5px 0}
.dv-neg span{background:#e34948;border-radius:5px 0 0 5px}
.dv-row em{font-style:normal;font-size:12px;font-weight:700;color:var(--ink);white-space:nowrap}
.dv-cab{min-height:26px}
.dv-cab b{font-size:11.5px;font-weight:700;letter-spacing:.04em}
.dv-cab .dv-neg b{color:#c0392b;padding-right:8px}
.dv-cab .dv-pos b{color:#2a78d6;padding-left:8px}
.dv-cab .dv-neg{justify-content:flex-end;flex-direction:row}

/* faixas comparadas */
.fc-sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:8px 0 14px}
.fc-sum div{background:#faf9f6;border:1px solid var(--line);border-radius:14px;padding:10px 12px;display:flex;gap:10px;align-items:center}
.fc-sum b{font-family:Fraunces,serif;font-size:26px;font-weight:600;line-height:1}
.fc-sum span{font-size:12px;color:var(--muted);line-height:1.3}
.fc-leg{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--ink-2);margin:0 0 8px}
.fc-leg i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.fc-row{display:flex;align-items:center;gap:14px;padding:9px 0;border-top:1px solid var(--line)}
.fc-row .badge{width:38px;height:38px;font-size:19px;border-radius:11px;font-family:Fraunces,serif;flex:none}
.fc-bars{flex:1;display:flex;flex-direction:column;gap:5px}
.fc-l{display:flex;align-items:center;gap:10px}
.fc-track{flex:1;height:9px;border-radius:99px;background:#efede6;overflow:hidden}
.fc-track span{display:block;height:100%;border-radius:99px}
.fc-v{width:74px;font-size:13px;font-weight:600;color:var(--ink);text-align:right;white-space:nowrap}
.fc-v small{font-weight:500;color:var(--muted);margin-left:5px;font-size:11.5px}

/* mapa de conceitos */
.mapa-wrap{overflow-x:auto;margin:4px 0 6px}
.mapa{border-collapse:separate;border-spacing:6px 5px;width:auto}
.mapa th{font-size:12px;color:var(--muted);font-weight:700;letter-spacing:.06em;text-align:center;padding-bottom:4px}
.mapa td{text-align:center;padding:0}
.mapa td.curso{text-align:left;font-size:13.5px;color:var(--ink);white-space:nowrap;padding-right:14px;font-weight:500;position:sticky;left:0;background:#fff;z-index:1}
.mapa tbody tr:hover td.curso{color:var(--accent)}
.mapa .badge{width:34px;height:34px;font-size:16px;border-radius:10px;font-family:Fraunces,serif;cursor:default}
.mapa .vazio{display:inline-block;width:34px;height:34px;border-radius:10px;background:#f3f1ea;border:1px dashed rgba(15,31,61,.08)}

/* linha do tempo de faixas */
.timeline{display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 10px}
.tl{flex:1;min-width:92px;text-align:center;background:#faf9f6;border:1px solid var(--line);border-radius:16px;padding:12px 8px}
.tl-ano{font-size:12px;color:var(--muted);font-weight:700;letter-spacing:.08em}
.tl .badge{width:40px;height:40px;font-size:22px;border-radius:12px;margin:6px auto 4px;font-family:Fraunces,serif}
.tl-v{font-size:12px;color:var(--ink-2)}

/* abas, expansores, avisos */
.stTabs [role="tablist"]{gap:6px;background:#fff;padding:6px;border-radius:16px;border:1px solid var(--line);box-shadow:var(--shadow);width:fit-content;max-width:100%}
.stTabs [data-testid="stTab"]{border-radius:11px;padding:9px 18px!important;height:auto;font-weight:600;border:none!important;transition:background .2s}
.stTabs [data-testid="stTab"]:hover{background:#f1efe9}
.stTabs [data-testid="stTab"][aria-selected="true"]{background:var(--ink)!important}
.stTabs [data-testid="stTab"][aria-selected="true"] p{color:#fff!important}
.stTabs [data-testid="stTab"] p{font-size:14.5px;font-weight:600}
[data-testid="stExpander"] details{background:#fff;border-radius:18px!important;border:1px solid var(--line)!important;box-shadow:var(--shadow)}
[data-testid="stExpander"] summary p{font-weight:600}
[data-testid="stAlert"]{border-radius:14px}
.stDownloadButton button{border-radius:12px;font-weight:600}
.nota{font-size:12.5px;color:var(--muted);margin:2px 2px 10px}
[data-testid="stIFrame"][height="0"],iframe[height="0"]{display:none}
.element-container:has(iframe[height="0"]){display:none}
"""


# Seções do menu lateral recolhidas por padrão (o Streamlit não tem essa opção).
# O Streamlit guarda no navegador quais seções estão abertas; na primeira visita recolhemos todas,
# e em qualquer visita garantimos que a seção da página atual esteja aberta.
JS_SECOES = r"""
<script>
(function () {
  const doc = window.parent.document;
  const secaoDaPagina = __MAPA__;
  const caminho = window.parent.location.pathname.replace(/^\/+|\/+$/g, "").split("/").pop();
  const atual = secaoDaPagina[caminho] || secaoDaPagina[""];
  const MARCA = "observatorioEnade.secoesIniciadas";
  let primeiraVisita = false;
  try { primeiraVisita = !window.parent.localStorage.getItem(MARCA); } catch (e) {}
  let tentativas = 0;
  const ajustar = () => {
    const cabecalhos = [...doc.querySelectorAll('[data-testid="stNavSectionHeader"]')];
    if (!cabecalhos.length) { if (tentativas++ < 50) setTimeout(ajustar, 100); return; }
    cabecalhos.forEach(h => {
      const nome = (h.querySelector("p") || h).innerText.trim().toUpperCase();
      const aberta = h.parentElement.querySelectorAll("a").length > 0;
      const ehAtual = atual && nome === atual.toUpperCase();
      if ((ehAtual && !aberta) || (primeiraVisita && !ehAtual && aberta)) h.click();
    });
    try { window.parent.localStorage.setItem(MARCA, "1"); } catch (e) {}
  };
  ajustar();
})();
</script>
"""


def aplicar_estilo():
    st.html(f"<style>{CSS}</style>")
    mapa = {pg_.url_path: secao for secao, paginas in SECOES.items() for pg_ in paginas}
    mapa[""] = next(iter(SECOES))  # página inicial
    components.html(JS_SECOES.replace("__MAPA__", json.dumps(mapa, ensure_ascii=False)), height=0)
    st.sidebar.html(
        '<div class="brand"><div class="brand-mark">E</div><div><div class="brand-t">Observatório<br>ENADE</div>'
        '<div class="brand-s">Enade · CPC · IGC</div></div></div>'
        f'<div class="side-note">Base INEP {int(CPC["ano"].min())}–{int(CPC["ano"].max())}<br>'
        f'{len(CPC):,} cursos avaliados'.replace(",", ".")
        + (f'<br>Enade {int(NOVO["ano"].max())}: licenciaturas e Medicina' if not NOVO.empty else "") + "</div>"
    )


# ---------------------------------------------------------------- dados
def versao_dados():
    """Data de modificação das bases: o cache é refeito quando o ETL grava arquivos novos."""
    return tuple(round(a.stat().st_mtime) for a in sorted(DADOS.glob("*.parquet")))


def faixa_de(v):
    """Faixa 1–5 a partir de nota contínua 0–5 (regra do INEP); vazio = SC."""
    if pd.isna(v):
        return "SC"
    return "1" if v < 0.945 else "2" if v < 1.945 else "3" if v < 2.945 else "4" if v < 3.945 else "5"


@st.cache_data(show_spinner="Carregando bases…")
def carregar(versao=None):
    cpc = pd.read_parquet(DADOS / "cpc.parquet")
    igc = pd.read_parquet(DADOS / "igc.parquet")
    cpc["ies_label"] = cpc["ies_nome_atual"] + cpc["ies_sigla_atual"].map(lambda s: f" ({s})" if pd.notna(s) and s else "")
    igc["ies_label"] = igc["ies_nome"] + igc["ies_sigla"].map(lambda s: f" ({s})" if pd.notna(s) and s else "")
    cpc["idd_faixa"] = cpc["idd"].map(faixa_de)
    cpc["oferta_label"] = (
        cpc["area"].str.title() + " — " + cpc["ies_sigla_atual"].fillna(cpc["ies_nome_atual"]).astype(str)
        + " — " + cpc["municipio"].str.title() + "/" + cpc["uf"]
        + cpc["modalidade"].map(lambda m: " (EaD)" if "dist" in str(m).lower() else "")
    )
    return cpc, igc


if not (DADOS / "cpc.parquet").exists():
    st.error("Base consolidada não encontrada. Rode primeiro:  `python etl/consolidar.py`")
    st.stop()

CPC, IGC = carregar(versao_dados())


# ---------------------------------------------------------------- utilitários
def br(x, casas=2):
    if x is None or pd.isna(x):
        return "—"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, casas=0):
    return "—" if x is None or pd.isna(x) else br(100 * x, casas) + "%"


def titulo(a: str) -> str:
    t = str(a).title()
    for p in (" E ", " De ", " Da ", " Do ", " Das ", " Dos ", " Em "):
        t = t.replace(p, p.lower())
    return t


def lista_areas():
    return sorted(CPC["area"].dropna().unique())


def idx(opcoes, valor, padrao=0):
    try:
        return list(opcoes).index(valor)
    except ValueError:
        return padrao


def ini(chave, i):
    """Índice padrão do widget, omitido quando outra página já definiu o valor via session_state."""
    return {} if chave in st.session_state else {"index": i}


def anos_da_area(area):
    return sorted(CPC.loc[CPC["area"] == area, "ano"].unique())


def dif(v, ref, contra="Brasil", casas=2, pp=False, menor_melhor=False):
    """(texto, sinal) da diferença v − ref, para os selos de variação (sinal = bom/ruim)."""
    if v is None or ref is None or pd.isna(v) or pd.isna(ref):
        return None
    d = (v - ref) * (100 if pp else 1)
    s = 1 if d > 0.005 else (-1 if d < -0.005 else 0)
    seta = "▲" if s > 0 else ("▼" if s < 0 else "●")
    return f"{seta} {br(abs(d), 0 if pp else casas)}{' p.p.' if pp else ''} vs {contra}", (-s if menor_melhor else s)


# ---------------------------------------------------------------- componentes visuais
def hero(slot, eyebrow, titulo_html, sub, chips=(), numeral=""):
    chips_html = "".join(f"<span>{escape(str(c))}</span>" for c in chips if c)
    slot.html(
        f'<div class="hero"><div class="hero-num">{numeral}</div><div class="eyebrow">{eyebrow}</div>'
        f"<h1>{titulo_html}</h1><p>{sub}</p><div class='chips'>{chips_html}</div></div>"
    )


def selo(faixa, grande=True):
    f = str(faixa)
    cor = COR_FAIXA.get(f, COR_NEUTRA)
    txt = TINTA if f in ("1", "2", "SC") else "#fff"
    return f'<span class="badge" style="background:{cor};color:{txt}">{f}</span>'


def kpi(label, valor=None, delta=None, sub=None, faixa=None, destaque=False):
    if faixa is not None:
        corpo = selo(faixa) + f'<span class="k-of">{"faixa<br>de 1 a 5" if str(faixa) != "SC" else "sem<br>conceito"}</span>'
    else:
        corpo = valor
    d = f'<div class="k-delta {["flat", "up", "down"][delta[1]]}">{delta[0]}</div>' if delta else ""
    s = f'<div class="k-sub">{sub}</div>' if sub else ""
    return f'<div class="kpi{" destaque" if destaque else ""}"><div class="k-label">{label}</div><div class="k-val">{corpo}</div>{d}{s}</div>'


def kpis(*itens):
    st.html('<div class="kpis">' + "".join(itens) + "</div>")


def secao(eyebrow, texto, nota=None):
    n = f'<div class="sec-n">{nota}</div>' if nota else ""
    st.html(f'<div class="sec"><div class="sec-ey">{eyebrow}</div><div class="sec-t">{texto}</div>{n}</div>')


def bloco(texto, apoio=""):
    st.html(f'<div class="titulo-bloco"><h2>{texto}</h2><span>{apoio}</span></div>')


def card(chave):
    return st.container(key=f"card_{chave}")


def filtros(chave):
    """Painel de filtros que se sobrepõe à base do cabeçalho."""
    return st.container(key=f"filtros_{chave}")


def painel(chave):
    """Painel de filtros comum (sem sobreposição)."""
    return st.container(key=f"painel_{chave}")


def rank_html(rotulo, p, sufixo="dos cursos"):
    if not p:
        return ""
    pos, total, perc = p
    return (f'<div class="rank"><div class="rank-pos">{pos}º<small>de {total}</small></div><div class="rank-info">'
            f'<div class="rank-lbl">{rotulo}</div><div class="rank-bar"><span style="width:{max(perc, .02) * 100:.1f}%"></span></div>'
            f'<div class="rank-sub">Supera <b>{pct(perc)}</b> {sufixo}</div></div></div>')


def ajustar(fig, altura=360, legenda=True):
    fig.update_layout(
        height=altura,
        margin=dict(l=4, r=12, t=40 if legenda else 10, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=12.5, color=TINTA_2),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None, traceorder="normal", font=dict(size=12.5)),
        showlegend=legenda, title=None,
        hoverlabel=dict(bgcolor="white", bordercolor="rgba(15,31,61,.15)", font=dict(family=FONTE, color=TINTA, size=13), namelength=-1),
        separators=",.", bargap=0.28, bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(15,31,61,.15)", ticks="", tickfont=dict(color=TINTA_2))
    fig.update_yaxes(gridcolor=GRADE, zeroline=False, linecolor="rgba(0,0,0,0)", tickfont=dict(color="#8a91a2"))
    return fig


def mostrar(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "locale": "pt-BR"})


def resumo(df: pd.DataFrame) -> dict:
    com_cpc = df["cpc_continuo"].notna()
    return {
        "n": len(df),
        "n_cpc": int(com_cpc.sum()),
        "enade": df["enade_continuo"].mean(),
        "cpc": df["cpc_continuo"].mean(),
        "idd": df["idd"].mean(),
        "pct45_cpc": df.loc[com_cpc, "cpc_faixa"].isin(["4", "5"]).mean() if com_cpc.any() else float("nan"),
        "pct45_enade": df.loc[df["enade_continuo"].notna(), "enade_faixa"].isin(["4", "5"]).mean(),
        "participantes": df["participantes"].sum(),
        "inscritos": df["inscritos"].sum(),
    }


def posicao(df: pd.DataFrame, valor, col="cpc_continuo"):
    v = df[col].dropna()
    if pd.isna(valor) or v.empty:
        return None
    return int((v > valor).sum()) + 1, len(v), (v < valor).mean()


def distribuicao_faixas(grupos: dict[str, pd.Series]):
    """Barras 100% empilhadas horizontais: uma barra por grupo, segmentos = faixas."""
    linhas = []
    for nome, faixas in grupos.items():
        cont = faixas.value_counts()
        total = cont.sum()
        for f in FAIXAS:
            n = int(cont.get(f, 0))
            linhas.append({"grupo": nome, "faixa": f, "n": n, "pct": n / total if total else 0})
    t = pd.DataFrame(linhas)
    fig = go.Figure()
    for f in FAIXAS:
        s = t[t["faixa"] == f]
        nome = "Sem conceito" if f == "SC" else f"Faixa {f}"
        fig.add_bar(
            y=s["grupo"], x=s["pct"], name=nome, orientation="h",
            marker=dict(color=COR_FAIXA[f], line=dict(width=2, color="#fff")),
            text=[pct(p) if p >= 0.06 else "" for p in s["pct"]], textposition="inside",
            insidetextfont=dict(color="white" if f in ("3", "4", "5") else TINTA, size=12),
            customdata=s[["n"]].values,
            hovertemplate="%{y}<br>" + nome + ": <b>%{x:.1%}</b> (%{customdata[0]} cursos)<extra></extra>",
        )
    fig.update_layout(barmode="stack", xaxis=dict(tickformat=".0%", range=[0, 1], showticklabels=False))
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=TINTA, size=13))
    return ajustar(fig, altura=95 + 62 * len(grupos))


def faixas_html(grupos: list[tuple[str, pd.Series]]) -> str:
    """Comparativo faixa a faixa (selo + uma barra fina por grupo), com resumo de faixas 4–5."""
    cores = [COR_CURSO, COR_BR, COR_UF]
    dados = []
    for (nome, serie), cor in zip(grupos, cores):
        cont = serie.value_counts()
        tot = cont.sum()
        dados.append((nome, cont, tot, cor))
    p = lambda cont, tot, f: cont.get(f, 0) / tot if tot else 0
    linhas = []
    for f in FAIXAS:
        if all(cont.get(f, 0) == 0 for _, cont, _, _ in dados):
            continue
        barras = "".join(
            f'<div class="fc-l"><div class="fc-track"><span style="width:{max(p(cont, tot, f) * 100, 0.8):.1f}%;background:{cor}"></span></div>'
            f'<div class="fc-v">{pct(p(cont, tot, f))}<small>{cont.get(f, 0):,}</small></div></div>'.replace(",", ".")
            for _, cont, tot, cor in dados)
        linhas.append(f'<div class="fc-row">{selo(f)}<div class="fc-bars">{barras}</div></div>')
    resumo_html = '<div class="fc-sum">' + "".join(
        f'<div><b style="color:{cor}">{pct(p(cont, tot, "4") + p(cont, tot, "5"))}</b><span>{escape(nome)}<br>com faixa 4 ou 5</span></div>'
        for nome, cont, tot, cor in dados) + "</div>"
    legenda = '<div class="fc-leg">' + "".join(
        f'<span><i style="background:{cor}"></i>{escape(nome)} ({tot:,} cursos)</span>'.replace(",", ".")
        for nome, cont, tot, cor in dados) + "</div>"
    return f'<div class="fc">{resumo_html}{legenda}{"".join(linhas)}</div>'


def faixas_comparadas(a: pd.Series, b: pd.Series, nome_a: str, nome_b: str) -> str:
    return faixas_html([(nome_a, a), (nome_b, b)])


def situacao_html(df: pd.DataFrame, col_c: str, col_f: str, ind: str, escala_pct=False, mostrar_ano=True, destaque=None) -> str:
    """Uma linha por curso: trilho com o valor (0–5 ou 0–100%), losango na referência (coluna `ref`), valor e selo."""
    maximo = 1 if escala_pct else 5
    fmt = (lambda x: pct(x)) if escala_pct else (lambda x: br(x))
    fmt_dica = (lambda x: pct(x, 1)) if escala_pct else (lambda x: br(x, 3))
    marcas = [(t / 5, f"{t * 20}%" if escala_pct else str(t)) for t in range(6)]
    ticks = "".join(f'<span style="left:{pos * 100:.0f}%">{txt}</span>' for pos, txt in marcas)
    linhas = [f'<div class="st-row st-cab"><div></div><div class="st-ticks">{ticks}</div><div></div><div></div></div>']
    for r in df.itertuples():
        v, ref, f = getattr(r, col_c), r.ref, getattr(r, col_f)
        barra = "" if pd.isna(v) else f'<span style="width:{v / maximo * 100:.1f}%;background:{COR_FAIXA.get(f, COR_NEUTRA)}"></span>'
        losango = "" if pd.isna(ref) else f'<i style="left:{ref / maximo * 100:.1f}%"></i>'
        dica = f"{r.curso} · {r.ano}: {ind} {fmt_dica(v)} · referência {fmt_dica(ref)}"
        cls = " st-dest" if destaque is not None and getattr(r, "ies_id", None) == destaque else ""
        ano_txt = f"<small>{r.ano}</small>" if mostrar_ano else ""
        linhas.append(f'<div class="st-row{cls}" title="{escape(dica)}"><div class="st-nome">{escape(r.curso)}{ano_txt}</div>'
                      f'<div class="st-track">{barra}{losango}</div><div class="st-v">{fmt(v)}</div>{selo(f)}</div>')
    return f'<div class="st">{"".join(linhas)}</div>'


def divergente_html(df: pd.DataFrame, fmt=br) -> str:
    """Barras divergentes em HTML: nome do curso | abaixo da média | acima da média."""
    if df.empty:
        return '<div class="nota">Sem cursos com nota calculada.</div>'
    m = df["dif"].abs().max() or 1
    linhas = []
    for r in df.itertuples():
        w = abs(r.dif) / m * 78
        txt = ("+" if r.dif >= 0 else "−") + fmt(abs(r.dif))
        barra = f'<span style="width:{max(w, 1):.1f}%"></span><em>{txt}</em>'
        neg, pos = ("", barra) if r.dif >= 0 else (barra, "")
        linhas.append(f'<div class="dv-row" title="{escape(r.curso)} · {r.ano}: {txt} vs média nacional">'
                      f'<div class="dv-nome">{escape(r.curso)}</div><div class="dv-neg">{neg}</div><div class="dv-pos">{pos}</div></div>')
    cab = ('<div class="dv-row dv-cab"><div></div><div class="dv-neg"><b>◀ abaixo da média</b></div>'
           '<div class="dv-pos"><b>acima da média ▶</b></div></div>')
    return f'<div class="dv">{cab}{"".join(linhas)}</div>'


def tabela_cursos(df: pd.DataFrame, nome_arquivo="cursos.csv"):
    cols = {
        "ies_nome_atual": "IES", "ies_sigla_atual": "Sigla", "municipio": "Município", "uf": "UF",
        "modalidade": "Modalidade", "cat_administrativa": "Categoria", "participantes": "Participantes",
        "enade_continuo": "Enade contínuo", "enade_faixa": "Enade faixa", "idd": "IDD",
        "cpc_continuo": "CPC contínuo", "cpc_faixa": "CPC faixa",
    }
    t = df[list(cols)].rename(columns=cols).sort_values("CPC contínuo", ascending=False, na_position="last")
    st.dataframe(
        t, hide_index=True, use_container_width=True,
        column_config={
            "Enade contínuo": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=5),
            "CPC contínuo": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=5),
            "IDD": st.column_config.NumberColumn(format="%.3f"),
            "Participantes": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button("⬇  Baixar tabela (CSV)", t.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=nome_arquivo, mime="text/csv")


def filtro_modalidade(df, chave, col):
    mods = ["Todas"] + sorted(df["modalidade"].dropna().unique())
    m = col.selectbox("Modalidade", mods, key=chave)
    return (df if m == "Todas" else df[df["modalidade"] == m]), m


def linha_evolucao(series, altura=340, rotulos_em=None, faixa_y=(0, 5.3)):
    """series: lista de (nome, x, y, cor, destaque, tracejado)."""
    fig = go.Figure()
    for nome, x, y, cor, destaque, tracejado in series:
        mostrar_txt = rotulos_em == nome
        fig.add_scatter(
            x=x, y=y, name=nome, mode="lines+markers+text" if mostrar_txt else "lines+markers",
            line=dict(color=cor, width=3 if destaque else 2, dash="dot" if tracejado else None, shape="spline", smoothing=0.6),
            marker=dict(size=11 if destaque else 8, color=cor, line=dict(width=2, color="#fff")),
            text=[br(v) for v in y] if mostrar_txt else None, textposition="top center",
            textfont=dict(color=TINTA, size=12, family=FONTE),
            hovertemplate="%{x}: <b>%{y:.3f}</b><extra>" + nome + "</extra>",
        )
    fig.update_layout(yaxis=dict(range=list(faixa_y)), xaxis=dict(dtick=1), hovermode="x unified")
    return ajustar(fig, altura=altura)


# ================================================================ páginas
def pagina_nacional():
    topo = st.empty()
    with filtros("nac"):
        areas = lista_areas()
        c1, c2, c3 = st.columns([3, 1, 2])
        area = c1.selectbox("Curso (área de avaliação)", areas, index=idx(areas, "ODONTOLOGIA"), format_func=titulo)
        ano = c2.selectbox("Ano", anos_da_area(area)[::-1])
        base, mod = filtro_modalidade(CPC[(CPC["area"] == area) & (CPC["ano"] == ano)], "nac_mod", c3)
    r = resumo(base)
    hero(topo, "Panorama nacional", f"{titulo(area)} <em>no Brasil</em>",
         f"Como os cursos de {titulo(area)} se saíram no Enade e no CPC na edição de {ano}.",
         [f"{br(r['n'], 0)} cursos avaliados", f"{br(base['ies_id'].nunique(), 0)} instituições",
          f"{base['uf'].nunique()} UFs", mod if mod != "Todas" else "Todas as modalidades"], numeral=ano)

    kpis(
        kpi("Cursos avaliados", br(r["n"], 0), sub=f"{br(r['n_cpc'], 0)} com CPC calculado"),
        kpi("Média Conceito Enade", br(r["enade"]), sub="nota contínua, 0 a 5", destaque=True),
        kpi("Média CPC", br(r["cpc"]), sub="nota contínua, 0 a 5", destaque=True),
        kpi("Cursos com CPC 4 ou 5", pct(r["pct45_cpc"]), sub=f"Enade 4 ou 5: {pct(r['pct45_enade'])}"),
        kpi("Concluintes participantes", br(r["participantes"], 0),
            sub=f"Participação: {pct(r['participantes'] / r['inscritos'] if r['inscritos'] else None)}"),
    )

    c1, c2 = st.columns(2, gap="medium")
    with c1, card("nac_faixas"):
        secao("Distribuição", "Faixas do Conceito Enade e do CPC", "Percentual de cursos em cada faixa")
        mostrar(distribuicao_faixas({"Conceito Enade": base["enade_faixa"], "CPC": base["cpc_faixa"]}))
    with c2, card("nac_regiao"):
        secao("Geografia", "Médias por região")
        reg = base.groupby("regiao", as_index=False).agg(cpc=("cpc_continuo", "mean"), enade=("enade_continuo", "mean"), n=("area", "size"))
        reg = reg.melt(id_vars=["regiao", "n"], value_vars=["enade", "cpc"], var_name="ind", value_name="media")
        reg["ind"] = reg["ind"].map({"enade": "Conceito Enade", "cpc": "CPC"})
        fig = px.bar(reg, x="regiao", y="media", color="ind", barmode="group", custom_data=["n"],
                     color_discrete_sequence=[COR_SERIE[0], COR_SERIE[1]], labels={"regiao": "", "media": ""})
        fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: <b>%{y:.2f}</b><br>%{customdata[0]} cursos<extra></extra>",
                          marker_cornerradius=6)
        mostrar(ajustar(fig, altura=262))

    c1, c2 = st.columns([2, 3], gap="medium")
    with c1, card("nac_cat"):
        secao("Perfil institucional", "CPC médio por categoria")
        cat = base.dropna(subset=["cat_administrativa"])
        if cat.empty:
            st.info("A planilha deste ano não informa a categoria administrativa.")
        else:
            g = cat.groupby("cat_administrativa", as_index=False).agg(cpc=("cpc_continuo", "mean"), n=("area", "size")).sort_values("cpc")
            fig = px.bar(g, y="cat_administrativa", x="cpc", orientation="h", custom_data=["n"], text=g["cpc"].map(br),
                         labels={"cat_administrativa": "", "cpc": ""})
            fig.update_traces(marker_color=COR_CURSO, marker_cornerradius=6, textposition="outside", textfont=dict(color=TINTA),
                              hovertemplate="%{y}<br>CPC médio: <b>%{x:.2f}</b><br>%{customdata[0]} cursos<extra></extra>")
            fig.update_xaxes(range=[0, 5], showticklabels=False)
            mostrar(ajustar(fig, altura=320, legenda=False))
    with c2, card("nac_uf"):
        secao("Geografia", "CPC médio por UF", "Ordenado do maior para o menor")
        uf = base.groupby("uf", as_index=False).agg(cpc=("cpc_continuo", "mean"), n=("area", "size")).sort_values("cpc", ascending=False)
        fig = px.bar(uf, x="uf", y="cpc", custom_data=["n"], labels={"uf": "", "cpc": ""})
        fig.update_traces(marker_color=COR_CURSO, marker_cornerradius=5,
                          hovertemplate="%{x}<br>CPC médio: <b>%{y:.2f}</b><br>%{customdata[0]} cursos<extra></extra>")
        mostrar(ajustar(fig, altura=320, legenda=False))

    bloco("Evolução histórica", f"{titulo(area)} em todas as edições")
    hist = CPC[CPC["area"] == area]
    ev = hist.groupby("ano").agg(enade=("enade_continuo", "mean"), cpc=("cpc_continuo", "mean")).reset_index()
    c1, c2 = st.columns(2, gap="medium")
    with c1, card("nac_ev"):
        secao("Tendência", "Médias nacionais por edição")
        fig = linha_evolucao([("Conceito Enade", ev["ano"], ev["enade"], COR_SERIE[0], True, False),
                              ("CPC", ev["ano"], ev["cpc"], COR_SERIE[1], True, False)])
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=ev["ano"]))
        mostrar(fig)
    with c2, card("nac_evfaixa"):
        secao("Tendência", "Faixas de CPC por edição")
        dist = hist.groupby(["ano", "cpc_faixa"]).size().unstack(fill_value=0)
        dist = dist.div(dist.sum(axis=1), axis=0)
        fig = go.Figure()
        for f in FAIXAS:
            if f in dist:
                nome = "Sem conceito" if f == "SC" else f"CPC {f}"
                fig.add_bar(x=dist.index.astype(str), y=dist[f], name=nome,
                            marker=dict(color=COR_FAIXA[f], line=dict(width=2, color="#fff")),
                            hovertemplate="%{x}: <b>%{y:.1%}</b><extra>" + nome + "</extra>")
        fig.update_layout(barmode="stack", yaxis=dict(tickformat=".0%"))
        mostrar(ajustar(fig, altura=340))

    with st.expander(f"Todos os cursos de {titulo(area)} em {ano}", icon="📋"):
        tabela_cursos(base, f"{area.lower()}_{ano}.csv")


def pagina_ies():
    topo = st.empty()
    with filtros("ies"):
        areas = lista_areas()
        c1, c2, c3 = st.columns([2, 3, 1])
        area = c1.selectbox("Curso (área de avaliação)", areas, **ini("ies_area", idx(areas, "ODONTOLOGIA")), format_func=titulo, key="ies_area")
        da_area = CPC[CPC["area"] == area]
        ies = da_area.drop_duplicates("ies_id").sort_values("ies_label")
        ies_ids = ies["ies_id"].tolist()
        nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
        ies_id = c2.selectbox("Instituição (IES)", ies_ids, **ini("ies_ies", idx(ies_ids, UNILAVRAS)), format_func=nomes.get, key="ies_ies")
        d = da_area[da_area["ies_id"] == ies_id]
        ano = c3.selectbox("Ano", sorted(d["ano"].unique())[::-1], key="ies_ano")
        linhas = d[d["ano"] == ano]
        if len(linhas) > 1:
            rot = linhas.apply(lambda x: f"{x['municipio'].title()}/{x['uf']} · {x['modalidade']}"
                               + (f" · cód. {x['cod_curso']}" if x["cod_curso"] else ""), axis=1)
            if st.session_state.get("ies_oferta") not in rot.index:
                st.session_state.pop("ies_oferta", None)
            escolha = st.radio(f"{len(linhas)} cursos desta IES na área em {ano}", rot.index, format_func=rot.get, horizontal=True, key="ies_oferta")
            r = linhas.loc[escolha]
        else:
            r = linhas.iloc[0]

    br_ano = CPC[(CPC["area"] == area) & (CPC["ano"] == ano)]
    uf_ano = br_ano[br_ano["uf"] == r["uf"]]
    rb = resumo(br_ano)
    sigla = r["ies_sigla_atual"] if pd.notna(r["ies_sigla_atual"]) else ""
    hero(topo, escape(titulo(r["ies_nome_atual"])) + (f" · {escape(sigla)}" if sigla else ""),
         f"{titulo(area)} <em>{ano}</em>",
         f"{r['municipio'].title()} / {r['uf']} — resultado do curso comparado com o estado e com o Brasil.",
         [r["modalidade"], r["cat_administrativa"], r["org_academica"], f"Código do curso {r['cod_curso']}" if r["cod_curso"] else None],
         numeral=ano)
    if pd.notna(r.get("observacao")) and r.get("observacao"):
        st.warning(f"Observação do INEP: {r['observacao']}")

    kpis(
        kpi("Conceito Enade", faixa=r["enade_faixa"]),
        kpi("Enade contínuo", br(r["enade_continuo"], 3), delta=dif(r["enade_continuo"], rb["enade"])),
        kpi("CPC", faixa=r["cpc_faixa"]),
        kpi("CPC contínuo", br(r["cpc_continuo"], 3), delta=dif(r["cpc_continuo"], rb["cpc"]), destaque=True),
        kpi("IDD padronizado", br(r["idd"], 3), delta=dif(r["idd"], rb["idd"])),
        kpi("Participantes", f"{br(r['participantes'], 0)}<span class='k-of'>de {br(r['inscritos'], 0)}<br>inscritos</span>",
            sub=f"Participação de {pct(r['taxa_participacao'])}"),
    )
    st.html('<div class="rank-row">'
            + rank_html("Posição no Brasil · CPC", posicao(br_ano, r["cpc_continuo"]))
            + rank_html(f"Posição em {r['uf']} · CPC", posicao(uf_ano, r["cpc_continuo"]))
            + rank_html("Posição no Brasil · Enade", posicao(br_ano, r["enade_continuo"], "enade_continuo"))
            + "</div>")

    bloco("Composição do CPC", f"curso × média {r['uf']} × média Brasil")
    with card("ies_comp"):
        secao("Insumos", "Notas padronizadas de cada componente", "Escala de 0 a 5")
        linhas_g = []
        for c, nome in INDICADORES:
            linhas_g += [
                {"indicador": nome, "grupo": "Este curso", "valor": r[c]},
                {"indicador": nome, "grupo": f"Média {r['uf']}", "valor": uf_ano[c].mean()},
                {"indicador": nome, "grupo": "Média Brasil", "valor": br_ano[c].mean()},
            ]
        fig = px.bar(pd.DataFrame(linhas_g), x="indicador", y="valor", color="grupo", barmode="group",
                     color_discrete_sequence=[COR_CURSO, COR_UF, COR_BR], labels={"indicador": "", "valor": ""})
        fig.update_traces(marker_cornerradius=4, hovertemplate="%{x}<br>%{fullData.name}: <b>%{y:.3f}</b><extra></extra>")
        fig.update_yaxes(range=[0, 5.2])
        mostrar(ajustar(fig, altura=400))
    if pd.notna(r["fg_bruta"]):
        fg_br, ce_br = br_ano["fg_bruta"].mean(), br_ano["ce_bruta"].mean()
        fg_uf, ce_uf = uf_ano["fg_bruta"].mean(), uf_ano["ce_bruta"].mean()
        # Nota geral = 25% Formação Geral + 75% Componente Específico (regra do INEP); oficial quando a planilha traz.
        geral = lambda d: d["geral_bruta"].fillna(0.25 * d["fg_bruta"] + 0.75 * d["ce_bruta"])
        g_curso = r["geral_bruta"] if pd.notna(r["geral_bruta"]) else 0.25 * r["fg_bruta"] + 0.75 * r["ce_bruta"]
        g_br, g_uf = geral(br_ano).mean(), geral(uf_ano).mean()
        kpis(
            kpi("Formação Geral · nota bruta", br(r["fg_bruta"], 1), delta=dif(r["fg_bruta"], fg_br, casas=1),
                sub=f"Média {r['uf']}: {br(fg_uf, 1)} · Brasil: {br(fg_br, 1)}"),
            kpi("Componente Específico · nota bruta", br(r["ce_bruta"], 1), delta=dif(r["ce_bruta"], ce_br, casas=1),
                sub=f"Média {r['uf']}: {br(ce_uf, 1)} · Brasil: {br(ce_br, 1)}"),
            kpi("Resultado Geral · nota bruta", br(g_curso, 1), delta=dif(g_curso, g_br, casas=1), destaque=True,
                sub=f"Média {r['uf']}: {br(g_uf, 1)} · Brasil: {br(g_br, 1)}<br>25% Formação Geral + 75% Componente Específico"),
        )

    bloco("Histórico do curso", "todas as edições em que foi avaliado")
    hist = CPC[CPC["curso_chave"] == r["curso_chave"]].groupby("ano").agg(
        enade=("enade_continuo", "mean"), cpc=("cpc_continuo", "mean"),
        enade_faixa=("enade_faixa", "first"), cpc_faixa=("cpc_faixa", "first"), idd=("idd", "mean")).reset_index()
    st.html('<div class="timeline">' + "".join(
        f'<div class="tl"><div class="tl-ano">{h.ano}</div>{selo(h.cpc_faixa)}<div class="tl-v">CPC {br(h.cpc)} · Enade {h.enade_faixa}</div></div>'
        for h in hist.itertuples()) + "</div>")
    toda_area = CPC[CPC["area"] == area]
    m_br = toda_area.groupby("ano")[["enade_continuo", "cpc_continuo"]].mean()
    m_uf = toda_area[toda_area["uf"] == r["uf"]].groupby("ano")[["enade_continuo", "cpc_continuo"]].mean()
    anos = hist["ano"]
    c1, c2 = st.columns(2, gap="medium")
    for col, campo, cmp, nome, ch in [(c1, "enade", "enade_continuo", "Conceito Enade contínuo", "h1"), (c2, "cpc", "cpc_continuo", "CPC contínuo", "h2")]:
        with col, card(f"ies_{ch}"):
            secao("Trajetória", nome)
            fig = linha_evolucao([
                ("Média Brasil", anos, m_br.reindex(anos)[cmp], COR_BR, False, True),
                (f"Média {r['uf']}", anos, m_uf.reindex(anos)[cmp], COR_UF, False, True),
                ("Este curso", anos, hist[campo], COR_CURSO, True, False),
            ], rotulos_em="Este curso")
            fig.update_layout(xaxis=dict(tickmode="array", tickvals=anos))
            mostrar(fig)
    if len(hist) <= 1:
        st.html('<div class="nota">Só há uma edição para este curso. O histórico liga as edições por IES + área + município + modalidade.</div>')


def pagina_cursos_ies():
    topo = st.empty()
    with filtros("cies"):
        ies = CPC.sort_values("ano").drop_duplicates("ies_id", keep="last").sort_values("ies_label")
        ids = ies["ies_id"].tolist()
        nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
        c1, c2, c3 = st.columns([3, 1.4, 1.2])
        iid = c1.selectbox("Instituição (IES)", ids, index=idx(ids, UNILAVRAS), format_func=nomes.get, key="cies_ies")
        dados = CPC[CPC["ies_id"] == iid]
        edicoes = ["atual"] + sorted(dados["ano"].unique())[::-1]
        ed = c2.selectbox("Edição", edicoes, format_func=lambda e: "Mais recente de cada curso" if e == "atual" else str(e), key="cies_ed")
        ind = c3.selectbox("Indicador", ["CPC", "Conceito Enade"], key="cies_ind")
    col_c, col_f = ("cpc_continuo", "cpc_faixa") if ind == "CPC" else ("enade_continuo", "enade_faixa")
    sigla_ind = "CPC" if ind == "CPC" else "Enade"

    # Rótulo de cada curso (pela avaliação mais recente): área, município se a IES tiver vários, EaD.
    recentes = dados.sort_values("ano").groupby("curso_chave").tail(1)
    varios_mun = recentes["municipio"].nunique() > 1
    rot = {r.curso_chave: titulo(r.area).replace("Tecnologia em ", "Tec. em ") + (f" · {r.municipio.title()}" if varios_mun else "")
           + (" (EaD)" if "dist" in str(r.modalidade).lower() else "") for r in recentes.itertuples()}

    sel = recentes if ed == "atual" else dados[dados["ano"] == ed]
    sel = sel.assign(curso=sel["curso_chave"].map(rot))
    ref = CPC.groupby(["area", "ano"])[[col_c]].mean().rename(columns={col_c: "ref"})
    sel = sel.join(ref, on=["area", "ano"])
    sel["dif"] = sel[col_c] - sel["ref"]
    nac = CPC.merge(sel[["area", "ano"]].drop_duplicates(), on=["area", "ano"])  # mesmas áreas e edições no Brasil

    info = dados.sort_values("ano").iloc[-1]
    hero(topo, "Cursos da instituição", escape(titulo(info["ies_nome_atual"])),
         ("Situação mais recente de cada curso avaliado" if ed == "atual" else f"Cursos avaliados na edição de {ed}")
         + f" — {ind} comparado com a média nacional da mesma área e edição.",
         [info["org_academica"], info["cat_administrativa"], f"{info['municipio'].title()}/{info['uf']}",
          f"{dados['curso_chave'].nunique()} cursos avaliados desde {dados['ano'].min()}"],
         numeral="" if ed == "atual" else ed)

    com = sel[sel[col_c].notna()]
    acima = int((com["dif"] > 0).sum())
    p45 = com[col_f].isin(["4", "5"]).mean() if len(com) else None
    p45_br = nac.loc[nac[col_c].notna(), col_f].isin(["4", "5"]).mean()
    ig = IGC[IGC["ies_id"] == iid].sort_values("ano")
    kpis(
        kpi("Cursos", br(len(sel), 0), sub=f"{len(com)} com {ind} calculado"),
        kpi(f"{ind} médio", br(com[col_c].mean()), delta=dif(com[col_c].mean(), com["ref"].mean()), destaque=True,
            sub="vs média nacional das mesmas áreas"),
        kpi(f"{ind} 4 ou 5", pct(p45), delta=dif(p45, p45_br, pp=True)),
        kpi("Acima da média nacional", f"{acima}<span class='k-of'>de {len(com)}<br>cursos</span>",
            sub=f"{pct(acima / len(com) if len(com) else None)} dos cursos"),
        kpi(f"IGC {ig['ano'].iloc[-1]}", faixa=ig["igc_faixa"].iloc[-1]) if not ig.empty else "",
    )
    if sel.empty:
        st.info("Nenhum curso desta IES nesta edição.")
        return

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, card("cies_sit"):
        secao("Situação", f"{ind} contínuo de cada curso", "Barra na cor da faixa · ◆ = média nacional da área na mesma edição")
        st.html(situacao_html(sel.sort_values(col_c, ascending=False, na_position="last"), col_c, col_f, ind))
    with c2, card("cies_dist"):
        secao("Distribuição", f"Faixas de {ind}", "Esta IES × Brasil, nas mesmas áreas e edições")
        st.html(faixas_comparadas(sel[col_f], nac[col_f], "Esta IES", "Brasil"))

    with card("cies_dif"):
        secao("Desempenho relativo", "Diferença para a média nacional",
              f"{ind} contínuo do curso menos a média nacional da área na mesma edição")
        st.html(divergente_html(sel.dropna(subset=["dif"]).sort_values("dif", ascending=False)))

    bloco("Mapa de conceitos", f"faixa de {ind} de cada curso em cada edição")
    cursos = sorted(rot, key=lambda k: rot[k])
    with card("cies_mapa"):
        anos = sorted(dados["ano"].unique())
        m = dados.groupby(["curso_chave", "ano"]).agg(f=(col_f, "first"), v=(col_c, "mean")).reset_index()
        piv_f = m.pivot(index="curso_chave", columns="ano", values="f").reindex(index=cursos, columns=anos)
        piv_v = m.pivot(index="curso_chave", columns="ano", values="v").reindex(index=cursos, columns=anos)
        cab = "".join(f"<th>{a}</th>" for a in anos)
        linhas = []
        for k in cursos:
            cels = []
            for a in anos:
                f, v = piv_f.loc[k, a], piv_v.loc[k, a]
                if pd.isna(f):
                    cels.append('<td><span class="vazio"></span></td>')
                else:
                    cels.append(f'<td title="{escape(rot[k])} · {a}: {ind} contínuo {br(v, 3)}">{selo(f)}</td>')
            linhas.append(f'<tr><td class="curso">{escape(rot[k])}</td>{"".join(cels)}</tr>')
        st.html(f'<div class="mapa-wrap"><table class="mapa"><thead><tr><th></th>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>')
        st.html('<div class="nota">Células vazias: o curso não foi avaliado naquela edição (cada área é avaliada a cada três anos). SC = sem conceito.</div>')

    with card("cies_ir"):
        secao("Detalhar", "Abrir a análise completa de um curso")
        c1, c2, c3 = st.columns([3, 1, 1], vertical_alignment="bottom")
        k = c1.selectbox("Curso", cursos, format_func=rot.get, key="cies_curso")
        anos_k = sorted(dados.loc[dados["curso_chave"] == k, "ano"].unique())[::-1]
        a = c2.selectbox("Edição", anos_k, key="cies_curso_ano")
        if c3.button("Ver detalhes →", type="primary", use_container_width=True):
            linha = dados[(dados["curso_chave"] == k) & (dados["ano"] == a)]
            st.session_state.update(ies_area=linha["area"].iloc[0], ies_ies=iid, ies_ano=a, ies_oferta=linha.index[0])
            st.switch_page(PAGINA_IES)

    with st.expander("Tabela de todos os cursos e edições", icon="📋"):
        t = dados.assign(Curso=dados["curso_chave"].map(rot)).sort_values(["Curso", "ano"])
        t = t[["Curso", "ano", "modalidade", "participantes", "enade_continuo", "enade_faixa", "idd", "cpc_continuo", "cpc_faixa"]].rename(columns={
            "ano": "Ano", "modalidade": "Modalidade", "participantes": "Participantes", "enade_continuo": "Enade contínuo",
            "enade_faixa": "Enade faixa", "idd": "IDD", "cpc_continuo": "CPC contínuo", "cpc_faixa": "CPC faixa"})
        st.dataframe(t, hide_index=True, use_container_width=True,
                     column_config={"Enade contínuo": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=5),
                                    "CPC contínuo": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=5),
                                    "IDD": st.column_config.NumberColumn(format="%.3f")})
        st.download_button("⬇  Baixar tabela (CSV)", t.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           file_name=f"cursos_{iid}.csv", mime="text/csv")


def pagina_estado():
    topo = st.empty()
    with filtros("uf"):
        areas = lista_areas()
        c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
        area = c1.selectbox("Curso (área de avaliação)", areas, index=idx(areas, "ODONTOLOGIA"), format_func=titulo)
        ufs = sorted(CPC["uf"].dropna().unique())
        uf = c2.selectbox("UF", ufs, index=idx(ufs, "MG"))
        ano = c3.selectbox("Ano", anos_da_area(area)[::-1])
        br_ano, mod = filtro_modalidade(CPC[(CPC["area"] == area) & (CPC["ano"] == ano)], "uf_mod", c4)
    uf_ano = br_ano[br_ano["uf"] == uf]
    hero(topo, "Curso no estado", f"{titulo(area)} <em>em {uf}</em>",
         f"Os cursos de {titulo(area)} de {uf} na edição de {ano}, comparados com o restante do Brasil.",
         [f"{len(uf_ano)} cursos em {uf}", f"{uf_ano['ies_id'].nunique()} instituições", mod if mod != "Todas" else "Todas as modalidades"],
         numeral=ano)
    if uf_ano.empty:
        st.warning(f"Nenhum curso de {titulo(area)} avaliado em {uf} em {ano}.")
        return
    ru, rb = resumo(uf_ano), resumo(br_ano)

    kpis(
        kpi(f"Cursos em {uf}", br(ru["n"], 0), sub=f"{pct(ru['n'] / rb['n'], 1)} do total nacional ({br(rb['n'], 0)})"),
        kpi("Média Enade", br(ru["enade"]), delta=dif(ru["enade"], rb["enade"])),
        kpi("Média CPC", br(ru["cpc"]), delta=dif(ru["cpc"], rb["cpc"]), destaque=True),
        kpi("CPC 4 ou 5", pct(ru["pct45_cpc"]), delta=dif(ru["pct45_cpc"], rb["pct45_cpc"], pp=True)),
        kpi("Enade 4 ou 5", pct(ru["pct45_enade"]), delta=dif(ru["pct45_enade"], rb["pct45_enade"], pp=True)),
    )

    c1, c2 = st.columns(2, gap="medium")
    with c1, card("uf_fe"):
        secao("Distribuição", "Faixas do Conceito Enade", f"{uf} × Brasil")
        mostrar(distribuicao_faixas({uf: uf_ano["enade_faixa"], "Brasil": br_ano["enade_faixa"]}))
    with c2, card("uf_fc"):
        secao("Distribuição", "Faixas do CPC", f"{uf} × Brasil")
        mostrar(distribuicao_faixas({uf: uf_ano["cpc_faixa"], "Brasil": br_ano["cpc_faixa"]}))

    bloco(f"Ranking em {uf}", f"{titulo(area)} · {ano} · ordenado pelo CPC contínuo")
    with card("uf_rank"):
        ies_opts = ["(nenhuma)"] + sorted(uf_ano["ies_label"].unique())
        padrao = uf_ano.loc[uf_ano["ies_id"] == UNILAVRAS, "ies_label"]
        c1, _ = st.columns([2, 3])
        destaque = c1.selectbox("Destacar instituição", ies_opts, index=idx(ies_opts, padrao.iloc[0] if len(padrao) else "(nenhuma)"))
        rk = uf_ano.dropna(subset=["cpc_continuo"]).sort_values("cpc_continuo")
        rk = rk.assign(nome=rk["ies_sigla_atual"].fillna(rk["ies_nome_atual"]).astype(str).str.slice(0, 38) + " · " + rk["municipio"].str.title())
        cores = ([COR_CURSO if l == destaque else COR_NEUTRA for l in rk["ies_label"]] if destaque != "(nenhuma)"
                 else [COR_FAIXA[f] for f in rk["cpc_faixa"]])
        fig = go.Figure(go.Bar(
            y=rk["nome"], x=rk["cpc_continuo"], orientation="h", marker=dict(color=cores, cornerradius=5),
            text=rk["cpc_faixa"], textposition="outside", textfont=dict(color=TINTA_2, size=11),
            customdata=rk[["ies_nome_atual", "cpc_faixa", "enade_continuo", "enade_faixa"]].values,
            hovertemplate="<b>%{customdata[0]}</b><br>CPC contínuo: %{x:.3f} (faixa %{customdata[1]})"
                          "<br>Enade contínuo: %{customdata[2]:.3f} (faixa %{customdata[3]})<extra></extra>",
        ))
        fig.add_vline(x=rb["cpc"], line=dict(color=COR_BR, dash="dot", width=2), annotation_text=f"Brasil {br(rb['cpc'])}",
                      annotation_position="bottom right", annotation_font=dict(color=TINTA_2))
        fig.add_vline(x=ru["cpc"], line=dict(color=COR_UF, dash="dot", width=2), annotation_text=f"{uf} {br(ru['cpc'])}",
                      annotation_position="top right", annotation_font=dict(color=TINTA_2))
        fig.update_layout(xaxis=dict(range=[0, 5.25], side="top"), bargap=0.22)
        fig.update_yaxes(tickfont=dict(color=TINTA, size=12))
        mostrar(ajustar(fig, altura=max(320, 24 * len(rk) + 90), legenda=False))

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, card("uf_cmp"):
        secao("Contexto nacional", "CPC médio por UF", f"{uf} em destaque")
        g = br_ano.groupby("uf", as_index=False).agg(cpc=("cpc_continuo", "mean"), enade=("enade_continuo", "mean"), n=("area", "size")).sort_values("cpc", ascending=False)
        fig = px.bar(g, x="uf", y="cpc", custom_data=["n", "enade"], labels={"uf": "", "cpc": ""})
        fig.update_traces(marker_color=[COR_UF if u == uf else COR_NEUTRA for u in g["uf"]], marker_cornerradius=5,
                          hovertemplate="%{x}<br>CPC médio: <b>%{y:.2f}</b><br>Enade médio: %{customdata[1]:.2f}<br>%{customdata[0]} cursos<extra></extra>")
        mostrar(ajustar(fig, altura=320, legenda=False))
    with c2, card("uf_cat"):
        secao("Perfil", f"Cursos em {uf} por categoria")
        cat = uf_ano.dropna(subset=["cat_administrativa"])
        if cat.empty:
            st.info("A planilha deste ano não informa a categoria administrativa.")
        else:
            g = cat.groupby("cat_administrativa", as_index=False).agg(n=("area", "size"), cpc=("cpc_continuo", "mean")).sort_values("n")
            fig = px.bar(g, y="cat_administrativa", x="n", orientation="h", text="n", custom_data=["cpc"], labels={"cat_administrativa": "", "n": ""})
            fig.update_traces(marker_color=COR_CURSO, marker_cornerradius=5, textposition="outside",
                              hovertemplate="%{y}<br>%{x} cursos<br>CPC médio: %{customdata[0]:.2f}<extra></extra>")
            fig.update_xaxes(showticklabels=False)
            mostrar(ajustar(fig, altura=320, legenda=False))

    with st.expander(f"Tabela completa — {titulo(area)} · {uf} · {ano}", icon="📋"):
        tabela_cursos(uf_ano, f"{area.lower()}_{uf}_{ano}.csv")


def pagina_comparar():
    topo = st.empty()
    with filtros("cmp"):
        c1, c2 = st.columns([3, 2])
        areas_f = c1.multiselect("Filtrar áreas", lista_areas(), default=["ODONTOLOGIA"], format_func=titulo, key="esp_areas", placeholder="Todas")
        ufs = sorted(CPC["uf"].dropna().unique())
        ufs_f = c2.multiselect("Filtrar UFs", ufs, default=["MG"], key="esp_ufs", placeholder="Todas")
        pool = CPC
        if areas_f:
            pool = pool[pool["area"].isin(areas_f)]
        if ufs_f:
            pool = pool[pool["uf"].isin(ufs_f)]
        ofertas = pool.sort_values("ano").drop_duplicates("curso_chave", keep="last").sort_values("oferta_label")
        rot = dict(zip(ofertas["curso_chave"], ofertas["oferta_label"]))
        padrao = ofertas.loc[ofertas["ies_id"] == UNILAVRAS, "curso_chave"].tolist()[:1]
        escolhidos = st.multiselect("Cursos a comparar (até 8)", list(rot), default=padrao, format_func=rot.get, max_selections=8,
                                    placeholder="Escolha…", help="Digite parte do nome da IES ou do município para buscar.")
    hero(topo, "Comparações", "Compare <em>cursos</em>",
         "Coloque lado a lado o mesmo curso em instituições diferentes — ou cursos diferentes — e acompanhe a trajetória de cada um.",
         [f"{len(escolhidos)} curso(s) selecionado(s)", "Até 8 cursos"])
    if len(escolhidos) < 2:
        st.info("Escolha dois ou mais cursos para comparar.")
    if escolhidos:
        d = CPC[CPC["curso_chave"].isin(escolhidos)]
        cor = {k: COR_SERIE[i] for i, k in enumerate(escolhidos)}
        ult = d.sort_values("ano").groupby("curso_chave").tail(1).set_index("curso_chave")
        st.html('<div class="kpis">' + "".join(
            kpi(escape(rot[k]), faixa=ult.loc[k, "cpc_faixa"], sub=f"CPC {br(ult.loc[k, 'cpc_continuo'], 3)} · Enade {ult.loc[k, 'enade_faixa']} · {ult.loc[k, 'ano']}")
            for k in escolhidos) + "</div>")
        c1, c2 = st.columns(2, gap="medium")
        for col, campo, nome, ch in [(c1, "enade_continuo", "Conceito Enade contínuo", "c"), (c2, "cpc_continuo", "CPC contínuo", "d")]:
            with col, card(f"esp_{ch}"):
                secao("Trajetória", nome)
                series = []
                for k in escolhidos:
                    s = d[d["curso_chave"] == k].groupby("ano")[campo].mean()
                    series.append((rot[k], s.index, s.values, cor[k], True, False))
                fig = linha_evolucao(series, altura=380)
                fig.update_layout(hovermode="closest")
                mostrar(fig)

        with card("esp_comp"):
            c1, _ = st.columns([1, 4])
            ano = c1.selectbox("Edição", sorted(d["ano"].unique())[::-1], key="esp_ano")
            secao("Insumos", f"Composição do CPC em {ano}")
            u = d[d["ano"] == ano]
            linhas = [{"curso": rot[k], "indicador": nome, "valor": u.loc[u["curso_chave"] == k, c].mean()}
                      for k in escolhidos if (u["curso_chave"] == k).any() for c, nome in INDICADORES]
            if linhas:
                fig = px.bar(pd.DataFrame(linhas), x="indicador", y="valor", color="curso", barmode="group",
                             color_discrete_map={rot[k]: cor[k] for k in escolhidos}, labels={"indicador": "", "valor": "", "curso": ""})
                fig.update_traces(marker_cornerradius=4, hovertemplate="%{x}<br>%{fullData.name}: <b>%{y:.3f}</b><extra></extra>")
                fig.update_yaxes(range=[0, 5.2])
                mostrar(ajustar(fig, altura=440))
        with st.expander("Tabela dos cursos selecionados", icon="📋"):
            t = d.assign(Curso=d["curso_chave"].map(rot))[["Curso", "ano", "participantes", "enade_continuo", "enade_faixa", "idd", "cpc_continuo", "cpc_faixa"]]
            st.dataframe(t.sort_values(["Curso", "ano"]).rename(columns={"ano": "Ano", "participantes": "Participantes", "enade_continuo": "Enade contínuo",
                                                                        "enade_faixa": "Enade faixa", "idd": "IDD", "cpc_continuo": "CPC contínuo", "cpc_faixa": "CPC faixa"}),
                         hide_index=True, use_container_width=True)


def pagina_igc():
    topo = st.empty()
    with filtros("igc"):
        ies = IGC.sort_values("ano").drop_duplicates("ies_id", keep="last").sort_values("ies_label")
        ids = ies["ies_id"].tolist()
        nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
        c1, c2 = st.columns([2, 3])
        iid = c1.selectbox("Instituição", ids, index=idx(ids, UNILAVRAS), format_func=nomes.get)
        outras = c2.multiselect("Comparar com outras IES", [i for i in ids if i != iid], format_func=nomes.get, max_selections=6, placeholder="Escolha…")
    d = IGC[IGC["ies_id"] == iid].sort_values("ano")
    x = d.iloc[-1]
    uf_ult = IGC[(IGC["ano"] == x["ano"]) & (IGC["uf"] == x["uf"])]
    br_ult = IGC[IGC["ano"] == x["ano"]]
    hero(topo, "Índice Geral de Cursos", f"{escape(titulo(x['ies_nome']))}",
         f"Evolução do IGC da instituição e comparação com o estado ({x['uf']}) e o Brasil.",
         [x["org_academica"], x["cat_administrativa"], x["uf"], f"Edições {', '.join(map(str, d['ano']))}"], numeral=x["ano"])

    kpis(
        kpi(f"IGC {x['ano']}", faixa=x["igc_faixa"]),
        kpi("IGC contínuo", br(x["igc_continuo"], 3), delta=dif(x["igc_continuo"], br_ult["igc_continuo"].mean()), destaque=True),
        kpi("Conceito médio da graduação", br(x["conceito_graduacao"], 3), sub=f"peso α = {br(x['alfa'], 3)}"),
        kpi("Cursos com CPC no triênio", br(x["n_cursos_cpc"], 0)),
    )
    st.html('<div class="rank-row">'
            + rank_html(f"Posição em {x['uf']} · {x['ano']}", posicao(uf_ult, x["igc_continuo"], "igc_continuo"), "das IES do estado")
            + rank_html(f"Posição no Brasil · {x['ano']}", posicao(br_ult, x["igc_continuo"], "igc_continuo"), "das IES do país")
            + "</div>")
    st.html('<div class="timeline">' + "".join(
        f'<div class="tl"><div class="tl-ano">{y.ano}</div>{selo(y.igc_faixa)}<div class="tl-v">contínuo {br(y.igc_continuo, 3)}</div></div>'
        for y in d.itertuples()) + "</div>")

    with card("igc_ev"):
        secao("Trajetória", "IGC contínuo por edição")
        m_br = IGC.groupby("ano")["igc_continuo"].mean()
        m_uf = IGC[IGC["uf"] == x["uf"]].groupby("ano")["igc_continuo"].mean()
        series = [("Média Brasil", m_br.index, m_br.values, COR_NEUTRA, False, True),
                  (f"Média {x['uf']}", m_uf.index, m_uf.values, "#9aa3b5", False, True)]
        for i, sid in enumerate([iid] + outras):
            s = IGC[IGC["ies_id"] == sid].sort_values("ano")
            series.append((titulo(nomes[sid]), s["ano"], s["igc_continuo"], COR_SERIE[i], i == 0, False))
        fig = linha_evolucao(series, altura=400, rotulos_em=titulo(nomes[iid]), faixa_y=(1.5, 5))
        fig.update_layout(hovermode="closest", xaxis=dict(tickmode="array", tickvals=sorted(IGC["ano"].unique())))
        mostrar(fig)

    st.html('<div class="nota">Para ver o CPC de cada curso desta instituição, use a página <b>Cursos da IES</b>.</div>')
    with card("igc_rank"):
        anos_uf = sorted(IGC.loc[IGC["uf"] == x["uf"], "ano"].unique())[::-1]
        c1, c2, c3 = st.columns([1.3, 2.4, 2.4])
        ano_rk = c1.selectbox("Ano", anos_uf, index=idx(anos_uf, x["ano"]), key="igc_rank_ano")
        uf_ano = IGC[(IGC["ano"] == ano_rk) & (IGC["uf"] == x["uf"])].dropna(subset=["igc_continuo"])
        cats = c2.multiselect("Categoria administrativa", sorted(uf_ano["cat_administrativa"].dropna().unique()),
                              placeholder="Todas", key="igc_rank_cat")
        orgs = c3.multiselect("Organização acadêmica", sorted(uf_ano["org_academica"].dropna().unique()),
                              placeholder="Todas", key="igc_rank_org")
        if cats:
            uf_ano = uf_ano[uf_ano["cat_administrativa"].isin(cats)]
        if orgs:
            uf_ano = uf_ano[uf_ano["org_academica"].isin(orgs)]
        filtro_txt = " · ".join(filter(None, [", ".join(cats), ", ".join(orgs)]))
        secao("Ranking", f"IGC em {x['uf']} · {ano_rk}", f"Filtro: {escape(filtro_txt)}" if filtro_txt else "Todas as instituições do estado")
        rk = uf_ano.sort_values("igc_continuo", ascending=False)[["ies_id", "ies_label", "igc_continuo", "igc_faixa"]]
        rk.insert(0, "Pos.", range(1, len(rk) + 1))
        if (rk["ies_id"] == iid).any():
            pos = int(rk.loc[rk["ies_id"] == iid, "Pos."].iloc[0])
            st.html('<div class="rank-row" style="margin-top:4px">'
                    + rank_html(f"{escape(titulo(nomes[iid]))} · {ano_rk}", (pos, len(rk), (len(rk) - pos) / len(rk)),
                               "das IES do filtro" if filtro_txt else "das IES do estado")
                    + "</div>")
        else:
            motivo = "não está no filtro selecionado" if filtro_txt else f"não tem IGC em {x['uf']} em {ano_rk}"
            st.html(f'<div class="nota">{escape(titulo(nomes[iid]))} {motivo}.</div>')
        if rk.empty:
            st.info("Nenhuma instituição com esses filtros.")
        t = rk.rename(columns={"ies_label": "IES", "igc_continuo": "IGC contínuo", "igc_faixa": "Faixa"})
        destaque = t["ies_id"] == iid
        estilo = t.drop(columns="ies_id").style.apply(
            lambda linha: ["background-color:#eaf2fc;font-weight:700" if destaque.loc[linha.name] else "" for _ in linha], axis=1)
        st.dataframe(estilo, hide_index=True, use_container_width=True, height=420,
                     column_config={"IGC contínuo": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=5)})

    with st.expander("Componentes do IGC por edição", icon="📋"):
        st.dataframe(d[["ano", "igc_faixa", "igc_continuo", "conceito_graduacao", "alfa", "conceito_mestrado", "beta", "conceito_doutorado", "gama", "n_cursos_cpc"]]
                     .rename(columns={"ano": "Ano", "igc_faixa": "Faixa", "igc_continuo": "Contínuo", "conceito_graduacao": "Graduação",
                                      "alfa": "α (grad.)", "conceito_mestrado": "Mestrado", "beta": "β (mestr.)",
                                      "conceito_doutorado": "Doutorado", "gama": "γ (dout.)", "n_cursos_cpc": "Cursos c/ CPC"}),
                     hide_index=True, use_container_width=True)


def pagina_sobre():
    topo = st.empty()
    hero(topo, "Metodologia", "Sobre <em>os dados</em>", "De onde vêm os números e como foram tratados.",
         [f"CPC {int(CPC['ano'].min())}–{int(CPC['ano'].max())}", f"IGC {int(IGC['ano'].min())}–{int(IGC['ano'].max())}", "Fonte: INEP"])
    st.html("<div style='height:18px'></div>")
    c1, c2 = st.columns([3, 2], gap="medium")
    with c1, card("sobre_txt"):
        secao("Tratamento", "Como a base foi montada")
        st.markdown("""
- **Fontes:** planilhas do INEP de CPC (2010–2023), IGC (2010–2023) e Conceito Enade das licenciaturas e de Medicina (2025),
  lidas automaticamente das pastas `Resultados CPC`, `Resultados IGC`, `Enade Licenciaturas` e `Enade Medicina` (o ano vem do nome do arquivo).
- Os nomes de colunas mudam a cada edição; o script `etl/consolidar.py` os padroniza.
- **Licenciaturas e Medicina (2025):** não há CPC; o Conceito Enade é definido pelo percentual de concluintes com desempenho
  igual ou acima do padrão, usado como indicador contínuo nessas seções. O histórico liga essas avaliações às edições anteriores do Enade regular.
- Nomes antigos de áreas (2010–2012) foram padronizados, ex.: "Engenharia (Grupo I) – Engenharia Civil" → "Engenharia Civil".
- A **faixa do Conceito Enade** é calculada a partir da nota contínua pela regra do INEP
  (1: < 0,945 · 2: < 1,945 · 3: < 2,945 · 4: < 3,945 · 5: ≥ 3,945), pois as planilhas de CPC não trazem a faixa.
- Em 2014–2018 e 2021 a planilha não traz o código da IES; ele foi recuperado pelo nome da IES em outros anos.
- Em 2013 e 2014 não há a coluna "Modalidade"; esses cursos foram considerados presenciais.
- A planilha de 2017 tinha cada linha repetida; as duplicatas foram removidas.
- **SC** = sem conceito (ex.: menos de 2 concluintes participantes).
- O histórico de um curso liga as edições por IES + área + município + modalidade.
- Médias são simples (cada curso pesa igual), sobre os cursos com valor calculado.
""")
    with c2, card("sobre_upd"):
        secao("Manutenção", "Como incluir uma nova edição")
        st.markdown("""
1. Salve a planilha do INEP na pasta certa dentro de `Resultados`, com o ano no nome do arquivo (ex.: `CPC 2026.xlsx`).
2. Dê dois cliques em **Atualizar Dados.bat**. O arquivo e a aba certa são encontrados automaticamente.
""")
    with card("sobre_cob"):
        secao("Cobertura", "Base de CPC por edição")
        cob = CPC.groupby("ano").agg(cursos=("area", "size"), areas=("area", "nunique"), ies=("ies_id", "nunique"),
                                     com_cpc=("cpc_continuo", lambda s: s.notna().sum())).reset_index()
        st.dataframe(cob.rename(columns={"ano": "Ano", "cursos": "Cursos", "areas": "Áreas", "ies": "IES", "com_cpc": "Com CPC"}),
                     hide_index=True, use_container_width=True)
    with st.expander("Áreas avaliadas em cada edição", icon="🗓️"):
        m = pd.crosstab(CPC["area"].map(titulo), CPC["ano"])
        st.dataframe(m.map(lambda v: "●" if v else ""), use_container_width=True, height=520)


# ================================================================ ENADE Licenciaturas / ENADE Medicina
# Avaliações no formato novo (a partir de 2025): não há CPC; o indicador contínuo é o
# percentual de concluintes com desempenho igual ou acima do padrão, que define a faixa do Conceito Enade.
PROGRAMAS = {"licenciaturas": "ENADE Licenciaturas", "medicina": "ENADE Medicina"}
IND_NOVO = "% acima do padrão"
NOTA_METODO = ("A partir de 2025 o Conceito Enade destas áreas é definido pelo percentual de concluintes com desempenho "
               "igual ou acima do padrão. As faixas das edições anteriores (Enade regular) usavam a nota contínua.")


@st.cache_data(show_spinner="Carregando bases…")
def carregar_novo(versao=None):
    arq = DADOS / "enade_novo.parquet"
    if not arq.exists():
        return pd.DataFrame(columns=["programa"])
    e = pd.read_parquet(arq)
    e["ies_nome_atual"], e["ies_sigla_atual"] = e["ies_nome"], e["ies_sigla"]
    e["ies_label"] = e["ies_nome"] + e["ies_sigla"].map(lambda s: f" ({s})" if pd.notna(s) and s else "")
    e["oferta_label"] = (
        e["area"].map(titulo) + " — " + e["ies_sigla"].fillna(e["ies_nome"]).astype(str)
        + " — " + e["municipio"].str.title() + "/" + e["uf"]
        + e["modalidade"].map(lambda m: " (EaD)" if "dist" in str(m).lower() else "")
    )
    return e


NOVO = carregar_novo(versao_dados())


def base_novo(prog):
    return NOVO[NOVO["programa"] == prog]


def resumo_novo(df: pd.DataFrame) -> dict:
    f = df.loc[df["enade_faixa"] != "SC", "enade_faixa"]
    part = df["participantes"].sum()
    return {
        "n": len(df),
        "n_conc": int(df["pct_acima"].notna().sum()),
        "pct": df["pct_acima"].mean(),
        "p45": f.isin(["4", "5"]).mean() if len(f) else float("nan"),
        "p12": f.isin(["1", "2"]).mean() if len(f) else float("nan"),
        "part": part,
        "insc": df["inscritos"].sum(),
        "acima": df["n_acima"].sum(),
    }


def area_novo(prog, dados, col, chave):
    """Seletor de área; Medicina tem uma só área e dispensa o seletor."""
    areas = sorted(dados["area"].unique())
    if len(areas) == 1:
        return areas[0]
    return col.selectbox("Curso (área de avaliação)", areas, index=idx(areas, "PEDAGOGIA (LICENCIATURA)"),
                         format_func=titulo, key=chave)


def ies_padrao(ids):
    return idx(ids, UNILAVRAS)


def rotulos_ofertas(df: pd.DataFrame) -> dict:
    """Rótulo curto de cada curso de uma IES: área, município (se houver vários) e EaD."""
    varios_mun = df["municipio"].nunique() > 1
    return {r.curso_chave: titulo(r.area).replace("Tecnologia em ", "Tec. em ")
            + (f" · {r.municipio.title()}" if varios_mun else "")
            + (" (EaD)" if "dist" in str(r.modalidade).lower() else "") for r in df.itertuples()}


def barras_media(df_grupo: pd.DataFrame, col_grupo: str, destaque=None, altura=320, horizontal=False):
    """Média do % acima do padrão por grupo (região, UF, categoria...)."""
    g = df_grupo.groupby(col_grupo, as_index=False).agg(v=("pct_acima", "mean"), n=("area", "size"))
    g = g.sort_values("v", ascending=horizontal)
    cores = [COR_UF if destaque is not None and x == destaque else (COR_NEUTRA if destaque is not None else COR_CURSO) for x in g[col_grupo]]
    if horizontal:
        fig = go.Figure(go.Bar(y=g[col_grupo], x=g["v"], orientation="h", marker=dict(color=cores, cornerradius=5),
                               text=g["v"].map(pct), textposition="outside", textfont=dict(color=TINTA), customdata=g[["n"]].values,
                               cliponaxis=False, hovertemplate="%{y}<br>Média: <b>%{x:.1%}</b><br>%{customdata[0]} cursos<extra></extra>"))
        fig.update_xaxes(range=[0, 1.12], showticklabels=False)
        fig.update_yaxes(tickfont=dict(color=TINTA))
    else:
        fig = go.Figure(go.Bar(x=g[col_grupo], y=g["v"], marker=dict(color=cores, cornerradius=5), customdata=g[["n"]].values,
                               hovertemplate="%{x}<br>Média: <b>%{y:.1%}</b><br>%{customdata[0]} cursos<extra></extra>"))
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig = ajustar(fig, altura=altura, legenda=False)
    fig.update_layout(margin=dict(r=40))
    return fig


def histograma_pct(valores: pd.Series, marca=None, rotulo_marca="este curso", altura=300):
    fig = go.Figure(go.Histogram(x=valores * 100, xbins=dict(start=0, end=100.01, size=5), marker=dict(color=COR_FAIXA["2"], line=dict(width=1.5, color="#fff")),
                                 hovertemplate="%{x}%: <b>%{y}</b> cursos<extra></extra>"))
    if marca is not None and pd.notna(marca):
        fig.add_vline(x=marca * 100, line=dict(color=COR_UF, width=3), annotation_text=f"{rotulo_marca}: {pct(marca)}",
                      annotation_position="top", annotation_font=dict(color=TINTA, size=12))
    fig.update_xaxes(range=[0, 100], ticksuffix="%", title=None)
    fig.update_yaxes(title=None)
    fig = ajustar(fig, altura=altura, legenda=False)
    fig.update_layout(margin=dict(t=34))
    return fig


def historico_faixas_area(area: str, novo_area: pd.DataFrame):
    """Distribuição das faixas por edição: Enade regular (bases de CPC) + edições novas."""
    antigo = CPC.loc[CPC["area"] == area, ["ano", "enade_faixa"]]
    tudo = pd.concat([antigo, novo_area[["ano", "enade_faixa"]]])
    dist = tudo.groupby(["ano", "enade_faixa"]).size().unstack(fill_value=0)
    dist = dist.div(dist.sum(axis=1), axis=0)
    fig = go.Figure()
    for f in FAIXAS:
        if f in dist:
            nome = "Sem conceito" if f == "SC" else f"Faixa {f}"
            fig.add_bar(x=dist.index.astype(str), y=dist[f], name=nome, marker=dict(color=COR_FAIXA[f], line=dict(width=2, color="#fff")),
                        hovertemplate="%{x}: <b>%{y:.1%}</b><extra>" + nome + "</extra>")
    fig.update_layout(barmode="stack", yaxis=dict(tickformat=".0%"), xaxis=dict(type="category"))
    return ajustar(fig, altura=340)


def mapa_html(chaves: list, rot: dict, anos: list, faixa: dict, dica: dict) -> str:
    """Grade curso × edição com o selo da faixa (faixa/dica: {(chave, ano): valor})."""
    cab = "".join(f"<th>{a}</th>" for a in anos)
    linhas = []
    for k in chaves:
        cels = []
        for a in anos:
            f = faixa.get((k, a))
            if f is None or pd.isna(f):
                cels.append('<td><span class="vazio"></span></td>')
            else:
                cels.append(f'<td title="{escape(rot[k])} · {a}: {escape(dica.get((k, a), ""))}">{selo(f)}</td>')
        linhas.append(f'<tr><td class="curso">{escape(rot[k])}</td>{"".join(cels)}</tr>')
    return f'<div class="mapa-wrap"><table class="mapa"><thead><tr><th></th>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'


def historico_cursos(chaves: list, novo: pd.DataFrame):
    """Faixas de cada curso em todas as edições: Enade regular (CPC) + formato novo."""
    antigo = CPC[CPC["curso_chave"].isin(chaves)]
    faixa, dica = {}, {}
    for r in antigo.itertuples():
        faixa[(r.curso_chave, r.ano)] = r.enade_faixa
        dica[(r.curso_chave, r.ano)] = f"Enade contínuo {br(r.enade_continuo, 3)}"
    for r in novo[novo["curso_chave"].isin(chaves)].itertuples():
        faixa[(r.curso_chave, r.ano)] = r.enade_faixa
        dica[(r.curso_chave, r.ano)] = f"{pct(r.pct_acima, 1)} acima do padrão"
    anos = sorted({a for _, a in faixa})
    return anos, faixa, dica


def tabela_novo(df: pd.DataFrame, nome_arquivo: str):
    cols = {
        "ies_nome": "IES", "ies_sigla": "Sigla", "area": "Área", "municipio": "Município", "uf": "UF", "modalidade": "Modalidade",
        "cat_administrativa": "Categoria", "inscritos": "Inscritos", "participantes": "Participantes",
        "n_acima": "Acima do padrão", "pct_acima": "% acima do padrão", "enade_faixa": "Conceito Enade",
    }
    t = df[list(cols)].rename(columns=cols).sort_values("% acima do padrão", ascending=False, na_position="last")
    t["Área"] = t["Área"].map(titulo)
    st.dataframe(t, hide_index=True, use_container_width=True,
                 column_config={"% acima do padrão": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                                "Inscritos": st.column_config.NumberColumn(format="%d"),
                                "Participantes": st.column_config.NumberColumn(format="%d"),
                                "Acima do padrão": st.column_config.NumberColumn(format="%d")})
    st.download_button("⬇  Baixar tabela (CSV)", t.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=nome_arquivo, mime="text/csv")


# ---------------------------------------------------------------- páginas (geradas para cada programa)
def pagina_nacional_novo(prog):
    nome = PROGRAMAS[prog]

    def pagina():
        dados = base_novo(prog)
        topo = st.empty()
        with filtros(f"{prog}_nac"):
            unica = dados["area"].nunique() == 1
            cols = st.columns([1, 2]) if unica else st.columns([3, 1, 2])
            area = area_novo(prog, dados, cols[0], f"{prog}_nac_area")
            d_area = dados[dados["area"] == area]
            i = 0 if unica else 1
            ano = cols[i].selectbox("Ano", sorted(d_area["ano"].unique())[::-1], key=f"{prog}_nac_ano")
            base, mod = filtro_modalidade(d_area[d_area["ano"] == ano], f"{prog}_nac_mod", cols[i + 1])
        r = resumo_novo(base)
        hero(topo, f"{nome} · Panorama nacional", f"{titulo(area)} <em>no Brasil</em>",
             f"Resultados da edição de {ano}. Indicador: percentual de concluintes com desempenho igual ou acima do padrão.",
             [f"{br(r['n'], 0)} cursos avaliados", f"{base['ies_id'].nunique()} instituições", f"{base['uf'].nunique()} UFs",
              mod if mod != "Todas" else "Todas as modalidades"], numeral=ano)
        kpis(
            kpi("Cursos avaliados", br(r["n"], 0), sub=f"{r['n_conc']} com conceito"),
            kpi("Concluintes acima do padrão", pct(r["pct"]), sub="média dos cursos", destaque=True),
            kpi("Conceito 4 ou 5", pct(r["p45"]), sub="dos cursos com conceito"),
            kpi("Conceito 1 ou 2", pct(r["p12"]), sub="dos cursos com conceito"),
            kpi("Concluintes participantes", br(r["part"], 0),
                sub=f"{br(r['acima'], 0)} acima do padrão ({pct(r['acima'] / r['part'] if r['part'] else None)})"),
        )
        c1, c2 = st.columns(2, gap="medium")
        with c1, card(f"{prog}_nac_fx"):
            if mod == "Todas" and base["modalidade"].nunique() > 1:
                secao("Distribuição", "Faixas do Conceito Enade", "Presencial × EaD")
                grupos = [(("EaD" if "dist" in m.lower() else "Presencial"), base.loc[base["modalidade"] == m, "enade_faixa"])
                          for m in sorted(base["modalidade"].unique(), key=lambda m: "dist" in m.lower())]
            else:
                secao("Distribuição", "Faixas do Conceito Enade")
                grupos = [("Brasil", base["enade_faixa"])]
            st.html(faixas_html(grupos))
        with c2, card(f"{prog}_nac_hist"):
            secao("Distribuição", "Percentual acima do padrão", "Número de cursos em cada intervalo de 5 pontos")
            mostrar(histograma_pct(base["pct_acima"].dropna(), altura=330))

        c1, c2 = st.columns([2, 3], gap="medium")
        with c1, card(f"{prog}_nac_reg"):
            secao("Geografia", "Média por região")
            mostrar(barras_media(base, "regiao", horizontal=True, altura=280))
        with c2, card(f"{prog}_nac_cat"):
            secao("Perfil institucional", "Média por categoria administrativa")
            mostrar(barras_media(base.dropna(subset=["cat_administrativa"]), "cat_administrativa", horizontal=True, altura=280))
        with card(f"{prog}_nac_uf"):
            secao("Geografia", "Média por UF", "Percentual médio de concluintes acima do padrão")
            mostrar(barras_media(base, "uf", altura=300))

        todas = dados[dados["ano"] == ano]
        if todas["area"].nunique() > 1:
            with card(f"{prog}_nac_areas"):
                secao("Contexto", "Comparação entre as áreas", f"{titulo(area)} em destaque")
                mostrar(barras_media(todas.assign(area_t=todas["area"].map(titulo)), "area_t", destaque=titulo(area),
                                     horizontal=True, altura=max(320, 30 * todas["area"].nunique() + 40)))

        bloco("Histórico no Enade", f"{titulo(area)} — distribuição das faixas em todas as edições")
        with card(f"{prog}_nac_ev"):
            secao("Tendência", "Faixas do Conceito Enade por edição")
            mostrar(historico_faixas_area(area, d_area))
            st.html(f'<div class="nota">{NOTA_METODO}</div>')

        with st.expander(f"Todos os cursos de {titulo(area)} em {ano}", icon="📋"):
            tabela_novo(base, f"{prog}_{ano}.csv")
    pagina.__name__ = f"nacional_{prog}"
    return pagina


def pagina_ies_novo(prog):
    nome = PROGRAMAS[prog]

    def pagina():
        dados = base_novo(prog)
        topo = st.empty()
        with filtros(f"{prog}_ies"):
            unica = dados["area"].nunique() == 1
            cols = st.columns([4, 1]) if unica else st.columns([2, 3, 1])
            area = area_novo(prog, dados, cols[0], f"{prog}_ies_area")
            d = dados[dados["area"] == area]
            ies = d.drop_duplicates("ies_id").sort_values("ies_label")
            ids = ies["ies_id"].tolist()
            nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
            j = 0 if unica else 1
            iid = cols[j].selectbox("Instituição (IES)", ids, index=ies_padrao(ids), format_func=nomes.get, key=f"{prog}_ies_ies")
            dd = d[d["ies_id"] == iid]
            ano = cols[j + 1].selectbox("Ano", sorted(dd["ano"].unique())[::-1], key=f"{prog}_ies_ano")
            linhas = dd[dd["ano"] == ano]
            if len(linhas) > 1:
                rot = linhas.apply(lambda x: f"{x['municipio'].title()}/{x['uf']} · {x['modalidade']}"
                                   + (f" · cód. {x['cod_curso']}" if x["cod_curso"] else ""), axis=1)
                esc = st.radio(f"{len(linhas)} cursos desta IES na área em {ano}", rot.index, format_func=rot.get,
                               horizontal=True, key=f"{prog}_ies_oferta")
                r = linhas.loc[esc]
            else:
                r = linhas.iloc[0]
        br_ano = d[d["ano"] == ano]
        uf_ano = br_ano[br_ano["uf"] == r["uf"]]
        rb, ru = resumo_novo(br_ano), resumo_novo(uf_ano)
        sigla = r["ies_sigla"] if pd.notna(r["ies_sigla"]) else ""
        hero(topo, escape(titulo(r["ies_nome"])) + (f" · {escape(sigla)}" if sigla else ""), f"{titulo(area)} <em>{ano}</em>",
             f"{r['municipio'].title()} / {r['uf']} — {nome}: resultado do curso comparado com o estado e com o Brasil.",
             [r["modalidade"], r["cat_administrativa"], r["org_academica"],
              f"Código do curso {r['cod_curso']}" if r["cod_curso"] else None,
              "CEBAS" if str(r.get("cebas", "")).strip().upper() == "SIM" else None], numeral=ano)

        kpis(
            kpi("Conceito Enade", faixa=r["enade_faixa"]),
            kpi("Concluintes acima do padrão", pct(r["pct_acima"], 1), delta=dif(r["pct_acima"], rb["pct"], pp=True), destaque=True),
            kpi("Acima do padrão", f"{br(r['n_acima'], 0)}<span class='k-of'>de {br(r['participantes'], 0)}<br>participantes</span>",
                sub=f"Participação de {pct(r['taxa_participacao'])}"),
            kpi(f"Média {r['uf']}", pct(ru["pct"], 1), sub=f"{ru['n']} cursos no estado"),
            kpi("Média Brasil", pct(rb["pct"], 1), sub=f"{rb['n']} cursos no país"),
        )
        st.html('<div class="rank-row">'
                + rank_html("Posição no Brasil", posicao(br_ano, r["pct_acima"], "pct_acima"))
                + rank_html(f"Posição em {r['uf']}", posicao(uf_ano, r["pct_acima"], "pct_acima"))
                + "</div>")

        c1, c2 = st.columns([2, 3], gap="medium")
        with c1, card(f"{prog}_ies_cmp"):
            secao("Comparação", "Concluintes acima do padrão", "Curso × estado × Brasil")
            g = pd.DataFrame({"grupo": ["Este curso", f"Média {r['uf']}", "Média Brasil"],
                              "v": [r["pct_acima"], ru["pct"], rb["pct"]], "cor": [COR_CURSO, COR_UF, COR_BR]})
            fig = go.Figure(go.Bar(x=g["grupo"], y=g["v"], marker=dict(color=g["cor"], cornerradius=6), text=g["v"].map(lambda v: pct(v, 1)),
                                   textposition="outside", textfont=dict(color=TINTA, size=13), cliponaxis=False,
                                   hovertemplate="%{x}: <b>%{y:.1%}</b><extra></extra>"))
            fig.update_yaxes(tickformat=".0%", range=[0, 1.1])
            mostrar(ajustar(fig, altura=320, legenda=False))
        with c2, card(f"{prog}_ies_dist"):
            secao("Posição", "Onde o curso está na distribuição nacional", "Número de cursos por faixa de % acima do padrão")
            mostrar(histograma_pct(br_ano["pct_acima"].dropna(), r["pct_acima"], altura=320))

        bloco("Histórico do curso", "faixa do Conceito Enade em todas as edições")
        anos, faixa, dica = historico_cursos([r["curso_chave"]], d)
        st.html('<div class="timeline">' + "".join(
            f'<div class="tl"><div class="tl-ano">{a}</div>{selo(faixa[(r["curso_chave"], a)])}'
            f'<div class="tl-v">{escape(dica[(r["curso_chave"], a)])}</div></div>' for a in anos) + "</div>")
        st.html(f'<div class="nota">{NOTA_METODO}' + (" Não há edições anteriores deste curso nas bases." if len(anos) <= 1 else "") + "</div>")
    pagina.__name__ = f"ies_{prog}"
    return pagina


def pagina_cursos_ies_novo(prog):
    nome = PROGRAMAS[prog]

    def pagina():
        dados = base_novo(prog)
        topo = st.empty()
        with filtros(f"{prog}_cies"):
            ies = dados.drop_duplicates("ies_id").sort_values("ies_label")
            ids = ies["ies_id"].tolist()
            nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
            c1, c2 = st.columns([4, 1])
            iid = c1.selectbox("Instituição (IES)", ids, index=ies_padrao(ids), format_func=nomes.get, key=f"{prog}_cies_ies")
            d_ies = dados[dados["ies_id"] == iid]
            ano = c2.selectbox("Ano", sorted(d_ies["ano"].unique())[::-1], key=f"{prog}_cies_ano")
        sel = d_ies[d_ies["ano"] == ano].copy()
        rot = rotulos_ofertas(sel)
        sel["curso"] = sel["curso_chave"].map(rot)
        ref = dados[dados["ano"] == ano].groupby("area")["pct_acima"].mean()
        sel["ref"] = sel["area"].map(ref)
        sel["dif"] = sel["pct_acima"] - sel["ref"]
        nac = dados[(dados["ano"] == ano) & dados["area"].isin(sel["area"])]
        info = sel.iloc[0]
        hero(topo, f"{nome} · Cursos da instituição", escape(titulo(info["ies_nome"])),
             f"Todos os cursos da instituição avaliados em {ano}, comparados com a média nacional da mesma área.",
             [info["org_academica"], info["cat_administrativa"], f"{sel['uf'].iloc[0]}", f"{len(sel)} cursos avaliados"], numeral=ano)
        com = sel[sel["pct_acima"].notna()]
        acima = int((com["dif"] > 0).sum())
        rs, rn = resumo_novo(sel), resumo_novo(nac)
        kpis(
            kpi("Cursos", br(len(sel), 0), sub=f"{len(com)} com conceito"),
            kpi("Acima do padrão (média)", pct(rs["pct"], 1), delta=dif(rs["pct"], com["ref"].mean(), pp=True), destaque=True,
                sub="vs média nacional das mesmas áreas"),
            kpi("Conceito 4 ou 5", pct(rs["p45"]), delta=dif(rs["p45"], rn["p45"], pp=True)),
            kpi("Conceito 1 ou 2", pct(rs["p12"]), delta=dif(rs["p12"], rn["p12"], pp=True, menor_melhor=True)),
            kpi("Acima da média nacional", f"{acima}<span class='k-of'>de {len(com)}<br>cursos</span>"),
        )
        c1, c2 = st.columns([3, 2], gap="medium")
        with c1, card(f"{prog}_cies_sit"):
            secao("Situação", "Concluintes acima do padrão em cada curso", "Barra na cor da faixa · ◆ = média nacional da área")
            st.html(situacao_html(sel.sort_values("pct_acima", ascending=False, na_position="last"), "pct_acima", "enade_faixa",
                                  IND_NOVO, escala_pct=True, mostrar_ano=False))
        with c2, card(f"{prog}_cies_fx"):
            secao("Distribuição", "Faixas do Conceito Enade", "Esta IES × Brasil (mesmas áreas)")
            st.html(faixas_comparadas(sel["enade_faixa"], nac["enade_faixa"], "Esta IES", "Brasil"))
        if len(com) > 1:
            with card(f"{prog}_cies_dif"):
                secao("Desempenho relativo", "Diferença para a média nacional", "% acima do padrão do curso menos a média nacional da área (pontos percentuais)")
                st.html(divergente_html(com.sort_values("dif", ascending=False), fmt=lambda x: br(x * 100, 1) + " p.p."))

        bloco("Mapa de conceitos", "faixa de cada curso em todas as edições do Enade")
        chaves = sorted(rot, key=lambda k: rot[k])
        anos, faixa, dica = historico_cursos(chaves, dados)
        with card(f"{prog}_cies_mapa"):
            st.html(mapa_html(chaves, rot, anos, faixa, dica))
            st.html(f'<div class="nota">{NOTA_METODO} Células vazias: o curso não foi avaliado naquela edição.</div>')
        with st.expander("Tabela dos cursos", icon="📋"):
            tabela_novo(sel, f"{prog}_cursos_{iid}_{ano}.csv")
    pagina.__name__ = f"cursos_ies_{prog}"
    return pagina


def pagina_estado_novo(prog):
    nome = PROGRAMAS[prog]

    def pagina():
        dados = base_novo(prog)
        topo = st.empty()
        with filtros(f"{prog}_uf"):
            unica = dados["area"].nunique() == 1
            cols = st.columns([1, 1, 2]) if unica else st.columns([3, 1, 1, 2])
            area = area_novo(prog, dados, cols[0], f"{prog}_uf_area")
            j = 0 if unica else 1
            ufs = sorted(dados["uf"].dropna().unique())
            uf = cols[j].selectbox("UF", ufs, index=idx(ufs, "MG"), key=f"{prog}_uf_uf")
            d_area = dados[dados["area"] == area]
            ano = cols[j + 1].selectbox("Ano", sorted(d_area["ano"].unique())[::-1], key=f"{prog}_uf_ano")
            br_ano, mod = filtro_modalidade(d_area[d_area["ano"] == ano], f"{prog}_uf_mod", cols[j + 2])
        uf_ano = br_ano[br_ano["uf"] == uf]
        hero(topo, f"{nome} · Curso no estado", f"{titulo(area)} <em>em {uf}</em>",
             f"Os cursos de {titulo(area)} de {uf} na edição de {ano}, comparados com o restante do Brasil.",
             [f"{len(uf_ano)} cursos em {uf}", f"{uf_ano['ies_id'].nunique()} instituições",
              mod if mod != "Todas" else "Todas as modalidades"], numeral=ano)
        if uf_ano.empty:
            st.warning(f"Nenhum curso de {titulo(area)} avaliado em {uf} em {ano}.")
            return
        ru, rb = resumo_novo(uf_ano), resumo_novo(br_ano)
        kpis(
            kpi(f"Cursos em {uf}", br(ru["n"], 0), sub=f"{pct(ru['n'] / rb['n'], 1)} do total nacional ({br(rb['n'], 0)})"),
            kpi("Acima do padrão (média)", pct(ru["pct"], 1), delta=dif(ru["pct"], rb["pct"], pp=True), destaque=True),
            kpi("Conceito 4 ou 5", pct(ru["p45"]), delta=dif(ru["p45"], rb["p45"], pp=True)),
            kpi("Conceito 1 ou 2", pct(ru["p12"]), delta=dif(ru["p12"], rb["p12"], pp=True, menor_melhor=True)),
        )
        c1, c2 = st.columns([2, 3], gap="medium")
        with c1, card(f"{prog}_uf_fx"):
            secao("Distribuição", "Faixas do Conceito Enade", f"{uf} × Brasil")
            st.html(faixas_comparadas(uf_ano["enade_faixa"], br_ano["enade_faixa"], uf, "Brasil"))
        with c2, card(f"{prog}_uf_rank"):
            rk = uf_ano.copy()
            rk["curso"] = rk["ies_sigla"].fillna(rk["ies_nome"]).astype(str).str.slice(0, 34) + " · " + rk["municipio"].str.title() \
                + rk["modalidade"].map(lambda m: " (EaD)" if "dist" in str(m).lower() else "")
            rk["ref"] = rb["pct"]
            secao("Ranking", f"Cursos de {titulo(area)} em {uf}", "Ordenado pelo % acima do padrão · ◆ = média nacional"
                  + (" · Unilavras em destaque" if (rk["ies_id"] == UNILAVRAS).any() else ""))
            st.html(situacao_html(rk.sort_values("pct_acima", ascending=False, na_position="last"), "pct_acima", "enade_faixa",
                                  IND_NOVO, escala_pct=True, mostrar_ano=False, destaque=UNILAVRAS))
        with card(f"{prog}_uf_ufs"):
            secao("Contexto nacional", "Média por UF", f"{uf} em destaque")
            mostrar(barras_media(br_ano, "uf", destaque=uf, altura=300))
        with st.expander(f"Tabela completa — {titulo(area)} · {uf} · {ano}", icon="📋"):
            tabela_novo(uf_ano, f"{prog}_{uf}_{ano}.csv")
    pagina.__name__ = f"estado_{prog}"
    return pagina


def pagina_comparar_novo(prog):
    nome = PROGRAMAS[prog]

    def pagina():
        dados = base_novo(prog)
        topo = st.empty()
        with filtros(f"{prog}_cmp"):
            unica = dados["area"].nunique() == 1
            if unica:
                ufs = sorted(dados["uf"].dropna().unique())
                ufs_f = st.multiselect("Filtrar UFs", ufs, default=["MG"], key=f"{prog}_cmp_ufs", placeholder="Todas")
                areas_f = []
            else:
                c1, c2 = st.columns([3, 2])
                areas_f = c1.multiselect("Filtrar áreas", sorted(dados["area"].unique()), default=["PEDAGOGIA (LICENCIATURA)"],
                                         format_func=titulo, key=f"{prog}_cmp_areas", placeholder="Todas")
                ufs = sorted(dados["uf"].dropna().unique())
                ufs_f = c2.multiselect("Filtrar UFs", ufs, default=["MG"], key=f"{prog}_cmp_ufs", placeholder="Todas")
            pool = dados
            if areas_f:
                pool = pool[pool["area"].isin(areas_f)]
            if ufs_f:
                pool = pool[pool["uf"].isin(ufs_f)]
            ofertas = pool.sort_values("ano").drop_duplicates("curso_chave", keep="last").sort_values("oferta_label")
            rot = dict(zip(ofertas["curso_chave"], ofertas["oferta_label"]))
            padrao = ofertas.loc[ofertas["ies_id"] == UNILAVRAS, "curso_chave"].tolist()[:1]
            escolhidos = st.multiselect("Cursos a comparar (até 8)", list(rot), default=padrao, format_func=rot.get, max_selections=8,
                                        placeholder="Escolha…", key=f"{prog}_cmp_sel",
                                        help="Digite parte do nome da IES ou do município para buscar.")
        hero(topo, f"{nome} · Comparações", "Compare <em>cursos</em>",
             "Coloque lado a lado o mesmo curso em instituições diferentes — ou cursos diferentes — e veja a trajetória de cada um no Enade.",
             [f"{len(escolhidos)} curso(s) selecionado(s)", "Até 8 cursos"])
        if len(escolhidos) < 2:
            st.info("Escolha dois ou mais cursos para comparar.")
        if not escolhidos:
            return
        ult = dados[dados["curso_chave"].isin(escolhidos)].sort_values("ano").groupby("curso_chave").tail(1).set_index("curso_chave")
        st.html('<div class="kpis">' + "".join(
            kpi(escape(rot[k]), faixa=ult.loc[k, "enade_faixa"],
                sub=f"{pct(ult.loc[k, 'pct_acima'], 1)} acima do padrão · {ult.loc[k, 'ano']}") for k in escolhidos) + "</div>")
        u = ult.loc[escolhidos].reset_index()
        u["curso"] = u["curso_chave"].map(rot)
        u["ref"] = u.apply(lambda x: dados.loc[(dados["area"] == x["area"]) & (dados["ano"] == x["ano"]), "pct_acima"].mean(), axis=1)
        with card(f"{prog}_cmp_sit"):
            secao("Situação", "Concluintes acima do padrão", "Barra na cor da faixa · ◆ = média nacional da área")
            st.html(situacao_html(u.sort_values("pct_acima", ascending=False, na_position="last"), "pct_acima", "enade_faixa",
                                  IND_NOVO, escala_pct=True))
        bloco("Trajetória no Enade", "faixa de cada curso em todas as edições")
        anos, faixa, dica = historico_cursos(escolhidos, dados)
        with card(f"{prog}_cmp_mapa"):
            st.html(mapa_html(escolhidos, rot, anos, faixa, dica))
            st.html(f'<div class="nota">{NOTA_METODO}</div>')
        with st.expander("Tabela dos cursos selecionados", icon="📋"):
            tabela_novo(dados[dados["curso_chave"].isin(escolhidos)], f"{prog}_comparacao.csv")
    pagina.__name__ = f"comparar_{prog}"
    return pagina


# ---------------------------------------------------------------- Curso por cidade (todas as seções)
# indicador -> (coluna do valor, coluna da faixa, escala em %)
INDICADORES_CIDADE = {
    None: {
        "CPC": ("cpc_continuo", "cpc_faixa", False),
        "Conceito Enade": ("enade_continuo", "enade_faixa", False),
        "IDD": ("idd", "idd_faixa", False),
    },
    "novo": {
        "% acima do padrão": ("pct_acima", "enade_faixa", True),
        "Taxa de participação": ("taxa_participacao", "enade_faixa", True),
    },
}


def rotulo_local(df: pd.DataFrame) -> pd.Series:
    """Nome curto de cada curso dentro de uma cidade: sigla da IES (+ EaD); código do curso se repetir."""
    base = df["ies_sigla_atual"].fillna(df["ies_nome_atual"]).astype(str).str.slice(0, 40) \
        + df["modalidade"].map(lambda m: " (EaD)" if "dist" in str(m).lower() else "")
    dup = base.duplicated(keep=False)
    return base.where(~dup, base + " · cód. " + df["cod_curso"].astype(str))


def pagina_cidade(prog=None):
    rotulo_secao = "ENADE" if prog is None else PROGRAMAS[prog]
    inds = INDICADORES_CIDADE[None if prog is None else "novo"]
    chave = prog or "enade"

    def pagina():
        dados = CPC if prog is None else base_novo(prog)
        topo = st.empty()
        with filtros(f"cid_{chave}"):
            unica = dados["area"].nunique() == 1
            if unica:
                area = dados["area"].iloc[0]
                c_ano, c_ind, _ = st.columns([1.3, 1.7, 3])
            else:
                c_area, c_ano, c_ind = st.columns([3, 1.2, 1.6])
                areas = sorted(dados["area"].dropna().unique())
                padrao_area = "ODONTOLOGIA" if prog is None else "PEDAGOGIA (LICENCIATURA)"
                area = c_area.selectbox("Curso (área de avaliação)", areas, index=idx(areas, padrao_area), format_func=titulo,
                                        key=f"cid_{chave}_area")
            d_area = dados[dados["area"] == area]
            ano = c_ano.selectbox("Edição", sorted(d_area["ano"].unique())[::-1], key=f"cid_{chave}_ano")
            ind = c_ind.selectbox("Indicador", list(inds), key=f"cid_{chave}_ind")
            d_ano = d_area[d_area["ano"] == ano]

            # Estado e cidade (padrão: onde está a Unilavras, se ela oferece o curso; senão MG)
            c_uf, c_mun, c_ies = st.columns([1.2, 2, 2.8])
            base_unl = d_ano[d_ano["ies_id"] == UNILAVRAS]
            uf_padrao = base_unl["uf"].iloc[0] if len(base_unl) else "MG"
            ufs = sorted(d_ano["uf"].dropna().unique())
            uf = c_uf.selectbox("Estado", ufs, index=idx(ufs, uf_padrao), key=f"cid_{chave}_uf")
            d_uf = d_ano[d_ano["uf"] == uf]
            muns = sorted(d_uf["municipio"].dropna().unique())
            mun_padrao = base_unl["municipio"].iloc[0] if len(base_unl) and base_unl["uf"].iloc[0] == uf else None
            if mun_padrao is None:  # cidade com mais cursos no estado
                mun_padrao = d_uf["municipio"].value_counts().index[0] if len(d_uf) else None
            mun = c_mun.selectbox("Cidade", muns, index=idx(muns, mun_padrao), format_func=lambda m: m.title(), key=f"cid_{chave}_mun")

            # IES da cidade (opcional, para destacar)
            d_cid = d_uf[d_uf["municipio"] == mun]
            ies = d_cid.drop_duplicates("ies_id").sort_values("ies_label")
            nomes = dict(zip(ies["ies_id"], ies["ies_label"]))
            ids = [None] + ies["ies_id"].tolist()
            iid = c_ies.selectbox("Instituição em destaque (IES)", ids, index=idx(ids, UNILAVRAS, padrao=1 if len(ids) > 1 else 0),
                                  format_func=lambda i: "(nenhuma)" if i is None else nomes[i], key=f"cid_{chave}_ies")

        col_v, col_f, escala = inds[ind]
        fmt = (lambda v: pct(v, 1)) if escala else (lambda v: br(v))
        cidade = d_cid.copy()
        uf_df = d_uf
        m_c, m_u, m_b = cidade[col_v].mean(), uf_df[col_v].mean(), d_ano[col_v].mean()
        cidade["curso"] = rotulo_local(cidade)
        cidade["ref"] = m_b
        if iid is None:
            sigla = None
        else:
            sigla = nomes[iid].split("(")[-1].rstrip(")") if "(" in nomes[iid] else titulo(nomes[iid])

        hero(topo, f"{rotulo_secao} · Curso por cidade", f"{titulo(area)} <em>em {escape(mun.title())}</em>",
             f"{escape(mun.title())}/{uf} — todos os cursos da área na cidade na edição de {ano}, comparados com o estado e o Brasil. "
             f"Indicador: {ind}.",
             [f"{len(cidade)} curso(s) na cidade", f"{cidade['ies_id'].nunique()} instituição(ões)", f"Destaque: {sigla}" if sigla else None],
             numeral=ano)

        com = cidade.dropna(subset=[col_v]).sort_values(col_v, ascending=False)
        meus = com[com["ies_id"] == iid]
        if len(meus):
            pos = int((com[col_v] > meus[col_v].iloc[0]).sum()) + 1
            pos_html = f"{pos}º<span class='k-of'>de {len(com)}<br>na cidade</span>"
        else:
            pos_html = "—"
        f45 = lambda d: d.loc[d[col_f] != "SC", col_f].isin(["4", "5"]).mean() if (d[col_f] != "SC").any() else float("nan")
        kpis(
            kpi("Cursos na cidade", br(len(cidade), 0), sub=f"{cidade['ies_id'].nunique()} instituição(ões)"),
            kpi(f"Posição · {escape(sigla)}", pos_html, sub=f"{ind}: {fmt(meus[col_v].iloc[0])}" if len(meus) else "sem valor nesta edição")
            if sigla else kpi("Melhor curso da cidade", escape(com["curso"].iloc[0]) if len(com) else "—",
                              sub=f"{ind}: {fmt(com[col_v].iloc[0])}" if len(com) else None),
            kpi("Faixa 4 ou 5 na cidade", pct(f45(cidade)), delta=dif(f45(cidade), f45(d_ano), pp=True)),
        )

        c1, c2 = st.columns([3, 2], gap="medium")
        with c1, card(f"cid_{chave}_rank"):
            secao("Concorrência local", f"Cursos de {titulo(area)} em {escape(mun.title())}",
                  f"Ordenado por {ind} · ◆ = média nacional" + (f" · {escape(sigla)} em destaque" if sigla else ""))
            st.html(situacao_html(cidade.sort_values(col_v, ascending=False, na_position="last"), col_v, col_f, ind,
                                  escala_pct=escala, mostrar_ano=False, destaque=iid))
        with c2, card(f"cid_{chave}_fx"):
            secao("Distribuição", "Faixas", f"{escape(mun.title())} × {uf} × Brasil")
            st.html(faixas_html([(mun.title(), cidade[col_f]), (uf, uf_df[col_f]), ("Brasil", d_ano[col_f])]))

        with card(f"cid_{chave}_cidades"):
            LIMITE = 15
            g = uf_df.groupby("municipio").agg(n=("area", "size"), ies=("ies_id", "nunique"), v=(col_v, "mean"))
            g = g.sort_values(["n", "v"], ascending=[False, False])
            total, total_cursos = len(g), int(g["n"].sum())
            secao("Contexto estadual", f"Cidades de {uf} com {titulo(area)}",
                  f"Quantidade de cursos avaliados por cidade em {ano} · {total_cursos} cursos em {total} cidades")
            ver_todas = False
            if total > LIMITE:
                ver_todas = st.toggle(f"Ver mais — mostrar todas as {total} cidades", key=f"cid_{chave}_todas")
            if not ver_todas and total > LIMITE:
                topo_g = g.head(LIMITE)
                if mun in g.index and mun not in topo_g.index:  # a cidade selecionada sempre aparece
                    topo_g = pd.concat([topo_g, g.loc[[mun]]])
                g = topo_g
            g = g.iloc[::-1]
            fig = go.Figure(go.Bar(
                y=[m.title() for m in g.index], x=g["n"], orientation="h",
                marker=dict(color=[COR_UF if m == mun else COR_CURSO for m in g.index], cornerradius=4),
                text=g["n"], textposition="outside", textfont=dict(color=TINTA, size=12), cliponaxis=False,
                customdata=list(zip(g["ies"], [fmt(v) for v in g["v"]])),
                hovertemplate="<b>%{y}</b><br>%{x} curso(s) · %{customdata[0]} instituição(ões)<br>"
                              + f"Média de {ind}: " + "%{customdata[1]}<extra></extra>"))
            fig.update_xaxes(range=[0, g["n"].max() * 1.15 + 0.5], showticklabels=False, showgrid=False)
            fig.update_yaxes(tickfont=dict(color=TINTA, size=12))
            fig = ajustar(fig, altura=max(220, 26 * len(g) + 40), legenda=False)
            fig.update_layout(margin=dict(t=10, r=30), bargap=0.3)
            mostrar(fig)
            if not ver_todas and total > LIMITE:
                st.html(f'<div class="nota">Exibindo as {LIMITE} cidades com mais cursos'
                        + (" e a cidade selecionada" if len(g) > LIMITE else "") + f". Ative “Ver mais” para ver todas as {total}.</div>")

        bloco("Trajetória na cidade", "faixa de cada curso em todas as edições")
        chaves = cidade.sort_values("curso")["curso_chave"].unique().tolist()
        rot = dict(zip(cidade["curso_chave"], cidade["curso"]))
        if prog is None:
            faixa, dica = {}, {}
            for r in CPC[CPC["curso_chave"].isin(chaves)].itertuples():
                faixa[(r.curso_chave, r.ano)] = getattr(r, col_f)
                dica[(r.curso_chave, r.ano)] = f"{ind} {br(getattr(r, col_v), 3)}"
            anos = sorted({a for _, a in faixa})
        else:
            anos, faixa, dica = historico_cursos(chaves, dados)
        with card(f"cid_{chave}_mapa"):
            st.html(mapa_html(chaves, rot, anos, faixa, dica))
            st.html('<div class="nota">' + (f"Faixa de {ind} em cada edição." if prog is None else NOTA_METODO)
                    + " Células vazias: o curso não foi avaliado naquela edição.</div>")

        with st.expander(f"Tabela — {titulo(area)} em {mun.title()}/{uf} · {ano}", icon="📋"):
            if prog is None:
                tabela_cursos(cidade, f"{area.lower()}_{mun.lower()}_{ano}.csv")
            else:
                tabela_novo(cidade, f"{prog}_{mun.lower()}_{ano}.csv")
    pagina.__name__ = f"cidade_{chave}"
    return pagina


def paginas_programa(prog, slug, icone_nac):
    if base_novo(prog).empty:
        return []
    return [
        st.Page(pagina_nacional_novo(prog), title="Panorama nacional", icon=icone_nac, url_path=f"{slug}-nacional"),
        st.Page(pagina_ies_novo(prog), title="Curso na IES", icon=":material/school:", url_path=f"{slug}-ies"),
        st.Page(pagina_cursos_ies_novo(prog), title="Cursos da IES", icon=":material/view_list:", url_path=f"{slug}-cursos-ies"),
        st.Page(pagina_estado_novo(prog), title="Curso no estado", icon=":material/map:", url_path=f"{slug}-estado"),
        st.Page(pagina_cidade(prog), title="Curso por cidade", icon=":material/location_city:", url_path=f"{slug}-cidade"),
        st.Page(pagina_comparar_novo(prog), title="Comparar cursos", icon=":material/compare_arrows:", url_path=f"{slug}-comparar"),
    ]


PAGINA_IES = st.Page(pagina_ies, title="Curso na IES", icon=":material/school:", url_path="ies")
SECOES = {
    "ENADE": [
        st.Page(pagina_nacional, title="Panorama nacional", icon=":material/public:", url_path="nacional", default=True),
        PAGINA_IES,
        st.Page(pagina_cursos_ies, title="Cursos da IES", icon=":material/view_list:", url_path="cursos-ies"),
        st.Page(pagina_estado, title="Curso no estado", icon=":material/map:", url_path="estado"),
        st.Page(pagina_cidade(None), title="Curso por cidade", icon=":material/location_city:", url_path="cidade"),
        st.Page(pagina_comparar, title="Comparar cursos", icon=":material/compare_arrows:", url_path="comparar"),
    ],
    "ENADE Licenciaturas": paginas_programa("licenciaturas", "lic", ":material/menu_book:"),
    "ENADE Medicina": paginas_programa("medicina", "med", ":material/stethoscope:"),
    "IGC": [st.Page(pagina_igc, title="Índice Geral de Cursos", icon=":material/account_balance:", url_path="igc")],
    "Informações": [st.Page(pagina_sobre, title="Sobre os dados", icon=":material/info:", url_path="sobre")],
}
pg = st.navigation({k: v for k, v in SECOES.items() if v}, expanded=True)
aplicar_estilo()
pg.run()
