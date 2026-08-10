"""
LLM summarization service using Groq and Gemini APIs.
FIXED: Updated Gemini model names and added fallback mechanism.
"""
import logging
from typing import List, Any, Optional
from django.conf import settings
from apps.utils.http_client import HTTPClient, APIError

logger = logging.getLogger(__name__)


class Summarizer:
    """
    LLM-powered text summarization using Groq (primary) and Gemini (fallback).
    """
    
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    SYSTEM_PROMPT = """You are an expert research analyst. Your task is to synthesize information from multiple sources into a comprehensive, well-structured summary.

Follow these guidelines:
1. Identify the main themes and key findings
2. Present facts with clear attribution
3. Group related information thematically
4. Highlight significant developments or trends
5. Maintain objectivity and accuracy
6. Use Markdown formatting with clear headings

Structure your response as:
## Summary
[Comprehensive overview]

## Key Findings
- [Finding 1]
- [Finding 2]
...

## Sources Overview
[Brief overview of source quality and coverage]

## Final Insight
[Forward-looking conclusion or recommendation]"""
    
    # List of available Gemini models to try in order
    GEMINI_MODELS = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    def __init__(self):
        self.groq_key = settings.GROQ_API_KEY
        self.gemini_key = settings.GOOGLE_API_KEY
        
        self.groq_client = HTTPClient(base_url=self.GROQ_BASE_URL, timeout=60, max_retries=2)
        self.gemini_client = HTTPClient(base_url=self.GEMINI_BASE_URL, timeout=60, max_retries=2)
    
    def summarize(
        self,
        text: str,
        query: str = "",
        model: str = "groq"
    ) -> str:
        """
        Summarize text using LLM.
        
        Args:
            text: Text to summarize
            query: Original research query for context
            model: 'groq' or 'gemini'
            
        Returns:
            Markdown-formatted summary
        """
        if not text or len(text.strip()) == 0:
            return "No content to summarize."
        
        user_prompt = f"Research Query: {query}\n\nContent to summarize:\n\n{text}"
        
        if model == "groq" and self.groq_key:
            try:
                return self._summarize_groq(user_prompt)
            except APIError as e:
                logger.warning(f"Groq failed: {e}. Trying Gemini fallback...")
                if self.gemini_key:
                    return self._summarize_gemini(user_prompt)
                raise
        elif model == "gemini" and self.gemini_key:
            return self._summarize_gemini(user_prompt)
        else:
            raise ValueError(f"No API key available for model: {model}")
    
    def summarize_chunks(
        self,
        chunks: List[Any],
        query: str = "",
        model: str = "groq"
    ) -> str:
        """
        Summarize multiple chunks by summarizing each then merging.
        """
        if not chunks:
            return "No content to summarize."
        
        if len(chunks) == 1:
            return self.summarize(chunks[0].content, query, model)
        
        partial_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}...")
            partial = self.summarize(chunk.content, query, model)
            partial_summaries.append(f"### Source {i+1} ({chunk.source_title})\n{partial}")
        
        merged_text = "\n\n".join(partial_summaries)
        merge_prompt = f"Research Query: {query}\n\nSynthesize these partial summaries into a cohesive final report:\n\n{merged_text}"
        
        logger.info("Merging partial summaries...")
        return self.summarize(merge_prompt, query, model)
    
    def _summarize_groq(self, prompt: str) -> str:
        """Use Groq API with Llama 3.3 70B."""
        headers = {
            "Authorization": f"Bearer {self.groq_key}"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 4096,
        }
        
        response = self.groq_client.post("/chat/completions", data=payload, headers=headers)
        content = response['choices'][0]['message']['content']
        logger.info("Groq summarization complete")
        return content
    
    def _summarize_gemini(self, prompt: str) -> str:
        """
        Use Google Gemini API as fallback.
        Tries multiple model names in case one is not available.
        """
        headers = {
            "x-goog-api-key": self.gemini_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": self.SYSTEM_PROMPT + "\n\n" + prompt}]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4096,
            }
        }
        
        last_error = None
        
        # Try each model in order
        for model_name in self.GEMINI_MODELS:
            try:
                url = f"/models/{model_name}:generateContent"
                logger.info(f"Attempting Gemini with model: {model_name}")
                
                response = self.gemini_client.post(url, data=payload, headers=headers)
                
                # Check if response has the expected structure
                if 'candidates' in response and len(response['candidates']) > 0:
                    if 'content' in response['candidates'][0]:
                        parts = response['candidates'][0]['content'].get('parts', [])
                        if parts and 'text' in parts[0]:
                            content = parts[0]['text']
                            logger.info(f"Gemini summarization complete with {model_name}")
                            return content
                
                # If we got here, the response structure was unexpected
                logger.warning(f"Unexpected response structure from {model_name}: {response}")
                continue
                
            except APIError as e:
                last_error = e
                logger.warning(f"Gemini {model_name} failed: {e}")
                
                # Check if it's a model not found error
                if "not found" in str(e).lower():
                    continue
                # If it's a rate limit or other error, try next model
                elif "rate limit" in str(e).lower():
                    logger.warning("Rate limit hit, waiting before next attempt...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    # Other errors - try next model anyway
                    continue
        
        # If all models failed, try one more time with gemini-1.5-flash as last resort
        try:
            logger.warning("All models failed, trying gemini-1.5-flash as last resort...")
            url = "/models/gemini-1.5-flash:generateContent"
            response = self.gemini_client.post(url, data=payload, headers=headers)
            content = response['candidates'][0]['content']['parts'][0]['text']
            logger.info("Gemini summarization complete with gemini-1.5-flash (last resort)")
            return content
        except Exception as e:
            logger.error(f"All Gemini models failed. Last error: {e}")
            raise APIError(f"All Gemini models failed: {last_error or e}") from last_error