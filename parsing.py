from typing import Dict, Any, List, Optional


def extract_text(runs: List[Dict[str, Any]]) -> str:
    return "".join(run.get("text", "") for run in runs)


def extract_first_url(thumbnails: List[Dict[str, Any]]) -> Optional[str]:
    return thumbnails[0].get("url") if thumbnails else None


def parse_video_renderer(video_renderer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    video_id = video_renderer.get("videoId")
    title = extract_text(video_renderer.get("title", {}).get("runs", []))
    description = extract_text(video_renderer.get("descriptionSnippet", {}).get("runs", []))
    view_count = int(video_renderer.get("viewCountText", {}).get("simpleText").split(" ")[0].replace(",", ""))
    duration = video_renderer.get("lengthText", {}).get("simpleText")
    upload_time = video_renderer.get("publishedTimeText", {}).get("simpleText")
    channel_name = extract_text(video_renderer.get("longBylineText", {}).get("runs", []))
    thumbnail_url = extract_first_url(video_renderer.get("thumbnail", {}).get("thumbnails", []))

    if not video_id or not title or not channel_name:
        return None

    return {
        "video_id": video_id,
        "title": title,
        "description": description,
        "view_count": view_count,
        "duration": duration,
        "upload_time": upload_time,
        "channel_name": channel_name,
        "thumbnail_url": thumbnail_url
    }


def parse_short_renderer(short_model: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    video_id = short_model.get('entityId', '').replace('shorts-shelf-item-', '')
    accessibility_text = short_model.get('accessibilityText', '')
    thumbnail_url = extract_first_url(short_model.get('thumbnail', {}).get('sources', []))

    if not video_id or not accessibility_text:
        return None

    title, view_count = None, None
    parts = accessibility_text.split(', ')
    if len(parts) > 1 and 'views' in parts[-1]:
        view_count = parts[-1].strip()
        title = ', '.join(parts[:-1]).split(' - play Short')[0].strip()
    elif ' - play Short' in accessibility_text:
        title = accessibility_text.split(' - play Short')[0].strip()

    if not title:
        return None

    return {
        "video_id": video_id,
        "title": title,
        "channel_name": None,
        "view_count": view_count,
        "duration": None,
        "upload_time": None,
        "thumbnail_url": thumbnail_url,
        "description": ""
    }


def parse_youtube_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    videos = []
    tabs = data.get('tabs', [])

    for tab in tabs:
        tab_renderer = tab.get("tabRenderer", {})
        section_list = tab_renderer.get("content", {}).get("sectionListRenderer", {}).get("contents", [])

        for section in section_list:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                shelf = item.get("shelfRenderer", {})
                expanded_shelf = shelf.get("content", {}).get("expandedShelfContentsRenderer", {}).get("items", [])

                for video_item in expanded_shelf:
                    video_renderer = video_item.get("videoRenderer")
                    if video_renderer:
                        video = parse_video_renderer(video_renderer)
                        if video:
                            videos.append(video)

                for short_item in item.get("reelShelfRenderer", {}).get("items", []):
                    short_model = short_item.get("shortsLockupViewModel")
                    if short_model:
                        short = parse_short_renderer(short_model)
                        if short:
                            videos.append(short)

    return videos


def parse_podcast_details(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    videos = []
    try:
        video_contents = data.get("contents", {}) \
            .get("twoColumnBrowseResultsRenderer", {}) \
            .get("tabs", [])[0] \
            .get("tabRenderer", {}) \
            .get("content", {}) \
            .get("richGridRenderer", {}) \
            .get("contents", [])

        for item in video_contents:
            video_renderer = item.get("richItemRenderer", {}) \
                .get("content", {}) \
                .get("videoRenderer")

            if video_renderer:
                video = parse_video_renderer(video_renderer)
                if video:
                    video["thumbnail_urls"] = video_renderer.get("thumbnail", {}).get("thumbnails", [])
                    # Adjust thumbnail field if needed for podcast
                    videos.append(video)

    except (KeyError, IndexError) as e:
        print(f"Parsing error: {e}")

    return videos
