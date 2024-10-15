import json
import os
from unittest.mock import patch, Mock
from datetime import datetime, timezone

import pytest
from api.app import (
    lambda_handler,
    get_test_duration_seconds,
    handle_tests,
    start_state_machine_execution,
    write_scenario_to_s3,
    merge_region_infra_config_details,
    upload_test_entry_to_db,
    InvalidParameterException,
    InvalidRegionException,
    TableNotFoundInEnvironmentException
)


TEST_SCENARIOS_BUCKET = "some bucket"
AWS_TESTS_REGION = "us-east-1"
TAURUS_STATE_MACHINE_ARN = "ARn"


@patch("api.app.handle_tests")
def test_lambda_handler_calls_handle_tests(mock_handle_tests):
    event = {"resource": "/test", "httpMethod": "POST", "test_id": "123"}
    lambda_handler(event, None)

    mock_handle_tests.assert_called_once_with(event)


@patch("api.app.handle_tests")
def test_lambda_handler_with_other_resource(mock_handle_tests: Mock):
    event = {"resource": "/other", "httpMethod": "GET"}
    lambda_handler(event, None)

    mock_handle_tests.assert_not_called()


def test_handle_tests_invalid_region():
    event = {
        "httpMethod": "POST",
        "test_id": "123",
        "test_task_config": {"concurrency": 5, "task_count": 10},
    }

    with patch.dict(os.environ, {"AWS_TESTS_REGION": "invalid-region"}):
        with pytest.raises(InvalidRegionException):
            handle_tests(event)


@patch("api.app.boto3.client")
@patch("api.app.datetime")
@patch.dict(os.environ, {"TAURUS_STATE_MACHINE_ARN": "ARN"})
def test_start_state_machine_execution(mock_datetime, mock_boto3_client):
    mock_now = datetime(2023, 10, 12, 15, 30, 45, tzinfo=timezone.utc)
    mock_datetime.now.return_value = mock_now

    sfn = mock_boto3_client.return_value
    step_function_params = {
        "test_task_config": {"concurrency": 5},
        "test_id": "123",
        "duration": 600,
    }

    start_state_machine_execution(sfn, step_function_params)

    expected_prefix = "".join(reversed(mock_now.isoformat().replace("Z", "")))

    sfn.start_execution.assert_called_once_with(
        stateMachineArn=os.environ["TAURUS_STATE_MACHINE_ARN"],
        input=json.dumps({**step_function_params, "prefix": expected_prefix}),
    )


@patch("api.app.boto3.client")
def test_write_scenario_to_s3(mock_boto3_client):
    s3 = mock_boto3_client.return_value
    test_scenario = {"execution": [{"hold-for": "10m"}]}
    test_task_config = {"concurrency": 5, "task_count": 10}
    test_id = "123"

    with patch.dict(
        os.environ,
        {"TEST_SCENARIOS_BUCKET": "test_bucket", "AWS_TESTS_REGION": "us-east-1"},
    ):
        write_scenario_to_s3(s3, test_scenario, test_task_config, test_id)

        s3.put_object.assert_called_once_with(
            Body=json.dumps(
                {
                    "execution": [
                        {
                            "hold-for": "10m",
                            "task_count": 10,
                            "concurrency": 5,
                        }
                    ]
                }
            ).encode(),
            Bucket="test_bucket",
            Key="test-scenarios/123-us-east-1.json",
        )


@patch("api.app.boto3.client")
def test_merge_region_infra_config_details(mock_boto3_client):
    mock_ddb_client = mock_boto3_client.return_value
    mock_ddb_client.get_item.return_value = {
        "Item": {
            "subnet": {"S": "subnet-123"},
            "cluster": {"S": "cluster-abc"},
            "task_definition": {"S": "task-def-xyz"},
            "task_container": {"S": "container-789"},
        }
    }

    test_task_config = {}
    merge_region_infra_config_details(mock_ddb_client, "us-east-1", test_task_config)

    assert test_task_config == {
        "subnet": "subnet-123",
        "cluster": "cluster-abc",
        "task_definition": "task-def-xyz",
        "task_container": "container-789",
    }


