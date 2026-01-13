from pathlib import Path

from sphinx.application import Sphinx


def setup(app: Sphinx):
    # Register theme
    theme_dir = Path(__file__).parent.resolve()
    app.add_html_theme("astropy", theme_dir)
    app.add_css_file("astropy.css", priority=650)
