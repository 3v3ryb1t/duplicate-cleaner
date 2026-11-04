import errno
from pathlib import Path
from unittest.mock import patch

import allure
import pytest

from duplicate_cleaner import remove_empty_directories

from .assertions import assert_bool_result, assert_lists_diff


@allure.title("Empty dirs removal -> {scenario_name}")
@allure.epic("Cleanup")
@allure.feature("Directories Cleanup")
@allure.story("Empty directories removal")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "tree_structure, expected_dirs, scenario_name",
    [
        pytest.param(
            {"folder_A": {"subfolder_empty": {}}},
            [],
            "Empty subfodler in another folder",
        ),
        pytest.param(
            {"level1": {"level2": {"level3": {}}}},
            [],
            "Cascade empty subfodlers",
        ),
        pytest.param(
            {"folder_with_file": {"keep_me.txt": "data"}},
            ["folder_with_file"],
            "Folder contains a file",
        ),
        pytest.param(
            {"empty_dir": {}, "active_dir": {"file.txt": "hello"}},
            ["active_dir"],
            "Empty and Not empty dirs",
        ),
        pytest.param(
            {"root_folder": {}},
            [],
            "Empty start dir",
        ),
        pytest.param(
            {"folder_with_hidden_file": {".gitignore": ""}},
            ["folder_with_hidden_file"],
            "Dir with a hidden file",
        ),
        pytest.param(
            {"parent_folder": {".hidden_empty_dir": {}}},
            [],
            "Dir with hidden empty folder",
        ),
        pytest.param(
            {"parent_folder": {".hidden_active_dir": {".keep_me.txt": "data"}}},
            ["parent_folder", "parent_folder/.hidden_active_dir"],
            "Dir with hidden not empty folder",
        ),
    ],
)
def test_remove_empty_directories_scenarios(
    create_test_tree, tree_structure, expected_dirs, scenario_name
):
    with allure.step("Creating directory structure"):
        test_path = create_test_tree(tree_structure)

        initial_dirs = [
            str(p.relative_to(test_path)) for p in test_path.rglob("*") if p.is_dir()
        ]

    with allure.step("Running remove_empty_directories()"):
        remove_empty_directories(test_path)

    actual_remaining_dirs = [
        str(p.relative_to(test_path)) for p in test_path.rglob("*") if p.is_dir()
    ]

    expected_diff = list(set(initial_dirs) - set(expected_dirs))

    assert_lists_diff(
        actual_remaining_dirs,
        initial_dirs,
        expected_diff,
        "Check remaining directories",
    )


@allure.title("Empty directory removal -> OS Error handling")
@allure.epic("Cleanup")
@allure.feature("Directories Cleanup")
@allure.story("Empty directories removal")
@allure.severity(allure.severity_level.CRITICAL)
def test_remove_empty_directories_os_error(create_test_tree, capsys):
    with allure.step("Creating empty directory"):
        structure = {"empty_dir": {}}
        test_path = create_test_tree(structure)
        target_dir = test_path / "protected_empty_dir"

    with (
        allure.step("Mocking system OSError on rmdir() call"),
        patch.object(
            Path,
            "rmdir",
            side_effect=OSError(errno.EACCES, "Permission denied"),
        ),
    ):
        remove_empty_directories(test_path)

    captured = capsys.readouterr()
    expected_err = "ERROR: failed removing a dir"
    assert_bool_result(
        target_dir.exists(),
        lambda: target_dir.exists(),
        "Check  directory still exists",
    )
    assert_bool_result(
        True,
        lambda: expected_err in captured.out,
        "Check error output",
    )
