import os
import json

POMODORO_HOURS = 0.55
WEEKS_PER_MONTH = 4.33
DAYS_PER_MONTH = 30.44

DATA_TYPES = {
    "Flows": "Number of Flows",
    "Words": "Number of Words",
}

def url_encode(s):
    return s.replace(' ', '%20')

def read_month_json_data(folder_path, field_name):
    """Read a month folder's JSON file and return (total, nonzero_count)."""
    json_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.json')]
    if json_files:
        try:
            with open(os.path.join(folder_path, json_files[0]), 'r', encoding='utf-8') as f:
                month_data = json.load(f)
                if 'data' in month_data:
                    values = [entry.get(field_name, 0) for entry in month_data['data']]
                    total = sum(values)
                    nonzero_count = sum(1 for v in values if v > 0)
                    return total, nonzero_count
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return 0, 0

def _render_year_entry(section_folder, dname):
    return f"* <details>\n\t<summary>\n\t  <strong>\n\t\t<a href=\"{url_encode(section_folder)}/{dname}\">{dname}</a>\n\t  </strong>\n\t</summary>"

def _render_month_entry(section_folder, drel_path, dname, total, daily_avg, month_files):
    href = f"{url_encode(section_folder)}/{url_encode(drel_path)}"
    image_entry = ""
    if month_files:
        img_href = f"{href}/{month_files[0]}"
        image_entry = (
            f"\n\n\t   | ![{section_folder}]({img_href}) |"
            f"\n\t   | :-: |"
            f"\n\t   | Total = {total:,} |"
            f"\n\t   | Daily Average = {daily_avg:,} |"
        )
    return f"\n\t* <details>\n\t   <summary>\n\t   <a href=\"{href}\">{dname}</a>\n\t   </summary>{image_entry}"

def generate_tree(base_dir, section_folder, rel_dir="", indent=0):
    abs_dir = os.path.join(base_dir, rel_dir)
    month_count = 0
    entries = []
    dirs = []

    for name in sorted(os.listdir(abs_dir)):
        if name.startswith('.'):
            continue
        path = os.path.join(abs_dir, name)
        rel_path = os.path.join(rel_dir, name)
        if os.path.isdir(path):
            dirs.append((name, rel_path))

    dirs = sorted(dirs, key=lambda x: x[0], reverse=True)

    for dname, drel_path in dirs:
        if indent == 0:
            entries.append(_render_year_entry(section_folder, dname))
            sub_entries, sub_month_count = generate_tree(base_dir, section_folder, drel_path, indent + 1)
            entries.extend(sub_entries)
            month_count += sub_month_count
            entries.append("  </details>")
        elif indent == 1:
            month_count += 1
            month_abs_dir = os.path.join(base_dir, drel_path)
            month_files = [f for f in os.listdir(month_abs_dir) if f.lower().endswith('.png')]
            total, nonzero_count = read_month_json_data(month_abs_dir, section_folder)
            daily_avg = round(total / nonzero_count) if nonzero_count else 0
            entries.append(_render_month_entry(section_folder, drel_path, dname, total, daily_avg, month_files))
            entries.append("\t   </details>")
    return entries, month_count

def get_monthly_totals(project_root, data_type, field_name):
    folder_path = os.path.join(project_root, f"Number of {data_type}")
    monthly_totals = []
    
    for year_dir in sorted(os.listdir(folder_path)):
        if year_dir.startswith('.') or not os.path.isdir(os.path.join(folder_path, year_dir)):
            continue
        year_path = os.path.join(folder_path, year_dir)
        for month_dir in sorted(os.listdir(year_path)):
            if month_dir.startswith('.') or not os.path.isdir(os.path.join(year_path, month_dir)):
                continue
            month_path = os.path.join(year_path, month_dir)
            total, _ = read_month_json_data(month_path, field_name)
            monthly_totals.append(total)
    return monthly_totals

def calculate_stats(project_root):
    flows_monthly_totals = get_monthly_totals(project_root, "Flows", DATA_TYPES["Flows"])
    words_monthly_totals = get_monthly_totals(project_root, "Words", DATA_TYPES["Words"])

    # Filter out zero values for average calculations
    flows_nonzero = [x for x in flows_monthly_totals if x > 0]
    words_nonzero = [x for x in words_monthly_totals if x > 0]

    total_flows = sum(flows_monthly_totals)
    total_words = sum(words_monthly_totals)
    num_months_flows = len(flows_nonzero) if flows_nonzero else 1
    num_months_words = len(words_nonzero) if words_nonzero else 1

    monthly_avg_flows = total_flows / num_months_flows
    monthly_avg_words = total_words / num_months_words
    weekly_avg_flows = total_flows / (num_months_flows * WEEKS_PER_MONTH)
    daily_avg_flows = total_flows / (num_months_flows * DAYS_PER_MONTH)
    weekly_avg_words = total_words / (num_months_words * WEEKS_PER_MONTH)
    daily_avg_words = total_words / (num_months_words * DAYS_PER_MONTH)

    return {
        'total_flows': total_flows,
        'total_flow_hours': int(total_flows * POMODORO_HOURS),
        'total_words': total_words,
        'monthly_avg_flows': int(monthly_avg_flows),
        'monthly_avg_hours': int(monthly_avg_flows * POMODORO_HOURS),
        'weekly_avg_flows': int(weekly_avg_flows),
        'weekly_avg_hours': int(weekly_avg_flows * POMODORO_HOURS),
        'daily_avg_flows': round(daily_avg_flows, 1),
        'daily_avg_hours': round(daily_avg_flows * POMODORO_HOURS, 1),
        'monthly_avg_words': int(monthly_avg_words),
        'weekly_avg_words': int(weekly_avg_words),
        'daily_avg_words': int(daily_avg_words)
    }

