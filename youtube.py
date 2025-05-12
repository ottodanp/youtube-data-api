from asyncio import run, gather
from typing import Dict, Any, List

from aiohttp import ClientSession

from data import BASE_PAYLOAD, VideoData, PODCAST_PAYLOAD, generate_podcast_payload
from parsing import parse_youtube_data, parse_podcast_details


async def get_cookies(session: ClientSession) -> None:
    async with session.get("https://www.youtube.com/") as response:
        cookies = response.cookies
        session.cookie_jar.update_cookies(cookies)

    async with session.post(
            "https://consent.youtube.com/save?continue=https://www.youtube.com/%3FthemeRefresh%3D1&gl=GB&m=0&pc=yt&x=5&src=2&hl=en&bl=755513870&cm=2&set_eom=true") as consent_response:
        return


async def load(session: ClientSession, endpoint: str) -> List[VideoData]:
    async with session.post("https://www.youtube.com/youtubei/v1/browse?prettyPrint=false",
                            json=inject_tab_payload(BASE_PAYLOAD, endpoint)) as response:
        body = await response.json()
        contents = body.get("contents")

        if contents is None:
            raise

        two_column_results = contents.get("twoColumnBrowseResultsRenderer")
        if two_column_results is None:
            raise

        return [VideoData(v) for v in parse_youtube_data(two_column_results)]


async def load_podcasts(session: ClientSession) -> List[VideoData]:
    async with session.post("https://www.youtube.com/youtubei/v1/browse?prettyPrint=false",
                            json=generate_podcast_payload()) as response:
        body = await response.json()

        return [VideoData(v) for v in parse_podcast_details(body)]


def inject_tab_payload(data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    data["params"] = endpoint
    data["context"]["client"]["originalUrl"] = f"https://www.youtube.com/feed/trending?bp={endpoint}"
    return data


async def gather_video_details_mass(session: ClientSession, videos: List[VideoData]):
    await gather(*[video.get_video_details(session) for video in videos])


async def load_trending_videos(session: ClientSession) -> Dict[str, List[VideoData]]:
    videos = {"Podcasts": await load_podcasts(session)}
    for payload, category in [
        ("", "Now"),
        ("4gINGgt5dG1hX2NoYXJ0cw%3D%3D", "Music"),
        ("4gIcGhpnYW1pbmdfY29ycHVzX21vc3RfcG9wdWxhcg%3D%3D", "Gaming"),
        ("4gIKGgh0cmFpbGVycw%3D%3D", "Movies")
    ]:
        videos[category] = await load(session, payload)

    for cat in videos:
        await gather_video_details_mass(session, videos[cat])

    return videos


async def main():
    async with ClientSession() as session:
        await load_trending_videos(session)


if __name__ == '__main__':
    run(main())
