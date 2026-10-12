# Windows setup

**SMS Spam Detection**  
**Author:** Abhishek Kushare

Steps that match this machine: Windows, Python 3.10, TensorFlow 2.10.1, MySQL 8.

## 1. What to install

| Install | Why |
|---|---|
| Python 3.10.11 | TensorFlow 2.10.1 does not target 3.11+ |
| MySQL Server 8, Full or Server | The database engine. Workbench is the practical way to create the schema |
| Microsoft Visual C++ 2015–2022 x64 | Only if `import tensorflow` fails with a missing DLL |

The project folder may contain an old `pyvenv.cfg` from Linux. Do not activate that environment.

## 2. Virtual environment

OneDrive paths can exceed Windows’ default path limit and break `pip`. This project uses a short path:

```text
C:\Users\kusharea\AppData\Local\Programs\spam310venv
```

PowerShell:

```powershell
& "C:\Users\kusharea\AppData\Local\Programs\spam310venv\Scripts\Activate.ps1"
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

From the project folder:

```powershell
python -m pip install -r requirements.txt
```

Pinned versions are in `requirements.txt` (Flask 2.2.5, TensorFlow 2.10.1, and the rest). `twilio` is unpinned there; this environment installed **9.11.2**.

## 3. MySQL

1. Start the **MySQL80** service (`services.msc`).
2. Open Workbench with a user that can create a database.
3. Run `setup_mysql.sql`, or the statements below. Replace the sample password if you use it.

```sql
CREATE DATABASE IF NOT EXISTS SMS_SPAM_DETECTION;

USE SMS_SPAM_DETECTION;

CREATE TABLE IF NOT EXISTS users (
  authid VARCHAR(64) NOT NULL,
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  tno VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  suggestions TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

If registration returns access denied (error 1044), the login user can connect but cannot use this database. As an administrator:

```sql
GRANT ALL PRIVILEGES ON SMS_SPAM_DETECTION.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

## 4. Environment file

Create `.env` in the project folder. Do not commit it.

```env
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=SMS_SPAM_DETECTION
FLASK_SECRET_KEY=replace-this
```

`app.py` reads these names. Twilio SID and token are entered on the Sign In form.

## 5. Model artifacts

`model.py` fails until this directory exists:

```text
spam_model/tokenizer.pkl
spam_model/saved_model.pb
```

Generate them:

```powershell
python train_export_model.py
```

The script reads `spam.csv`, trains, and writes `spam_model/`. Training uses the CPU if CUDA is not installed. The `cudart64_110.dll` warning is safe to ignore in that case.

## 6. Run

```powershell
python app.py
```

Open `http://127.0.0.1:8001`.

1. Home → enter Twilio Account SID and Auth Token → Submit.  
   Or use **Sign In** in the header. Register sits to the right of Sign In.
2. Inbox lists up to 10 messages with IST times. Green is ham, red is spam.
3. The moon/sun control switches theme.
4. After sign-in the header turns teal and shows the name (or SID), Inbox, Contact, and **Sign Out**. Signed out, it is slate.

A new Twilio account with no SMS shows an empty inbox. Send a text to the Twilio number, then refresh.

## 7. If something fails

| Symptom | What to check |
|---|---|
| `No module named tensorflow` | The prompt is not using `spam310venv` |
| Long-path error during pip | Install into a short path, not under OneDrive |
| `spam_model` or tokenizer missing | Run `train_export_model.py` |
| Registration or feedback error about MySQL | Service running, `.env` password, `GRANT` on `SMS_SPAM_DETECTION` |
| Sign-in says the ID and token are not valid | SID and Auth Token are a pair from the same Twilio account |
| Inbox is empty | Twilio logs have no messages yet |
| Inbox asks you to sign in after a restart | The saved session credentials could not rebuild the Twilio client. Sign in again |

## 8. Git

```powershell
git status
```

Confirm `.env` and `.venv/` are absent before `git add`. `spam_model/` is ignored as well. Anyone who clones the repo must train or copy the model before classification works.
