"""Tests for logdiff.templater and logdiff.cli_templater."""

import json
import pytest
from logdiff.templater import (
    Template,
    TemplateError,
    save_template,
    load_template,
    list_templates,
    remove_template,
)
from logdiff.cli_templater import add_templater_args, handle_templater
import argparse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_template(name="default", fmt="text", **kwargs) -> Template:
    return Template(name=name, format=fmt, **kwargs)


def build_args(store, cmd, **kwargs):
    ns = argparse.Namespace(template_cmd=cmd, **kwargs)
    return ns


# ---------------------------------------------------------------------------
# Unit tests — Template dataclass
# ---------------------------------------------------------------------------

def test_template_repr():
    t = make_template("slack", "json")
    assert "slack" in repr(t)
    assert "json" in repr(t)


def test_template_roundtrip():
    t = make_template(
        "brief", "markdown",
        fields=["status", "latency"],
        summary_only=True,
        min_score=2.5,
        description="quick brief",
    )
    restored = Template.from_dict(t.to_dict())
    assert restored.name == t.name
    assert restored.format == t.format
    assert restored.fields == t.fields
    assert restored.summary_only is True
    assert restored.min_score == 2.5
    assert restored.description == "quick brief"


# ---------------------------------------------------------------------------
# Unit tests — persistence
# ---------------------------------------------------------------------------

def test_save_and_load_template(tmp_path):
    store = str(tmp_path / "templates.json")
    t = make_template("mytemplate", "csv", fields=["level"])
    save_template(t, path=store)
    loaded = load_template("mytemplate", path=store)
    assert loaded.name == "mytemplate"
    assert loaded.format == "csv"
    assert loaded.fields == ["level"]


def test_load_missing_template_raises(tmp_path):
    store = str(tmp_path / "templates.json")
    with pytest.raises(TemplateError, match="not found"):
        load_template("ghost", path=store)


def test_list_templates_returns_all(tmp_path):
    store = str(tmp_path / "templates.json")
    save_template(make_template("a", "text"), path=store)
    save_template(make_template("b", "json"), path=store)
    names = {t.name for t in list_templates(path=store)}
    assert names == {"a", "b"}


def test_list_templates_empty(tmp_path):
    store = str(tmp_path / "templates.json")
    assert list_templates(path=store) == []


def test_remove_template(tmp_path):
    store = str(tmp_path / "templates.json")
    save_template(make_template("todelete"), path=store)
    remove_template("todelete", path=store)
    with pytest.raises(TemplateError):
        load_template("todelete", path=store)


def test_remove_missing_template_raises(tmp_path):
    store = str(tmp_path / "templates.json")
    with pytest.raises(TemplateError):
        remove_template("nope", path=store)


# ---------------------------------------------------------------------------
# CLI handler tests
# ---------------------------------------------------------------------------

def test_add_templater_args_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_templater_args(sub)
    args = parser.parse_args(["template", "list"])
    assert args.template_cmd == "list"


def test_handle_templater_save_and_list(tmp_path, capsys, monkeypatch):
    store = str(tmp_path / "t.json")
    monkeypatch.setattr("logdiff.templater.TEMPLATE_FILE", store)
    monkeypatch.setattr("logdiff.cli_templater.save_template",
                        lambda t: save_template(t, path=store))
    monkeypatch.setattr("logdiff.cli_templater.list_templates",
                        lambda: list_templates(path=store))

    save_args = argparse.Namespace(
        template_cmd="save", name="ci", format="json",
        fields=["status"], exclude_fields=[], summary_only=False,
        min_score=None, description="CI template",
    )
    rc = handle_templater(save_args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ci" in out


def test_handle_templater_remove_missing_returns_one(tmp_path, monkeypatch):
    store = str(tmp_path / "t.json")
    monkeypatch.setattr("logdiff.cli_templater.remove_template",
                        lambda name: remove_template(name, path=store))
    args = argparse.Namespace(template_cmd="remove", name="ghost")
    rc = handle_templater(args)
    assert rc == 1
