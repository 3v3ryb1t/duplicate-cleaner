import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import allure
import pytest

from duplicate_cleaner import B_RED, RST, parse_args

from .assertions import assert_equal, assert_equal_with_attachment
from .templates import reference_cli_meta


@allure.title("Successful argument parsing -> {scenario_name}")
@allure.epic("CLI")
@allure.feature("Arguments parser")
@allure.story("Run parameters parsing")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "cli_args, expected_flags, scenario_name",
    [
        pytest.param(
            [],
            {
                "root_dir": Path.home(),
                "recursive": False,
                "no_confirm": False,
                "remove_empty_dirs": False,
            },
            "default, no parameters",
        ),
        pytest.param(
            ["-t", str(Path.home()), "-r", "-nc", "-re"],
            {
                "root_dir": Path.home(),
                "recursive": True,
                "no_confirm": True,
                "remove_empty_dirs": True,
            },
            "all 'shortname' flags",
        ),
        pytest.param(
            [
                "--target",
                str(Path.home()),
                "--recurse",
                "--no-confirm",
                "--remove-empty",
            ],
            {
                "root_dir": Path.home(),
                "recursive": True,
                "no_confirm": True,
                "remove_empty_dirs": True,
            },
            "all 'longname' flags",
        ),
        pytest.param(
            ["-t", "."],
            {"root_dir": Path.cwd().resolve()},
            "relative path resolution (.)",
        ),
    ],
)
def test_parse_args_success(monkeypatch, cli_args, expected_flags, scenario_name):
    with allure.step(f"Passing CLI args simulation: {cli_args}"):
        monkeypatch.setattr(sys, "argv", ["duplicate_cleaner.py"] + cli_args)

    with allure.step("Call 'parse_args()'"):
        args = parse_args()

    for attr, expected_value in expected_flags.items():
        assert_equal(
            getattr(args, attr),
            expected_value,
            f"Validation of CLI arg '{attr}'",
        )


@allure.title("Failing argument parsing -> {scenario_name}")
@allure.epic("CLI")
@allure.feature("Arguments parser")
@allure.story("Run parameters parsing")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "cli_args, expected_exit_code, error_msg_template, is_custom_err, scenario_name",
    [
        pytest.param(
            ["-t", "/non/existent/path/at/all"],
            -1,
            "Error: path '/non/existent/path/at/all' not found",
            True,
            "Path doesn't exist",
        ),
        pytest.param(
            ["-t", __file__],
            -1,
            "Error: '{target_file}' is not a directory. Aborted",  # Путь подставится динамически внутри теста
            True,
            "Path to file",
        ),
        pytest.param(
            ["--unknown-flag"],
            2,
            "unrecognized arguments: --unknown-flag",
            False,
            "Unknown arg",
        ),
        pytest.param(
            ["-r", "invalid_arg_type"],
            2,
            "unrecognized arguments: invalid_arg_type",
            False,
            "Invalid type for '--recurse'",
        ),
        pytest.param(
            ["-nc", "invalid_arg_type"],
            2,
            "unrecognized arguments: invalid_arg_type",
            False,
            "Invalid type for '--no-confirm'",
        ),
        pytest.param(
            ["-re", "invalid_arg_type"],
            2,
            "unrecognized arguments: invalid_arg_type",
            False,
            "Invalid type for '--remove-empty'",
        ),
    ],
)
def test_parse_args_failures(
    monkeypatch,
    capsys,
    cli_args,
    expected_exit_code,
    error_msg_template,
    is_custom_err,
    scenario_name,
):
    with allure.step(f"Passing CLI args simulation: {cli_args}"):
        monkeypatch.setattr(sys, "argv", ["duplicate_cleaner.py"] + cli_args)

    with (
        allure.step("Checking run cancellation via SystemExit"),
        pytest.raises(SystemExit) as exc_info,
    ):
        parse_args()

    assert_equal(
        exc_info.value.code,
        expected_exit_code,
        "Exit Code validation",
    )

    captured = capsys.readouterr()
    help_msg, usage_msg = reference_cli_meta().values()

    error_msg = (
        error_msg_template.format(target_file=__file__)
        if "{target_file}" in error_msg_template
        else error_msg_template
    )

    expected_full_output = (
        f"{B_RED}{error_msg}{RST}\n{help_msg}"
        if is_custom_err
        else f"{usage_msg}Duplicate cleaner script: error: {error_msg}\n"
    )
    actual_output = captured.out if is_custom_err else captured.err

    assert_equal_with_attachment(
        actual_output,
        expected_full_output,
        allure.attachment_type.TEXT,
        "Verify error and help messages",
    )


@allure.title("parse_args fall into except")
@allure.epic("CLI")
@allure.feature("Argument parser")
@allure.story("Run parameters parsing")
@allure.severity(allure.severity_level.NORMAL)
def test_parse_args_argument_error_handling():
    with (
        allure.step("ArgumentError simulation"),
        patch.object(
            argparse.ArgumentParser,
            "parse_args",
            side_effect=argparse.ArgumentError(None, "Custom error"),
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        parse_args()

    assert_equal(
        exc_info.value.code,
        -1,
        "Exit Code validation",
    )
