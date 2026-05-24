from core.models import (
    BaseMessage, TopicRequest, Article, ResearchResult, 
    NormalizedArticle, NormalizeResult, ArticleSummary, 
    SummaryResult, Briefing
)
from datetime import datetime

def test_base_message_defaults():
    msg = BaseMessage(agent_name="TestAgent")
    assert msg.agent_name == "TestAgent"
    assert msg.run_id is not None
    assert isinstance(msg.run_id, str)
    assert isinstance(msg.timestamp, datetime)

def test_topic_request():
    req = TopicRequest(agent_name="Client", topic="AI")
    assert req.topic == "AI"
    assert req.agent_name == "Client"

def test_research_result():
    article = Article(title="Test", link="http://example.com")
    res = ResearchResult(agent_name="Research", topic="AI", articles=[article])
    assert len(res.articles) == 1
    assert res.articles[0].title == "Test"

def test_briefing():
    b = Briefing(
        agent_name="Editor",
        topic="AI",
        content="This is the final briefing.",
        sources=["http://example.com"]
    )
    assert b.content == "This is the final briefing."
    assert len(b.sources) == 1
