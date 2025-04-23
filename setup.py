from setuptools import find_packages, setup

setup(
    name="password_manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flet",
        "pycryptodome",
        "pyperclip",
        "nest-asyncio",
    ],
)
