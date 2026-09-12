import fitz
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean_text(text):
    text=re.sub(r"\s+"," ",text)
    text=re.sub(r"Page\s+\d+\s+of\s+\d+","",text,flags=re.IGNORECASE)
    return text.strip()


def extract_pages(pdf_file):
    document=fitz.open(stream=pdf_file.read(),filetype="pdf")
    pages=[]

    for page_number,page in enumerate(document,start=1):
        text=page.get_text("text")
        text=clean_text(text)

        pages.append({
            "page":page_number,
            "text":text
        })

    document.close()
    return pages


def create_chunks(pages,chunk_size=1200,overlap=200):
    chunks=[]

    for page_data in pages:
        text=page_data["text"]
        page_number=page_data["page"]

        start=0

        while start<len(text):
            end=start+chunk_size
            chunk_text=text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text":chunk_text,
                    "page":page_number
                })

            start+=chunk_size-overlap

    return chunks


def add_document_name(chunks,document_name):
    for chunk in chunks:
        chunk["document"]=document_name

    return chunks


def process_document(pdf_file,document_name):
    pages=extract_pages(pdf_file)
    chunks=create_chunks(pages)
    chunks=add_document_name(chunks,document_name)

    return {
        "document_name":document_name,
        "pages":pages,
        "chunks":chunks
    }


def retrieve_evidence(query,chunks,top_k=5):
    if not chunks:
        return []

    documents=[chunk["text"] for chunk in chunks]

    vectorizer=TfidfVectorizer(stop_words="english")
    matrix=vectorizer.fit_transform(documents+[query])

    scores=cosine_similarity(matrix[-1],matrix[:-1]).flatten()
    ranked_indexes=scores.argsort()[::-1][:top_k]

    evidence=[]

    for index in ranked_indexes:
        if scores[index]<=0:
            continue

        evidence.append({
            "text":chunks[index]["text"],
            "page":chunks[index]["page"],
            "document":chunks[index]["document"],
            "score":round(float(scores[index]),4)
        })

    return evidence