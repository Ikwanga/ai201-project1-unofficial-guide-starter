import os
from dotenv import load_dotenv
from groq import Groq

from rag_flow import retrieve


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)


def format_context(chunks):
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        source_url = chunk.get("source_url", "Unknown source")
        title = chunk.get("title", "Unknown title")
        content = chunk.get("content", chunk.get("text", ""))

        context_parts.append(
            f"[Source {i}]\n"
            f"Title: {title}\n"
            f"URL: {source_url}\n"
            f"Content:\n{content}"
        )

    return "\n\n".join(context_parts)


def ask(question, k=5):
    retrieved_chunks = retrieve(question, k=k)
    context = format_context(retrieved_chunks)

    prompt = f"""
You are a grounded RAG assistant for an unofficial guide to Williams College dining.

Answer the user's question using ONLY the provided retrieved context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the retrieved context does not contain enough information, say:
   "I don't have enough information in the provided documents to answer that."
4. Cite the source title or URL when you use information from it.
5. Be concise but specific.

Retrieved context:
{context}

User question:
{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You answer only from retrieved context and cite the provided sources."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    sources = []
    for chunk in retrieved_chunks:
        source_url = chunk.get("source_url", "Unknown source")
        title = chunk.get("title", "Unknown title")
        source_text = f"{title} — {source_url}"

        if source_text not in sources:
            sources.append(source_text)

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "chunks": retrieved_chunks
    }


if __name__ == "__main__":
    question = input("Ask a question: ")
    result = ask(question)

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print("-", source)

    print("\nRETRIEVED CHUNKS:")
    for chunk in result["chunks"]:
        print("\n---")
        print("Distance:", chunk.get("distance"))
        print("Title:", chunk.get("title"))
        print("URL:", chunk.get("source_url"))
        print(chunk.get("content", chunk.get("text", ""))[:700])