function Write-Log {
    param (
        [string]$Message,
        [string]$LogLevel = "INFO"
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "$timestamp [$LogLevel] $Message"
    Write-Host $logEntry
}

try {
    Write-Log "Starting deployment of SAM Lambdas..."

    & ./scripts/deploy-sam-lambdas.ps1

    Write-Log "Deployment of SAM Lambdas completed successfully."

    Write-Log "Uploading state machine files..."

    & ./scripts/upload-state-file.ps1

    Write-Log "State machine files uploaded successfully."

} catch {
    Write-Log "An error occurred: $_" "ERROR"
    
    throw $_
} finally {
    Write-Log "Script execution finished."
}
# cf stack creation
# ./uplaod-sample-test-files.ps1