import builtins
import sys

import allure
import pytest

from duplicate_cleaner.duplicate_cleaner import main

from .assertions import assert_bool_result, assert_contains, assert_equal

pytestmark = pytest.mark.integration


@allure.epic("MainApp")
@allure.feature("App execution")
@allure.story("Successful Deletion Scenarios")
@allure.title("Main flow -> Successful removal via {scenario_name}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "setup_flags, user_input, remove_empty, scenario_name",
    [
        pytest.param(
            ["--no-confirm"], None, True, "No-confirm flag with empty dir cleanup"
        ),
        pytest.param(
            ["--no-confirm"], None, False, "No-confirm flag keeping empty dirs"
        ),
        pytest.param(
            [], "y", True, "Interactive confirmation 'Y' with empty dir cleanup"
        ),
        pytest.param([], "y", False, "Interactive confirmation 'Y' keeping empty dirs"),
    ],
)
def test_main_successful_removal_flows(
    monkeypatch, capsys, tmp_path, setup_flags, user_input, remove_empty, scenario_name
):
    sub_dir = tmp_path / "empty_sub"
    sub_dir.mkdir()
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("duplicate_content", encoding="utf-8")
    file2.write_text("duplicate_content", encoding="utf-8")

    cli_args = ["duplicate-cleaner", "--target", str(tmp_path)] + setup_flags
    if remove_empty:
        cli_args.append("--remove-empty")

    with allure.step(f"Simulating CLI environment for scenario: {scenario_name}"):
        monkeypatch.setattr(sys, "argv", cli_args)
        if user_input:
            monkeypatch.setattr(builtins, "input", lambda _: user_input)

    run_main()

    with allure.step("Checking remaining files"):
        assert_bool_result(
            True,
            lambda: file1.exists() or file2.exists(),
            "Check that one original file stays",
        )

        remaining_txt_files = list(tmp_path.glob("*.txt"))
        assert_equal(
            len(remaining_txt_files),
            1,
            "Verify exactly one unique file remains on disk",
        )

    with allure.step("Checking empty folders cleanup"):
        assert_bool_result(
            not remove_empty,
            lambda: sub_dir.exists(),
            "Verify empty directory persistence matches configuration",
        )


@allure.epic("MainApp")
@allure.feature("App execution")
@allure.story("Aborted Deletion Scenarios")
@allure.title("Main flow -> User abortion via interactive 'N' input")
@allure.severity(allure.severity_level.NORMAL)
def test_main_interactive_confirm_no(monkeypatch, capsys, tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("duplicate_content", encoding="utf-8")
    file2.write_text("duplicate_content", encoding="utf-8")

    with allure.step("Simulating interactive session with 'n' abort response"):
        monkeypatch.setattr(
            sys, "argv", ["duplicate-cleaner", "--target", str(tmp_path)]
        )
        monkeypatch.setattr(builtins, "input", lambda _: "n")

    run_main()

    captured = capsys.readouterr()
    assert_contains(
        captured.out,
        "File deletion aborted",
        "Verify standard abort message is logged to stdout",
    )

    with allure.step("Verifying data safety (no files were modified)"):
        assert_bool_result(
            True, lambda: file1.exists(), "Verify file1 remains untouched"
        )
        assert_bool_result(
            True, lambda: file2.exists(), "Verify file2 remains untouched"
        )


@allure.epic("MainApp")
@allure.feature("App execution")
@allure.story("No Action Scenarios")
@allure.title("Main flow -> High-level scan with zero duplicates found")
@allure.severity(allure.severity_level.NORMAL)
def test_main_no_duplicates_found(monkeypatch, capsys, tmp_path):
    unique_file = tmp_path / "unique.txt"
    unique_file.write_text("completely unique raw data string", encoding="utf-8")

    with allure.step("Simulating standard execution against unique file"):
        monkeypatch.setattr(
            sys, "argv", ["duplicate-cleaner", "--target", str(tmp_path)]
        )

    run_main()

    assert_bool_result(
        True,
        lambda: unique_file.exists(),
        "Verify unique file is untouched",
    )


def run_main():
    with allure.step("Running main()"):
        main()
