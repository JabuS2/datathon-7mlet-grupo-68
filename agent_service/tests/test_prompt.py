from agent_service.agent import SYSTEM_PROMPT


def test_prompt_requires_tool_call_for_dashboard_requests():
    prompt = SYSTEM_PROMPT.lower()
    assert "get_users_overview" in prompt
    # Must instruct calling the tool on every dashboard/overview request.
    assert "must call" in prompt
    assert "every time" in prompt


def test_prompt_forbids_answering_from_memory():
    prompt = SYSTEM_PROMPT.lower()
    assert "never answer these requests from memory" in prompt


def test_prompt_forbids_reproducing_widget_data_as_text():
    prompt = SYSTEM_PROMPT.lower()
    assert "never transcribe the widget" in prompt


def test_prompt_covers_followup_phrasings():
    # Guard the specific rephrasings that previously failed to trigger the tool.
    assert "I want a dashboard" in SYSTEM_PROMPT


def test_prompt_requires_schema_and_sql_tools_for_data_questions():
    prompt = SYSTEM_PROMPT.lower()
    assert "get_db_schema" in prompt
    assert "run_sql_query" in prompt
    assert "never by guessing table or column names" in prompt


def test_prompt_forbids_write_queries():
    prompt = SYSTEM_PROMPT.lower()
    assert "never attempt insert/update/delete/ddl" in prompt
