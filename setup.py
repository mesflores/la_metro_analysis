from setuptools import setup

setup(name='analysis',
      version='0.1',
      description='Metro data analysis',
      author='Marcel Flores',
      license='None',
      packages=['analysis'],
      install_requires=[
        "matplotlib",
        "numpy",
        "requests",
      ],
      entry_points = {
                      'console_scripts': ['analysis_fetch=analysis.main:fetch',
                                          'plot_times=analysis.main:main',
										 ],
                     },
      )
