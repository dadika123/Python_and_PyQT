from setuptools import setup, find_packages

setup(name="gb_messenger_server",
      version="0.0.1",
      description="gb_messenger_server",
      author="Anatolii Tsirkunenko",
      author_email="tsirkunenkoat@gmail.com",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
