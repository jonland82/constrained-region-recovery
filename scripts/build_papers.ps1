$ErrorActionPreference = 'Stop'

$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$papersDirectory = Join-Path $workspaceRoot 'papers'
$buildDirectory = Join-Path $workspaceRoot 'build\latex'
New-Item -ItemType Directory -Path $buildDirectory -Force | Out-Null

function Invoke-LatexPass([string]$SourceName) {
    & pdflatex '-interaction=nonstopmode' '-halt-on-error' '-output-directory=../build/latex' $SourceName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "LaTeX failed for $SourceName. Read the log in $buildDirectory."
    }
}

Push-Location -LiteralPath $papersDirectory
try {
    Invoke-LatexPass 'inverse_sampling_region.tex'
    & bibtex '..\build\latex\inverse_sampling_region' | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "BibTeX failed for inverse_sampling_region.tex. Read the log in $buildDirectory."
    }
    Invoke-LatexPass 'inverse_sampling_region.tex'
    Invoke-LatexPass 'inverse_sampling_region.tex'
    Invoke-LatexPass 'inverse_sampling_shared_references.tex'
    Invoke-LatexPass 'inverse_sampling_shared_references.tex'

    foreach ($stem in @('inverse_sampling_region', 'inverse_sampling_shared_references')) {
        Copy-Item -LiteralPath (Join-Path $buildDirectory "$stem.pdf") -Destination (Join-Path $papersDirectory "$stem.pdf")
        Write-Output "Built papers\$stem.pdf"
    }
}
finally {
    Pop-Location
}
