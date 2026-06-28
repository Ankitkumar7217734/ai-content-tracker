import os
import re

from crewai import Agent, Crew, LLM, Process

from crew.tasks import (
    build_video_research_task,
    build_video_writing_task,
    build_website_research_task,
    build_website_writing_task,
)
from crew.tools import build_website_tool, build_youtube_tool


def topic_to_filename(topic: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", topic.strip().lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return f"{slug}.md" if slug else "writing_output.md"


def _build_llm(openai_api_key: str) -> LLM:
    os.environ["OPENAI_API_KEY"] = openai_api_key
    return LLM(model="openai/gpt-4o")


def _build_agents(llm: LLM, tools: list) -> tuple[Agent, Agent]:
    researcher = Agent(
        role="Senior Content Researcher",
        goal="get the relevant content for the topic {topic} using the available search tools",
        verbose=True,
        memory=True,
        backstory="Expert in understanding videos and web content on AI, Data Science, and Gen AI",
        tools=tools,
        llm=llm,
        allow_delegation=True,
    )
    writer = Agent(
        role="Technical Writer",
        goal="write engaging tech stories about {topic} based on the researched content",
        verbose=True,
        memory=True,
        backstory=(
            "You craft engaging narratives that are captivating and educative, "
            "bringing complex topics to light in an accessible manner."
        ),
        tools=tools,
        llm=llm,
        allow_delegation=True,
    )
    return researcher, writer


def run_video_crew(*, openai_api_key: str, video_url: str, topic: str) -> str:
    llm = _build_llm(openai_api_key)
    yt_tool = build_youtube_tool(video_url)
    researcher, writer = _build_agents(llm, [yt_tool])

    crew = Crew(
        agents=[researcher, writer],
        tasks=[
            build_video_research_task(researcher, yt_tool),
            build_video_writing_task(writer, yt_tool),
        ],
        process=Process.sequential,
        memory=True,
        cache=True,
        max_rpm=100,
        share_crew=False,
    )
    result = crew.kickoff(inputs={"topic": topic})
    return str(result.raw)


def run_website_crew(*, openai_api_key: str, website_url: str, topic: str) -> str:
    llm = _build_llm(openai_api_key)
    web_tool = build_website_tool(website_url)
    researcher, writer = _build_agents(llm, [web_tool])

    crew = Crew(
        agents=[researcher, writer],
        tasks=[
            build_website_research_task(researcher, web_tool),
            build_website_writing_task(writer, web_tool),
        ],
        process=Process.sequential,
        memory=True,
        cache=True,
        max_rpm=100,
        share_crew=False,
    )
    result = crew.kickoff(inputs={"topic": topic})
    return str(result.raw)
