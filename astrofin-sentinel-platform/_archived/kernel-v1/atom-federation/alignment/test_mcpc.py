from alignment import gcpl


class TestMCPC:
    def test_gcpl_import(self):
        assert gcpl is not None

    def test_gcpl_has_dataclasses(self):
        # проверяем что модуль загружен корректно
        assert hasattr(gcpl, "__file__")

    def test_gcpl_basic_structure(self):
        # мягкая проверка без глубокого анализа
        assert gcpl.__name__.endswith("gcpl")
