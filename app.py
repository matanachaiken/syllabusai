import streamlit as st
import anthropic
import PyPDF2
import markdown
import io
import re
import json
from icalendar import Calendar, Event
from datetime import datetime, date

# --- Page Config ---
st.set_page_config(page_title="SyllabusAI", page_icon="📚", layout="centered")

st.title("📚 SyllabusAI")
st.caption("Upload a course syllabus PDF and get a full breakdown of assignments, exams, and a personalized study schedule.")

# --- API Key ---
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    if not api_key:
        st.info("Enter your Anthropic API key above to get started.")
        st.stop()

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your syllabus PDF", type="pdf")

if uploaded_file:
    with st.spinner("Reading PDF..."):
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        pdf_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pdf_text += f"\n--- Page {i+1} ---\n{text}"

    if not pdf_text.strip():
        st.error("Could not extract text from this PDF. It may be a scanned image.")
        st.stop()

    st.success(f"✓ Read {len(reader.pages)} pages ({len(pdf_text):,} characters)")

    if st.button("✨ Parse Syllabus", type="primary"):
        client = anthropic.Anthropic(api_key=api_key)

        # --- Parse Syllabus ---
        with st.spinner("Sending to Claude... this takes 15-30 seconds"):
            prompt = f"""You are an expert academic assistant. I will give you the raw text from a course syllabus.

Your job is to extract ALL of the following and return them in clean Markdown:

## 📚 Course Info
- Course name, code, professor, semester

## 📝 Assignments
List every assignment with:
- Name
- Due date (exact date if available)
- Weight/percentage of grade (if listed)
- Description (brief)

## 📅 Exam Dates
List every quiz, midterm, and final exam with:
- Name
- Date and time
- Location (if mentioned)
- Topics covered (if mentioned)

## 📖 Weekly Schedule
Summarize the week-by-week topics if a schedule is provided.

## 🗓️ Personalized Study Schedule
Based on the deadlines and exams above, generate a recommended study schedule.
For each exam/major assignment, suggest:
- When to start studying (e.g., "Start 2 weeks before")
- Weekly study goals leading up to it

Be thorough. If info isn't in the syllabus, say "Not specified."

Here is the syllabus text:
---
{pdf_text}
---"""

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            result = message.content[0].text

        # --- Extract Calendar Events ---
        with st.spinner("Extracting dates for calendar..."):
            cal_prompt = f"""Extract all important dates from this syllabus and return ONLY a JSON array, no other text.

Each item should have:
- "title": name of the assignment/exam/deadline
- "date": in YYYY-MM-DD format
- "description": brief description (1 sentence max)

Only include items with specific dates. Example format:
[
  {{"title": "Midterm Exam", "date": "2026-03-11", "description": "In-class closed-book exam covering weeks 1-8"}},
  {{"title": "Final Project Due", "date": "2026-05-01", "description": "Creative project + 3-page reflection"}}
]

Syllabus text:
---
{pdf_text}
---"""

            cal_message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2048,
                messages=[{"role": "user", "content": cal_prompt}]
            )
            raw = cal_message.content[0].text.strip()
            raw = re.sub(r"```json|```", "", raw).strip()

            events = []
            try:
                events_data = json.loads(raw)
                for e in events_data:
                    try:
                        d = datetime.strptime(e['date'], "%Y-%m-%d").date()
                        events.append({
                            'title': e['title'],
                            'date': d,
                            'description': e.get('description', '')
                        })
                    except:
                        continue
            except:
                pass

        st.success("✓ Done!")

        # --- Calendar Download ---
        if events:
            cal = Calendar()
            cal.add('prodid', '-//SyllabusAI//EN')
            cal.add('version', '2.0')
            for e in events:
                event = Event()
                event.add('summary', e['title'])
                event.add('dtstart', e['date'])
                event.add('dtend', e['date'])
                if e.get('description'):
                    event.add('description', e['description'])
                cal.add_component(event)

            st.download_button(
                label="📅 Download Calendar File (.ics)",
                data=cal.to_ical(),
                file_name="syllabus_calendar.ics",
                mime="text/calendar"
            )
            st.caption(f"Found {len(events)} dates. Open the file to import all events into Google Calendar, Apple Calendar, or Outlook in one click.")

        # --- Display Results ---
        tab1, tab2 = st.tabs(["📄 Formatted View", "⬇️ Download"])

        with tab1:
            st.markdown(result)

        with tab2:
            html_body = markdown.markdown(result, extensions=["tables"])
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SyllabusAI Output</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.6; }}
        h1 {{ color: #1d4ed8; }} h2 {{ color: #1e40af; border-bottom: 2px solid #dbeafe; padding-bottom: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        th {{ background: #1d4ed8; color: white; padding: 10px 14px; text-align: left; }}
        td {{ padding: 10px 14px; border: 1px solid #e2e8f0; vertical-align: top; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
    </style>
</head>
<body>{html_body}</body>
</html>"""

            st.download_button(
                label="⬇️ Download as HTML",
                data=html,
                file_name="syllabus_parsed.html",
                mime="text/html"
            )

            st.download_button(
                label="⬇️ Download as Text",
                data=result,
                file_name="syllabus_parsed.txt",
                mime="text/plain"
            )