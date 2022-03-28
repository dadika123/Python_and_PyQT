import datetime
import os

from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from common.variables import *


class ClientDatabase:
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, from_username, to_username, message):
            self.id = None
            self.from_username = from_username
            self.to_username = to_username
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.username = contact

    def __init__(self, username):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{username}.db3'
        self.database_engine = create_engine(
            f'sqlite:///{os.path.join(path, filename)}',
            echo=False,
            pool_recycle=7200,
            connect_args={
                'check_same_thread': False})

        self.metadata = MetaData()

        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_username', String),
                        Column('to_username', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('username', String, unique=True)
                         )

        self.metadata.create_all(self.database_engine)

        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact_username):
        if not self.session.query(self.Contacts).filter_by(username=contact_username).count():
            contact_row = self.Contacts(contact_username)
            self.session.add(contact_row)
            self.session.commit()

    def contacts_clear(self):
        self.session.query(self.Contacts).delete()

    def del_contact(self, contact_username):
        self.session.query(self.Contacts).filter_by(username=contact_username).delete()

    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_username, to_username, message):
        message_row = self.MessageHistory(from_username, to_username, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.username).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, username):
        if self.session.query(self.KnownUsers).filter_by(username=username).count():
            return True
        else:
            return False

    def check_contact(self, contact_username):
        if self.session.query(self.Contacts).filter_by(username=contact_username).count():
            return True
        else:
            return False

    def get_history(self, from_user=None, to_user=None):
        query = self.session.query(self.MessageHistory)
        if from_user:
            query = query.filter_by(from_username=from_user)
        if to_user:
            query = query.filter_by(to_username=to_user)
        return [(history_row.from_username, history_row.to_username, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for username in ['user_1', 'user_2', 'user_3']:
        test_db.add_contact(username)
    test_db.add_contact('user_4')
    test_db.add_users(['user_1', 'user_2', 'user_3', 'user_4', 'user_5'])
    test_db.save_message('user_1', 'user_2', f'Привет! я тестовое сообщение от {datetime.datetime.now()}!')
    test_db.save_message('user_2', 'user_1', f'Привет! я другое тестовое сообщение от {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('user_1'))
    print(test_db.check_user('user_6'))
    print(test_db.get_history('user_2'))
    print(test_db.get_history(to_user='user_2'))
    print(test_db.get_history('user_3'))
    test_db.del_contact('user_4')
    print(test_db.get_contacts())
