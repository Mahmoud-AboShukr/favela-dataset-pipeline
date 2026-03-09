# scripts/final_tidy.ps1
# Final tidy: archive distractions, remove junk, keep pipeline clean.
# Safe by design:
# - does NOT delete data/raw
# - archives instead of deleting
# - removes only .ipynb_checkpoints and __pycache__
# - uses git mv when possible

$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "!!  $msg" -ForegroundColor Yellow }
function Ok($msg)   { Write-Host "OK  $msg" -ForegroundColor Green }

# --- 0) Must be run from repo root ---
if (-not (Test-Path ".git")) {
  throw "No .git folder found. Run this script from the repository root."
}

# --- 1) Safety branch ---
$branchName = "chore/final-tidy"
Info "Switching to safety branch $branchName ..."
$exists = (git branch --list $branchName) -match $branchName
if (-not $exists) {
  git checkout -b $branchName | Out-Null
  Ok "Created and switched to $branchName"
} else {
  git checkout $branchName | Out-Null
  Ok "Switched to existing $branchName"
}

# --- 2) Ensure archive structure ---
$stamp = Get-Date -Format "yyyyMMdd"
$archiveRoot = "archive\final_tidy_$stamp"
$archiveMisc = Join-Path $archiveRoot "misc"
$archiveExternal = Join-Path $archiveRoot "external"

Info "Creating archive folders under $archiveRoot"
New-Item -ItemType Directory -Force -Path $archiveMisc | Out-Null
New-Item -ItemType Directory -Force -Path $archiveExternal | Out-Null

# --- 3) Helper: move tracked/untracked paths safely into archive ---
function Move-ToArchive {
  param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$DestPath
  )

  if (-not (Test-Path $SourcePath)) {
    Warn "Not found (skip): $SourcePath"
    return
  }

  # Ensure destination parent exists
  $destParent = Split-Path $DestPath -Parent
  New-Item -ItemType Directory -Force -Path $destParent | Out-Null

  # If git knows about any file under SourcePath, use git mv
  $tracked = (git ls-files $SourcePath 2>$null)
  if ($tracked) {
    Info "git mv: $SourcePath -> $DestPath"
    git mv $SourcePath $DestPath | Out-Null
  } else {
    Info "Move-Item (untracked): $SourcePath -> $DestPath"
    Move-Item -Force $SourcePath $DestPath
  }
}

# --- 4) Archive “distraction” folders (edit here if you want) ---
Info "Archiving distraction folders (code/, cache/, supervisor preprocessing folder with spaces)."

Move-ToArchive -SourcePath "code" -DestPath (Join-Path $archiveMisc "code")
Move-ToArchive -SourcePath "cache" -DestPath (Join-Path $archiveMisc "cache")

# The folder with spaces (your supervisor code). We archive it for now.
Move-ToArchive -SourcePath "src\sentinel\s1 and s2 preprocessing" -DestPath (Join-Path $archiveExternal "s1_s2_preprocessing_original")

# Optional: archive notebooks (uncomment if you want them out of the way)
# Move-ToArchive -SourcePath "notebooks" -DestPath (Join-Path $archiveMisc "notebooks")

Ok "Archiving done."

# --- 5) Remove junk directories (safe to delete) ---
Info "Removing junk folders: .ipynb_checkpoints and __pycache__"
Get-ChildItem -Path . -Directory -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -in @(".ipynb_checkpoints", "__pycache__") } |
  ForEach-Object {
    Warn "Deleting junk folder: $($_.FullName)"
    Remove-Item -Recurse -Force $_.FullName
  }
Ok "Junk folders removed."

# --- 6) Ensure venv is NOT tracked in git index ---
Info "Checking if venv/ is tracked..."
$venvTracked = (git ls-files | Select-String -Pattern "^venv/|^\.venv/" -SimpleMatch)
if ($venvTracked) {
  Warn "venv appears tracked. Removing from index (keeps it locally)."
  if (Test-Path "venv") { git rm -r --cached venv | Out-Null }
  if (Test-Path ".venv") { git rm -r --cached .venv | Out-Null }
  Ok "Removed venv from tracking."
} else {
  Ok "venv is not tracked."
}

# --- 7) Ensure .gitignore contains common ignores (append if missing) ---
$gitignore = ".gitignore"
if (-not (Test-Path $gitignore)) {
  Warn ".gitignore not found, creating one."
  New-Item -ItemType File -Path $gitignore | Out-Null
}

$neededIgnores = @(
  "venv/",
  ".venv/",
  "site/",
  "data/raw/",
  "data/interim/",
  "data/processed/",
  "__pycache__/",
  "*.pyc",
  ".ipynb_checkpoints/"
)

$existing = Get-Content $gitignore -ErrorAction SilentlyContinue
$toAdd = @()
foreach ($rule in $neededIgnores) {
  if ($existing -notcontains $rule) { $toAdd += $rule }
}

if ($toAdd.Count -gt 0) {
  Info "Updating .gitignore with missing rules..."
  Add-Content -Path $gitignore -Value ""
  Add-Content -Path $gitignore -Value "# Added by scripts/final_tidy.ps1"
  $toAdd | ForEach-Object { Add-Content -Path $gitignore -Value $_ }
  Ok ".gitignore updated."
} else {
  Ok ".gitignore already contains needed rules."
}

# --- 8) Show status and next commands ---
Info "Final status:"
git status

Warn "NEXT STEPS:"
Write-Host "1) Review the changes above." -ForegroundColor Yellow
Write-Host "2) Commit:" -ForegroundColor Yellow
Write-Host "   git add . && git commit -m `"Final tidy: archive distractions, remove junk folders`"" -ForegroundColor Yellow
Write-Host "3) Push branch:" -ForegroundColor Yellow
Write-Host "   git push --set-upstream origin $branchName" -ForegroundColor Yellow