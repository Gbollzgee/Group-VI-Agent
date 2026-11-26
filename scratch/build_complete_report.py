import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

# Import content modules
sys.path.append(str(Path(__file__).parent))
from content_prelims import (
    MEMBERS, PROJECT_TITLE, COURSE_CODE, COURSE_TITLE,
    DEPARTMENT, INSTITUTION, LOCATION, LECTURER, DATE_STR
)
from content_chapter1_2 import CHAPTER_1_DATA, CHAPTER_2_DATA
from content_chapter3 import CHAPTER_3_DATA
from content_chapter4_5_ref import CHAPTER_4_DATA, CHAPTER_5_DATA, REFERENCES_DATA

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
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

def set_table_borders(table, color="B0B0B0", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders_elm = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders_elm)

def format_run(run, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color=RGBColor(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color

def create_report():
    doc = Document()
    
    # Configure Page Margins: 1.0 inch all around
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
    # Configure Base Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)

    print("Building Title Page...")
    # =========================================================================
    # PAGE 1: TITLE PAGE
    # =========================================================================
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(2)
    p1.paragraph_format.line_spacing = 1.15
    r = p1.add_run(INSTITUTION)
    format_run(r, size_pt=15, bold=True)
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(16)
    p2.paragraph_format.line_spacing = 1.15
    r = p2.add_run(LOCATION)
    format_run(r, size_pt=11, bold=True)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_before = Pt(0)
    p3.paragraph_format.space_after = Pt(14)
    r = p3.add_run(DEPARTMENT)
    format_run(r, size_pt=13, bold=True)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p4.paragraph_format.space_before = Pt(0)
    p4.paragraph_format.space_after = Pt(2)
    p4.paragraph_format.line_spacing = 1.15
    r = p4.add_run(f"COURSE CODE: {COURSE_CODE}")
    format_run(r, size_pt=12, bold=True)
    
    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p5.paragraph_format.space_before = Pt(0)
    p5.paragraph_format.space_after = Pt(16)
    p5.paragraph_format.line_spacing = 1.15
    r = p5.add_run(f"COURSE TITLE: {COURSE_TITLE}")
    format_run(r, size_pt=12, bold=True)

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p6.paragraph_format.space_before = Pt(0)
    p6.paragraph_format.space_after = Pt(6)
    r = p6.add_run("A PROJECT REPORT ON")
    format_run(r, size_pt=12, bold=True)

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p7.paragraph_format.space_before = Pt(0)
    p7.paragraph_format.space_after = Pt(18)
    p7.paragraph_format.line_spacing = 1.2
    r = p7.add_run(PROJECT_TITLE)
    format_run(r, size_pt=13, bold=True)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p8.paragraph_format.space_before = Pt(0)
    p8.paragraph_format.space_after = Pt(4)
    r = p8.add_run("SUBMITTED BY\nGROUP 6")
    format_run(r, size_pt=12, bold=True)

    # Members Table
    table_m = doc.add_table(rows=1, cols=3)
    table_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_m, color="666666", sz="6", val="single")
    
    col_widths = [Inches(0.8), Inches(3.6), Inches(2.0)]
    
    # Header Row
    hdr_cells = table_m.rows[0].cells
    hdr_titles = ["S/N", "NAME", "MATRIC NO."]
    for idx, title in enumerate(hdr_titles):
        hdr_cells[idx].width = col_widths[idx]
        set_cell_margins(hdr_cells[idx], top=100, bottom=100)
        set_cell_background(hdr_cells[idx], "E8EEF5")
        p = hdr_cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        format_run(r, size_pt=11, bold=True)

    # Member Rows
    for s_no, name, mat_no in MEMBERS:
        row_cells = table_m.add_row().cells
        for idx, val in enumerate([s_no, name, mat_no]):
            row_cells[idx].width = col_widths[idx]
            set_cell_margins(row_cells[idx], top=80, bottom=80)
            p = row_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=11, bold=False)

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p9.paragraph_format.space_before = Pt(20)
    p9.paragraph_format.space_after = Pt(4)
    r = p9.add_run(f"SUBMITTED TO: {LECTURER}")
    format_run(r, size_pt=12, bold=True)

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p10.paragraph_format.space_before = Pt(0)
    p10.paragraph_format.space_after = Pt(0)
    r = p10.add_run(DATE_STR)
    format_run(r, size_pt=12, bold=True)

    doc.add_page_break()

    print("Building Certification Page...")
    # =========================================================================
    # PAGE 2: CERTIFICATION
    # =========================================================================
    pc_h = doc.add_paragraph()
    pc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pc_h.paragraph_format.space_before = Pt(12)
    pc_h.paragraph_format.space_after = Pt(18)
    r = pc_h.add_run("CERTIFICATION")
    format_run(r, size_pt=16, bold=True)

    cert_text = (
        'This is to certify that the project report titled "Design and Implementation of a Goal Oriented '
        'AI Web Agent for Intelligent Website Navigation and Task Execution" was carried out by the members '
        f'of Group 6 listed below, in partial fulfilment of the requirements of the course {COURSE_CODE} '
        f'({COURSE_TITLE}), in the {DEPARTMENT}, {INSTITUTION}, {LOCATION}.'
    )
    pc_body = doc.add_paragraph()
    pc_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pc_body.paragraph_format.line_spacing = 1.5
    pc_body.paragraph_format.space_after = Pt(16)
    r = pc_body.add_run(cert_text)
    format_run(r, size_pt=12, bold=False)

    # Certification Table (with Signature column)
    table_c = doc.add_table(rows=1, cols=4)
    table_c.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_c, color="666666", sz="6", val="single")
    
    col_widths_c = [Inches(0.6), Inches(2.9), Inches(1.6), Inches(1.5)]
    hdr_cells_c = table_c.rows[0].cells
    hdr_titles_c = ["S/N", "Name", "Matric No.", "Signature"]
    for idx, title in enumerate(hdr_titles_c):
        hdr_cells_c[idx].width = col_widths_c[idx]
        set_cell_margins(hdr_cells_c[idx], top=100, bottom=100)
        set_cell_background(hdr_cells_c[idx], "E8EEF5")
        p = hdr_cells_c[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in [0, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        format_run(r, size_pt=11, bold=True)

    for s_no, name, mat_no in MEMBERS:
        row_cells = table_c.add_row().cells
        for idx, val in enumerate([s_no, name, mat_no, ""]):
            row_cells[idx].width = col_widths_c[idx]
            # Height for signature
            set_cell_margins(row_cells[idx], top=100, bottom=100)
            p = row_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in [0, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=11, bold=False)

    # Lecturer Sign-off
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(36)
    p_sign.paragraph_format.space_after = Pt(0)
    p_sign.paragraph_format.line_spacing = 1.3
    r1 = p_sign.add_run(f"{LECTURER}\nCourse Lecturer\n\n\n_____________________________\nSignature")
    format_run(r1, size_pt=12, bold=False)

    p_date = doc.add_paragraph()
    p_date.paragraph_format.space_before = Pt(6)
    p_date.paragraph_format.space_after = Pt(0)
    r2 = p_date.add_run("Date: .......................................")
    format_run(r2, size_pt=12, bold=False)

    p_pg_c = doc.add_paragraph()
    p_pg_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_pg_c.paragraph_format.space_before = Pt(20)
    r_pg_c = p_pg_c.add_run("ii")
    format_run(r_pg_c, size_pt=11, italic=True)

    doc.add_page_break()

    print("Building Table of Contents...")
    # =========================================================================
    # PAGE 3: TABLE OF CONTENTS
    # =========================================================================
    ptoc_h = doc.add_paragraph()
    ptoc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ptoc_h.paragraph_format.space_before = Pt(12)
    ptoc_h.paragraph_format.space_after = Pt(18)
    r = ptoc_h.add_run("TABLE OF CONTENTS")
    format_run(r, size_pt=16, bold=True)

    TOC_ITEMS = [
        ("CERTIFICATION", "ii", True),
        ("CHAPTER ONE: INTRODUCTION", "1", True),
        ("  1.1 Background of the Study", "1", False),
        ("  1.2 Statement of the Problem", "2", False),
        ("  1.3 Aim and Objectives of the Study", "3", False),
        ("  1.4 Research Questions", "4", False),
        ("  1.5 Significance of the Study", "4", False),
        ("  1.6 Scope and Delimitations of the Study", "5", False),
        ("  1.7 Definition of Terms", "6", False),
        ("  1.8 Organization of the Report", "6", False),
        ("CHAPTER TWO: LITERATURE REVIEW", "7", True),
        ("  2.1 Introduction", "7", False),
        ("  2.2 Conceptual Framework", "8", False),
        ("  2.3 The Evolution of Autonomous Web Agents", "9", False),
        ("  2.4 Large Language Models (LLMs) in Web Navigation and Reasoning", "10", False),
        ("  2.5 Chrome DevTools Protocol (CDP) & DOM State Representation", "12", False),
        ("  2.6 Multimodal Vision & Grounding in Web Tasks", "14", False),
        ("  2.7 Continuous Voice Interfaces & Dual-Engine Speech Processing", "16", False),
        ("  2.8 E-Commerce Intelligence & Deep Information Extraction", "18", False),
        ("  2.9 Review of Related Works & Contemporary Autonomous Agent Frameworks", "20", False),
        ("  2.10 Summary of the Literature Review and Research Gap", "22", False),
        ("CHAPTER THREE: METHODOLOGY", "23", True),
        ("  3.1 Introduction", "23", False),
        ("  3.2 Architectural Design & System Framework", "24", False),
        ("  3.3 Team Organization and Workflow", "26", False),
        ("  3.4 Data Ingestion and Semantic DOM Parsing Pipeline", "27", False),
        ("  3.5 Smart Intent Routing Engine", "29", False),
        ("  3.6 5-Stage Visual Execution Pipeline Design", "31", False),
        ("  3.7 Dual-Engine Voice System & Gemini Cloud STT Fallback Architecture", "33", False),
        ("  3.8 Deep Market Search Engine Implementation", "35", False),
        ("  3.9 Security, Error Recovery, and Resilient Multi-Model Fallback Mechanics", "37", False),
        ("  3.10 System Deployment and Cloudflare Zero-Trust Tunnel Architecture", "39", False),
        ("CHAPTER FOUR: RESULTS AND DISCUSSION", "41", True),
        ("  4.1 Introduction", "41", False),
        ("  4.2 Experimental Setup and Test Environments", "42", False),
        ("  4.3 Evaluation of Intent Classification Accuracy and Latency", "44", False),
        ("  4.4 Performance Analysis of the 5-Stage Execution Feed", "46", False),
        ("  4.5 Real-Time Voice Interaction & Latency Benchmark", "48", False),
        ("  4.6 Deep Information Extraction & Jumia E-Commerce Case Study", "50", False),
        ("  4.7 Autonomous Live Browser Navigation & CDP Interaction Results", "52", False),
        ("  4.8 Error Recovery and Multi-Model Fallback Resilience Under Traffic Spikes", "54", False),
        ("  4.9 Discussion of Findings & Academic Implications", "56", False),
        ("CHAPTER FIVE: CONCLUSION AND RECOMMENDATIONS", "58", True),
        ("  5.1 Summary of Findings", "58", False),
        ("  5.2 Contributions to Knowledge", "59", False),
        ("  5.3 Limitations of the Study", "60", False),
        ("  5.4 Recommendations for Future Research", "61", False),
        ("  5.5 Final Remarks", "62", False),
        ("REFERENCES", "63", True)
    ]

    for item_text, pg, is_major in TOC_ITEMS:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(2) if not is_major else Pt(4)
        
        # Build leader dots
        dot_count = max(4, 75 - len(item_text) - len(pg))
        dots = " ." * (dot_count // 2)
        
        r1 = p.add_run(item_text)
        format_run(r1, size_pt=11 if not is_major else 11.5, bold=is_major)
        
        r2 = p.add_run(f" {dots} ")
        format_run(r2, size_pt=10, bold=False, color=RGBColor(140, 140, 140))
        
        r3 = p.add_run(pg)
        format_run(r3, size_pt=11, bold=is_major)

    p_pg_toc = doc.add_paragraph()
    p_pg_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_pg_toc.paragraph_format.space_before = Pt(16)
    r_pg_toc = p_pg_toc.add_run("iii")
    format_run(r_pg_toc, size_pt=11, italic=True)

    doc.add_page_break()

    print("Adding Chapters 1 & 2...")
    # =========================================================================
    # CHAPTERS 1, 2, 3, 4, 5
    # =========================================================================
    def render_chapter(ch_data):
        # Chapter Title
        p_ch = doc.add_paragraph()
        p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ch.paragraph_format.space_before = Pt(12)
        p_ch.paragraph_format.space_after = Pt(18)
        r = p_ch.add_run(ch_data["title"])
        format_run(r, size_pt=16, bold=True)

        for sec_title, paragraphs in ch_data["sections"]:
            p_sec = doc.add_paragraph()
            p_sec.paragraph_format.space_before = Pt(12)
            p_sec.paragraph_format.space_after = Pt(6)
            r = p_sec.add_run(sec_title)
            format_run(r, size_pt=13, bold=True)

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

        doc.add_page_break()

    render_chapter(CHAPTER_1_DATA)
    render_chapter(CHAPTER_2_DATA)
    print("Adding Chapter 3...")
    render_chapter(CHAPTER_3_DATA)
    print("Adding Chapters 4 & 5...")
    render_chapter(CHAPTER_4_DATA)
    render_chapter(CHAPTER_5_DATA)

    print("Adding References...")
    # =========================================================================
    # REFERENCES
    # =========================================================================
    p_ref_h = doc.add_paragraph()
    p_ref_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref_h.paragraph_format.space_before = Pt(12)
    p_ref_h.paragraph_format.space_after = Pt(18)
    r = p_ref_h.add_run("REFERENCES")
    format_run(r, size_pt=16, bold=True)

    for ref in REFERENCES_DATA:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        r = p.add_run(ref)
        format_run(r, size_pt=11.5, bold=False)

    # Save documents
    desktop_path = Path("C:/Users/Laptop/Desktop/Group 6 Report.docx")
    project_path = Path("C:/Users/Laptop/OneDrive/Documenten/group 6 agent/Group 6 Report.docx")

    doc.save(str(project_path))
    print(f"[OK] Saved project report to: {project_path}")
    try:
        doc.save(str(desktop_path))
        print(f"[OK] Saved desktop report to: {desktop_path}")
    except Exception as e:
        print(f"[Note] Desktop save note: {e}")

# =========================================================================
# EXPERIMENTAL TABLES IN CHAPTER 4
# =========================================================================
def render_table_4_1(doc):
    t = doc.add_table(rows=1, cols=6)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(1.0), Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.1)]
    headers = ["Query Class", "Total Trials", "Heuristic Match", "LLM Fallback", "Total Correct", "Accuracy (%)"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=90, bottom=90)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=10, bold=True)

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
            set_cell_margins(row_cells[i], top=70, bottom=70)
            if is_total:
                set_cell_background(row_cells[i], "F0F4F8")
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=10, bold=is_total)

