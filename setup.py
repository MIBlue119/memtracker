from setuptools import setup, find_packages
# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='memtracker',
    version='0.1.3',
    description='A simple utility to track and log peak CPU and GPU memory usage of a function.',
    author='MIBlue119',  
    author_email='miblue119@gmail.com',  
    packages=find_packages(),
    install_requires=[
        'pandas',
        'psutil',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Debuggers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='memory tracking, CPU, GPU, memory usage',
    project_urls={
        'Bug Reports': 'https://github.com/MIBlue119/memtracker/issues',  # Replace with your GitHub repo URL
        'Source': 'https://github.com/MIBlue119/memtracker',  # Replace with your GitHub repo URL
    },
    # Add the following lines for the long description
    long_description=long_description,
    long_description_content_type="text/markdown",    
)
