document.getElementById('generate-btn').addEventListener('click', async () => {
    const topic = document.getElementById('topic-input').value.trim();
    if (!topic) return;

    const btn = document.getElementById('generate-btn');
    const workflowSection = document.getElementById('workflow-section');
    const resultsSection = document.getElementById('results-section');
    const timeline = document.getElementById('timeline');
    const briefingContent = document.getElementById('briefing-content');

    btn.disabled = true;
    btn.textContent = 'Executing...';
    
    workflowSection.style.display = 'block';
    resultsSection.style.display = 'none';
    timeline.innerHTML = '';
    
    // Add initial step
    addTimelineItem({
        agent: 'System',
        status: 'pending',
        details: `Initializing pipeline for topic: "${topic}"`
    }, 0);

    try {
        const response = await fetch('/api/run_pipeline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ topic: topic })
        });

        const data = await response.json();

        if (data.timeline) {
            // Re-render timeline with actual results, with stagger animation
            timeline.innerHTML = '';
            data.timeline.forEach((item, index) => {
                let details = '';
                if (item.agent === 'ResearchAgent') details = `Found ${item.articles_found} articles`;
                else if (item.agent === 'NormalizeAgent') details = `Normalized ${item.articles_normalized} articles`;
                else if (item.agent === 'SummaryAgent') details = `Generated ${item.summaries_generated} summaries`;
                else if (item.agent === 'EditorAgent') details = `Compiled briefing (${item.briefing_length} chars)`;
                else if (item.error) details = `Error: ${item.error}`;
                
                setTimeout(() => {
                    addTimelineItem({
                        agent: item.agent,
                        status: item.status,
                        details: details
                    }, index);
                }, index * 600); // Stagger the rendering
            });

            // Show results after timeline completes
            setTimeout(() => {
                if (data.briefing && data.briefing.content) {
                    resultsSection.style.display = 'block';
                    briefingContent.innerHTML = marked.parse(data.briefing.content);
                }
                btn.disabled = false;
                btn.textContent = 'Generate Briefing';
            }, data.timeline.length * 600 + 500);
        } else {
            throw new Error("Pipeline failed");
        }

    } catch (error) {
        console.error('Error running pipeline:', error);
        addTimelineItem({
            agent: 'Error',
            status: 'failed',
            details: 'Failed to connect to the backend server.'
        }, timeline.children.length);
        
        btn.disabled = false;
        btn.textContent = 'Generate Briefing';
    }
});

function addTimelineItem(data, index) {
    const timeline = document.getElementById('timeline');
    const div = document.createElement('div');
    div.className = `timeline-item ${data.status === 'success' ? 'success' : ''}`;
    // Inline style delay handled by setTimeout above, but keeping structure clean
    
    div.innerHTML = `
        <h3>${data.agent}</h3>
        <p>${data.details}</p>
    `;
    
    timeline.appendChild(div);
}
