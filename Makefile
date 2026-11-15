PY := .venv/bin/python
APP_NAME ?= fixit-madison
WS_PATH ?= /Workspace/Users/$(shell databricks current-user me --output json 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['userName'])" 2>/dev/null)/fixit-madison-app

.PHONY: setup dev api web build test seed bundle deploy

setup:            ## venv + backend deps + frontend deps
	python3 -m venv .venv && .venv/bin/pip install -q -r app/requirements.txt pytest
	cd app/frontend && npm install

api:              ## backend on :8000 (auto-reload)
	.venv/bin/uvicorn app.backend.main:app --reload --port 8000

web:              ## Vite dev server on :5173 (proxies /api to :8000)
	cd app/frontend && npm run dev

dev:              ## both (Ctrl-C stops both)
	$(MAKE) -j2 api web

build:            ## build frontend into app/frontend/dist (served by FastAPI)
	cd app/frontend && npm run build

test:
	$(PY) -m pytest -q app/backend/tests

seed:             ## reseed local SQLite demo data
	$(PY) -m app.backend.seed

bundle: build     ## stage a deployable copy in build/app (static + demo cache inside app dir)
	rm -rf build/app && mkdir -p build/app
	cp -R app/backend app/app.yaml app/requirements.txt build/app/
	cp -R app/frontend/dist build/app/static
	mkdir -p build/app/demo && cp -R demo/cached_outputs build/app/demo/
	find build/app -name __pycache__ -prune -exec rm -rf {} +
	rm -rf build/app/backend/tests

deploy: bundle    ## sync + deploy to Databricks Apps (needs CLI auth; app created once via `databricks apps create $(APP_NAME)`)
	databricks workspace import-dir build/app $(WS_PATH) --overwrite   # not `sync`: it skips gitignored build/
	databricks apps deploy $(APP_NAME) --source-code-path $(WS_PATH)
