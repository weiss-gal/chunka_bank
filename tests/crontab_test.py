import unittest
from cb_server.crontab import CronTab

class CronTabTests(unittest.TestCase):
    def test_parse_cron_part(self):
        cron = CronTab()
        self.assertEqual(cron.parse_cron_part('*', 0, 59), set(range(0, 60)))
        self.assertEqual(cron.parse_cron_part('0', 0, 59), {0})
        self.assertEqual(cron.parse_cron_part('0-5', 0, 59), set(range(0, 6)))
        self.assertEqual(cron.parse_cron_part('0,1,2,3,4,5', 0, 59), set(range(0, 6)))
        items = [0,1,2,3,4,5,10,20,30,40,50,59]
        self.assertEqual(cron.parse_cron_part(','.join([str(item) for item in items]), 0, 59), set(items))
        self.assertEqual(cron.parse_cron_part('1-3,10,20,30', 0, 59), {1,2,3,10,20,30})
        
        
        with self.assertRaises(Exception):
            cron.parse_cron_part('a', 0, 59)
        with self.assertRaises(Exception):
            cron.parse_cron_part('0-a', 0, 59)
        with self.assertRaises(Exception):
            cron.parse_cron_part('0-5a', 0, 59)

if __name__ == '__main__':
    unittest.main()