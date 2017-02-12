"""
Checks whether the explorer is available and that it advances correctly.
"""
import datetime
import time

import requests

from monitoring import config
from monitoring.notifications import (
    log, info, error,
    trigger_pagerduty_incident, resolve_pagerduty_incident
)

SUCCESS = "success"
EXPLORER_OFFLINE = "explorer offline"
EXPLORER_STALLED = "explorer stalled"


def run(previous):
    """
    Checks whether the explorer is available and that it advances correctly.
    """
    now = time.time()
    height = _get_height()

    if height is None:
        return _explorer_offline(now, previous)
    elif previous is None:
        return _first_run(now, height)
    elif now - previous["timestamp"] < config.END_OF_BLOCK_SECS:
        return _skip(previous, now)
    elif previous["height"] == height:
        return _explorer_stalled(previous, now, height)
    else:
        return _success(previous, now, height)


def _get_height():
    response = requests.get("http://explorer.factom.org/height")
    response.raise_for_status()
    return response.text


def _explorer_offline(now, previous):
    error("Cannot contact explorer, is it up?")
    return False, {
        "timestamp": now,
        "height": previous["height"],
        "result": EXPLORER_OFFLINE
    }


def _first_run(now, height):
    log("Explorer check first run, checks skipped.")
    return True, {
        "timestamp": now,
        "height": height,
        "result": SUCCESS
    }


def _skip(previous, now):
    log("Not enough time passed, explorer check skipped.")
    log("Previous run: ", _format_ts(previous["timestamp"]))
    log("Current run: ", _format_ts(now))
    return True, previous  # keep previous results


def _explorer_stalled(previous, now, height):
    incident_key = previous.get("incident_key")
    if previous["result"] != EXPLORER_STALLED:
        error(
            "Explorer stalled at {}".format(height),
            "First seen: {} (UTC)".format(_format_ts(previous["timestamp"])),
            "Creating alert in PagerDuty."
        )
    else:
        log("Explorer still at {}", height)

    incident_key = trigger_pagerduty_incident(
        "Explorer stalled at {}".format(height),
        {
            "height": height,
        },
        incident_key
    )
    return False, {
        "timestamp": now,
        "height": height,
        "result": EXPLORER_STALLED,
        "incident_key": incident_key
    }


def _success(previous, now, height):
    if previous["result"] == EXPLORER_OFFLINE:
        info("Explorer is available again")
    elif previous["result"] == EXPLORER_STALLED:
        msg = "Explorer advanced from {} to {}".format(
            previous["height"],
            height
        )
        info(msg, "Resolving PagerDuty incident.")
        resolve_pagerduty_incident(
            msg,
            {
                "previous_height": previous["height"],
                "current_height": height,

            },
            previous["incident_key"]
        )
    return True, {
        "timestamp": now,
        "height": height,
        "result": SUCCESS
    }


def _format_ts(timestamp):
    if timestamp is None:
        return "<unknown>"

    date = datetime.datetime.utcfromtimestamp(timestamp)
    return date.strftime("%Y-%m-%dT%H:%M:%S")
