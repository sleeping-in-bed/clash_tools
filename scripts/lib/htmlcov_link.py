#!/usr/bin/env python3
"""Generate an index.html that links to sub coverage reports."""

from pathlib import Path

import click
from bs4 import BeautifulSoup


@click.command()
@click.option(
    "--dir",
    "htmlcov_dir",
    default="htmlcov",
    help="Coverage HTML output directory.",
)
def main(htmlcov_dir: Path) -> None:
    """Generate an index.html that links to sub coverage reports."""
    links = []
    if not htmlcov_dir.exists():
        click.echo(f"Directory '{htmlcov_dir}' does not exist.", err=True)
        raise SystemExit(1)

    for item in sorted(htmlcov_dir.iterdir()):
        index_file = item / "index.html"
        if item.is_dir() and index_file.exists():
            soup = BeautifulSoup(
                Path(index_file).read_text(encoding="utf-8"),
                "html.parser",
            )
            coverage_span = soup.find("span", class_="pc_cov")
            content = (
                f'<li><a href="{item.name}/index.html">{item.name} Coverage Report</a><br/>'
                f"<p>Coverage report: {coverage_span.text}</p></li>"
            )
            links.append(content)

    links_html = "\n".join(links)
    content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Coverage Reports</title>
</head>
<body>
    <h1>Coverage Reports</h1>
    <ul>
        {links_html}
    </ul>
</body>
</html>"""

    index_path = htmlcov_dir / "index.html"
    index_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
