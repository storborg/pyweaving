from __future__ import print_function

from setuptools import setup, find_packages


setup(name='pyweaving',
      version=__import__('pyweaving').__version__,
      description='Python Weaving Tools',
      long_description='',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Topic :: Multimedia :: Graphics',
      ],
      keywords='weaving handweaving wif draft pattern',
      url='https://github.com/storborg/pyweaving',
      author='Scott Torborg',
      author_email='storborg@gmail.com',
      install_requires=[
          'Pillow>=2.1.0',      # Provides PIL
          'svglib>=0.6.3',
          'reportlab>=3.1.44',
          'six>=1.5.2',
      ],
      license='MIT',
      packages=find_packages(),
      test_suite='nose.collector',
      tests_require=['nose'],
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [console_scripts]
      pyweaving = pyweaving.cmd:main
      """)
