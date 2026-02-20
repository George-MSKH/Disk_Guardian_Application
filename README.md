🛡 Disk Guardian
🚀 Overview

Disk Guardian is a lightweight, Python-based monitoring agent built to prevent server downtime caused by disk exhaustion.

Running inside a Docker container, it continuously monitors host storage in real time and automatically sends Slack alerts when predefined usage thresholds are exceeded.

The goal is simple: detect disk pressure early and act before it becomes an outage.

✨ Key Features

Real-Time Monitoring
Continuous disk health checks powered by psutil.

Event-Driven Alerting
Instant notifications via Slack Incoming Webhooks when thresholds are breached.

Containerized Architecture
Fully portable and easy to deploy using Docker and Docker Compose.

Security-First Design

Read-only volume mounts

Environment variable–based secret injection

Minimal container footprint

🛠 Tech Stack

Language

Python 3.11

Libraries

psutil – System statistics and disk metrics

requests – API communication

Infrastructure

Docker

Docker Compose

Communication

Slack Incoming Webhooks API

📐 Architecture

Disk Guardian runs in an isolated container environment.

The host filesystem is mounted into the container using a read-only bind mount. This ensures the agent can monitor disk usage without having write access to sensitive system files.

This design enforces separation of concerns:

The host system remains protected.

The monitoring agent operates independently.

No modification rights are granted to the container.

🚦 Getting Started
Prerequisites

Docker

Docker Compose

A Slack Incoming Webhook URL

Installation & Setup
1. Clone the Repository
git clone https://github.com/your-username/disk-guardian.git
cd disk-guardian

2. Configure Environment Variables

Create a .env file from the provided example:

cp .env.example .env


Open the .env file and add your Slack Webhook URL.

3. Deploy with Docker Compose
docker-compose up -d


The monitoring agent will start running in the background.

📊 How It Works

Every 10 seconds (configurable), the agent:

Scans the mounted /host directory.

Calculates the percentage of used disk space.

Compares usage against the defined THRESHOLD.

If usage exceeds the threshold, it sends a JSON payload to the Slack API.

This loop continues indefinitely to ensure continuous monitoring.

🛡 Security Practices Implemented

Least Privilege Principle
The host filesystem is mounted with the :ro (read-only) flag.

Secret Management
Sensitive credentials are stored in a .env file and excluded from version control via .gitignore.

Minimal Attack Surface
Uses python-slim base images to reduce image size and potential vulnerabilities.