from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ServerDb:
    """
    Класс - оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    """

    class AllUsers:
        """Класс - отображение таблицы всех пользователей."""

        def __init__(self, username, passwd_hash, first_name='', last_name=''):
            self.id = None
            self.username = username
            self.first_name = first_name
            self.last_name = last_name
            self.last_login = datetime.datetime.now()
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
            self.passwd_hash = passwd_hash
            self.pubkey = None

    class ActiveUsers:
        """Класс - отображение таблицы активных пользователей."""

        def __init__(self, user_id, ip, port, logged_at):
            self.id = None
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.logged_at = logged_at

    class UsersLoginHistory:
        """Класс - отображение таблицы истории входов."""

        def __init__(self, user_id, ip, port, logged_at):
            self.id = None
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.logged_at = logged_at

    class UsersContacts:
        """Класс - отображение таблицы контактов пользователей."""

        def __init__(self, user_id, contact_id):
            self.id = None
            self.user_id = user_id
            self.contact_id = contact_id

    class UsersHistory:
        """Класс - отображение таблицы истории действий."""

        def __init__(self, user_id):
            self.id = None
            self.user_id = user_id
            self.sent = 0
            self.received = 0

    def __init__(self, path):
        self.db_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                       connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String, unique=True),
                            Column('first_name', String),
                            Column('last_name', String),
                            Column('last_login', DateTime),
                            Column('created_at', DateTime),
                            Column('updated_at', DateTime),
                            Column('passwd_hash', String),
                            Column('pubkey', Text)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('Users.id'), unique=True),
                                   Column('ip', String),
                                   Column('port', Integer),
                                   Column('logged_at', DateTime)
                                   )

        users_login_history_table = Table('Login_history', self.metadata,
                                          Column('id', Integer, primary_key=True),
                                          Column('user_id', ForeignKey('Users.id')),
                                          Column('ip', String),
                                          Column('port', Integer),
                                          Column('logged_at', DateTime)
                                          )

        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user_id', ForeignKey('Users.id')),
                         Column('contact_id', ForeignKey('Users.id'))
                         )

        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user_id', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('received', Integer)
                                    )

        self.metadata.create_all(self.db_engine)
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.UsersLoginHistory, users_login_history_table)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def get_user(self, username):
        query_res = self.session.query(self.AllUsers.username,
                                       self.AllUsers.first_name,
                                       self.AllUsers.last_name,
                                       self.AllUsers.last_login,
                                       ).filter_by(username=username)
        if query_res.count():
            return query_res.first()
        return None

    def user_change_name(self, username, first_name='', last_name=''):
        query_res = self.session.query(self.AllUsers).filter_by(username=username)
        if query_res.count():
            user = query_res.first()
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if first_name or last_name:
                self.session.add(user)
                self.session.commit()

    def user_login(self, username, ip, port, key):
        query_res = self.session.query(self.AllUsers).filter_by(username=username)
        if query_res.count():
            user = query_res.first()
            user.last_login = datetime.datetime.now()
            self.session.add(user)
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')
        # else:
        #     user = self.AllUsers(username)
        #     self.session.add(user)
        #     self.session.commit()
        #     user_in_history = self.UsersHistory(user.id)
        #     self.session.add(user_in_history)

        active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(active_user)

        logging_history = self.UsersLoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(logging_history)

        self.session.commit()

    def user_register(self, username, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user = self.AllUsers(username, passwd_hash)
        self.session.add(user)
        self.session.commit()

        user_in_history = self.UsersHistory(user.id)
        self.session.add(user_in_history)
        self.session.commit()

    def user_delete(self, username):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.query(self.UsersLoginHistory).filter_by(user_id=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user_id=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(contact_id=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user_id=user.id).delete()
        self.session.query(self.AllUsers).filter_by(username=username).delete()
        self.session.commit()

    def get_hash(self, username):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        return user.passwd_hash

    def get_pubkey(self, username):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        return user.pubkey

    def check_user(self, username):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.AllUsers).filter_by(username=username).count():
            return True
        else:
            return False

    def user_logout(self, username):
        """Метод фиксирующий отключения пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    def users_list(self):
        """Метод возвращающий список известных пользователей со временем последнего входа."""
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.first_name,
            self.AllUsers.last_name,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        """Метод возвращающий список активных пользователей."""
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.logged_at
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        """Метод возвращающий историю входов."""
        query = self.session.query(self.AllUsers.username,
                                   self.UsersLoginHistory.ip,
                                   self.UsersLoginHistory.port,
                                   self.UsersLoginHistory.logged_at
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()

    def process_message(self, sender_username, recipient_username):
        """Метод записывающий в таблицу статистики факт передачи сообщения."""
        sender_id = self.session.query(self.AllUsers).filter_by(username=sender_username).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user_id=sender_id).first()
        sender_row.sent += 1

        recipient_id = self.session.query(self.AllUsers).filter_by(username=recipient_username).first().id
        recipient_row = self.session.query(self.UsersHistory).filter_by(user_id=recipient_id).first()
        recipient_row.received += 1

        self.session.commit()

    def add_contact(self, username, contact_username):
        """Метод добавления контакта для пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        contact_user = self.session.query(self.AllUsers).filter_by(username=contact_username).first()

        if not contact_user or \
                self.session.query(self.UsersContacts).filter_by(user_id=user.id, contact_id=contact_user.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact_user.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, username, contact_username):
        """Метод удаления контакта пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        contact_user = self.session.query(self.AllUsers).filter_by(username=contact_username).first()

        if not contact_user:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user_id == user.id,
            self.UsersContacts.contact_id == contact_user.id
        ).delete()
        self.session.commit()

    def get_contacts(self, username):
        """Метод возвращающий список контактов пользователя."""
        user = self.session.query(self.AllUsers).filter_by(username=username).one()

        query = self.session.query(self.UsersContacts, self.AllUsers.username). \
            filter_by(user_id=user.id). \
            join(self.AllUsers, self.UsersContacts.contact_id == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        """Метод возвращающий статистику сообщений."""
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.received
        ).join(self.AllUsers)
        return query.all()


if __name__ == '__main__':
    username_1 = 'user_1'
    ip_1 = '192.168.1.100'
    port_1 = 7777
    username_2 = 'user_2'
    ip_2 = '192.168.1.101'
    port_2 = 7777

    server_db = ServerDb('server_db.db3')
    server_db.user_login(username_1, ip_1, port_1)
    server_db.user_login(username_2, ip_2, port_2)
    print(server_db.active_users_list())
    server_db.user_logout(username_1)
    print(server_db.active_users_list())
    print(f'История входов пользователя {username_1}')
    [print(f'\t{username}: {ip}:{port}, {time}') for username, ip, port, time in server_db.login_history(username_1)]
    print(server_db.users_list())
    server_db.user_change_name(username_1, 'Anatolii')
    print(server_db.get_user(username_1))
    server_db.user_change_name(username_1, last_name='Tsirkunenko')
    print(server_db.get_user(username_1))

    server_db.add_contact(username_1, username_2)
    print(server_db.get_contacts(username_1))
    print(server_db.get_contacts(username_2))
    server_db.remove_contact(username_1, username_2)
    print(server_db.get_contacts(username_1))
    print(server_db.get_contacts(username_2))
    server_db.process_message(username_1, username_2)
    print(server_db.message_history())
    server_db.process_message(username_2, username_1)
    print(server_db.message_history())
