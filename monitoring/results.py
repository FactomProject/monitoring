"""
Check result manipulation and storage.
"""

import json
import os

import monitoring.config


def get_previous():
    """
    Read the file that stores previously recorded results.
    """
    if not os.path.isfile(monitoring.config.RESULTS_PATH):
        return {}

    with open(monitoring.config.RESULTS_PATH) as results_file:
        data = json.load(results_file)

    return data


def save_result(result):
    """
    Save current result to the file, so it can be retrieved during
    the next run.
    """
    with open(monitoring.config.RESULTS_PATH, "w") as results_file:
        json.dump(result, results_file)
