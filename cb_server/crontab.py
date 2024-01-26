from typing import Set

class CronTab:
    """
    Represents a single line in a crontab file.
    """
    def parse_cron_part(self, part: str, min_value: int, max_value: int) -> Set[int]:
        """
        Parses a single part of a cron line.
        part: The part to parse
        min_value: The minimum value allowed in the part
        max_value: The maximum value allowed in the part (inclusive)
        """
        # parse the part
        if part == '*':
            # all values are valid
            return set(range(min_value, max_value + 1))

        # split the part by commas
        part_values = part.split(',')
        values = []
        for part_value in part_values:
            # split the part by dashes
            part_range = part_value.split('-')
            if len(part_range) == 1:
                # this is a single value
                try:
                    value = int(part_range[0])
                except ValueError:
                    raise Exception(f"Invalid cron part: '{part}'")
                if value < min_value or value > max_value:
                    raise Exception(f"Invalid cron part: '{part}'")
                values.append(value)
            elif len(part_range) == 2:
                # this is a range
                try:
                    min_range = int(part_range[0])
                    max_range = int(part_range[1])
                except ValueError:
                    raise Exception(f"Invalid cron part: '{part}'")
                if min_range < min_value or min_range > max_value or \
                   max_range < min_value or max_range > max_value or \
                   min_range > max_range:
                    raise Exception(f"Invalid cron part: '{part}'")
                values.extend(list(range(min_range, max_range + 1)))
            else:
                raise Exception(f"Invalid cron part: '{part}'")
            
        return set(values)


    def parse_cron_line(self):
        # split the line by spaces
        line_parts = self.cron_line.split()
        if len(line_parts) != 6:
            raise Exception(f"Invalid cron line: '{self.cron_line}'")
        
        # parse the minute
        try:
            self.minute = self.parse_cron_part(line_parts[0], 0, 59)
        except Exception as e:
            raise Exception(f"Invalid minute in cron line: '{self.cron_line}'") from e
        
        # parse the hour
        try:
            self.hour = self.parse_cron_part(line_parts[1], 0, 23)
        except Exception as e:
            raise Exception(f"Invalid hour in cron line: '{self.cron_line}'") from e
        
        # parse the day of month
        try:
            self.day_of_month = self.parse_cron_part(line_parts[2], 1, 31)
        except Exception as e:
            raise Exception(f"Invalid day of month in cron line: '{self.cron_line}'") from e
        
        # parse the month
        try:
            self.month = self.parse_cron_part(line_parts[3], 1, 12)
        except Exception as e:
            raise Exception(f"Invalid month in cron line: '{self.cron_line}'") from e
        
        # parse the day of week
        try:
            self.day_of_week = self.parse_cron_part(line_parts[4], 0, 6)
        except Exception as e:
            raise Exception(f"Invalid day of week in cron line: '{self.cron_line}'") from e
        
        # parse the command
        self.command = line_parts[5]

    def __init__(self):
        self.minute = None
        self.hour = None
        self.day_of_month = None
        self.month = None
        self.day_of_week = None
    
    def parse_line(self, line: str):
        self.cron_line = line
        self.parse_cron_line()
        