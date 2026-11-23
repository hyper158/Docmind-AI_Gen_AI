import pytest
from app.api.routes import health, documents, sessions
from app.schemas.session_schema import SessionCreateRequest
from app.database.initialization import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()


def test_health_endpoint():
    res = health.health_check()
    assert res["status"] == "healthy"
    assert "version" in res
    assert "model" in res


def test_list_documents_empty_or_existing():
    res = documents.list_documents()
    assert hasattr(res, "documents")
    assert hasattr(res, "total_count")
    assert res.total_count >= 0


def test_create_and_delete_session():
    # 1. Create session
    req = SessionCreateRequest(session_name="Test Biology Session")
    sess = sessions.create_session(req)
    assert sess.session_name == "Test Biology Session"
    sid = sess.session_id

    # 2. Get session
    fetched = sessions.get_session(sid)
    assert fetched.session_id == sid
    assert fetched.session_name == "Test Biology Session"

    # 3. Delete session
    del_res = sessions.delete_session(sid)
    assert del_res["success"] is True

    # 4. Verify 404 after deletion
    with pytest.raises(Exception):
        sessions.get_session(sid)


def test_evaluation_summary_and_history():
    from app.api.routes import evaluation

    # Test summary
    summary = evaluation.get_evaluation_summary()
    assert summary.has_evaluation is True
    assert summary.latest_run is not None
    assert summary.latest_run.total_questions > 0

    # Test history
    history = evaluation.get_evaluation_history()
    assert history.total_count >= 1
    assert len(history.runs) >= 1

    # Test results
    results = evaluation.get_evaluation_results(limit=5)
    assert "results" in results
    assert len(results["results"]) <= 5


@pytest.mark.asyncio
async def test_summarization_endpoints():
    from app.api.routes import summarization
    from app.services.summarization.summarization_service import SummarizationService

    mock_service = SummarizationService(mock_mode=True)

    # 1. Test get summary on non-existent document raises 404
    with pytest.raises(Exception):
        await summarization.get_document_summary_endpoint(
            document_id="doc_non_existent",
            summarization_service=mock_service,
        )

    # 2. Test status on non-existent document raises 404
    with pytest.raises(Exception):
        await summarization.get_summarization_status_endpoint(
            document_id="doc_non_existent",
            summarization_service=mock_service,
        )


