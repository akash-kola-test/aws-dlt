Import-Module -Name ./UploadObjectToS3.psm1 -Function Upload-FileToS3

$BucketName = "loadtesting-dltbucket"
$TaurusFile = "123-us-east-1.json"
$JmeterFile = "123.jmx"

$TaurusS3Path = "s3://$BucketName/test-scenarios/$TaurusFile"
UploadFileToS3 -filePath "./$TaurusFile" -s3Path $TaurusS3Path

$JmeterS3Path = "s3://$BucketName/public/test-scenarios/jmeter/$JmeterFile"
UploadFileToS3 -filePath "./$JmeterFile" -s3Path $JmeterS3Path
