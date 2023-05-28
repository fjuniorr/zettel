import os
from datetime import datetime, timedelta

def create_daily_markdown(start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    current = start
    while current <= end:
        filename = f"daily-{current.strftime('%Y%m%d')}.md"
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                file.write(f"# daily {current.strftime('%d/%m/%Y')}\n\n")
        current += timedelta(days=1)

# use the function
create_daily_markdown("2023-01-01", "2023-01-05")
