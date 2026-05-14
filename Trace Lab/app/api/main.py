"""
TraceLab — FastAPI application entry point.

Configures:
- SQLite run store initialization
- OpenTelemetry SDK + auto-instrumentation (FastAPI, httpx, sqlite3)
- API routes for runs and workflow execution
- Simple HTML dashboard at /
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.store.database import init_db, close_db
from app.core.telemetry import setup_telemetry, shutdown_telemetry
from app.api.routes.runs import router as runs_router
from app.api.routes.workflows import router as workflows_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: init DB + telemetry on startup, cleanup on shutdown."""
    logger.info("Starting TraceLab...")
    await init_db()
    logger.info("SQLite run store initialized at: %s", settings.sqlite_db_path)

    setup_telemetry(app)
    logger.info("OpenTelemetry configured (service=%s)", settings.otel_service_name)

    yield

    shutdown_telemetry()
    await close_db()
    logger.info("TraceLab shutdown complete")


app = FastAPI(
    title="TraceLab",
    description="OpenTelemetry-based observability layer for Python AI workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# Include API routers
app.include_router(runs_router)
app.include_router(workflows_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "OK", "service": "tracelab"}


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the TraceLab dashboard."""
    return DASHBOARD_HTML


# ---------------------------------------------------------------------------
# Inline Dashboard HTML
# ---------------------------------------------------------------------------
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TraceLab — AI Workflow Observability</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-card: #1a2233;
            --bg-card-hover: #1f2b3f;
            --border: #2a3548;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --accent-purple: #8b5cf6;
            --gradient-primary: linear-gradient(135deg, #3b82f6, #8b5cf6);
            --gradient-success: linear-gradient(135deg, #10b981, #06b6d4);
            --gradient-error: linear-gradient(135deg, #ef4444, #f59e0b);
            --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.15);
            --radius: 12px;
            --radius-sm: 8px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.04) 0%, transparent 60%);
            pointer-events: none;
            z-index: 0;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 24px;
            position: relative;
            z-index: 1;
        }

        .header {
            padding: 32px 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 36px;
            height: 36px;
            background: var(--gradient-primary);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: var(--shadow-glow);
        }
        .logo h1 {
            font-size: 22px;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header-links {
            display: flex;
            gap: 10px;
        }
        .header-links a {
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-jaeger { background: rgba(139, 92, 246, 0.15); color: var(--accent-purple); border: 1px solid rgba(139, 92, 246, 0.3); }
        .btn-docs { background: rgba(59, 130, 246, 0.15); color: var(--accent-blue); border: 1px solid rgba(59, 130, 246, 0.3); }

        /* Main Query Input Section */
        .query-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 32px;
            margin-bottom: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border-top: 2px solid var(--accent-blue);
        }
        .query-box h2 {
            font-size: 18px;
            margin-bottom: 20px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .input-group {
            position: relative;
            margin-bottom: 20px;
        }
        .input-group textarea {
            width: 100%;
            padding: 18px 20px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 16px;
            min-height: 100px;
            resize: vertical;
            transition: all 0.2s;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }
        .input-group textarea:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }
        .workflow-select {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            font-size: 14px;
            cursor: pointer;
        }
        .btn-execute {
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: var(--radius-sm);
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }
        .btn-execute:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }
        .btn-execute:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Results Display */
        #result-container {
            display: none;
            animation: slideUp 0.4s ease;
            margin-top: 24px;
        }
        .result-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 24px;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.success { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
        .badge.failed { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }

        .result-body {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 13px;
            line-height: 1.6;
            color: var(--accent-cyan);
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            background: #000;
            padding: 16px;
            border-radius: var(--radius-sm);
        }

        /* Runs List */
        .runs-section {
            margin-top: 48px;
        }
        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .section-title h3 { font-size: 18px; color: var(--text-secondary); }
        .btn-refresh {
            background: transparent;
            color: var(--accent-blue);
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 6px 14px;
            border-radius: var(--radius-sm);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-refresh:hover { background: rgba(59, 130, 246, 0.1); }

        .run-list {
            display: grid;
            gap: 12px;
        }
        .run-item {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px 20px;
            display: grid;
            grid-template-columns: 80px 1fr 120px 100px 140px;
            align-items: center;
            transition: all 0.2s;
        }
        .run-item:hover {
            border-color: var(--accent-blue);
            transform: translateX(4px);
        }
        .run-status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            margin-right: 8px;
            display: inline-block;
        }
        .status-success { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
        .status-failed { background: var(--accent-red); box-shadow: 0 0 8px var(--accent-red); }
        .status-running { background: var(--accent-amber); box-shadow: 0 0 8px var(--accent-amber); }

        .run-workflow { font-weight: 600; font-size: 14px; }
        .run-question { color: var(--text-secondary); font-size: 13px; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 20px; }
        .run-time { font-size: 12px; color: var(--text-muted); font-family: monospace; }
        .trace-link { color: var(--accent-purple); text-decoration: none; font-size: 12px; font-weight: 500; }
        .trace-link:hover { text-decoration: underline; }

        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .loading-spinner {
            width: 18px; height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Stats */
        .stats-bar {
            display: flex;
            gap: 20px;
            margin-bottom: 24px;
        }
        .stat-item {
            font-size: 13px;
            color: var(--text-muted);
        }
        .stat-item span { color: var(--text-primary); font-weight: 600; margin-left: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">
                <div class="logo-icon">🔭</div>
                <h1>TraceLab</h1>
            </div>
            <div class="header-links">
                <a href="http://localhost:16686" target="_blank" class="btn-jaeger">🔍 Open Jaeger</a>
                <a href="/docs" target="_blank" class="btn-docs">📜 API Docs</a>
            </div>
        </header>

        <div class="stats-bar" id="stats-bar">
            <div class="stat-item">Total Runs <span id="stat-total">0</span></div>
            <div class="stat-item">Success <span id="stat-success" style="color:var(--accent-green)">0</span></div>
            <div class="stat-item">Failed <span id="stat-failed" style="color:var(--accent-red)">0</span></div>
        </div>

        <section class="query-box">
            <h2><span>⚡</span> Query Playground</h2>
            <div class="input-group">
                <textarea id="query-input" placeholder="Enter your natural language query (e.g., 'Show top 5 customers by revenue')"></textarea>
            </div>
            <div class="controls">
                <select id="workflow-mode" class="workflow-select">
                    <option value="querypilot">Success Mode (Normal)</option>
                    <option value="failing">Failure Mode (Test Observability)</option>
                </select>
                <button id="btn-run" class="btn-execute" onclick="runWorkflow()">
                    🚀 Execute Workflow
                </button>
            </div>

            <div id="result-container">
                <div class="result-card">
                    <div class="result-header">
                        <span id="result-badge" class="badge">SUCCESS</span>
                        <span id="result-trace-info" class="trace-link"></span>
                    </div>
                    <div id="result-display" class="result-body"></div>
                </div>
            </div>
        </section>

        <section class="runs-section">
            <div class="section-title">
                <h3>📜 Recent Traces</h3>
                <button class="btn-refresh" onclick="loadRuns()">Refresh List</button>
            </div>
            <div id="run-list" class="run-list">
                <!-- Runs loaded via JS -->
            </div>
        </section>
    </div>

    <script>
        async function loadRuns() {
            try {
                const resp = await fetch('/runs?limit=10');
                const data = await resp.json();
                renderRuns(data.runs);
                updateStats(data.runs);
            } catch (e) { console.error(e); }
        }

        function updateStats(runs) {
            const total = runs.length;
            const success = runs.filter(r => r.status === 'success').length;
            const failed = runs.filter(r => r.status === 'failed').length;
            document.getElementById('stat-total').textContent = total;
            document.getElementById('stat-success').textContent = success;
            document.getElementById('stat-failed').textContent = failed;
        }

        function renderRuns(runs) {
            const list = document.getElementById('run-list');
            if (!runs || runs.length === 0) {
                list.innerHTML = '<div style="text-align:center; padding: 40px; color: var(--text-muted)">No traces found. Run a query above!</div>';
                return;
            }
            list.innerHTML = runs.map(r => `
                <div class="run-item">
                    <div>
                        <span class="run-status-dot status-${r.status}"></span>
                        <span class="run-workflow">${r.workflow_name}</span>
                    </div>
                    <div class="run-question">${r.metadata?.question || 'No question'}</div>
                    <div class="run-time">${new Date(r.start_time).toLocaleTimeString()}</div>
                    <div>
                        <a href="http://localhost:16686/trace/${r.trace_id}" target="_blank" class="trace-link">View Trace</a>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); font-family: monospace;">${r.id.substring(0, 8)}...</div>
                </div>
            `).join('');
        }

        async function runWorkflow() {
            const input = document.getElementById('query-input');
            const btn = document.getElementById('btn-run');
            const mode = document.getElementById('workflow-mode').value;
            const resultContainer = document.getElementById('result-container');
            const resultDisplay = document.getElementById('result-display');
            const resultBadge = document.getElementById('result-badge');
            const resultTrace = document.getElementById('result-trace-info');

            if (!input.value.trim()) return;

            btn.disabled = true;
            btn.innerHTML = '<div class="loading-spinner"></div> Running...';
            resultContainer.style.display = 'none';

            try {
                const resp = await fetch('/workflow/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        workflow_name: mode,
                        question: input.value,
                        should_fail: mode === 'failing'
                    })
                });
                const data = await resp.json();

                resultContainer.style.display = 'block';
                resultBadge.className = `badge ${data.status}`;
                resultBadge.textContent = data.status.toUpperCase();
                resultTrace.innerHTML = `<a href="${data.jaeger_url}" target="_blank" class="trace-link">View in Jaeger (ID: ${data.trace_id.substring(0, 8)}...)</a>`;
                
                // Pretty print the result
                const displayData = data.status === 'success' ? data.result : { error: data.error };
                resultDisplay.textContent = JSON.stringify(displayData, null, 2);

                loadRuns();
            } catch (e) {
                console.error(e);
                alert('Execution failed. Check console.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🚀 Execute Workflow';
            }
        }

        loadRuns();
        setInterval(loadRuns, 15000);
    </script>
</body>
</html>"""
