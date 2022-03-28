from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'logs', 'client', 'unit_tests'],
}
setup(name='gb_messenger_client',
      version='0.0.1',
      description='gb_messenger_client',
      options={
          'build_exe': build_exe_options
      },
      executables=[Executable('client.py',
                              base='Win32GUI',
                              targetName='client.exe',
                              )]
      )
