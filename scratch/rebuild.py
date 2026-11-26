import json
from scratch.generate_perfect_report import build_perfect_document

with open('scratch/toc_map.json', 'r', encoding='ascii') as f:
    toc_dict = json.load(f)

doc = build_perfect_document(toc_dict=toc_dict)
doc.save('Group 6 Report.docx')
print('[OK] Document successfully generated with exact page numbers.')