# Model

**SMS Spam Detection**  
**Author:** Abhishek Kushare

How the classifier is trained, saved, and used at inbox time.

## 1. Dataset

File: `spam.csv` (SMS Spam Collection).

| Item | Value |
|---|---|
| Encoding | `latin-1` |
| Messages | 5,572 |
| Ham | 4,825 |
| Spam | 747 |
| Original columns | `v1` label, `v2` text, three unused columns |

The unused columns are dropped. `v1` becomes `label`, `v2` becomes `text`.

```text
ham  → 0
spam → 1
```

The set is imbalanced: about 87 percent ham. Accuracy alone looks strong because most messages are ham. Spam recall is the number to watch.

## 2. Split and tokens

```text
train_test_split(..., test_size=0.20, random_state=42)
```

About 4,457 messages train the network. About 1,115 are held out. The split is not stratified.

`Tokenizer` is fit on the training texts only. Each message becomes a list of word ids. Sequences are padded or trimmed to **8 tokens**, post-padding. The running app uses the same length in `model.py`.

Eight tokens is short. For a longer SMS, the default Keras padding keeps the **end** of the message and drops the beginning. Unknown words are dropped because no out-of-vocabulary token was reserved.

## 3. Network

TensorFlow **2.10.1**, Keras `Sequential`.

```text
Embedding(vocabulary size, 24, input_length=8)
Flatten
Dense(500, ReLU)
Dense(200, ReLU)
Dropout(0.5)
Dense(100, ReLU)
Dense(1, Sigmoid)
```

The notebook summary reports **407,821** trainable parameters.

| Setting | Value |
|---|---|
| Optimizer | RMSprop |
| Loss | binary cross-entropy |
| Metric | accuracy |
| Max epochs | 50 |
| Early stopping | validation loss, patience 10 |
| Decision threshold | 0.5 |

The test split is also passed as `validation_data`, so the reported score is not from a third untouched set.

## 4. Result recorded from training

A training run of `train_export_model.py` stopped at epoch 12.

Notebook evaluation on the 1,115-message test split:

| | Precision | Recall | Support |
|---|---:|---:|---:|
| Ham (0) | 0.98 | 1.00 | 965 |
| Spam (1) | 0.98 | 0.89 | 150 |
| Accuracy | | 0.982 | 1,115 |

About one in ten spam messages in that split was labelled ham.

## 5. Files the app needs

```text
spam_model/
├── saved_model.pb
├── keras_metadata.pb
├── variables/
└── tokenizer.pkl
```

`model.py` loads both the SavedModel and `tokenizer.pkl`. Git ignores `spam_model/`. Create it with:

```powershell
python train_export_model.py
```

or by running every cell in `spam-detection-explore.ipynb`.

Prediction in the inbox:

```text
process_sms(text) → model.predict → 1 if probability > 0.5 else 0
```

## 6. Limits worth remembering

- The sequence length is 8 words.
- Spam is the minority class, and the split is not stratified.
- The same test rows are used for early stopping and the final score.
- Live Twilio traffic will not match the 2000s SMS collection exactly, so inbox labels can be wrong.
