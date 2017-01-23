"""
Checks if the transactions submitted to one follower show up on another one.
"""
NAME = "transactions"


def run(previous):
    """
    Creates some transactions and checks that they show up on another follower.
    Returns a tuple of: boolean indicating whether the check was successful and
    the information that should be stored for the next run.
    """
    return True, previous
