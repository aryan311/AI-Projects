from core.models import ResearchResult, NormalizeResult, NormalizedArticle
from core.a2a import Executor
from datetime import datetime
import dateutil.parser # Might not be available, fallback to simple parsing or just None
from email.utils import parsedate_to_datetime

def run_normalize(input_data: ResearchResult) -> NormalizeResult:
    normalized = []
    seen_urls = set()
    
    for article in input_data.articles:
        if article.link in seen_urls:
            continue
        seen_urls.add(article.link)
        
        pub_date = None
        if article.published:
            try:
                pub_date = parsedate_to_datetime(article.published)
            except Exception:
                pass
                
        # Clean up title by removing "- Publisher" if present (common in Google News)
        title = article.title
        source = "Unknown"
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0]
            source = parts[1]
            
        normalized.append(NormalizedArticle(
            title=title,
            url=article.link,
            published_date=pub_date,
            content=article.summary or "No summary available",
            source=source
        ))
        
    return NormalizeResult(
        run_id=input_data.run_id,
        agent_name="NormalizeAgent",
        articles=normalized
    )

normalize_executor = Executor(
    name="NormalizeAgent",
    func=run_normalize,
    input_type=ResearchResult
)
