# Architecture

**SMS Spam Detection**  
**Author:** Abhishek Kushare

This note explains how the running application is put together. Training details are in [MODEL.md](MODEL.md). Windows install steps are in [SETUP_WINDOWS.md](SETUP_WINDOWS.md).

## 1. Purpose

The app is a single Flask process. It serves HTML, talks to Twilio, optionally talks to MySQL, and calls a saved Keras model. There is no separate frontend build and no separate prediction service.

## 2. Runtime picture

```text
Browser
   │  HTTP :8001
   ▼
app.py
   ├── session          signed-in name and SID
   ├── Twilio Client    created after a successful sign-in
   ├── MySQL            registration and optional lookup
   └── model.py
         ├── spam_model/            SavedModel directory
         └── tokenizer.pkl          Keras Tokenizer
```

`model.py` loads the tokenizer when the process starts. `load_model()` reads the SavedModel again on each inbox request.

## 3. Routes

| Method | Path | What it does |
|---|---|---|
| GET | `/` | Home and the main sign-in form |
| POST | `/login` | Checks Twilio, then opens the inbox |
| GET | `/logout` | Clears the session and the Twilio client |
| GET | `/inbox` | Classifies up to 10 messages |
| GET, POST | `/register` | Inserts a row into `users` |
| GET | `/contact` | Feedback form (display only) |

Sign-in accepts either a matching database row or the SID and token typed into the form. Twilio is the check that matters: the app calls `accounts(sid).fetch()`. If that call fails, the visitor stays on Home with an error.

## 4. Sign-in and inbox

```text
POST /login
  → optional SELECT from users
  → Twilio account fetch
  → session['logged_in'], session['user_name'], session['user_sid']
  → redirect /inbox

GET /inbox
  → require twilio_api from this process
  → messages.stream(), first 10
  → process_sms(body)
  → predict > 0.5 → spam list, else ham list
  → inbox.html
```

The session remembers who is signed in across page loads. The Twilio client itself lives in a module global, so a server restart requires Sign In again.

Header after sign-in:

```text
[ theme ] [ user name ] [ Sign Out ] [ Register ]
```

Before sign-in, Sign Out is **Sign In**. Register stays to the right of that button. The theme icon is always immediately to its left. The choice is stored in `localStorage` under the key `theme`.

## 5. Pages

| Template | Shared parts |
|---|---|
| `templates/index.html` | nav, sign-in dialog, footer |
| `templates/inbox.html` | nav, sign-in dialog, footer |
| `templates/register.html` | nav, sign-in dialog, footer |
| `templates/contactus.html` | nav, sign-in dialog, footer |
| `templates/partials/` | head, nav, footer, scripts, login modal |

Styles live in `static/css/style.css`. Ham uses green (`#059669`). Spam uses red (`#dc2626`). The brand bar is teal (`#0f766e`).

Screenshots: [images/home-light.png](images/home-light.png), [images/home-dark.png](images/home-dark.png), [images/sign-in.png](images/sign-in.png), [images/inbox.png](images/inbox.png), [images/register.png](images/register.png).

## 6. Database

Database name: `SMS_SPAM_DETECTION`.

`users`

| Column | Type | Meaning in this app |
|---|---|---|
| `authid` | VARCHAR(64) | Twilio Account SID. Selected first, so login can read it as column 0 |
| `id` | INT, primary key | Auto-increment |
| `name` | VARCHAR(100) | Name shown after sign-in when the row exists |
| `tno` | VARCHAR(64) | Twilio Auth Token |

The insert is `INSERT INTO users(name, authid, tno)`. Lookup is `authid` plus `tno`.

MySQL settings come from `.env`: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`. If MySQL is down, sign-in can still succeed through Twilio. Registration cannot.

## 7. What this shape does not do

- It does not page beyond the first 10 messages.
- It does not keep a Twilio client per browser session in a durable store.
- The contact form does not save or send feedback.
- `aboutus1.html` is an unused course page and is not linked.
