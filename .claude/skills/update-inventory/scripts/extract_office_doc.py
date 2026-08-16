#!/usr/bin/env python3
"""Extract plain text/JSON from a .docx or .xlsx without external dependencies.

Both formats are just zipped XML, so this uses only zipfile + the standard
library's xml.etree — no python-docx/openpyxl install needed.

Usage:
    extract_office_doc.py <file.docx> [output.txt]
    extract_office_doc.py <file.xlsx> [output.json]

With no output path, prints to stdout.
"""
import sys
import json
import zipfile
from xml.etree import ElementTree as ET


def docx_text(path):
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml")
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ET.fromstring(xml)
    paras = []
    for p in root.iter(f"{{{ns['w']}}}p"):
        texts = [t.text or "" for t in p.iter(f"{{{ns['w']}}}t")]
        paras.append("".join(texts))
    return "\n".join(paras)


def xlsx_sheets(path):
    z = zipfile.ZipFile(path)
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in sst.findall("s:si", ns):
            texts = [t.text or "" for t in si.iter(f"{{{ns['s']}}}t")]
            shared.append("".join(texts))

    def col_letter_to_idx(cell_ref):
        letters = "".join(c for c in cell_ref if c.isalpha())
        idx = 0
        for c in letters:
            idx = idx * 26 + (ord(c.upper()) - 64)
        return idx - 1

    sheet_files = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
    sheets = {}
    for i, sheet_file in enumerate(sheet_files, start=1):
        root = ET.fromstring(z.read(sheet_file))
        rows_data = []
        for row in root.iter(f"{{{ns['s']}}}row"):
            cells = {}
            for c in row.findall("s:c", ns):
                ref = c.get("r")
                t = c.get("t")
                v = c.find("s:v", ns)
                val = v.text if v is not None else ""
                if t == "s" and val != "":
                    val = shared[int(val)]
                cells[col_letter_to_idx(ref)] = val
            maxcol = max(cells.keys()) if cells else -1
            rows_data.append([cells.get(j, "") for j in range(maxcol + 1)])
        sheets[f"sheet{i}"] = rows_data
    return sheets


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    if path.lower().endswith(".docx"):
        result = docx_text(path)
    elif path.lower().endswith(".xlsx"):
        result = json.dumps(xlsx_sheets(path), indent=2, ensure_ascii=False)
    else:
        print(f"Unsupported file type: {path} (expected .docx or .xlsx)", file=sys.stderr)
        sys.exit(1)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"wrote {out_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
