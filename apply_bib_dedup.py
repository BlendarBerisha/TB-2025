#!/usr/bin/env python3
# apply_bib_dedup.py
# Usage: python apply_bib_dedup.py /path/to/latex/root citation_key_replacements.csv
import sys, os, re, csv

def load_map(csv_path):
    repl = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repl.append((row["remplacer"].strip(), row["conserver"].strip()))
    # remove identity and duplicates
    repl = [(a,b) for a,b in repl if a and b and a!=b]
    # ensure deterministic order (longer keys first to avoid partial overlaps)
    repl.sort(key=lambda x: (-len(x[0]), x[0]))
    return repl

CITE_CMDS = r'(?:cite|parencite|textcite|autocite|Cite|Parencite|Textcite|Autocite)'
BRACE_CONTENT = r'\{([^}]*)\}'

def replace_in_cite_args(text, key_map):
    # Replace inside citation commands only: \cmd[opt]{k1, k2} or \cmd{...}
    def repl_func(m):
        head = m.group(0)
        # Find the last {...} which holds the keys
        # We handle patterns like \cmd[...]{keys}
        parts = re.split(BRACE_CONTENT, head, maxsplit=0)
        # parts alternates text and captures; but ambiguous. Simpler approach: scan braces.
        out = []
        i = 0; depth = 0; buf = []
        # We'll rebuild scanning characters to find the LAST {...} group.
        last_open = head.rfind('{')
        last_close = head.rfind('}')
        if last_open != -1 and last_close != -1 and last_close > last_open:
            keys_str = head[last_open+1:last_close]
            # split by comma and trim
            keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            new_keys = []
            for k in keys:
                replaced = k
                for a,b in key_map:
                    if k == a:
                        replaced = b
                        break
                new_keys.append(replaced)
            new_keys_str = ', '.join(new_keys)
            return head[:last_open+1] + new_keys_str + head[last_close:]
        return head

    pattern = re.compile(r'\\' + CITE_CMDS + r'(?:\[[^\]]*\])?\s*\{[^}]*\}')
    return pattern.sub(repl_func, text)

def process_file(path, key_map):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        original = f.read()
    updated = replace_in_cite_args(original, key_map)
    if updated != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated)
        return True
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python apply_bib_dedup.py /path/to/latex/root citation_key_replacements.csv")
        sys.exit(1)
    root = sys.argv[1]
    csv_map = sys.argv[2]
    key_map = load_map(csv_map)
    changed = 0
    scanned = 0
    for dirpath,_,filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.tex'):
                scanned += 1
                fp = os.path.join(dirpath, fn)
                if process_file(fp, key_map):
                    changed += 1
                    print("Patched:", fp)
    print(f"Scanned .tex files: {scanned} — Modified: {changed}")

if __name__ == "__main__":
    main()
