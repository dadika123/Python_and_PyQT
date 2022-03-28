import dis
import socket


class ClientMaker(type):
    """
    Метакласс, проверяющий что в результирующем классе нет серверных
    вызовов таких как: accept, listen. Также проверяется, что сокет не
    создаётся внутри конструктора класса.
    """

    def __new__(cls, name, bases, dct):
        # Check all instances at class creation and throw error if the are of socket instance
        for key, value in dct.items():
            if not hasattr(value, '__call__'):
                if isinstance(value, socket.socket):
                    raise ValueError(f'Сокет не может быть создан на уровне создания класса!')
        return type.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        sock_alias = ['sock', 'socket', 'client']
        com_fcn = ['get_message', 'send_message']
        forbidden_sock_cmd = ['accept', 'listen']
        class_methods = {}
        class_attrs = []
        found_com_fcn = False

        # Get class methods
        for key, value in dct.items():
            if hasattr(value, '__call__'):
                class_methods.update({key: value})

        # Get class attributes
        for instruction in dis.get_instructions(dct['__init__']):
            if instruction.opname == 'STORE_ATTR':
                class_attrs.append(getattr(instruction, 'argval'))

        # Check if client has a socket definition in its init
        if not [class_attr for class_attr in class_attrs if class_attr in sock_alias]:
            raise ValueError(f'У клиента должен быть сокет!')

        # Check each class method and check whether socket was called with accept or listen functions
        for class_method in class_methods.values():
            instructions = dis.get_instructions(class_method)
            sock_found = False
            for instruction in instructions:
                # Set a flag if any of communication functions is used
                if instruction.opname == 'LOAD_GLOBAL':
                    if instruction.argval in com_fcn:
                        found_com_fcn = True
                # If method call goes right after the socket load and method is accept or listen - throw an error
                if sock_found:
                    if instruction.opname == 'LOAD_METHOD':
                        instruction_cmd = instruction.argval
                        if instruction_cmd in forbidden_sock_cmd:
                            raise TypeError(f'Использование метода {instruction_cmd} у сокета '
                                            f'недопустимо в классе {name}')
                    sock_found = False
                if instruction.opname == 'LOAD_ATTR' and instruction.argval in sock_alias:
                    sock_found = True
        # Check if one of the 2 communication methods is present
        if not found_com_fcn:
            raise ValueError(f'Отсутствуют вызовы функций, работающих с сокетами')
        type.__init__(cls, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        for arg in args:
            if isinstance(arg, socket.socket):
                if arg.family != socket.AddressFamily.AF_INET or arg.type != socket.SocketKind.SOCK_STREAM:
                    raise ValueError(f'Сокеты должны использоваться для TCP')
        return super().__call__(*args, **kwargs)
