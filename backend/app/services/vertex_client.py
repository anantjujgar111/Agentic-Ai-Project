from __future__ import annotations

import logging

from app.config import settings


logger = logging.getLogger(__name__)


class VertexTextClient:
    """Optional Gemini wrapper.

    The POC works without Vertex credentials by returning deterministic agent
    responses. Set USE_VERTEX=true after enabling Vertex AI in GCP to let Gemini
    polish responses.
    """

    def __init__(self) -> None:
        self.enabled = settings.use_vertex
        self._model = None

        if self.enabled:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                if not settings.gcp_project_id:
                    raise ValueError("GCP_PROJECT_ID is required when USE_VERTEX=true")

                vertexai.init(
                    project=settings.gcp_project_id,
                    location=settings.gcp_location,
                )
                self._model = GenerativeModel(settings.vertex_model)
            except Exception as exc:
                logger.warning("Vertex AI initialization failed; using deterministic responses: %s", exc)
                self.enabled = False
                self._model = None

    def polish(self, system_goal: str, draft: str) -> str:
        if not self.enabled or self._model is None:
            return draft

        prompt = f"""
You are a safe banking assistant for a proof of concept.
Goal: {system_goal}

Rewrite the draft answer in a concise, professional chat style.
Do not invent account data. Keep rupee amounts exactly as given.
If the draft contains a disclaimer, keep it.

Draft:
{draft}
"""
        try:
            response = self._model.generate_content(prompt)
            return getattr(response, "text", None) or draft
        except Exception as exc:
            logger.warning("Vertex AI response polishing failed; returning draft: %s", exc)
            return draft
