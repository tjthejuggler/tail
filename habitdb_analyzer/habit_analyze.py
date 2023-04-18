import pandas as pd
import numpy as np
from scipy import stats

# Step 1: Data preprocessing
data = {
    "habit1": {"2022-01-01": 3, "2022-01-02": 2, "2022-01-03": 4},
    "habit2": {"2022-01-01": 1, "2022-01-02": 0, "2022-01-03": 2},
    "habit3": {"2022-01-01": 2, "2022-01-02": 1},
    "habit4": {"2022-01-02": 3, "2022-01-03": 1},
    "habit5": {"2022-01-01": 1, "2022-01-03": 2}
}

df = pd.DataFrame(data)
df.fillna(value=0, inplace=True)

# Step 2: Calculate daily statistics
df_stats = pd.DataFrame({
    "date": df.index,
    "total_habits": df.sum(axis=1),
    "avg_habits": df.mean(axis=1),
    "std_habits": df.std(axis=1)
})

# Step 3: Identify outliers
# Option A: Z-score
z_scores = np.abs(stats.zscore(df_stats[["total_habits", "avg_habits", "std_habits"]]))
threshold = 2
df_stats["outlier_zscore"] = np.any(z_scores > threshold, axis=1)

# Option B: IQR
Q1 = df_stats.quantile(0.25, numeric_only=True)
Q3 = df_stats.quantile(0.75, numeric_only=True)
IQR = Q3.subtract(Q1)
df_stats["outlier_iqr"] = df_stats[["total_habits", "avg_habits", "std_habits"]].apply(
    lambda x: (x < (Q1.subtract(1.5 * IQR))) | (x > (Q3.add(1.5 * IQR))), axis=1
).any(axis=1)


# Option C: other outlier detection techniques
# You can also explore other outlier detection techniques like Local Outlier Factor (LOF), Isolation Forest, or One-class SVMs.

print(df_stats)
