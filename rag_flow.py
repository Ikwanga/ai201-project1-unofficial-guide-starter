import os
import re
import json
from io import BytesIO
from urllib.parse import urlparse

import requests
import pdfplumber
import trafilatura
from bs4 import BeautifulSoup
import chromadb
from sentence_transformers import SentenceTransformer


DOCUMENTS_DIR = "documents"
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "williams_dining"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def ensure_dirs():
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def clean_text(text):
    if not text:
        return ""

    text = text.replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def read_source_files():
    """
    Reads documents/source1.txt, source2.txt, etc.

    Each source file can contain either:
    1. a URL, or
    2. manually pasted text.

    If it starts with http:// or https://, the pipeline treats it as a link.
    Otherwise, it treats the file content as already-collected text.
    """
    sources = []

    for filename in sorted(os.listdir(DOCUMENTS_DIR)):
        if not filename.lower().endswith(".txt"):
            continue

        path = os.path.join(DOCUMENTS_DIR, filename)

        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read().strip()

        if not content:
            print(f"Skipping empty file: {filename}")
            continue

        first_line = content.splitlines()[0].strip()

        if first_line.startswith("http://") or first_line.startswith("https://"):
            sources.append({
                "source_file": filename,
                "kind": "url",
                "url": first_line,
                "manual_text": None
            })
        else:
            sources.append({
                "source_file": filename,
                "kind": "manual_text",
                "url": None,
                "manual_text": content
            })

    return sources


def fetch_url(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text, response.content, response.headers.get("content-type", "")


def is_pdf_url(url, content_type):
    return url.lower().endswith(".pdf") or "application/pdf" in content_type.lower()


def extract_pdf_text(pdf_bytes):
    pages = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)

    return "\n\n".join(pages)


def reddit_json_url(url):
    """
    Converts a Reddit post URL into its JSON endpoint.
    """
    url = url.split("?")[0].rstrip("/")
    return url + ".json"


def flatten_reddit_comments(comment_node, comments):
    """
    Recursively extracts Reddit comment text from Reddit JSON.
    """
    if not isinstance(comment_node, dict):
        return

    data = comment_node.get("data", {})
    body = data.get("body")

    if body:
        comments.append(body)

    replies = data.get("replies")

    if isinstance(replies, dict):
        children = replies.get("data", {}).get("children", [])

        for child in children:
            flatten_reddit_comments(child, comments)


