Import-Module -Name ./scripts/DeploySamLambdas.psm1 -Function UploadSamPackage
Import-Module -Name ./scripts/UploadObjectToS3.psm1 -Function UploadFileToS3
Import-Module -Name ./scripts/LogUtils.psm1 -Function WriteLog

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

WriteLog "Starting deployment of SAM Lambdas..."
WriteLog "Output Template File: $OutputTemplateFile"
WriteLog "S3 Bucket: $BucketName"
WriteLog "Started Processing Lambda folders..."

foreach ($LambdaFolder in $LambdaFolders.Keys) {
    try {
        WriteLog "Processing Lambda folder: $LambdaFolder"

        UploadSamPackage `
            -LambdaFolderPath $LambdaFolder `
            -BucketName $BucketName `
            -S3Prefix $S3Prefix `
            -OutputTemplateFile $OutputTemplateFile `
            -LambdaFunctionName $LambdaFolders[$LambdaFolder]

        WriteLog "Successfully processed Lambda: $LambdaFolder"
    } catch {
        WriteLog "Error while processing Lambda folder: $LambdaFolder - $_" "ERROR"
    }
}

WriteLog "Deployment of SAM Lambdas completed successfully."

try {
    WriteLog "Uploading state machine file: $StateMachineFilePath"

    UploadFileToS3 -FilePath $StateMachineFilePath -S3Path $StateMachineFileS3Path

    WriteLog "State machine file uploaded successfully." "Green"
} catch {
    WriteLog "Error while uploading state machine file: $_" "ERROR"
}
