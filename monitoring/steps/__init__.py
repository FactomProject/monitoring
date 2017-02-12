"""
Various checks performed against the network to verify it is running correctly.
"""
import importlib

ALL_STEPS = ['monitoring.steps.heights',
             'monitoring.steps.explorer',
             'monitoring.steps.transactions']


def run_all(previous):
    """
    Runs all checks
    """
    current = {}
    success = True
    for step in ALL_STEPS:
        module = importlib.import_module(step)
        step_name = getattr(module, "NAME")
        step_run = getattr(module, "run")
        module_previous = previous.get(step_name)
        success, result = step_run(module_previous)
        current[step_name] = result
        if not success:
            break
    return success, current
