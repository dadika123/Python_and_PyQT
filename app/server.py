import configparser
import socket
import os
import argparse
import select
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from server_database import ServerDb
from common.variables import *
from common.utils import *
from decos import log
from descrptrs import Port
from metaclasses import ServerMaker

# Инициализация логирования сервера.
from server_gui import MainWindow, HistoryWindow, ConfigWindow, gui_create_model, create_stat_model

logger = logging.getLogger('server')


# Парсер аргументов коммандной строки.
@log
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


# Основной класс сервера
class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database, **kwargs):
        # Параментры подключения
        self.addr = listen_address
        self.port = listen_port

        # База данных сервера
        self.database = database

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        # Конструктор предка
        super().__init__(**kwargs)

        self.connected_lock = threading.Lock()
        self.new_connection = False

    def init_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}'
            f'. Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen()

    def run(self):
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message)
                    except (OSError):
                        # Ищем клиента в словаре клиентов и удаляем его из него
                        # и  базы подключённых
                        logger.info(
                            f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    logger.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    # Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение, список зарегистрированых
    # пользователей и слушающие сокеты. Ничего не возвращает.
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    # Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента, проверяет корректность, отправляет
    #     словарь-ответ в случае необходимости.
    def process_client_message(self, message, client):
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован, регистрируем, иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(
                    message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with self.connected_lock:
                    self.new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(
                message[SENDER], message[DESTINATION])
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            logger.info(
                f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with self.connected_lock:
                self.new_connection = True
            return

        # Если это запрос контакт-листа
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        # Если это добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


class ServerGUI:
    def __init__(self, server: Server, config: configparser.ConfigParser):
        self.server = server
        self.config = config

        self.server_app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.stat_window = None

        self.main_window.statusBar().showMessage('Server Working')
        self.main_window.active_clients_table.setModel(gui_create_model(self.server.database))
        self.main_window.active_clients_table.resizeColumnsToContents()
        self.main_window.active_clients_table.resizeRowsToContents()

        self.main_window.refresh_button.triggered.connect(self.list_update)
        self.main_window.show_history_button.triggered.connect(self.show_statistics)
        self.main_window.config_btn.triggered.connect(self.server_config)

        self.timer = QTimer()
        self.timer.timeout.connect(self.list_update)

    def start(self):
        self.timer.start(1000)
        self.server_app.exec_()

    def list_update(self):
        if self.server.new_connection:
            self.main_window.active_clients_table.setModel(gui_create_model(self.server.database))
            self.main_window.active_clients_table.resizeColumnsToContents()
            self.main_window.active_clients_table.resizeRowsToContents()
            with self.server.connected_lock:
                self.server.new_connection = False

    def show_statistics(self):
        self.stat_window = HistoryWindow()
        self.stat_window.history_table.setModel(create_stat_model(self.server.database))
        self.stat_window.history_table.resizeColumnsToContents()
        self.stat_window.history_table.resizeRowsToContents()
        self.stat_window.show()

    def server_config(self):
        config_window = ConfigWindow()
        config_window.db_path.insert(self.config['SETTINGS']['Database_path'])
        config_window.db_file.insert(self.config['SETTINGS']['Database_file'])
        config_window.port.insert(self.config['SETTINGS']['Default_port'])
        config_window.ip.insert(self.config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(lambda: self.save_server_config(config_window))

    def save_server_config(self, config_window):
        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = config_window.db_path.text()
        self.config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    self.config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerDb(os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера.
    server = Server(listen_address, listen_port, database, daemon=True)
    server.start()

    server_gui = ServerGUI(server, config)
    server_gui.start()


if __name__ == '__main__':
    main()
