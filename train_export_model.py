"""Train spam classifier and export spam_model/ + tokenizer.pkl (notebook pipeline)."""
import os
import pickle

import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, Dropout, Embedding, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

os.chdir(os.path.dirname(os.path.abspath(__file__)))

df = pd.read_csv("spam.csv", encoding="latin-1")
data = df.copy()
data.drop(columns=["Unnamed: 2", "Unnamed: 3", "Unnamed: 4"], inplace=True)
data = data.rename(columns={"v1": "label", "v2": "text"})
data["label"] = data["label"].map({"spam": 1, "ham": 0})

X = data["text"].values
y = data["label"].values
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

t = Tokenizer()
t.fit_on_texts(X_train)
encoded_train = t.texts_to_sequences(X_train)
encoded_test = t.texts_to_sequences(X_test)

max_length = 8
padded_train = pad_sequences(encoded_train, maxlen=max_length, padding="post")
padded_test = pad_sequences(encoded_test, maxlen=max_length, padding="post")

vocab_size = len(t.word_index) + 1
model = Sequential()
model.add(Embedding(vocab_size, 24, input_length=max_length))
model.add(Flatten())
model.add(Dense(500, activation="relu"))
model.add(Dense(200, activation="relu"))
model.add(Dropout(0.5))
model.add(Dense(100, activation="relu"))
model.add(Dense(1, activation="sigmoid"))

model.compile(optimizer="rmsprop", loss="binary_crossentropy", metrics=["accuracy"])
early_stop = EarlyStopping(monitor="val_loss", mode="min", verbose=1, patience=10)
model.fit(
    x=padded_train,
    y=y_train,
    epochs=50,
    validation_data=(padded_test, y_test),
    verbose=1,
    callbacks=[early_stop],
)

model.save("spam_model")
with open("spam_model/tokenizer.pkl", "wb") as output:
    pickle.dump(t, output, pickle.HIGHEST_PROTOCOL)

print("Saved spam_model/ and spam_model/tokenizer.pkl")
