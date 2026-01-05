#!/usr/bin/env python3
"""
Debug tool for visualizing the complete memory retrieval workflow.

Usage:
    python debug_retrieval.py "your query here"
    python debug_retrieval.py "your query here" --mode agentic
    python debug_retrieval.py "your query here" -k 10 --output results.json
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, List
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def print_subheader(text: str):
    """Print a formatted subsection header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.ENDC}")

def print_step(step_num: int, step_name: str):
    """Print a step indicator."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[STEP {step_num}] {step_name}{Colors.ENDC}")

def print_key_value(key: str, value: Any, indent: int = 0):
    """Print a key-value pair with formatting."""
    indent_str = "  " * indent
    if isinstance(value, (list, dict)):
        print(f"{indent_str}{Colors.GREEN}{key}:{Colors.ENDC}")
        print(f"{indent_str}  {json.dumps(value, indent=2)}")
    else:
        print(f"{indent_str}{Colors.GREEN}{key}:{Colors.ENDC} {value}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ WARNING: {text}{Colors.ENDC}")

def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ ERROR: {text}{Colors.ENDC}")


class RetrievalDebugger:
    """Debug wrapper for AgenticMemorySystem to trace retrieval workflow."""

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.debug_info = {}

    def debug_search(self, query: str, k: int = 5, mode: str = "basic") -> Dict[str, Any]:
        """
        Execute a search with full debugging information.

        Args:
            query: Search query
            k: Number of results
            mode: "basic" or "agentic"

        Returns:
            Dictionary containing debug information and results
        """
        start_time = time.time()
        self.debug_info = {
            "query": {
                "original": query,
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "k_requested": k
            },
            "steps": []
        }

        print_header(f"DEBUGGING RETRIEVAL WORKFLOW")
        print_key_value("Query", query)
        print_key_value("Mode", mode)
        print_key_value("Results requested (k)", k)

        # STEP 1: ChromaDB Query
        print_step(1, "ChromaDB Vector Search")
        step1_start = time.time()

        raw_results = self.memory_system.retriever.search(query, k)

        step1_time = (time.time() - step1_start) * 1000

        print_key_value("Collection", self.memory_system.retriever.collection.name)
        print_key_value("Embedding model", "all-MiniLM-L6-v2")
        print_key_value("Query time", f"{step1_time:.2f}ms")
        print_key_value("Results found", len(raw_results['ids'][0]) if raw_results['ids'] else 0)

        self.debug_info['steps'].append({
            "step": 1,
            "name": "ChromaDB Vector Search",
            "duration_ms": step1_time,
            "results_count": len(raw_results['ids'][0]) if raw_results['ids'] else 0
        })

        # STEP 2: Display Raw ChromaDB Results
        print_step(2, "Raw ChromaDB Results")

        if raw_results['ids'] and len(raw_results['ids'][0]) > 0:
            print_subheader("Top Results with Similarity Scores")

            raw_data = []
            for i, doc_id in enumerate(raw_results['ids'][0]):
                distance = raw_results['distances'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                document = raw_results['documents'][0][i] if raw_results.get('documents') else None
                metadata = raw_results['metadatas'][0][i] if raw_results.get('metadatas') else {}

                print(f"\n  {Colors.BOLD}Result #{i+1}{Colors.ENDC}")
                print_key_value("ID", doc_id, indent=1)
                print_key_value("Distance", f"{distance:.4f}", indent=1)
                print_key_value("Similarity", f"{similarity:.4f}", indent=1)

                if document:
                    # Show enhanced document (what was actually embedded)
                    print_key_value("Enhanced document", document[:200] + "..." if len(document) > 200 else document, indent=1)

                # Show raw metadata (still as JSON strings)
                if metadata:
                    print(f"  {Colors.GREEN}Raw metadata (pre-deserialization):{Colors.ENDC}")
                    for key, value in metadata.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        else:
                            print(f"    {key}: {value}")

                raw_data.append({
                    "id": doc_id,
                    "distance": distance,
                    "similarity": similarity,
                    "document": document,
                    "metadata": metadata
                })

            self.debug_info['raw_chromadb_results'] = raw_data
        else:
            print_warning("No results found from ChromaDB")

        # STEP 3: Metadata Processing
        print_step(3, "Metadata Deserialization")
        step3_start = time.time()

        # The retriever.search() already deserializes metadata
        print_success("Metadata automatically deserialized by retriever")
        print_key_value("Conversions performed", {
            "keywords": "JSON string → list",
            "tags": "JSON string → list",
            "links": "JSON string → list",
            "retrieval_count": "string → int"
        })

        step3_time = (time.time() - step3_start) * 1000
        self.debug_info['steps'].append({
            "step": 3,
            "name": "Metadata Deserialization",
            "duration_ms": step3_time
        })

        # STEP 4: Memory System Processing
        print_step(4, "Memory System Processing")
        step4_start = time.time()

        if mode == "basic":
            results = self.memory_system.search(query, k)
        else:
            results = self.memory_system.search_agentic(query, k)

        step4_time = (time.time() - step4_start) * 1000

        print_key_value("Search method", f"search_agentic()" if mode == "agentic" else "search()")
        print_key_value("Processing time", f"{step4_time:.2f}ms")
        print_key_value("Final results count", len(results))

        self.debug_info['steps'].append({
            "step": 4,
            "name": "Memory System Processing",
            "duration_ms": step4_time,
            "method": mode,
            "final_count": len(results)
        })

        # STEP 5: Agentic Expansion (if applicable)
        if mode == "agentic":
            print_step(5, "Agentic Link Expansion")

            primary_results = [r for r in results if not r.get('is_neighbor', False)]
            linked_results = [r for r in results if r.get('is_neighbor', False)]

            print_key_value("Primary results (from vector search)", len(primary_results))
            print_key_value("Linked results (from graph traversal)", len(linked_results))

            if linked_results:
                print_subheader("Link Expansion Details")
                expansion_map = {}
                for result in linked_results:
                    parent = result.get('parent_memory_id', 'unknown')
                    if parent not in expansion_map:
                        expansion_map[parent] = []
                    expansion_map[parent].append(result['id'])

                for parent_id, linked_ids in expansion_map.items():
                    print(f"  {Colors.YELLOW}├─{Colors.ENDC} {parent_id} → {linked_ids}")

                self.debug_info['agentic_expansion'] = {
                    "primary_count": len(primary_results),
                    "linked_count": len(linked_results),
                    "expansion_map": expansion_map
                }

        # STEP 6: Final Results
        print_step(6, "Final Results")

        print_subheader("Retrieved Memories")

        for i, result in enumerate(results):
            print(f"\n  {Colors.BOLD}{Colors.GREEN}Memory #{i+1}{Colors.ENDC}")
            print_key_value("ID", result['id'], indent=1)

            if result.get('is_neighbor'):
                print(f"  {Colors.YELLOW}  [LINKED MEMORY - via graph traversal]{Colors.ENDC}")
            else:
                print_key_value("Similarity Score", f"{result.get('score', 'N/A'):.4f}" if result.get('score') else 'N/A', indent=1)

            print_key_value("Content", result['content'][:150] + "..." if len(result['content']) > 150 else result['content'], indent=1)
            print_key_value("Keywords", result.get('keywords', []), indent=1)
            print_key_value("Tags", result.get('tags', []), indent=1)
            print_key_value("Context", result.get('context', 'N/A'), indent=1)
            print_key_value("Retrieval Count", result.get('retrieval_count', 0), indent=1)

            if result.get('links'):
                print_key_value("Links to", result['links'], indent=1)

        # Performance Summary
        total_time = (time.time() - start_time) * 1000

        print_header("PERFORMANCE SUMMARY")
        print_key_value("Total execution time", f"{total_time:.2f}ms")
        print_key_value("ChromaDB collection size", self.memory_system.retriever.collection.count())
        print_key_value("In-memory index size", len(self.memory_system.memories))

        print_subheader("Step Timing Breakdown")
        for step in self.debug_info['steps']:
            percentage = (step['duration_ms'] / total_time * 100) if total_time > 0 else 0
            print(f"  Step {step['step']}: {step['name']:<30} {step['duration_ms']:>8.2f}ms ({percentage:>5.1f}%)")

        self.debug_info['performance'] = {
            "total_duration_ms": total_time,
            "collection_size": self.memory_system.retriever.collection.count(),
            "in_memory_size": len(self.memory_system.memories)
        }

        self.debug_info['final_results'] = results

        return self.debug_info


def main():
    parser = argparse.ArgumentParser(
        description="Debug the memory retrieval workflow with detailed output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug_retrieval.py "how does memory evolution work"
  python debug_retrieval.py "authentication flow" --mode agentic
  python debug_retrieval.py "database queries" -k 10 --output debug.json
        """
    )

    parser.add_argument(
        "query",
        type=str,
        help="The search query to debug"
    )

    parser.add_argument(
        "-k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5)"
    )

    parser.add_argument(
        "--mode",
        choices=["basic", "agentic"],
        default="basic",
        help="Search mode: 'basic' for semantic search only, 'agentic' to include linked memories (default: basic)"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Save debug information to JSON file"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    try:
        # Import and initialize memory system
        from agentic_memory.memory_system import AgenticMemorySystem
        from agentic_memory_mcp.config import load_config

        print(f"{Colors.CYAN}Initializing memory system...{Colors.ENDC}")
        config = load_config()
        memory_system = AgenticMemorySystem(
            llm_backend=config.llm_backend,
            llm_model=config.llm_model,
            embedding_model=config.embedding_model,
            evo_threshold=config.evo_threshold,
            persist_directory=config.storage_path
        )
        print_success("Memory system initialized")

        # Create debugger and run search
        debugger = RetrievalDebugger(memory_system)
        debug_info = debugger.debug_search(args.query, args.k, args.mode)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(debug_info, f, indent=2, default=str)
            print_success(f"Debug information saved to {args.output}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}Debug session completed successfully!{Colors.ENDC}\n")

    except ImportError as e:
        print_error(f"Failed to import required modules: {e}")
        print(f"\n{Colors.YELLOW}Make sure you're running from the project root directory.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
