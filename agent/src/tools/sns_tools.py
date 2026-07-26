"""Custom SNS notification tool."""

import logging
import os

import boto3
from strands import tool

logger = logging.getLogger(__name__)


@tool
def send_job_alert(subject: str, message: str) -> str:
    """
    Send a job alert notification to the configured SNS topic.

    Args:
        subject: Short subject line for the notification
        message: Full notification body text

    Returns:
        str: Result of the publish attempt
    """
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "").strip()
    if not topic_arn:
        return "SNS notifications are not configured"

    sns = boto3.client("sns")
    # SNS rejects subjects over 100 characters
    sns.publish(TopicArn=topic_arn, Subject=subject[:100], Message=message)
    logger.info(f"Job alert published to {topic_arn}")
    return "Notification sent"
