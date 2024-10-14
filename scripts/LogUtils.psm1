function WriteLog {
    param (
        [string]$Message,
        [string]$LogLevel = "INFO",
        [string]$ForegroundColor = "White"
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "$timestamp [$LogLevel] $Message"
    Write-Host $logEntry -ForegroundColor $ForegroundColor
}
