from crewai import Agent, Task
from crewai_tools import ScrapeWebsiteTool, YoutubeVideoSearchTool


def build_video_research_task(agent: Agent, yt_tool: YoutubeVideoSearchTool) -> Task:
    return Task(
        description=(
            "Identify the video about {topic}. "
            "Use the YouTube video search tool to get detailed information from the video transcript."
        ),
        expected_output="A comprehensive three-paragraph report based on the topic of the video",
        agent=agent,
        tools=[yt_tool],
    )


def build_video_writing_task(agent: Agent, yt_tool: YoutubeVideoSearchTool) -> Task:
    return Task(
        description=(
            "Using the research from the previous task and the YouTube video search tool, "
            "summarize the key points about {topic} from the video."
        ),
        expected_output="A clear summary of the YouTube video content on {topic} in markdown format",
        agent=agent,
        tools=[yt_tool],
        async_execution=False,
        markdown=True,
    )


def build_website_research_task(agent: Agent, web_tool: ScrapeWebsiteTool) -> Task:
    return Task(
        description=(
            "Analyze the website content about {topic}. "
            "Use the website scrape tool to gather detailed information from the page."
        ),
        expected_output="A comprehensive three-paragraph report based on the website content",
        agent=agent,
        tools=[web_tool],
    )


def build_website_writing_task(agent: Agent, web_tool: ScrapeWebsiteTool) -> Task:
    return Task(
        description=(
            "Using the research from the previous task, "
            "summarize the key points about {topic} from the website."
        ),
        expected_output="A clear summary of the website content on {topic} in markdown format",
        agent=agent,
        tools=[web_tool],
        async_execution=False,
        markdown=True,
    )
