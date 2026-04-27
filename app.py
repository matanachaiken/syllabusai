import streamlit as st
import anthropic
import PyPDF2
import markdown
import io

# --- Page Config ---
st.set_page_config(page_title="SyllabusAI", page_icon="📚", layout="centered")

st.title("📚 SyllabusAI")
st.caption("Upload a course syllabus PDF and get a full breakdown of assignments, exams, and a personalized study schedule.")

# --- API Key Input ---
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
        with st.spinner("Sending to Claude... this takes 15-30 seconds"):

            client = anthropic.Anthropic(api_key=api_key)

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

        st.success("✓ Done!")

        # --- Display Results ---
        tab1, tab2 = st.tabs(["📄 Formatted View", "⬇️ Download"])

        with tab1:
            st.markdown(result)

        with tab2:
            # Generate HTML download
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