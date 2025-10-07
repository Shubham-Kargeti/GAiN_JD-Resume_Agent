import streamlit as st
import requests

st.title("Upload JD and Resume to Check Compatibility")

# File uploaders
file_a = st.file_uploader("Upload the Job Description", type=["pdf", "docx"], key="file_a")
file_b = st.file_uploader("Upload the Resume", type=["pdf", "docx"], key="file_b")

# Upload buttons
col1, col2 = st.columns(2)

with col1:
    if file_a:
        res = requests.post(
            "http://localhost:8000/jd/upload/",
            files={"file": (file_a.name, file_a, file_a.type)}
        )
        if res.status_code == 200:
            st.success(res.json()["info"])
        else:
            st.error(res.json().get("detail", "Failed to upload JD."))

with col2:
    if file_b:
        res = requests.post(
            "http://localhost:8000/resume/upload/",
            files={"file": (file_b.name, file_b, file_b.type)}
        )
        if res.status_code == 200:
            st.success(res.json()["info"])
        else:
            st.error(res.json().get("detail", "Failed to upload Resume."))

# Separator
st.markdown("---")

# Process files
if st.button("Process files"):
    res = requests.get("http://localhost:8000/process/process/")
    if res.status_code == 200:
        st.subheader("Resume Compatibility Output:")
        st.text_area("Output", res.json()["combined_text"], height=400)
    else:
        st.error("Unknown error occurred while processing.")
