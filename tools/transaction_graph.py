"""
tools/transaction_graph.py
Builds and exports transaction network graph data for frontend PyVis rendering.
"""
from __future__ import annotations
import json
from typing import List, Dict, Any
import networkx as nx
from tools.financial_reconciliation import build_transaction_digraph, get_fraud_nodes


def build_graph_data(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Build node/edge data suitable for PyVis and the /graph API endpoint.
    Fraud nodes (part of circular trading) are colored red.
    """
    G = build_transaction_digraph(transactions)
    fraud_node_set = set(get_fraud_nodes(transactions))

    nodes = []
    for node in G.nodes():
        is_fraud = node in fraud_node_set
        nodes.append({
            "id": node,
            "label": node,
            "color": "#e74c3c" if is_fraud else "#2ecc71",
            "size": 20 if is_fraud else 14,
            "title": f"{'⚠ FRAUD NODE — Circular Trading' if is_fraud else 'Normal entity'}: {node}",
            "font": {"color": "#ffffff"},
            "borderWidth": 3 if is_fraud else 1,
        })

    edges = []
    for u, v, data in G.edges(data=True):
        is_fraud_edge = (u in fraud_node_set) and (v in fraud_node_set)
        edges.append({
            "from": u,
            "to": v,
            "label": f"₹{data.get('amount', 0):,.0f}",
            "color": "#e74c3c" if is_fraud_edge else "#95a5a6",
            "width": 3 if is_fraud_edge else 1,
            "arrows": "to",
            "title": f"Amount: ₹{data.get('amount', 0):,.0f} | Transactions: {data.get('count', 1)}",
        })

    # Graph-level metrics
    metrics = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "fraud_node_count": len(fraud_node_set),
        "density": round(nx.density(G), 4),
        "is_dag": nx.is_directed_acyclic_graph(G),
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": metrics,
        "fraud_nodes": list(fraud_node_set),
    }


def generate_pyvis_html(transactions: List[Dict], output_path: str = "logs/graph.html") -> str:
    """
    Generate a self-contained PyVis HTML file for the Streamlit iframe embed.
    Returns the output path.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        return ""

    data = build_graph_data(transactions)
    net = Network(
        height="520px",
        width="100%",
        bgcolor="#0d1117",
        font_color="#ffffff",
        directed=True,
        notebook=False,
    )
    net.set_options("""
    {
      "physics": {
        "barnesHut": { "gravitationalConstant": -8000, "springLength": 160 },
        "stabilization": { "iterations": 120 }
      },
      "edges": { "smooth": { "type": "dynamic" } },
      "interaction": { "hover": true }
    }
    """)

    for node in data["nodes"]:
        net.add_node(
            node["id"],
            label=node["label"],
            color=node["color"],
            size=node["size"],
            title=node["title"],
        )

    for edge in data["edges"]:
        net.add_edge(
            edge["from"],
            edge["to"],
            label=edge["label"],
            color=edge["color"],
            width=edge["width"],
            title=edge["title"],
            arrows="to",
        )

    net.save_graph(output_path)
    return output_path
