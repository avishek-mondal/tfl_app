from datetime import datetime
from uuid import uuid4
import plog

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

import constants as c
from store import AbstractMemoryStore


def get_from_tfl(url, id: str, store: AbstractMemoryStore):
    plog.info("running get_from_tfl")
    resp = requests.get(url)
    store.add_response(id, resp.json())
    store.remove_pending_task_id(task_id=id)


class TflScheduler:
    def __init__(self,
                 store: AbstractMemoryStore,
                 scheduler: BackgroundScheduler = None):
        plog.info("Initialising scheduler wrapper")
        if not scheduler:
            scheduler = BackgroundScheduler()
        self.scheduler = scheduler
        self.store = store
        if len(store.get_all_pending_tasks()) > 0:
            self.schedule_all_pending_tasks()
        self.scheduler.start()


    def schedule_all_pending_tasks(self):
        pass

    def schedule_tfl_call(self, url: str, dt: datetime, id: str = None) -> str:
        plog.info("Scheduling tfl call")
        dt = datetime.now() if not dt else dt
        trigger = DateTrigger(run_date=dt)
        dt_str = dt.strftime(c.DT_STR)
        id = id or uuid4().hex
        args = [url, id, self.store]

        if not self.store.is_pending_task_id(task_id=dt_str):
            self.store.add_pending_task_id(id, dt_str, url)

        plog.info(f"scheduling job, dt = {dt}, id = {id}")
        self.scheduler.add_job(func=get_from_tfl,
                               trigger=trigger,
                               args=args,
                               id=id,
                               replace_existing=True)
        return id