def render_table_4_2(doc):
    t = doc.add_table(rows=1, cols=7)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(0.8), Inches(0.9), Inches(0.9), Inches(0.8), Inches(0.9), Inches(1.1)]
    headers = ["Task Modality", "Stage 1 (s)", "Stage 2 (s)", "Stage 3 (s)", "Stage 4 (s)", "Stage 5 (s)", "Total Latency"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=90, bottom=90)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9.5, bold=True)

    data = [
        ["Direct AI Answer", "0.38", "0.42", "0.45", "0.31", "0.20", "1.76 s"],
        ["Deep Market Search", "0.52", "0.85", "1.42", "0.54", "0.40", "3.73 s"],
        ["Live Browser Navigation", "0.64", "4.82", "5.16", "2.10", "2.10", "14.82 s"]
    ]
    for row in data:
        row_cells = t.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].width = col_w[i]
            set_cell_margins(row_cells[i], top=70, bottom=70)
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9.5, bold=(i == 6))

def render_table_4_3(doc):
    t = doc.add_table(rows=1, cols=6)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(1.5), Inches(1.2), Inches(1.1), Inches(1.1), Inches(1.0), Inches(1.1)]
    headers = ["Test Environment", "Ambient Noise", "Trials", "Native Web Speech", "Gemini Cloud STT", "Echo Suppression"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=90, bottom=90)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=9.5, bold=True)

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
            set_cell_margins(row_cells[i], top=70, bottom=70)
            if is_total:
                set_cell_background(row_cells[i], "F0F4F8")
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9.5, bold=is_total)

def render_table_4_4(doc):
    t = doc.add_table(rows=1, cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="777777", sz="4", val="single")
    col_w = [Inches(2.2), Inches(1.5), Inches(1.3), Inches(2.2)]
    headers = ["Product Name & Brand", "Style / Category", "Price (₦)", "Key Specifications & Rating"]
    hdr_cells = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = col_w[i]
        set_cell_margins(hdr_cells[i], top=90, bottom=90)
        set_cell_background(hdr_cells[i], "D9E2EC")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        format_run(r, size_pt=10, bold=True)

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
            set_cell_margins(row_cells[i], top=80, bottom=80)
            p = row_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            format_run(r, size_pt=9.5, bold=(i == 2))

if __name__ == "__main__":
    create_report()
