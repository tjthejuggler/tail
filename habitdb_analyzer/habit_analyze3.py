import pandas as pd
import numpy as np
from scipy import stats
import json

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

# Load data from file
data = json.load(open(obsidian_dir+"habitsdb.txt"))

# Process data
activities = list(data.keys())
for i in range(len(activities)):
    dates = list(data[activities[i]].keys())
    for j in range(len(dates)):
        if dates[j] < "2022-09-27":
            del data[activities[i]][dates[j]]
        else:
            last_value = data[activities[i]][dates[j]]
            if "Pushups" in activities[i]:
                last_value = round(last_value/30)
            elif "Situps" in activities[i]:
                last_value = round(last_value/50)
            elif "Squats" in activities[i]:
                last_value = round(last_value/30)
            elif "Cold Shower" in activities[i]:
                if last_value > 0 and last_value < 3:
                    last_value = 3
                last_value = round(last_value/3)
            data[activities[i]][dates[j]] = last_value

# Create DataFrame
df = pd.DataFrame(data)

# Calculate daily statistics
df_stats = pd.DataFrame({
    "date": df.index,
    "total_habits": df.sum(axis=1),
    "avg_habits": df.mean(axis=1),
    "std_habits": df.std(axis=1),
    "min_habits": df.min(axis=1),
    "max_habits": df.max(axis=1),
    "range_habits": df.max(axis=1) - df.min(axis=1)
})

# Calculate score for each day based on how unusual its statistics are
stats_cols = ["total_habits", "avg_habits", "std_habits", "min_habits", "max_habits", "range_habits"]
for col in stats_cols:
    mean = df_stats[col].mean()
    std = df_stats[col].std()
    df_stats[f"{col}_score"] = np.abs((df_stats[col] - mean) / std)

df_stats["total_score"] = df_stats[[f"{col}_score" for col in stats_cols]].sum(axis=1)

# Sort by score to get list of most unusual days
df_stats_sorted = df_stats.sort_values("total_score", ascending=False)

# Print stats and list of unusual days to file
with open("habits_stats.txt", "w") as f:
    f.write("Daily Statistics\n")
    f.write(df_stats.to_string(index=False) + "\n\n")
    f.write("Most Unusual Days\n")
    f.write(df_stats_sorted[["date", "total_score"]].to_string(index=False))
