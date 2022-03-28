from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'logs', 'server', 'unit_tests'],
}
setup(name='gb_messenger_server',
      version='0.0.1',
      description='gb_messenger_server',
      options={
          'build_exe': build_exe_options
      },
      executables=[Executable('server.py',
                              base='Win32GUI',
                              targetName='server.exe',
                              )]
      )
