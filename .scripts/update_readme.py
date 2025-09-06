import os
import json

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
            entries.append(f"* <details>\n\t<summary>\n\t  <strong>\n\t\t<a href=\"{section_folder.replace(' ', '%20')}/{dname}\">{dname}</a>\n\t  </strong>\n\t</summary>")
            sub_entries, sub_month_count = generate_tree(base_dir, section_folder, drel_path, indent + 1)
            entries.extend(sub_entries)
            month_count += sub_month_count
            entries.append("  </details>")
        elif indent == 1:
            month_count += 1
            month_abs_dir = os.path.join(base_dir, drel_path)
            month_files = [f for f in os.listdir(month_abs_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            image_entry = ""
            if month_files:
                img_href = f"{section_folder.replace(' ', '%20')}/{drel_path.replace(' ', '%20')}/{month_files[0]}"
                image_entry = f"\n\t   <a href=\"{img_href}\">\n\t   <kbd>\n\t   <img src=\"{img_href}\" width=\"400\" title=\"🖱️ Click me to view an interactive chart!\"/>\n\t   </kbd>\n\t   </a>"
            entries.append(f"\n\t* <details>\n\t   <summary>\n\t   <a href=\"{section_folder.replace(' ', '%20')}/{drel_path.replace(' ', '%20')}\">{dname}</a>\n\t   </summary>{image_entry}")
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
            json_files = [f for f in os.listdir(month_path) if f.endswith('.json')]
            if json_files:
                try:
                    with open(os.path.join(month_path, json_files[0]), 'r', encoding='utf-8') as f:
                        month_data = json.load(f)
                        if 'data' in month_data:
                            monthly_totals.append(sum(entry.get(field_name, 0) for entry in month_data['data']))
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
    return monthly_totals

def calculate_stats(project_root):
    flows_monthly_totals = get_monthly_totals(project_root, "Flows", "Number of Flows")
    words_monthly_totals = get_monthly_totals(project_root, "Words", "Number of Words")
    
    total_flows = sum(flows_monthly_totals)
    total_flow_hours = total_flows * 0.55
    total_words = sum(words_monthly_totals)
    num_months = max(len(flows_monthly_totals), len(words_monthly_totals))
    
    monthly_avg_flows = total_flows / num_months
    monthly_avg_words = total_words / num_months
    estimated_weeks = num_months * 4.33
    estimated_days = num_months * 30.44
    weekly_avg_flows = total_flows / estimated_weeks
    daily_avg_flows = total_flows / estimated_days
    weekly_avg_words = total_words / estimated_weeks
    daily_avg_words = total_words / estimated_days
    
    return {
        'total_flows': total_flows,
        'total_flow_hours': int(total_flow_hours),
        'total_words': total_words,
        'monthly_avg_flows': int(monthly_avg_flows),
        'monthly_avg_hours': int(monthly_avg_flows * 0.55),
        'weekly_avg_flows': int(weekly_avg_flows),
        'weekly_avg_hours': int(weekly_avg_flows * 0.55),
        'daily_avg_flows': round(daily_avg_flows, 1),
        'daily_avg_hours': round(daily_avg_flows * 0.55, 1),
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
    
    return f"Number%20of%20{data_type.replace(' ', '%20')}/{latest_year}/{latest_month_folder.replace(' ', '%20')}/{png_files[0]}"

def get_latest_json_data(project_root, data_type, field_name):
    latest_year, latest_month_folder = get_latest_data_folder(project_root, data_type)
    
    folder_path = os.path.join(project_root, f"Number of {data_type}", str(latest_year), latest_month_folder)
    json_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.json')]
    
    try:
        with open(os.path.join(folder_path, json_files[0]), 'r', encoding='utf-8') as f:
            month_data = json.load(f)
            if 'data' in month_data:
                return sum(entry.get(field_name, 0) for entry in month_data['data']), len(month_data['data'])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return 0, 0

def generate_last_month_section(project_root):
    latest_year, latest_month_folder = get_latest_data_folder(project_root, "Flows")
    
    latest_month_flows, flows_days_count = get_latest_json_data(project_root, "Flows", "Number of Flows")
    latest_month_words, words_days_count = get_latest_json_data(project_root, "Words", "Number of Words")
    
    days_in_month = max(flows_days_count, words_days_count)
    
    daily_avg_flows = latest_month_flows / days_in_month if latest_month_flows > 0 else 0
    daily_avg_words = latest_month_words / days_in_month if latest_month_words > 0 else 0
    
    flows_png_path = get_latest_png_path(project_root, "Flows")
    words_png_path = get_latest_png_path(project_root, "Words")
    
    return f"""### Latest Month ({latest_month_folder.split('-')[1]} {latest_year})

<div align="center">

| ![Flows Chart]({flows_png_path}) | ![Words Chart]({words_png_path}) |
| :-: | :-: |
| Total Number of Flows = {latest_month_flows:,} | Total Number of Words = {latest_month_words:,} |
| Daily Average = {int(daily_avg_flows):,} | Daily Average = {int(daily_avg_words):,} |

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
    update_readme(readme_path, 'lastmonth', generate_last_month_section(project_root))
    
    for section_name, section_key in [("Number of Flows", 'flows'), ("Number of Words", 'words')]:
        section_root = os.path.join(project_root, section_name)
        tree, month_count = generate_tree(section_root, section_name)
        section_content = f"""<details>

<summary>
   <strong>
\t  <a href="{section_name.replace(' ', '%20')}">All stats over {month_count} months</a>
   </strong>
</summary>

{chr(10).join(tree)}
</details>"""
        update_readme(readme_path, section_key, section_content)

if __name__ == "__main__":
    main()
