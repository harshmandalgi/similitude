"""Appendix table of every variant, from the code (paper/tables/variants.tex).

uv run python scripts/variant_table.py
"""

from __future__ import annotations

from pathlib import Path

from similitude.workflows import research, tau, wikiqa

ROOT = Path(__file__).resolve().parents[1]
ESCAPES = [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"),
           ("$", r"\$"), ("τ", r"$\tau$")]  # fmt: skip


def tex(text: str) -> str:
    for a, b in ESCAPES:
        text = text.replace(a, b)
    return text


def main() -> None:
    rows = [r"\begin{table*}[p]", r"\centering\footnotesize",
            r"\begin{tabular}{@{}lllp{6.3cm}@{}}", r"\toprule",
            r"WF & Variant & Kind & What it changes \\", r"\midrule"]  # fmt: skip
    for wf, variants in (("W1", wikiqa.variants()), ("W2", tau.variants()),
                         ("W3", research.variants())):  # fmt: skip
        for v in variants:
            focus = f" ({v.focus})" if wf == "W3" and v.kind != "base" else ""
            rows.append(rf"{wf} & \texttt{{{tex(v.name)}}} & {v.kind}{focus} & "
                        rf"{tex(v.description)} \\")  # fmt: skip
        rows.append(r"\addlinespace")
    rows[-1] = r"\bottomrule"
    rows += [
        r"\end{tabular}",
        r"\caption{Every variant, as defined in the code. Edits were written by a separate Claude Code instance; mutants by hand.}",
        r"\label{tab:variants}",
        r"\end{table*}",
    ]
    out = ROOT / "paper" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / "variants.tex").write_text("\n".join(rows) + "\n")
    print(f"wrote {out / 'variants.tex'}")


if __name__ == "__main__":
    main()
