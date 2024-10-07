from task_status_checker_function.app import lambda_handler, get_tasks_arns
from unittest.mock import patch


@patch("boto3.client")
def test_get_tasks_arns(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"]}

    cluster = "cluster"
    taskArns = get_tasks_arns(mock_ecs, cluster)

    assert taskArns == ["1", "2"]


@patch("boto3.client")
def test_lambda_handler(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"]}
    mock_ecs.describe_tasks.return_value = {"tasks": None}

    event = {"region": "useast1", "cluster": "cluster"}
    result = lambda_handler(event, {})

    assert result["is_running"] is False

@patch("boto3.client")
def test_lambda_handler_others_running(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"]}
    mock_ecs.describe_tasks.return_value = {"tasks": [{"group": "other_group"}, {"group": "other_group"}]}

    event = {"region": "useast1", "cluster": "cluster", "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["is_running"] is False

@patch("boto3.client")
def test_lambda_handler_running(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": ["1", "2"]}
    mock_ecs.describe_tasks.return_value = {"tasks": [{"group": "123"}, {"group": "other_group"}]}

    event = {"region": "useast1", "cluster": "cluster", "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["is_running"] is True

@patch("boto3.client")
def test_tasks_are_empty_describe_not_called(mock_boto_client):
    mock_ecs = mock_boto_client.return_value
    mock_ecs.list_tasks.return_value = {"taskArns": []}

    event = {"region": "useast1", "cluster": "cluster", "test_id": "123"}
    result = lambda_handler(event, {})

    assert result["is_running"] is False
    mock_ecs.describe_tasks.assert_not_called()
