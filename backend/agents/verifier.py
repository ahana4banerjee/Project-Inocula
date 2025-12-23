import os
import requests
import urllib.parse
from agents.state import AgentState

def verifier_node(state: AgentState):
    """
    Queries the Wikipedia API to find factual context for the claim.
    Requires no API key or billing account.
    """
    # If it was a memory hit, we already know the answer
    if state.get("is_memory_hit"):
        return {}

    text = state["input_text"]
    # We take the first 150 characters to use as a search query
    query = text[:150] 
    
    new_reasons = []
    verification_context = ""
    wiki_url = ""

    try:
        # Step 1: Search Wikipedia for the most relevant page title
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&origin=*"
        headers = {
            'User-Agent': 'ProjectInocula/1.0 (https://github.com/your-username/Project-Inocula)'
        }
        
        search_response = requests.get(search_url, headers=headers)
        if search_response.status_code == 200:
            search_data = search_response.json()
            search_results = search_data.get("query", {}).get("search", [])
            
            if search_results:
                # Take the top result title
                top_title = search_results[0]['title']
                
                # Step 2: Get the summary for that specific page
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_title)}"
                summary_response = requests.get(summary_url, headers=headers)
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    extract = summary_data.get("extract", "")
                    wiki_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    
                    if extract:
                        new_reasons.append(f"Factual Context Found: Wikipedia ('{top_title}')")
                        verification_context = f"Wikipedia summary for '{top_title}': {extract}"
            
    except Exception as e:
        print(f"DEBUG: Wikipedia Verifier Error: {e}")

    # We don't automatically deduct score here because Wikipedia is neutral.
    # Instead, we pass the 'verification_context' to the Explainer node (Gemini),
    # which will decide if the Wikipedia facts contradict the input text.
    return {
        "reasons": new_reasons,
        "metadata": {
            "verification_summary": verification_context,
            "verification_link": wiki_url
        } if verification_context else {}
    }