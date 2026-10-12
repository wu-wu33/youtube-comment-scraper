import pandas as pd
import googleapiclient.discovery
import os
import time

# ==================== 1. API Configuration ====================
api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = "YOUR_API_KEY_HERE"   # Replace with your own YouTube Data API key

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)


# ==================== 2. Configuration ====================
# Option A: Single video ID (default)
VIDEO_ID = "dQw4w9WgXcQ"   # Replace with your target video ID

# Option B: Batch mode - load video IDs from an Excel file
# Set USE_BATCH_MODE = True and provide an Excel file with video IDs in column A
USE_BATCH_MODE = False
EXCEL_PATH = "data/video_ids.xlsx"   # Path to your Excel file
EXCEL_SHEET = "Sheet1"

# Output directory
OUTPUT_DIR = "output"


# ==================== 3. Functions ====================
def get_replies(parent_id, video_id):
    """Fetch all replies under a given top-level comment."""
    replies = []
    try:
        request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()
    except Exception as e:
        print(f"      [Reply failed] {parent_id}: {e}")
        return replies

    while True:
        for item in response['items']:
            snip = item['snippet']
            replies.append([
                snip['authorDisplayName'],
                snip['publishedAt'],
                snip['likeCount'],
                snip['textOriginal'],
                video_id,
                parent_id,
                item['id'],
                True,     # is_reply
                1         # reply_level
            ])
        if 'nextPageToken' not in response:
            break
        response = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            pageToken=response['nextPageToken'],
            textFormat="plainText"
        ).execute()
    return replies


def get_comments(video, fetch_replies=True):
    """Fetch top-level comments (and optionally replies) for a video."""
    rows = []

    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video,
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()
    except Exception as e:
        print(f"  [Skipped] {video} - cannot fetch comments: {e}")
        return pd.DataFrame(columns=['author', 'updated_at', 'like_count',
                                     'text', 'video_id', 'parent_id',
                                     'comment_id', 'is_reply', 'reply_level'])

    while True:
        for item in response['items']:
            top = item['snippet']['topLevelComment']
            snip = top['snippet']
            top_id = top['id']

            rows.append([
                snip['authorDisplayName'],
                snip['publishedAt'],
                snip['likeCount'],
                snip['textOriginal'],
                video,
                None,
                top_id,
                False,    # is_reply
                0         # reply_level
            ])

            if fetch_replies and item['snippet'].get('totalReplyCount', 0) > 0:
                reply_rows = get_replies(top_id, video)
                rows.extend(reply_rows)

        if 'nextPageToken' not in response:
            break
        response = youtube.commentThreads().list(
            part="snippet", videoId=video,
            maxResults=100, pageToken=response['nextPageToken'],
            textFormat="plainText"
        ).execute()

    df2 = pd.DataFrame(rows, columns=['author', 'updated_at', 'like_count',
                                      'text', 'video_id', 'parent_id',
                                      'comment_id', 'is_reply', 'reply_level'])
    return df2


# ==================== 4. Clean Video ID ====================
def clean_video_id(vid):
    """Clean video ID from URL or string."""
    vid = str(vid).strip()
    if '&' in vid:
        vid = vid.split('&')[0]
    if '?' in vid:
        vid = vid.split('?')[0]
    return vid


# ==================== 5. Load Video IDs ====================
if USE_BATCH_MODE:
    print(f"Batch mode: loading video IDs from {EXCEL_PATH}")
    id_df = pd.read_excel(EXCEL_PATH, sheet_name=EXCEL_SHEET)
    video_ids = id_df.iloc[:, 0].dropna().astype(str).tolist()
    video_ids = [v for v in video_ids if v.strip() and v.strip().lower() != 'videoid']
    video_ids = [clean_video_id(v) for v in video_ids]
    video_ids = list(dict.fromkeys(video_ids))
    print(f"Loaded {len(video_ids)} video IDs")
else:
    video_ids = [clean_video_id(VIDEO_ID)]
    print(f"Single mode: video ID = {video_ids[0]}")


# ==================== 6. Output Paths ====================
os.makedirs(OUTPUT_DIR, exist_ok=True)

csv_file      = os.path.join(OUTPUT_DIR, 'comments_with_replies.csv')
done_file     = os.path.join(OUTPUT_DIR, 'done_videos.txt')
progress_file = os.path.join(OUTPUT_DIR, 'progress_temp.csv')


# ---------- Load completed video IDs ----------
done_ids = set()
if os.path.exists(done_file):
    with open(done_file, 'r', encoding='utf-8') as f:
        done_ids = set(line.strip() for line in f if line.strip())
    print(f"Found progress file, {len(done_ids)} videos already completed")

# ---------- Load previously scraped data ----------
if os.path.exists(progress_file):
    df_all = pd.read_csv(progress_file, encoding='utf-8-sig')
    print(f"Loaded {len(df_all)} previously scraped records")
else:
    df_all = pd.DataFrame(columns=['author', 'updated_at', 'like_count',
                                   'text', 'video_id', 'parent_id',
                                   'comment_id', 'is_reply', 'reply_level'])


# ==================== 7. Scraping Loop ====================
todo_ids = [v for v in video_ids if v not in done_ids]
print(f"Videos to scrape this run: {len(todo_ids)} (total {len(video_ids)})\n")

for idx, vid in enumerate(todo_ids, 1):
    print(f"[{idx}/{len(todo_ids)}] Scraping: {vid}")
    try:
        df2 = get_comments(vid, fetch_replies=True)
    except Exception as e:
        print(f"\n!! Error while scraping {vid}: {e}")
        print("!! Progress saved. Next run will resume from here.")
        break

    top_n = (~df2['is_reply']).sum() if len(df2) else 0
    rep_n = df2['is_reply'].sum() if len(df2) else 0
    print(f"    -> {top_n} top-level comments, {rep_n} replies")

    # Merge and save immediately
    df_all = pd.concat([df_all, df2], ignore_index=True)
    df_all.to_csv(progress_file, index=False, encoding='utf-8-sig')

    # Mark as done
    with open(done_file, 'a', encoding='utf-8') as f:
        f.write(vid + '\n')

    time.sleep(0.5)   # Small delay to avoid quota limits

print(f"\nTotal records so far: {len(df_all)}")


# ==================== 8. Final: Deduplicate and Save ====================
df_final = df_all.drop_duplicates(subset=['comment_id']).reset_index(drop=True)
df_final.to_csv(csv_file, index=False, encoding='utf-8-sig')

print(f"Saved to: {csv_file}")
print(f"Top-level comments: {(~df_final['is_reply']).sum()}, "
      f"Replies: {df_final['is_reply'].sum()}")
print(f"Videos covered: {df_final['video_id'].nunique()} / {len(video_ids)}")

if len(done_ids) + len(todo_ids) >= len(video_ids):
    print("\nAll videos scraped successfully.")
    # Optional: uncomment to clean up temp files
    # os.remove(progress_file)
    # os.remove(done_file)