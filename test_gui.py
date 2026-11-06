"""GUI smoke test: multi-file tabs sharing one set of filters.

Skipped automatically when tkinter or a display is not available
(on a headless Linux box run it with ``xvfb-run python -m pytest test_gui.py``).
"""
import os
import shutil
import time

import pytest

tk = pytest.importorskip("tkinter")
import xml_audit_viewer as v  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
F1 = os.path.join(HERE, "examples", "sample_audit_log_1.xml")
F2 = os.path.join(HERE, "examples", "sample_audit_log_2.xml")


@pytest.fixture()
def app():
    try:
        a = v.AuditViewer()
    except tk.TclError:
        pytest.skip("no display available")
    yield a
    try:
        for t in list(a.tabs.values()):
            a._stop_tail(t)
        a.destroy()
    except tk.TclError:
        pass


def pump(app, sec=1.0):
    end = time.time() + sec
    while time.time() < end:
        app.update()
        time.sleep(0.02)


def test_two_tabs_share_filters(app):
    app._open_path(F1)
    app._open_path(F2)
    pump(app, 1.5)
    t1, t2 = list(app.tabs.values())
    assert (len(t1.events), len(t2.events)) == (548, 334)
    assert app.cur is t2

    # opening the same file again reuses its tab
    app._open_path(F1)
    pump(app, 1.0)
    assert len(app.tabs) == 2 and app.cur is t1

    # one filter, every tab
    app.filter_result.set("Audit Failure")
    app._apply_filters()
    assert len(t1.filtered_indices) == 68
    assert len(t2.filtered_indices) == 0
    app.notebook.select(t2.frame)
    pump(app, 0.3)
    assert len(t2.tree.get_children()) == 0
    app._reset_filters()
    pump(app, 0.3)
    assert len(t2.tree.get_children()) == 334


def test_tail_in_a_tab_and_close(app, tmp_path):
    live = str(tmp_path / "live.xml")
    shutil.copy(F1, live)
    tab = app._open_path(live)
    pump(app, 1.0)
    n0 = len(tab.events)
    app._toggle_tail()
    pump(app, 1.5)
    assert tab.tailing
    line = open(F1, encoding="utf-8").read().splitlines()[0]
    with open(live, "a", encoding="utf-8") as f:
        f.write(line + "\n" + line + "\n")
    pump(app, 3.0)
    assert len(tab.events) == n0 + 2
    app._close_tab(tab)
    assert not app.tabs and not tab.tailing


def test_open_all_files_in_folder(app, tmp_path):
    for i, src in enumerate((F1, F2, F1)):
        shutil.copy(src, tmp_path / f"audit{i}.xml")
    (tmp_path / "notes.txt").write_text("not an audit file")
    assert app._open_all_in_dir(str(tmp_path), confirm=False) == 3
    pump(app, 1.5)
    assert len(app.tabs) == 3
    assert sorted(len(t.events) for t in app.tabs.values()) == [334, 548, 548]
    # the shared filters reach every one of those tabs
    app.filter_result.set("Audit Failure")
    app._apply_filters()
    assert sorted(len(t.filtered_indices) for t in app.tabs.values()) == [0, 68, 68]


def test_close_one_others_and_all(app):
    tabs = [app._open_path(F1), app._open_path(F2)]
    pump(app, 1.0)
    extra = app._add_tab("/nonexistent/third.xml")
    extra2 = app._add_tab("/nonexistent/fourth.xml")
    assert len(app.tabs) == 4
    app._close_tab(extra)                      # one
    assert len(app.tabs) == 3
    app._close_all_tabs(keep=tabs[0])          # all others
    assert list(app.tabs.values()) == [tabs[0]]
    app._close_all_tabs()                      # everything
    assert not app.tabs and app.cur is None
    assert app.status_var.get().startswith("Ready")
