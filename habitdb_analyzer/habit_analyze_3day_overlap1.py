import pandas as pd
import numpy as np
from scipy import stats
import json

# Load data from file
data = json.load(open("/path/to/habitsdb.txt"))

# Modify the data
for habit in data:
    for date in data[habit]:
        if "Pushups" in habit:
            data[habit][date] = round(data[habit][date] / 30)
        elif "Situps" in habit:
            data[habit][date] = round(data[habit][date] / 50)
        elif "Squats" in habit:
            data[habit][date] = round(data[habit][date] / 30)
        elif "Cold Shower" in habit:
            if data[habit][date] > 0 and data[habit][date] < 3:
                data[habit][date] = 3
            data[habit][date] = round(data[habit][date] / 3)

# Convert to pandas DataFrame
df = pd.DataFrame(data)
df.fillna(value=0, inplace=True)

# Calculate daily statistics for each group of 3 days
df_stats = pd.DataFrame()
for i in range(0, len(df)-2, 3):
    group = df.iloc[i:i+3]
    df_stats = df_stats.append({
        "start_date": group.index.min(),
        "end_date": group.index.max(),
        "total_habits": group.sum(axis=0).sum(),
        "avg_habits": group.mean(axis=0).mean(),
        "std_habits": group.std(axis=0).mean(),
    }, ignore_index=True)

# Identify the most unusual groups of 3 days based on Z-score
z_scores = np.abs(stats.zscore(df_stats[["total_habits", "avg_habits", "std_habits"]]))
df_stats["z_score"] = z_scores.sum(axis=1)
df_stats.sort_values("z_score", ascending=False, inplace=True)

# Print the results to a file
with open("output.txt", "w") as f:
    f.write("Top 10 unusual groups of 3 days:\n")
    f.write(df_stats[["start_date", "end_date", "z_score"]].head(10).to_string(index=False))
    f.write("\n\n")
    f.write("All group stats:\n")
    f.write(df_stats.to_string(index=False))
