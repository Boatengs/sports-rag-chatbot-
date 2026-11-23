import numpy as np

from sportzbot.report import answer_in_sources, norm, rates
from sportzbot.run import TEMPLATE, shard_rows
from sportzbot.systems import clean_query, mmr
from sportzbot.wiki import html_to_passages

HTML = """
<div class="mw-parser-output">
<table class="infobox"><tr><th>Champions</th><td>Spain (4th title)</td></tr><tr><th>Runners-up</th><td>England</td></tr></table>
<p>UEFA Euro 2024 was held in Germany.<sup class="reference">[1]</sup></p>
<div class="mw-heading mw-heading2"><h2>Final</h2></div>
<p>Spain beat England 2–1 in Berlin.</p>
<table class="wikitable"><caption>Top scorers</caption>
<tr><th>Player</th><th>Goals</th></tr>
<tr><td>Dani Olmo</td><td>3</td></tr>
</table>
<ul><li>Player of the tournament: Rodri</li></ul>
<div class="navbox">Navigation junk</div>
<div class="mw-heading mw-heading2"><h2>References</h2></div>
<p>Should be dropped.</p>
</div>
"""


def test_html_to_passages_keeps_tables_and_sections():
    ps = html_to_passages("UEFA Euro 2024", HTML, 123)
    text = "\n".join(p.render() for p in ps)
    assert "Champions: Spain (4th title)" in text
    assert "Top scorers: Player: Dani Olmo; Goals: 3" in text
    assert "UEFA Euro 2024 > Final" in text
    assert "- Player of the tournament: Rodri" in text
    assert "[1]" not in text and "Navigation junk" not in text and "Should be dropped" not in text
    assert all(p.revid == 123 for p in ps)


def test_long_paragraph_is_split():
    html = '<div class="mw-parser-output"><p>' + " ".join(f"w{i}" for i in range(500)) + "</p></div>"
    ps = html_to_passages("T", html, 1, max_words=120)
    assert len(ps) == 5 and all(len(p.text.split()) <= 120 for p in ps)


def test_mmr_prefers_diverse():
    q = np.array([1.0, 1.0])
    docs = np.array([[1.0, 0.05], [1.0, 0.06], [0.05, 1.0]])
    # the near copy of the first pick loses to the different but still relevant document
    assert mmr(q, docs, 2) == [1, 2]


def test_rates_and_f1():
    r = rates(np.array(["CORRECT", "INCORRECT", "NOT_ATTEMPTED", "CORRECT"]))
    assert r["correct"] == 0.5 and r["incorrect"] == 0.25 and r["not_attempted"] == 0.25
    assert abs(r["accuracy_when_answered"] - 2 / 3) < 1e-9
    assert abs(r["f1"] - 2 * (2 / 3) * 0.5 / (2 / 3 + 0.5)) < 1e-9


def test_answer_in_sources_normalises():
    assert norm("Kylian Mbappé!") == "kylian mbappe"
    assert answer_in_sources("Mbappé", [{"text": "signed Kylian Mbappe in 2024"}])
    assert not answer_in_sources("Rodri", [{"text": "Vinicius Junior"}])


def test_clean_query_and_shards():
    assert clean_query('Query: "Euro 2024 final"\nextra') == "Euro 2024 final"
    rows = list(range(10))
    assert sorted(shard_rows(rows, 0, 3) + shard_rows(rows, 1, 3) + shard_rows(rows, 2, 3)) == rows


def test_grader_template_has_slots():
    for slot in ("{question}", "{target}", "{predicted_answer}"):
        assert TEMPLATE.count(slot) == 1
