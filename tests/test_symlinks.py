import os
from pathlib import Path

import allure
import pytest

from duplicate_cleaner import flatten_symlink_chain, symlink_depth

from .assertions import assert_bool_result, assert_equal, assert_exception


@allure.title("Symbolic link depth -> {scenario_name}")
@allure.epic("Symbolic links")
@allure.feature("Symbolic links processing")
@allure.story("Symbolic links depth definition")
@pytest.mark.parametrize(
    "tree_structure, link_to_check, expected_depth, scenario_name",
    [
        pytest.param(
            {"real.txt": "data", "link1.txt": "symlink:real.txt"},
            "link1.txt",
            1,
            "Direct link to file, depth = 1",
        ),
        pytest.param(
            {
                "real.txt": "data",
                "link3.txt": "symlink:real.txt",
                "link2.txt": "symlink:link3.txt",
                "link1.txt": "symlink:link2.txt",
            },
            "link1.txt",
            3,
            "Symbolic links chain, depth = 3",
        ),
    ],
)
def test_symlink_depth_success(
    create_test_tree, tree_structure, link_to_check, expected_depth, scenario_name
):
    with allure.step("Symbolic links generation"):
        test_path = create_test_tree(tree_structure)
        target_link = test_path / link_to_check

    assert_equal(
        symlink_depth(target_link),
        expected_depth,
        "Link depth validation",
    )


@allure.epic("Symbolic links")
@allure.feature("Symbolic links processing")
@allure.story("Symbolic links depth definition")
@allure.title("Symbolic links - relative path depth definition")
def test_symlink_depth_with_relative_target(tmp_path: Path) -> None:
    target_file: Path = tmp_path / "real_file.txt"
    target_file.write_text("content")

    sub_dir: Path = tmp_path / "sub_folder"
    sub_dir.mkdir()

    link_path: Path = sub_dir / "my_link.txt"
    relative_target: str = "../real_file.txt"

    os.symlink(relative_target, link_path)
    depth: int = symlink_depth(link_path)

    assert_bool_result(True, lambda x=depth: x >= 1, "Validating depth >= 1")


@allure.epic("Symbolic links")
@allure.feature("Symbolic links processing")
@allure.story("Flattening symbolic links chain")
@allure.title("Collapsing multi-level symbolic link chain")
def test_flatten_symlink_chain_with_multiple_links(tmp_path: Path) -> None:
    real_file: Path = tmp_path / "real.txt"
    real_file.write_text("data")

    link1: Path = tmp_path / "link1.txt"
    os.symlink(real_file, link1)

    link2: Path = tmp_path / "link2.txt"
    os.symlink(link1, link2)

    flatten_symlink_chain(link2)

    assert_bool_result(
        False, lambda: link1.exists(), "Check if intermediary link was removed"
    )

    assert_bool_result(
        True,
        lambda: Path(os.readlink(link2)).resolve() == real_file.resolve(),
        "Check if original link points directly to the real file target",
    )
    assert_bool_result(
        True, lambda: real_file.exists(), "Verify target real file remains untouched"
    )


@allure.title("Symbolic links depth -> {scenario_name}")
@allure.epic("Symbolic links")
@allure.feature("Symbolic links processing")
@allure.story("Links loops detection")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "tree_structure, loop_link, scenario_name",
    [
        pytest.param(
            {"loop.txt": "symlink:loop.txt"},
            "loop.txt",
            "Link points to itself",
        ),
        pytest.param(
            {"link_A.txt": "symlink:link_B.txt", "link_B.txt": "symlink:link_A.txt"},
            "link_A.txt",
            "A -> B -> A loop",
        ),
    ],
)
def test_symlink_depth_loops(
    create_test_tree, tree_structure, loop_link, scenario_name
):
    with allure.step("Symbolic links loop generation"):
        test_path = create_test_tree(tree_structure)
        target_link = test_path / loop_link
    with pytest.raises(RuntimeError) as exc_info:
        symlink_depth(target_link)
    assert_exception(
        exc_info,
        RuntimeError,
        "Symlink loop detected",
        step="Exception validation",
    )


@allure.title("RuntimeError when flattening link loops")
@allure.epic("Symbolic links")
@allure.feature("Symbolic links processing")
@allure.story("Links loops detection")
@allure.severity(allure.severity_level.CRITICAL)
def test_flatten_symlink_chain_loop_detection(create_test_tree):
    with allure.step("Generating link loop (A -> B -> A)"):
        structure = {
            "link_A.txt": "symlink:link_B.txt",
            "link_B.txt": "symlink:link_A.txt",
        }
        test_path = create_test_tree(structure)

        with pytest.raises(RuntimeError) as exc_info:
            flatten_symlink_chain(test_path / "link_A.txt")

    assert_exception(
        actual_exception=exc_info,
        expected_exception=RuntimeError,
        expected_msg_substring="Symlink loop detected",
        step="Exception validation when flattening link loops",
    )
