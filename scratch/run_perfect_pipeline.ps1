$projDir = "C:\Users\Laptop\OneDrive\Documenten\group 6 agent"
Set-Location $projDir

Write-Output "=== STEP 1: Generating Initial Document Structure ==="
& ".venv\Scripts\python.exe" "scratch\generate_perfect_report.py"

Write-Output "=== STEP 2: Scanning Exact Page Numbers in Word COM ==="
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("$projDir\scratch\perfect_report.docx")

$tocOrder = @(
    "1.1 Background of the Study",
    "1.2 Statement of the Problem",
    "1.3 Aim and Objectives of the Study",
    "1.4 Research Questions",
    "1.5 Significance of the Study",
    "1.6 Scope and Delimitations of the Study",
    "1.7 Definition of Terms",
    "1.8 Organization of the Report",
    "CHAPTER TWO: LITERATURE REVIEW",
    "2.1 Introduction",
    "2.2 Conceptual Framework",
    "2.3 The Evolution of Autonomous Web Agents",
    "2.4 Large Language Models (LLMs) in Web Navigation and Reasoning",
    "2.5 Chrome DevTools Protocol (CDP) & DOM State Representation",
    "2.6 Multimodal Vision & Grounding in Web Tasks",
    "2.7 Continuous Voice Interfaces & Dual-Engine Speech Processing",
    "2.8 E-Commerce Intelligence & Deep Information Extraction",
    "2.9 Review of Related Works & Contemporary Autonomous Agent Frameworks",
    "2.10 Summary of the Literature Review and Research Gap",
    "CHAPTER THREE: METHODOLOGY",
    "3.1 Introduction",
    "3.2 Architectural Design & System Framework",
    "3.3 Team Organization and Workflow",
    "3.4 Data Ingestion and Semantic DOM Parsing Pipeline",
    "3.5 Smart Intent Routing Engine",
    "3.6 5-Stage Visual Execution Pipeline Design",
    "3.7 Dual-Engine Voice System & Gemini Cloud STT Fallback Architecture",
    "3.8 Deep Market Search Engine Implementation",
    "3.9 Security, Error Recovery, and Resilient Multi-Model Fallback Mechanics",
    "3.10 System Deployment and Cloudflare Zero-Trust Tunnel Architecture",
    "CHAPTER FOUR: RESULTS AND DISCUSSION",
    "4.1 Introduction",
    "4.2 Experimental Setup and Test Environments",
    "4.3 Evaluation of Intent Classification Accuracy and Latency",
    "4.4 Performance Analysis of the 5-Stage Execution Feed",
    "4.5 Real-Time Voice Interaction & Latency Benchmark",
    "4.6 Deep Information Extraction & Jumia E-Commerce Case Study",
    "4.7 Autonomous Live Browser Navigation & CDP Interaction Results",
    "4.8 Error Recovery and Multi-Model Fallback Resilience Under Traffic Spikes",
    "4.9 Discussion of Findings & Academic Implications",
    "CHAPTER FIVE: CONCLUSION AND RECOMMENDATIONS",
    "5.1 Summary of Findings",
    "5.2 Contributions to Knowledge",
    "5.3 Limitations of the Study",
    "5.4 Recommendations for Future Research",
    "5.5 Final Remarks",
    "REFERENCES"
)

# Chapter 1 is always page 1 of body
$map = @{
    "CERTIFICATION" = "ii"
    "CHAPTER ONE: INTRODUCTION" = "1"
}

# Scan paragraphs in Section 2 (Body Section) only!
$secBody = $doc.Sections.Item(2)
foreach ($para in $secBody.Range.Paragraphs) {
    $t = $para.Range.Text.Trim()
    foreach ($key in $tocOrder) {
        if (-not $map.ContainsKey($key) -and ($t -eq $key -or $t.StartsWith($key))) {
            # wdActiveEndAdjustedPageNumber = 27 (returns page number within section, starting at 1!)
            $pgNum = $para.Range.Information(27)
            $map[$key] = "$pgNum"
            Write-Output "Mapped: $key -> Page $pgNum"
            break
        }
    }
}

