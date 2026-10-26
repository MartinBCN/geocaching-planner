import io
import time
import tracemalloc

import pytest

from geocaching_planner.adapters.gpx.pq_source import PocketQuerySource, SourceFile
from geocaching_planner.services.ports import ParsedCache, ParseError
from tests.fixtures.pq.generate import make_pq


@pytest.mark.slow
def test_large_pq_time_and_memory() -> None:
    source_data = make_pq(5000)
    source = PocketQuerySource([SourceFile("large.gpx", io.BytesIO(source_data))])

    tracemalloc.start()
    started = time.perf_counter()
    parsed_count = 0
    log_count = 0
    error_count = 0
    for result in source.iter_caches():
        if isinstance(result, ParsedCache):
            parsed_count += 1
            log_count += len(result.cache.logs)
        elif isinstance(result, ParseError):
            error_count += 1
    elapsed = time.perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert parsed_count == 5000
    assert log_count == 20000
    assert error_count == 0
    assert elapsed < 5
    assert peak_bytes < 200 * 1024 * 1024
