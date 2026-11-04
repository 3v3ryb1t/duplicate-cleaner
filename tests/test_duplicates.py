import errno
from pathlib import Path
from unittest.mock import MagicMock, patch

import allure
import pytest

from duplicate_cleaner.duplicate_cleaner import find_duplicate_files

from .assertions import assert_equal


@allure.title("Scan exceptions -> {scenario_name}")
@allure.epic("Duplicates Search")
@allure.feature("Scanning File Structure")
@allure.story("Handling OS errors during scan")
@pytest.mark.parametrize(
    "error_code, scenario_name",
    [
        (errno.ELOOP, "Circular symlink loop (ELOOP)"),
        (errno.EACCES, "Symlink access denial (EACCES)"),
    ],
)
def test_find_duplicate_files_symlink_errors(
    tmp_path: Path, error_code: int, scenario_name: str
) -> None:
    mock_file: Path = tmp_path / "fake_link.txt"

    mock_error: OSError = OSError()
    mock_error.errno = error_code
    mock_error.strerror = f"System error code: {error_code}"

    with (
        allure.step("Injecting exception via mocking glob iterator results"),
        patch.object(Path, "glob", return_value=[mock_file]),
        patch("os.path.islink", return_value=True),
        patch.object(Path, "is_dir", return_value=False),
        patch.object(Path, "stat", side_effect=mock_error),
    ):
        result: dict = find_duplicate_files(tmp_path, recurse=True)

    assert_equal(
        len(result),
        0,
        "Verify application safely recovers and returns an empty duplicates map",
    )


@allure.epic("Duplicates Search")
@allure.feature("Hashes handling")
@allure.story("Handling Hashing Exceptions")
@allure.title("Scan flow -> Gracefully skip files returning empty or None hash values")
@allure.severity(allure.severity_level.NORMAL)
@patch("duplicate_cleaner.duplicate_cleaner.calculate_file_hash")
def test_find_duplicate_files_empty_hash(mock_hash: MagicMock, tmp_path: Path) -> None:
    file1: Path = tmp_path / "file1.txt"
    file2: Path = tmp_path / "file2.txt"
    file1.write_text("same_size", encoding="utf-8")
    file2.write_text("same_size", encoding="utf-8")

    def dynamic_hash_behavior(file_path: Path) -> str | None:
        return None if file_path.name == "file2.txt" else "valid_hash"

    with allure.step(
        "Substitution of calculate_file_hash to dynamically inject None for specific layout target"
    ):
        mock_hash.side_effect = dynamic_hash_behavior

    with allure.step("Call find_duplicate_files and inject"):
        result: dict = find_duplicate_files(tmp_path, recurse=True)

    assert_equal(
        len(result),
        0,
        "Verify application safely skips empty hash entries and forms zero duplicate mapping groups",
    )
