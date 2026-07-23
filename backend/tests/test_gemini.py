from services.gemini_client import GeminiClient

client = GeminiClient()

response = client.generate(
    """
    Analyze this company:
    Google

    Return JSON:
    {
      "industry": "",
      "strengths": [],
      "weaknesses": []
    }
    """
)

print(response)