"""Data Room module.

Единственное место в кодбазе, откуда разрешён прямой
HTTP-доступ к внешним провайдерам данных.

Архитектурное правило R3 (см. .coderabbit.yaml) запрещает
`import requests` за пределами этой директории.
"""

from data_room import blueprint  # noqa: F401

__all__ = ["blueprint"]
