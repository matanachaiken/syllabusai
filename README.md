## SyllabusAI
An AI-powered syllabus parser that extracts deadlines, assignments, and exam dates from course PDFs and generates a personalized study schedule — built with Claude API and deployed as a Streamlit web app.

Live App: [syllabusai-kqkowl6c2jnaeign3tpksh.streamlit.app](https://syllabusai-kqkowl6c2jnaeign3tpksh.streamlit.app/)**

## What It Does:
- Upload any course syllabus PDF
- Extracts all assignments, due dates, exam dates, and weekly reading schedule
- Generates a personalized study schedule with week-by-week goals
- Exports all deadlines directly to Google Calendar, Apple Calendar, or Outlook via `.ics` file
- Downloads a clean, formatted HTML report

## Built With
- [Claude API](https://anthropic.com) — LLM-based extraction and study schedule generation
- [Streamlit](https://streamlit.io) — Web interface and deployment
- [PyPDF2](https://pypdf2.readthedocs.io) — PDF text extraction
- [icalendar](https://icalendar.readthedocs.io) — Google Calendar `.ics` export
- Python, Markdown

## How It Works
1. PyPDF2 extracts raw text from the uploaded PDF
2. The text is sent to Claude with a structured prompt to extract course info, assignments, exam dates, and weekly schedule
3. A second Claude call extracts all specific dates and formats them as calendar events
4. Results are displayed in the app and available for download as HTML or `.ics`
