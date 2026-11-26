import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

sys.path.append(str(Path(__file__).parent))
from content_prelims import (
    MEMBERS, PROJECT_TITLE, COURSE_CODE, COURSE_TITLE,
    DEPARTMENT, INSTITUTION, LOCATION, LECTURER, DATE_STR
)
from content_chapter1_2 import CHAPTER_1_DATA, CHAPTER_2_DATA
from content_chapter3 import CHAPTER_3_DATA
from content_chapter4_5_ref import CHAPTER_4_DATA, CHAPTER_5_DATA, REFERENCES_DATA
from helpers import add_page_number_to_paragraph, configure_section_page_numbers

def set_cell_margins(cell, top=45, bottom=45, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_table_borders(table, color="A0A0A0", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_elm = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders_elm)

def format_run(run, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color=RGBColor(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color

def build_perfect_document(toc_dict=None):
    doc = Document()
    
    # Configure Section 0 (Preliminary Pages: Title, Certification, TOC)
    sec_prelim = doc.sections[0]
    sec_prelim.top_margin = Inches(1.0)
    sec_prelim.bottom_margin = Inches(1.0)
    sec_prelim.left_margin = Inches(1.0)
    sec_prelim.right_margin = Inches(1.0)
    sec_prelim.page_width = Inches(8.5)
    sec_prelim.page_height = Inches(11.0)
    
    # Different First Page for Title Page (Page 1 has no visible footer)
    sec_prelim.different_first_page_header_footer = True
    
    # Add Roman numeral page numbering to normal footer of prelim section
    p_foot_prelim = sec_prelim.footer.paragraphs[0]
    add_page_number_to_paragraph(p_foot_prelim, font_name="Times New Roman", size_pt=11)
    configure_section_page_numbers(sec_prelim, fmt="lowerRoman")

    # Configure Base Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)

    # Configure Heading 1
    h1_style = doc.styles['Heading 1']
    h1_style.font.name = 'Times New Roman'
    h1_style.font.size = Pt(15)
    h1_style.font.bold = True
    h1_style.font.color.rgb = RGBColor(0, 0, 0)
    h1_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1_style.paragraph_format.space_before = Pt(8)
    h1_style.paragraph_format.space_after = Pt(16)
    h1_style.paragraph_format.keep_with_next = True

    # Configure Heading 2
    h2_style = doc.styles['Heading 2']
    h2_style.font.name = 'Times New Roman'
    h2_style.font.size = Pt(12.5)
    h2_style.font.bold = True
    h2_style.font.color.rgb = RGBColor(0, 0, 0)
    h2_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2_style.paragraph_format.space_before = Pt(12)
    h2_style.paragraph_format.space_after = Pt(4)
    h2_style.paragraph_format.keep_with_next = True

    # =========================================================================
    # PAGE 1: TITLE PAGE (Fits strictly on Page 1 with zero spillover)
    # =========================================================================
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(2)
    p1.paragraph_format.line_spacing = 1.15
    r = p1.add_run(INSTITUTION)
    format_run(r, size_pt=14, bold=True)
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(10)
    p2.paragraph_format.line_spacing = 1.15
    r = p2.add_run(LOCATION)
    format_run(r, size_pt=11, bold=True)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_before = Pt(0)
    p3.paragraph_format.space_after = Pt(10)
    r = p3.add_run(DEPARTMENT)
    format_run(r, size_pt=12.5, bold=True)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p4.paragraph_format.space_before = Pt(0)
    p4.paragraph_format.space_after = Pt(2)
    p4.paragraph_format.line_spacing = 1.15
    r = p4.add_run(f"COURSE CODE: {COURSE_CODE}")
    format_run(r, size_pt=11.5, bold=True)
    
    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p5.paragraph_format.space_before = Pt(0)
    p5.paragraph_format.space_after = Pt(10)
    p5.paragraph_format.line_spacing = 1.15
    r = p5.add_run(f"COURSE TITLE: {COURSE_TITLE}")
    format_run(r, size_pt=11.5, bold=True)

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p6.paragraph_format.space_before = Pt(0)
    p6.paragraph_format.space_after = Pt(4)
    r = p6.add_run("A PROJECT REPORT ON")
    format_run(r, size_pt=11.5, bold=True)

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p7.paragraph_format.space_before = Pt(0)
    p7.paragraph_format.space_after = Pt(12)
    p7.paragraph_format.line_spacing = 1.15
    r = p7.add_run(PROJECT_TITLE)
    format_run(r, size_pt=12.5, bold=True)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p8.paragraph_format.space_before = Pt(0)
    p8.paragraph_format.space_after = Pt(4)
    r = p8.add_run("SUBMITTED BY\nGROUP 6")
    format_run(r, size_pt=11.5, bold=True)

    # Members Table
    table_m = doc.add_table(rows=1, cols=3)
    table_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_m, color="666666", sz="4", val="single")
    
    col_widths = [Inches(0.7), Inches(3.8), Inches(1.8)]
    hdr_cells = table_m.rows[0].cells
    hdr_titles = ["S/N", "NAME", "MATRIC NO."]
    for idx, title in enumerate(hdr_titles):
        hdr_cells[idx].width = col_widths[idx]
        set_cell_margins(hdr_cells[idx], top=40, bottom=40)
        set_cell_background(hdr_cells[idx], "E8EEF5")
        p = hdr_cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(title)
        format_run(r, size_pt=10, bold=True)

    for s_no, name, mat_no in MEMBERS:
        row_cells = table_m.add_row().cells
        for idx, val in enumerate([s_no, name, mat_no]):
            row_cells[idx].width = col_widths[idx]
            set_cell_margins(row_cells[idx], top=35, bottom=35)
            p = row_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(val)
            format_run(r, size_pt=10, bold=False)

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p9.paragraph_format.space_before = Pt(12)
    p9.paragraph_format.space_after = Pt(2)
    r = p9.add_run(f"SUBMITTED TO: {LECTURER}")
    format_run(r, size_pt=11.5, bold=True)

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p10.paragraph_format.space_before = Pt(0)
    p10.paragraph_format.space_after = Pt(0)
    r = p10.add_run(DATE_STR)
    format_run(r, size_pt=11.5, bold=True)

    doc.add_page_break()

    # =========================================================================
    # PAGE 2: CERTIFICATION (Fits strictly on Page 2 with zero spillover)
    # =========================================================================
    pc_h = doc.add_paragraph()
    pc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pc_h.paragraph_format.space_before = Pt(4)
    pc_h.paragraph_format.space_after = Pt(10)
    r = pc_h.add_run("CERTIFICATION")
    format_run(r, size_pt=15, bold=True)

    cert_text = (
        'This is to certify that the project report titled "Design and Implementation of a Goal Oriented '
        'AI Web Agent for Intelligent Website Navigation and Task Execution" was carried out by the members '
        f'of Group 6 listed below, in partial fulfilment of the requirements of the course {COURSE_CODE} '
        f'({COURSE_TITLE}), in the {DEPARTMENT}, {INSTITUTION}, {LOCATION}.'
    )
    pc_body = doc.add_paragraph()
    pc_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pc_body.paragraph_format.line_spacing = 1.3
    pc_body.paragraph_format.space_after = Pt(10)
    r = pc_body.add_run(cert_text)
    format_run(r, size_pt=11.5, bold=False)

    # Certification Table (with Signature column)
    table_c = doc.add_table(rows=1, cols=4)
    table_c.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_c, color="666666", sz="4", val="single")
    
    col_widths_c = [Inches(0.6), Inches(2.9), Inches(1.6), Inches(1.4)]
    hdr_cells_c = table_c.rows[0].cells
    hdr_titles_c = ["S/N", "Name", "Matric No.", "Signature"]
    for idx, title in enumerate(hdr_titles_c):
        hdr_cells_c[idx].width = col_widths_c[idx]
        set_cell_margins(hdr_cells_c[idx], top=45, bottom=45)
        set_cell_background(hdr_cells_c[idx], "E8EEF5")
        p = hdr_cells_c[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in [0, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(title)
        format_run(r, size_pt=10, bold=True)

    for s_no, name, mat_no in MEMBERS:
        row_cells = table_c.add_row().cells
        for idx, val in enumerate([s_no, name, mat_no, ""]):
            row_cells[idx].width = col_widths_c[idx]
            set_cell_margins(row_cells[idx], top=50, bottom=50)
            p = row_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in [0, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(val)
            format_run(r, size_pt=10, bold=False)

    # Lecturer Sign-off
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(14)
    p_sign.paragraph_format.space_after = Pt(2)
    p_sign.paragraph_format.line_spacing = 1.15
    r1 = p_sign.add_run(f"{LECTURER}\nCourse Lecturer\n\n\n_____________________________\nSignature")
    format_run(r1, size_pt=11.5, bold=False)

    p_date = doc.add_paragraph()
    p_date.paragraph_format.space_before = Pt(4)
    p_date.paragraph_format.space_after = Pt(0)
    r2 = p_date.add_run("Date: .......................................")
    format_run(r2, size_pt=11.5, bold=False)

    doc.add_page_break()

    # =========================================================================
    # TABLE OF CONTENTS (Pages iii - iv)
    # =========================================================================
    ptoc_h = doc.add_paragraph()
    ptoc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ptoc_h.paragraph_format.space_before = Pt(4)
    ptoc_h.paragraph_format.space_after = Pt(12)
    r = ptoc_h.add_run("TABLE OF CONTENTS")
    format_run(r, size_pt=15, bold=True)

    TOC_ORDER = [
        ("CERTIFICATION", True, "ii"),
        ("CHAPTER ONE: INTRODUCTION", True, "1"),
        ("1.1 Background of the Study", False, "1"),
        ("1.2 Statement of the Problem", False, "2"),
        ("1.3 Aim and Objectives of the Study", False, "3"),
        ("1.4 Research Questions", False, "4"),
        ("1.5 Significance of the Study", False, "4"),
        ("1.6 Scope and Delimitations of the Study", False, "5"),
        ("1.7 Definition of Terms", False, "5"),
        ("1.8 Organization of the Report", False, "6"),
        ("CHAPTER TWO: LITERATURE REVIEW", True, "7"),
        ("2.1 Introduction", False, "7"),
        ("2.2 Conceptual Framework", False, "7"),
        ("2.3 The Evolution of Autonomous Web Agents", False, "8"),
        ("2.4 Large Language Models (LLMs) in Web Navigation and Reasoning", False, "10"),
        ("2.5 Chrome DevTools Protocol (CDP) & DOM State Representation", False, "11"),
        ("2.6 Multimodal Vision & Grounding in Web Tasks", False, "12"),
        ("2.7 Continuous Voice Interfaces & Dual-Engine Speech Processing", False, "13"),
        ("2.8 E-Commerce Intelligence & Deep Information Extraction", False, "14"),
        ("2.9 Review of Related Works & Contemporary Autonomous Agent Frameworks", False, "15"),
        ("2.10 Summary of the Literature Review and Research Gap", False, "16"),
        ("CHAPTER THREE: METHODOLOGY", True, "17"),
        ("3.1 Introduction", False, "17"),
        ("3.2 Architectural Design & System Framework", False, "17"),
        ("3.3 Team Organization and Workflow", False, "18"),
        ("3.4 Data Ingestion and Semantic DOM Parsing Pipeline", False, "20"),
        ("3.5 Smart Intent Routing Engine", False, "21"),
        ("3.6 5-Stage Visual Execution Pipeline Design", False, "22"),
        ("3.7 Dual-Engine Voice System & Gemini Cloud STT Fallback Architecture", False, "23"),
        ("3.8 Deep Market Search Engine Implementation", False, "24"),
        ("3.9 Security, Error Recovery, and Resilient Multi-Model Fallback Mechanics", False, "25"),
        ("3.10 System Deployment and Cloudflare Zero-Trust Tunnel Architecture", False, "26"),
        ("CHAPTER FOUR: RESULTS AND DISCUSSION", True, "27"),
        ("4.1 Introduction", False, "27"),
        ("4.2 Experimental Setup and Test Environments", False, "27"),
        ("4.3 Evaluation of Intent Classification Accuracy and Latency", False, "28"),
        ("4.4 Performance Analysis of the 5-Stage Execution Feed", False, "29"),
        ("4.5 Real-Time Voice Interaction & Latency Benchmark", False, "30"),
        ("4.6 Deep Information Extraction & Jumia E-Commerce Case Study", False, "31"),
        ("4.7 Autonomous Live Browser Navigation & CDP Interaction Results", False, "32"),
        ("4.8 Error Recovery and Multi-Model Fallback Resilience Under Traffic Spikes", False, "33"),
        ("4.9 Discussion of Findings & Academic Implications", False, "34"),
        ("CHAPTER FIVE: CONCLUSION AND RECOMMENDATIONS", True, "35"),
        ("5.1 Summary of Findings", False, "35"),
        ("5.2 Contributions to Knowledge", False, "36"),
        ("5.3 Limitations of the Study", False, "37"),
        ("5.4 Recommendations for Future Research", False, "37"),
        ("5.5 Final Remarks", False, "38"),
        ("REFERENCES", True, "39")
    ]

    for item_key, is_major, default_pg in TOC_ORDER:
        pg = str(toc_dict.get(item_key, default_pg)) if toc_dict else default_pg
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.12
        p.paragraph_format.space_before = Pt(3) if is_major else Pt(0)
        p.paragraph_format.space_after = Pt(2) if is_major else Pt(1)
        
        display_title = item_key if is_major else f"    {item_key}"
        dot_count = max(4, 76 - len(display_title) - len(pg))
        dots = " ." * (dot_count // 2)
        
        r1 = p.add_run(display_title)
        format_run(r1, size_pt=10.5 if not is_major else 11, bold=is_major)
        
        r2 = p.add_run(f" {dots} ")
        format_run(r2, size_pt=9.5, bold=False, color=RGBColor(150, 150, 150))
        
        r3 = p.add_run(pg)
        format_run(r3, size_pt=10.5, bold=is_major)

    # =========================================================================
    # SECTION 1: MAIN BODY (Arabic Page Numbers Starting at 1)
    # =========================================================================
    sec_body = doc.add_section(WD_SECTION_START.NEW_PAGE)
    sec_body.top_margin = Inches(1.0)
    sec_body.bottom_margin = Inches(1.0)
    sec_body.left_margin = Inches(1.0)
    sec_body.right_margin = Inches(1.0)
    sec_body.page_width = Inches(8.5)
    sec_body.page_height = Inches(11.0)
    
    # Unlink headers/footers from preliminary section
    sec_body.header.is_linked_to_previous = False
    sec_body.footer.is_linked_to_previous = False
    sec_body.different_first_page_header_footer = False
    
    # Configure Arabic page numbering starting at 1
    p_foot_body = sec_body.footer.paragraphs[0]
    add_page_number_to_paragraph(p_foot_body, font_name="Times New Roman", size_pt=11)
    configure_section_page_numbers(sec_body, fmt="decimal", start=1)

    # Render Chapters with strict paragraph formatting & justification
    def render_chapter(ch_data, is_first_chapter=False):
        if not is_first_chapter:
            doc.add_page_break()

        # Chapter Title (Heading 1)
        p_ch = doc.add_paragraph(style='Heading 1')
        p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ch.paragraph_format.space_before = Pt(8)
        p_ch.paragraph_format.space_after = Pt(16)
        p_ch.paragraph_format.keep_with_next = True
        r = p_ch.add_run(ch_data["title"])
        format_run(r, size_pt=15, bold=True)

        for sec_title, paragraphs in ch_data["sections"]:
            # Section Title (Heading 2)
            p_sec = doc.add_paragraph(style='Heading 2')
            p_sec.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_sec.paragraph_format.space_before = Pt(12)
            p_sec.paragraph_format.space_after = Pt(4)
            p_sec.paragraph_format.keep_with_next = True
            r = p_sec.add_run(sec_title)
            format_run(r, size_pt=12.5, bold=True)

            for para in paragraphs:
                if para == "[TABLE_4_1]":
                    render_table_4_1(doc)
                elif para == "[TABLE_4_2]":
                    render_table_4_2(doc)
                elif para == "[TABLE_4_3]":
                    render_table_4_3(doc)
                elif para == "[TABLE_4_4]":
                    render_table_4_4(doc)
                else:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.line_spacing = 1.5
                    p.paragraph_format.space_after = Pt(6)
                    r = p.add_run(para)
                    format_run(r, size_pt=12, bold=False)

    render_chapter(CHAPTER_1_DATA, is_first_chapter=True)
    render_chapter(CHAPTER_2_DATA)
    render_chapter(CHAPTER_3_DATA)
    render_chapter(CHAPTER_4_DATA)
    render_chapter(CHAPTER_5_DATA)

    # References
    doc.add_page_break()
    p_ref_h = doc.add_paragraph(style='Heading 1')
    p_ref_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref_h.paragraph_format.space_before = Pt(8)
    p_ref_h.paragraph_format.space_after = Pt(16)
    p_ref_h.paragraph_format.keep_with_next = True
    r = p_ref_h.add_run("REFERENCES")
    format_run(r, size_pt=15, bold=True)

    for ref in REFERENCES_DATA:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        r = p.add_run(ref)
        format_run(r, size_pt=11.5, bold=False)

    return doc

# =========================================================================
# EXPERIMENTAL TABLES IN CHAPTER 4
# =========================================================================
def render_table_4_1(doc):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r = p_cap.add_run("Table 4.1: Intent Classification Accuracy and Routing Latency Benchmark")
    format_run(r, size_pt=11, bold=True)

    t = doc.add_table(rows=1, cols=6)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(1.0), Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.1)]
    headers = ["Query Class", "Total Trials", "Heuristic Match", "LLM Fallback", "Total Correct", "Accuracy (%)"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=65, bottom=65)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9.5, bold=True)

    data = [
        ["DEEP_SEARCH", "50", "46 (92.0%)", "4 (8.0%)", "49", "98.0%"],
        ["BROWSER_ACTION", "50", "44 (88.0%)", "6 (12.0%)", "48", "96.0%"],
        ["DIRECT_ANSWER", "50", "44 (88.0%)", "6 (12.0%)", "50", "100.0%"],
        ["Overall / Average", "150", "134 (89.3%)", "16 (10.7%)", "147", "98.0%"]
    ]
    for row in data:
        row_cells = t.add_row().cells
        is_total = (row[0] == "Overall / Average")
        for i, val in enumerate(row):
            row_cells[i].width = col_w[i]
            set_cell_margins(row_cells[i], top=45, bottom=45)
            if is_total:
                set_cell_background(row_cells[i], "F0F4F8")
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9.5, bold=is_total)

def render_table_4_2(doc):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r = p_cap.add_run("Table 4.2: End-to-End Latency Profile Across Execution Stages (Seconds)")
    format_run(r, size_pt=11, bold=True)

    t = doc.add_table(rows=1, cols=7)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(0.8), Inches(0.9), Inches(0.9), Inches(0.8), Inches(0.9), Inches(1.1)]
    headers = ["Task Modality", "Stage 1 (s)", "Stage 2 (s)", "Stage 3 (s)", "Stage 4 (s)", "Stage 5 (s)", "Total Latency"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=65, bottom=65)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9, bold=True)

    data = [
        ["Direct AI Answer", "0.38", "0.42", "0.45", "0.31", "0.20", "1.76 s"],
        ["Deep Market Search", "0.52", "0.85", "1.42", "0.54", "0.40", "3.73 s"],
        ["Live Browser Navigation", "0.64", "4.82", "5.16", "2.10", "2.10", "14.82 s"]
    ]
    for row in data:
        row_cells = t.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].width = col_w[i]
            set_cell_margins(row_cells[i], top=45, bottom=45)
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9, bold=(i == 6))

