# Análisis estático de TruchaSmart con SciTools Understand (guía S14), pasos 1 a 6 de la guía.
#
# Uso (lo ejecuta el workflow .github/workflows/understand.yml en el runner con Understand):
#   powershell -File tools/understand/analizar.ps1 -Ref develop -Salida docs/understand
#
# Requiere Understand instalado y licenciado en la máquina (variable UND o D:\SciTools).
param(
    [string]$Repo = "https://github.com/Ronald-Castillon/trucha-smart.git",
    [string]$Ref = "develop",
    [string]$Salida = "docs/understand",
    [string]$Trabajo = "$env:RUNNER_TEMP\understand"
)
$ErrorActionPreference = "Stop"
$und = if ($env:UND) { $env:UND } else { "D:\SciTools\bin\pc-win64\und.exe" }
$Salida = (New-Item -ItemType Directory -Force $Salida).FullName
if (Test-Path $Trabajo) { Remove-Item -Recurse -Force $Trabajo }
New-Item -ItemType Directory -Force $Trabajo | Out-Null
$db = Join-Path $Trabajo "truchasmart.und"

function Paso($titulo) { Write-Host ""; Write-Host "=== $titulo" }
function Und { & $und @args; if ($LASTEXITCODE -ne 0) { throw "und $($args[0]) terminó con código $LASTEXITCODE" } }

Paso "Paso 0 · Licencia de Understand"
Write-Host ("Understand: " + (Get-Item $und).VersionInfo.ProductVersion + " · " + $und)
if ((& $und license -isundlicensed) -ne "1") { throw "Understand no está licenciado en este runner" }
Write-Host (& $und license -licensehowmanydays)

Paso "Paso 1 · Clonar el repositorio GitHub ($Ref)"
git clone --quiet --depth 1 --branch $Ref $Repo (Join-Path $Trabajo "trucha-smart")
$codigo = Join-Path $Trabajo "trucha-smart"
Write-Host ("Commit analizado: " + (git -C $codigo log -1 --format="%h %s"))

Paso "Paso 2 · Crear el proyecto de Understand (Python)"
Und create -db $db -languages python

Paso "Paso 3 · Añadir el código fuente (src/ y tools/)"
Und add -db $db -exclude "__pycache__,.*" (Join-Path $codigo "src") (Join-Path $codigo "tools")
& $und list -db $db files | Measure-Object -Line | ForEach-Object { Write-Host "Archivos en el proyecto: $($_.Lines)" }

Paso "Paso 4 · Analizar el proyecto"
& $und analyze -db $db -all -errors -sarif (Join-Path $Salida "analisis.sarif")
if ($LASTEXITCODE -ne 0) { throw "und analyze terminó con código $LASTEXITCODE" }

Paso "Paso 5 · Emitir reportes (métricas, dependencias, clases, funciones y arquitectura)"
Und settings -db $db -ReportReports "Project Metrics" "File Metrics" "File Average Metrics" "Class Metrics" "Class OO Metrics" "Program Unit Metrics" "Program Unit Complexity" "Imports" `
    -ReportOutputDirectory (Join-Path $Salida "html") -ReportOutputFileSingle (Join-Path $Salida "reporte_understand.txt")
Und report -db $db
Und metrics -db $db (Join-Path $Salida "metricas.csv")
Und export -db $db -dependencies file csv (Join-Path $Salida "dependencias_archivos.csv")
Und export -db $db -dependencies class csv (Join-Path $Salida "dependencias_clases.csv")

Paso "Paso 6 · Resumen automático del reporte"
python tools/understand/resumen.py --salida $Salida --codigo $codigo
if ($LASTEXITCODE -ne 0) { throw "resumen.py terminó con código $LASTEXITCODE" }
Get-ChildItem $Salida | ForEach-Object { Write-Host ("  {0,-34} {1,10:N0} bytes" -f $_.Name, $_.Length) }
