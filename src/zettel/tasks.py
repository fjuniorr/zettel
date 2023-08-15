import re
from datetime import datetime, timedelta
import logging
import humanize

logger = logging.getLogger()

class Task():

    def __init__(self, line):
        self.task = self.parse_task(line)

    def __repr__(self) -> str:
        return str(self.task)

    def parse_duration(self, duration_str):
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 3:  # hh:mm:ss format
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:  # mm:ss format
            return parts[0]*60 + parts[1]
        else:
            raise ValueError('Invalid duration format')

    def format_duration(self, total_seconds):
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def extract_date(self, filename):
        match = re.search(r'\d{8}', filename)
        if match:
            date_str = match.group(0)
            return date_str
        else:
            return None

    def extract_status(self, checkbox):
        options = {
                "- [ ]": 'next',
                "- [!]": 'focus',
                "- [@]": 'in progress',
                "- [?]": 'someday',
                "- [x]": 'done',
            }
        
        option = checkbox  # replace this with the actual option
        if option in options:
            result = options[option]
        else:
            result = None
        return result

    def split_task(self, line):
        match = re.search(r'(- \[.\])', line)
        if match:
            start = match.start()
            matched = match.group(0)
            rest_of_line = line[start+len(matched):].strip()
            return [matched, rest_of_line]
        else:
            return None

    def parse_task(self, task):
        status, body = self.split_task(task)

        tags_re = re.compile(r'@([a-zA-Z0-9_]+)(?:\((.*?)\))?')
        matches = tags_re.findall(body)

        tags = {key: value if value != '' else True for key, value in matches if key != 'todo'}

        if 'clock' in tags.keys():
            tags['clock'] = self.parse_clock(tags['clock'])
            task_duration = humanize.precisedelta(sum([session['duration'] for session in tags['clock']], timedelta()), suppress=['seconds'])
        else:
            tags['clock'] = None
            task_duration = None
        
        title = tags_re.sub('', body).strip()

        output = {
            "title": title,
            "open": False if self.extract_status(status) in ['done'] else True,
            "status": self.extract_status(status),
            "duration": task_duration,
            "tags": tags,
        }

        return output
    
    def parse_clock(self, sessions):
        result = []
        sessions = re.split('[,;]', sessions)
        for session in sessions:
            try:
                start, end = session.split('/')
                start = start.strip()
                end = end.strip()
                duration = timedelta(seconds=self.parse_duration(end))
                start_ts = datetime.strptime(start, '%Y%m%dT%H%M%S')
                end_ts = start_ts + duration
            except ValueError:
                end = session
                duration = timedelta(seconds=self.parse_duration(end))
                start_ts = None
                end_ts = None
            
            result.append({'start': start_ts, 'end': end_ts, 'duration': duration})
            # if duration.seconds != (end_ts - start_ts).total_seconds():
            #     logger.warning('Duration calculation failed...')
        return result