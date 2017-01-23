"""
Configuration values.
"""

# the location of the file which keeps previously recorded heights
RESULTS_PATH = "monitoring_results.json"

# addresses of follower instances used in various checks
FOLLOWER_ADDRESS1 = "52.19.99.236:8088"
FOLLOWER_ADDRESS2 = "52.19.99.236:8188"

# interval for end-of-block calculations performed by servers
END_OF_BLOCK_SECS = 10 * 60  # 10 minutes

# address of the slack webhook to call
SLACK_WEBHOOK = (
    "https://hooks.slack.com/services/"
    "T0328S5DQ/B3VQ4659D/2cKmL7w2uysbOF9mugu6VZWI"
)

# address to post PagerDuty events
PAGERDUTY_URL = (
    "https://events.pagerduty.com/generic/2010-04-15/create_event.json"
)

# PagerDuty API key
PAGERDUTY_KEY = "a0eba9950e1849cd9adde9b0b2598633"
