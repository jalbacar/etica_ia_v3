"""
Ethical Guard - Python Decorator for Ethical AI Validation

Automatically validates inputs and outputs against ethical principles
using the Ethical Observability System orchestrator.
"""

from setuptools import setup, find_packages

setup(
    name="ethical-guard",
    version="0.1.0",
    author="Your Team",
    author_email="team@example.com",
    description="Python decorator for automatic ethical validation of AI systems",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/ethic-obs-v2",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="ethics ai validation bias compliance unesco eu-ai-act",
    project_urls={
        "Documentation": "https://github.com/yourorg/ethic-obs-v2/docs",
        "Source": "https://github.com/yourorg/ethic-obs-v2",
        "Tracker": "https://github.com/yourorg/ethic-obs-v2/issues",
    },
)
