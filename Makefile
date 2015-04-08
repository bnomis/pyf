PEP := pep8
PYFLAKES := pyflakes
FLAKE8 := flake8

RM := rm -rf
src := pyf/*.py
PANDOC := pandoc
RST2HTML := rst2html-2.7.py
PYTHON := python
CHMOD := chmod -R

.PHONY: dev

sdist:
	# make inaccessible files readable so they can be packaged
	$(CHMOD) u+r tests/inaccessible-files
	$(PYTHON) setup.py sdist

doc/README.rst: README.md
	$(PANDOC) -f markdown -t rst -o $@ $<

doc/README.html: doc/README.rst
	$(RST2HTML) $< $@

rst: doc/README.rst

html: doc/README.html

pep8:
	-@ $(PEP) $(src)

pyflakes:
	-@ $(PYFLAKES) $(src)

flake8:
	-@ $(FLAKE8) $(src)

# will fail if dev is not on the path
# source bin/activate.csh first
dev:
	-@ mkdir dev
	@ python setup.py develop -d dev

test:
	@ tox

coverage:
	@ tox -c tox-coverage.ini

coverclean:
	@ $(RM) .coverage htmlcov

devclean:
	@ $(RM) dev

clean: coverclean devclean
	@ $(RM) pip-install.log .tox pyf.egg-info debug.log debug.log.* dist *.egg-info