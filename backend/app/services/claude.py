import json
import re
import httpx
from fastapi import HTTPException
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_API_URL, ANTHROPIC_MODEL

async def generate_book_via_claude(prompt: str, uploaded_files_context: str = "") -> dict:
    system_prompt = """You are Inkwell AI, a creative book generation assistant. When given a book idea, generate a complete,
engaging, illustrated book outline with:
1. A compelling title
2. A brief synopsis (2-3 sentences)
3. Exactly 3 chapters, each with:
   - A chapter title
   - Chapter content (4-6 paragraphs of vivid, engaging prose)
   - An image description for an AI-generated illustration

Format your response as JSON exactly like this:
{
  "title": "Book Title",
  "synopsis": "Brief synopsis...",
  "chapters": [
    {
      "number": 1,
      "title": "Chapter Title",
      "content": "Full chapter prose...",
      "imageDescription": "Detailed visual description for illustration"
    }
  ]
}
Only respond with valid JSON. No preamble or extra text."""

    user_content = prompt
    if uploaded_files_context:
        user_content += f"\n\nReference files uploaded by user:\n{uploaded_files_context}"

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4000,  # Claude sonnet is powerful, allow larger token response for full book
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_content}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=f"Claude API returned error ({response.status_code}): {response.text}"
                )
            
            resp_data = response.json()
            raw_text = resp_data["content"][0]["text"].strip()
            
            # Clean up potential markdown formatting wrapping the JSON
            raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"```\s*$", "", raw_text, flags=re.IGNORECASE)
            raw_text = raw_text.strip()
            
            book_json = json.loads(raw_text)
            
            # Validate basic format
            if not book_json.get("title") or not book_json.get("chapters"):
                raise ValueError("JSON missing required fields 'title' or 'chapters'")
                
            return book_json

        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Claude API connection failed: {exc}")
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to parse Claude JSON response: {exc}. Response text: {raw_text}")
        except (KeyError, IndexError, ValueError) as exc:
            raise HTTPException(status_code=502, detail=f"Invalid format returned from Claude: {exc}")
