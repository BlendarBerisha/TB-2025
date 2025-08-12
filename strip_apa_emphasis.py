#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strip_apa_emphasis.py
Remove LaTeX emphasis commands (\emph, \textit, \texttt by default) while preserving their contents,
skipping verbatim-like environments (verbatim, lstlisting, minted). Designed to help align with APA 7.

Usage examples:
  # Dry-run: show summary only
  python strip_apa_emphasis.py main.tex

  # In-place on multiple files (creates .bak backups)
  python strip_apa_emphasis.py --inplace main.tex chapters/*.tex annexes/*.tex

  # Custom macro list
  python strip_apa_emphasis.py --macros emph textit texttt textsc --inplace main.tex
"""
import argparse
import sys
from pathlib import Path

DEFAULT_MACROS = ["emph", "textit", "texttt"]
VERBATIM_ENVS = {"verbatim", "lstlisting", "minted"}

def extract_brace_group(s: str, start: int):
    """
    Extract a balanced { ... } group starting at index `start` (which must be '{').
    Returns (substring, next_index). If unbalanced, returns (None, start).
    """
    n = len(s)
    if start >= n or s[start] != '{':
        return None, start
    depth = 0
    i = start
    while i < n:
        ch = s[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                # include the closing brace
                return s[start:i+1], i+1
        i += 1
    # Unbalanced
    return None, start

def remove_macros(s: str, macros):
    """
    Remove specified LaTeX macros of the form \macro{...} while preserving contents.
    Recurses into contents to remove nested occurrences.
    """
    i = 0
    n = len(s)
    out_chars = []
    macros_sorted = sorted(macros, key=len, reverse=True)  # prefer longest first
    total_replacements = 0

    while i < n:
        ch = s[i]
        if ch == '\\':
            # Try to match any macro
            matched = False
            for name in macros_sorted:
                j = i + 1
                # name must follow immediately
                if s.startswith(name, j):
                    j += len(name)
                    # optional whitespace
                    while j < n and s[j].isspace():
                        j += 1
                    if j < n and s[j] == '{':
                        grp, k = extract_brace_group(s, j)
                        if grp is not None:
                            inner = grp[1:-1]
                            # recursively remove inside
                            inner_processed, inner_repl = remove_macros(inner, macros)
                            out_chars.append(inner_processed)
                            i = k
                            total_replacements += inner_repl + 1
                            matched = True
                            break
                # no match for this name, continue
            if matched:
                continue
            else:
                # Not one of our macros: keep the backslash and continue
                out_chars.append(ch)
                i += 1
        else:
            out_chars.append(ch)
            i += 1

    return "".join(out_chars), total_replacements

def split_verbatim_blocks(s: str):
    """
    Yield tuples (is_verbatim, text) splitting the document into chunks that are either
    inside a verbatim-like environment or normal text.
    """
    i = 0
    n = len(s)
    chunks = []
    while i < n:
        # Look for \begin{...}
        idx = s.find(r"\begin{", i)
        if idx == -1:
            chunks.append((False, s[i:]))
            break
        # Emit non-verbatim text before begin
        if idx > i:
            chunks.append((False, s[i:idx]))
        # parse env name
        j = idx + len(r"\begin{")
        k = s.find("}", j)
        if k == -1:
            # malformed begin, emit rest as normal
            chunks.append((False, s[idx:]))
            break
        env_name = s[j:k]
        # Find matching \end{env_name}
        end_tag = rf"\end{{{env_name}}}"
        end_idx = s.find(end_tag, k+1)
        if end_idx == -1:
            # no end found: treat as normal
            chunks.append((False, s[idx:]))
            break
        block = s[idx:end_idx + len(end_tag)]
        is_verbatim = env_name in VERBATIM_ENVS
        chunks.append((is_verbatim, block))
        i = end_idx + len(end_tag)
    return chunks

def process_text(s: str, macros):
    """
    Process LaTeX text, skipping verbatim-like environments.
    """
    parts = split_verbatim_blocks(s)
    processed = []
    total_repl = 0
    for is_verbatim, text in parts:
        if is_verbatim:
            processed.append(text)  # keep as-is
        else:
            p, cnt = remove_macros(text, macros)
            processed.append(p)
            total_repl += cnt
    return "".join(processed), total_repl

def main():
    p = argparse.ArgumentParser(description="Strip LaTeX emphasis commands while preserving contents (APA 7).")
    p.add_argument("files", nargs="+", help="LaTeX files to process (e.g., main.tex chapters/*.tex)")
    p.add_argument("--inplace", action="store_true", help="Modify files in place (create .bak backups).")
    p.add_argument("--macros", nargs="+", default=DEFAULT_MACROS, help="Macros to strip (default: emph textit texttt).")
    args = p.parse_args()

    total_files = 0
    total_changes = 0

    for pattern in args.files:
        for path in sorted(Path().glob(pattern)):
            if not path.is_file():
                continue
            try:
                original = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"[WARN] Could not read {path} as UTF-8. Skipped.", file=sys.stderr)
                continue

            processed, cnt = process_text(original, args.macros)

            if args.inplace and processed != original:
                bak = path.with_suffix(path.suffix + ".bak")
                bak.write_text(original, encoding="utf-8")
                path.write_text(processed, encoding="utf-8")
                print(f"[OK] {path}  —  replacements: {cnt}  (backup: {bak.name})")
            else:
                # Dry-run summary
                print(f"[DRY] {path}  —  replacements: {cnt}")
            total_files += 1
            total_changes += cnt

    if args.inplace:
        print(f"\nDone. Files processed: {total_files} — Total replacements: {total_changes}")
    else:
        print(f"\nDry-run complete. Files scanned: {total_files} — Total potential replacements: {total_changes}")

if __name__ == "__main__":
    main()
