import unittest
import subprocess
import plog

from store import SQLStore
import sql_config as config


class SQLTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the testing database"""
        cls._container_name = 'tfl_scheduler'

        cls.stop_containers()

        # start the container
        container = subprocess.check_output([
            'docker', 'run', '-d', '-p', '5431:5432', '--name',
            f'{cls._container_name}', 'postgres:11.5-alpine'
        ]).decode("utf-8").split("\n")

        plog.info(f"docker run done. container = {container}")


        cls.store = SQLStore()


    def test_add_pending_task_id(self):
        task_id = 'test_add_pending_task_id'
        dt_str = '2021-11-14T13:43:15'
        url = "https://api.tfl.gov.uk/Line/bakerloo,jubilee/Disruption"
        self.store.add_pending_task_id(task_id=task_id, dt_str=dt_str, url=url)
        self.store.remove_pending_task_id(task_id=task_id)

    def test_is_pending_task_id(self):
        task_id = 'test_is_pending_task_id'
        dt_str = '2021-11-14T13:43:15'
        url = "https://api.tfl.gov.uk/Line/bakerloo,jubilee/Disruption"
        self.assertFalse(self.store.is_pending_task_id(task_id))

        self.store.add_pending_task_id(task_id=task_id, dt_str=dt_str, url=url)
        self.assertTrue(self.store.is_pending_task_id(task_id))
        self.store.remove_pending_task_id(task_id=task_id)

    def test_add_response(self):
        task_id = 'Test'
        response = []
        self.store.add_response(task_id=task_id, response=response)
        self.store.remove_finished_task(task_id=task_id)

    def test_get_task_id_response(self):
        task_id = 'Test'
        response = ["Test response"]
        self.store.add_response(task_id=task_id, response=response)
        ret_val = self.store.get_task_id_response(task_id=task_id)
        self.assertEqual(ret_val, response)
        self.store.remove_finished_task(task_id=task_id)

    def test_get_all_pending_tasks(self):
        pending_tasks = [('task_1', 'dt_str_1', 'url1'),
                        #  ('task_2', 'dt_str_2', 'url2'),
                        #  ('task_3', 'dt_str_3', 'url3')
                        ]
        for task_id, dt_str, url in pending_tasks:
            self.store.add_pending_task_id(task_id=task_id,
                                           dt_str=dt_str,
                                           url=url)
        task_ids = self.store.get_all_pending_tasks()
        self.assertCountEqual(task_ids,
                              [task_id for task_id, _, _ in pending_tasks])

        for task_id, dt_str, url in pending_tasks:
            self.store.remove_pending_task_id(task_id=task_id)

    def test_get_all_finished_tasks(self):
        tasks_response = [('id1', ['response1']), ('id2', ['response2']),
                          ('id3', ['response3'])]
        for task_id, response in tasks_response:
            self.store.add_response(task_id=task_id, response=response)
        finished_tasks = self.store.get_all_finished_tasks()
        self.assertDictEqual(
            finished_tasks,
            {task_id: response
             for task_id, response in tasks_response})
        for task_id, _ in tasks_response:
            self.store.remove_finished_task(task_id=task_id)


    @classmethod
    def stop_containers(cls):
        # shut down any running containers
        containers = subprocess.check_output([
            "docker",
            "ps",
            "-q",
            "-a",
            "--filter",
            f"name={cls._container_name}",
        ]).decode("utf-8").split("\n")
        if containers:
            plog.info(f"Stop {len(containers)} containers")
            for container in containers:
                c_id = container.strip()
                if c_id:
                    subprocess.check_output(["docker", "stop", c_id])
                    subprocess.check_output(["docker", "rm", c_id])
                    plog.info(f"Stopped container {c_id}")

    @classmethod
    def tearDownClass(cls):
        """Stop the container at the end of suite"""
        conn = cls.store.engine.connect()
        try:
            # drop any existing connection
            conn.execute(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid)"
                f" FROM pg_stat_activity"
                f" WHERE pg_stat_activity.datname = '{config.DB_NAME}'"
                f" AND pid <> pg_backend_pid();")
            conn.execute(f"DROP DATABASE IF EXISTS {config.DB_NAME}")
        finally:
            conn.close()

        cls.stop_containers()


if __name__ == '__main__':
    unittest.main()