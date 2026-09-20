.PHONY: help smoke data-fetch data-extract data-features data-splits data-verify \
        test experiments-track-a validate aggregate figures tables paper clean check-imports

help:
	@echo "Pipeline targets (run in order):"
	@grep -E '^[a-zA-Z-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

smoke: ## Phase 3 -- 60s environment check
	bash scripts/smoke_test.sh

data-fetch: ## Phase 6 -- download corpora, verify checksums
	python -m oran_ids.ingest.fetch --config configs/base.yaml

data-extract: ## Phase 6 -- ONE exporter over BOTH corpora (resolves A3)
	python -m oran_ids.ingest.exporter --config configs/exporter/default.yaml --all-corpora

data-features: ## Phase 6 -- families, windowing, short-flow policy
	python -m oran_ids.features.build --config configs/base.yaml

data-splits: ## Phase 6 -- grouped stratified splits per split_seed
	python -m oran_ids.splits.grouped --config configs/base.yaml

data-verify: ## Phase 6 RED GATE -- extractor agreement + manifest reproducibility
	python -m oran_ids.ingest.verify --config configs/base.yaml --strict

test: ## Phase 9 -- unit, integration, property tests
	pytest -q --cov=src/oran_ids --cov-fail-under=80

check-imports: ## Phase 5 -- assert the import graph is acyclic
	python scripts/check_imports.py src/oran_ids

experiments-track-a: ## Phase 13 -- offline transfer experiments (~5h on 12 cores)
	python -m experiments.run --config configs/experiments/e1.yaml
	python -m experiments.run --config configs/experiments/e2.yaml
	python -m experiments.run --config configs/experiments/e3.yaml
	python -m experiments.run --config configs/experiments/e7.yaml

validate: ## Phase 14 RED GATE -- fails loudly on bad results
	python analysis/validate_results.py --strict

aggregate: ## Phase 15 -- raw runs -> aggregated CSVs
	python analysis/aggregate.py --in results/raw --out results/aggregated

figures: ## Phase 16 -- generate every data figure
	python analysis/make_figures.py --config configs/base.yaml

tables: ## Phase 17 -- generate every LaTeX table body
	python analysis/make_tables.py --config configs/base.yaml

paper: validate aggregate figures tables ## Phase 18 -- regenerate the PDF end to end
	cd paper && latexmk -pdf main.tex
	python scripts/check_no_placeholders.py paper/main.tex

clean:
	rm -rf paper/*.aux paper/*.log paper/*.out paper/*.fls paper/*.fdb_latexmk