def render_table_4_3(doc):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r = p_cap.add_run("Table 4.3: Voice Pipeline Performance and Recognition Accuracy")
    format_run(r, size_pt=11, bold=True)

    t = doc.add_table(rows=1, cols=6)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(1.2), Inches(1.1), Inches(1.1), Inches(1.0), Inches(1.1)]
    headers = ["Test Environment", "Ambient Noise", "Trials", "Native Web Speech", "Gemini Cloud STT", "Echo Suppression"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=65, bottom=65)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9, bold=True)

    data = [
        ["Quiet Lab Room", "32 dB", "30", "28 / 30 (93.3%)", "30 / 30 (100.0%)", "100.0% (Zero Echo)"],
        ["Noisy Presentation Hall", "62 dB", "30", "21 / 30 (70.0%)", "29 / 30 (96.7%)", "100.0% (Zero Echo)"],
        ["Combined / Overall", "47 dB avg", "60", "49 / 60 (81.7%)", "59 / 60 (98.3%)", "100.0% (Zero Echo)"]
    ]
    for row in data:
        row_cells = t.add_row().cells
        is_total = (row[0] == "Combined / Overall")
        for i, val in enumerate(row):
            row_cells[i].width = col_w[i]
            set_cell_margins(row_cells[i], top=45, bottom=45)
            if is_total:
                set_cell_background(row_cells[i], "F0F4F8")
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9, bold=is_total)

