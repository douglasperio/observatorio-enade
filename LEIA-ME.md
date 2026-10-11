# Observatório ENADE — Enade / CPC / IGC

## Como abrir
Dê dois cliques em **Iniciar Dashboard.bat**. O navegador abre em http://localhost:8501.

## Seções e páginas (menu lateral)

**ENADE** — Enade regular com CPC (2010–2023)
- **Panorama nacional** – um curso no Brasil em um ano (ex.: Odontologia 2023).
- **Curso na IES** – um curso em uma instituição em um ano, com histórico (ex.: Odontologia, Unilavras, 2013).
- **Cursos da IES** – todos os cursos de uma instituição: situação atual, mapa de conceitos por edição, comparação com a média nacional e atalho para o detalhe de cada curso.
- **Curso no estado** – um curso em uma UF em um ano, com ranking (ex.: Odontologia, MG, 2013).
- **Curso por cidade** – escolha curso, edição, indicador (CPC, Conceito Enade ou IDD), estado, cidade e a IES em destaque: mostra todos os cursos da área na cidade (concorrência local), faixas cidade × estado × Brasil, as cidades do estado e a trajetória de cada curso.
- **Comparar cursos** – compara até 8 cursos específicos (ex.: o mesmo curso em IES diferentes).

**ENADE Licenciaturas** e **ENADE Medicina** — formato novo (a partir de 2025)
- As mesmas análises: Panorama nacional, Curso na IES, Cursos da IES, Curso no estado, Curso por cidade e Comparar cursos
  (em Curso por cidade, os indicadores são % acima do padrão e taxa de participação).
- Não há CPC. O indicador contínuo é o **% de concluintes com desempenho igual ou acima do padrão**, que define a faixa do Conceito Enade.
- O histórico de cada curso inclui as faixas que ele teve no Enade regular.

**IGC** — Índice Geral de Cursos (2010–2023): evolução do IGC da IES, comparação com outras IES e ranking estadual.

**Informações** — Sobre os dados: fontes, tratamento e cobertura.

As seções do menu começam recolhidas (fica aberta só a da página atual); clique no nome da seção para abrir ou fechar.

## Atualizar com uma nova edição
1. Salve a planilha do INEP na pasta certa dentro de `..\Resultados`, **com o ano no nome do arquivo**:
   - `Resultados CPC` (ex.: `CPC 2026.xlsx`)
   - `Resultados IGC` (ex.: `IGC 2026.xlsx`)
   - `Enade Licenciaturas` (ex.: `Enade licenciaturas 2026.xlsx`)
   - `Enade Medicina` (ex.: `Enade Medicina 2026.xlsx`)
2. Dê dois cliques em **Atualizar Dados.bat**.

### Notas de Formação Geral e Componente Específico (microdados)
As médias de FG, CE e Resultado Geral do estado e do Brasil vêm dos microdados do Enade (de 2014 em diante),
já resumidos em `dados/notas_microdados.parquet`. Quando o INEP publicar uma nova edição:
1. Baixe os microdados em https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enade
   (arquivo `microdados_enade_AAAA.zip`) para uma pasta qualquer (se vier em .rar, extraia numa subpasta `extraido_AAAA`).
2. Rode: `python etl/microdados_enade.py <pasta onde está o arquivo>` (os anos já resumidos são mantidos).
3. Dê dois cliques em **Atualizar Dados.bat**. O arquivo baixado pode ser apagado depois.

O arquivo e a aba certa são encontrados automaticamente; não é preciso editar código.
Se houver dois arquivos do mesmo ano na mesma pasta, o mais recente é usado (e um aviso aparece).

Requisitos (já instalados nesta máquina): `python -m pip install -r requirements.txt`
