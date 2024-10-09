$BucketName = "dlt-codes-akash"
$StateMachineFile = "taurus-test-task-handler.json"

function Upload-FileToS3 {
    param (
        [string]$filePath,
        [string]$s3Path
    )

    try {
        Write-Host "Starting upload of '$filePath' to '$s3Path'..."
        
        aws s3 cp "$filePath" "$s3Path" *> $null

        Write-Host "Upload of '$filePath' to '$s3Path' completed successfully." -ForegroundColor Green
    } catch {
        Write-Host "Error uploading '$filePath': $($_.Exception.Message)" -ForegroundColor Red
    }
}

$StateMachineFileS3Path = "s3://$BucketName/state-machine-files/$StateMachineFile"
Upload-FileToS3 -filePath "./state-machine/$StateMachineFile" -s3Path $StateMachineFileS3Path
