"""
Checks if follower/leader heights advanced after end-of-block time elapsed.
"""
import datetime
import subprocess
import time

from monitoring import config
from monitoring.notifications import (
    log, info, error,
    trigger_pagerduty_incident, resolve_pagerduty_incident
)


NAME = "heights"


SUCCESS = "success"
FOLLOWER_STALLED = "follower stalled"
LEADER_STALLED = "leader stalled"
FOLLOWER_REVERSED = "follower reversed"


def run(previous):
    """
    Checks whether heights of the follower and leader advance correctly.
    Returns a tuple of: boolean indicating whether the check was successful and
    the information that should be stored for the next run.
    """
    now = time.time()
    heights = _get_heights()

    if heights is None:
        result = _no_follower(previous)
    elif previous is None:
        result = _first_run(now, heights)
    elif now - previous["timestamp"] < config.END_OF_BLOCK_SECS:
        result = _skip(previous, now)
    elif previous["heights"]["leader"] == heights["leader"]:
        result = _leader_stalled(previous, now, heights)
    elif previous["heights"]["follower"] == heights["follower"]:
        result = _follower_stalled(previous, now, heights)
    elif previous["heights"]["follower"] > heights["follower"]:
        result = _follower_reversed(previous, now, heights)
    else:
        result = _success(previous, now, heights)

    return result


def _no_follower(previous):
    error("Error connecting to the follower. See Jenkins job details.")
    return False, previous  # keep previous results


def _first_run(now, heights):
    log("First run, height checks skipped.")
    return True, {
        "timestamp": now,
        "heights": heights,
        "result": SUCCESS
    }


def _skip(previous, now):
    log("Not enough time passed, heights checks skipped.")
    log("Previous run: ", _format_ts(previous["timestamp"]))
    log("Current run: ", _format_ts(now))
    return True, previous  # keep previous results


def _follower_stalled(previous, now, heights):
    if previous["result"] != FOLLOWER_STALLED:
        error(
            "Follower stalled at {}".format(heights["follower"]),
            "First seen at {}".format(_format_ts(previous["timestamp"]))
        )
    else:
        log("Follower still at: {}".format(heights["follower"]))
    return False, {
        "timestamp": now,
        "heights": heights,
        "result": FOLLOWER_STALLED
    }


def _follower_reversed(previous, now, heights):
    if previous["result"] not in [FOLLOWER_STALLED, FOLLOWER_REVERSED]:
        error(
            "Follower reversed from {} to {}".format(
                previous["heights"]["follower"], heights["follower"]
            )
        )
    else:
        log(
            "Follower catching up with leader.",
            "Leader height: {}".format(heights["leader"]),
            "Current follower height: {}".format(heights["follower"]),
            "Max follower height: {}".format(previous["heights"]["follower"])
        )
    return False, {
        "timestamp": now,
        "heights": {
            "leader": heights["leader"],
            # keep previous follower height until it goes forward
            "follower": previous["heights"]["follower"]
        },
        "result": FOLLOWER_REVERSED
    }


def _leader_stalled(previous, now, heights):
    incident_key = previous.get("incident_key")
    if previous["result"] != LEADER_STALLED:
        error(
            "Network stalled at {}".format(heights["leader"]),
            "First seen: {} (UTC)".format(_format_ts(previous["timestamp"])),
            "Current follower height at {}".format(heights["follower"]),
            "Creating alert in PagerDuty."
        )

    else:
        log("Follower still at {}", heights["follower"])

    incident_key = trigger_pagerduty_incident(
        "Leader stalled at {}".format(heights["leader"]),
        {
            "leader_height": heights["leader"],
            "follower_height": heights["follower"]
        },
        incident_key
    )
    return False, {
        "timestamp": now,
        "heights": heights,
        "result": LEADER_STALLED,
        "incident_key": incident_key
    }


def _success(previous, now, heights):
    if previous["result"] in [FOLLOWER_STALLED, FOLLOWER_REVERSED]:
        info(
            "Follower advanced from {} to {}".format(
                previous["heights"]["follower"],
                heights["follower"]
            ),
            "Previous problem resolved."
        )
    elif previous["result"] == LEADER_STALLED:
        msg = "Leader advanced from {} to {}".format(
            previous["heights"]["leader"],
            heights["leader"]
        )
        info(msg, "Resolving PagerDuty incident.")
        resolve_pagerduty_incident(
            msg,
            {
                "previous_leader_height": previous["heights"]["leader"],
                "current_leader_height": heights["leader"],

            },
            previous["incident_key"]
        )
    return True, {
        "timestamp": now,
        "heights": heights,
        "result": SUCCESS
    }


def _get_heights():
    output = _get_cli_output()
    if output is None:
        return None
    return _parse_cli_output(output)


def _get_cli_output():
    address = config.FOLLOWER_ADDRESS
    cmd = ["factom-cli", "-s", address, "get", "heights"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        log("Error running cli command: ", str(exc))
        return None

    net_error = "Post http://{}/v2: dial tcp".format(address)
    if output.startswith(net_error):
        log("Unable to contact follower: ", output)
        return None
    return output


def _parse_cli_output(output):
    lines = output.split('\n')
    follower_data = lines[0].split(" ")
    leader_data = lines[1].split(" ")

    follower_height = int(follower_data[1])
    leader_height = int(leader_data[1])

    return {
        "leader": leader_height,
        "follower": follower_height
    }


def _format_ts(timestamp):
    if timestamp is None:
        return "<unknown>"

    date = datetime.datetime.utcfromtimestamp(timestamp)
    return date.strftime("%Y-%m-%dT%H:%M:%S")