def extract_reddit_text(url):
    """
    Tries to extract Reddit post and comments using Reddit's JSON endpoint.
    This may fail if Reddit blocks the request.
    """
    json_url = reddit_json_url(url)

    response = requests.get(json_url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or len(data) < 1:
        return ""

    parts = []

    post_listing = data[0]
    post_children = post_listing.get("data", {}).get("children", [])

    if post_children:
        post_data = post_children[0].get("data", {})
        title = post_data.get("title", "")
        selftext = post_data.get("selftext", "")

        if title:
            parts.append(f"Title: {title}")

        if selftext:
            parts.append(f"Post: {selftext}")

    if len(data) > 1:
        comments_listing = data[1]
        comment_children = comments_listing.get("data", {}).get("children", [])

        comments = []
        for child in comment_children:
            flatten_reddit_comments(child, comments)

        if comments:
            parts.append("Comments:")
            for i, comment in enumerate(comments, start=1):
                parts.append(f"Comment {i}: {comment}")

    return "\n\n".join(parts)


def extract_html_text(html, url):
    """
    Uses trafilatura first because it is designed to extract main article text.
    Falls back to BeautifulSoup if trafilatura returns little or nothing.
    """
    extracted = trafilatura.extract(
        html,
        url=url,
        include_comments=True,
        include_tables=True,
        favor_recall=True
    )

    if extracted and len(extracted.strip()) > 300:
        return extracted

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 0:
            lines.append(line)

    return "\n".join(lines)


def extract_from_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if "reddit.com" in domain:
        try:
            text = extract_reddit_text(url)
            if len(text.strip()) > 200:
                return text
        except Exception as error:
            print(f"Reddit JSON extraction failed for {url}: {error}")
            print("Trying regular webpage extraction instead...")

    html, content_bytes, content_type = fetch_url(url)

    if is_pdf_url(url, content_type):
        return extract_pdf_text(content_bytes)

    return extract_html_text(html, url)


def load_or_fetch_documents():
    """
    Main ingestion step.

    It reads the source files, fetches URLs when needed,
    saves raw extracted text, cleans it, and returns structured documents.
    """
    ensure_dirs()

    sources = read_source_files()
    documents = []

    for source in sources:
        source_file = source["source_file"]
        base_name = os.path.splitext(source_file)[0]

        print(f"\nProcessing {source_file}...")

        try:
            if source["kind"] == "url":
                url = source["url"]
                extracted_text = extract_from_url(url)
                source_label = url
            else:
                extracted_text = source["manual_text"]
                source_label = source_file

            raw_path = os.path.join(RAW_DIR, f"{base_name}_raw.txt")
            processed_path = os.path.join(PROCESSED_DIR, f"{base_name}_clean.txt")

            with open(raw_path, "w", encoding="utf-8") as file:
                file.write(extracted_text or "")

            cleaned_text = clean_text(extracted_text)

            with open(processed_path, "w", encoding="utf-8") as file:
                file.write(cleaned_text)

            if len(cleaned_text) < 200:
                print(f"WARNING: Very little text extracted from {source_file}.")
                print("You may need to manually paste this source's content into the file.")

            documents.append({
                "source_file": source_file,
                "source_label": source_label,
                "text": cleaned_text
            })

            print(f"Extracted {len(cleaned_text)} characters.")

        except Exception as error:
            print(f"FAILED to process {source_file}: {error}")
            print("Manually paste the webpage text into this source file if needed.")

    return documents


def chunk_text(text, chunk_size=900, overlap=150):
    """
    Paragraph-aware chunking.

    We first split by paragraphs, then combine paragraphs until we reach
    about 900 characters. The overlap preserves context between chunks.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_size:
            current = (current + "\n" + paragraph).strip()
        else:
            if current:
                chunks.append(current)

            if overlap > 0 and current:
                current = current[-overlap:] + "\n" + paragraph
            else:
                current = paragraph

    if current:
        chunks.append(current)

    return chunks


def build_chunks():
    documents = load_or_fetch_documents()
    all_chunks = []

    for doc in documents:
        chunks = chunk_text(doc["text"])

        for index, chunk in enumerate(chunks):
            if len(chunk.strip()) < 80:
                continue

            all_chunks.append({
                "id": f"{doc['source_file']}_chunk_{index}",
                "text": chunk,
                "source_file": doc["source_file"],
                "source_label": doc["source_label"],
                "chunk_index": index
            })

    return all_chunks


def build_vector_store():
    chunks = build_chunks()

    print("\n==============================")
    print(f"Total chunks created: {len(chunks)}")

    if len(chunks) == 0:
        raise ValueError(
            "No chunks were created. Check that your source files contain valid URLs "
            "or pasted text."
        )

    print("\nFive sample chunks:")
    for chunk in chunks[:5]:
        print("\n---")
        print("Source file:", chunk["source_file"])
        print("Source label:", chunk["source_label"])
        print(chunk["text"][:700])

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source_file": chunk["source_file"],
                "source_label": chunk["source_label"],
                "chunk_index": chunk["chunk_index"]
            }
            for chunk in chunks
        ]
    )

    print(f"\nStored {len(chunks)} chunks in ChromaDB.")


def retrieve(query, k=5):
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode([query]).tolist()[0]

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    retrieved = []

    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "text": doc,
            "source_file": metadata["source_file"],
            "source_label": metadata["source_label"],
            "chunk_index": metadata["chunk_index"],
            "distance": distance
        })

    return retrieved


if __name__ == "__main__":
    build_vector_store()

    test_queries = [
        "What do students complain about most regarding Williams dining?",
        "What positive things do students say about Williams dining?",
        "What do students say about dietary restrictions?",
        "What do students say about dining during winter break?",
        "What improvements do students suggest for Williams dining?"
    ]

    for query in test_queries:
        print("\n==============================")
        print("QUERY:", query)

        results = retrieve(query, k=5)

        for result in results:
            print("\nSource file:", result["source_file"])
            print("Source label:", result["source_label"])
            print("Chunk:", result["chunk_index"])
            print("Distance:", result["distance"])
            print(result["text"][:700])