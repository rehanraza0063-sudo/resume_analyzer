"""
config.py

Optional AI integration switch.

By default AI_PROVIDER is "none", which means every endpoint in app.py
uses the local, rule-based logic in analyzer.py / resume_parser.py.
The whole app is fully functional this way — no API key required.

To later plug in a real AI API:
1. Set AI_PROVIDER to something other than "none" (e.g. "anthropic").
2. Set AI_API_KEY via an environment variable (never hard-code it here).
3. In app.py, branch on `AI_PROVIDER != "none"` at the top of whichever
   endpoint you want to upgrade, and call your AI provider there,
   falling back to the existing rule-based function on any error.
"""

import os

AI_PROVIDER = os.environ.get("AI_PROVIDER", "none")
AI_API_KEY = os.environ.get("AI_API_KEY", "")

MAX_UPLOAD_SIZE_MB = 5
ALLOWED_EXTENSIONS = {"pdf", "docx"}
