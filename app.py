import gradio as gr
from query import ask


def handle_query(question):
    if not question.strip():
        return "Please enter a question.", "", ""

    result = ask(question)

    answer = result["answer"]

    sources = "\n".join(f"• {source}" for source in result["sources"])

    retrieved_chunks = ""

    for chunk in result["chunks"]:
        content = chunk.get("content", chunk.get("text", ""))

        retrieved_chunks += (
            "\n---\n"
            f"Distance: {chunk.get('distance')}\n"
            f"Title: {chunk.get('title')}\n"
            f"URL: {chunk.get('source_url')}\n"
            f"Content:\n{content[:900]}\n"
        )

    return answer, sources, retrieved_chunks


with gr.Blocks() as demo:
    gr.Markdown("# Williams Dining Unofficial Guide")
    gr.Markdown(
        "Ask questions about student opinions on Williams College food, dining halls, "
        "dietary restrictions, dining access, and suggested improvements."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="Example: What do students complain about most regarding Williams dining?"
    )

    ask_button = gr.Button("Ask")

    answer = gr.Textbox(label="Grounded Answer", lines=8)
    sources = gr.Textbox(label="Sources", lines=6)
    chunks = gr.Textbox(label="Retrieved Chunks", lines=14)

    ask_button.click(
        handle_query,
        inputs=question,
        outputs=[answer, sources, chunks]
    )

    question.submit(
        handle_query,
        inputs=question,
        outputs=[answer, sources, chunks]
    )


demo.launch()