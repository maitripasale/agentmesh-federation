.PHONY: run test mcp

run:
	docker compose up --build

test:
	pytest -q

mcp:
	python -m mcp_servers.kubernetes.server
