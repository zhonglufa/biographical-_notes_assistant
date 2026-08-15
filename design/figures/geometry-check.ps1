#!/usr/bin/env pwsh
# geometry-check.ps1 - C3 component diagram geometry penetration check

param(
    [string]$File = "",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

function Get-A([string]$s, [string]$n) {
    $p1 = '(?:\s|^)' + [regex]::Escape($n) + '="([^"]*)"'
    if ($s -match $p1) { return $Matches[1] }
    $p2 = '(?:\s|^)' + [regex]::Escape($n) + '=([^\s>]+)'
    if ($s -match $p2) { return $Matches[1] }
    return ""
}

function Parse-D([string]$d) {
    $segs = New-Object System.Collections.ArrayList
    $tokens = [regex]::Matches($d, '([MLHV])([^MLHV]*)')
    $lx = 0.0; $ly = 0.0
    foreach ($t in $tokens) {
        $cmd = $t.Groups[1].Value
        $nums = [regex]::Matches($t.Groups[2].Value, '-?\d+(?:\.\d+)?')
        $n = @($nums | ForEach-Object { [double]$_.Value })
        if ($cmd -eq 'M' -or $cmd -eq 'L') {
            for ($i = 0; $i -lt $n.Count; $i += 2) {
                $x = $n[$i]; $y = $n[$i+1]
                if ($i -eq 0 -and $cmd -eq 'M') {
                    $lx = $x; $ly = $y
                } else {
                    [void]$segs.Add(@{ x1 = $lx; y1 = $ly; x2 = $x; y2 = $y })
                    $lx = $x; $ly = $y
                }
            }
        } elseif ($cmd -eq 'H') {
            foreach ($x in $n) {
                [void]$segs.Add(@{ x1 = $lx; y1 = $ly; x2 = $x; y2 = $ly })
                $lx = $x
            }
        } elseif ($cmd -eq 'V') {
            foreach ($y in $n) {
                [void]$segs.Add(@{ x1 = $lx; y1 = $ly; x2 = $lx; y2 = $y })
                $ly = $y
            }
        }
    }
    return $segs
}

function Test-SegRect($seg, $rect) {
    $x1 = $seg.x1; $y1 = $seg.y1; $x2 = $seg.x2; $y2 = $seg.y2
    $rxMin = $rect.x; $rxMax = $rect.x + $rect.w
    $ryMin = $rect.y; $ryMax = $rect.y + $rect.h

    if ($y1 -eq $y2) {
        $y = $y1
        if ($y -le $ryMin -or $y -ge $ryMax) { return $false }
        $xmin = [Math]::Min($x1, $x2); $xmax = [Math]::Max($x1, $x2)
        if ($xmax -le $rxMin -or $xmin -ge $rxMax) { return $false }
        # Check if both endpoints on rect edges
        $lOn = ($xmin -ge $rxMin -and $xmin -le $rxMax)
        $rOn = ($xmax -ge $rxMin -and $xmax -le $rxMax)
        if ($lOn -and $rOn) { return $false }
        # Allow line touching rect boundary at either endpoint (enter/exit)
        if ($xmin -eq $rxMin -or $xmin -eq $rxMax -or $xmax -eq $rxMin -or $xmax -eq $rxMax) { return $false }
        return $true
    }
    if ($x1 -eq $x2) {
        $x = $x1
        if ($x -le $rxMin -or $x -ge $rxMax) { return $false }
        $ymin = [Math]::Min($y1, $y2); $ymax = [Math]::Max($y1, $y2)
        if ($ymax -le $ryMin -or $ymin -ge $ryMax) { return $false }
        $tOn = ($ymin -ge $ryMin -and $ymin -le $ryMax)
        $bOn = ($ymax -ge $ryMin -and $ymax -le $ryMax)
        if ($tOn -and $bOn) { return $false }
        # Allow: line starts inside box and exits through an edge
        if (($tOn -and $ymin -ge $ryMin -and $ymax -ge $ryMax)) { return $false }
        if (($bOn -and $ymax -le $ryMax -and $ymin -le $ryMin)) { return $false }
        # Allow line touching rect boundary at either endpoint (enter/exit)
        if ($ymin -eq $ryMin -or $ymin -eq $ryMax -or $ymax -eq $ryMin -or $ymax -eq $ryMax) { return $false }
        return $true
    }
    return $true  # diagonal
}

# === Main ===
if (-not $File -or -not (Test-Path $File)) {
    Write-Host "Usage: geometry-check.ps1 -File <file.svg> [-Verbose]" -ForegroundColor Yellow
    exit 2
}

$content = Get-Content -Path $File -Raw -Encoding UTF8

# Collect all rects (skip target container dashed boundary)
$rects = New-Object System.Collections.ArrayList
$regex = [regex]'<rect\b([^/>]*)\/?>'
foreach ($m in $regex.Matches($content)) {
    $a = $m.Groups[1].Value
    $w = [double](Get-A $a 'width')
    $h = [double](Get-A $a 'height')
    $dash = Get-A $a 'stroke-dasharray'
    $fill = Get-A $a 'fill'
    if ($dash -and $dash -match '6[, ]*4' -and $w -gt 300 -and $h -gt 300) {
        continue  # skip target container boundary
    }
    if ($w -le 6) {
        continue  # skip UML activation bars (sequence diagrams)
    }
    if ($fill -and $fill.ToUpper() -eq '#F0F0F0' -and $w -gt 100) {
        continue  # skip UML combined fragment frames
    }
    if ($fill -and $fill.ToUpper() -eq '#F8F9FA' -and $w -gt 500 -and $h -gt 80) {
        $stroke = Get-A $a 'stroke'
        if ($stroke -and $stroke.ToUpper() -eq '#E2E8F0') {
            continue  # skip C2 layer frames (跨层干线/出层连线正常)
        }
    }
    if ($fill -and $fill.ToUpper() -eq '#FFFFFF' -and $w -lt 150 -and $h -lt 30) {
        $stroke = Get-A $a 'stroke'
        if (-not $stroke) {
            continue  # skip line-label background rects (labels sit on lines)
        }
    }
    [void]$rects.Add([pscustomobject]@{
        x = [double](Get-A $a 'x')
        y = [double](Get-A $a 'y')
        w = $w
        h = $h
        desc = "rect"
    })
}

# Collect all paths and their segments (skip paths inside <defs>)
$paths = New-Object System.Collections.ArrayList
$regex = [regex]'<path\b([^/>]*)\/?>'
$idx = 0
# Get content outside <defs> blocks
$contentNoDefs = [regex]::Replace($content, '<defs>[\s\S]*?</defs>', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
foreach ($m in $regex.Matches($contentNoDefs)) {
    $a = $m.Groups[1].Value
    $d = Get-A $a 'd'
    if (-not $d) { continue }
    $pf = Get-A $a 'fill'
    if ($pf -and $pf.ToUpper() -ne 'NONE' -and $pf.ToUpper() -ne '#00000010' -and $pf.ToUpper() -ne '#00000020') {
        continue  # skip filled polygonal faces (3D node sides, shadows) - shapes not links
    }
    $idx++
    [void]$paths.Add(@{
        idx = $idx
        d = $d
        segs = Parse-D $d
    })
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Geometry Check: $File" -ForegroundColor Cyan
Write-Host "  Rects: $($rects.Count), Paths: $($paths.Count)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$errs = 0
$pass = 0
$total = 0

foreach ($p in $paths) {
    foreach ($seg in $p.segs) {
        $total++
        $isH = ($seg.y1 -eq $seg.y2)
        $isV = ($seg.x1 -eq $seg.x2)
        $isD = (-not $isH -and -not $isV)
        if ($isD) {
            Write-Host "[FAIL] DIAGONAL: path#$($p.idx) ($($seg.x1),$($seg.y1))->($($seg.x2),$($seg.y2)) -- C3 mandates orthogonal" -ForegroundColor Red
            $errs++
            continue
        }
        $hit = $false
        foreach ($r in $rects) {
            if (Test-SegRect $seg $r) {
                $orient = if ($isH) { "H" } else { "V" }
                Write-Host "[FAIL] PENETRATION: path#$($p.idx) $orient ($($seg.x1),$($seg.y1))->($($seg.x2),$($seg.y2)) penetrates rect($($r.x),$($r.y),$($r.w),$($r.h))" -ForegroundColor Red
                $errs++
                $hit = $true
                break
            }
        }
        if (-not $hit) {
            if ($Verbose) {
                $orient = if ($isH) { "H" } else { "V" }
                Write-Host "[OK] $orient ($($seg.x1),$($seg.y1))->($($seg.x2),$($seg.y2))"
            }
            $pass++
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Summary: $pass passed, $errs errors, $total total" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($errs -gt 0) { exit 1 } else { exit 0 }