$doc.Close()

Write-Output "`n=== STEP 3: Re-generating Final Document with Exact Page Numbers ==="
# Serialize map to json without UTF-8 BOM
$pairs = @()
foreach ($k in $map.Keys) {
    $safeK = $k.Replace('\', '\\').Replace('"', '\"')
    $safeV = $map[$k]
    $pairs += "`"$safeK`": `"$safeV`""
}
$jsonString = "{" + ($pairs -join ", ") + "}"
[System.IO.File]::WriteAllText("$projDir\scratch\toc_map.json", $jsonString, [System.Text.Encoding]::ASCII)

$rebuildScript = @"
import json
from scratch.generate_perfect_report import build_perfect_document

with open('scratch/toc_map.json', 'r', encoding='ascii') as f:
    toc_dict = json.load(f)

doc = build_perfect_document(toc_dict=toc_dict)
doc.save('Group 6 Report.docx')
print('[OK] Document successfully generated with exact page numbers.')
"@
[System.IO.File]::WriteAllText("$projDir\scratch\rebuild.py", $rebuildScript, [System.Text.Encoding]::ASCII)
& ".venv\Scripts\python.exe" "scratch\rebuild.py"

Write-Output "`n=== STEP 4: Inspecting Every Page in Word COM for Blank Content & Exporting PDF ==="
$docFinal = $word.Documents.Open("$projDir\Group 6 Report.docx")
$pdfOut = "$projDir\Group 6 Report.pdf"
$docFinal.SaveAs([ref]$pdfOut, [ref]17) # 17 = wdFormatPDF

$totalCount = $docFinal.ComputeStatistics(2) # 2 = wdStatisticPages
Write-Output "Total Final Page Count: $totalCount"

$emptyPages = @()
for ($p = 1; $p -le $totalCount; $p++) {
    $rStart = $docFinal.GoTo(1, 1, $p)
    if ($p -eq $totalCount) {
        $endPos = $docFinal.Content.End
    } else {
        $rNext = $docFinal.GoTo(1, 1, ($p + 1))
        $endPos = $rNext.Start
    }
    $pageRange = $docFinal.Range($rStart.Start, $endPos)
    $pageText = $pageRange.Text.Trim()
    $firstLine = if ($pageText.Length -gt 0) { ($pageText -split "`r`n|`r|`n")[0].Substring(0, [Math]::Min(50, ($pageText -split "`r`n|`r|`n")[0].Length)) } else { "<EMPTY>" }
    Write-Output "Page $($p): Length=$($pageText.Length) | First: $($firstLine)"
    
    if ($pageText.Length -eq 0) {
        $emptyPages += $p
    }
}

$docFinal.Close()
$word.Quit()

if ($emptyPages.Count -eq 0) {
    Write-Output "`n>>> [SUCCESS] 100% VERIFIED: ZERO EMPTY PAGES in entire document! <<<"
} else {
    Write-Output "`n>>> [WARNING] Empty page detected on: $($emptyPages -join ', ') <<<"
}

Write-Output "`n=== STEP 5: Copying to Desktop and Documents Folders ==="
$desktop = "C:\Users\Laptop\OneDrive\Desktop"
$docs = "C:\Users\Laptop\OneDrive\Documenten"

Copy-Item "$projDir\Group 6 Report.docx" (Join-Path $desktop "Group 6 Report.docx") -Force
Copy-Item "$projDir\Group 6 Report.pdf" (Join-Path $desktop "Group 6 Report.pdf") -Force
Copy-Item "$projDir\Group 6 Report.docx" (Join-Path $docs "Group 6 Report.docx") -Force
Copy-Item "$projDir\Group 6 Report.pdf" (Join-Path $docs "Group 6 Report.pdf") -Force

Write-Output "[OK] All files successfully updated and placed in Desktop and Documents!"
