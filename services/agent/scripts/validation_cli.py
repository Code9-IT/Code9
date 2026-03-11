#!/usr/bin/env python3
"""
Small CLI for the validation endpoints.

Examples:
  python scripts/validation_cli.py benchmark
  python scripts/validation_cli.py sweep --top-k 2,3,4,5 --min-similarity 0.20,0.30,0.35,0.40
  python scripts/validation_cli.py analysis --latest
  python scripts/validation_cli.py analysis --event-id 123 --top-k 4 --min-similarity 0.35
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from statistics import mean
from urllib import error, parse, request

API_BASE = "http://localhost:8000/api/v1"

BENCHMARK_CASES = [
    {
        "name": "charge_air_temp",
        "event_type": "HIGH_DG5_CHARGE_AIR_TEMP",
        "sensor_name": "dg5_charge_air_temp",
        "expected_sources": ["main_engine.md", "p3_normal_values_thresholds.md"],
    },
    {
        "name": "fuel_viscosity",
        "event_type": "HIGH_HFO_FUEL_VISCOSITY",
        "sensor_name": "hfo_fuel_viscosity",
        "expected_sources": ["fuel_system.md", "p3_normal_values_thresholds.md"],
    },
    {
        "name": "scrubber_so2",
        "event_type": "HIGH_SCRUBBER_FWD_SO2",
        "sensor_name": "scrubber_fwd_so2",
        "expected_sources": [
            "fuel_system.md",
            "p3_normal_values_thresholds.md",
            "p9_maritime_regulations.md",
        ],
    },
    {
        "name": "low_lo_flow",
        "event_type": "LOW_CLEAN_LO_FLOW",
        "sensor_name": "clean_lo_flow",
        "expected_sources": ["main_engine.md", "p5_troubleshooting_procedures.md"],
    },
    {
        "name": "engine_overload",
        "event_type": "HIGH_DG3_ENGINE_LOAD",
        "sensor_name": "dg3_engine_load",
        "expected_sources": ["auxiliary_engines.md", "main_engine.md"],
    },
    {
        "name": "low_tank_weight",
        "event_type": "LOW_HFO_TANK_WEIGHT",
        "sensor_name": "hfo_tank_weight",
        "expected_sources": ["fuel_system.md", "p3_normal_values_thresholds.md"],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run validation benchmarks against the agent.")
    parser.add_argument(
        "--base-url",
        default=API_BASE,
        help=f"Agent API base URL (default: {API_BASE})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the fixed retrieval benchmark suite.")
    benchmark_parser.add_argument("--top-k", type=int, default=None)
    benchmark_parser.add_argument("--min-similarity", type=float, default=None)
    benchmark_parser.add_argument("--json", action="store_true")

    sweep_parser = subparsers.add_parser("sweep", help="Sweep top-K and similarity combinations.")
    sweep_parser.add_argument("--top-k", default="2,3,4,5")
    sweep_parser.add_argument("--min-similarity", default="0.20,0.25,0.30,0.35,0.40")
    sweep_parser.add_argument("--json", action="store_true")

    analysis_parser = subparsers.add_parser("analysis", help="Run analysis validation for one event.")
    analysis_parser.add_argument("--event-id", type=int, default=None)
    analysis_parser.add_argument("--latest", action="store_true", help="Use the latest event automatically.")
    analysis_parser.add_argument("--top-k", type=int, default=None)
    analysis_parser.add_argument("--min-similarity", type=float, default=None)
    analysis_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "benchmark":
            response = run_benchmark(args.base_url, args.top_k, args.min_similarity)
            if args.json:
                print(json.dumps(response, indent=2))
            else:
                print_benchmark(response)
            return

        if args.command == "sweep":
            top_k_values = [int(value) for value in split_csv(args.top_k)]
            min_similarity_values = [float(value) for value in split_csv(args.min_similarity)]
            results = run_sweep(args.base_url, top_k_values, min_similarity_values)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print_sweep(results)
            return

        if args.command == "analysis":
            event_id = args.event_id
            if args.latest or event_id is None:
                event_id = fetch_latest_event_id(args.base_url)
            response = run_analysis(args.base_url, event_id, args.top_k, args.min_similarity)
            if args.json:
                print(json.dumps(response, indent=2))
            else:
                print_analysis(response)
            return
    except RuntimeError as exc:
        raise SystemExit(str(exc))


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code} {exc.reason}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def get_json(url: str) -> dict | list:
    try:
        with request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code} {exc.reason}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def run_benchmark(base_url: str, top_k: int | None, min_similarity: float | None) -> dict:
    payload = {"cases": BENCHMARK_CASES}
    if top_k is not None:
        payload["top_k"] = top_k
    if min_similarity is not None:
        payload["min_similarity"] = min_similarity
    return post_json(f"{base_url}/validate/retrieval", payload)


def run_analysis(
    base_url: str,
    event_id: int,
    top_k: int | None,
    min_similarity: float | None,
) -> dict:
    payload = {"event_id": event_id}
    if top_k is not None:
        payload["top_k"] = top_k
    if min_similarity is not None:
        payload["min_similarity"] = min_similarity
    return post_json(f"{base_url}/validate/analysis", payload)


def fetch_latest_event_id(base_url: str) -> int:
    query = parse.urlencode({"limit": 1})
    response = get_json(f"{base_url}/events?{query}")
    if not isinstance(response, dict) and isinstance(response, list) and response:
        return int(response[0]["id"])
    if isinstance(response, dict) and "id" in response:
        return int(response["id"])
    raise RuntimeError("No events available.")


def summarize_benchmark(response: dict) -> dict:
    matched_cases = int(response["matched_cases"])
    total_cases = int(response["total_cases"])
    top_hit_cases = 0
    expected_hits = 0
    avg_unique_sources = 0.0
    avg_docs = 0.0

    source_counts: list[int] = []
    doc_counts: list[int] = []

    for result in response["results"]:
        docs = result["retrieved_documents"]
        expected_sources = [value.lower() for value in result["expected_sources"]]
        unique_sources = {doc["source"] for doc in docs}
        source_counts.append(len(unique_sources))
        doc_counts.append(len(docs))

        hits = [
            doc for doc in docs
            if any(doc["source"].lower().endswith(expected) for expected in expected_sources)
        ]
        expected_hits += len(hits)

        if docs and any(docs[0]["source"].lower().endswith(expected) for expected in expected_sources):
            top_hit_cases += 1

    if source_counts:
        avg_unique_sources = mean(source_counts)
    if doc_counts:
        avg_docs = mean(doc_counts)

    return {
        "matched_cases": matched_cases,
        "total_cases": total_cases,
        "top_hit_cases": top_hit_cases,
        "expected_hits": expected_hits,
        "avg_unique_sources": avg_unique_sources,
        "avg_docs": avg_docs,
    }


def run_sweep(base_url: str, top_k_values: list[int], min_similarity_values: list[float]) -> dict:
    rows = []
    for top_k, min_similarity in product(top_k_values, min_similarity_values):
        benchmark = run_benchmark(base_url, top_k, min_similarity)
        summary = summarize_benchmark(benchmark)
        rows.append(
            {
                "top_k": top_k,
                "min_similarity": min_similarity,
                **summary,
            }
        )

    best = max(
        rows,
        key=lambda row: (
            row["matched_cases"],
            row["top_hit_cases"],
            row["expected_hits"],
            row["avg_unique_sources"],
            -row["avg_docs"],
            -row["top_k"],
        ),
    )
    return {"results": rows, "best": best}


def print_benchmark(response: dict) -> None:
    summary = summarize_benchmark(response)
    print(
        "Benchmark summary:"
        f" matched={summary['matched_cases']}/{summary['total_cases']},"
        f" top_hit={summary['top_hit_cases']}/{summary['total_cases']},"
        f" expected_hits={summary['expected_hits']},"
        f" avg_unique_sources={summary['avg_unique_sources']:.2f},"
        f" avg_docs={summary['avg_docs']:.2f}"
    )
    print("")
    print(f"{'Case':<18} {'Match':<7} {'Top Source':<32} {'Top Sim':<8} Sources")
    print("-" * 108)
    for result in response["results"]:
        docs = result["retrieved_documents"]
        top_doc = docs[0] if docs else None
        sources = ", ".join(dict.fromkeys(doc["source"] for doc in docs))
        top_source = top_doc["source"] if top_doc else "-"
        top_similarity = f"{top_doc['similarity']:.3f}" if top_doc else "-"
        print(
            f"{result['name']:<18} "
            f"{'yes' if result['matched_expected_source'] else 'no':<7} "
            f"{top_source:<32} "
            f"{top_similarity:<8} "
            f"{sources}"
        )


def print_sweep(payload: dict) -> None:
    print(f"{'top_k':<7} {'min_sim':<8} {'matched':<9} {'top_hit':<9} {'exp_hits':<9} {'avg_src':<8} {'avg_docs':<8}")
    print("-" * 70)
    for row in payload["results"]:
        print(
            f"{row['top_k']:<7} "
            f"{row['min_similarity']:<8.2f} "
            f"{row['matched_cases']}/{row['total_cases']:<7} "
            f"{row['top_hit_cases']}/{row['total_cases']:<7} "
            f"{row['expected_hits']:<9} "
            f"{row['avg_unique_sources']:<8.2f} "
            f"{row['avg_docs']:<8.2f}"
        )
    best = payload["best"]
    print("")
    print(
        "Suggested config:"
        f" RAG_TOP_K={best['top_k']},"
        f" RAG_MIN_SIMILARITY={best['min_similarity']:.2f}"
    )


def print_analysis(response: dict) -> None:
    factors = response["quality_factors"]
    print(f"Event: {response['event']['id']} {response['event']['event_type']} ({response['event']['sensor_name']})")
    print(
        "Quality factors:"
        f" status={factors['status']},"
        f" model={factors['model_used']},"
        f" docs={factors['retrieved_documents_count']},"
        f" tool_calls={factors['tool_calls_count']},"
        f" top_k={factors['rag_top_k']},"
        f" min_similarity={factors['rag_min_similarity']}"
    )
    print("")
    print("Retrieved docs:")
    for doc in response["retrieved_documents"]:
        print(f"  - {doc['source']} ({doc['similarity']:.3f})")
    print("")
    print("Analysis text:")
    print(response["analysis_text"])


if __name__ == "__main__":
    main()
