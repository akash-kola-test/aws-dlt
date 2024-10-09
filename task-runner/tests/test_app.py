from unittest.mock import patch, Mock

import pytest
from task_runner_function.app import NameParameterNeededException, SubnetIDsNeededException, lambda_handler

@patch("boto3.client")
def test_lambda_returns_if_tasks_are_running(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value

    result = lambda_handler({"is_running": True}, {})

    assert result["is_running"] is True
    mock_ecs.assert_not_called()


@patch("boto3.client")
def test_lambda_starts_tasks(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = "container_name"
    subnets = ["some subnet 1"]

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': s3_bucket
                    },
                    {
                        'name': 'TEST_ID',
                        'value': test_id
                    },
                    {
                        'name': 'PREFIX',
                        'value': prefix
                    },
                    {
                        'name': 'AWS_REGION',
                        'value': region
                    },
                ],
            },
        ]
    }

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "container_name": container_name,
        "subnets": subnets
    }

    result = lambda_handler(event, {})

    assert result["is_running"] is True
    
    assert_values = {
        "launchType": 'FARGATE',
        "group": test_id,
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "assignPublicIp": "ENABLED"
            }
        }
    }
    run_task.assert_called_once_with(**assert_values)


@patch("boto3.client")
def test_lambda_starts_task_fail_without_container_name(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket
    }

    with pytest.raises(NameParameterNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
def test_lambda_starts_task_fail_with_empty_container_name(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = ""

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "container_name": container_name
    }

    with pytest.raises(NameParameterNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
def test_lambda_starts_task_fail_without_subnets(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = "somename"

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "container_name": container_name
    }

    with pytest.raises(SubnetIDsNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
def test_lambda_starts_task_fail_with_empty_subnets(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = "somename"
    subnets = []

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "subnets": subnets,
        "container_name": container_name
    }

    with pytest.raises(SubnetIDsNeededException):
        lambda_handler(event, {})

@patch("boto3.client")
def test_lambda_starts_with_fargate_launch_type(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = "container_name"
    subnets = ["some subnet 1"]

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': s3_bucket
                    },
                    {
                        'name': 'TEST_ID',
                        'value': test_id
                    },
                    {
                        'name': 'PREFIX',
                        'value': prefix
                    },
                    {
                        'name': 'AWS_REGION',
                        'value': region
                    },
                ],
            },
        ]
    }

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "container_name": container_name,
        "subnets": subnets
    }

    result = lambda_handler(event, {})

    assert result["is_running"] is True
    
    assert_values = {
        "group": test_id,
        "launchType": 'FARGATE',
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "assignPublicIp": "ENABLED"
            }
        }
    }
    run_task.assert_called_once_with(**assert_values)


# for downloading the ecr image
@patch("boto3.client")
def test_lambda_starts_tasks_which_has_public_ip_enable(mock_boto_client):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    s3_bucket = "s3_bucket"
    prefix = "some_prefix"
    region = "some_region"
    container_name = "container_name"
    subnets = ["some subnet 1"]

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': s3_bucket
                    },
                    {
                        'name': 'TEST_ID',
                        'value': test_id
                    },
                    {
                        'name': 'PREFIX',
                        'value': prefix
                    },
                    {
                        'name': 'AWS_REGION',
                        'value': region
                    },
                ],
            },
        ]
    }

    event = {
        "is_running": False,
        "region": region,
        "task_count": task_count,
        "test_id": test_id,
        "cluster": cluster,
        "task_definition": task_definition,
        "prefix": prefix,
        "s3_bucket": s3_bucket,
        "container_name": container_name,
        "subnets": subnets
    }

    result = lambda_handler(event, {})

    assert result["is_running"] is True
    
    assert_values = {
        "group": test_id,
        "launchType": 'FARGATE',
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "assignPublicIp": "ENABLED"
            }
        }
    }
    run_task.assert_called_once_with(**assert_values)
