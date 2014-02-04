.PHONY: clean-pyc publish test tox-test

test:
	py.test

tox-test:
	tox

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

publish:
	python setup.py sdist upload
