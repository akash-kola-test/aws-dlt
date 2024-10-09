Import-Module powershell-yaml

function UploadSamPackage {
    param (
        [string]$LambdaFolderPath,
        [string]$BucketName,
        [string]$S3Prefix,
        [string]$OutputTemplateFile,
        [string]$LambdaFunctionName
    )

    $originalPath = Get-Location
    cd $LambdaFolderPath
    
    try {
        Write-Host "Building and validating $LambdaFolderPath..."

        sam build *> $null
        sam validate *> $null

        Write-Host "Packaging $LambdaFolderPath..."
        
        sam package --output-template-file $OutputTemplateFile --s3-bucket $BucketName --s3-prefix $S3Prefix --no-resolve-s3 *> $null

        Write-Host "Reading and converting the YAML file..."
        
        $yamlContent = Get-Content -Path ./$OutputTemplateFile -Raw
        $yaml = ConvertFrom-Yaml $yamlContent

        $oldObjectKey = ($yaml.Resources.$LambdaFunctionName.Properties.CodeUri -split "/")[-1]
        
        Write-Host "Removing old object $LambdaFolderPath.zip, if present"

        if (aws s3 ls "s3://$BucketName/$S3Prefix/$LambdaFolderPath.zip" *> $null) {
            aws s3 rm "s3://$BucketName/$S3Prefix/$LambdaFolderPath.zip" *> $null
        }

        Write-Host "Copying old object: $oldObjectKey to new location..."

        aws s3 cp "s3://$BucketName/$S3Prefix/$oldObjectKey" "s3://$BucketName/$S3Prefix/$LambdaFolderPath.zip"
        aws s3 rm "s3://$BucketName/$S3Prefix/$oldObjectKey" *> $null

    } catch {
        throw $_
    } finally {
        cd $originalPath
    }
}
