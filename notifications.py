import datetime
import json
import sys
import time
import uuid

import requests

import checks


SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
PAGERDUTY_URL = "https://events.pagerduty.com/generic/2010-04-15/create_event.json"
PAGERDUTY_KEY = "a0eba9950e1849cd9adde9b0b2598633"


def handle_result(previous, current):
    """
    Handle the result of running the checks.
    """
    if current["outcome"] == checks.SUCCESS:
        _log_success(previous, current)
    if current["outcome"] == checks.FIRST_RUN:
        _log_first_run(current)
    elif current["outcome"] == checks.SKIPPED:
        _log_checks_skipped(previous, current)
    elif current["outcome"] == checks.FOLLOWER_ERROR:
        _log_follower_error()
        _notify_follower_error()
        sys.exit(-1)
    elif current["outcome"] == checks.FOLLOWER_STALLED:
        _log_follower_stalled(previous, current)
        _notify_follower_stalled(previous, current)
    elif current["outcome"] == checks.NETWORK_STALLED:
        _log_network_stalled(previous, current)
        _notify_network_stalled(previous, current)


def _log_success(previous, current):
    print "All checks passed."
    print "Current leader height: {}".format(current["heights"]["leader"])
    print "Current follower height: {}".format(current["heights"]["follower"])
    # TODO remove
    height = current["heights"]["leader"]
    prev_run = _format_timestamp(previous["timestamp"])
    curr_run = _format_timestamp(current["timestamp"])
    _trigger_pagerduty_alert(
        "Factom network stalled at {}".format(height),
        {
            "heights": current["heights"],
            "previous_run": prev_run,
            "current_run": curr_run
        },
        incident_key
    )

def _log_first_run(current):
    print "First run, skipping checks."


def _log_checks_skipped(previous, current):
    print "Not enough time passed since the last run, all checks skipped."
    print "Previous run: {}".format(previous["timestamp"])
    print "Current run: {}".format(current["timestamp"])


def _log_follower_error():
    print "Follower error, no checks run."


def _log_follower_stalled(previous, current):
    print "Follower stalled."
    print "Previous height: {}".format(previous["heights"]["follower"])
    print "Current height: {}".format(current["heights"]["follower"])


def _log_network_stalled(previous, current):
    print "The main network stalled."
    print "Previous height: {}".format(previous["heights"]["leader"])
    print "Current height: {}".format(current["heights"]["leader"])


def _notify_follower_error():
    _post_to_slack([
        "Error contacting the follower. See jenkins job for details."
    ])


def _notify_follower_stalled(previous, current):
    prev_run = _format_timestamp(previous["timestamp"])
    curr_run = _format_timestamp(current["timestamp"])
    _post_to_slack([
        "@here Follower stalled.",
        "Height: {}".format(current["heights"]["follower"]),
        "Previous check at {}".format(prev_run),
        "Current check at {}".format(curr_run)
    ])


def _notify_network_stalled(previous, current):
    prev_run = _format_timestamp(previous["timestamp"])
    curr_run = _format_timestamp(current["timestamp"])
    height = current["heights"]["leader"]
    _post_to_slack([
        "@everyone The network is stalled.",
        "Current height: {}".format(height),
        "Previous check at {}".format(prev_run),
        "Current check at {}".format(curr_run)
    ])
    incident_key = previous["incident_key"] or str(uuid.uuid4())
    current["incident_key"] = incident_key
    _trigger_pagerduty_alert(
        "Factom network stalled at {}".format(height),
        {
            "heights": current["heights"],
            "previous_run": prev_run,
            "current_run": curr_run
        },
        incident_key
    )


def _post_to_slack(lines):
    message = {
        "attachments": [{
            "color": "danger",
            "text": "\n".join(lines)
            }]
        }
    requests.post(SLACK_WEBHOOK, json.dumps(message))


def _trigger_pagerduty_alert(description, details, incident_key):
    message = {
        "event_type": "trigger",
        "client": "jenkins",
        "service_key": PAGERDUTY_KEY,
        "description": description,
        "details": details
    }

    if incident_key:
        message["incident_key"] = incident_key

    requests.post(PAGERDUTY_URL, json.dumps(message))


def _format_timestamp(ts):
    if ts is None:
        return ""

    dt = datetime.datetime.utcfromtimestamp(ts)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

