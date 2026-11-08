# Upload Guide — put this project on GitHub (under 10 minutes)

Your GitHub: **github.com/Raheem-1234** · The ZIP with everything:
`cwt-sentiment-agent.zip` (sent with this project).

## Option A — GitHub website (easiest, no installs)

1. Unzip `cwt-sentiment-agent.zip` on your laptop. You'll get a folder
   named `cwt-sentiment-agent`.
2. Go to **github.com** → log in → top-right **+** → **New repository**.
3. Repository name: `cwt-sentiment-agent` · keep it **Public** ·
   do NOT tick "Add a README" (we already have one) → **Create repository**.
4. On the new repo page, click **uploading an existing file**.
5. Open the unzipped folder, select **everything inside it**
   (config.py, main.py, README.md, requirements.txt, .env.example,
   .gitignore, SUBMISSION_EMAIL.md, UPLOAD_GUIDE.md, and the `src` and
   `output` folders) and drag it all into the browser window.
   ⚠️ Do NOT upload the `.venv` folder if you see one — it's huge and not needed.
6. Wait for the upload bar to finish → click **Commit changes**.
7. Your repo link is now: `https://github.com/Raheem-1234/cwt-sentiment-agent`
8. Open `SUBMISSION_EMAIL.md`, paste that link in place of the placeholder,
   and send the email to **gilad@crowdwisdomtrading.com**.

## Option B — GitHub Desktop (if you prefer an app)

1. Install GitHub Desktop (desktop.github.com) and log in.
2. **File → Add local repository** → choose the unzipped
   `cwt-sentiment-agent` folder (if it says "not a git repo", choose
   **create a repository** there instead).
3. Click **Publish repository** → keep the name `cwt-sentiment-agent`,
   keep it Public → **Publish**.
4. Same final step: paste the repo link into `SUBMISSION_EMAIL.md` and send.

## Quick checks before you send the email

- [ ] Open your repo page — you can see README content rendered on the front page.
- [ ] Click into `output/` — `report.html` and `predictions.csv` are there.
- [ ] Search the repo for "APIFY_TOKEN=" — the only match should be the
      empty placeholder in `.env.example`. **No real tokens anywhere.**
- [ ] Deadline: submit within 5–7 days of receiving the task (~13–15 Nov 2026).

## If CWT asks you to run it live

```bash
pip install -r requirements.txt
python main.py
```
It runs with no API keys (real prices + real news + public social feed).
With your own Apify/Exa keys in a `.env` file, it uses those sources instead.
