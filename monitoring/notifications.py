"""
Notifications send by the monitoring scripts.
"""
import json
import uuid

import requests

from monitoring import config


def log(*messages):
    """
    Logs the messages in the job output.
    """
    for msg in messages:
        print msg


def info(*messages):
    """
    Logs the message and sends the output to Slack as an information.
    """
    log(*messages)
    _post_to_slack(messages, "good", "<!here>")


def error(*messages):
    """
    Logs the message and sends the output to Slack as an error.
    """
    log(*messages)
    _post_to_slack(messages, "danger", "<!channel>")


def trigger_pagerduty_incident(message, details, incident_key=None):
    """
    Triggers a new PagerDuty incident.
    """
    incident_key = incident_key or str(uuid.uuid4())
    _send_pagerduty_event("trigger", message, details, incident_key)
    return incident_key


def resolve_pagerduty_incident(message, details, incident_key):
    """
    Resolves a previously triggered PagerDuty incident.
    """
    _send_pagerduty_event("resolve", message, details, incident_key)


def _post_to_slack(lines, color, header):
    message = {
        "text": header,
        "attachments": [{
            "color": color,
            "text": "\n".join(lines)
            }]
        }
    requests.post(config.SLACK_WEBHOOK, json.dumps(message))


def _send_pagerduty_event(event_type, description, details, incident_key):
    message = {
        "event_type": event_type,
        "client": "monitoring scripts",
        "service_key": config.PAGERDUTY_KEY,
        "description": description,
        "details": details,
        "incident_key": incident_key
    }

    requests.post(config.PAGERDUTY_URL, json.dumps(message))
