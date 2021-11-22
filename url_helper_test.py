import unittest
import url_helper as module

class UtilsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.url_helper = module.TflUrlHelper()

    def test_construct_url_from_lines(self):
        lines = ['bakerloo', 'jubilee']
        url = self.url_helper.construct_url_from_lines(lines)
        self.assertEqual(
            url, "https://api.tfl.gov.uk/Line/bakerloo,jubilee/Disruption")

    def test_is_valid_lines(self):
        lines = ['bakerloo', 'jubilee']
        self.assertTrue(self.url_helper.is_valid_lines(lines))

        lines = ['bakerloo', 'juBilee']
        self.assertFalse(self.url_helper.is_valid_lines(lines))


if __name__ == '__main__':
    unittest.main()