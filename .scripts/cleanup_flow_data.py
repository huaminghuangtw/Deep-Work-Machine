import json
from datetime import datetime, timedelta
from pathlib import Path

data_file = Path(__file__).parent.parent / "Number of Flows" / "data.json"

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

cutoff_date = datetime.now() - timedelta(days=90)

filtered_data = {
    date_str: times
    for date_str, times in data.items()
    if datetime.strptime(date_str, '%Y-%m-%d') >= cutoff_date
}

sorted_data = dict(sorted(filtered_data.items(), reverse=True))

with open(data_file, 'w', encoding='utf-8') as f:
    json.dump(sorted_data, f, indent=4, ensure_ascii=False)
    f.write('\n')
