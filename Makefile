.PHONY: help venv install serve serve-docker build build-docker clean

PYTHON ?= python3
VENV_DIR ?= .venv
VENV_BIN := $(VENV_DIR)/bin
PORT ?= 18000
DOCKER_IMAGE ?= squidfunk/mkdocs-material:latest
export NO_MKDOCS_2_WARNING=1

help: ## Exibe esta mensagem de ajuda
	@echo "=================================================================="
	@echo " PFM Core Banking — Docs-as-Code (MkDocs Material)"
	@echo "=================================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(VENV_DIR)/bin/mkdocs:
	@rm -rf $(VENV_DIR)
	@if command -v uv >/dev/null 2>&1; then \
		echo "Criando ambiente virtual Python via uv em $(VENV_DIR)..."; \
		uv venv $(VENV_DIR); \
		uv pip install --python $(VENV_BIN)/python -r requirements.txt; \
	elif $(PYTHON) -m venv $(VENV_DIR) >/dev/null 2>&1; then \
		echo "Instalando dependencias via pip em $(VENV_DIR)..."; \
		$(VENV_BIN)/pip install --upgrade pip; \
		$(VENV_BIN)/pip install -r requirements.txt; \
	else \
		rm -rf $(VENV_DIR); \
		echo "Ambiente venv local indisponivel; utilizando container Docker ($(DOCKER_IMAGE))."; \
		exit 1; \
	fi

install: $(VENV_DIR)/bin/mkdocs ## Instala as dependências do MkDocs Material em virtualenv local (.venv)

serve: ## Inicia o servidor local MkDocs Material (porta 18000 por padrão; sobrescreva com PORT=...)
	@echo "🚀 Iniciando MkDocs Material em http://localhost:$(PORT) ..."
	@if [ -x "$(VENV_BIN)/mkdocs" ]; then \
		$(VENV_BIN)/mkdocs serve --dev-addr=0.0.0.0:$(PORT); \
	elif command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve --dev-addr=0.0.0.0:$(PORT); \
	elif $(MAKE) $(VENV_DIR)/bin/mkdocs; then \
		$(VENV_BIN)/mkdocs serve --dev-addr=0.0.0.0:$(PORT); \
	else \
		docker run --rm -it -p $(PORT):8000 -v $(PWD):/docs $(DOCKER_IMAGE); \
	fi

serve-docker: ## Inicia o servidor MkDocs Material usando Docker
	@echo "🚀 Iniciando MkDocs Material (Docker) em http://localhost:$(PORT) ..."
	docker run --rm -it -p $(PORT):8000 -v $(PWD):/docs $(DOCKER_IMAGE)

build: ## Compila o site estático em ./site com validação estrita (--strict)
	@if [ -x "$(VENV_BIN)/mkdocs" ]; then \
		$(VENV_BIN)/mkdocs build --clean --strict; \
	elif command -v mkdocs >/dev/null 2>&1; then \
		mkdocs build --clean --strict; \
	elif $(MAKE) $(VENV_DIR)/bin/mkdocs; then \
		$(VENV_BIN)/mkdocs build --clean --strict; \
	else \
		docker run --rm -v $(PWD):/docs $(DOCKER_IMAGE) build --clean --strict; \
	fi

build-docker: ## Compila o site estático usando o container oficial do MkDocs Material
	docker run --rm -v $(PWD):/docs $(DOCKER_IMAGE) build --clean --strict

clean: ## Remove o diretório ./site e o ambiente virtual .venv
	rm -rf site $(VENV_DIR)
