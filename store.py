import typing as ty
from abc import abstractmethod
from sqlalchemy.engine.url import URL

from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
import sql_config as config
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from misc_utils import retry_func


import plog

Base = declarative_base()

_global_mem_store = None
_global_session = None

def get_global_session_maker(engine):
    global _global_session
    if not _global_session:
        _global_session = sessionmaker(bind=engine)
    return _global_session


def get_store(in_memory_store: bool):
    if not in_memory_store:
        raise NotImplementedError("SQL not implemented yet")

    global _global_mem_store
    if in_memory_store:
        if _global_mem_store is None:
            _global_mem_store = InMemoryStore()
        return _global_mem_store


class AbstractMemoryStore:

    @abstractmethod
    def add_response(self, task_id, response):
        pass

    @abstractmethod
    def add_pending_task_id(self, task_id, url):
        pass

    @abstractmethod
    def is_pending_task_id(self, task_id):
        pass

    @abstractmethod
    def remove_pending_task_id(self, task_id):
        pass

    @abstractmethod
    def get_task_id_response(self):
        pass

    @abstractmethod
    def get_all_pending_tasks(self, task_id):
        pass

    @abstractmethod
    def get_all_finished_tasks(self):
        pass


class InMemoryStore(AbstractMemoryStore):

    def __init__(self):
        plog.info("Store init")
        self.task_id2response = dict()
        self.pending_task_ids = dict()

    def add_response(self, task_id, response):
        plog.info(f"adding response for {task_id}", response=response)
        self.task_id2response[task_id] = response
        plog.info(f"added. task_id2response = {self.task_id2response}",
                  store=self)
        self.remove_pending_task_id(task_id=task_id)

    def add_pending_task_id(self, task_id, dt_str: str, url: str):
        plog.info(f"adding pending task for {dt_str}")
        self.pending_task_ids[task_id] = (dt_str, url)

    def remove_pending_task_id(self, task_id):
        if task_id in self.pending_task_ids:
            del self.pending_task_ids[task_id]

    def get_task_id_response(self, task_id) -> dict:
        plog.info(f"getting response for {task_id}")
        if task_id in self.task_id2response:
            return self.task_id2response[task_id]
        else:
            plog.error(f"in store. task_id2response = {self.task_id2response}",
                       store=self)
            raise ValueError(f"Store does not have {task_id}")

    def get_all_pending_tasks(self) -> ty.List[str]:
        return list(self.pending_task_ids.keys())

    def get_all_finished_tasks(self) -> ty.Dict[str, str]:
        return self.task_id2response


class TaskId2Response(Base):
    __tablename__ = 'taskid2response'
    task_id = Column(String, primary_key=True)
    response = Column(String)

class PendingTaskIds(Base):
    __tablename__ = 'pending_task_ids'
    task_id = Column(String, primary_key=True)
    dt_str = Column(String)
    url = Column(String)


@contextmanager
def session_scope(session_maker: sessionmaker):
    """Provide a transactional scope around a series of operations.

    Args:
        session_maker: sqlalchemy.orm.sessionmaker"""
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception as e:
        plog.exception('Rolling back as exception occurred', exc=e)
        session.rollback()
        raise e
    finally:
        session.close()


class SQLStore(AbstractMemoryStore):
    def __init__(self):
        plog.info("Sql store init")

        conn_options = dict(
            drivername="postgresql",
            username="postgres",
            host="127.0.0.1",
            port=5431
        )
        database_url = URL(**conn_options)
        self.engine = create_engine(database_url)
        conn, retries = retry_func(self.engine.connect,
                                   max_attempts=3,
                                   waiting_time=3)
        plog.info(f"successfully connected after {retries} times")                                   
        conn.connection.set_isolation_level(0)
        try:
            conn.execute(f"CREATE DATABASE {config.DB_NAME}")
        except ProgrammingError:
            plog.info("Ignore error creating database, already exists")
        finally:
            conn.close()
        Base.metadata.create_all(self.engine)
        self.session_maker = get_global_session_maker(self.engine)

    @contextmanager
    def session_scope(self):
        """Create a session context"""
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            plog.error(f'Rolling back as exception occurred: {str(e)}')
            session.rollback()
            raise e
        finally:
            session.close()

    def add_response(self, task_id, response):
        if task_id and not isinstance(task_id, str):
            task_id = str(task_id)
        if response and not isinstance(response, str):
            response = str(response)
        plog.info(f"adding response for {task_id}", response=response)

        with self.session_scope() as s:
            to_insert = TaskId2Response(task_id=task_id, response=response)
            s.add(to_insert)
            s.commit()
        plog.info("Done adding task_id to sql table")
        self.remove_pending_task_id(task_id=task_id)


    def remove_pending_task_id(self, task_id):
        with self.session_scope() as s:
            to_del = s.query(PendingTaskIds).filter(
                PendingTaskIds.task_id == task_id).first()
