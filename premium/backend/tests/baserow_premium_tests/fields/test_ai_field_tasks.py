from unittest.mock import patch

import pytest
from baserow_premium.fields.tasks import generate_ai_values_for_rows

from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.generative_ai.exceptions import GenerativeAIPromptError


@pytest.mark.django_db
@pytest.mark.field_ai
@patch("baserow.contrib.database.rows.signals.rows_updated.send")
def test_generate_ai_field_value_view_generative_ai(
    patched_rows_updated, premium_data_fixture
):
    premium_data_fixture.register_fake_generate_ai_type()
    user = premium_data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = premium_data_fixture.create_database_application(
        user=user, name="database"
    )
    table = premium_data_fixture.create_database_table(name="table", database=database)
    field = premium_data_fixture.create_ai_field(
        table=table, name="ai", ai_prompt="'Hello'"
    )

    rows = RowHandler().create_rows(user, table, rows_values=[{}])

    assert patched_rows_updated.call_count == 0
    generate_ai_values_for_rows(user.id, field.id, [rows[0].id])
    assert patched_rows_updated.call_count == 1
    updated_row = patched_rows_updated.call_args[1]["rows"][0]
    assert getattr(updated_row, field.db_column) == "Generated: Hello"
    assert patched_rows_updated.call_args[1]["updated_field_ids"] == set([field.id])


@pytest.mark.django_db
@pytest.mark.field_ai
@patch("baserow.contrib.database.rows.signals.rows_updated.send")
def test_generate_ai_field_value_view_generative_ai_parse_formula(
    patched_rows_updated, premium_data_fixture
):
    premium_data_fixture.register_fake_generate_ai_type()
    user = premium_data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = premium_data_fixture.create_database_application(
        user=user, name="database"
    )
    table = premium_data_fixture.create_database_table(name="table", database=database)
    firstname = premium_data_fixture.create_text_field(table=table, name="firstname")
    lastname = premium_data_fixture.create_text_field(table=table, name="lastname")
    formula = f"concat('Hello ', get('fields.field_{firstname.id}'), ' ', get('fields.field_{lastname.id}'))"
    field = premium_data_fixture.create_ai_field(
        table=table, name="ai", ai_prompt=formula
    )

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{firstname.id}": "Bram", f"field_{lastname.id}": "Wiepjes"},
        ],
    )

    assert patched_rows_updated.call_count == 0
    generate_ai_values_for_rows(user.id, field.id, [rows[0].id])
    assert patched_rows_updated.call_count == 1
    updated_row = patched_rows_updated.call_args[1]["rows"][0]
    assert getattr(updated_row, field.db_column) == "Generated: Hello Bram Wiepjes"
    assert patched_rows_updated.call_args[1]["updated_field_ids"] == set([field.id])


@pytest.mark.django_db
@pytest.mark.field_ai
@patch("baserow.contrib.database.rows.signals.rows_updated.send")
def test_generate_ai_field_value_view_generative_ai_invalid_field(
    patched_rows_updated, premium_data_fixture
):
    premium_data_fixture.register_fake_generate_ai_type()
    user = premium_data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = premium_data_fixture.create_database_application(
        user=user, name="database"
    )
    table = premium_data_fixture.create_database_table(name="table", database=database)
    firstname = premium_data_fixture.create_text_field(table=table, name="firstname")
    formula = "concat('Hello ', get('fields.field_0'))"
    field = premium_data_fixture.create_ai_field(
        table=table, name="ai", ai_prompt=formula
    )

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{f"field_{firstname.id}": "Bram"}],
    )
    assert patched_rows_updated.call_count == 0
    generate_ai_values_for_rows(user.id, field.id, [rows[0].id])
    assert patched_rows_updated.call_count == 1
    updated_row = patched_rows_updated.call_args[1]["rows"][0]
    assert getattr(updated_row, field.db_column) == "Generated: Hello "


@pytest.mark.django_db
@pytest.mark.field_ai
@patch("baserow.contrib.database.rows.signals.rows_ai_values_generation_error.send")
@patch("baserow.contrib.database.rows.signals.rows_updated.send")
def test_generate_ai_field_value_view_generative_ai_invalid_prompt(
    patched_rows_updated, patched_rows_ai_values_generation_error, premium_data_fixture
):
    premium_data_fixture.register_fake_generate_ai_type()
    user = premium_data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )

    database = premium_data_fixture.create_database_application(
        user=user, name="database"
    )
    table = premium_data_fixture.create_database_table(name="table", database=database)
    firstname = premium_data_fixture.create_text_field(table=table, name="firstname")
    formula = "concat('Hello ', get('fields.field_0'))"
    field = premium_data_fixture.create_ai_field(
        table=table,
        name="ai",
        ai_generative_ai_type="test_generative_ai_prompt_error",
        ai_prompt=formula,
    )

    rows = RowHandler().create_rows(
        user,
        table,
        rows_values=[{f"field_{firstname.id}": "Bram"}],
    )

    assert patched_rows_ai_values_generation_error.call_count == 0

    with pytest.raises(GenerativeAIPromptError):
        generate_ai_values_for_rows(user.id, field.id, [rows[0].id])

    assert patched_rows_updated.call_count == 0
    assert patched_rows_ai_values_generation_error.call_count == 1
    call_args_rows = patched_rows_ai_values_generation_error.call_args[1]["rows"]
    assert len(call_args_rows) == 1
    assert rows[0].id == call_args_rows[0].id
    assert patched_rows_ai_values_generation_error.call_args[1]["field"] == field
    assert (
        patched_rows_ai_values_generation_error.call_args[1]["error_message"]
        == "Test error"
    )
