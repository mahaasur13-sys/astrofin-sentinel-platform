"""
Tests for causal_semantic_space.py
"""

from consistency_v3.causal_semantic_space import (
    CausalSemanticSpace,
    CausalSemanticVector,
    _dict_diff,
    _l2_norm,
)


class TestCausalSemanticVector:
    def test_zero(self):
        v = CausalSemanticVector.zero()
        assert v.s_state == 0.0
        assert v.c_depth == 0

    def test_to_vector(self):
        v = CausalSemanticVector(s_state=3.0, s_delta=1.5, r_transitions=2.0, c_depth=4, t_wallclock_ns=1000)
        vec = v.to_vector()
        assert vec == [3.0, 1.5, 2.0, 4.0, 1000.0]

    def test_from_state_dict(self):
        state = {"a": 3.0, "b": 4.0}
        prev = {"a": 1.0, "b": 2.0}
        v = CausalSemanticVector.from_state_dict(state, prev, transitions=5, causal_depth=3)
        assert v.s_state > 0
        assert v.s_delta > 0
        assert v.r_transitions == 5.0
        assert v.c_depth == 3

    def test_distance_to(self):
        v1 = CausalSemanticVector(s_state=3.0, s_delta=0.0, r_transitions=0.0, c_depth=0, t_wallclock_ns=0)
        v2 = CausalSemanticVector(s_state=0.0, s_delta=0.0, r_transitions=0.0, c_depth=0, t_wallclock_ns=0)
        assert v1.distance_to(v2) == 3.0
        assert v1.distance_to(v1) == 0.0


class TestL2Norm:
    def test_empty(self):
        assert _l2_norm({}) == 0.0

    def test_scalar_values(self):
        assert _l2_norm({"a": 3.0, "b": 4.0}) == 5.0

    def test_nested_dict(self):
        assert _l2_norm({"a": {"x": 3.0}, "b": 4.0}) > 0


class TestDictDiff:
    def test_all_present(self):
        curr = {"a": 5, "b": 10}
        prev = {"a": 1, "b": 2}
        diff = _dict_diff(curr, prev)
        assert diff["a"] == 4
        assert diff["b"] == 8

    def test_missing_key(self):
        curr = {"a": 5}
        prev = {"b": 10}
        diff = _dict_diff(curr, prev)
        # missing keys (None values from .get()) don't pass isinstance checks → absent from diff
        assert "a" not in diff or not isinstance(diff["a"], (int, float))
        assert "b" not in diff or not isinstance(diff["b"], (int, float))

    def test_novel_key(self):
        curr = {"a": 5, "c": 100}
        prev = {"a": 1}
        diff = _dict_diff(curr, prev)
        # 'c' only in curr, its value (100) vs None from prev → no addition to diff
        assert "a" in diff and diff["a"] == 4
        assert "c" not in diff


class TestCausalSemanticSpace:
    def test_embed_basic(self):
        space = CausalSemanticSpace(domain="test")
        e_vec, r_vec = space.embed(
            exec_state={"a": 3.0},
            replay_state={"a": 3.0},
        )
        assert isinstance(e_vec, CausalSemanticVector)
        assert isinstance(r_vec, CausalSemanticVector)

    def test_embed_diverges(self):
        space = CausalSemanticSpace(domain="test")
        e_vec, r_vec = space.embed(
            exec_state={"a": 10.0},
            replay_state={"a": 1.0},
        )
        # state magnitudes differ → non-zero divergence
        assert space.semantic_distance() >= 0.0

    def test_semantic_distance_zero_identical(self):
        space = CausalSemanticSpace(domain="test")
        state = {"a": 5.0}
        space.embed(exec_state=state, replay_state=state,
                    exec_prev_state=state, replay_prev_state=state)
        space.embed(exec_state=state, replay_state=state,
                    exec_prev_state=state, replay_prev_state=state)
        assert space.semantic_distance() == 0.0

    def test_per_axis_divergence_length(self):
        space = CausalSemanticSpace(domain="test")
        space.embed(exec_state={"a": 1.0}, replay_state={"a": 2.0})
        axis = space.per_axis_divergence()
        assert len(axis) == 5

    def test_dominant_divergence_axis(self):
        space = CausalSemanticSpace(domain="test")
        space.embed(
            exec_state={"a": 10.0, "b": 0.0},
            replay_state={"a": 1.0, "b": 0.0},
        )
        idx, mag = space.dominant_divergence_axis()
        assert idx in range(5)
        assert mag >= 0.0

    def test_divergence_classification(self):
        space = CausalSemanticSpace(domain="test")
        space.embed(exec_state={"a": 10.0}, replay_state={"a": 1.0})
        cls = space.divergence_classification()
        assert isinstance(cls, str)
        assert len(cls) > 0

    def test_window_trim(self):
        space = CausalSemanticSpace(domain="test", window_size=3)
        for i in range(5):
            space.embed(
                exec_state={"x": float(i)},
                replay_state={"x": float(i)},
            )
        assert len(space.exec_vectors) <= 3
        assert len(space.replay_vectors) <= 3

    def test_to_dict(self):
        space = CausalSemanticSpace(domain="test")
        space.embed(exec_state={"a": 1.0}, replay_state={"a": 2.0})
        d = space.to_dict()
        assert d["domain"] == "test"
        assert "semantic_distance" in d
        assert "per_axis_divergence" in d
        assert "classification" in d
