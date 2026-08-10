"""
Report builder service -- assembles Markdown report content from research data.
Generates rich, structured Markdown with proper hierarchy and formatting.
"""
from apps.research.models import ResearchQuery


class ReportBuilder:
    """
    Builds structured Markdown content from research queries.

    Produces professional reports with:
    - Executive summary with proper formatting
    - Detailed source citations with URLs and relevance scores
    - Key insights and conclusions
    - Structured metadata
    """

    def __init__(self):
        self.summary = ""
        self.insight = ""
        self.sources = []
        self.metadata = {}

    def add_summary(self, summary: str):
        self.summary = summary
        return self

    def add_sources(self, sources: list):
        self.sources = sources
        return self

    def add_insight(self, insight: str):
        self.insight = insight
        return self

    def add_metadata(self, **kwargs):
        self.metadata.update(kwargs)
        return self

    def build(self) -> str:
        """Build the complete Markdown report."""
        lines = []

        # Report Header
        lines.append("# Research Report")
        lines.append("")

        # Executive Summary
        if self.summary:
            lines.append("## Executive Summary")
            lines.append("")
            if self.summary.strip().startswith("#"):
                # If summary already has headers, use it as-is
                lines.append(self.summary.strip())
            else:
                lines.append(self.summary.strip())
            lines.append("")
            lines.append("---")
            lines.append("")

        # Sources Section
        if self.sources:
            lines.append("## Sources & References")
            lines.append("")
            lines.append(f"*Total sources analyzed: {len(self.sources)}*")
            lines.append("")

            for i, source in enumerate(self.sources, 1):
                title = source.get("title", "Untitled")
                domain = source.get("domain", "")
                score = source.get("score", 0)
                url = source.get("url", "")

                # Create rich source entry
                lines.append(f"### {i}. {title}")
                if domain:
                    lines.append(f"**Domain:** {domain}")
                if url:
                    lines.append(f"**URL:** [{url}]({url})")
                lines.append(f"**Relevance Score:** {score:.2f}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Key Insights
        if self.insight:
            lines.append("## Key Insights & Conclusions")
            lines.append("")
            lines.append(self.insight.strip())
            lines.append("")
            lines.append("---")
            lines.append("")

        # Metadata Footer
        if self.metadata:
            lines.append("## Report Metadata")
            lines.append("")
            for key, value in self.metadata.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_research_query(cls, research: ResearchQuery) -> str:
        """
        Build a report from a ResearchQuery model instance.

        Args:
            research: ResearchQuery instance with summary, sources, and insights

        Returns:
            Complete Markdown report string
        """
        builder = cls()

        # Add summary
        if research.summary:
            builder.add_summary(research.summary)

        # Add final insight
        if research.final_insight:
            builder.add_insight(research.final_insight)

        # Collect sources with full metadata
        sources = []
        if hasattr(research, "sources"):
            for source in research.sources.all():
                sources.append({
                    "url": source.url,
                    "title": source.title or "Untitled",
                    "domain": source.domain or "",
                    "score": source.relevance_score or 0,
                })
        builder.add_sources(sources)

        # Add metadata
        builder.add_metadata(
            query=research.query_text,
            search_depth=getattr(research, "search_depth", "standard"),
            llm_model=getattr(research, "llm_model", "default"),
            status=research.status,
        )

        return builder.build()