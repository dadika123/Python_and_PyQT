class Port:
    port = 7777

    def __get__(self, instance, owner):
        return instance.__dict__[self.port]

    def __set__(self, instance, port):
        if not (1023 < port < 65536):
            raise ValueError(f'Неверный порт {port}. Допустимы адреса с 1024 до 65535')
        instance.__dict__[self.port] = port

    def __delete__(self, instance):
        del instance.__dict__[self.port]

    def __set_name__(self, owner, port):
        self.port = port
