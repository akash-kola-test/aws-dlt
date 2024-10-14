Import-Module -Name ./scripts/DeploySamLambdas.psm1 -Function UploadSamPackage
Import-Module -Name ./scripts/UploadObjectToS3.psm1 -Function UploadFileToS3

function Write-Log {
    param (
        [string]$Message,
        [string]$LogLevel = "INFO",
        [string]$ForegroundColor = "White"
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "$timestamp [$LogLevel] $Message"
    Write-Host $logEntry -ForegroundColor $ForegroundColor
}

$Version = "1.0.0"
$S3Prefix = "aws-dlt/$Version"
$BucketName = "dlt-codes-akash"
$OutputTemplateFile = "packaged.yaml"
$StateMachineFilePath = ".\state-machine\taurus-test-task-handler.json"
$StateMachineFileS3Path = "s3://$BucketName/state-machine-files/taurus-test-task-handler.json"

$LambdaFolders = @{
    "task-status-checker" = "TaskStatusChecker"
    "task-runner"         = "TaskRunnerFunction"
}

Write-Log "Starting deployment of SAM Lambdas..."
Write-Log "Output Template File: $OutputTemplateFile"
Write-Log "S3 Bucket: $BucketName"
Write-Log "Started Processing Lambda folders..."

foreach ($LambdaFolder in $LambdaFolders.Keys) {
    try {
        Write-Log "Processing Lambda folder: $LambdaFolder"

        UploadSamPackage `
            -LambdaFolderPath $LambdaFolder `
            -BucketName $BucketName `
            -S3Prefix $S3Prefix `
            -OutputTemplateFile $OutputTemplateFile `
            -LambdaFunctionName $LambdaFolders[$LambdaFolder]

        Write-Log "Successfully processed Lambda: $LambdaFolder" "Green"
    } catch {
        Write-Log "Error while processing Lambda folder: $LambdaFolder - $_" "ERROR" "Red"
    }
}

Write-Log "Deployment of SAM Lambdas completed successfully." "Green"

try {
    Write-Log "Uploading state machine file: $StateMachineFilePath"

    UploadFileToS3 -FilePath $StateMachineFilePath -S3Path $StateMachineFileS3Path

    Write-Log "State machine file uploaded successfully." "Green"
} catch {
    Write-Log "Error while uploading state machine file: $_" "ERROR" "Red"
}
