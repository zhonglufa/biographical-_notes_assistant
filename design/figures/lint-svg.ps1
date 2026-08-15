#!/usr/bin/env pwsh
# lint-svg.ps1 - SVG 校验脚本 (PowerShell 版, 无 Node.js 备用方案)
# 对应: design/figures/lint-svg.cjs

[CmdletBinding()]
param(
    [string[]]$Files = @(),
    [string]$Dir = "",
    [switch]$Json,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

# ============================================================
# 配置 (与 lint-svg.cjs 同步)
# ============================================================

$ALLOWED_COLORS = @(
    '#1A73E8','#22C55E','#EF4444','#E8A317','#F59E0B',
    '#9CA3AF','#333333','#666666','#999999','#F8F9FA',
    '#DBEAFE','#F0F0F0','#FFFFFF','#DC2626','#1f2937',
    '#475569','#64748b','#0284c7','#e0f2fe','#f0fdf4',
    '#fef2f2','#f8fafc','#e2e8f0','#f0f9ff','#fdf4ff',
    '#94a3b8','#F3F4F6','#6B7280','#CBD5E1',
    '#D1D5DB','#F9FAFB',
    '#000000','#00000010','#00000020',
    'none'
)

# 跳过透明 / 无填充的特殊值 (不区分大小写)
$SKIP_COLORS = @('NONE', 'TRANSPARENT', 'CURRENTCOLOR', '')

$ALLOWED_FONT_SIZES = @(9, 10, 11, 12, 13, 14, 16)
$ALLOWED_STROKE_WIDTHS = @(0.5, 1, 1.5, 2, 2.5, 3)
$ASPECT_RATIO_MIN = 1.33
$ASPECT_RATIO_MAX = 2.0
$PROTOCOL_REGEX = '([A-Z][A-Z0-9]+):(\d{2,5})'

# ============================================================
# 解析
# ============================================================

function Get-ViewBox([string]$Content) {
    if ($Content -match 'viewBox="([^"]+)"') {
        $parts = $Matches[1].Trim() -split '[\s,]+'
        if ($parts.Count -eq 4) {
            return @{ x=[double]$parts[0]; y=[double]$parts[1]; w=[double]$parts[2]; h=[double]$parts[3] }
        }
    }
    return $null
}

function Get-Attr([string]$AttrStr, [string]$Name) {
    $pattern1 = '(?:\s|^)' + [regex]::Escape($Name) + '="([^"]*)"'
    if ($AttrStr -match $pattern1) { return $Matches[1] }
    $pattern2 = '(?:\s|^)' + [regex]::Escape($Name) + '=([^\s>]+)'
    if ($AttrStr -match $pattern2) { return $Matches[1] }
    return ""
}

function Get-Rects([string]$Content) {
    $rects = New-Object System.Collections.ArrayList
    $regex = [regex]'<rect\b([^/>]*)\/?>'
    foreach ($m in $regex.Matches($Content)) {
        $a = $m.Groups[1].Value
        [void]$rects.Add([pscustomobject]@{
            x = [double](Get-Attr $a 'x')
            y = [double](Get-Attr $a 'y')
            w = [double](Get-Attr $a 'width')
            h = [double](Get-Attr $a 'height')
            fill = Get-Attr $a 'fill'
            stroke = Get-Attr $a 'stroke'
            strokeDasharray = Get-Attr $a 'stroke-dasharray'
        })
    }
    return $rects
}

function Get-Texts([string]$Content) {
    $texts = New-Object System.Collections.ArrayList
    $regex = [regex]'<text\b([^>]*)>([\s\S]*?)<\/text>'
    foreach ($m in $regex.Matches($Content)) {
        $a = $m.Groups[1].Value
        $content = $m.Groups[2].Value -replace '<[^>]+>','' -replace '^\s+|\s+$',''
        [void]$texts.Add([pscustomobject]@{
            x = [double](Get-Attr $a 'x')
            y = [double](Get-Attr $a 'y')
            fontSize = [double](Get-Attr $a 'font-size')
            textAnchor = Get-Attr $a 'text-anchor'
            content = $content
        })
    }
    return $texts
}

function Get-Circles([string]$Content) {
    $circles = New-Object System.Collections.ArrayList
    $regex = [regex]'<circle\b([^/>]*)\/?>'
    foreach ($m in $regex.Matches($Content)) {
        $a = $m.Groups[1].Value
        [void]$circles.Add([pscustomobject]@{
            cx = [double](Get-Attr $a 'cx')
            cy = [double](Get-Attr $a 'cy')
            r = [double](Get-Attr $a 'r')
        })
    }
    return $circles
}

function Get-Paths([string]$Content) {
    $paths = New-Object System.Collections.ArrayList
    $regex = [regex]'<path\b([^/>]*)\/?>'
    foreach ($m in $regex.Matches($Content)) {
        $a = $m.Groups[1].Value
        [void]$paths.Add([pscustomobject]@{
            d = Get-Attr $a 'd'
            stroke = Get-Attr $a 'stroke'
            strokeWidth = [double](Get-Attr $a 'stroke-width')
            strokeDasharray = Get-Attr $a 'stroke-dasharray'
            fill = Get-Attr $a 'fill'
        })
    }
    return $paths
}

# ============================================================
# 结果对象 (使用 ArrayList 解决 PSCustomObject 属性 += 问题)
# ============================================================

function New-LintResult {
    param([string]$FilePath)
    return [pscustomobject]@{
        file = $FilePath
        errors = New-Object System.Collections.ArrayList
        warnings = New-Object System.Collections.ArrayList
        passed = New-Object System.Collections.ArrayList
    }
}

function Add-Error($Result, [string]$Msg) { [void]$Result.errors.Add($Msg) }
function Add-Warning($Result, [string]$Msg) { [void]$Result.warnings.Add($Msg) }
function Add-Pass($Result, [string]$Msg) { [void]$Result.passed.Add($Msg) }

# ============================================================
# 校验规则
# ============================================================

function Test-StrokeWidth($Paths, $Result) {
    foreach ($p in $Paths) {
        if ($p.stroke -and $p.stroke -ne 'none' -and $p.strokeWidth -gt 0) {
            if ($ALLOWED_STROKE_WIDTHS -notcontains $p.strokeWidth) {
                Add-Warning $Result "STROKE-WIDTH: line width $($p.strokeWidth) not in standard list ($($ALLOWED_STROKE_WIDTHS -join ','))"
            }
        }
    }
    Add-Pass $Result "STROKE-WIDTH"
}

function Test-ColorPalette($Paths, $Rects, $Circles, $Result) {
    $used = @{}
    $skipUpper = @($SKIP_COLORS | ForEach-Object { $_.ToUpper() })
    foreach ($p in $Paths) {
        if ($p.stroke) {
            $s = $p.stroke.ToUpper()
            if ($skipUpper -inotcontains $s) { $used[$s] = $true }
        }
        if ($p.fill) {
            $f = $p.fill.ToUpper()
            if ($skipUpper -inotcontains $f) { $used[$f] = $true }
        }
    }
    foreach ($r in $Rects) {
        if ($r.fill) {
            $f = $r.fill.ToUpper()
            if ($skipUpper -inotcontains $f) { $used[$f] = $true }
        }
        if ($r.stroke) {
            $s = $r.stroke.ToUpper()
            if ($skipUpper -inotcontains $s) { $used[$s] = $true }
        }
    }
    foreach ($c in $Circles) {
        if ($c.fill) {
            $f = $c.fill.ToUpper()
            if ($skipUpper -inotcontains $f) { $used[$f] = $true }
        }
    }
    $allowedUpper = @($ALLOWED_COLORS | ForEach-Object { $_.ToUpper() })
    foreach ($color in $used.Keys) {
        if ($allowedUpper -inotcontains $color) {
            Add-Warning $Result "COLOR-PALETTE: color $color not in mandatory palette"
        }
    }
    Add-Pass $Result "COLOR-PALETTE"
}

function Test-FontSize($Texts, $Result) {
    foreach ($t in $Texts) {
        if ($t.fontSize -gt 0 -and $ALLOWED_FONT_SIZES -notcontains $t.fontSize) {
            Add-Warning $Result "FONT-SIZE: font-size $($t.fontSize) not in standard list ($($ALLOWED_FONT_SIZES -join ',')) (text='$($t.content)')"
        }
    }
    Add-Pass $Result "FONT-SIZE"
}

function Test-AspectRatio($ViewBox, $Result) {
    if (-not $ViewBox) {
        Add-Warning $Result "ASPECT-RATIO: viewBox attribute not found"
        return
    }
    if ($ViewBox.h -le 0) { return }
    $ratio = $ViewBox.w / $ViewBox.h
    if ($ratio -lt $ASPECT_RATIO_MIN -or $ratio -gt $ASPECT_RATIO_MAX) {
        Add-Warning $Result "ASPECT-RATIO: ratio $([math]::Round($ratio,2)) not in 4:3 ~ 2:1 range"
    }
    Add-Pass $Result "ASPECT-RATIO"
}

function Test-C3Protocol($Texts, $Result) {
    $violation = $false
    foreach ($t in $Texts) {
        if ($t.content -and $t.content -match $PROTOCOL_REGEX) {
            Add-Error $Result "C3-PROTOCOL: C3 forbids protocol:port labels ('$($t.content)'), belongs to C2 layer"
            $violation = $true
        }
    }
    if (-not $violation) { Add-Pass $Result "C3-PROTOCOL" }
}

function Test-C3ContainerBoundary($Rects, $Result) {
    $has = $false
    foreach ($r in $Rects) {
        if ($r.strokeDasharray -and $r.strokeDasharray -match '6[, ]*4' -and $r.w -gt 300 -and $r.h -gt 300) {
            $has = $true; break
        }
    }
    if ($has) { Add-Pass $Result "C3-CONTAINER-BOUNDARY" }
    else { Add-Warning $Result "C3-CONTAINER-BOUNDARY: missing target container dashed boundary (stroke-dasharray='6,4' large rect)" }
}

function Test-C3GrayBox($Rects, $Result) {
    $has = $false
    foreach ($r in $Rects) {
        if (($r.fill).ToUpper() -eq '#F3F4F6' -and ($r.stroke).ToUpper() -eq '#9CA3AF') {
            $has = $true; break
        }
    }
    if ($has) { Add-Pass $Result "C3-GRAY-BOX" }
    elseif ($Rects.Count -gt 5) { Add-Warning $Result "C3-GRAY-BOX: recommend gray box (fill=#F3F4F6 + stroke=#9CA3AF) for external containers" }
}

function Test-C3ComponentCount($Rects, $Result) {
    $n = 0
    foreach ($r in $Rects) {
        if (($r.fill).ToUpper() -eq '#E0F2FE') { $n++ }
    }
    if ($n -gt 12) { Add-Error $Result "C3-COMPONENT-COUNT: internal components $n exceed limit 12" }
    else { Add-Pass $Result "C3-COMPONENT-COUNT" }
}

function Test-C3InterfaceMarker($Circles, $Result) {
    if ($Circles.Count -gt 0) { Add-Pass $Result "C3-INTERFACE-MARKER" }
    else { Add-Warning $Result "C3-INTERFACE-MARKER: recommend lollipop (circle marker) for interfaces" }
}

# ============================================================
# 单文件校验
# ============================================================

function Test-Svg([string]$FilePath) {
    $content = Get-Content -Path $FilePath -Raw -Encoding UTF8
    $result = New-LintResult $FilePath

    $vb = Get-ViewBox $content
    $rects = Get-Rects $content
    $texts = Get-Texts $content
    $circles = Get-Circles $content
    $paths = Get-Paths $content

    Test-StrokeWidth $paths $result
    Test-ColorPalette $paths $rects $circles $result
    Test-FontSize $texts $result
    Test-AspectRatio $vb $result

    if ($FilePath -match 'c3' -or $FilePath -match 'c3-component') {
        Test-C3Protocol $texts $result
        Test-C3ContainerBoundary $rects $result
        Test-C3GrayBox $rects $result
        Test-C3ComponentCount $rects $result
        Test-C3InterfaceMarker $circles $result
    }

    return $result
}

# ============================================================
# 输出
# ============================================================

function Show-Result($Result, [bool]$JsonOutput) {
    if ($JsonOutput) {
        $r = [pscustomobject]@{
            file = $Result.file
            errors = @($Result.errors)
            warnings = @($Result.warnings)
            passed = @($Result.passed)
        }
        return ($r | ConvertTo-Json -Depth 5)
    }
    $status = if ($Result.errors.Count -gt 0) { "FAIL" }
              elseif ($Result.warnings.Count -gt 0) { "PASS_WITH_WARNINGS" }
              else { "PASS" }
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "File: $($Result.file)"
    Write-Host "Status: $status"
    Write-Host "Passed: $($Result.passed.Count), Warnings: $($Result.warnings.Count), Errors: $($Result.errors.Count)"
    Write-Host "============================================================"
    if ($Result.errors.Count -gt 0) {
        Write-Host ""
        Write-Host "[ERRORS] (must fix):" -ForegroundColor Red
        for ($i=0; $i -lt $Result.errors.Count; $i++) {
            Write-Host "  [$($i+1)] $($Result.errors[$i])" -ForegroundColor Red
        }
    }
    if ($Result.warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "[WARNINGS] (suggested improvements):" -ForegroundColor Yellow
        for ($i=0; $i -lt $Result.warnings.Count; $i++) {
            Write-Host "  [$($i+1)] $($Result.warnings[$i])" -ForegroundColor Yellow
        }
    }
    if ($Result.passed.Count -gt 0) {
        Write-Host ""
        Write-Host "[PASSED]:"
        $grouped = $Result.passed | Group-Object
        foreach ($g in $grouped) {
            Write-Host "  [$($g.Name)] x $($g.Count)"
        }
    }
    return $status
}

# ============================================================
# 主入口
# ============================================================

$fileList = @()
if ($Dir) {
    $fullDir = Resolve-Path $Dir
    $fileList = @(Get-ChildItem -Path $fullDir -Filter "*.svg" | ForEach-Object { $_.FullName })
} else {
    $fileList = @($Files)
}

if ($fileList.Count -eq 0) {
    Write-Host "No SVG files specified" -ForegroundColor Red
    exit 2
}

$hasFail = $false
$hasWarning = $false
$summary = New-Object System.Collections.ArrayList
foreach ($f in $fileList) {
    if (-not (Test-Path $f)) {
        Write-Host "File not found: $f" -ForegroundColor Red
        $hasFail = $true
        continue
    }
    $r = Test-Svg $f
    $st = Show-Result $r ([bool]$Json)
    if ($st -eq "FAIL") { $hasFail = $true }
    if ($st -eq "PASS_WITH_WARNINGS") { $hasWarning = $true }
    [void]$summary.Add([pscustomobject]@{
        file = $r.file
        status = $st
        errors = $r.errors.Count
        warnings = $r.warnings.Count
    })
}

if (-not $Json) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "Summary:" -ForegroundColor Cyan
    foreach ($s in $summary) {
        $color = switch ($s.status) {
            "FAIL" { "Red" }
            "PASS_WITH_WARNINGS" { "Yellow" }
            default { "Green" }
        }
        Write-Host "  $($s.file): $($s.status) (E=$($s.errors), W=$($s.warnings))" -ForegroundColor $color
    }
}

if ($Strict -and $hasWarning) { $hasFail = $true }
exit $(if ($hasFail) { 1 } else { 0 })
