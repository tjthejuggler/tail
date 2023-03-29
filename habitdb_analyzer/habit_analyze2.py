import pandas as pd
import numpy as np
from keras.layers import Input, Dense
from keras.models import Model
from sklearn.preprocessing import StandardScaler
import json

# The 'total_score' unusual rating is a metric that represents how unusual a given day's habits are compared to the other days in the dataset. The total score is calculated by summing the Z-scores for each of the habit statistics (total habits, average habits, and standard deviation of habits) for that particular day.

# The Z-score is a statistical measure that indicates how many standard deviations an observation or data point is from the mean. In this case, the Z-score is used to calculate how far each day's habit statistics deviate from the average habit statistics for the dataset as a whole.

# The total score is then calculated by summing the Z-scores for each of the habit statistics for that particular day. This means that the more the habits on a particular day deviate from the average habits for the dataset, the higher the total score will be for that day.

# A high total score indicates that the habits on that particular day are highly unusual when compared to the rest of the dataset. Conversely, a low total score indicates that the habits on that day are relatively similar to the habits on the other days in the dataset.

# Overall, the total score provides a useful metric for identifying highly unusual or anomalous days in the dataset. However, it's important to note that the interpretation of the total score will depend on the specific dataset and the habits being measured. It's always important to interpret the total score in the context of the specific habits being measured and the overall goals of the analysis.

# load data from file
data = json.load(open("/home/lunkwill/Documents/obsidian_note_vault/noteVault/habitsdb.txt"))

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
# Compute the reconstruction error for each data point
reconstructions = autoencoder.predict(X)
mse = np.mean(np.power(X - reconstructions, 2), axis=1)

# Identify the data points with the highest reconstruction error
threshold = np.percentile(mse, 95)
anomalies = df_stats[mse > threshold]

print(anomalies)

print(df_stats)