#!/bin/bash
# to be called by a webhook
# we suppose docker-compose is and alias for either "podman-compose" or "docker compose"

su turtle -c "git pull"
su turtle -c "docker compose build"
su turtle -c "docker compose up -d"