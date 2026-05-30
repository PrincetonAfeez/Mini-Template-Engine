#!/usr/bin/env python3
"""Render benchmark and stage profiler using only the standard library."""

from __future__ import annotations

import cProfile
import io
import json
import pstats
import timeit
from dataclasses import asdict, dataclass
from pathlib import Path

from template_engine import Template
from template_engine.lexer import lex
from template_engine.parser import parse

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "benchmarks" / "results.json"
CONTEXT = {
    "user": {"name": "Princeton"},
    "items": ["design", "build", "test"],
    "price": 12.345,
    "users": [{"name": f"User-{index}"} for index in range(50)],
}


@dataclass(frozen=True)
class BenchCase:
    label: str
    source: str
    iterations: int


CASES = [
    BenchCase("small", "Hello {{ name | title }}!", 10_000),
    BenchCase("medium", (ROOT / "examples" / "invoice.tmpl").read_text(encoding="utf-8"), 5_000),
    BenchCase(
        "large",
        (ROOT / "examples" / "invoice.tmpl").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "examples" / "loop.tmpl").read_text(encoding="utf-8") * 20,
        500,
    ),
]


@dataclass
class BenchResult:
    label: str
    iterations: int
    total_seconds: float
    ms_per_render: float
    lex_ms: float
    parse_ms: float
    render_ms: float


def _stage_timings(source: str, iterations: int = 200) -> tuple[float, float, float]:
    template = Template(source)

    lex_seconds = timeit.timeit(lambda: list(lex(source)), number=iterations)
    tokens = list(lex(source))
    parse_seconds = timeit.timeit(lambda: parse(tokens), number=iterations)
    parse(tokens)
    render_seconds = timeit.timeit(lambda: template.render(CONTEXT), number=iterations)

    scale = 1000 / iterations
    return lex_seconds * scale, parse_seconds * scale, render_seconds * scale


def _bench_case(case: BenchCase) -> BenchResult:
    template = Template(case.source)
    total = timeit.timeit(lambda: template.render(CONTEXT), number=case.iterations)
    lex_ms, parse_ms, render_ms = _stage_timings(case.source)
    return BenchResult(
        label=case.label,
        iterations=case.iterations,
        total_seconds=total,
        ms_per_render=(total / case.iterations) * 1000,
        lex_ms=lex_ms,
        parse_ms=parse_ms,
        render_ms=render_ms,
    )


def _profile_medium_case() -> str:
    source = CASES[1].source
    template = Template(source)
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(1000):
        template.render(CONTEXT)
    profiler.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs().sort_stats("cumulative").print_stats(8)
    return stream.getvalue()


def main() -> None:
    print("Mini Template Engine — benchmark + profiler")
    print("Complexity: lex O(n), parse O(n), render O(nodes)")
    print()

    results = [_bench_case(case) for case in CASES]
    for result in results:
        print(
            f"{result.label:8} {result.iterations:5} renders in {result.total_seconds:8.3f}s"
            f"  ({result.ms_per_render:.3f} ms/render)"
        )
        print(
            f"         stages/iter: lex={result.lex_ms:.3f}ms"
            f" parse={result.parse_ms:.3f}ms render={result.render_ms:.3f}ms"
        )

    RESULTS_PATH.write_text(
        json.dumps([asdict(result) for result in results], indent=2) + "\n",
        encoding="utf-8",
    )
    print()
    print(f"Wrote {RESULTS_PATH.relative_to(ROOT)}")
    print()
    print("Top cumulative profile (medium template, 1000 renders):")
    print(_profile_medium_case())


if __name__ == "__main__":
    main()
