PYTHON ?= python3

.PHONY: help install uninstall test demo curriculum fields providers doctor dist clean

help:
	@echo "expert-mentor"
	@echo ""
	@echo "  make install      install the 'mentor' command and link the skill"
	@echo "  make uninstall    remove the command and skill links"
	@echo "  make test         run the self-test suite"
	@echo "  make doctor       check the local setup"
	@echo "  make fields       list curated field profiles"
	@echo "  make providers    list supported providers"
	@echo "  make demo         generate a sample prompt to stdout"
	@echo "  make curriculum   generate a sample curriculum prompt to stdout"
	@echo "  make dist         build sdist + wheel into dist/ (needs 'build')"
	@echo "  make clean        remove __pycache__ and build artifacts"

install:
	@chmod +x install.sh uninstall.sh bin/mentor scripts/*.py
	@./install.sh

uninstall:
	@chmod +x uninstall.sh
	@./uninstall.sh

test:
	@$(PYTHON) scripts/selftest.py

doctor:
	@$(PYTHON) scripts/expert_mentor.py doctor

fields:
	@$(PYTHON) scripts/expert_mentor.py --list-fields

providers:
	@$(PYTHON) scripts/expert_mentor.py --list-providers

demo:
	@$(PYTHON) scripts/expert_mentor.py --field "quantum computing" --level beginner

curriculum:
	@$(PYTHON) scripts/expert_mentor.py curriculum --field "Rust" --level intermediate

dist:
	@$(PYTHON) -m pip install --quiet --upgrade build
	@$(PYTHON) -m build
	@echo "artifacts in dist/ — publish with: python -m twine upload dist/*"

clean:
	@rm -rf scripts/__pycache__ build dist *.egg-info scripts/*.egg-info
