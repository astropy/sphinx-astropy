# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# Astropy shared Sphinx settings.  These settings are shared between
# astropy itself and affiliated packages.
#
# v3 extends v2 to use the shared sunpy-sphinx-theme settings

from .v2 import *  # noqa: F403

html_theme = "sunpy"

html_theme_options = {
    "sst_site_root": "https://astropy.org",
    "navbar_links": [
        (
            "About",
            [
                ("About Astropy", "about.html", 2),
                ("Code of Conduct", "code_of_conduct.html", 2),
                ("Acknowledging & Citing", "acknowledging.html", 2),
                ("History", "history.html", 2),
            ],
        ),
        (
            "Documentation",
            [
                # core first
                ("astropy", "https://docs.astropy.org", 3),
                # Coordinated
                ("asdf-astropy", "https://asdf-astropy.readthedocs.io", 3),
                ("astropy-healpix", "https://astropy-healpix.readthedocs.io", 3),
                ("astroquery", "https://astroquery.readthedocs.io", 3),
                ("ccdproc", "https://ccdproc.readthedocs.io", 3),
                ("photutils", "https://photutils.readthedocs.io", 3),
                ("regions", "https://astropy-regions.readthedocs.io", 3),
                ("reproject", "https://reproject.readthedocs.io", 3),
                ("specreduce", "https://specreduce.readthedocs.io", 3),
                ("specutils", "https://specutils.readthedocs.io", 3),
            ],
        ),
        ("Get Help", "help.html", 2),
        ("Contribute", "contribute.html", 2),
        ("Affiliated Packages", "affiliated/index.html", 2),
        ("Team", "team.html", 2),
    ],
}
