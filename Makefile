# Makefile for Wasabi Filemanager

.PHONY: clean install test-wasabi

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -exec rm -rf {} +
	rm -f .wasabi_sync.json .wasabi_config.json

install:
	pip install boto3

# tkinter is included with most Python installations, but you can add python3-tk for Linux:
# sudo apt-get install python3-tk

# Test Wasabi connection using test-wasabi.py

test-wasabi:
	python3 test-wasabi.py 