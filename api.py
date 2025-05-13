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
        "category": row[9],
        "timestamp": row[10]
    }


def get_all_data(category: str) -> List[Dict[str, Any]]:
    query = f"SELECT * FROM VIDEOS"
    if category.lower() != "all":
        query += f" where category like '{category}'"

    cur = db.cursor()
    cur.execute(query)
    results = cur.fetchall()
    return [parse_db_output(r) for r in results]


@quart.route("/data/<category>")
async def trending_data(category):
    return get_all_data(category)


@quart.route("/tags/<category>")
async def trending_tags(category):
    results = get_all_data(category)
    trending_tags_result = []
    for r in results:
        tags = r["keywords"]
        if len(tags) == 0:
            continue
        if len(tags) == 1 and tags[0] == "":
            continue

        trending_tags_result.append(tags)
        continue

    return trending_tags_result


if __name__ == '__main__':
    quart.run(host="0.0.0.0")
