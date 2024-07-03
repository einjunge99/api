import re


# TODO: handle invalid urls
def get_youtube_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)

    return match.group(1)
