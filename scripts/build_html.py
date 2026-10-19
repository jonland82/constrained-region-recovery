"""Publish faithful HTML editions of the two LaTeX research notes.

Requires Pandoc and beautifulsoup4. Run from any directory:
    python scripts/build_html.py
"""

from __future__ import annotations

import re
import subprocess
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
PAPERS = (
    {
        "stem": "inverse_sampling_region",
        "title": "Can sampled distances recover a constrained region?",
        "subtitle": "An inverse problem for output distributions",
        "date": "12 OCT 2026",
        "description": "An inverse sampling note on distance ambiguity, exact-law identification, and finite-sample recovery.",
        "figure": "../experiments/original_region/inverse_region_experiment.png",
        "other": "inverse_sampling_shared_references.html",
        "refs": (
            (
                "chazal2009",
                'F. Chazal, D. Cohen-Steiner, and A. Lieutier. '
                '<a href="https://doi.org/10.1007/s00454-009-9144-8">'
                'A sampling theory for compact sets in Euclidean space</a>. '
                '<em>Discrete &amp; Computational Geometry</em> 41:461–479, 2009.',
            ),
            (
                "cuevas1997",
                'A. Cuevas and R. Fraiman. '
                '<a href="https://doi.org/10.1214/aos/1030741073">'
                'A plug-in approach to support estimation</a>. '
                '<em>The Annals of Statistics</em> 25:2300–2312, 1997.',
            ),
            (
                "devroye1980",
                'L. Devroye and G. L. Wise. '
                '<a href="https://doi.org/10.1137/0138038">'
                'Detection of abnormal behavior via nonparametric estimation '
                'of the support</a>. <em>SIAM Journal on Applied Mathematics</em> '
                '38:480–488, 1980.',
            ),
        ),
    },
    {
        "stem": "inverse_sampling_shared_references",
        "title": "Can shared references sharpen region recovery?",
        "subtitle": "A finite-sample extension of the inverse sampling model",
        "date": "18 OCT 2026",
        "description": "A shared-reference extension with anchor reconstruction and finite-family recovery bounds.",
        "figure": "figures/shared_reference_illustration.png",
        "other": "inverse_sampling_region.html",
        "refs": (
            (
                "inverse",
                'J. R. Landers. <a href="inverse_sampling_region.html">'
                'Can sampled distances recover a constrained region?</a> '
                'Companion note, 2026.',
            ),
            (
                "edm",
                'I. Dokmanić, R. Parhizkar, J. Ranieri, and M. Vetterli. '
                '<a href="https://arxiv.org/abs/1502.07541">'
                'Euclidean distance matrices: Essential theory, algorithms '
                'and applications</a>. 2015.',
            ),
            (
                "scott",
                'C. D. Scott and R. D. Nowak. '
                '<a href="https://jmlr.org/papers/v7/scott06a.html">'
                'Learning minimum volume sets</a>. JMLR 7:665–704, 2006.',
            ),
        ),
    },
)


def paper_body(source: str) -> str:
    body = source.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
    body = body[body.index(r"\section{") :]
    if r"\bibliographystyle{" in body:
        body = body.split(r"\bibliographystyle{", 1)[0]
    if r"\begin{thebibliography}" in body:
        body = body.split(r"{\footnotesize\raggedright", 1)[0]
    if r"\bibliography{" in body or r"\bibitem" in body:
        raise ValueError("Bibliography was not removed before HTML conversion")
    return body


