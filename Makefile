.DEFAULT_GOAL := help

# set by: PATH_TO_OUTDATED_PACKAGES=/some/path/outdated_packages.py
OUTDATED_PACKAGES = ${PATH_TO_OUTDATED_PACKAGES}

NODE_PATH=./node_modules
WEBPACK=./node_binaries/webpack
GRUNT=./node_binaries/grunt

.PHONY: clean
clean: ## full clean
	make test-clean
	find . -type f \( -iname '*.c' -o -iname '*.pyc' -o -iname '*.so' -o -iname '*.orig' \) -exec rm '{}' ';'


.PHONY: test
test: ## run test-clean and tests
	make test-clean
	make test-only


.PHONY:test-clean
test-clean:  ## run test-clean and tests
	rm -rf coverage.xml htmlcov junit.xml pylint.log result
	find . -type d -name "__pycache__" -prune -exec rm -rf '{}' ';'
	find . -type f \( -iname '.coverage.*' \) -exec rm '{}' ';'


.PHONY: test-only
test-only: ## run tests
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar \
	--cov=rhodecode --cov-report=term-missing --cov-report=html \
    rhodecode


.PHONY: test-only-mysql
test-only-mysql: ## run tests against mysql
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar \
	--cov=rhodecode --cov-report=term-missing --cov-report=html \
    --ini-config-override='{"app:main": {"sqlalchemy.db1.url": "mysql://root:qweqwe@localhost/rhodecode_test?charset=utf8"}}' \
    rhodecode


.PHONY: test-only-postgres
test-only-postgres: ## run tests against postgres
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar \
	--cov=rhodecode --cov-report=term-missing --cov-report=html \
    --ini-config-override='{"app:main": {"sqlalchemy.db1.url": "postgresql://postgres:qweqwe@localhost/rhodecode_test"}}' \
    rhodecode

.PHONY: docs
docs: ## build docs
	(cd docs; nix-build default.nix -o result; make clean html)


.PHONY: docs-clean
docs-clean: ## Cleanup docs
	(cd docs; make clean)


.PHONY: docs-cleanup
docs-cleanup: ## Cleanup docs
	(cd docs; make cleanup)


.PHONY: web-build
web-build: ## Build static/js
	NODE_PATH=$(NODE_PATH) $(GRUNT)


.PHONY: generate-pkgs
generate-pkgs: ## generate new python packages
	nix-shell pkgs/shell-generate.nix --command "pip2nix generate --licenses"


.PHONY: pip-packages
pip-packages: ## show outdated packages
	python ${OUTDATED_PACKAGES}


.PHONY: generate-js-pkgs
generate-js-pkgs: ## generate js packages
	rm -rf node_modules && \
	nix-shell pkgs/shell-generate.nix --command "node2nix --input package.json -o pkgs/node-packages.nix -e pkgs/node-env.nix -c pkgs/node-default.nix -d --flatten --nodejs-8" && \
	sed -i -e 's/http:\/\//https:\/\//g' pkgs/node-packages.nix


.PHONY: generate-license-meta
generate-license-meta: ## Generate license metadata
	nix-build pkgs/license-generate.nix -o result-license && \
	cat result-license/licenses.json | python -m json.tool > rhodecode/config/licenses.json

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
