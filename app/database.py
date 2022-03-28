from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ServerDb:
    class AllUsers:
        def __init__(self, username, first_name='', last_name=''):
            self.id = None
            self.username = username
            self.first_name = first_name
            self.last_name = last_name
            self.last_login = datetime.datetime.now()
            self.created_at = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip, port, logged_at):
            self.id = None
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.logged_at = logged_at

    class UsersLoginHistory:
        def __init__(self, user_id, ip, port, logged_at):
            self.id = None
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.logged_at = logged_at

    def __init__(self):
        self.db_engine = create_engine('sqlite:///server_db.db3')
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String, unique=True),
                            Column('first_name', String),
                            Column('last_name', String),
                            Column('last_login', DateTime),
                            Column('created_at', DateTime),
                            Column('updated_at', DateTime)
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

        self.metadata.create_all(self.db_engine)
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.UsersLoginHistory, users_login_history_table)

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

    def user_login(self, username, ip, port):
        query_res = self.session.query(self.AllUsers).filter_by(username=username)
        if query_res.count():
            user = query_res.first()
            user.last_login = datetime.datetime.now()
            self.session.add(user)
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(active_user)

        logging_history = self.UsersLoginHistory(user.id, ip, port, datetime.datetime.now())
        self.session.add(logging_history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.first_name,
            self.AllUsers.last_name,
            self.AllUsers.last_login,
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.logged_at
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.AllUsers.username,
                                   self.UsersLoginHistory.ip,
                                   self.UsersLoginHistory.port,
                                   self.UsersLoginHistory.logged_at
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.username == username)
        return query.all()


if __name__ == '__main__':
    username_1 = 'user_1'
    ip_1 = '192.168.1.100'
    port_1 = 7777
    username_2 = 'user_2'
    ip_2 = '192.168.1.101'
    port_2 = 7777

    server_db = ServerDb()
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
