from setuptools import find_packages, setup

setup(
    name="pokefisi",
    version="1.0.0",
    description="Simulador academico de combates tipo Pokemon con agentes de IA",
    packages=find_packages(exclude=["tests*", "scripts*", "docs*"]),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "pokefisi=backend.main:main",
        ],
    },
)