def pandoc_fragment(body: str) -> str:
    theorem_definitions = "\n".join(
        (
            r"\newtheorem{lemma}{Lemma}",
            r"\newtheorem{proposition}[lemma]{Proposition}",
            r"\newtheorem{remark}[lemma]{Remark}",
        )
    )
    result = subprocess.run(
        ["pandoc", "--from=latex", "--to=html5", "--mathjax"],
        input=theorem_definitions + "\n" + body,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.stdout


def convert(paper: dict) -> None:
    source = (ROOT / "papers" / f"{paper['stem']}.tex").read_text(encoding="utf-8")
    body = paper_body(source)
    soup = BeautifulSoup(pandoc_fragment(body), "html.parser")
    ref_numbers = {key: i for i, (key, _) in enumerate(paper["refs"], 1)}

    for citation in soup.select("span.citation[data-cites]"):
        keys = citation["data-cites"].split()
        citation.clear()
        citation.append("[")
        for i, key in enumerate(keys):
            if key not in ref_numbers:
                raise ValueError(f"Unknown citation: {key}")
            if i:
                citation.append(", ")
            link = soup.new_tag("a", href=f"#ref-{key}")
            link.string = str(ref_numbers[key])
            citation.append(link)
        citation.append("]")

    equation_numbers: dict[str, int] = {}
    for math in soup.select("span.math.display"):
        raw = math.get_text()
        label = re.search(r"\\label\{([^}]+)\}", raw)
        if not label:
            continue
        name = label.group(1)
        equation_numbers[name] = len(equation_numbers) + 1
        math.clear()
        math.append(re.sub(r"\s*\\label\{[^}]+\}", "", raw))
        wrapper = soup.new_tag("span", attrs={"class": "equation", "id": name})
        math.wrap(wrapper)
        number = soup.new_tag("span", attrs={"class": "equation-number"})
        number.string = f"({equation_numbers[name]})"
        wrapper.append(number)

    for link in soup.select("a[data-reference-type]"):
        label = link.get("data-reference", "")
        if label.startswith("eq:"):
            if label not in equation_numbers:
                raise ValueError(f"Unresolved equation reference: {label}")
            number = str(equation_numbers[label])
            link.string = f"({number})" if link["data-reference-type"] == "eqref" else number
        elif label.startswith("fig:"):
            link.string = "1"

    headings = soup.find_all("h1")
    expected_headings = len(re.findall(r"\\section\{", body))
    if len(headings) != expected_headings:
        raise ValueError(f"Expected {expected_headings} sections, found {len(headings)}")
    for i, heading in enumerate(headings, 1):
        heading.name = "h2"
        heading.insert(0, f"{i}. ")

    figures = soup.find_all("figure")
    if len(figures) != len(re.findall(r"\\begin\{figure\}", body)):
        raise ValueError("A figure was lost during conversion")
    for i, figure in enumerate(figures, 1):
        embed = figure.find("embed")
        if embed is None:
            raise ValueError("Pandoc did not emit a figure embed")
        image = soup.new_tag("img", src=paper["figure"])
        image["alt"] = f"Figure {i}: experiment and region-recovery illustration"
        image["loading"] = "lazy"
        if embed.get("id"):
            figure["id"] = embed["id"]
        embed.replace_with(image)
        caption = figure.find("figcaption")
        if caption:
            caption.attrs.pop("aria-hidden", None)
            prefix = soup.new_tag("strong")
            prefix.string = f"Figure {i}. "
            caption.insert(0, prefix)

    expected_proofs = len(re.findall(r"\\begin\{proof\}", body))
    if len(soup.select("div.proof")) != expected_proofs:
        raise ValueError("A proof was lost during conversion")
    for environment in ("lemma", "proposition", "remark"):
        expected = len(re.findall(rf"\\begin\{{{environment}\}}", body))
        if len(soup.select(f"div.{environment}")) != expected:
            raise ValueError(f"A {environment} was lost during conversion")
    if any(r"\label{" in span.get_text() for span in soup.select(".math")):
        raise ValueError("An equation label was left in rendered math")

    references = "\n".join(
        f'<li id="ref-{key}">{entry}</li>' for key, entry in paper["refs"]
    )
    stem = paper["stem"]
    title = escape(paper["title"])
    subtitle = escape(paper["subtitle"])
    description = escape(paper["description"], quote=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <title>{title} — Jonathan R. Landers</title>
  <link rel="stylesheet" href="../assets/site.css">
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
  <a class="skip-link" href="#content">Skip to paper</a>
  <div class="shell">
    <header class="masthead"><a href="../index.html">Distribution Sampling Neighborhoods</a><span>{paper['date']}</span></header>
    <main id="content">
      <div class="title-block">
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
        <p class="author">Jonathan R. Landers</p>
        <div class="paper-links"><a class="button" href="{stem}.pdf">Read PDF</a><a class="button text" href="https://github.com/jonland82/constrained-region-recovery/blob/main/papers/{stem}.tex">LaTeX source</a></div>
      </div>
      <article class="paper-body">
{soup}
        <h2 id="references">References</h2>
        <ol class="references">{references}</ol>
      </article>
      <nav class="paper-nav" aria-label="Paper navigation"><a href="../index.html">← Research overview</a><a href="{paper['other']}">Other paper</a><a href="{stem}.pdf">PDF edition</a></nav>
    </main>
    <footer class="foot">Jonathan R. Landers · 2026</footer>
  </div>
</body>
</html>
"""
    path = ROOT / "papers" / f"{stem}.html"
    path.write_text(html, encoding="utf-8")
    print(f"Built {path.relative_to(ROOT)}")


def main() -> None:
    for paper in PAPERS:
        convert(paper)


if __name__ == "__main__":
    main()
