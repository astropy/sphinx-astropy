pytest_plugins = ('sphinx.testing.fixtures',)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "sphinx(builder, testroot='name'): Run sphinx on a site"
    )
