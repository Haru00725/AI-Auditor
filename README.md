# 🌐 AI Website Auditor

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API%20v4-34A853?style=flat-square&logo=googlesheets&logoColor=white)](https://developers.google.com/sheets/api)
[![Groq AI](https://img.shields.io/badge/Groq-Fast%20Inference-F55036?style=flat-square)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Challenge](https://img.shields.io/badge/%2325x25AI-Day%204-purple?style=flat-square)](#)

> **Automate lead audits & cold outreach pitches directly in Google Sheets.**  
> Built as part of **Day 4 of the #25x25AI Challenge**.

---

## 💡 What It Does

Cold pitching local businesses with generic messages rarely works. What *does* work is pointing out real, verifiable issues on their website and offering a fix.

**AI Website Auditor** automates this entire workflow:
1. **Reads** business names and website URLs directly from your Google Sheet.
2. **Audits** each site with deterministic Python checks (speed, mobile responsiveness, SEO tags, CTAs, SSL, etc.).
3. **Generates** a personalized, human-sounding cold outreach opening line using Groq AI.
4. **Writes** the top 3 issues, the custom pitch, and an "Audited" status badge right back into your Google Sheet.

> ⚡ **No AI key? No problem!** The script includes a built-in rule-based pitch generator. If you don't provide a Groq API key, it still audits websites and generates outreach pitches completely free.

---

## 📊 Before & After in Google Sheets

### Before Running:
| Business Name | Website |
| :--- | :--- |
| Sunset Bakery | `sunsetbakery.com` |
| Downtown Dental | `downtowndentalcare.com` |

### After Running:
| Business Name | Website | Top Issues | Pitch Line | Audited |
| :--- | :--- | :--- | :--- | :--- |
| Sunset Bakery | `sunsetbakery.com` | • Slow to load (4.2s)<br>• Not mobile-friendly (no viewport tag)<br>• No clear call-to-action | *"Hi Sunset Bakery, noticed your site takes 4.2s to load on mobile—visitors usually bounce after 3s. Want me to help speed it up?"* | Yes |
| Downtown Dental | `downtowndentalcare.com` | • No phone number visible<br>• Missing meta description<br>• Footer says © 2021 | *"Hi Downtown Dental, spotted that customers on your site can't click to call directly from their phones. Happy to send over a quick fix if you'd like!"* | Yes |

---

## 🔍 The 10 Website Checks

The audit is powered by plain, factual Python checks—**zero AI hallucinations**:

| Check | What It Looks For | Why It Matters |
| :--- | :--- | :--- |
| 🔒 **HTTPS / SSL** | Verifies URL starts with `https://` | Insecure sites trigger browser warnings and lose trust. |
| ⚡ **Load Speed** | Measures initial page response time (`> 3s`) | 53% of mobile visits are abandoned if pages take >3s to load. |
| 📱 **Mobile Viewport** | Checks for `<meta name="viewport">` | Missing viewport tag makes websites unusable on mobile devices. |
| 🏷️ **Page Title** | Checks for a valid `<title>` tag | Missing titles hurt Google rank and display poorly in search results. |
| 📝 **Meta Description** | Checks for `<meta name="description">` | Missing descriptions cause search engines to show random snippets. |
| 🔤 **Heading Structure** | Validates exactly one `<h1>` tag | Missing or duplicate H1 headings confuse search crawlers. |
| 📞 **Phone Number** | Looks for `tel:` links or phone patterns | Customers on mobile can't quickly call to make inquiries or orders. |
| 🎯 **Call-to-Action (CTA)** | Scans for keywords (*book, reserve, order, quote...*) | Missing CTAs lead to high bounce rates and lost conversions. |
| 🖼️ **Image Alt Tags** | Flags if >50% of images lack `alt` text | Hurts SEO visibility and web accessibility. |
| 📅 **Copyright Freshness** | Checks footer year against current year | Outdated copyright dates make businesses look inactive or abandoned. |

---

## 🚀 Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Haru00725/AI-Auditor.git
cd AI-Auditor
```

### 2. Set Up a Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Google Cloud Setup (Service Account)

The script connects to your Google Sheet using a Google Cloud Service Account:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `ai-website-auditor`).
3. Enable both:
   - **Google Sheets API**
   - **Google Drive API**
4. Navigate to **IAM & Admin** > **Service Accounts** and click **Create Service Account**.
5. Give it a name (e.g., `sheet-auditor`) and click **Done**.
6. Click on the created service account > **Keys** tab > **Add Key** > **Create new key** > Select **JSON**.
7. Download the JSON file, rename it to `service_account.json`, and place it in the root folder of this project.
8. **Important:** Open your Google Sheet in your browser, click **Share**, and share it with the service account email (found in your `service_account.json` under `client_email`) as an **Editor**.

---

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and add your [Groq API Key](https://console.groq.com/keys) (free):

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
AI_MODEL=qwen/qwen3.8-27b
```

*(Optional: You can leave `GROQ_API_KEY` blank to use the built-in fallback pitch template.)*

---

### 5. Format Your Google Sheet

Make sure your Google Sheet's first row (row 1) contains at least these two column headers:
- `Business Name`
- `Website`

The auditor will automatically create the `Top Issues`, `Pitch Line`, and `Audited` columns if they don't already exist!

---

## 💻 Usage

Run the auditor from your terminal:

```bash
python website_auditor.py --sheet "Your Sheet Name" --limit 5
```

### Command Line Options

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--sheet` | string | *required* | The exact name of your Google Sheet. |
| `--limit` | int | `10` | Maximum number of websites to audit in this run. |
| `--redo` | flag | `False` | Re-audit websites even if they are already marked `Audited = Yes`. |

### Examples:

Audit up to 20 un-audited businesses:
```bash
python website_auditor.py --sheet "Dental Clinics - NY" --limit 20
```

Force re-auditing already processed rows:
```bash
python website_auditor.py --sheet "Dental Clinics - NY" --limit 10 --redo
```

---

## 📁 Project Structure

```text
ai-website-auditor/
├── website_auditor.py        # Core auditing and pitch generation script
├── requirements.txt          # Python project dependencies
├── .env.example              # Template for environment configuration
├── .gitignore                # Protects secrets from being pushed to Git
├── service_account.json      # Your Google Cloud credentials (DO NOT COMMIT)
└── README.md                 # Project documentation
```

---

## 🔒 Security Best Practices

> ⚠️ **NEVER commit your `service_account.json` or `.env` files to GitHub!**
> 
> The included `.gitignore` file automatically excludes them. Always double-check before pushing:
> ```bash
> git status
> ```
> Verify that neither `.env` nor `service_account.json` appear in the staged files list.

---

## 🛠️ Tech Stack

- **Python 3**
- [**BeautifulSoup4**](https://www.crummy.com/software/BeautifulSoup/) & [**Requests**](https://requests.readthedocs.io/) - Fast HTML parsing & network auditing
- [**gspread**](https://docs.gspread.org/) & [**google-auth**](https://google-auth.readthedocs.io/) - Google Sheets API automation
- [**Groq API**](https://groq.com/) - Ultra-fast LLM inference for natural cold outreach pitches

---

## 🤝 Contributing

Contributions, feedback, and issue reports are welcome! Feel free to open an issue or submit a pull request.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
