"""
Website Auditor: reads the businesses from your Day 1 Google Sheet, checks each
business's website, and writes the top 3 problems + a one-line pitch next to it.
Built on Day 4 of #25x25AI.

The checks are done by plain Python (so they're real, measured facts).
The AI only turns those facts into a human-sounding pitch. No AI key? It still works.

Run:
    python website_auditor.py --sheet "Your Sheet Name" --limit 5
"""

import argparse
import datetime
import json
import os
import re
import time

import gspread
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

load_dotenv()

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
AI_MODEL = os.environ.get("AI_MODEL", "qwen/qwen3.8-27b")   # check console.groq.com/docs/models if changed
NEW_COLUMNS = ["Top Issues", "Pitch Line", "Audited"]
CTA_WORDS = ["book", "reserve", "order", "contact", "call us", "get a quote", "whatsapp", "enquire", "inquire"]


# ---------- 1. measure the website ----------
def audit_site(url):
    """Returns (facts, problems). 'problems' are plain-English issues, worst first."""
    if not url.startswith("http"):
        url = "https://" + url
    problems, facts = [], {"url": url}
    try:
        start = time.time()
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 (site-audit)"})
        facts["load_seconds"] = round(time.time() - start, 1)
    except Exception:
        return {"url": url, "reachable": False}, ["The website didn't load at all"]

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    facts["reachable"] = True

    if not r.url.startswith("https"):
        problems.append("Site isn't secure (no HTTPS), so browsers show a warning")
    if facts["load_seconds"] > 3:
        problems.append(f"Slow to load ({facts['load_seconds']}s), visitors leave after about 3s")
    if not soup.find("meta", attrs={"name": "viewport"}):
        problems.append("Not mobile-friendly (no viewport tag), most customers browse on phones")
    if not (soup.title and soup.title.get_text(strip=True)):
        problems.append("No page title, so it looks bad on Google")
    if not soup.find("meta", attrs={"name": "description"}):
        problems.append("No meta description, so Google shows random text for this business")
    if len(soup.find_all("h1")) != 1:
        problems.append("Missing or duplicate main heading (H1), which hurts search ranking")
    if not (soup.select_one('a[href^="tel:"]') or re.search(r"\+?\d[\d\s\-()]{8,}", text)):
        problems.append("No phone number visible, so customers can't call quickly")
    if not any(w in text for w in CTA_WORDS):
        problems.append("No clear call-to-action (book / order / contact)")
    imgs = soup.find_all("img")
    no_alt = [i for i in imgs if not i.get("alt")]
    if imgs and len(no_alt) / len(imgs) > 0.5:
        problems.append(f"{len(no_alt)} of {len(imgs)} images have no alt text (bad for SEO and accessibility)")
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d\d)", r.text, re.I)]
    if years and max(years) < datetime.date.today().year - 1:
        problems.append(f"Footer says © {max(years)}, so the site looks abandoned")
    return facts, problems


# ---------- 2. turn facts into a pitch ----------
def fallback_pitch(name, problems):
    top = problems[:3] or ["No major issues found"]
    pitch = (f"Hi {name}, I checked your website and found {len(problems)} quick fix{'es' if len(problems) != 1 else ''} "
             f"that could bring you more customers. Want me to send them over?") if problems else \
            f"Hi {name}, your site looks solid. Want help getting more customers to it?"
    return top, pitch


def ai_pitch(name, problems):
    if not GROQ_API_KEY or not problems:
        return fallback_pitch(name, problems)
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": AI_MODEL,
                "max_tokens": 300,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Business: {name}\nMeasured website problems:\n- " + "\n- ".join(problems) +
                        "\n\nReturn ONLY JSON: {\"issues\": [the 3 most important problems, each under 12 words], "
                        "\"pitch\": \"one friendly sentence I can use to open a cold message to the owner, "
                        "mentioning one specific problem\"}. Use only the problems listed."
                    ),
                }],
            },
            timeout=20,
        )
        if not r.ok:
            try:
                err_detail = r.json().get("error", {}).get("message", r.text)
            except Exception:
                err_detail = r.text
            raise Exception(f"{r.status_code} {err_detail}")
        content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
        issues = [str(i) for i in data["issues"]][:3]
        return issues, str(data["pitch"])
    except Exception as e:
        print(f"   (AI step skipped: {e})")
        return fallback_pitch(name, problems)


# ---------- 3. the sheet ----------
def ensure_columns(sheet, headers):
    """Adds Top Issues / Pitch Line / Audited headers to row 1 if they're missing."""
    for col in NEW_COLUMNS:
        if col not in headers:
            headers.append(col)
            sheet.update_cell(1, len(headers), col)
    return {h: i + 1 for i, h in enumerate(headers)}


def run(sheet_name, limit, redo):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    sheet = gspread.authorize(creds).open(sheet_name).sheet1

    headers = sheet.row_values(1)
    for needed in ("Business Name", "Website"):
        if needed not in headers:
            print(f"❌ Your sheet needs a '{needed}' column in row 1 (your Day 1 sheet has it).")
            return
    col = ensure_columns(sheet, headers)
    rows = sheet.get_all_records(expected_headers=[])

    print(f"🔎 Auditing up to {limit} websites from '{sheet_name}'\n")
    done = 0
    for i, row in enumerate(rows, start=2):
        if done >= limit:
            break
        name, site = str(row.get("Business Name", "")).strip(), str(row.get("Website", "")).strip()
        if not name or not site:
            continue
        if str(row.get("Audited", "")).strip().lower() == "yes" and not redo:
            continue

        print(f"🔎 {name}  ({site})")
        facts, problems = audit_site(site)
        issues, pitch = ai_pitch(name, problems)
        print(f"   ⚠️  {len(problems)} problem(s) found")
        print(f"   💬 {pitch}\n")

        start, end = rowcol_to_a1(i, col["Top Issues"]), rowcol_to_a1(i, col["Audited"])
        sheet.update(range_name=f"{start}:{end}", values=[["\n".join(f"• {x}" for x in issues), pitch, "Yes"]])
        done += 1
        time.sleep(1)  # be polite to the websites

    print(f"✅ Done. {done} website(s) audited. Check your sheet!")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", required=True, help="Exact name of your Google Sheet (the one from Day 1)")
    p.add_argument("--limit", type=int, default=10, help="How many websites to audit this run")
    p.add_argument("--redo", action="store_true", help="Re-audit rows already marked Audited")
    a = p.parse_args()
    run(a.sheet, a.limit, a.redo)
