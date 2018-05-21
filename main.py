#!/usr/bin/env python

"""
Main entry point for running all the monitoring checks.
"""

import sys

import monitoring.results
import monitoring.steps


def main():
    """
    Main entry point for running all the monitoring checks.
    """
    previous = monitoring.results.get_previous()
    success, current = monitoring.steps.run_all(previous)
    monitoring.results.save_result(current)

    if not success:
        print "Job failed"
        sys.exit(-1)

    print "Job finished successfully"


if __name__ == "__main__":
    main()
