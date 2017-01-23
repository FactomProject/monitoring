import json
import os
import subprocess
import time


# address to connect the follower to
FOLLOWER_ADDRESS = "52.19.99.236:8180"


MIN_SECS_BETWEEN_RUNS = 10 * 60  # 10 minutes


# various outcomes of comparison
SUCCESS = "success"
SKIPPED = "skipped"
FIRST_RUN = "first"
FOLLOWER_STALLED = "follower stalled"
NETWORK_STALLED = "network stalled"
FOLLOWER_ERROR = "follower error"


def get_previous_result(results_path):
    """
    Read the file that stores previously recorded results.
    """
    if not os.path.isfile(results_path):
        return None

    with open(results_path) as results_file:
        data = json.load(results_file)

    return data


def save_result(result, results_path):
    """
    Save current result to the file, so it can be retrieved during
    the next run.
    """
    if result["outcome"] == SKIPPED:
        return  # do not overwrite the results, we'll wait for the next run

    with open(results_path, "w") as results_file:
        json.dump(result, results_file)


def run(previous):
    """
    Run all checks against the monitored follower node.
    """
    now = time.time()

    try:
        heights = _get_heights()
    except FollowerError:
        outcome = FOLLOWER_ERROR
        heights = None
    else:
        if previous_result is None:
            outcome = FIRST_RUN
        elif now - previous["timestamp"] < MIN_SECS_BETWEEN_RUNS:
            outcome = SKIPPED
        elif previous_result["heights"]["leader"] == heights["leader"]:
            outcome = NETWORK_STALLED
        elif previous_result["heights"]["follower"] == heights["follower"]:
            outcome = FOLLOWER_STALLED

    return {
        "outcome": outcome,
        "heights": heights,
        "timestamp": now
    }


def _get_heights():
    output = _get_cli_output()
    return _parse_cli_output(output)


def _get_cli_output():
    cmd = ["factom-cli", "-s", FOLLOWER_ADDRESS, "get", "heights"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print "Error running cli command: {}".format(str(e))
        raise FollowerError()

    net_error = "Post http://{}/v2: dial tcp".format(FOLLOWER_ADDRESS)
    if output.startswith(net_error):
        print "Unable to contact follower: {}".format(output)
        raise FollowerError()
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


class FollowerError(Exception):
    pass
