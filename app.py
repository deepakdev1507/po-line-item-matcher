import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import io
import json
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=st.secrets["openaiKey"])

def check_login(username, password):
    env_username = st.secrets["userName"]
    env_password = st.secrets["password"]
    # print(env_username)
    # print(env_password)
    return username == env_username and password == env_password



def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    return ""

def process_more(invoice_Line, po_line_items):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
        {"role": "system", "content": "Given below are the line items of the invoice: "+str(invoice_Line)},
        {"role": "system", "content": "Given below are the line items of the PO: "+str(po_line_items)},
        {"role": "system", "content": "Your task is to find the line items that are present in the PO. with all the details like quantity,Are there any difference in quantity,what is the difference, unit price, total price, etc. and always respond back in json format"},
        {"role": "system", "content": "mentioning difference in quatity is must, if there is no difference in quantity then mention it as 0."},
        {"role": "system", "content": "give the response in two json objects, one for the line items that are present in the PO and the other for the line items that are not present in the PO."}
    ], 
    response_format={"type": "json_object"},
    temperature=0.1
    )
    return completion.choices[0].message.content


def main():
    # Session state
    if 'login_status' not in st.session_state:
        st.session_state['login_status'] = False

    if st.session_state['login_status']:
        st.title("PDF Text Extractor")

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            text = extract_text_from_pdf(uploaded_file)
            st.write("Below are the details extracted from the PDF")
            st.text_area("Text",findDetails(text), height=250)

            if st.button("Process More"):
                if st.session_state.po_no is not None:
                    result = extract_text_from_file(st.session_state.po_no)
                    if result != "The file was not found.":
                        result = process_more(st.session_state.line_items, result)
                else:
                    result = "No PO number found"
                st.text_area("Text", result, height=250)
                

    else:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if check_login(username, password):
                st.session_state['login_status'] = True
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password")


def findDetails(text):
    # client = OpenAI(os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
        {"role": "system", "content": "Given to you will be details of a invoice in an unstructured manner, your task is to find the PO number, Invoice number, vendor name , vendor address, vendor GSTIN, invoice date, invoice amount and the line items."},
        {"role": "system", "content": "Always respond back in json format with the following keys: PO number, Invoice number, vendor name , vendor address, vendor GSTIN, invoice date, invoice amount and the line items."},
        {"role": "user", "content": text}
    ],
    response_format={"type": "json_object"},
    temperature=0.1
    )

    response = completion.choices[0].message.content
    # print(response)
    response = json.loads(response)
    st.session_state.line_items = response['line items']
    st.session_state.po_no= response['PO number']
    # print(st.session_state.line_items)
    return completion.choices[0].message.content


def extract_text_from_file(file_path):
    file_path = file_path.replace("/", "")
    try:
        with open(file_path+".txt", 'r') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        return "The file was not found."
    except Exception as e:
        return f"An error occurred: {e}"


if __name__ == "__main__":
    main()
