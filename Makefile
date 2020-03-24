
.PHONY: clean docs docs-clean docs-cleanup test test-clean test-only test-only-postgres test-only-mysql web-build generate-pkgs pip-packages

NODE_PATH=./node_modules
WEBPACK=./node_binaries/webpack
GRUNT=./node_binaries/grunt
# set by: PATH_TO_OUTDATED_PACKAGES=/some/path/outdated_packages.py
OUTDATED_PACKAGES = ${PATH_TO_OUTDATED_PACKAGES}

clean:
	make test-clean
	find . -type f \( -iname '*.c' -o -iname '*.pyc' -o -iname '*.so' -o -iname '*.orig' \) -exec rm '{}' ';'

test:
	make test-clean
	make test-only

test-clean:
	rm -rf coverage.xml htmlcov junit.xml pylint.log result
	find . -type d -name "__pycache__" -prune -exec rm -rf '{}' ';'
	find . -type f \( -iname '.coverage.*' \) -exec rm '{}' ';'

test-only:
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar --cov=rhodecode \
    --cov-report=term-missing --cov-report=html \
    rhodecode

test-only-mysql:
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar --cov=rhodecode \
    --cov-report=term-missing --cov-report=html \
    --ini-config-override='{"app:main": {"sqlalchemy.db1.url": "mysql://root:qweqwe@localhost/rhodecode_test?charset=utf8"}}' \
    rhodecode

test-only-postgres:
	PYTHONHASHSEED=random \
	py.test -x -vv -r xw -p no:sugar --cov=rhodecode \
    --cov-report=term-missing --cov-report=html \
    --ini-config-override='{"app:main": {"sqlalchemy.db1.url": "postgresql://postgres:qweqwe@localhost/rhodecode_test"}}' \
    rhodecode


docs:
	(cd docs; nix-build default.nix -o result; make clean html)

docs-clean:
	(cd docs; make clean)

docs-cleanup:
	(cd docs; make cleanup)

web-build:
	NODE_PATH=$(NODE_PATH) $(GRUNT)

generate-pkgs:
	nix-shell pkgs/shell-generate.nix --command "pip2nix generate --licenses"

pip-packages:
	python ${OUTDATED_PACKAGES}

generate-js-pkgs:
	rm -rf node_modules && \
	nix-shell pkgs/shell-generate.nix --command "node2nix --input package.json -o pkgs/node-packages.nix -e pkgs/node-env.nix -c pkgs/node-default.nix -d --flatten --nodejs-8" && \
	sed -i -e 's/http:\/\//https:\/\//g' pkgs/node-packages.nix

generate-license-meta:
	nix-build pkgs/license-generate.nix -o result-license && \
	cat result-license/licenses.json | python -m json.tool > rhodecode/config/licenses.json