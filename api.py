from aiohttp import ClientSession
from quart import Quart

from youtube import load_trending_videos

quart = Quart(__name__)


@quart.route("/data")
async def trending_data():
    async with ClientSession() as session:
        results = await load_trending_videos(session)
        for category in results.keys():
            results[category] = [r.to_dict() for r in results[category]]

        return results


if __name__ == '__main__':
    quart.run(host="0.0.0.0")
