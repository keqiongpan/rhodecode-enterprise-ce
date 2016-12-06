
WEBPACK=./node_modules/webpack/bin/webpack.js
GRUNT=grunt
NODE_PATH=./node_modules
CI_PREFIX=enterprise

.PHONY: docs docs-clean ci-docs clean test test-clean test-lint test-only


docs:
	(cd docs; nix-build default.nix -o result; make clean html)

docs-clean:
	(cd docs; make clean)

docs-cleanup:
	(cd docs; make cleanup)

ci-docs: docs;


clean: test-clean
	find . -type f \( -iname '*.c' -o -iname '*.pyc' -o -iname '*.so' \) -exec rm '{}' ';'

test: test-clean test-only

test-clean:
	rm -rf coverage.xml htmlcov junit.xml pylint.log result

test-only:
	PYTHONHASHSEED=random py.test -vv -r xw --cov=rhodecode --cov-report=term-missing --cov-report=html rhodecode/tests/

web-build:
	NODE_PATH=$(NODE_PATH) $(GRUNT)

web-test:
	@echo "no test for our javascript, yet!"

docs-bootstrap:
	(cd docs; nix-build default.nix -o result)
	@echo "Please go to docs folder and run make html"

