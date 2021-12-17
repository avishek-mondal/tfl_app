import ast
import typing as ty
from abc import abstractmethod
from contextlib import contextmanager

import sqlalchemy
from sqlalchemy import Column, String, create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import tlog
import sql_config as config
from misc_utils import retry_func

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
    def add_pending_task_id(self, task_id, dt_str: str, url: str):
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
        tlog.info("Store init")
        self.task_id2response = dict()
        self.pending_task_ids = dict()

    def add_response(self, task_id, response):
        tlog.info(f"adding response for {task_id}", response=response)
        self.task_id2response[task_id] = response
        tlog.info(f"added. task_id2response = {self.task_id2response}",
                  store=self)
        self.remove_pending_task_id(task_id=task_id)

    def add_pending_task_id(self, task_id, dt_str: str, url: str):
        tlog.info(f"adding pending task for {dt_str}")
        self.pending_task_ids[task_id] = (dt_str, url)

    def remove_pending_task_id(self, task_id):
        if task_id in self.pending_task_ids:
            del self.pending_task_ids[task_id]

    def get_task_id_response(self, task_id) -> dict:
        tlog.info(f"getting response for {task_id}")
        if task_id in self.task_id2response:
            return self.task_id2response[task_id]
        else:
            tlog.error(f"in store. task_id2response = {self.task_id2response}",
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
        tlog.exception('Rolling back as exception occurred', exc=e)
        session.rollback()
        raise e
    finally:
        session.close()


class SQLStore(AbstractMemoryStore):
    def __init__(self):
        tlog.info("Sql store init")

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
        tlog.info(f"successfully connected after {retries} times")
        conn.connection.set_isolation_level(0)
        try:
            conn.execute(f"CREATE DATABASE {config.DB_NAME}")
        except ProgrammingError:
            tlog.info("Ignore error creating database, already exists")
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
            tlog.error(f'Rolling back as exception occurred: {str(e)}')
            session.rollback()
            raise e
        finally:
            session.close()

    def add_response(self, task_id, response):
        if task_id and not isinstance(task_id, str):
            task_id = str(task_id)
        if response and not isinstance(response, str):
            response = str(response)
        tlog.info(f"adding response for {task_id}", response=response)

        with self.session_scope() as s:
            to_insert = TaskId2Response(task_id=task_id, response=response)
            s.add(to_insert)
            s.commit()
        tlog.info("Done adding task_id to sql table")
        self.remove_pending_task_id(task_id=task_id)


    def remove_pending_task_id(self, task_id):
        tlog.info(f"Removing pending task_id {task_id}")
        with self.session_scope() as s:
            try:
                to_del = s.query(PendingTaskIds).filter(
                    PendingTaskIds.task_id == task_id).first()
            except sqlalchemy.orm.exc.NoResultFound as e:
                tlog.error(
                    f"could not find task_id {task_id} in PendingTaskIds table"
                )
            if not to_del:
                return
            try:
                s.delete(to_del)
            except Exception as e:
                tlog.error(f"could not delete {to_del.task_id}", err=e)

    def add_pending_task_id(self, task_id, dt_str: str, url: str):
        with self.session_scope() as s:
            try:
                s.add(PendingTaskIds(task_id=task_id, dt_str=dt_str, url=url))
            except Exception as e:
                err_msg = (f"could not add task_id = {task_id} "
                           f"dt_str={dt_str} url = {url}")
                tlog.error(err_msg, err=e)


    def is_pending_task_id(self, task_id):
        with self.session_scope() as s:
            try:
                to_find = s.query(PendingTaskIds).filter(
                    PendingTaskIds.task_id == task_id).first()
            except sqlalchemy.orm.exc.NoResultFound as e:
                return False
            return to_find is not None


    def get_task_id_response(self, task_id: str):
        with self.session_scope() as s:
            try:
                res = s.query(TaskId2Response.response).filter(
                    TaskId2Response.task_id == task_id).one_or_none()
            except sqlalchemy.orm.exc.NoResultFound as e:
                tlog.error(f"task_id {task_id} is not in TaskId2Response table", err = e)
                raise e
            if res:
                return ast.literal_eval(res.response)


    def get_all_pending_tasks(self) -> list:
        with self.session_scope() as s:
            try:
                res = s.query(PendingTaskIds.task_id).all()
            except sqlalchemy.orm.exc.NoResultFound as e:
                tlog.error(
                    f"No pending tasks found",
                    err=e)
                raise e
            if res:
                return [task_id for task_id, in res]

    def remove_finished_task(self, task_id):
        tlog.info(f"Removing finished task_id {task_id}")
        with self.session_scope() as s:
            try:
                to_del = s.query(TaskId2Response).filter(
                    TaskId2Response.task_id == task_id).first()
            except sqlalchemy.orm.exc.NoResultFound as e:
                tlog.error(
                    f"could not find task_id {task_id} in TaskId2Response table"
                )
            if not to_del:
                return
            try:
                s.delete(to_del)
            except Exception as e:
                tlog.error(f"could not delete {to_del.task_id}", err=e)

    def get_all_finished_tasks(self) -> dict:
        with self.session_scope() as s:
            try:
                res = s.query(TaskId2Response).all()
            except Exception as e:
                tlog.error("Could not find TaskId2Response", err=e)
                raise e
            if res:
                return {
                    row.task_id: ast.literal_eval(row.response)
                    for row in res
                }
