import os
import json

POMODORO_HOURS = 0.55
WEEKS_PER_MONTH = 4.33
DAYS_PER_MONTH = 30.44

DATA_TYPES = ["Flows", "Words"]

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
                    return sum(values), sum(1 for v in values if v > 0)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return 0, 0

def _render_year_entry(section_folder, dname):
    return f"* <details>\n\t<summary>\n\t  <strong>\n\t\t<a href=\"{url_encode(section_folder)}/{dname}\">{dname}</a>\n\t  </strong>\n\t</summary>"

def _metric_slug(section_folder):
    """'Number of Flows'/'Number of Words' -> the site's metric slug."""
    return "flows" if section_folder == "Number of Flows" else "words"

def _month_key(drel_path):
    """'2026/07-July' -> '2026-07'."""
    parts = drel_path.replace(os.sep, '/').split('/')
    if len(parts) >= 2 and len(parts[1]) >= 2:
        return f"{parts[0]}-{parts[1][:2]}"
    return ""

def _render_month_entry(section_folder, drel_path, dname, total, daily_avg, month_files):
    href = f"{url_encode(section_folder)}/{url_encode(drel_path)}"
    image_entry = ""
    if month_files:
        img_href = f"{href}/{month_files[0]}"
        chart_url = (
            f"https://huam.ing/deep-work-machine/{_metric_slug(section_folder)}/{_month_key(drel_path)}"
        )
        image_entry = (
            f"\n\n\t   | [![{section_folder}]({img_href})]({chart_url} \"Click me to view an interactive chart!\") |"
            f"\n\t   | :-: |"
            f"\n\t   | Total = {total:,} |"
            f"\n\t   | Daily Average = {daily_avg:,} |"
        )
    return f"\n\t* <details>\n\t   <summary>\n\t   <a href=\"{href}\">{dname}</a>\n\t   </summary>{image_entry}"

def generate_tree(base_dir, section_folder, rel_dir="", indent=0):
    abs_dir = os.path.join(base_dir, rel_dir)
    dirs = sorted(
        (name, os.path.join(rel_dir, name))
        for name in os.listdir(abs_dir)
        if not name.startswith('.') and os.path.isdir(os.path.join(abs_dir, name))
    )
    dirs.reverse()

    entries = []
    month_count = 0

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

def _iter_month_folders(project_root, data_type):
    """Yield (year, month_folder, month_path) for every month, newest first."""
    section_root = os.path.join(project_root, f"Number of {data_type}")
    for year in sorted(os.listdir(section_root), reverse=True):
        year_path = os.path.join(section_root, year)
        if year.startswith('.') or not os.path.isdir(year_path):
            continue
        for month in sorted(os.listdir(year_path), reverse=True):
            month_path = os.path.join(year_path, month)
            if month.startswith('.') or not os.path.isdir(month_path):
                continue
            yield year, month, month_path


def get_monthly_totals(project_root, data_type):
    return [read_month_json_data(path, f"Number of {data_type}")[0]
            for _, _, path in _iter_month_folders(project_root, data_type)]


def calculate_stats(project_root):
    flows_monthly_totals = get_monthly_totals(project_root, "Flows")
    words_monthly_totals = get_monthly_totals(project_root, "Words")

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

|         | Monthly Average | Weekly Average | Daily Average |
| :-: | :-: | :-: | :-: |
| **Number of Flows** | 🍅 × {stats['monthly_avg_flows']}<br>≈ {stats['monthly_avg_hours']} hours | 🍅 × {stats['weekly_avg_flows']}<br>≈ {stats['weekly_avg_hours']} hours | 🍅 × {stats['daily_avg_flows']}<br>≈ {stats['daily_avg_hours']} hours |
| **Number of Words** | {stats['monthly_avg_words']:,} words | {stats['weekly_avg_words']:,} words | {stats['daily_avg_words']:,} words |

</div>"""

def get_latest_data_folder(project_root, data_type):
    return next(_iter_month_folders(project_root, data_type), (None, None, None))


def get_latest_png_path(project_root, data_type):
    year, month, month_path = get_latest_data_folder(project_root, data_type)
    png_files = [f for f in os.listdir(month_path) if f.lower().endswith('.png')]
    return f"{url_encode(f'Number of {data_type}')}/{year}/{url_encode(month)}/{png_files[0]}"


def get_latest_json_data(project_root, data_type):
    _, _, month_path = get_latest_data_folder(project_root, data_type)
    return read_month_json_data(month_path, f"Number of {data_type}")

def generate_latest_month_section(project_root):
    latest_year, latest_month_folder, _ = get_latest_data_folder(project_root, "Flows")
    
    latest_month_flows, flows_nonzero_days = get_latest_json_data(project_root, "Flows")
    latest_month_words, words_nonzero_days = get_latest_json_data(project_root, "Words")
    
    daily_avg_flows = latest_month_flows / flows_nonzero_days
    daily_avg_words = latest_month_words / words_nonzero_days
    
    flows_png_path = get_latest_png_path(project_root, "Flows")
    words_png_path = get_latest_png_path(project_root, "Words")

    latest_key = f"{latest_year}-{latest_month_folder[:2]}"
    flows_chart_url = f"https://huam.ing/deep-work-machine/flows/{latest_key}"
    words_chart_url = f"https://huam.ing/deep-work-machine/words/{latest_key}"
    
    return f"""### Latest Month ({latest_month_folder.split('-')[1]} {latest_year})

<div align="center">

| [![Flows Chart]({flows_png_path})]({flows_chart_url} "Click me to view an interactive chart!") | [![Words Chart]({words_png_path})]({words_chart_url} "Click me to view an interactive chart!") |
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
