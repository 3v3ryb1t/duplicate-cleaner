from pathlib import Path

import pytest


@pytest.fixture
def create_test_tree(tmp_path: Path):
    def _blueprint(structure: dict, base_path: Path = tmp_path) -> Path:
        for name, content in structure.items():
            current_path = base_path / name

            if isinstance(content, dict):
                current_path.mkdir(parents=True, exist_ok=True)
                _blueprint(content, current_path)
            elif isinstance(content, str) and content.startswith("symlink:"):
                target_str = content.split(":", 1)[1]
                target_path = (
                    base_path / target_str
                    if not target_str.startswith("/")
                    else Path(target_str)
                )
                current_path.symlink_to(target_path)
            else:
                current_path.parent.mkdir(parents=True, exist_ok=True)
                current_path.write_text(content)
        return tmp_path

    return _blueprint
