import os
from task_status_checker_function.app import lambda_handler, list_tasks
from unittest.mock import Mock, patch, call


@patch("boto3.client")
def test_list_tasks(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    expected_task_arns = ["1", "2"]
    next_token = None
    mock_ecs.list_tasks.return_value = {
        "taskArns": expected_task_arns,
        "nextToken": next_token,
    }

    cluster = "cluster"
    tasks = list_tasks(mock_ecs, cluster)

    assert tasks["taskArns"] == expected_task_arns


@patch("boto3.client")
def test_list_tasks_with_next_token(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    list_tasks_mock: Mock = Mock()
    mock_ecs.list_tasks = list_tasks_mock

    expected_first_list_task_arns = ["1", "2"]
    expected_first_next_token = "some token"

    expected_second_list_task_arns = ["3", "4"]
    expected_second_next_token = None

    mock_ecs.list_tasks.side_effect = [
        {
            "taskArns": expected_first_list_task_arns,
            "nextToken": expected_first_next_token,
        },
        {
            "taskArns": expected_second_list_task_arns,
            "nextToken": expected_second_next_token,
        },
    ]

    cluster = "cluster"
    tasks = list_tasks(mock_ecs, cluster)
    next_tasks = list_tasks(mock_ecs, cluster, expected_first_next_token)

    assert tasks["taskArns"] == expected_first_list_task_arns
    assert tasks["nextToken"] == expected_first_next_token
    assert next_tasks["taskArns"] == expected_second_list_task_arns
    assert next_tasks["nextToken"] is expected_second_next_token

    list_tasks_mock.assert_has_calls(
        [
            call(cluster=cluster),
            call(cluster=cluster, nextToken=expected_first_next_token),
        ]
    )


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1"})
def test_lambda_handler(mock_boto_client):
    mock_ecs = mock_boto_client.return_value

    expected_task_arns = ["1", "2"]
    next_token = None
    expected_is_running = False

    mock_ecs.list_tasks.return_value = {
        "taskArns": expected_task_arns,
        "nextToken": next_token,
    }
    mock_ecs.describe_tasks.return_value = {"tasks": None}

    event = {"test_task_config": {"cluster": "some cluster"}}
    result = lambda_handler(event, {})

    assert result["isRunning"] is expected_is_running


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1"})
def test_lambda_handler_when_only_other_groups_running(mock_boto_client):
    expected_is_running = False

    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"]}
    mock_ecs.describe_tasks.return_value = {
        "tasks": [
            {"taskArn": "1", "group": "other_group"},
            {"taskArn": "2", "group": "other_group"},
        ]
    }

    event = {"test_task_config": {"cluster": "some cluster"}, "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["isRunning"] is expected_is_running


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1"})
def test_lambda_handler_when_test_group_running(mock_boto_client):
    expected_is_running = True

    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"], "nextToken": None}
    mock_ecs.describe_tasks.return_value = {
        "tasks": [
            {"taskArn": "1", "group": "123"},
            {"taskArn": "2", "group": "other_group"},
        ]
    }

    event = {"test_task_config": {"cluster": "cluster"}, "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["isRunning"] is expected_is_running


@patch("boto3.client")
@patch.dict(os.environ, {"TEST_AWS_REGION": "us-east-1"})
def test_describe_not_calls_with_empty_task_arns(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    list_tasks_mock: Mock = Mock()
    mock_ecs.list_tasks = list_tasks_mock

    expected_first_list_task_arns = []
    expected_first_next_token = "some token"

    expected_second_list_task_arns = []
    expected_second_next_token = None

    mock_ecs.list_tasks.side_effect = [
        {
            "taskArns": expected_first_list_task_arns,
            "nextToken": expected_first_next_token,
        },
        {
            "taskArns": expected_second_list_task_arns,
            "nextToken": expected_second_next_token,
        },
    ]

    event = {"test_task_config": {"cluster": "cluster"}, "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["isRunning"] is False
    mock_ecs.describe_tasks.assert_not_called()
