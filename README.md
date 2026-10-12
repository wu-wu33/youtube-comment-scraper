# YouTube Comment Scraper

A Python script to scrape top-level comments and replies from YouTube videos using the YouTube Data API v3.

## Overview

This tool collects user comments (both top-level and nested replies) from YouTube videos for research purposes, such as sentiment analysis, discourse studies, and computational social science.

## Features

- Scrape top-level comments and all nested replies
- Support both single video ID and batch mode (multiple IDs from Excel)
- Resume from interruption (checkpoint system)
- Automatic deduplication by comment ID
- Export to CSV with UTF-8 BOM (Excel-compatible)
- Includes user metadata: author, timestamp, likes, reply level

## Requirements

    pip install google-api-python-client pandas openpyxl

## Setup

### 1. Get a YouTube Data API Key

1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create an API Key under Credentials

### 2. Set Your API Key

Replace the placeholder in the script:

    DEVELOPER_KEY = "YOUR_API_KEY_HERE"

## Usage

### Single Video Mode (default)

Set the video ID at the top of the script:

    VIDEO_ID = "dQw4w9WgXcQ"
    USE_BATCH_MODE = False

Then run:

    python youtube_comment_scraper.py

### Batch Mode (multiple videos)

To scrape multiple videos from an Excel file, set:

    USE_BATCH_MODE = True
    EXCEL_PATH = "data/video_ids.xlsx"

Prepare an Excel file with video IDs in the first column:

| VideoID |
|---------|
| dQw4w9WgXcQ |
| BE7JXDLFyhM |

Then run:

    python youtube_comment_scraper.py

## Output Format

| Column | Description |
|--------|-------------|
| author | Comment author display name |
| updated_at | Timestamp |
| like_count | Number of likes |
| text | Comment text |
| video_id | YouTube video ID |
| parent_id | Parent comment ID (for replies) |
| comment_id | Unique comment ID |
| is_reply | True if this is a reply |
| reply_level | 0 for top-level, 1 for reply |

## Output Files

All output files are saved in the `output/` directory:

- `comments_with_replies.csv` - final deduplicated data
- `progress_temp.csv` - intermediate progress file (for resume)
- `done_videos.txt` - list of completed video IDs

## How It Works

1. Load video IDs: either a single ID or multiple IDs from an Excel file.
2. Fetch comments: Uses commentThreads().list() to get top-level comments.
3. Fetch replies: For each top-level comment, uses comments().list() with parentId to get replies.
4. Checkpoint system: Saves progress after each video, so you can resume if interrupted.
5. Deduplication: Removes duplicate comments by comment_id.

## Notes

- YouTube API has a daily quota limit (10,000 units/day by default).
- Each video with many comments may take several minutes.
- The script handles quota exhaustion gracefully and can resume later.
- Please respect YouTube's Terms of Service and use this tool only for academic research.

## Disclaimer

This tool is intended for academic research purposes only. Users are responsible for complying with YouTube's Terms of Service and applicable data protection laws.

## Contact

florencewu103@gmail.com
