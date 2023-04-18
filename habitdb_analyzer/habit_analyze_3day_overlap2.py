import pandas as pd
import numpy as np
from keras.layers import Input, Dense
from keras.models import Model
from sklearn.preprocessing import StandardScaler
import json

with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

# load data from file
data = json.load(open(obsidian_dir+"habitsdb.txt"))


# loop through habits and update values
for habit_name in data:
    habit_values = data[habit_name]
    new_habit_values = {}
    for date in sorted(habit_values):
        if date < "2022-09-27":
            continue
        if "Pushups" in habit_name:
            last_value = round(habit_values[date]/30)
        elif "Situps" in habit_name:
            last_value = round(habit_values[date]/50)
        elif "Squats" in habit_name:
            last_value = round(habit_values[date]/30)
        elif "Cold Shower" in habit_name:
            if habit_values[date] > 0 and habit_values[date] < 3:
                last_value = 3
            last_value = round(habit_values[date]/3)
        else:
            last_value = habit_values[date]
        new_habit_values[date] = last_value
        if date == "2022-09-27":
            break
    data[habit_name] = new_habit_values

# filter out dates prior to "2022-09-27"
for habit_name in data:
    habit_values = data[habit_name]
    data[habit_name] = {date: habit_values[date] for date in habit_values if date >= "2022-09-27"}

# save updated data to file
with open("updated_habitsdb.txt", "w") as f:
    json.dump(data, f)

df = pd.DataFrame(data)
df.fillna(value=0, inplace=True)

# Step 2: Feature engineering
# Compute daily statistics
df_stats = pd.DataFrame({
    "date": df.index,
    "total_habits": df.sum(axis=1),
    "avg_habits": df.mean(axis=1),
    "std_habits": df.std(axis=1)
})

# Normalize the features
scaler = StandardScaler()
X = scaler.fit_transform(df_stats[["total_habits", "avg_habits", "std_habits"]])

# Step 3: Train autoencoder model
# Define the input and output layers
input_layer = Input(shape=(X.shape[1],))
encoded = Dense(2, activation='relu')(input_layer)
decoded = Dense(X.shape[1], activation='linear')(encoded)

# Create the autoencoder model
autoencoder = Model(input_layer, decoded)

# Compile the model
autoencoder.compile(optimizer='adam', loss='mse')

# Fit the model on the training data
autoencoder.fit(X, X, epochs=100, batch_size=16, shuffle=True)

# Step 4: Use the model for anomaly detection
# Compute the reconstruction error for each data point with 3-day overlapping window
reconstructions = autoencoder.predict(X)
mse = np.mean(np.power(X - reconstructions, 2), axis=1)
window_size = 3
rolling_mse = np.convolve(mse, np.ones(window_size)/window_size, mode='valid')

# Identify the data points with the highest reconstruction error
threshold = np.percentile(rolling_mse, 95)
anomaly_indexes = np.argwhere(rolling_mse > threshold).flatten()
anomaly_dates = df_stats.iloc[anomaly_indexes]["date"]

anomalies = pd.DataFrame({
    "date": anomaly_dates,
    "total_habits": df_stats.iloc[anomaly_indexes]["total_habits"],
    "avg_habits": df_stats.iloc[anomaly_indexes]["avg_habits"],
    "std_habits": df_stats.iloc[anomaly_indexes]["std_habits"],
    "rolling_mse": rolling_mse[anomaly_indexes]
})

# Save the anomalies to a file
anomalies.to_csv("anomalies.csv", index=False)

print(anomalies)
