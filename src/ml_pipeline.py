# ML pipeline placeholder
import pandas as pd
import numpy as np
np.random.seed(0)
import matplotlib.pyplot as plt

import seaborn as sns
import xgboost as xgb
sns.set_style('darkgrid')
pd.set_option('display.max_columns', None)

import datetime, warnings, scipy
warnings.filterwarnings("ignore")

import keras
from keras.models import Sequential
from keras.layers import Dense
from sklearn.preprocessing import StandardScaler, LabelBinarizer
from sklearn.model_selection import train_test_split
from keras.layers import Dense, Dropout , BatchNormalization
from sklearn import preprocessing
import sklearn.metrics as metrics

dfm_ready = pd.read_csv('../data/sample/flight_delay_aug2024_jul2025.csv', index_col=0)
df = dfm_ready.astype(float)

def model_metrics(a, b):
    accuracy = metrics.accuracy_score(a, b)
    precision = precision_score(a, b)
    recall = recall_score(a, b)
    f1 = f1_score(a, b)

    print('Accuracy:', round(accuracy*100, 2),'%')
    print('Precision score:', round(precision*100, 2),'%')
    print('Recall score:', round(recall*100, 2),'%')
    print('F1 score:', round(f1*100, 2),'%')

y = df['FLIGHT_STATUS']
X = df.drop(['FLIGHT_STATUS'], axis=1)

col_names = list(df.columns)

s_scaler = preprocessing.StandardScaler()
df_s = s_scaler.fit_transform(df)

df_s = pd.DataFrame(df_s, columns=col_names)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)

model_1 = Sequential()

model_1.add(Dense(50, activation='relu', input_shape=(63,)))

model_1.add(Dense(30, activation='relu'))

model_1.add(Dense(10, activation='relu'))

model_1.add(Dense(1, activation='sigmoid'))

model_1.summary()

model_1.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

results1 = model_1.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.1)

y_pred_m1 = model_1.predict(X_test)
y_pred_m1 =(y_pred_m1 > 0.5)

model_metrics(y_test, y_pred_m1)
