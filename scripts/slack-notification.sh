#!/bin/bash

HEADER=$1
COLOR=$2
TEXT=$3

PAYLOAD="{\"text\": \"${HEADER}\", \"attachments\":[{\"color\": \"${COLOR}\", \"text\":\"${TEXT}\"}]}"

curl -X POST \
  -H 'application/json' \
  --data "${PAYLOAD}" \
  https://hooks.slack.com/services/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
