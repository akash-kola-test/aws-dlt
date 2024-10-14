Import-Module -Name ./scripts/LogUtils.psm1 -Function WriteLog

try {
    WriteLog "Building Docker image 'aws-dlt/taurus-tester'..."
    docker build -t aws-dlt/taurus-tester -f taurus-tester-image\Dockerfile taurus-tester-image
    WriteLog "Docker image 'aws-dlt/taurus-tester' built successfully."

    WriteLog "Authenticating Docker with AWS ECR Public..."
    aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/x2t0y6c0
    WriteLog "Successfully authenticated with AWS ECR Public."

    WriteLog "Tagging Docker image..."
    docker tag aws-dlt/taurus-tester:latest public.ecr.aws/x2t0y6c0/aws-dlt/taurus-tester:latest  *> $null
    WriteLog "Image tagged successfully."

    WriteLog "Pushing Docker image to AWS ECR Public..."
    docker push public.ecr.aws/x2t0y6c0/aws-dlt/taurus-tester:latest  *> $null
    WriteLog "Image pushed successfully to AWS ECR Public."

} catch {
    WriteLog "An error occurred: $_" "ERROR"
} finally {
    WriteLog "Script execution completed."
}
