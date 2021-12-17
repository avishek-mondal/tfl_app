import os
from datetime import datetime

from flask import Flask
from flask_classful import FlaskView, request, route

import constants as c
import tlog
from store import get_store
from tfl_scheduler import TflScheduler
from url_helper import TflUrlHelper

app = Flask(__name__)


class TflAppServer(FlaskView):

    def __init__(self):
        tlog.info("Initialising tfl app server")
        self.store = get_store(in_memory_store=True)
        self.tfl_scheduler = TflScheduler(store=self.store)
        self.url_helper = TflUrlHelper()

    def tasks_post(self, raw_lines: str, schedule_time: str):
        tlog.info(f"schedule_time = {schedule_time}")
        if schedule_time:
            dt = datetime.strptime(schedule_time, c.DT_STR)
            if dt < datetime.now():
                return "Please post a date that is in the future"
        else:
            dt = None
        url = self.url_helper.construct_url_from_lines(raw_lines)
        id = self.tfl_scheduler.schedule_tfl_call(url=url, dt=dt)
        return f"Successfully posted. Task id is {id}"


    def tasks_get_all(self):
        all_tasks = self.store.get_all_finished_tasks()
        return all_tasks

    @route('/tasks', methods=['GET', 'POST'])
    def tasks(self):
        if request.method == 'POST':
            lines = request.values.get('lines')
            schedule_time = request.values.get('schedule_time')
            return self.tasks_post(lines, schedule_time)
        elif request.method == 'GET':
            return self.tasks_get_all()

    @route('/tasks/<task_id>', methods=['GET'])
    def task_id(self, task_id):
        print(f'task_id is = {task_id}')
        try:
            to_ret = self.store.get_task_id_response(task_id)
        except ValueError as e:
            tlog.error(f"in run. task id not found", err=e)
            return ("Task id has either not been scheduled, "
                    "or not been completed")

        return f"response from api is {to_ret}"


TflAppServer.register(app, route_base="/")

if __name__ == '__main__':
    # need to run with FLASK_DEBUG=1
    port = os.getenv('FLASK_PORT', 5000)
    app.run(host = '0.0.0.0', debug=True, port=port)
