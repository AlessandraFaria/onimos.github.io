.PHONY: install test bench

install:
	pip install -e ".[dev]"

test:
	pytest -q

bench:
	python benchmarks/read_write_benchmark.py
	python benchmarks/insertion_order_benchmark.py
	python benchmarks/first_word_gating_benchmark.py
