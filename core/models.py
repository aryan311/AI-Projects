from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class BaseMessage(BaseModel):
    run_id: str = Field(default_factory=generate_uuid)
    agent_name: str
    timestamp: datetime = Field(default_factory=get_utc_now)
    
    model_config = ConfigDict(populate_by_name=True)

class TopicRequest(BaseMessage):
    topic: str

class Article(BaseModel):
    title: str
    link: str
    published: Optional[str] = None
    summary: Optional[str] = None

class ResearchResult(BaseMessage):
    topic: str
    articles: List[Article]

class NormalizedArticle(BaseModel):
    title: str
    url: str
    published_date: Optional[datetime] = None
    content: str
    source: str

class NormalizeResult(BaseMessage):
    articles: List[NormalizedArticle]

class ArticleSummary(BaseModel):
    url: str
    summary: str

class SummaryResult(BaseMessage):
    summaries: List[ArticleSummary]

class Briefing(BaseMessage):
    topic: str
    content: str
    sources: List[str]
