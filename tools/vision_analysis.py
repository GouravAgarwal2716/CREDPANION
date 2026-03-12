"""
tools/vision_analysis.py
Multimodal Factory Photo Analysis
Uses GPT-4o to visually analyze uploaded factory photos and precisely
count active manufacturing assets versus idle ones to compute reality scores.
"""
from __future__ import annotations
import os
import random
import base64
import json
from functools import lru_cache
from typing import List, Dict, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# ─────────────────────────────────────────────────────────────────────────────
# Core Multimodal Vision Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

@lru_cache(maxsize=32)
def _cached_analyse_image(image_path: str) -> Dict:
    """
    Passes the image to GPT-4o for visual reasoning.
    Demands a strict JSON response containing active_assets, idle_assets, and a brief reasoning string.
    """
    try:
        base64_image = _encode_image_base64(image_path)
        
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
        
        system_prompt = (
            "You are an expert industrial inspector. You are looking at a photo of a manufacturing plant. "
            "You must estimate two numbers: 'active_assets' (machines running, workers present, goods moving) "
            "and 'idle_assets' (empty floor space, unused machines, shut down areas). "
            "Respond ONLY with a valid JSON object matching this schema: "
            "{\"active_assets\": <int>, \"idle_assets\": <int>, \"reasoning\": \"<brief text>\"}"
        )

        message = HumanMessage(
            content=[
                {"type": "text", "text": "Analyze this factory photo and return strictly JSON."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        )

        response = llm.invoke([SystemMessage(content=system_prompt), message])
        
        # Parse output rigidly
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        active = max(0, int(data.get("active_assets", 0)))
        idle = max(0, int(data.get("idle_assets", 0)))
        
        if active + idle == 0:
            active, idle = 0, 1 # Prevent ZeroDivision
            
        reality_score = active / (active + idle)

        return {
            "image_path": image_path,
            "active_assets": active,
            "idle_assets": idle,
            "reality_score": round(reality_score, 3),
            "reasoning": data.get("reasoning", "No physical reasoning provided."),
            "analysis_method": "gpt-4o Multimodal Vision",
        }

    except Exception as e:
        # Fallback to 0 if API or JSON parse fails
        return {
            "image_path": image_path,
            "active_assets": 0,
            "idle_assets": 1,
            "reality_score": 0.0,
            "error": str(e),
            "analysis_method": "vision api error",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Batch Analyser
# ─────────────────────────────────────────────────────────────────────────────

def analyse_factory_photos(photo_paths: List[str]) -> Tuple[List[Dict], float]:
    """
    Analyse a list of factory photo paths.
    Returns (per-image results list, aggregated reality score).
    """
    results = []
    for path in photo_paths:
        if os.path.exists(path):
            result = _cached_analyse_image(path)
        else:
            result = {
                "image_path": path,
                "active_assets": 0,
                "idle_assets": 0,
                "reality_score": 0.0,
                "analysis_method": "file not found",
            }
        results.append(result)

    if not results:
        return [], 0.0

    total_active = sum(r.get("active_assets", 0) for r in results)
    total_idle = sum(r.get("idle_assets", 0) for r in results)

    if total_active + total_idle == 0:
        aggregate_score = 0.0
    else:
        aggregate_score = total_active / (total_active + total_idle)

    return results, round(aggregate_score, 3)


def synthesize_vision_result(company_type: str) -> Tuple[List[Dict], float]:
    """
    Generate a synthetic vision result for demo purposes when no photos are uploaded.
    company_type: 'clean' | 'fraud' | 'litigation'
    """
    random.seed(42)  # deterministic for demos

    if company_type == "clean":
        active, idle = random.randint(7, 10), random.randint(0, 2)
    elif company_type == "fraud":
        active, idle = random.randint(1, 3), random.randint(5, 9)
    else:  # litigation
        active, idle = random.randint(4, 6), random.randint(2, 4)

    rs = active / (active + idle)
    result = {
        "image_path": "synthetic_demo",
        "active_assets": active,
        "idle_assets": idle,
        "reality_score": round(rs, 3),
        "analysis_method": "synthetic demo",
    }
    return [result], round(rs, 3)
