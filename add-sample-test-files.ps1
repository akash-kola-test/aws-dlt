$BucketName = "loadtesting-dltbucket"
$TaurusFile = "123-us-east-1.json"
$JmeterFile = "123.jmx"

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

$TaurusS3Path = "s3://$BucketName/test-scenarios/$TaurusFile"
Upload-FileToS3 -filePath "./$TaurusFile" -s3Path $TaurusS3Path

$JmeterS3Path = "s3://$BucketName/public/test-scenarios/jmeter/$JmeterFile"
Upload-FileToS3 -filePath "./$JmeterFile" -s3Path $JmeterS3Path
