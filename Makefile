
.PHONY: clean docs docs-clean docs-cleanup test test-clean test-only web-build

WEBPACK=./node_modules/webpack/bin/webpack.js
GRUNT=grunt
NODE_PATH=./node_modules


clean:
	make test-clean
	find . -type f \( -iname '*.c' -o -iname '*.pyc' -o -iname '*.so' \) -exec rm '{}' ';'

test:
	make test-clean
	make test-only

test-clean:
	rm -rf coverage.xml htmlcov junit.xml pylint.log result
	find . -type d -name "__pycache__" -prune -exec rm -rf '{}' ';'

test-only:
	PYTHONHASHSEED=random py.test -vv -r xw --cov=rhodecode --cov-report=term-missing --cov-report=html rhodecode

docs:
	(cd docs; nix-build default.nix -o result; make clean html)

docs-clean:
	(cd docs; make clean)

docs-cleanup:
	(cd docs; make cleanup)

web-build:
	NODE_PATH=$(NODE_PATH) $(GRUNT)

