import errno
from pathlib import Path
from unittest.mock import patch

import allure
import pytest

from duplicate_cleaner import (
    B_RED,
    GREEN,
    RST,
    calculate_file_hash,
    color_print,
    find_duplicate_files,
)

from .assertions import (
    assert_bool_result,
    assert_contains,
    assert_equal,
    assert_exception,
)


@allure.title("Scan flow - {scenario_name}")
@allure.epic("Duplicates Search")
@allure.feature("Scanning File Structure")
@allure.story("Directory scanning scenarios")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.functional
@pytest.mark.parametrize(
    "tree_structure, recurse, expected_groups_count, scenario_name",
    [
        pytest.param(
            {"file1.txt": "hello", "file2.txt": "hello", "unique.txt": "different"},
            False,
            1,
            "Duplicates in the same root folder",
        ),
        pytest.param(
            {"file1.txt": "hello", "sub": {"file2.txt": "hello"}},
            False,
            0,
            "Duplicates inside subfolders without recursion flag",
        ),
        pytest.param(
            {"file1.txt": "hello", "sub": {"file2.txt": "hello"}},
            True,
            1,
            "Duplicates inside subfolders with recursion flag",
        ),
        pytest.param(
            {"zero1.dat": "", "zero2.dat": "", "zero3.dat": ""},
            False,
            1,
            "Empty files",
        ),
    ],
)
def test_find_duplicates(
    create_test_tree,
    tree_structure,
    recurse,
    expected_groups_count,
    scenario_name,
):
    with allure.step("Creating file tree"):
        test_path = create_test_tree(tree_structure)

    with allure.step(f"Call find_duplicate_files() with --recurse={recurse}"):
        result = find_duplicate_files(test_path, recurse=recurse)

    assert_equal(
        len(result),
        expected_groups_count,
        "Check duplicate groups count",
    )


@allure.epic("Duplicates Search")
@allure.feature("Hashes handling")
@allure.story("File hashing verification")
@allure.title("Hashing -> Verify chunked hashing for large files")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.functional
def test_calculate_file_hash_large_chunked_file(tmp_path):
    with allure.step("Generating a file larger than standard 64KB"):
        test_file = tmp_path / "large_chunk.txt"
        chunked_data = "A" * (65536 * 2 + 1024)
        test_file.write_text(chunked_data, encoding="utf-8")

    with allure.step("Calculating file hash"):
        hash_result = calculate_file_hash(test_file)

    assert_bool_result(
        True,
        lambda: hash_result is not None and len(hash_result) > 0,
        "Check that hash is generated",
    )


@allure.epic("Duplicates Search")
@allure.feature("Hashes handling")
@allure.story("Handling hashing exceptions")
@allure.title("Hashing -> Handle FS read errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.unit
@pytest.mark.parametrize(
    "exception_type, error_msg, scenario_name",
    [
        pytest.param(
            PermissionError, "Permission denied", "Access denial (PermissionError)"
        ),
        pytest.param(
            FileNotFoundError,
            "No such file or directory",
            "Missing file (FileNotFoundError)",
        ),
        pytest.param(OSError, "Input/output error", "System I/O error (OSError)"),
    ],
)
def test_calculate_file_hash_exceptions(
    tmp_path,
    exception_type,
    error_msg,
    scenario_name,
):
    with allure.step("Generating temporary file for reading"):
        test_file = tmp_path / "broken_read.txt"
        test_file.write_text("dummy data")

    with (
        allure.step(f"Mocking open() to raise exception: {exception_type.__name__}"),
        patch("builtins.open", side_effect=exception_type(error_msg)),
    ):
        result = calculate_file_hash(test_file)
    assert_equal(
        result,
        None,
        "Check that function returns None",
    )


@allure.title("Scan flow -> Handle OSError on file size check")
@allure.epic("Duplicates Search")
@allure.feature("Scanning File Structure")
@allure.story("Handling FS Exceptions")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.unit
def test_find_duplicate_files_stat_exception(create_test_tree, capsys):
    with allure.step("Creating files for stat error test"):
        structure = {"file1.txt": "hello", "file2.txt": "world"}
        test_path = create_test_tree(structure)

    original_stat = Path.stat

    def mock_stat(self, *args, **kwargs):
        if self.name == "file1.txt":
            raise OSError(errno.EIO, "Input/output error")
        return original_stat(self, *args, **kwargs)

    with (
        allure.step("Mocking Path.stat to simulate system I/O error"),
        patch.object(Path, "stat", mock_stat),
    ):
        result = find_duplicate_files(test_path, recurse=False)

    assert_equal(result, {}, "Check that broken file is skipped")

    captured = capsys.readouterr()
    assert_contains(
        captured.out,
        "[OSError File] Failed to get size for",
        "Verify 'stat' error is captured in stdout",
    )


@allure.epic("Duplicates Search")
@allure.feature("Scanning File Structure")
@allure.story("Filtering Unique Entities")
@allure.title("Scan flow -> ignore files with unique sizes")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.functional
def test_find_duplicate_files_unique_sizes(create_test_tree):
    with allure.step("Creating unique size files"):
        structure = {
            "unique1.txt": "a",
            "unique2.txt": "bb",
            "unique3.txt": "ccc",
        }
        test_path = create_test_tree(structure)

    with allure.step("Running duplicate scan"):
        result = find_duplicate_files(test_path, recurse=False)
    assert_equal(result, {}, "Check that result is empty")


@allure.epic("Not epic")
@allure.feature("Console Logger")
@allure.story("Colorized Console Output")
@allure.title("Logger -> Verify console print for {scenario_name}")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.unit
@pytest.mark.parametrize(
    "color_code, text_msg, expected_exception, scenario_name",
    [
        pytest.param(GREEN, "Success log", None, "Valid GREEN sequence"),
        pytest.param(B_RED, "Failure log", None, "Valid B_RED sequence"),
        pytest.param(
            "\033[1;35m",
            "Glitch log",
            RuntimeError,
            "Invalid color layout exception fallback",
        ),
    ],
    ids=[
        "green_print",
        "red_print",
        "invalid_color",
    ],
)
def test_color_print_scenarios(
    capsys, color_code, text_msg, expected_exception, scenario_name
):
    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            color_print(color_code, text_msg)

        assert_exception(
            actual_exception=exc_info,
            expected_exception=expected_exception,
            expected_msg_substring="ERROR: color",
            step="Check error message",
        )
    else:
        with allure.step("Executing color_print()"):
            color_print(color_code, text_msg)
            captured = capsys.readouterr()

        assert_contains(captured.out, text_msg, step="Verify text presence")
        assert_contains(
            captured.out, color_code, step="Verify ANSI color code presence"
        )
        assert_contains(captured.out, RST, step="Verify ANSI color reset presence")
