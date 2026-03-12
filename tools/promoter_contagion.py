"""
tools/promoter_contagion.py
Director DIN → Company bipartite graph. Detects promoter contagion risk
when a director sits on multiple companies and one is blacklisted.
"""
from __future__ import annotations
import networkx as nx
from typing import List, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Sample Blacklist (in production these would be fetched from RBI / MCA APIs)
# ─────────────────────────────────────────────────────────────────────────────

BLACKLISTED_COMPANIES = {
    "ShadowTrade Pvt Ltd",
    "GhostCredit Corp",
    "Carousel Holdings",
    "PhantomExports Ltd",
    "NullAccounts Inc",
}

DISQUALIFIED_DIRECTORS = {
    "DIN00000001",
    "DIN00009999",
    "DIN88888888",
}


# ─────────────────────────────────────────────────────────────────────────────
# Graph Builder
# ─────────────────────────────────────────────────────────────────────────────

def build_promoter_graph(director_company_map: List[Dict]) -> nx.Graph:
    """
    Build a bipartite graph connecting DINs to companies.

    director_company_map format:
        [
          {"din": "DIN12345678", "name": "Ravi Kumar", "companies": ["CompanyA", "CompanyB"]},
          ...
        ]
    """
    G = nx.Graph()
    for entry in director_company_map:
        din = entry.get("din", "UNKNOWN")
        director_name = entry.get("name", din)
        G.add_node(din, type="director", label=director_name)
        for company in entry.get("companies", []):
            G.add_node(company, type="company", label=company)
            G.add_edge(din, company)
    return G


# ─────────────────────────────────────────────────────────────────────────────
# Contagion Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_promoter_contagion(
    director_company_map: List[Dict],
    additional_blacklist: Optional[List[str]] = None,
) -> Dict:
    """
    Detect promoter contagion:
    A director appears in multiple companies AND one of those companies is blacklisted.

    Returns a structured contagion report.
    """
    blacklist = set(BLACKLISTED_COMPANIES)
    if additional_blacklist:
        blacklist.update(additional_blacklist)

    G = build_promoter_graph(director_company_map)
    contagion_flags = []
    affected_directors = []
    affected_companies = []

    for entry in director_company_map:
        din = entry.get("din", "UNKNOWN")
        director_name = entry.get("name", din)
        companies = entry.get("companies", [])

        # Check disqualified DIN
        if din in DISQUALIFIED_DIRECTORS:
            contagion_flags.append(
                f"DISQUALIFIED DIRECTOR — {director_name} (DIN: {din}) is on the MCA disqualification list."
            )
            affected_directors.append(din)

        # Check blacklisted company association
        blacklisted_hits = [c for c in companies if c in blacklist]
        if blacklisted_hits and len(companies) > 1:
            contagion_flags.append(
                f"PROMOTER CONTAGION — {director_name} (DIN: {din}) sits on "
                f"{len(companies)} companies including blacklisted entity/ies: "
                f"{', '.join(blacklisted_hits)}."
            )
            affected_directors.append(din)
            affected_companies.extend(blacklisted_hits)

    contagion_detected = len(contagion_flags) > 0

    return {
        "contagion_detected": contagion_detected,
        "contagion_flags": contagion_flags,
        "affected_directors": list(set(affected_directors)),
        "affected_companies": list(set(affected_companies)),
        "graph_node_count": G.number_of_nodes(),
        "graph_edge_count": G.number_of_edges(),
    }


def get_graph_export(director_company_map: List[Dict]) -> Dict:
    """Export promoter graph structure for visualization."""
    G = build_promoter_graph(director_company_map)
    nodes = []
    edges = []

    for node, data in G.nodes(data=True):
        node_type = data.get("type", "unknown")
        is_blacklisted = node in BLACKLISTED_COMPANIES
        is_disqualified = node in DISQUALIFIED_DIRECTORS
        color = "#e74c3c" if (is_blacklisted or is_disqualified) else (
            "#3498db" if node_type == "director" else "#2ecc71"
        )
        nodes.append({
            "id": node,
            "label": data.get("label", node),
            "type": node_type,
            "color": color,
        })

    for u, v in G.edges():
        edges.append({"from": u, "to": v})

    return {"nodes": nodes, "edges": edges}
