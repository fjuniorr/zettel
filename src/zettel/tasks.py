import re

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

        tags = {key: value if value != '' else True for key, value in matches}

        if tags.get('clock'):
          durations = re.split('[,;]', tags['clock'])
          tags['clock'] = self.format_duration(sum(self.parse_duration(d) for d in durations))

        title = tags_re.sub('', body).strip()

        output = {
            "title": title,
            "status": self.extract_status(status),
            "tags": tags,
        }

        return output
    
    def parse_clock(self, task):
        pass