def generate_stats_section(stats):
    return f"""<div align="center">

|         | All Time | Monthly Average | Weekly Average | Daily Average |
| :-: | :-: | :-: | :-: | :-: |
| **Number of Flows** | 🍅 × {stats['total_flows']}<br>≈ {stats['total_flow_hours']} hours | 🍅 × {stats['monthly_avg_flows']}<br>≈ {stats['monthly_avg_hours']} hours | 🍅 × {stats['weekly_avg_flows']}<br>≈ {stats['weekly_avg_hours']} hours | 🍅 × {stats['daily_avg_flows']}<br>≈ {stats['daily_avg_hours']} hours |
| **Number of Words** | {stats['total_words']:,} words | {stats['monthly_avg_words']:,} words | {stats['weekly_avg_words']:,} words | {stats['daily_avg_words']:,} words |

</div>"""

def get_latest_data_folder(project_root, data_type):
    folder_path = os.path.join(project_root, f"Number of {data_type}")
    
    for year_dir in sorted(os.listdir(folder_path), reverse=True):
        if year_dir.startswith('.') or not os.path.isdir(os.path.join(folder_path, year_dir)):
            continue
        year_path = os.path.join(folder_path, year_dir)
        month_folders = [month_dir for month_dir in os.listdir(year_path) 
                        if not month_dir.startswith('.') and os.path.isdir(os.path.join(year_path, month_dir))]
        if month_folders:
            return int(year_dir), sorted(month_folders, reverse=True)[0]
    
    return None, None

def get_latest_png_path(project_root, data_type):
    latest_year, latest_month_folder = get_latest_data_folder(project_root, data_type)
    
    folder_path = os.path.join(project_root, f"Number of {data_type}", str(latest_year), latest_month_folder)
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    
    return f"{url_encode(f'Number of {data_type}')}/{latest_year}/{url_encode(latest_month_folder)}/{png_files[0]}"

def get_latest_json_data(project_root, data_type, field_name):
    latest_year, latest_month_folder = get_latest_data_folder(project_root, data_type)
    folder_path = os.path.join(project_root, f"Number of {data_type}", str(latest_year), latest_month_folder)
    return read_month_json_data(folder_path, field_name)

def generate_latest_month_section(project_root):
    latest_year, latest_month_folder = get_latest_data_folder(project_root, "Flows")
    
    latest_month_flows, flows_nonzero_days = get_latest_json_data(project_root, "Flows", DATA_TYPES["Flows"])
    latest_month_words, words_nonzero_days = get_latest_json_data(project_root, "Words", DATA_TYPES["Words"])
    
    daily_avg_flows = latest_month_flows / flows_nonzero_days
    daily_avg_words = latest_month_words / words_nonzero_days
    
    flows_png_path = get_latest_png_path(project_root, "Flows")
    words_png_path = get_latest_png_path(project_root, "Words")
    
    return f"""### Latest Month ({latest_month_folder.split('-')[1]} {latest_year})

<div align="center">

| ![Flows Chart]({flows_png_path}) | ![Words Chart]({words_png_path}) |
| :-: | :-: |
| Total Number of Flows = {latest_month_flows:,} | Total Number of Words = {latest_month_words:,} |
| Daily Average = {round(daily_avg_flows):,} | Daily Average = {round(daily_avg_words):,} |

</div>"""

def update_readme(readme_path, section, section_content):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    markers = {
        'flows': ("<!-- INDEX-FLOWS-START -->", "<!-- INDEX-FLOWS-END -->"),
        'words': ("<!-- INDEX-WORDS-START -->", "<!-- INDEX-WORDS-END -->"),
        'stats': ("<!-- STATS-START -->", "<!-- STATS-END -->"),
        'lastmonth': ("<!-- LASTMONTH-START -->", "<!-- LASTMONTH-END -->")
    }
    
    if section not in markers:
        return
    
    start_marker, end_marker = markers[section]
    before, _, rest = content.partition(start_marker)
    _, _, after = rest.partition(end_marker)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"{before}{start_marker}\n{section_content}\n{end_marker}{after}")

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(project_root, "README.md")
    
    stats = calculate_stats(project_root)
    update_readme(readme_path, 'stats', generate_stats_section(stats))
    update_readme(readme_path, 'lastmonth', generate_latest_month_section(project_root))
    
    for data_type in DATA_TYPES:
        section_name = f"Number of {data_type}"
        section_key = data_type.lower()
        section_root = os.path.join(project_root, section_name)
        tree, month_count = generate_tree(section_root, section_name)
        section_content = f"""<details>

<summary>
   <strong>
\t  <a href="{url_encode(section_name)}">All stats over {month_count} months</a>
   </strong>
</summary>

{chr(10).join(tree)}
</details>"""
        update_readme(readme_path, section_key, section_content)

if __name__ == "__main__":
    main()
