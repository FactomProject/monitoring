"""
Various checks performed against the network to verify it is running correctly.
"""

import monitoring.steps.heights
import monitoring.steps.transactions

ALL_STEPS = [monitoring.steps.heights,
             monitoring.steps.transactions]


def run_all(previous):
    """
    Runs all checks
    """
    current = {}
    success = True
    for step in ALL_STEPS:
        module_previous = previous.get(step.NAME)
        success, result = step.run(module_previous)
        current[step.NAME] = result
        if not success:
            break
    return success, current
