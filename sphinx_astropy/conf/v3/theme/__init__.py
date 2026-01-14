from pathlib import Path

from sphinx.application import Sphinx


def setup(app: Sphinx):
    # Register theme
    theme_dir = Path(__file__).parent.resolve()
    app.add_html_theme("astropy", theme_dir)
    app.add_css_file("css/astropy.css", priority=650)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
