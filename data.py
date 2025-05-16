import re
from typing import Dict, Any, List, Optional

from aiohttp import ClientSession

KEYWORDS_REGEX = re.compile(r""""keywords":\[([\w"\s,]+)]""")
DESCRIPTION_REGEX = re.compile(r"""attributedDescriptionBodyText":{"content":"([\w\s\\,'.:/ ]+)""")

TAG_BLACKLIST = ["", "i", "the", "my", "when", "how", "is"]

BASE_CLIENT = {
    "deviceMake": "",
    "deviceModel": "",
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36,gzip(gfe)",
    "clientName": "WEB",
    "clientVersion": "2.20250509.01.01",
    "osName": "Windows",
    "osVersion": "10.0",
    "originalUrl": "https://www.youtube.com/feed/trending",
    "screenPixelDensity": 1,
    "platform": "DESKTOP",
    "clientFormFactor": "UNKNOWN_FORM_FACTOR",
    "screenDensityFloat": 1.25,
    "userInterfaceTheme": "USER_INTERFACE_THEME_DARK",
    "browserName": "Chrome",
    "browserVersion": "136.0.0.0",
    "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "screenWidthPoints": 1536,
    "screenHeightPoints": 730,
    "utcOffsetMinutes": 60,
    "memoryTotalKbytes": "8000000"
}

BASE_PAYLOAD = {
    "context": {
        "client": BASE_CLIENT,
        "user": {
            "lockedSafetyMode": False
        },
        "request": {
            "useSsl": True,
            "internalExperimentFlags": [],
            "consistencyTokenJars": []
        }
    }
}

PODCAST_APP_WEB_INFO = {
    "graftUrl": "/podcasts",
    "pwaInstallabilityStatus": "PWA_INSTALLABILITY_STATUS_UNKNOWN",
    "webDisplayMode": "WEB_DISPLAY_MODE_BROWSER",
    "isWebNativeShareAvailable": True
}


class CaptchaDetected(Exception):
    def __init__(self, source: str):
        super().__init__(f"Captcha raised. Source: {source}")


def generate_podcast_payload() -> Dict[str, Any]:
    payload = BASE_PAYLOAD
    payload["context"]["client"]["mainAppWebInfo"] = PODCAST_APP_WEB_INFO
    payload["context"]["client"]["originalUrl"] = "https://www.youtube.com/podcasts"
    payload["params"] = "qgcCCAE%3D"
    payload["browseId"] = "FEpodcasts_destination"

    return payload


def generate_base_payload(param: str) -> Dict[str, Any]:
    payload = BASE_PAYLOAD
    payload["params"] = param
    payload["browseId"] = "FEtrending"

    return payload


class VideoData:
    title: str = ""
    video_id: str = ""
    channel_name: str = ""
    view_count: int = -1
    duration: str = ""
    upload_time: str = ""
    thumbnail_url: str = ""
    description: str = ""
    keywords: List[str] = []
    dictionary: Dict[str, Any] = {}

    def __init__(self, video: Dict[str, Any]):
        self.title = video["title"]
        self.video_id = video["video_id"]
        self.channel_name = video["channel_name"]
        self.view_count = video["view_count"]
        self.duration = video["duration"]
        self.upload_time = video["upload_time"]
        self.thumbnail_url = video["thumbnail_url"]
        self.description = video["description"]
        self.dictionary = video
        self.dictionary["video_link"] = "https://youtube.com/watch?v=" + self.video_id

    def __str__(self) -> str:
        return (f"Title: {self.title}\nVideo ID: {self.video_id}\nChannel: {self.channel_name}\n"
                f"View Count: {self.view_count}\nDuration: {self.duration}\nUploaded: {self.upload_time}\n"
                f"Thumbnail Url: {self.thumbnail_url}\nLink: https://youtu.be/watch?v={self.video_id}\nDescription:{self.description}")

    def __repr__(self) -> str:
        return str(self)

    def to_dict(self) -> Dict[str, Any]:
        return self.dictionary

    async def get_video_details(self, session: ClientSession) -> None:
        async with session.get("https://youtube.com/watch?v=" + self.video_id) as response:
            body = await response.text()
            if "Our systems have detected unusual traffic from your computer network." in body:
                raise CaptchaDetected("get_video_details")
            description = DESCRIPTION_REGEX.findall(body)
            if len(description) > 0:
                description = description[0]
            else:
                description = ""
            keywords = KEYWORDS_REGEX.findall(body)
            if len(keywords) != 0:
                chunks = keywords[0].split(",")
                self.keywords = [c.replace('"', "") for c in chunks]
            else:
                if len(description) != 0 and "#" in description[0]:
                    self.keywords = [k.split(" ")[0] for k in description[0].split("#")[1:]]

            self.description = description
            self.dictionary["keywords"] = self.keywords
            self.dictionary["description"] = self.description

    @property
    def tags(self) -> Optional[List[str]]:
        tags = []
        for s in [self._extract_tags(self.description), self._extract_tags(self.title)]:
            for t in s:
                if t in tags:
                    continue

                tags.append(t)

        return tags if len(tags) > 0 else None

    @property
    def keyword_string(self) -> str:
        return "#".join(self.keywords)

    @staticmethod
    def _extract_tags(string: str) -> List[str]:
        tags = list(set([t.split(" ")[0] for t in string.split("#")[1:]]))

        return [t for t in tags if t.lower() not in TAG_BLACKLIST]
