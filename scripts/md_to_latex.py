"""
One-time conversion of the Markdown paper drafts to LaTeX sections (paper/sections/).

After this conversion the .tex files are the paper; edit them, not the Markdown, which
is archived in paper/drafts_md/. Kept for the record and in case a draft section is
written in Markdown first.

What it does
- Pandoc (markdown -> latex, --biblatex): [@key] -> \\autocite{key}, @key -> \\textcite{key}
- HTML comments (source notes such as <!-- outputs/... -->) -> LaTeX % comments
- Figures: "Figure N. caption" -> \\caption{caption}\\label{fig:N}; text "Figure N" ->
  Figure~\\ref{fig:N}. The same for tables ("*Table N. caption*" lines before a table)
  and appendix items (A1, B2 ...). LaTeX then numbers everything itself.
- Headings: "# 2 Title" -> \\section{Title} (numbers removed; LaTeX numbers them);
  appendices "# Appendix A: Title" -> \\section{Title} after \\appendix.

Usage
    python scripts/md_to_latex.py paper/part_a_measured_impacts.md paper/sections/02_measured_impacts.tex
"""

import re
import subprocess
import sys
from pathlib import Path

FIG = re.compile(r"!\[Figure ([A-C]?\d+)\. (.*?)\]\(([^)]+)\)", re.S)
TAB_CAP = re.compile(r"^\*Table ([A-C]?\d+)\. (.*?)\*\s*$", re.M | re.S)


def pre(md):
    # HTML comments -> raw LaTeX comment blocks
    def com(m):
        body = "\n".join("% " + l.strip() for l in m.group(1).strip().splitlines())
        return f"\n```{{=latex}}\n{body}\n```\n"
    md = re.sub(r"<!--(.*?)-->", com, md, flags=re.S)
    # headings: strip leading numbers ("# 2 Title", "## 2.1 Title")
    md = re.sub(r"^(#+) (?:\d+(?:\.\d+)*) ", r"\1 ", md, flags=re.M)
    md = re.sub(r"^# Appendix ([A-C]): (.*)$", r"# \2", md, flags=re.M)
    # figures: caption without the "Figure N." prefix, label marker kept for post()
    md = FIG.sub(lambda m: f"![{m.group(2).strip()} LBLFIG{m.group(1)}LBL]({m.group(3)})", md)
    # table captions: "*Table N. caption*" before a table -> pandoc caption
    md = TAB_CAP.sub(lambda m: f"Table: {' '.join(m.group(2).split())} LBLTAB{m.group(1)}LBL\n", md)
    # a source-note comment between a caption and its table would detach the caption:
    # move such comments above the caption
    md = re.sub(r"(Table: [^\n]*\n)\s*(```\{=latex\}\n(?:%[^\n]*\n)+```\n)", r"\2\n\1", md)
    return md


def post(tex):
    tex = re.sub(r"\\caption\{(.*?)\s*LBLFIG([A-C]?\d+)LBL\}", r"\\caption{\1}\\label{fig:\2}", tex, flags=re.S)
    tex = re.sub(r"\\caption\{(.*?)\s*LBLTAB([A-C]?\d+)LBL\}", r"\\caption{\1}\\label{tab:\2}", tex, flags=re.S)
    # alt-text duplicates of the marker inside \includegraphics[alt=...] etc.
    tex = re.sub(r"\s*LBL(FIG|TAB)[A-C]?\d+LBL", "", tex)
    # cross-references in running text
    tex = re.sub(r"\bFigure ([A-C]?\d+)\b", lambda m: f"Figure~\\ref{{fig:{m.group(1)}}}", tex)
    tex = re.sub(r"\bTable ([A-C]?\d+)\b", lambda m: f"Table~\\ref{{tab:{m.group(1)}}}", tex)
    # figures: fixed width, no pandoc sizing macros
    tex = tex.replace("\\pandocbounded{", "{")
    tex = re.sub(r"\\includegraphics(\[[^\]]*\])?\{", r"\\includegraphics[width=\\linewidth]{", tex)
    tex = tex.replace("{figures/", "{")    # \graphicspath{{figures/}} in main.tex
    return tex


def convert(src, dst):
    md = pre(Path(src).read_text(encoding="utf-8"))
    out = subprocess.run(["pandoc", "-f", "markdown+tex_math_dollars+pipe_tables+raw_attribute",
                          "-t", "latex", "--biblatex", "--wrap=preserve", "--top-level-division=section"],
                         input=md, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(f"% Converted from {Path(src).name} by scripts/md_to_latex.py; edit this file.\n"
                         + post(out), encoding="utf-8")
    print(f"{src} -> {dst}")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
