$ErrorActionPreference = "Stop"

function Log {
    param ([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "$timestamp - $message"
}

try {
    Log "Building Docker image 'aws-dlt/taurus-tester'..."
    docker build -t aws-dlt/taurus-tester .
    Log "Docker image 'aws-dlt/taurus-tester' built successfully."

    Log "Authenticating Docker with AWS ECR Public..."
    aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/x2t0y6c0
    Log "Successfully authenticated with AWS ECR Public."

    Log "Tagging Docker image..."
    docker tag aws-dlt/taurus-tester:latest public.ecr.aws/x2t0y6c0/aws-dlt/taurus-tester:latest  *> $null
    Log "Image tagged successfully."

    Log "Pushing Docker image to AWS ECR Public..."
    docker push public.ecr.aws/x2t0y6c0/aws-dlt/taurus-tester:latest  *> $null
    Log "Image pushed successfully to AWS ECR Public."

} catch {
    Log "An error occurred: $_"
} finally {
    Log "Script execution completed."
}
