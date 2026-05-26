"""Regenerate binary fixtures (PDFs) from text sources.

Run manually:

    .venv/bin/python tests/fixtures/build_fixtures.py

The generated PDFs are committed under tests/fixtures/pdf/ so the test
suite does not depend on fpdf2 at run time.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).parent
OUT = HERE / "pdf"
OUT.mkdir(exist_ok=True)


HANDBOOK_PAGES = [
    """Acme Employee Handbook

Welcome to Acme. This handbook covers the policies every employee should
know. Please read it thoroughly during your first week.

Leave Policy
Employees receive 21 days paid leave annually. Leave accrual begins on the
employee start date and resets every January 1st. Unused leave may be
carried over up to a maximum of 5 days.""",
    """Office Address
The Acme office is located at 221B Baker Street, London. Office hours are
9:00 AM to 6:00 PM, Monday through Friday. Visitors must sign in at the
front desk.

Remote Work
Employees may work remotely up to three days per week with manager
approval. Equipment requests must be filed through the IT portal.""",
    """Code of Conduct
All employees are expected to act with integrity and respect. Harassment of
any kind is not tolerated and will result in disciplinary action up to
termination.

Reporting
Concerns may be raised confidentially through the HR portal or directly to
the Chief People Officer. Acme prohibits retaliation against good-faith
reporters.""",
]


SECURITY_PAGES = [
    """Acme Security Policy

Passwords must be at least 12 characters and include a mix of letters,
numbers, and symbols. Reuse across systems is forbidden.""",
    """Incident Response
All suspected security incidents must be reported to the SOC within 15
minutes of discovery. The on-call rotation is maintained in the runbook.""",
]


def _write_pdf(path: Path, pages: list[str]) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for page_text in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        for line in page_text.splitlines() or [""]:
            pdf.multi_cell(180, 7, line if line else " ")
    pdf.output(str(path))


def main() -> None:
    _write_pdf(OUT / "handbook.pdf", HANDBOOK_PAGES)
    _write_pdf(OUT / "security_policy.pdf", SECURITY_PAGES)
    print(f"wrote {OUT}/handbook.pdf ({len(HANDBOOK_PAGES)} pages)")
    print(f"wrote {OUT}/security_policy.pdf ({len(SECURITY_PAGES)} pages)")


if __name__ == "__main__":
    main()
