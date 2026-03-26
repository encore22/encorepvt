# Gmail Automation System

Automated Gmail offer link retrieval system using Firebase Test Lab, Appium, and Telegram bot interface.

## Overview

This system automates the process of retrieving Google One Gemini Pro 12-month free offer redemption links by:
1. Accepting Gmail credentials via Telegram bot
2. Spinning up Pixel 10 Pro virtual devices on Firebase Test Lab
3. Logging into Gmail and navigating to Google One
4. Extracting the offer link
5. Returning the link via Telegram
6. Destroying the device

## Quick Start

See [docs/SETUP.md](docs/SETUP.md) for full setup instructions.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system architecture details.

## Services

- **Telegram Bot** - User interaction & credential collection
- **Device Manager** - Job queue processing & device orchestration
- **Device Automation** - Appium-based device control

## Requirements

- Google Cloud Project with Firebase Test Lab enabled
- Telegram Bot Token
- Firebase service account credentials
