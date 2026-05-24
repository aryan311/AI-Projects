from core.models import NormalizeResult, SummaryResult, ArticleSummary
from core.a2a import Executor
import re

def clean_html(raw_html: str) -> str:
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def run_summary(input_data: NormalizeResult) -> SummaryResult:
    summaries = []
    
    for article in input_data.articles:
        text = clean_html(article.content)
        # Fake summarizer: truncate to 150 characters and prepend "Summary: "
        if len(text) > 150:
            text = text[:147] + "..."
        summary_text = f"Summary: {text}"
        
        summaries.append(ArticleSummary(
            url=article.url,
            summary=summary_text
        ))
        
    return SummaryResult(
        run_id=input_data.run_id,
        agent_name="SummaryAgent",
        summaries=summaries
    )

summary_executor = Executor(
    name="SummaryAgent",
    func=run_summary,
    input_type=NormalizeResult
)
