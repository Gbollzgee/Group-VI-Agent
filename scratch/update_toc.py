import json
from pathlib import Path
from build_complete_report import generate_document

with open('scratch/page_map.json', 'r', encoding='utf-8') as f:
    page_map = json.load(f)

# Certification is on Roman numeral ii
page_map['CERTIFICATION'] = 'ii'

doc = generate_document(toc_page_map=page_map)
doc.save('Group 6 Report.docx')
print('[OK] Document re-generated with exact page numbers.')
