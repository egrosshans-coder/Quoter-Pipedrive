# Quoter Sync

A Python project that synchronizes products/items between Quoter and Pipedrive APIs.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then add your API keys:
   ```
   QUOTER_API_KEY=your_quoter_api_key
   PIPEDRIVE_API_TOKEN=your_pipedrive_api_token
   ```

3. **Run the sync:**
   ```bash
   python main.py
   ```

## Project Structure

- `main.py` - Entry point for the sync process
- `quoter.py` - Quoter API integration
- `pipedrive.py` - Pipedrive API integration
- `utils/logger.py` - Logging configuration
- `.env` - Environment variables (not in git)

## Features

- Syncs products/items from Quoter to Pipedrive
- Handles API authentication
- Logging for debugging and monitoring
- Environment-based configuration 