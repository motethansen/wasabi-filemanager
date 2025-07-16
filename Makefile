# Makefile for Wasabi Filemanager

.PHONY: clean install install-dev setup-venv run test-wasabi help

# Default target
help:
	@echo "Available targets:"
	@echo "  setup-venv    - Create virtual environment"
	@echo "  install       - Install all dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  run           - Run the application"
	@echo "  test-wasabi   - Test Wasabi connection"
	@echo "  clean         - Clean up temporary files"

setup-venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "All dependencies installed successfully!"

install-dev: install
	pip install tkinterdnd2
	@echo "Development dependencies installed (including drag-and-drop support)!"

run:
	python3 main.py

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -exec rm -rf {} +
	rm -f .wasabi_sync.json .wasabi_config.json
	@echo "Cleaned up temporary files"

# Test Wasabi connection using test_wasabi_connection.py
test-wasabi:
	python3 test_wasabi_connection.py
