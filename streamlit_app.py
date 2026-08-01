import os
import fitz  # PyMuPDF
import requests
import streamlit as st

# ================= CONFIGURATION =================
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["BOT_TOKEN"]
# =================================================

def pdf_first_page_to_image(pdf_path, output_img_path="first_page.png"):
    """Renders the first page of a PDF to a PNG image using PyMuPDF."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)  # Page index starts at 0
    
    # Render page to high-res image
    matrix = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=matrix)
    pix.save(output_img_path)
    doc.close()
    
    return output_img_path

def send_photo_to_telegram(bot_token, chat_id, photo_path, caption=None):
    """Sends a photo to a Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(photo_path, "rb") as photo_file:
        files = {"photo": photo_file}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        return response.json()

def send_document_to_telegram(bot_token, chat_id, doc_path, caption=None, filename=None):
    """Sends a document (PDF) to a Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(doc_path, "rb") as doc_file:
        files = {"document": (filename, doc_file)} if filename else {"document": doc_file}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        return response.json()

def main():
    st.set_page_config(page_title="PDF to Telegram Uploader", page_icon="📄")
    st.title("Upload PDF to Telegram")
    st.write("Upload PDF files below to send their first pages as images and the original documents to your Telegram group.")

    uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True)

    AVAILABLE_TAGS = [
        "Programming Language", "Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "TypeScript",
        "Web Development", "React", "Angular", "Vue", "Node.js", "Django", "Flask",
        "Spring", "Spring Boot",
        "Data Science", "Machine Learning", "AIML",
        "Mobile Development", "Android", "iOS", "Flutter", "React Native",
        "DevOps", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
        "Database", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL",
        "Cheat Sheets", "Interview Prep", "System Design", "Algorithms", "Data Structures"
    ]

    if uploaded_files:
        apply_same_tags = st.checkbox("Apply same tags to all files", value=True)
        
        file_tags = {}
        
        if apply_same_tags:
            selected_tags = st.multiselect("Select Tags for all files", AVAILABLE_TAGS)
            custom_tags_input = st.text_input("Add custom tags for all files (comma-separated)")
            
            all_tags = list(selected_tags) if selected_tags else []
            if custom_tags_input:
                custom_tags = [t.strip() for t in custom_tags_input.split(',') if t.strip()]
                all_tags.extend(custom_tags)
                
            formatted_tags = " ".join([f"#{tag.replace(' ', '')}" for tag in all_tags]) if all_tags else None
            
            for f in uploaded_files:
                file_tags[f.name] = formatted_tags
        else:
            for i, f in enumerate(uploaded_files):
                st.subheader(f"Tags for: {f.name}")
                selected_tags = st.multiselect(f"Select Tags for {f.name}", AVAILABLE_TAGS, key=f"sel_{i}")
                custom_tags_input = st.text_input(f"Add custom tags for {f.name} (comma-separated)", key=f"cust_{i}")
                
                all_tags = list(selected_tags) if selected_tags else []
                if custom_tags_input:
                    custom_tags = [t.strip() for t in custom_tags_input.split(',') if t.strip()]
                    all_tags.extend(custom_tags)
                    
                formatted_tags = " ".join([f"#{tag.replace(' ', '')}" for tag in all_tags]) if all_tags else None
                file_tags[f.name] = formatted_tags

        if st.button("Send to Telegram"):
            with st.spinner("Processing and sending..."):
                for uploaded_file in uploaded_files:
                    # Save uploaded file temporarily
                    temp_pdf_path = f"temp_{uploaded_file.name}"
                    with open(temp_pdf_path, "wb") as f_out:
                        f_out.write(uploaded_file.getbuffer())

                    img_path = f"temp_first_page_{uploaded_file.name}.png"
                    
                    try:
                        # 1. Render first page
                        pdf_first_page_to_image(temp_pdf_path, img_path)

                        # 2. Sending image preview to Telegram with file name as caption
                        send_photo_to_telegram(
                            BOT_TOKEN, 
                            CHAT_ID, 
                            img_path, 
                            caption=uploaded_file.name
                        )

                        # 3. Uploading actual PDF file with tag caption
                        send_document_to_telegram(
                            BOT_TOKEN, 
                            CHAT_ID, 
                            temp_pdf_path, 
                            caption=file_tags[uploaded_file.name],
                            filename=uploaded_file.name
                        )

                        st.success(f"Successfully sent **{uploaded_file.name}** to Telegram!")

                    except Exception as e:
                        st.error(f"An error occurred while sending {uploaded_file.name}: {e}")

                    finally:
                        # Cleanup temporary files
                        if os.path.exists(temp_pdf_path):
                            os.remove(temp_pdf_path)
                        if os.path.exists(img_path):
                            os.remove(img_path)

if __name__ == "__main__":
    main()