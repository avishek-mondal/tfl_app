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


    def test_add_response(self):
        task_id = 'Test'
        response = []
        self.store.add_response(task_id=task_id, response=response)

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