import pytest

from app.llm import JSONParseError, parse_json_object


def test_plain():
    assert parse_json_object('{"a": 1}') == {"a": 1}


def test_fenced_with_prose():
    assert parse_json_object('Sure!\n```json\n{"a": [1, 2]}\n```\nDone') == {"a": [1, 2]}


def test_prose_around_and_nested():
    assert parse_json_object('Here: {"a": {"b": "x}y"}} thanks {not}') == {"a": {"b": "x}y"}}


def test_trailing_commas():
    assert parse_json_object('{"a": [1, 2,], "b": {"c": 1,},}') == {"a": [1, 2], "b": {"c": 1}}


def test_trailing_comma_inside_string_kept():
    assert parse_json_object('{"a": "x,}", }') == {"a": "x,}"}


def test_smart_quote_delimiters():
    assert parse_json_object('{“a”: “hello”}') == {"a": "hello"}


def test_smart_quotes_inside_string_untouched():
    assert parse_json_object('{"a": "it’s “fine”"}') == {"a": "it’s “fine”"}


@pytest.mark.parametrize("bad", ["", "no json here", "[1,2]", '{"a": ', "{a: 1}"])
def test_errors(bad):
    with pytest.raises(JSONParseError):
        parse_json_object(bad)


def test_error_has_snippet():
    with pytest.raises(JSONParseError) as ei:
        parse_json_object("nothing useful")
    assert "nothing useful" in str(ei.value)
