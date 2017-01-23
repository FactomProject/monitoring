import checks

import json
import requests
import time


SLACK_WEBHOOK = "https://hooks.slack.com/services/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"


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
    _post_to_slack([
        "@everyone The network is stalled.",
        "Current height: {}".format(current["heights"]["follower"]),
        "Previous check at {}".format(prev_run),
        "Current check at {}".format(curr_run)
    ])


def _post_to_slack(lines):
    message = {
        "attachments": [{
            "color": "danger",
            "text": "\n".join(lines)
            }]
        }
    requests.post(SLACK_WEBHOOK, json.dumps(message))

def _format_timestamp(ts):
    if ts is None:
        return ""

    dt = datetime.utcfromtimestamp(ts)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
