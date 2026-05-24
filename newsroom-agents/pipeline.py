from fastapi import APIRouter
from core.a2a import Client, AgentCard
from core.models import TopicRequest, ResearchResult, NormalizeResult, SummaryResult, Briefing
import uuid

router = APIRouter()

cards = {
    "research": AgentCard(name="ResearchAgent", description="Fetches news", url="http://localhost:8000/agents/research"),
    "normalize": AgentCard(name="NormalizeAgent", description="Normalizes articles", url="http://localhost:8000/agents/normalize"),
    "summary": AgentCard(name="SummaryAgent", description="Summarizes text", url="http://localhost:8000/agents/summary"),
    "editor": AgentCard(name="EditorAgent", description="Creates briefing", url="http://localhost:8000/agents/editor"),
}

@router.post("/api/run_pipeline")
async def run_pipeline(request: dict):
    topic = request.get("topic", "AI")
    run_id = str(uuid.uuid4())
    
    timeline = []
    
    try:
        # Step 1: Research
        topic_req = TopicRequest(run_id=run_id, agent_name="Client", topic=topic)
        research_raw = await Client.execute_agent(cards["research"], topic_req)
        research_res = ResearchResult.model_validate(research_raw)
        timeline.append({"agent": "ResearchAgent", "status": "success", "articles_found": len(research_res.articles)})
        
        # Step 2: Normalize
        normalize_raw = await Client.execute_agent(cards["normalize"], research_res)
        normalize_res = NormalizeResult.model_validate(normalize_raw)
        timeline.append({"agent": "NormalizeAgent", "status": "success", "articles_normalized": len(normalize_res.articles)})
        
        # Step 3: Summary
        summary_raw = await Client.execute_agent(cards["summary"], normalize_res)
        summary_res = SummaryResult.model_validate(summary_raw)
        timeline.append({"agent": "SummaryAgent", "status": "success", "summaries_generated": len(summary_res.summaries)})
        
        # Step 4: Editor
        editor_raw = await Client.execute_agent(cards["editor"], summary_res)
        editor_res = Briefing.model_validate(editor_raw)
        timeline.append({"agent": "EditorAgent", "status": "success", "briefing_length": len(editor_res.content)})
        
        return {
            "run_id": run_id,
            "topic": topic,
            "timeline": timeline,
            "briefing": editor_res.model_dump()
        }
        
    except Exception as e:
        timeline.append({"agent": "Error", "status": "failed", "error": str(e)})
        return {
            "run_id": run_id,
            "topic": topic,
            "timeline": timeline,
            "error": str(e)
        }
