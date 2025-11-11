from setuptools import setup, find_packages

setup(
    name="mcp-client",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "httpx>=0.23.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "python-dateutil>=2.8.2"
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-httpx>=0.24.0",
            "pytest-cov>=4.1.0"
        ]
    }
)
