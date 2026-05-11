# LANES-flake-sync
Powershell scripts for flake indexing and syncing images between folders.

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

Check that `Brandon\02_Areas` exists.

## Step 2: Locate your paths

The script lives in

```
X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py
```

and the data root is 

```
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

Paste this into your profile:

```powershell
$FlakeLibrary = "X:\Brandon\02_Areas\materials-exfoliation"  
$FlakeScript  = "X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py"  
  
function flake-index {  
    param([string]$BatchFolder)  
  
    $path = Join-Path $FlakeLibrary $BatchFolder  
    python "$FlakeScript" "$path"  
}
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

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

---

### "file not found (generate_flake_index.py)"

Check path:

Test-Path "X:\Brandon\02_Areas\fabrication\tools\generate_flake_index.py"

---

### ❌ X: drive not found

Remount:

net use X: \\lanesnas.epfl.ch\lanes /persistent:yes

---

## Step 10: Final workflow

```powershell
conda activate base  
flake-index 20260304_WSe2
```
