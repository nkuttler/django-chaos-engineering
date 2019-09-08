############################################################################
# Set variables
RESOURCES_PY := $(shell find . -type f -name \*.py -print)

# Reused commands
BLACK=black --line-length 89 $(RESOURCES_PY)
DOCFORMATTER=docformatter --recursive --make-summary-multi-line --pre-summary-newline ${RESOURCES_PY}

default: test docs

############################################################################
# Distribution
.PHONY: build sdist upload clean test
build:
	python setup.py build

sdist:
	python setup.py sdist

upload:
	python setup.py sdist upload

clean:
	rm -rfv dist build *.egg-info .coverage coverage reports docs/build \
		debug.log db.sqlite3 .mypy_cache djangochaos-*

requirements.txt: Makefile requirements.in
	pip-compile --no-index --no-emit-trusted-host --no-annotate \
		--output-file requirements.txt requirements.in

.PHONY: docs
docs:
	sphinx-build docs/ docs/build/

############################################################################
# Commands
test: style $(RESOURCES_PY)
	python manage.py makemigrations djangochaos --check
	coverage run manage.py test -v2
	coverage html
	flake8
	-mypy djangochaos/ --html-report reports/mypy/

messages: $(RESOURCES_PY)
	python manage.py makemessages

############################################################################
# Style
style: black docformatter

.PHONY: black blackcheck
black:
	${BLACK}

blackcheck:
	${BLACK} --check

.PHONY: docformatter docformattercheck
docformatter:
	${DOCFORMATTER} --in-place

docformattercheck:
	${DOCFORMATTER} --check

.git/hooks/pre-commit: Makefile
	echo 'make blackcheck || exit 1' > $@
	echo 'make docformattercheck || exit 1' >> $@
	chmod +x $@
