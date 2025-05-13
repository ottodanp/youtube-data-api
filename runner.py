from asyncio import run, sleep
from datetime import datetime
from sqlite3 import connect, Connection

from aiohttp import ClientSession

from data import VideoData
from youtube import load_trending_videos

RE_SCRAPE_DELAY = 60 * 30


def sanitize(item: str) -> str:
    return item.replace('"', '')


def insert_video_data(connection: Connection, video: VideoData, category: str):
    timestamp = datetime.now().timestamp()
    cur = connection.cursor()
    query = f"""SELECT * FROM videos WHERE video_id = \"{video.video_id}\""""
    cur.execute(query)
    if len(cur.fetchall()) != 0:
        print("returning")
        return
    query = f"""INSERT INTO videos (video_id, title, channel_name, view_count, duration, upload_time, thumbnail_url, description, keywords, category, timestamp)
    VALUES ("{video.video_id}", "{sanitize(video.title)}", "{video.channel_name}", "{video.view_count}", "{video.duration}", "{video.upload_time}", "{video.thumbnail_url}", "{sanitize(video.description)}", "{video.keyword_string}", "{category}", {timestamp})"""
    cur.execute(query)
    connection.commit()


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
    async with ClientSession() as session:
        videos = await load_trending_videos(session)
        for cat in videos:
            for video in videos[cat]:
                insert_video_data(db, video, cat)

        print("done")
        await sleep(RE_SCRAPE_DELAY)


if __name__ == '__main__':
    run(main())
