from typing import Dict, Any

def tab_meets_requirements(tab: Dict[str, Any]) -> bool:
    return 'tabRenderer' in tab and 'content' in tab['tabRenderer'] and \
        'sectionListRenderer' in tab['tabRenderer']['content'] and \
        'contents' in tab['tabRenderer']['content']['sectionListRenderer']


def verify_tab_section(item: Dict[str, Any]) -> bool:
    return 'shelfRenderer' in item and 'content' in item['shelfRenderer'] and \
        'expandedShelfContentsRenderer' in item['shelfRenderer']['content'] and \
        'items' in item['shelfRenderer']['content']['expandedShelfContentsRenderer']


def parse_youtube_data(data):
    videos_data = []
    if 'tabs' in data and isinstance(data['tabs'], list):
        for tab in data['tabs']:
            if not tab_meets_requirements(tab):
                continue

            for section in tab['tabRenderer']['content']['sectionListRenderer']['contents']:
                if not ('itemSectionRenderer' in section and 'contents' in section['itemSectionRenderer']):
                    continue

                for item in section['itemSectionRenderer']['contents']:
                    if verify_tab_section(item):
                        for video_item in item['shelfRenderer']['content']['expandedShelfContentsRenderer'][
                            'items']:
                            if 'videoRenderer' in video_item:
                                video_renderer = video_item['videoRenderer']
                                video_id = video_renderer.get('videoId')
                                title_runs = video_renderer.get('title', {}).get('runs', [])
                                title = title_runs[0]['text'] if title_runs else None
                                channel_runs = video_renderer.get('longBylineText', {}).get('runs', [])
                                channel_name = channel_runs[0]['text'] if channel_runs else None
                                description_snippet_runs = video_renderer.get("descriptionSnippet", {}).get("runs", [])
                                description = "".join(run.get("text", "") for run in description_snippet_runs)
                                view_count_text = video_renderer.get('viewCountText', {}).get('simpleText')
                                length_text = video_renderer.get('lengthText', {}).get('simpleText')
                                published_time_text = video_renderer.get('publishedTimeText', {}).get(
                                    'simpleText')
                                thumbnail_list = video_renderer.get('thumbnail', {}).get('thumbnails', [])
                                thumbnail_url = thumbnail_list[0]['url'] if thumbnail_list else None

                                if video_id and title and channel_name:
                                    videos_data.append({
                                        'title': title,
                                        'video_id': video_id,
                                        'channel_name': channel_name,
                                        'view_count': view_count_text,
                                        'duration': length_text,
                                        'upload_time': published_time_text,
                                        'thumbnail_url': thumbnail_url,
                                        'description': ""
                                    })
                    elif 'reelShelfRenderer' in item and 'items' in item['reelShelfRenderer']:
                        for short_item in item['reelShelfRenderer']['items']:
                            if 'shortsLockupViewModel' in short_item:
                                short_model = short_item['shortsLockupViewModel']
                                video_id = short_model.get('entityId', '').replace('shorts-shelf-item-', '')
                                accessibility_text = short_model.get('accessibilityText')
                                thumbnail_sources = short_model.get('thumbnail', {}).get('sources', [])
                                thumbnail_url = thumbnail_sources[0]['url'] if thumbnail_sources else None
                                view_match = None
                                title = None
                                if accessibility_text:
                                    parts = accessibility_text.split(', ')
                                    if len(parts) > 1 and 'views' in parts[-1]:
                                        view_match = parts[-1].strip()
                                        title = ', '.join(parts[:-1]).split(' - play Short')[0].strip()
                                    elif ' - play Short' in accessibility_text:
                                        title = accessibility_text.split(' - play Short')[0].strip()

                                if video_id and title:
                                    videos_data.append({
                                        'title': title,
                                        'video_id': video_id,
                                        'channel_name': None,
                                        'view_count': view_match,
                                        'duration': None,
                                        'upload_time': None,
                                        'thumbnail_url': thumbnail_url,
                                        'description': description
                                    })
    return videos_data


def parse_podcast_details(data):
    videos = []
    try:
        # Navigate through the JSON structure to find videoRenderer data.  This
        # structure is based on the provided JSON, and may need to be adapted
        # for different YouTube responses.
        contents = data.get("contents", {})
        two_column_browse_results_renderer = contents.get("twoColumnBrowseResultsRenderer", {})
        tabs = two_column_browse_results_renderer.get("tabs", [])

        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            content = tab_renderer.get("content", {})
            rich_grid_renderer = content.get("richGridRenderer", {})
            video_contents = rich_grid_renderer.get("contents", [])

            for item in video_contents:
                rich_item_renderer = item.get("richItemRenderer", {})
                if rich_item_renderer:  # Check if it is not None
                    video_renderer = rich_item_renderer.get("content", {}).get("videoRenderer", {})
                else:
                    continue  # if rich_item_renderer is None, skip this iteration

                if video_renderer:
                    # Extract the desired information.  Use .get() with default
                    # values to handle missing keys gracefully.
                    video_id = video_renderer.get("videoId")
                    title_runs = video_renderer.get("title", {}).get("runs", [])
                    title = "".join(run.get("text", "") for run in title_runs)
                    description_snippet_runs = video_renderer.get("descriptionSnippet", {}).get("runs", [])
                    description = "".join(run.get("text", "") for run in description_snippet_runs)
                    # Use the simpler viewCountText
                    view_count_text = int(
                        video_renderer.get("viewCountText", {}).get("simpleText", "0 ").split(" ")[0].replace(",", ""))
                    published_time_text = video_renderer.get("publishedTimeText", {}).get("simpleText", "N/A")
                    # Extract the channel name
                    long_byline_text_runs = video_renderer.get("longBylineText", {}).get("runs", [])
                    channel_name = ""
                    if long_byline_text_runs:
                        channel_name = long_byline_text_runs[0].get("text", "N/A")

                    # Extract the duration.
                    length_text = video_renderer.get("lengthText", {}).get("simpleText", "N/A")

                    # Extract thumbnail URLs
                    thumbnails = video_renderer.get("thumbnail", {}).get("thumbnails", [])
                    thumbnail_urls = [thumb.get("url") for thumb in thumbnails]

                    video_info = {
                        "video_id": video_id,
                        "title": title,
                        "description": description,
                        "view_count": view_count_text,
                        "published_time": published_time_text,
                        "channel_name": channel_name,
                        "duration": length_text,
                        "thumbnail_urls": thumbnail_urls,
                    }
                    videos.append(video_info)
    except KeyError as e:
        print(f"Error: Key not found in JSON data: {e}")
        return []  # Return an empty list in case of a KeyError

    return videos
