# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import subprocess
import json
from datetime import datetime


# %%
def get_listed_dates(listed: list) -> dict:
    dates = {}
    for tag in listed:
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa1 in position 1494: invalid start byte
        # Some commit messages contain invalid characters
        show_output = subprocess.check_output(
            ["git", "show", tag],
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        
        date_lines = [line for line in show_output.splitlines() if line.startswith("Date:")]
        if not date_lines:
            continue
        
        last_date_line = date_lines[-1].partition("Date:")[2].strip()
        dates[tag] = last_date_line
    return dates


# %%
def convert_strdate_to_datetime(dates: dict) -> dict:
    datetime_dates = {}
    for tag, strdate in dates.items():
        datetime_dates[tag] = int(datetime.strptime(strdate, "%a %b %d %H:%M:%S %Y %z").timestamp())
    return datetime_dates


# %%
# Step 1: Get issues

# !git tag | grep FIX | sed -r "s/FIX-([0-9]+)-[0-9]+/FIX-\1/" | sort | uniq > issues.txt

# %%
# Step 2: Get Fix-tags

tags = subprocess.check_output(["git", "tag"], text=True)

with open("issues.txt", "r") as f:
    issues = f.read().splitlines()

matched_tags = [tag for tag in tags.splitlines() if tag.startswith(tuple(issue for issue in issues))]

with open("fix-tags.txt", "w") as f:
    f.write("\n".join(matched_tags) + "\n")

# %%
# Step 3: Get Fixed date

with open("fix-tags.txt", "r") as f:
    fixes = f.read().splitlines()

dates = get_listed_dates(fixes)

with open("fix-dates.json", "w", encoding="utf-8") as f:
    json.dump(dates, f, ensure_ascii=False, indent=2)

# %%
# Step 4: Get Bug-tags

with open("fix-tags.txt", "r") as f:
    fixes = f.read().splitlines()

bug_tags = [f.replace("FIX", "BUG") for f in fixes]
all_tags = subprocess.check_output(["git", "tag"], text=True).splitlines()

matched_tags = [tag for tag in all_tags if tag.startswith(tuple(bug for bug in bug_tags))]

with open("bug-tags.txt", "w") as f:
    f.write("\n".join(matched_tags) + "\n")

# %%
# Step 5: Get Bug-injected date

with open("bug-tags.txt", "r") as f:
    bugs = f.read().splitlines()

dates = get_listed_dates(bugs)

with open("bug-dates.json", "w", encoding="utf-8") as f:
    json.dump(dates, f, ensure_ascii=False, indent=2)

# %%
# Step 6: Convert timestamp to unixtime

with open("fix-dates.json", "r", encoding="utf-8") as f:
    fix_dates = json.load(f)

with open("bug-dates.json", "r", encoding="utf-8") as f:
    bug_dates = json.load(f)

fix_dates_dt = convert_strdate_to_datetime(fix_dates)
bug_dates_dt = convert_strdate_to_datetime(bug_dates)

with open("fix-dates-dt.json", "w", encoding="utf-8") as f:
    json.dump({k: v for k, v in fix_dates_dt.items()}, f, ensure_ascii=False, indent=2)

with open("bug-dates-dt.json", "w", encoding="utf-8") as f:
    json.dump({k: v for k, v in bug_dates_dt.items()}, f, ensure_ascii=False, indent=2)

# %%
# Step 7: Calculate a bug's life

with open("fix-dates-dt.json", "r", encoding="utf-8") as f:
    fix_dates_dt = json.load(f)

with open("bug-dates-dt.json", "r", encoding="utf-8") as f:
    bug_dates_dt = json.load(f)

bug_lifetimes = {"-".join(bug_tag.replace("BUG", "FIX").split("-")[0:-1]): fix_dates_dt["-".join(bug_tag.replace("BUG", "FIX").split("-")[0:-1])] - bug_dates_dt[bug_tag] for bug_tag in bug_dates_dt.keys()}

average_lifetime = sum(bug_lifetimes.values()) / len(bug_lifetimes)
max_key = max(bug_lifetimes, key=bug_lifetimes.get)
min_key = min(bug_lifetimes, key=bug_lifetimes.get)
maximum_lifetime = max(bug_lifetimes.values())
minimum_lifetime = min(bug_lifetimes.values())

print(f"Average bug lifetime: {average_lifetime} seconds")
print(f"Maximum bug lifetime: {max_key} {maximum_lifetime} seconds")
print(f"Minimum bug lifetime: {min_key} {minimum_lifetime} seconds")

# %%
