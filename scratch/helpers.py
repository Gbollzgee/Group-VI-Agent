from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_page_number_to_paragraph(p, font_name="Times New Roman", size_pt=11):
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls('w'))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

def configure_section_page_numbers(section, fmt="decimal", start=None):
    sectPr = section._sectPr
    # Remove existing pgNumType if any
    for el in sectPr.findall(qn('w:pgNumType')):
        sectPr.remove(el)
    
    if start is not None:
        xml_str = f'<w:pgNumType {nsdecls("w")} w:fmt="{fmt}" w:start="{start}"/>'
    else:
        xml_str = f'<w:pgNumType {nsdecls("w")} w:fmt="{fmt}"/>'
    
    sectPr.append(parse_xml(xml_str))
