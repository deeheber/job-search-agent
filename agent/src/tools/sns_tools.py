"""Custom SNS notification tool."""

import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
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
    try:
        # SNS rejects subjects over 100 characters
        sns.publish(TopicArn=topic_arn, Subject=subject[:100], Message=message)
    # PEP 758 multi-exception catch; black strips the parentheses
    except BotoCoreError, ClientError:
        logger.error("Failed to publish job alert", exc_info=True)
        return "Notification failed"
    logger.info(f"Job alert published to {topic_arn}")
    return "Notification sent"


def send_failure_alert(company: str) -> None:
    """Alert when a background search fails; the async caller discards the result."""
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "").strip()
    if not topic_arn:
        return

    try:
        sns = boto3.client("sns")
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Job search failed: {company}"[:100],
            Message=f"The job search for {company} did not complete. "
            "Check the runtime logs in CloudWatch.",
        )
    except Exception:
        logger.error("Failed to publish failure alert", exc_info=True)
