# Mixto powershell
# Usage: some command | ./mixto.ps1 -MixtoEntryID some-id
[CmdletBinding()]
param (
    # Entry id 
    [Parameter()] [String] $MixtoEntryID = "",
    # Commit title. Defaults to Untitled
    [Parameter()] [String] $MixtoCommitTitle = "",
    [Parameter(ValueFromPipeline = $True, Mandatory = $True)] $MixtoOutput = ""
)
begin { $output = @() }
process { $output += $MixtoOutput }
end {
    # IMPORTANT Change this to the right host
    $MIXTO_HOST = "http://localhost:5000"
    # Hardcoded entry ID or pass via parameter
    $MIX_ENTRY_ID = ""
    
    if ($MIXTO_HOST -eq "") {
        Write-Output "Missing Mixto host"
        exit
    }
    if ($MIX_ENTRY_ID -eq "" -and $MixtoEntryID -eq "") {
        Write-Output "Missing Mixto entry ID"
        exit
    }
    elseif ($MixtoEntryID) {
        $MIX_ENTRY_ID = $MixtoEntryID
    }

    $SecureMixtoAPIKey = Read-Host -Prompt "Enter Mixto API key" -AsSecureString
    $MixtoAPIKey = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureMixtoAPIKey)
    $MixtoAPIKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($MixtoAPIKey)
    if ($MixtoAPIKey -eq "") {
        Write-Output "API key required"
        exit
    }

    $payload = @{
        "entry_id" = $MixtoEntryID;
        "title"    = $MixtoCommitTitle;
        "type"     = "stdout";
        "data"     = $output | Out-String;
    }
    $status = Invoke-WebRequest -Uri "$MIXTO_HOST/api/entry/$MixtoEntryID/commit" -UseBasicParsing -Method POST -Body ($payload | ConvertTo-Json) -ContentType "application/json" -Headers @{"x-api-key" = $MixtoAPIKey } | Select-Object -Expand StatusCode
    if ($status -eq 200) {
        Write-Output "Sent!"
    }
    else {
        Write-Output "Something went wrong.. ${status}"
    }
}