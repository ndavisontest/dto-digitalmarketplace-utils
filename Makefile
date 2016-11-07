pytest_args = --cov=dmutils --cov-report=term-missing

install:
	pip install -U pip
	pip install -U -r requirements_for_test.txt

lint:
	flake8 .

test:
	py.test $(pytest_args)

tox:
	tox -- $(pytest_args)

testall: lint tox

all: install lint tox
