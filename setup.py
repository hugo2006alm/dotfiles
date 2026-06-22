from setuptools import setup, find_packages

setup(
    name="dotfiles-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # System uses toml library for theme parsing
    ],
    entry_points={
        "console_scripts": [
            "dotfiles=dotfiles_api.presentation.cli:main",
        ],
    },
)
