"""Memory graph visualization CLI tool."""

import argparse
import html
import json
import sys
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from agentic_memory.memory_system import AgenticMemorySystem, MemoryNote
from .config import MCPConfig


def get_graph_data(
    memory_system: AgenticMemorySystem,
    filter_tag: Optional[str] = None,
    filter_category: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Extract graph data from memory system.

    Args:
        memory_system: Initialized memory system
        filter_tag: Only include memories with this tag
        filter_category: Only include memories in this category
        limit: Maximum number of memories to include

    Returns:
        Dict with 'nodes' and 'edges' lists for vis.js
    """
    # Get all memory IDs
    all_ids = memory_system.retriever.get_all_ids()

    if limit and len(all_ids) > limit:
        all_ids = all_ids[:limit]

    # Batch read all memories
    memories_map = memory_system.read_multiple(all_ids)

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    seen_edges: Set[tuple] = set()
    included_ids: Set[str] = set()

    # First pass: filter and create nodes
    for memory_id, note in memories_map.items():
        if note is None:
            continue

        # Apply filters
        if filter_tag and filter_tag not in (note.tags or []):
            continue
        if filter_category and note.category != filter_category:
            continue

        included_ids.add(memory_id)

        # Create node
        nodes.append({
            'id': memory_id,
            'label': _truncate(note.context or 'No context', 35),
            'title': _build_hover_html(note),
            'group': note.category or 'Uncategorized',
            'data': {
                'content': note.content,
                'keywords': note.keywords or [],
                'tags': note.tags or [],
                'context': note.context,
                'category': note.category,
                'timestamp': note.timestamp,
                'last_accessed': note.last_accessed,
                'retrieval_count': note.retrieval_count,
                'links': note.links or [],
                'evolution_history': note.evolution_history or []
            }
        })

    # Second pass: create edges (only for included nodes)
    for memory_id, note in memories_map.items():
        if memory_id not in included_ids or note is None:
            continue

        for link_id in (note.links or []):
            # Only create edge if both ends are in the graph
            if link_id not in included_ids:
                continue

            # Create canonical edge key to prevent duplicates
            edge_key = tuple(sorted([memory_id, link_id]))
            if edge_key not in seen_edges:
                edges.append({
                    'from': memory_id,
                    'to': link_id
                })
                seen_edges.add(edge_key)

    return {'nodes': nodes, 'edges': edges}


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + '...'


def _build_hover_html(note: MemoryNote) -> str:
    """Build HTML tooltip for node hover."""
    parts = [f"<b>{html.escape(note.context or 'No context')}</b>"]
    if note.keywords:
        keywords_str = ', '.join(note.keywords[:5])
        if len(note.keywords) > 5:
            keywords_str += '...'
        parts.append(f"<br><i>Keywords:</i> {html.escape(keywords_str)}")
    if note.tags:
        tags_str = ', '.join(note.tags[:5])
        if len(note.tags) > 5:
            tags_str += '...'
        parts.append(f"<br><i>Tags:</i> {html.escape(tags_str)}")
    return ''.join(parts)


def generate_html(graph_data: Dict[str, Any]) -> str:
    """Generate complete HTML page with embedded vis.js visualization.

    Args:
        graph_data: Dict with 'nodes' and 'edges' for vis.js

    Returns:
        Complete HTML string
    """
    template_path = Path(__file__).parent / 'templates' / 'graph.html'

    if template_path.exists():
        template = template_path.read_text()
    else:
        raise FileNotFoundError(
            f"Template not found at {template_path}. "
            "Please ensure the package is installed correctly."
        )

    # Inject graph data as JSON
    graph_json = json.dumps(graph_data, indent=2)
    return template.replace(
        '/* GRAPH_DATA_PLACEHOLDER */',
        f'const graphData = {graph_json};'
    )


def main():
    """CLI entry point for a-mem-viz."""
    parser = argparse.ArgumentParser(
        description='Visualize A-MEM memory graph in browser',
        prog='a-mem-viz'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output HTML file path (default: temp file)'
    )
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Generate HTML but do not open browser'
    )
    parser.add_argument(
        '--filter-tag',
        type=str,
        default=None,
        help='Only show memories with this tag'
    )
    parser.add_argument(
        '--filter-category',
        type=str,
        default=None,
        help='Only show memories in this category'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of memories to display'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='ChromaDB path (default: from CHROMA_DB_PATH env or ./chroma_db)'
    )

    args = parser.parse_args()

    # Load config
    config = MCPConfig.from_env()
    storage_path = args.db_path or config.storage_path

    print(f"Loading memories from: {storage_path}")

    # Initialize memory system
    try:
        memory_system = AgenticMemorySystem(
            storage_path=storage_path,
            model_name=config.embedding_model,
            llm_backend=config.llm_backend,
            llm_model=config.llm_model,
            api_key=config.api_key,
            evo_threshold=config.evo_threshold
        )
    except Exception as e:
        print(f"Error: Failed to load memory system: {e}", file=sys.stderr)
        sys.exit(1)

    # Get memory count
    total_count = memory_system.retriever.count()
    if total_count == 0:
        print("No memories found in database.")
        sys.exit(0)

    print(f"Found {total_count} memories")

    # Extract graph data
    graph_data = get_graph_data(
        memory_system,
        filter_tag=args.filter_tag,
        filter_category=args.filter_category,
        limit=args.limit
    )

    node_count = len(graph_data['nodes'])
    edge_count = len(graph_data['edges'])
    print(f"Generating graph: {node_count} nodes, {edge_count} edges")

    if node_count == 0:
        print("No memories match the filter criteria.")
        sys.exit(0)

    # Generate HTML
    try:
        html_content = generate_html(graph_data)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(html_content)
        print(f"Saved to: {output_path.absolute()}")
    else:
        # Create temp file that persists after script exits
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.html',
            prefix='a-mem-graph-',
            delete=False
        ) as f:
            f.write(html_content)
            output_path = Path(f.name)
        print(f"Generated: {output_path}")

    # Open in browser
    if not args.no_open:
        print("Opening in browser...")
        webbrowser.open(f'file://{output_path.absolute()}')


if __name__ == '__main__':
    main()
