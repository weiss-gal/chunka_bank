from datetime import datetime
import unittest
from cb_server.crontab import CronParsingException, CronTab

class CronTabTests(unittest.TestCase):
    def test_parse_cron_part(self):
        cron = CronTab()
        self.assertEqual(cron._parse_cron_part('*', 0, 59), set(range(0, 60)))
        self.assertEqual(cron._parse_cron_part('0', 0, 59), {0})
        self.assertEqual(cron._parse_cron_part('0-5', 0, 59), set(range(0, 6)))
        self.assertEqual(cron._parse_cron_part('0,1,2,3,4,5', 0, 59), set(range(0, 6)))
        items = [0,1,2,3,4,5,10,20,30,40,50,59]
        self.assertEqual(cron._parse_cron_part(','.join([str(item) for item in items]), 0, 59), set(items))
        self.assertEqual(cron._parse_cron_part('1-3,10,20,30', 0, 59), {1,2,3,10,20,30})

        with self.assertRaises(CronParsingException):
            cron._parse_cron_part('a', 0, 59)
        with self.assertRaises(CronParsingException):
            cron._parse_cron_part('0-a', 0, 59)
        with self.assertRaises(CronParsingException):
            cron._parse_cron_part('0-5a', 0, 59)

    def test_parse_cron_line(self):
        cron = CronTab()
        cron.from_line('0 0 1 1 1')
        self.assertEqual(cron.minute, {0})
        self.assertEqual(cron.hour, {0})
        self.assertEqual(cron.day_of_month, {1})
        self.assertEqual(cron.month, {1})
        self.assertEqual(cron.day_of_week, {1})
        
        cron.from_line('0-5 0-5 1-5 1-5 1-5')
        self.assertEqual(cron.minute, set(range(0, 6)))
        self.assertEqual(cron.hour, set(range(0, 6)))
        self.assertEqual(cron.day_of_month, set(range(1, 6)))
        self.assertEqual(cron.month, set(range(1, 6)))

        cron.from_line('* * * * *')
        self.assertEqual(cron.minute, set(range(0, 60)))
        self.assertEqual(cron.hour, set(range(0, 24)))
        self.assertEqual(cron.day_of_month, set(range(1, 32)))
        self.assertEqual(cron.month, set(range(1, 13)))
        self.assertEqual(cron.day_of_week, set(range(0, 7)))
    
    def test_to_string(self):
        cron = CronTab()
        cron.from_line('0 0 1 1 1')
        self.assertEqual(cron.to_string(), '0\t0\t1\t1\t1')
        
        cron.from_line('0-5 0-5 1-5 1-5 1-5')
        self.assertEqual(cron.to_string(), '0-5\t0-5\t1-5\t1-5\t1-5')

        cron.from_line('* * * * *')
        self.assertEqual(cron.to_string(), '*\t*\t*\t*\t*')


    def test_get_next_run(self):
        cron = CronTab()
        cron.from_line('0 0 1 1 1')
        self.assertEqual(cron.get_next_run(datetime(2024, 1, 31, 0, 49, 0)), datetime(2025, 1, 1, 0, 0, 0))
        cron.from_line('5 0 * 8 *')
        self.assertEqual(cron.get_next_run(datetime(2024, 1, 31, 0, 49, 0)), datetime(2024, 8, 1, 0, 5, 0))

if __name__ == '__main__':
    unittest.main()