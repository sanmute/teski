from __future__ import annotations

from textwrap import dedent

from tools.validate_content import main


def test_validate_content_success(tmp_path, capsys):
    tmp_path.joinpath("one.md").write_text(
        dedent(
            """\
            ---
            id: sample_mcq
            concept: Basics
            type: mcq
            question: |
              What is 2 + 2?
            choices:
              - text: 4
                correct: true
              - text: 3
            ---
            """
        ),
        encoding="utf-8",
    )
    tmp_path.joinpath("two.md").write_text(
        dedent(
            """\
            ---
            id: sample_numeric
            concept: Basics
            type: numeric
            question: |
              Solve for x in x + 1 = 2.
            answer:
              value: 1
            ---
            """
        ),
        encoding="utf-8",
    )

    code = main(["--content", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Validated 2 exercise(s)" in captured.out


def test_validate_content_reports_errors(tmp_path, capsys):
    tmp_path.joinpath("one.md").write_text(
        dedent(
            """\
            ---
            id: duplicate_id
            concept: Basics
            type: short_answer
            question: |
              Explain gravity.
            rubric:
              must_include: ["mass"]
            ---
            """
        ),
        encoding="utf-8",
    )
    tmp_path.joinpath("two.md").write_text(
        dedent(
            """\
            ---
            id: duplicate_id
            concept: Basics
            type: numeric
            question: |
              What is the answer?
            ---
            """
        ),
        encoding="utf-8",
    )

    code = main(["--content", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "duplicate exercise id detected: duplicate_id" in captured.err
    assert "numeric exercise must define answer.value" in captured.err
