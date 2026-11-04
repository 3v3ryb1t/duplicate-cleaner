import errno
from pathlib import Path
from unittest.mock import patch

import allure
import pytest

from duplicate_cleaner.duplicate_cleaner import remove_duplicate_files

from .assertions import assert_bool_result, assert_contains

pytestmark = pytest.mark.functional


@allure.epic("Cleanup")
@allure.feature("Files deletion")
@allure.title("Deleting a duplicate - symbolic link")
@allure.story("Flattening symlink chain")
@allure.severity(allure.severity_level.CRITICAL)
def test_remove_duplicate_as_symlink(create_test_tree):
    with allure.step("Creating original file, duplicate, and symlink"):
        structure = {
            "original.txt": "data",
            "duplicate.txt": "data",
            "link_to_duplicate.txt": "symlink:duplicate.txt",
        }
        test_path = create_test_tree(structure)

        duplicates = {
            "hash_data": [
                test_path / "original.txt",
                test_path / "link_to_duplicate.txt",
            ]
        }

    with allure.step("Deleting duplicate which is a symbolic link"):
        remove_duplicate_files(duplicates)

    assert_bool_result(
        expected=True,
        f=lambda: (test_path / "original.txt").exists(),
        step="Checking original file is untouched",
    )

    assert_bool_result(
        expected=False,
        f=lambda: (test_path / "link_to_duplicate.txt").exists(),
        step="Checking duplicate file is removed",
    )


@allure.epic("Cleanup")
@allure.title("Deleting duplicate files")
@allure.feature("Files deletion")
@allure.story("Deleting a duplicate - regular file")
@allure.severity(allure.severity_level.CRITICAL)
def test_remove_duplicate_physical_files(create_test_tree):
    with allure.step("Creating duplicate files"):
        structure = {
            "file1.txt": "same_content",
            "folder_sub": {"file2.txt": "same_content"},
        }
        test_path = create_test_tree(structure)
        duplicates = {
            "hash_123": [
                test_path / "file1.txt",
                test_path / "folder_sub" / "file2.txt",
            ]
        }

    with allure.step("Call remove_duplicate_files()"):
        remove_duplicate_files(duplicates)

    assert_bool_result(
        expected=True,
        f=lambda: (test_path / "file1.txt").exists(),
        step="Checking 'file1.txt' is untouched",
    )

    assert_bool_result(
        expected=False,
        f=lambda: (test_path / "folder_sub" / "file2.txt").exists(),
        step="Checking 'file2.txt' was removed",
    )


@allure.epic("Cleanup")
@allure.feature("Files deletion")
@allure.story("Handling Deletion Exceptions")
@allure.title("Removal -> Handle system OSError during deletion for {scenario_name}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "structure, duplicates_map, scenario_name",
    [
        pytest.param(
            {"file1.txt": "content", "file2.txt": "content"},
            {"hash_xxx": ["file1.txt", "file2.txt"]},
            "Physical duplicate file",
        ),
        pytest.param(
            {
                "original.txt": "data",
                "duplicate.txt": "data",
                "link_to_duplicate.txt": "symlink:duplicate.txt",
            },
            {"hash_data": ["original.txt", "link_to_duplicate.txt"]},
            "Symbolic link duplicate chain",
        ),
    ],
)
def test_remove_duplicate_files_unlink_os_errors(
    create_test_tree, capsys, structure, duplicates_map, scenario_name
):
    test_path = create_test_tree(structure)

    duplicates = {}
    for file_hash, files_list in duplicates_map.items():
        duplicates[file_hash] = [test_path / f for f in files_list]

    with (
        allure.step(
            f"Mocking system access denial on unlink() for target: {scenario_name}"
        ),
        patch.object(
            Path, "unlink", side_effect=OSError(errno.EACCES, "Permission denied")
        ),
    ):
        remove_duplicate_files(duplicates)

    captured = capsys.readouterr()
    assert_contains(
        captured.out,
        "[Error] Failed deleting",
        "Check error output in stdout",
    )
