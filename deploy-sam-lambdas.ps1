Import-Module powershell-yaml

$Version = "1.0.0"
$S3Prefix = "aws-dlt/$Version"
$BucketName = "dlt-codes-akash"
$OutputTemplateFile = "packaged.yaml"

$LambdaFolders = @{
    "task-status-checker" = "TaskStatusChecker"
    "task-runner" = "TaskRunnerFunction"
}

$originalPath = Get-Location

Write-Host "Script started. Version: $Version"
Write-Host "Output Template File: $OutputTemplateFile"
Write-Host "S3 Bucket: $BucketName"
Write-Host "Processing Lambda folders..."

foreach ($LambdaFolder in $LambdaFolders.Keys) {
    cd $LambdaFolder
    
    try {
        Write-Host "Building and validating $LambdaFolder..."

        sam build *> $null
        sam validate *> $null

        Write-Host "Packaging $LambdaFolder..."
        
        sam package --output-template-file $OutputTemplateFile --s3-bucket $BucketName --s3-prefix $S3Prefix --no-resolve-s3 *> $null

        Write-Host "Reading and converting the YAML file..."
        
        $yamlContent = Get-Content -Path ./$OutputTemplateFile -Raw
        $yaml = ConvertFrom-Yaml $yamlContent
        
        $oldObjectKey = ($yaml.Resources.$($LambdaFolders[$LambdaFolder]).Properties.CodeUri -split "/")[-1]
        
        Write-Host "Removing old object $LambdaFolder.zip, if presents"

        aws s3 rm "s3://$BucketName/$S3Prefix/$LambdaFolder.zip" *> $null

        Write-Host "Copying old object: $oldObjectKey to new location..."

        aws s3 cp "s3://$BucketName/$S3Prefix/$oldObjectKey" "s3://$BucketName/$S3Prefix/$LambdaFolder.zip"
        aws s3 rm "s3://$BucketName/$S3Prefix/$oldObjectKey" *> $null

        Write-Host "Processed $LambdaFolder successfully."
    } catch {
        Write-Host "Error processing $LambdaFolder : ${_}" -ForegroundColor Red
    } finally {
        cd $originalPath
    }
}

Write-Host "Script completed."
