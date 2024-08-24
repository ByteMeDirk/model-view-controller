from setuptools import setup, find_packages

setup(
    name="mvc",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "sqlalchemy",
        "PyYAML",
    ],
    entry_points="""
        [console_scripts]
        mvc=model_view_controller:cli
    """,
)
