from setuptools import setup, find_packages

setup(
    name='xmlforge',
    version='2.0.0',
    description='Professional XML Generator from XSD schemas with GUI and IBM MQ integration',
    author='Deivid Jhonatan Paio',
    author_email='deividjpaio@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pymqi>=1.12.0',
    ],
    entry_points={
        'console_scripts': [
            'xmlforge=xmlforge.app:main'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.8',
)
