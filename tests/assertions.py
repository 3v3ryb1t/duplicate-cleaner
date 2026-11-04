from collections.abc import Callable
from functools import singledispatch
from pathlib import Path
from typing import Any, TypeVar

import allure
from allure import attachment_type
from pytest import ExceptionInfo

T = TypeVar("T", int, str)


@singledispatch
def assert_equal[T](actual: T, expected: T, step="Equality check"):
    with allure.step(step):
        with allure.step(f"Ожидаемый результат: {expected}"):
            pass
        with allure.step(f"Фактический результат: {actual}"):
            pass
        assert actual == expected


@singledispatch
def assert_equal_with_attachment[T](
    actual: T,
    expected: T,
    attachment_type: attachment_type,
    step: str = "Equality check",
):
    with allure.step(step):
        allure.attach(
            expected,
            name="Ожидаемый результат",
            attachment_type=allure.attachment_type.TEXT,
        )

        allure.attach(
            actual,
            name="Фактический результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert actual == expected


def assert_lists_same[T](actual: list[T], expected: list[T], step="Lists comparison"):
    with allure.step(step):
        sorted_expected = sorted(expected)
        sorted_actual = sorted(actual)

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
    step="List diff valiation",
):
    with allure.step(step):
        actual_diff = list(set(listA) ^ set(listB))

        expected_text = "\n".join(str(item) for item in sorted(listB))
        actual_text = "\n".join(str(item) for item in sorted(listA))
        expected_diff_text = "\n".join(str(item) for item in sorted(expected_diff))
        actual_diff_text = "\n".join(str(item) for item in sorted(actual_diff))

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

        assert sorted(actual_diff) == sorted(expected_diff)


@allure.step("{step}")
def assert_exception(
    actual_exception: ExceptionInfo,
    expected_exception: type[BaseException],
    expected_msg_substring: str = None,  # noqa: RUF013
    step="Проверка исключения",
):
    with allure.step(
        f"Проверка типа исключения: Ожидается '{expected_exception.__name__}'"
    ):
        with allure.step(f"Фактический тип: '{actual_exception.type.__name__}'"):
            pass
        assert actual_exception.type is expected_exception

    if expected_msg_substring:
        actual_msg = str(actual_exception.value)
        with allure.step("Проверка сообщения об ошибке на содержание подстроки"):
            with allure.step(f"Ожидаемый фрагмент: '{expected_msg_substring}'"):
                pass
            with allure.step(f"Фактическое сообщение: '{actual_msg}'"):
                pass
            assert expected_msg_substring in actual_msg


def assert_function_result(
    func: Callable[[], bool],
    expected_result: Any,
    *args: Any,
    step: str = "Проверка выполнения функции",
    **kwargs: Any,
) -> None:
    """
    Выполняет переданную функцию с аргументами и проверяет её возвращаемое значение.

    :param func: Ссылка на саму функцию (например, calculate_file_hash)
    :param expected_result: Ожидаемый результат выполнения
    :param args: Позиционные аргументы для тестируемой функции
    :param step: Имя родительского шага в Allure
    :param kwargs: Ключевые аргументы для тестируемой функции
    """
    with allure.step(step):
        with allure.step(
            f"Вызов функции '{func.__name__}' с аргументами: args={args}, kwargs={kwargs}"
        ):
            # Выполняем переданную функцию
            actual_result = func(*args, **kwargs)

        # Используем ваш существующий метод для проверки результата
        assert_equal(
            actual_result,
            expected_result,
            step=f"Валидация возвращаемого значения функции '{func.__name__}'",
        )


def assert_bool_result(
    expected: bool, f: Callable, step: str, message: str | None = None
):
    with allure.step(step):
        assert f() == expected, message


@allure.step("{step}")
def assert_starts_with(text: str, substr: str, step="Проверка начала строки"):
    assert text.startswith(substr)


@allure.step("{step}")
def assert_ends_with(text: str, substr: str, step="Проверка конца строки"):
    assert text.endswith(substr)


@allure.step("{step}")
def assert_contains(text: str, substr: str, step="Проверка подстроки"):
    assert substr in text


@allure.step("{step}")
def assert_dir_exists(path: Path, step="Проверка существования директории"):
    with allure.step(f"Ожидается, что папка существует: {path}"):
        pass
    with allure.step(
        f"Фактическое состояние: {'Существует' if path.is_dir() else 'Не найдена/Не папка'}"
    ):
        pass
    assert path.is_dir()


@allure.step("{step}")
def assert_path_not_exists(path: Path, step="Проверка удаления пути"):
    with allure.step(f"Ожидается, что путь удален: {path}"):
        pass
    with allure.step(
        f"Фактическое состояние: {'Все еще существует' if path.exists() else 'Успешно удален (Не существует)'}"
    ):
        pass
    assert not path.exists()
