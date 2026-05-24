import feedparser
import urllib.parse
from core.models import TopicRequest, ResearchResult, Article
from core.a2a import Executor

def run_research(input_data: TopicRequest) -> ResearchResult:
    # Google News RSS for the topic
    encoded_topic = urllib.parse.quote(input_data.topic)
    rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(rss_url)
    articles = []
    
    # Limit to top 5 articles to keep processing fast
    for entry in feed.entries[:5]:
        articles.append(Article(
            title=entry.get('title', 'No Title'),
            link=entry.get('link', ''),
            published=entry.get('published', None),
            summary=entry.get('summary', None)
        ))
    
    return ResearchResult(
        run_id=input_data.run_id,
        agent_name="ResearchAgent",
        topic=input_data.topic,
        articles=articles
    )

research_executor = Executor(
    name="ResearchAgent",
    func=run_research,
    input_type=TopicRequest
)