def render_table_4_4(doc):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r = p_cap.add_run("Table 4.4: Extracted Jumia Nigeria E-Commerce Product Comparison (Shoes Under ₦50,000)")
    format_run(r, size_pt=11, bold=True)

    t = doc.add_table(rows=1, cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(2.2), Inches(1.5), Inches(1.3), Inches(2.2)]
    headers = ["Product Name & Brand", "Style / Category", "Price (₦)", "Key Specifications & Rating"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=65, bottom=65)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9.5, bold=True)

    data = [
        ["Adek Mesh Breathable Running Shoes", "Athletic / Running", "₦14,500", "Breathable mesh upper, lightweight EVA sole, 4.4/5 (182 reviews)"],
        ["X-Step Men's Casual Canvas Loafers", "Casual / Slip-on", "₦18,200", "Durable vulcanized canvas, cushioned insole, 4.2/5 (95 reviews)"],
        ["SportAir Cushion Athletic Sneakers", "Performance Sport", "₦26,800", "Air-cushion heel unit, anti-slip rubber outsole, 4.6/5 (310 reviews)"],
        ["UrbanFlex Lightweight Jogging Shoes", "Jogging / Training", "₦34,500", "Ergonomic arch support, reflective heel accent, 4.5/5 (140 reviews)"],
        ["KangaROX Outdoor High-Traction Trainers", "Cross-Training / Trail", "₦44,900", "Reinforced toe cap, deep lug traction outsole, 4.7/5 (215 reviews)"]
    ]
    for row in data:
        row_cells = t.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].width = col_w[i]
            set_cell_margins(row_cells[i], top=55, bottom=55)
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9.5, bold=(i == 2))

if __name__ == "__main__":
    doc = build_perfect_document()
    doc.save("scratch/perfect_report.docx")
    print("Perfect draft created in scratch/perfect_report.docx")
