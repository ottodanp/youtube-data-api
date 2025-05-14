from asyncio import run, sleep
from datetime import datetime
from sqlite3 import connect, Connection

from aiohttp import ClientSession

from data import VideoData
from youtube import load_trending_videos

RE_SCRAPE_DELAY = 60 * 10


def sanitize(item: str) -> str:
    return item.replace('"', '')


def insert_video_data(connection: Connection, video: VideoData, category: str)-> bool :
    timestamp = datetime.now().timestamp()
    cur = connection.cursor()
    query = f"""SELECT * FROM videos WHERE video_id = \"{video.video_id}\""""
    cur.execute(query)
    if len(cur.fetchall()) != 0:
        return False
    print("inserting " + video.video_id)
    query = f"""INSERT INTO videos (video_id, title, channel_name, view_count, duration, upload_time, thumbnail_url, description, keywords, category, timestamp)
    VALUES ("{video.video_id}", "{sanitize(video.title)}", "{video.channel_name}", "{video.view_count}", "{video.duration}", "{video.upload_time}", "{video.thumbnail_url}", "{sanitize(video.description)}", "{video.keyword_string}", "{category}", {timestamp})"""
    cur.execute(query)
    connection.commit()
    return True


def create_tables(connection: Connection):
    cur = connection.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        title TEXT,
        channel_name TEXT,
        view_count TEXT,
        duration TEXT, 
        upload_time TEXT,
        thumbnail_url TEXT,
        description TEXT,
        keywords TEXT,
        category TEXT,
        timestamp INTEGER)"""
    cur.execute(query)
    connection.commit()


async def main():
    db = connect("trending.db")
    create_tables(db)
    inserted = 0
    skipped = 0
    async with ClientSession() as session:
        videos = await load_trending_videos(session)
        for cat in videos:
            for video in videos[cat]:
                if not insert_video_data(db, video, cat):
                    skipped += 1
                else:
                    inserted += 1

        print(f"done. inserted: {inserted}, skipped: {skipped}")
        await sleep(RE_SCRAPE_DELAY)


if __name__ == '__main__':
    run(main())
