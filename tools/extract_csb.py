"""Extract original table cells once; retain page boundaries for review."""
import json
from pathlib import Path
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]

def extract(pdf_path,output_path):
    pages=[]
    with pdfplumber.open(pdf_path) as pdf:
        for n,page in enumerate(pdf.pages,1):
            tables=page.extract_tables()
            pages.append({'page':n,'tables':tables})
            page.close()
            if n%50==0:print(f'Extracted {n}/{len(pdf.pages)} pages',flush=True)
    Path(output_path).write_text(json.dumps(pages,ensure_ascii=False))
    print('Finished',len(pages),'pages',flush=True)

def run():
    extract(ROOT/'data/csb-2026.pdf',ROOT/'data/csb-tables.json')

if __name__=='__main__':run()
