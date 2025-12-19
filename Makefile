# Makefile for comux

.PHONY: install test clean lint run

install:
	pip install -r requirements.txt
	python setup.py install

test:
	python -m pytest tests/

lint:
	python -m flake8 comux.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run:
	python comux.py

dev:
	pip install -e .

build:
	python setup.py sdist bdist_wheel