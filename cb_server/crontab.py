from typing import List, Set

class CronParsingException(Exception):
    pass

class CronTab:
    """
    Represents a single line in a crontab file.
    """
    def _parse_cron_part(self, part: str, min_value: int, max_value: int) -> Set[int]:
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
                    raise CronParsingException(f"Invalid cron part: '{part}'")
                if value < min_value or value > max_value:
                    raise CronParsingException(f"Invalid cron part: '{part}'")
                values.append(value)
            elif len(part_range) == 2:
                # this is a range
                try:
                    min_range = int(part_range[0])
                    max_range = int(part_range[1])
                except ValueError:
                    raise CronParsingException(f"Invalid cron part: '{part}'")
                if min_range < min_value or min_range > max_value or \
                   max_range < min_value or max_range > max_value or \
                   min_range > max_range:
                    raise CronParsingException(f"Invalid cron part: '{part}'")
                values.extend(list(range(min_range, max_range + 1)))
            else:
                raise CronParsingException(f"Invalid cron part: '{part}'")
            
        return set(values)

    def _parse_cron_line(self, cron_line: str):
        # split the line by spaces
        line_parts = cron_line.split()
        if len(line_parts) != 5:
            raise CronParsingException(f"Invalid cron line: '{cron_line}'")
        
        self.minute = self._parse_cron_part(line_parts[0], 0, 59)
        self.hour = self._parse_cron_part(line_parts[1], 0, 23)
        self.day_of_month = self._parse_cron_part(line_parts[2], 1, 31)
        self.month = self._parse_cron_part(line_parts[3], 1, 12)
        self.day_of_week = self._parse_cron_part(line_parts[4], 0, 6)
        
    def __init__(self, minute: Set[int]=None, hour: Set[int]=None, day_of_month: Set[int]=None, 
            month: Set[int]=None, day_of_week: Set[int]=None):
        self.minute: Set[int] = minute or []
        self.hour: Set[int] = hour or []
        self.day_of_month: Set[int] = day_of_month or []
        self.month: Set[int] = month or []
        self.day_of_week: Set[int] = day_of_week or []
    
    def from_line(self, line: str):
        self._parse_cron_line(line)

    def _set_to_string(self, values_set: Set[int], min_value: int, max_value: int) -> str:
        if len(values_set) == max_value - min_value + 1:
            return '*'
        
        # convert consecutive values to ranges
        parts = []
        part_start = None
        part_end = None
        l = list(values_set)
        l.sort()
        for item in l:
            if part_start is None:
                part_start = item
                part_end = item
            elif item != part_end + 1:
                if part_start == part_end:
                    parts.append(str(part_start))
                else:
                    parts.append(f"{part_start}-{part_end}")
                part_start = item
                part_end = item
            else:
                part_end = item

        if part_start is not None:
            if part_start == part_end:
                parts.append(str(part_start))
            else:
                parts.append(f"{part_start}-{part_end}")
            
        return ','.join([part for part in parts])

    def to_string(self):
        return '\t'.join([
            self._set_to_string(self.minute, 0, 59),
            self._set_to_string(self.hour, 0, 23),
            self._set_to_string(self.day_of_month, 1, 31),
            self._set_to_string(self.month, 1, 12),
            self._set_to_string(self.day_of_week, 0, 6)
        ])
    