"""Unit tests for knowledge/rag_index.py — FAISS retrieval."""


class TestRAGIndexInit:
    def test_index_initializes_with_documents(self):
        import knowledge.rag_index as rag
        rag.init_index()
        assert len(rag._DOCS) >= 3
        assert rag._INDEX is not None

    def test_retrieve_context_returns_string(self):
        import knowledge.rag_index as rag
        rag.init_index()
        result = rag.retrieve_context("Apple revenue")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_retrieve_context_on_empty_query(self):
        import knowledge.rag_index as rag
        rag.init_index()
        result = rag.retrieve_context("")
        assert isinstance(result, str)

    def test_retrieve_context_limits_chunks(self):
        import knowledge.rag_index as rag
        rag.init_index()
        result = rag.retrieve_context("financial report", top_k=2)
        chunks = result.split("\n\n")
        assert len(chunks) <= 2

    def test_retrieve_context_returns_relevant_docs(self):
        import knowledge.rag_index as rag
        rag.init_index()
        result = rag.retrieve_context("net income revenue profit")
        assert isinstance(result, str)
        assert len(result) > 0
