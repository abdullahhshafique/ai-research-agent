"""
Research pipeline executor that works with the job queue.
"""

import os
import time
import logging
from typing import Callable, Optional
from django.conf import settings

from .search import SearchAgent
from .summarizer import Summarizer
from .chunker import TextChunker
from apps.reports.services.report_builder import ReportBuilder
from apps.reports.services.pdf_engine import PDFExporter
from apps.reports.models import GeneratedReport

logger = logging.getLogger(__name__)


def execute_research_pipeline(query, user, _progress_callback=None):
    """
    Main research pipeline executed by worker threads.
    _progress_callback is injected by the job queue.
    """
    def progress(pct, stage, msg):
        if _progress_callback:
            _progress_callback(pct, stage, msg)
    
    start_time = time.time()
    
    # Stage 1: Search with live source preview
    progress(5, "search", "Initiating web search...")
    search_agent = SearchAgent()
    sources = search_agent.search(
        query=query.query_text,
        max_results=query.max_results,
        search_depth=query.search_depth,
    )

    # Send source preview update
    for i, source in enumerate(sources):
        preview_msg = f"Found: {source.title} ({source.domain})"
        progress(10 + i * 3, "search", preview_msg)
        time.sleep(0.2)

    progress(25, "search", f"Found {len(sources)} sources")
    
    # Stage 2: Content retrieval & chunking (30-50%)
    progress(30, "chunk", "Processing source content...")
    
    # Save sources to database
    from apps.research.models import Source as SourceModel
    sources_data = []
    for i, source in enumerate(sources):
        SourceModel.objects.create(
            query=query,
            url=source.url,
            title=source.title,
            content=source.content[:5000],
            relevance_score=source.score,
            domain=source.domain
        )
        sources_data.append({
            'url': source.url,
            'title': source.title,
            'domain': source.domain,
            'score': source.score,
            'content': source.content
        })
    
    # Chunk content for summarization
    chunker = TextChunker()
    all_content = []
    for i, source in enumerate(sources_data):
        content = source.get('content', '')
        if len(content) > 60000:
            chunks = chunker.chunk_text(content, chunk_size=4000, overlap=200)
            all_content.extend(chunks)
        else:
            all_content.append(content)
        progress(30 + (i+1)/len(sources_data)*15, "chunk", f"Processed source {i+1}/{len(sources_data)}")
    
    # Stage 3: Summarization (50-80%)
    progress(50, "summarize", "Analyzing content with AI...")
    summarizer = Summarizer()
    
    # Build chunks for summarizer
    chunk_objects = []
    for i, content in enumerate(all_content):
        from .chunker import TextChunk
        chunk_objects.append(TextChunk(
            content=content if isinstance(content, str) else content.content,
            index=i,
            source_url=sources_data[min(i, len(sources_data)-1)]['url'],
            source_title=sources_data[min(i, len(sources_data)-1)]['title']
        ))
    
    summary_text = summarizer.summarize_chunks(
        chunks=chunk_objects,
        query=query.query_text,
        model=query.llm_model
    )
    
    # Extract sections from summary
    summary = summary_text
    insight = ""
    if "## Final Insight" in summary_text:
        parts = summary_text.split("## Final Insight")
        summary = parts[0].strip()
        insight = parts[1].strip() if len(parts) > 1 else ""
    
    progress(80, "summarize", "Analysis complete")
    
    # Stage 4: Report generation (80-90%)
    progress(80, "report", "Building structured report...")
    
    query.summary = summary
    query.final_insight = insight
    query.raw_sources = sources_data
    query.save()
    
    progress(90, "report", "Report structured")
    
    # Stage 5: PDF Generation (90-100%)
    progress(90, "pdf", "Generating PDF...")
    
    # Build report markdown from the saved query state
    report_md = ReportBuilder.from_research_query(query)
    
    # Get user's logo if available
    logo_url = None
    if hasattr(user, 'profile') and user.profile.logo_url:
        logo_url = user.profile.logo_url
    
    # Generate PDF
    filename = f"research_{query.id}_{query.query_text[:30].replace(' ', '_')}.pdf"
    output_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    exporter = PDFExporter()
    exporter.export(
        markdown_content=report_md,
        research=query,
        accent_color=user.profile.accent_color if hasattr(user, 'profile') else "#3B82F6",
        logo_url=logo_url,
        output_path=output_path
    )
    
    # Create GeneratedReport record
    report = GeneratedReport.objects.create(
        query=query,
        pdf_file_path=output_path,
        file_size_bytes=os.path.getsize(output_path),
        cover_title=f"Research: {query.query_text[:50]}"
    )
    
    progress(100, "complete", "Research complete!")
    
    # Update final stats
    query.status = 'completed'
    query.processing_time_ms = int((time.time() - start_time) * 1000)
    query.save()
    
    return {"query_id": query.id, "report_id": report.id}