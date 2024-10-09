function UploadFileToS3 {
    param (
        [string]$FilePath,
        [string]$S3Path
    )
    Write-Host "Starting upload of '$FilePath' to '$S3Path'..."
    aws s3 cp "$FilePath" "$S3Path" *> $null
}
