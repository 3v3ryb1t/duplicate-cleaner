# 🚀 Duplicate File Cleaner (with 100% Test Coverage)

A fast and secure Python command-line utility (CLI) for finding and removing duplicate files. This project is built with strict type annotations, system error handling, and full test coverage.

## 🌟 Features

* **100% Code Coverage:** Every part of the application, including empty directory cleanup, interactive choices, and edge cases, is tested.
* **Isolated Testing:** Robust handling of system exceptions such as symlink loops (`ELOOP`) and permission errors (`EACCES`) via  mocking.
* **Scan workflow:** Identifies duplicate files efficiently by grouping them by size first, then calculating SHA-256 chunked hashes for verification.

---

## 🛠 Stack & Tools

* **Language:** Python 3.12+ (with strict `typing` annotations)
* **Environment & Package Manager:** `uv`
* **Testing Framework:** `pytest`
* **Coverage Tool:** `pytest-cov`
* **Reporting:** `allure-pytest`

---

## 📦 Code Coverage Metrics

Run the coverage tool directly using the customized default test runner. The project has zero coverage gaps:

| File | Stmts | Miss | Branch | BrPart | Cover |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `src/duplicate_cleaner/__init__.py` | 8 | 0 | 0 | 0 | **100.0%** |
| `src/duplicate_cleaner/duplicate_cleaner.py` | 151 | 0 | 60 | 0 | **100.0%** |
| **TOTAL** | **159** | **0** | **60** | **0** | **100.0%** |

### Verified Edge Cases:
1. **Circular Symlinks (`ELOOP`):** Validated protection loops against recursive symlinks during depth detection and link flattening.
2. **Relative Symlink Targets:** Correct resolution of target paths when symlinks point to relative locations (`../`).
3. **Permission Errors (`EACCES`):** Ensures locked or system files are safely skipped and logged without crashing the tool.
4. **Interactive Prompts and Flags:** Complete parameter mapping for CLI combinations like `--no-confirm`, `--remove-empty`, and user inputs (`y/N`).

---

## 🚀 Quick Start

### 1. Installation and Setup
Project dependencies are managed via `uv`. Clone the repository and run the setup command in the project root:
```bash
uv sync
```
*This command creates an isolated virtual environment and automatically installs all dependencies.*

### 2. Running the Utility
Execute the application entry point using `uv run`:
```bash
# Basic run (scans user home directory by default)
uv run duplicate-cleaner

# Scan a specific directory recursively with auto-confirmation and empty directory cleanup
uv run duplicate-cleaner --target . --recurse --no-confirm --remove-empty
```

---

## 🧪 Testing & Reporting

Thanks to pre-configured `addopts` project settings, short logs, test execution coverage metrics collection, and Allure report indexing run automatically.

### Run Tests and Collect Coverage
```bash
uv run pytest
```
*This instantly executes tests, renders an HTML report in `htmlcov/`, and updates text metrics.*

### Generate Allure Reports
Build and view the dashboard in your default browser (requires a local installation of `allure-cli`):
```bash
allure serve allure-results
```

---

## ⚙️ Code Quality & Linters

The codebase complies with modern standard formatting guidelines. Code styles are validated with **Ruff**:
```bash
# Check code style, formatting, and imports
uv run ruff check

# Automatically format the code to PEP 8 standards
uv run ruff format
```

Run static type checking using **mypy**:
```bash
uv run mypy src/ tests/
```
