"""Extract original table cells once; retain page boundaries for review."""
import json
from pathlib import Path
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]

def extract(pdf_path,output_path):
    output_path=Path(output_path)
    partial=output_path.with_suffix('.partial.json')
    pages=json.loads(partial.read_text()) if partial.exists() else []
    with pdfplumber.open(pdf_path) as pdf:
        total=len(pdf.pages)
        for n,page in enumerate(pdf.pages[len(pages):],len(pages)+1):
            tables=page.extract_tables()
            pages.append({'page':n,'tables':tables})
            page.close()
            if n%25==0:
                partial.write_text(json.dumps(pages,ensure_ascii=False))
                print(f'Extracted {n}/{total} pages',flush=True)
    output_path.write_text(json.dumps(pages,ensure_ascii=False))
    partial.unlink(missing_ok=True)
    print('Finished',len(pages),'pages',flush=True)

def run():
    extract(ROOT/'data/csb-2026.pdf',ROOT/'data/csb-tables.json')

if __name__=='__main__':run()
