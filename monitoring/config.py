"""
Configuration values.
"""

# the location of the file which keeps previously recorded heights
RESULTS_PATH = "monitoring_results.json"

# address of follower instance used in various checks
FOLLOWER_ADDRESS = "localhost:8088"

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

# 3Scale token
X_3SCALE_SECRET_PROXY_TOKEN = "AX8Bj32w4SkgPBZbvcb6jm2McC2cTdYF"

# Base URL for API+ instance used by Explorer
EXPLORER_APIPLUS_URL = "https://apiplus-api-prod-mainnet.factom.com/v2/"
