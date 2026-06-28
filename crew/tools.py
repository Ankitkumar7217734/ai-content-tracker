from crewai_tools import ScrapeWebsiteTool, YoutubeVideoSearchTool


def build_youtube_tool(video_url: str) -> YoutubeVideoSearchTool:
    return YoutubeVideoSearchTool(youtube_video_url=video_url)


def build_website_tool(website_url: str) -> ScrapeWebsiteTool:
    return ScrapeWebsiteTool(website_url=website_url)
