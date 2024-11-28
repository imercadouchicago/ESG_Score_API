from setuptools import setup, find_packages

setup(
    name="esg_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'selenium',
        'pandas',
        'webdriver-manager',
        'requests',
        'beautifulsoup4',
        'numexpr>=2.8.4',
        'bottleneck>=1.3.6'
    ],
    python_requires='>=3.9',
)

