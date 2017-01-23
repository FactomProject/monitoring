#!/usr/bin/env python
import checks
import notifications

# the location of the file which keeps previously recorded heights
RESULTS_PATH = "heights.json"


def main():
    previous = checks.get_previous_result(RESULTS_PATH)
    current = checks.run(previous)
    notifications.handle_result(previous, current)
    checks.save_result(current, RESULTS_PATH)


if __name__ == "__main__":
    main()
