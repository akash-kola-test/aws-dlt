import os
from unittest.mock import patch, Mock

import pytest
from task_runner_function.app import NameParameterNeededException, SubnetIDNeededException, lambda_handler

@patch("boto3.client")
def test_lambda_returns_if_tasks_are_running(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value

    result = lambda_handler({"isRunning": True}, {})

    assert result["isRunning"] is True
    mock_ecs.assert_not_called()


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_tasks(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    region = "us-east-1"
    SCENARIOS_BUCKET = "some bucket"

    test_id = "123"
    prefix = "some_prefix"

    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    container_name = "container_name"
    subnet = "some subnet 1"

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name,
        "subnet": subnet
    }

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': SCENARIOS_BUCKET
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
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    result = lambda_handler(event, {})

    assert result["isRunning"] is True
    
    assert_values = {
        "launchType": 'FARGATE',
        "group": test_id,
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": [subnet],
                "assignPublicIp": "ENABLED"
            }
        }
    }
    run_task.assert_called_once_with(**assert_values)


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_task_fail_without_container_name(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    prefix = "some_prefix"

    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
    }

    event = {
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    with pytest.raises(NameParameterNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_task_fail_with_empty_container_name(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    prefix = "some_prefix"

    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    container_name = ""

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name
    }

    event = {
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    with pytest.raises(NameParameterNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_task_fail_without_subnet(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    prefix = "some_prefix"
    
    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    container_name = "somename"

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name
    }

    event = {
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    with pytest.raises(SubnetIDNeededException):
        lambda_handler(event, {})


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_task_fail_with_empty_subnets(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    test_id = "123"
    prefix = "some_prefix"

    task_count = 2
    task_definition = "some_task_definition"
    cluster = "some_cluster"
    container_name = "somename"
    subnet = ""

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name,
        "subnet": subnet
    }

    event = {
        "isRunning": False,
        "prefix": prefix,
        "test_id": test_id,
        "test_task_config": test_task_config
    }

    with pytest.raises(SubnetIDNeededException):
        lambda_handler(event, {})

@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_with_fargate_launch_type(mock_boto_client: Mock):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    region = "us-east-1"
    SCENARIOS_BUCKET = "some bucket"

    test_id = "123"
    prefix = "some_prefix"

    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    container_name = "container_name"
    subnet = "some subnet 1"

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': SCENARIOS_BUCKET
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

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name,
        "subnet": subnet
    }

    event = {
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    result = lambda_handler(event, {})

    assert result["isRunning"] is True
    
    assert_values = {
        "group": test_id,
        "launchType": 'FARGATE',
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": [subnet],
                "assignPublicIp": "ENABLED"
            }
        }
    }
    run_task.assert_called_once_with(**assert_values)


# for downloading the ecr image
@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1", "SCENARIOS_BUCKET": "some bucket"})
def test_lambda_starts_tasks_which_has_public_ip_enable(mock_boto_client):
    mock_ecs: Mock = mock_boto_client.return_value
    run_task = Mock()
    run_task.return_value = {}
    mock_ecs.run_task = run_task

    region = "us-east-1"
    SCENARIOS_BUCKET = "some bucket"

    test_id = "123"
    prefix = "some_prefix"

    cluster = "some_cluster"
    task_count = 2
    task_definition = "some_task_definition"
    container_name = "container_name"
    subnet = "some subnet 1"

    overrides = {
        "containerOverrides": [
            {
                "name": container_name,
                'environment': [
                    {
                        'name': 'S3_BUCKET',
                        'value': SCENARIOS_BUCKET
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

    test_task_config = {
        "cluster": cluster,
        "task_count": task_count,
        "task_definition": task_definition,
        "container_name": container_name,
        "subnet": subnet
    }

    event = {
        "isRunning": False,
        "test_id": test_id,
        "prefix": prefix,
        "test_task_config": test_task_config
    }

    result = lambda_handler(event, {})

    assert result["isRunning"] is True
    
    assert_values = {
        "group": test_id,
        "launchType": 'FARGATE',
        "overrides": overrides,
        "cluster": cluster,
        "count": task_count,
        "taskDefinition": task_definition,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": [subnet],
                "assignPublicIp": "ENABLED"
            }
        }
    }

    run_task.assert_called_once_with(**assert_values)
