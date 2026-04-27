# FHBG Eligibility Bot - Action Server

This Dockerfile builds the custom action server for the Rasa chatbot.

## Base Image

Uses the official `rasa/rasa:3.6.0-full` image which includes Rasa SDK and common dependencies.

## Build Args

None currently.

## Usage

Build and run with docker-compose:
```bash
docker-compose up action-server
```

Or build manually:
```bash
docker build -t fhbg-action-server .
docker run -p 5055:5055 fhbg-action-server
```

The action server listens on port 5055 by default and connects to the Rasa server via the `/webhook` endpoint.
