# AirCon Stock Watcher

Watches configured list of UK retailers for an air conditioner matching your chosen brands and target BTU.

Emails you the moment one is in-stock.

Runs on a schedule via GitHub Actions for free.

## One-time setup

1. Push this repo to GitHub
2. **Enable 2-Step Verification** on the Gmail account you want alerts sent from, then create an
   [App Password](https://myaccount.google.com/apppasswords) for it.
3. In the GitHub repo, go to **Settings → Secrets and variables → Actions** and add:
   - `GMAIL_ADDRESS` — the Gmail address the alerts are sent *from*.
   - `GMAIL_APP_PASSWORD` — the app password from step 2.
   - `ALERT_EMAIL_TO` — the address(es) alerts are sent *to*. One address, or several
     comma-separated (e.g. `you@gmail.com,partner@gmail.com`).
4. Go to the **Actions** tab and enable workflows if prompted.


## Configuration

Brands, target BTU, which retailers to skip, and the failure alert threshold are all plain
data in `config.json` at the repo root, e.g.

```json
{
  "target_btu": 14000,
  "brands": ["meaco", "black+decker"],
  "ignored_retailers": ["amazon"],
  "failure_alert_threshold": 5,
  "failure_reminder_days": 7
}
```

Adding a retailer to `ignored_retailers` above means that it will no longer be used. 
List a name there to stop checking that website (e.g. it's consistently failing or blocked) without having to change any code.

Otherwise, every retailer in `RETAILER_CLASSES_BY_NAME`
(`watcher/main.py`) runs by default, so a newly-added retailer module is included automatically.

`failure_alert_threshold` is the number of consecutive failed checks a retailer needs before
you get a "this retailer looks broken" email. That email is sent only to `GMAIL_ADDRESS`
(the developer).

`failure_reminder_days` is roughly how long a retailer can stay broken before you get a
reminder email that it's still broken, after the initial "looks broken" alert.


## Adjusting other things

- **Check frequency**: edit the `cron` line in `.github/workflows/check_stock.yml`.
- **Add a brand-new retailer**: add its module in `watcher/retailers/` and register it in
  `RETAILER_CLASSES_BY_NAME` in `watcher/main.py` — it starts running automatically, no
  `config.json` change needed.

## Local development

```bash
pip install -r requirements.txt
playwright install chromium

# Required env vars for sending emails locally:
export GMAIL_ADDRESS=you@gmail.com
export GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
export ALERT_EMAIL_TO=you@gmail.com,partner@gmail.com

python -m watcher.main
pytest tests/
```