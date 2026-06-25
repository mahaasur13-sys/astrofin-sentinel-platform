# Test PR for CodeRabbit — smoke test
#
# Этот файл создан для тестирования CodeRabbit-ревью.
# Здесь намеренно нет осмысленной логики — только sanity-check,
# что авто-ревьюер видит PR и пишет комментарий.


HELLO_MESSAGE = "CodeRabbit smoke test"
"""Заглушка, чтобы было что импортировать в smoke-тестах."""


def smoke_greeting(name: str = "world") -> str:
    """Вернуть приветствие; чистая функция, side-effects отсутствуют."""
    return f"Hello, {name}! {HELLO_MESSAGE}"
