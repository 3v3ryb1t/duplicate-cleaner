from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import allure
from allure import attachment_type
from pytest import ExceptionInfo

T = TypeVar("T")


def assert_equal[T: (str, int)](actual: T, expected: T, step="Equality check"):
    with allure.step(step):
        with allure.step(f"Expected result: {expected}"):
            pass
        with allure.step(f"Actual result: {actual}"):
            pass
        assert actual == expected


def assert_equal_with_attachment[T](
    actual: T,
    expected: T,
    attachment_type: attachment_type,
    step: str = "Equality check",
):
    with allure.step(step):
        allure.attach(
            expected,
            name="Expected result",
            attachment_type=allure.attachment_type.TEXT,
        )

        allure.attach(
            actual,
            name="Actual result",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert actual == expected


def assert_lists_same[T: (str | Path)](
    actual: list[T], expected: list[T], step="Lists comparison"
):
    with allure.step(step):
        sorted_expected = sorted(expected, key=lambda item: str(item))
        sorted_actual = sorted(actual, key=lambda item: str(item))

        expected_text = "\n".join(str(item) for item in sorted_expected)
        actual_text = "\n".join(str(item) for item in sorted_actual)

        allure.attach(
            expected_text,
            name="Expected list",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            actual_text,
            name="Actual list",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert_equal(len(actual), len(expected), "Lists length comparison")
        assert_bool_result(
            True,
            lambda a=sorted_actual, e=sorted_expected: all(
                act == exp for act, exp in zip(a, e)
            ),
            "Lists elements comparison",
        )


def assert_lists_diff[T](
    listA: list[T],
    listB: list[T],
    expected_diff: list[T],
    step="List diff validation",
):
    with allure.step(step):
        actual_diff = list(set(listA) ^ set(listB))

        expected_text = "\n".join(str(item) for item in sorted(listB, key=str))
        actual_text = "\n".join(str(item) for item in sorted(listA, key=str))
        expected_diff_text = "\n".join(
            str(item) for item in sorted(expected_diff, key=str)
        )
        actual_diff_text = "\n".join(str(item) for item in sorted(actual_diff, key=str))

        allure.attach(
            expected_text,
            name="list A",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            actual_text,
            name="list B",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            expected_diff_text,
            name="Expected diff",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            actual_diff_text,
            name="Actual diff",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert sorted(actual_diff, key=str) == sorted(expected_diff, key=str)


@allure.step("{step}")
def assert_exception(
    actual_exception: ExceptionInfo,
    expected_exception: type[BaseException],
    expected_msg_substring: str | None,
    step="Exception check",
):
    with allure.step(
        f"Checking exception type: Expected '{expected_exception.__name__}'"
    ):
        with allure.step(f"Actual type: '{actual_exception.type.__name__}'"):
            pass
        assert actual_exception.type is expected_exception

    if expected_msg_substring:
        actual_msg = str(actual_exception.value)
        with allure.step("Checking error message for substring"):
            with allure.step(f"Expected substring: '{expected_msg_substring}'"):
                pass
            with allure.step(f"Actual message: '{actual_msg}'"):
                pass
            assert expected_msg_substring in actual_msg


def assert_bool_result(
    expected: bool, f: Callable, step: str, message: str | None = None
):
    with allure.step(step):
        assert f() == expected, message


@allure.step("{step}")
def assert_contains(text: str, substr: str, step="Check substring"):
    assert substr in text
