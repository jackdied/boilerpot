clean: python-clean
	rm -rf build dist *.egg-info
python-clean:
	find . -name "*.pyc" | xargs rm -f

build: clean
	python setup.py build
install: clean
	python setup.py install
pypi: clean
	python setup.py register sdist upload