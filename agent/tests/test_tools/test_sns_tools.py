"""Tests for the SNS notification tool."""

import os
from unittest.mock import patch

from src.tools.sns_tools import send_job_alert


def test_send_job_alert_publishes_to_topic():
    """Publishes subject and message to the topic from SNS_TOPIC_ARN."""
    topic_arn = "arn:aws:sns:us-west-2:123456789012:test-topic"
    with (
        patch.dict(os.environ, {"SNS_TOPIC_ARN": topic_arn}),
        patch("src.tools.sns_tools.boto3") as mock_boto3,
    ):
        result = send_job_alert(subject="Job Alert: Acme is hiring!", message="details")

    assert result == "Notification sent"
    mock_boto3.client.return_value.publish.assert_called_once_with(
        TopicArn=topic_arn, Subject="Job Alert: Acme is hiring!", Message="details"
    )


def test_send_job_alert_without_topic_is_noop():
    """Returns without publishing when SNS_TOPIC_ARN is not set."""
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("src.tools.sns_tools.boto3") as mock_boto3,
    ):
        result = send_job_alert(subject="s", message="m")

    assert result == "SNS notifications are not configured"
    mock_boto3.client.assert_not_called()