@patch("api.app.start_state_machine_execution")
@patch("api.app.boto3.client")
def test_handle_tests_valid_post(mock_boto3_client, mock_start_state_machine_execution):
    event = {
        "httpMethod": "POST",
        "test_id": "123",
        "test_task_config": {"concurrency": 5, "task_count": 10},
        "test_scenario": {
            "execution": [
                {
                    "hold-for": "10m",
                    "scenario": "test_name",
                    "ramp-up": "2s",
                }
            ],
            "scenarios": {
                "test_name": {
                    "script": "123.jmx"
                }
            }
        },
        "test_description": "some_description",
        "test_name": "test_name"
    }

    mock_ddb_client = mock_boto3_client.return_value
    mock_ddb_client.get_item.return_value = {
        "Item": {
            "subnet": {"S": "subnet id"},
            "cluster": {"S": "cluster name"},
            "task_definition": {"S": "task definition"},
            "task_container": {"S": "task container"},
        }
    }

    mock_sfn_client = mock_boto3_client.return_value

    with patch.dict(os.environ, {"TESTS_TABLE": "SOME TESTS TABLE"}):
        handle_tests(event)

    mock_boto3_client.assert_any_call("dynamodb", region_name="us-east-1")
    mock_boto3_client.assert_any_call("s3", region_name="us-east-1")
    mock_start_state_machine_execution.assert_called_once_with(
        mock_sfn_client,
        {
            "test_task_config": {
                "concurrency": 5,
                "task_count": 10,
                "subnet": "subnet id",
                "cluster": "cluster name",
                "task_definition": "task definition",
                "task_container": "task container",
            },
            "test_id": "123",
            "duration": 600,
        },
    )


@patch("api.app.upload_test_entry_to_db")
@patch("api.app.boto3.client")
def test_create_test_uploads_test_information_to_db(
    mock_boto3_client, mock_upload_test_entry_to_db: Mock
):
    event = {
        "httpMethod": "POST",
        "test_id": "123",
        "test_task_config": {
            "concurrency": 5,
            "task_count": 10,
        },
        "test_scenario": {
            "execution": [
                {
                    "hold-for": "10m",
                    "scenario": "test_name",
                    "ramp-up": "2s",
                }
            ],
            "scenarios": {
                "test_name": {
                    "script": "123.jmx"
                }
            }
        },
        "test_description": "some_description",
        "test_name": "test_name"
    }

    mock_ddb_client = mock_boto3_client.return_value
    mock_ddb_client.get_item.return_value = {
        "Item": {
            "subnet": {"S": "subnet id"},
            "cluster": {"S": "cluster name"},
            "task_definition": {"S": "task definition"},
            "task_container": {"S": "task container"},
        }
    }

    handle_tests(event)

    expected_test_scenario = {
        "execution": [
            {
                "hold-for": "10m",
                "scenario": "test_name",
                "ramp-up": "2s",
                "concurrency": 5,
                "task_count": 10,
            }
        ],
        "scenarios": {
            "test_name": {
                "script": "123.jmx",
                "variables": {}
            }
        }
    }
    expected_test_scenario["reporting"] = [
        {
            "module": "final-stats",
            "summary": True,
            "percentiles": True,
            "summary-labels": True,
            "test-duration": True,
            "dump-xml": "/tmp/artifacts/results.xml",
        },
    ]

    expected_task_test_config = {
        "concurrency": 5,
        "task_count": 10,
        "subnet": "subnet id",
        "cluster": "cluster name",
        "task_definition": "task definition",
        "task_container": "task container",
    }

    mock_upload_test_entry_to_db.assert_called_once_with(
        mock_ddb_client,
        "123",
        "some_description",
        expected_test_scenario,
        expected_task_test_config,
    )


@patch("api.app.boto3.client")
def test_upload_test_entry_to_db_success(mock_boto3_client):
    mock_dynamodb = mock_boto3_client.return_value

    test_id = "test123"
    test_description = "Test Description"
    test_scenario = {
        "execution": [{"scenario": "scenario1", "hold-for": "10m", "ramp-up": "5m"}]
    }
    test_task_config = {"task_count": "10", "concurrency": "5"}

    with patch.dict(os.environ, {"TESTS_TABLE": "TESTS_TABLE"}):
        upload_test_entry_to_db(
            mock_dynamodb, test_id, test_description, test_scenario, test_task_config
        )

    mock_dynamodb.put_item.assert_called_once_with(
        TableName="TESTS_TABLE",
        Item={
            "test_id": {"S": "test123"},
            "task_count": {"N": "10"},
            "concurrency": {"N": "5"},
            "test_name": {"S": "scenario1"},
            "test_description": {"S": "Test Description"},
            "hold-for": {"S": "10m"},
            "ramp-up": {"S": "5m"},
            "running": {"BOOL": True}
        },
    )


