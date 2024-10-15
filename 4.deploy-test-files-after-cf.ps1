Import-Module -Name ./scripts/UploadObjectToS3.psm1 -Function UploadFileToS3
Import-Module -Name ./scripts/LogUtils.psm1 -Function WriteLog

$BucketName = "loadtesting-dltbucket"
# $TaurusFile = "123-us-east-1.json"
$JmeterFile = "123.jmx"

# $TaurusS3Path = "s3://$BucketName/test-scenarios/$TaurusFile"
# try {
#     WriteLog "Starting upload of $TaurusFile to $TaurusS3Path."
#     UploadFileToS3 -FilePath "./sample-test-files/$TaurusFile" -S3Path $TaurusS3Path
#     WriteLog "Successfully uploaded $TaurusFile to $TaurusS3Path."
# } catch {
#     WriteLog "Error uploading $TaurusFile to $TaurusS3Path. Error: $_" "ERROR"
# }

$JmeterS3Path = "s3://$BucketName/public/test-scenarios/jmeter/$JmeterFile"
try {
    WriteLog "Starting upload of $JmeterFile to $JmeterS3Path."
    UploadFileToS3 -FilePath "./sample-test-files/$JmeterFile" -S3Path $JmeterS3Path
    WriteLog "Successfully uploaded $JmeterFile to $JmeterS3Path."
} catch {
    WriteLog "Error uploading $JmeterFile to $JmeterS3Path. Error: $_" "ERROR"
}
