from asyncio import run
from typing import Dict, Any, List

from aiohttp import ClientSession

from data import BASE_PAYLOAD, VideoData, PODCAST_PAYLOAD
from parsing import parse_youtube_data, parse_podcast_details, VIDEO_DETAILS_REGEX


async def get_cookies(session: ClientSession) -> None:
    async with session.get("https://www.youtube.com/") as response:
        cookies = response.cookies
        session.cookie_jar.update_cookies(cookies)

    async with session.post(
            "https://consent.youtube.com/save?continue=https://www.youtube.com/%3FthemeRefresh%3D1&gl=GB&m=0&pc=yt&x=5&src=2&hl=en&bl=755513870&cm=2&set_eom=true") as consent_response:
        return


async def get_video_details(session: ClientSession, video_id: str):
    print(video_id)
    async with session.get("https://youtube.com/watch?v=" + video_id) as response:
        body = await response.text()
        open("test.txt", "wb").write(body.encode(errors="ignore"))
        data = VIDEO_DETAILS_REGEX.findall(body)
        input(data)


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
                            json=PODCAST_PAYLOAD) as response:
        body = await response.json()

        return [VideoData(v) for v in parse_podcast_details(body)]


def inject_tab_payload(data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    data["params"] = endpoint
    data["context"]["client"]["originalUrl"] = f"https://www.youtube.com/feed/trending?bp={endpoint}"
    return data


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
        for video in videos[cat]:
            tags = video.tags
            if not tags:
                continue

            await get_video_details(session, "zDuJqlt1nhE")
    return videos


async def main():
    async with ClientSession() as session:
        await load_trending_videos(session)


if __name__ == '__main__':
    run(main())