@patch("api.app.boto3.client")
def test_upload_test_entry_to_db_missing_env_variable(mock_boto3_client):
    mock_dynamodb = mock_boto3_client.return_value

    test_id = "test123"
    test_description = "Test Description"
    test_scenario = {
        "execution": [{"scenario": "scenario1", "hold-for": "10m", "ramp-up": "5m"}]
    }
    test_task_config = {"task_count": "10", "concurrency": "5"}

    # Environment variable `TESTS_TABLE` is not set
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(TableNotFoundInEnvironmentException):
            upload_test_entry_to_db(
                mock_dynamodb, test_id, test_description, test_scenario, test_task_config
            )


@patch("api.app.boto3.client")
def test_upload_test_entry_to_db_missing_task_count(mock_boto3_client):
    # Mocking DynamoDB client
    mock_dynamodb = mock_boto3_client.return_value

    test_id = "test123"
    test_description = "Test Description"
    test_scenario = {
        "execution": [{"scenario": "scenario1", "hold-for": "10m", "ramp-up": "5m"}]
    }
    # Missing "task_count" in `test_task_config`
    test_task_config = {"concurrency": "5"}

    with patch.dict(os.environ, {"TESTS_TABLE": "TESTS_TABLE"}):

        # Expect KeyError due to missing `task_count`
        with pytest.raises(KeyError):
            upload_test_entry_to_db(
                mock_dynamodb, test_id, test_description, test_scenario, test_task_config
            )


@patch("api.app.boto3.client")
def test_upload_test_entry_to_db_missing_concurrency(mock_boto3_client):
    # Mocking DynamoDB client
    mock_dynamodb = mock_boto3_client.return_value

    test_id = "test123"
    test_description = "Test Description"
    test_scenario = {
        "execution": [{"scenario": "scenario1", "hold-for": "10m", "ramp-up": "5m"}]
    }
    # Missing "concurrency" in `test_task_config`
    test_task_config = {"task_count": "10"}

    with patch.dict(os.environ, {"TESTS_TABLE": "TESTS_TABLE"}):

        # Expect KeyError due to missing `concurrency`
        with pytest.raises(KeyError):
            upload_test_entry_to_db(
                mock_dynamodb, test_id, test_description, test_scenario, test_task_config
            )


def test_get_test_duration_seconds_function_with_minutes():
    hold_for = "2m"
    seconds = get_test_duration_seconds(hold_for)
    assert seconds == 120


def test_get_test_duration_seconds_function_with_seconds():
    hold_for = "2s"
    seconds = get_test_duration_seconds(hold_for)
    assert seconds == 2


def test_get_test_duration_seconds_function_with_more_matches():
    hold_for = "2ss"
    with pytest.raises(InvalidParameterException):
        get_test_duration_seconds(hold_for)


def test_get_test_duration_seconds_function_with_some_unknown_unit():
    hold_for = "2y"

    with pytest.raises(InvalidParameterException):
        get_test_duration_seconds(hold_for)


def test_get_test_duration_seconds_function_with_some_unknown_number():
    hold_for = "yy"

    with pytest.raises(InvalidParameterException):
        get_test_duration_seconds(hold_for)


@patch("api.app.boto3.client")
def test_write_scenario_to_s3_takes_default_region(mock_boto3_client):
    s3 = mock_boto3_client.return_value
    test_scenario = {"execution": [{"hold-for": "10m"}]}
    test_task_config = {"concurrency": 5, "task_count": 10}
    test_id = "123"

    with patch.dict(
        os.environ,
        {"TEST_SCENARIOS_BUCKET": "test_bucket"},
    ):
        write_scenario_to_s3(s3, test_scenario, test_task_config, test_id)

        s3.put_object.assert_called_once_with(
            Body=json.dumps(
                {
                    "execution": [
                        {
                            "hold-for": "10m",
                            "task_count": 10,
                            "concurrency": 5,
                        }
                    ]
                }
            ).encode(),
            Bucket="test_bucket",
            Key="test-scenarios/123-us-east-1.json",
        )
