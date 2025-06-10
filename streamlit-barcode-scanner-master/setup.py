import setuptools

setuptools.setup(
    name="streamlit-barcode-scanner",
    version="0.0.1",
    author="FloWide Ltd.",
    author_email="",
    description="Streamlit component for barcode scanning using html5-qrcode",
    long_description="",
    long_description_content_type="text/plain",
    url="https://github.com/FloWide/streamlit-barcode-scanner",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.6",
    install_requires=[
        "streamlit >= 0.63",
    ],
)
