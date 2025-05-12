from sqlite3 import connect
from typing import List, Any, Dict

from quart import Quart

quart = Quart(__name__)
db = connect("trending.db")


def parse_db_output(row: List[Any]) -> Dict[str, Any]:
    return {
        "video_id": row[0],
        "title": row[1],
        "channel_name": row[2],
        "view_count": row[3],
        "duration": row[4],
        "upload_time": row[5],
        "thumbnail_url": row[6],
        "description": row[7],
        "keywords": row[8].split("#"),
        "category": row[9]
    }


@quart.route("/data")
async def trending_data():
    query = "SELECT * FROM VIDEOS"
    cur = db.cursor()
    cur.execute(query)
    results = cur.fetchall()
    return [parse_db_output(r) for r in results]


if __name__ == '__main__':
    quart.run(host="0.0.0.0")
