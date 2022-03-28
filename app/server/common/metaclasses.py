import dis
import socket


class ServerMaker(type):
    """
    Метакласс, проверяющий что в результирующем классе нет клиентских
    вызовов таких как: connect. Также проверяется, что серверный
    сокет является TCP и работает по IPv4 протоколу.
    """

    def __init__(cls, name, bases, dct):
        sock_alias = ['sock', 'socket', 'server']
        com_fcn = ['get_message', 'send_message', 'process_message', 'process_client_message']
        forbidden_sock_cmd = ['connect', ]
        tcp_sock_cfg = ['AF_INET', 'SOCK_STREAM']
        class_methods = {}
        found_com_fcn = False

        # Get class methods
        for key, value in dct.items():
            if hasattr(value, '__call__'):
                class_methods.update({key: value})

        # Check each class method and check whether socket was called with accept or listen functions
        for class_method in class_methods.values():
            instructions = dis.get_instructions(class_method)
            sock_found = False
            sock_arg_counter = 0
            for instruction in instructions:
                # Set a flag if any of communication functions is used
                if instruction.opname == 'LOAD_GLOBAL':
                    if instruction.argval in com_fcn:
                        found_com_fcn = True
                # If method call goes right after the socket load and method is connect - throw an error
                if sock_found:
                    if instruction.opname == 'LOAD_METHOD':
                        instruction_cmd = instruction.argval
                        if instruction_cmd in forbidden_sock_cmd:
                            raise TypeError(f'Использование метода {instruction_cmd} у сокета '
                                            f'недопустимо в классе {name}')
                        if instruction_cmd == 'socket':
                            sock_arg_counter += 2  # Waiting for two attributes to come from this function
                    sock_found = False
                # If socket was created - check 2 of its arguments, both should be in TCP config
                if sock_arg_counter:
                    if instruction.opname == 'LOAD_ATTR':
                        sock_arg_counter -= 1
                        if instruction.argval not in tcp_sock_cfg:
                            raise TypeError(f'Использование {instruction.argval} у сокета недопустимо для работы по TCP'
                                            f' в классе {name}')
                    elif instruction.opname == 'CALL_METHOD':
                        sock_arg_counter = 0  # Method was called before expected arguments were loaded
                if instruction.opname == 'LOAD_ATTR' and instruction.argval in sock_alias:
                    sock_found = True
        # Check if one of the 2 communication methods is present
        if not found_com_fcn:
            raise ValueError(f'Отсутствуют вызовы функций, работающих с сокетами')
        type.__init__(cls, name, bases, dct)
