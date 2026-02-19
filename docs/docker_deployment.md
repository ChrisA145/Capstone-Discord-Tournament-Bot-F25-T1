# Docker Deployment Guide

This document provides instructions for deploying the KSU Esports Tournament application using Docker and GitHub Actions.

## GitHub Actions Setup

The repository is configured with a GitHub Actions workflow that automatically builds and publishes Docker images to Docker Hub whenever:
- Code is pushed to the `main` branch
- A new tag is created (starting with 'v', e.g., v1.0.0)

### Prerequisites

Before you can use the automated Docker deployment, you'll need to:

1. Create a Docker Hub account at [hub.docker.com](https://hub.docker.com/)
2. Create a repository on Docker Hub for this project
3. Generate an access token in Docker Hub (Account Settings → Security → New Access Token)
4. Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: The access token generated in step 3

### How It Works

1. When you push to `main` or create a tag, GitHub Actions runs the workflow
2. The workflow builds a Docker image from your Dockerfile
3. If successful, it pushes the image to Docker Hub with appropriate tags

## Manual Docker Usage

If you prefer to use Docker locally or without GitHub Actions:

### Building the Image

```bash
docker build -t ksu-esports-tournament .
```

### Running the Container

```bash
docker run -d --name ksu-tournament \
  -e DISCORD_APITOKEN=your_token_here \
  -e DISCORD_GUILD=your_guild_id \
  -e DATABASE_NAME=KSU_Tournament.db \
  ksu-esports-tournament
```

Replace the environment variables with your actual configuration.

### Environment Variables

Configure the application by setting these environment variables when running the container:

- `DISCORD_APITOKEN`: Your Discord bot token
- `DISCORD_GUILD`: Your Discord guild ID
- `DATABASE_NAME`: Name of the SQLite database file
- `FEEDBACK_CH`: Feedback channel ID
- `WEBHOOK_URL`: Discord webhook URL
- `CHANNEL_CONFIG`: Channel configuration 
- `CHANNEL_PLAYER`: Player channel ID
- `TOURNAMENT_CH`: Tournament channel ID
- `PRIVATE_CH`: Private channel ID
- `API_KEY`: Riot API key
- `API_URL`: Riot API URL
- `GOOGLE_SHEET_ID`: Google Sheet ID for import/export feature
- `LOL_service_path`: Path to Google service account credentials

## Using Docker Compose

For a more manageable deployment, you can use Docker Compose:

```yaml
version: '3'

services:
  tournament-bot:
    image: your-dockerhub-username/ksu-esports-tournament:latest
    container_name: ksu-tournament
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./Log:/app/Log
      - ./config/google_credentials.json:/app/config/google_credentials.json
    environment:
      - DISCORD_APITOKEN=your_token_here
      - DISCORD_GUILD=your_guild_id
      - DATABASE_NAME=data/KSU_Tournament.db
      - FEEDBACK_CH=your_feedback_channel
      - WEBHOOK_URL=your_webhook_url
      - CHANNEL_CONFIG=your_channel_config
      - CHANNEL_PLAYER=your_player_channel
      - TOURNAMENT_CH=your_tournament_channel
      - PRIVATE_CH=your_private_channel
      - API_KEY=your_riot_api_key
      - API_URL=your_riot_api_url
      - GOOGLE_SHEET_ID=your_google_sheet_id
      - LOL_service_path=/app/config/google_credentials.json
```

Save this as `docker-compose.yml` and run:

```bash
docker-compose up -d
```

## Best Practices

1. Never hardcode sensitive information in Dockerfiles or source code
2. Use environment variables or secrets for all credentials
3. Store persistent data in volume mounts
4. Consider using a `.dockerignore` file to exclude logs, temp files, etc.
5. Use specific version tags in production rather than `latest`