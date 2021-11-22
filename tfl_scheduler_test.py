import time
import unittest

from datetime import datetime, timedelta
from store import get_memory_store
import tfl_scheduler as module
import constants as c


class SchedulerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.url = "https://api.tfl.gov.uk/Line/bakerloo,jubilee/Disruption"
        self.test_dt = datetime.now() + timedelta(seconds=1)
        self.dt_str = self.test_dt.strftime(c.DT_STR)

    def test_get_from_tfl(self):
        store = get_memory_store(in_memory_store=True)
        module.get_from_tfl(url=self.url, id='Test', store=store)
        self.assertIsNotNone(store.get_task_id_response('Test'))

    def test_schedule_tfl_call(self):
        store = get_memory_store(in_memory_store=True)
        tfl_scheduler = module.TflScheduler(store=store)
        tfl_scheduler.schedule_tfl_call(url=self.url,
                                        dt=self.test_dt,
                                        id="Test")
        time.sleep(2)
        self.assertIsNotNone(store.get_task_id_response("Test"))

    def test_change_job(self):
        url_new = "https://api.tfl.gov.uk/Line/victoria/"
        id = 'Test'
        store = get_memory_store(in_memory_store=True)
        tfl_scheduler = module.TflScheduler(store=store)
        test_dt = datetime.now() + timedelta(seconds=3)
        tfl_scheduler.schedule_tfl_call(url=self.url, dt=test_dt, id=id)
        tfl_scheduler.schedule_tfl_call(url=url_new, dt=test_dt, id=id)
        time.sleep(4)
        response = tfl_scheduler.store.get_task_id_response(id)
        self.assertEqual(response[0]['id'], 'victoria')

    def test_schedule_now(self):
        url = "https://api.tfl.gov.uk/Line/victoria/"
        id = 'Test'
        store = get_memory_store(in_memory_store=True)
        tfl_scheduler = module.TflScheduler(store=store)
        tfl_scheduler.schedule_tfl_call(url=url, dt=None, id=id)
        time.sleep(1)  # takes a second for api to return
        response = tfl_scheduler.store.get_task_id_response(id)
        self.assertEqual(response[0]['id'], 'victoria')




if __name__ == '__main__':
    unittest.main()
