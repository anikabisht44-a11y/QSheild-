from setuptools import setup, find_packages

setup(
    name="qshield",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "plotly>=5.17.0",
        "cryptography>=41.0.0",
        "fpdf2>=2.7.0",
        "markdown>=3.5.0",
    ],
)
