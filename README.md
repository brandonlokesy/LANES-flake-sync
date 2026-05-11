# LANES-flake-sync
Powershell scripts for flake indexing and syncing images between folders.

The following script takes the indexed names given to microscope images of 2D material flakes and builds a CSV file which allows the user to track the flake. The CSV file has the following columns:

| flake_id | slide_number | flake_number | color | thickness (nm) | layer | position | quality | est_area (um2) | used | used_in | notes |
|----------|--------------|--------------|-------|----------------|-------|----------|---------|----------------|------|----------|-------|


The fields `flake_id`, `slide_number`, `flake_number`, `color` (only for hBN), and `position` are generated from the indexing script.

## File naming requirements

### Folder structure

The following script runs on the following structure. Microscope images of flakes must be named in the following way:

```
+---YYYYMMDD_MATERIAL-NAME
|   +---AFM
|   +---all-flakes
|   |   +---S1
|   |   +---S2
|   |   +---S3
|   |   \---S4
|   +---best-flakes
|   \---selected
```

I believe something like YYYY-MM-DD should also work because the script uses the under score `_` to separate the date and the material name. The `S1`, `S2` etc. are chip numbers. You can omit these folders and store all flakes under `all-flakes`. The script will still work.

### Image naming convention

hBN flakes are labelled in the following way: `SXX_Y 00Z`, where `X` is the chip/sample number, `Y` is the flake number, and `Z` is the image number. The number `Z` does not matter to this script. Additionally, you may choose to include a microscope image like `S21_10_paleblue 0049`. The script will index the colour `paleblue` and write it to the CSV row.

> [!NOTE] 
> Due to my mistakes (taking two chips of the same number), the script will be able to distinguish two different chips of the same number if you add an additional identifier to it. For example, if you have two chip number `30`s, you can distinguish them with `30R` and `30L`, which refer to right and left, respectively. This is particularly useful on the 3x3 chip holder.

TMDC flakes are labelled in a similar way to hBN flakes, with the following format: `SXX_Y 00Z`. I also choose to take one more image which indicates the location of the TMDC with the following filename: `S2_1_BottomMiddle 0011`. The script indexes `BottomMiddle` to the `position` column in the CSV row.

I use the following location convention:

```
Flake position naming convention

Top-Left    | Top-Center    | Top-Right
-----------------------------------------
Middle-Left | Middle-Center | Middle-Right
-----------------------------------------
Bottom-Left | Bottom-Center | Bottom-Right
```

But you can abbreviate this to T,L,C,R,B, etc..

# Flake Index CLI Setup (Windows + Anaconda + PowerShell)

This guide sets up a convenient command:

```powershell
flake-index 20260304_WSe2
```

which runs

```
python generate_flake_index.py <material_folder>
```

## Step 1: Mount the Network Drive (X:)

The data and script lives on `\\lanesnas.epfl.ch\lanes`.

```powershell
net use X: \\lanesnas.epfl.ch\lanes /persistent:yes
```

and verify that the drive is mounted

```powershell
X:
dir
```

Check that the folder you want to deposit the images into exists. You can replace `\Brandon\02_Areas\` with `\to\your\own\path`.

## Step 2: Locate your paths

The script lives in

```powershell
X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py
```

and the data root is 

```powershell
X:\Brandon\02_Areas\materials-exfoliation
```

## Step 3: Fix Power Shell Execution Policy

PowerShell blocks scripts by default.

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Press `Y` to confirm.

## Step 4: Enable Conda in PowerShell

Open Anaconda Prompt

```anaconda prompt
conda init powershell
```

Restart Powershell

Test:

```powershell
conda activate base
```

you should see

```
(base) PS ...
```


## Step 5: Create your PowerShell profile

Create profile (if not already created)

```powershell
New-Item -ItemType Directory -Force -Path (Split-Path $PROFILE)  
New-Item -ItemType File -Force -Path $PROFILE
```

Open the profile 

```powershell
notepad $PROFILE
```

## Step 6: Add your flake-index command

Paste this into your profile. Remember to change the file paths.

```powershell
# --- CONFIG ---
$FlakeLibrary    = "X:\Brandon\02_Areas\materials-exfoliation"
$FlakeScript     = "X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py"
$FlakeSyncScript = "X:\Brandon\02_Areas\fabrication\tools\flake_sync.py"

# --- Helper: get latest batch folder ---
function Get-LatestBatch {
    Get-ChildItem -Path $FlakeLibrary -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1 -ExpandProperty Name
}

# --- Tab completion (shared between both commands) ---
$FlakeBatchCompleter = {
    param($commandName, $parameterName, $wordToComplete)
    Get-ChildItem -Path $FlakeLibrary -Directory |
        Where-Object { $_.Name -like "$wordToComplete*" } |
        ForEach-Object {
            [System.Management.Automation.CompletionResult]::new(
                $_.Name, $_.Name, 'ParameterValue', $_.Name
            )
        }
}

# --- Commands ---
function flake-index {
    param([string]$BatchFolder)
    if (-not $BatchFolder) {
        $BatchFolder = Get-LatestBatch
        Write-Host "No batch specified. Using latest: $BatchFolder"
    }
    $fullPath = Join-Path $FlakeLibrary $BatchFolder
    if (-not (Test-Path $fullPath)) {
        Write-Error "Batch folder not found: $fullPath"
        return
    }
    python "$FlakeScript" "$fullPath"
}

function flake-sync {
    param([string]$BatchFolder)
    if (-not $BatchFolder) {
        $BatchFolder = Get-LatestBatch
        Write-Host "No batch specified. Using latest: $BatchFolder"
    }
    $fullPath = Join-Path $FlakeLibrary $BatchFolder
    if (-not (Test-Path $fullPath)) {
        Write-Error "Batch folder not found: $fullPath"
        return
    }
    python "$FlakeSyncScript" "$fullPath"
}

Register-ArgumentCompleter -CommandName flake-index -ParameterName BatchFolder -ScriptBlock $FlakeBatchCompleter
Register-ArgumentCompleter -CommandName flake-sync  -ParameterName BatchFolder -ScriptBlock $FlakeBatchCompleter
```

Save and close. Reload profile

```powershell
. $PROFILE
```

## Step 8: Test everything

```powershell
flake-index 20260304_WSe2
```

Expected output:
```powershell
Material folder : ...  
Scanning        : ...\all-flakes  
CSV output      : ...``
```

---

## Troubleshooting

### "conda not recognized"

- Run `conda init powershell` from Anaconda Prompt
- Restart PowerShell

---

### "running scripts is disabled"

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
---

### "file not found (generate_flake_index.py)"

Check path:

```powershell
Test-Path "X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py"
```
---

### ❌ X: drive not found

Remount:

```powershell
net use X: \\lanesnas.epfl.ch\lanes /persistent:yes
```

---

## Step 10: Final workflow

```powershell
conda activate base  
flake-index 20260304_WSe2
```

Note that the script accepts autocomplete endings. 

# Flake Sync

With the CSV file now generated, you can edit the table to indicate if a flake has been used or the quality of the flake. By default, the `quality` entry of the CSV file is empty. Filling this in with a non-zero value indicates that the flake is of interest to you. You can also indicate if the flake has been used and in what sample. 

By running 

```powershell
flake-sync 20260404_WSe2
```

the `flake_sync.py` program looks for flakes with non-zero quality assigned to them and **copies** them into the `best-flakes`. It also looks for non-zero entries in the `used` CSV column and moves these flakes into the `selected` folder.

I am working on removing used flakes from the `best-flakes` column so it's easier to look for flakes in the future.
