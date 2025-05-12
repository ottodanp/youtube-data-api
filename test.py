from asyncio import run
import re

from aiohttp import ClientSession

VIDEO_DETAILS_REGEX = re.compile(r"""videoDetails":{".*"keywords":(\[[\w,\"\s.]+]).*"shortDescription":"([\w\s.\\:@/\-)(#]+)",""")


async def get_video_details(session: ClientSession, video_id: str):
    async with session.get("https://youtube.com/watch?v=" + video_id) as response:
        body = await response.text()
        data = VIDEO_DETAILS_REGEX.findall(body)
        keywords = data[0][0]
        description = data[0][1]
        if keywords[0] != "[" or keywords[-1] != "]":
            keywords = [t.split(" ")[0] for t in description.split("#")[1:]]
        else:
            keywords = keywords.replace("[", "").replace("]", "")
            keyword_items = keywords.split(",")
            keywords = [k.replace('"', "") for k in keyword_items]
        print(keywords)
        print(description)


async def main():
    async with ClientSession() as session:
        await get_video_details(session, "JlvkqFhbLu0")


if __name__ == '__main__':
    run(main())
