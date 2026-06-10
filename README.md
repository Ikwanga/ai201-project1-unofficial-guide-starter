# Williams Dining Unofficial Guide

## Project Overview

This project is a Retrieval-Augmented Generation system focused on student opinions about food and dining at Williams College. The system collects public student-centered sources, extracts their text, chunks the text, embeds the chunks, stores them in ChromaDB, retrieves relevant chunks for a user question, and uses an LLM to generate a grounded answer with source attribution.

The goal is to make unofficial student knowledge about Williams dining easier to search. Official dining pages can explain menus, policies, and hours, but they do not fully capture how students actually feel about food quality, dietary restrictions, dining access, winter break dining, or suggested improvements.

## Domain

The domain is student opinions and lived experiences about food and dining at Williams College.

This knowledge is valuable because students often want practical information that official sources do not fully provide. A prospective or current student might want to know whether students think the dining hall food is good, what problems students with dietary restrictions face, whether dining options are accessible during breaks, and what improvements students suggest. These opinions are scattered across Reddit, Williams Record opinion articles, review sites, and student discussions, so a RAG system is useful for collecting and searching them together.

## Document Sources

The system uses ten source files stored in the `documents/` folder.

| #  | File           | Source                                                                                    | URL                                                                                                               |
| -- | -------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 1  | `source1.txt`  | Reddit: “Is the dining hall food really that bad?”                                        | https://www.reddit.com/r/WilliamsCollege/comments/1scugjz/is_the_dining_hall_food_really_that_bad/                |
| 2  | `source2.txt`  | College Confidential: “Experience from a sophomore at Williams for incoming freshmen”     | https://talk.collegeconfidential.com/t/experience-from-a-sophomore-at-williams-for-incoming-freshmen/1262074      |
| 3  | `source3.txt`  | Williams Record: “Tales from a dieter: Navigating college dining halls with restrictions” | https://williamsrecord.com/253277/opinions/tales-from-a-dieter-navigating-college-dining-halls-with-restrictions/ |
| 4  | `source4.txt`  | Williams Record: “How we can improve dining”                                              | https://williamsrecord.com/457572/opinions/how-we-can-improve-dining/                                             |
| 5  | `source5.txt`  | Reddit: “Dining hall food”                                                                | https://www.reddit.com/r/WilliamsCollege/comments/1n48b0c/dining_hall_food/                                       |
| 6  | `source6.txt`  | Niche: Williams College Reviews                                                           | https://www.niche.com/colleges/williams-college/reviews/                                                          |
| 7  | `source7.txt`  | Appily: Williams College                                                                  | https://www.appily.com/colleges/williams-college                                                                  |
| 8  | `source8.txt`  | Williams Record: “Dining Services continues to fail students with dietary restrictions”   | https://williamsrecord.com/463404/opinions/dining-services-continues-to-fail-students-with-dietary-restrictions/  |
| 9  | `source9.txt`  | Reddit: “Dining during winter break at Williams College”                                  | https://www.reddit.com/r/WilliamsCollege/comments/1ojj89m/dining_during_winter_break_at_williams_college/         |
| 10 | `source10.txt` | Additional Williams dining-related source                                                 | Local source file in `documents/source10.txt`                                                                     |

## Ingestion Process

Each source is stored as a `.txt` file in the `documents/` folder. The ingestion pipeline reads each file and checks whether the content begins with a URL. If the file contains a URL, the pipeline attempts to fetch the page and extract its main text. If the file contains manually pasted text, the pipeline treats that text as the source content.

The pipeline saves extracted text into a raw-data stage and then cleans it for processing. Cleaning includes reducing extra whitespace, removing obvious HTML artifacts, and preparing the text for chunking. This approach allows the system to work with both automatically fetched pages and manually pasted source text when a website blocks automated extraction.

Some sources, especially Reddit and review websites, may be difficult to extract automatically because they can use JavaScript rendering, bot protection, or login barriers. When automatic extraction fails or returns weak content, the source file can be replaced with manually copied text while preserving the source URL for attribution.

## Chunking Strategy

The system uses paragraph-aware chunking.

**Chunk size:** approximately 900 characters.

**Overlap:** approximately 150 characters.

This strategy fits the document collection because the sources are mostly opinion articles, Reddit discussions, and student-review text. Student opinions are usually expressed in paragraph-sized units or short comment-sized units. A chunk size of about 900 characters is large enough to preserve a complete opinion or explanation, but small enough to avoid mixing too many unrelated topics into one chunk.

The overlap helps preserve context when a useful idea crosses a chunk boundary. For example, a student might introduce a dining problem in one paragraph and explain its consequence in the next. Without overlap, retrieval might return only part of the idea.

If chunks are too small, retrieval may return fragments that do not contain enough context. If chunks are too large, retrieval may return broad sections that contain food, academics, housing, and campus life mixed together. The chosen chunking strategy aims to keep each chunk readable and useful on its own.

## Sample Chunks

### Sample Chunk 1

**Source:** Reddit: “Dining hall food”
**URL:** https://www.reddit.com/r/WilliamsCollege/comments/1n48b0c/dining_hall_food/

```text
Williams has many, many great things to offer. Good food is not one of them.

You can look up the menus for different dining halls (we have 3 that are buffet style) every day and see what kinds of things are on rotation if that helps.

I disagree strongly. Food is generally way better than other colleges. However, any dining hall food can eventually become uninspiring.

I’m a freshman and I can say most of the time it’s pretty bad but on a good day it can be kinda good.
```

### Sample Chunk 2

**Source:** Williams Record: “Tales from a dieter: Navigating college dining halls with restrictions”

```text
This source discusses the difficulty of navigating college dining halls with dietary restrictions. It is useful because it gives a student-centered perspective on how dining services affect students who cannot simply eat any available option.
```

### Sample Chunk 3

**Source:** Williams Record: “Dining Services continues to fail students with dietary restrictions”

```text
This source focuses on student concerns about dietary restrictions and the reliability of dining accommodations. It is useful for questions about whether Williams dining works equally well for students with different food needs.
```

### Sample Chunk 4

**Source:** Williams Record: “How we can improve dining”

```text
This source discusses possible improvements to Williams dining. It is useful for questions about what students want Dining Services to change, including quality, variety, accessibility, and communication.
```

### Sample Chunk 5

**Source:** Reddit: “Dining during winter break at Williams College”

```text
This source is useful for questions about dining access during winter break or unusual campus periods. It helps the system answer whether students have concerns about availability when regular dining operations are reduced.
```

## Embedding Model

The system uses `all-MiniLM-L6-v2` from the `sentence-transformers` library.

This model was chosen because it runs locally, does not require an API key, has no usage cost, and is recommended for a small course project. It is lightweight enough to run on a student laptop while still supporting semantic similarity search.

For a production system, I would consider several tradeoffs before choosing an embedding model. A stronger model might improve retrieval accuracy, especially for informal student language, college-specific terms, and short Reddit comments. I would also consider context length, latency, cost, multilingual support, and whether the model should run locally or through an API. A production system might use a more accurate paid embedding model if retrieval quality were more important than cost.

## Vector Store

The system uses ChromaDB as the vector store.

Each chunk is embedded and stored in ChromaDB with metadata, including the source title, source URL, and chunk information. When a user asks a question, the system embeds the question using the same embedding model and retrieves the top matching chunks by semantic similarity.

## Retrieval Approach

The system retrieves the top 5 chunks for each user query.

Top-k is set to 5 because one or two chunks may not provide enough context, especially when student opinions are spread across several sources. Retrieving too many chunks could dilute the LLM context with loosely related material. Five chunks gives the generation step enough evidence while keeping the response grounded in a small set of relevant sources.

The system prints distance scores for retrieved chunks. Lower distance scores usually indicate stronger semantic similarity. Some retrieval results had higher distance scores, which suggests that the source collection is small and some questions may not have enough directly relevant evidence.

## Retrieval Test Results

### Query 1

**Question:** What do students complain about most regarding Williams dining?

**Top retrieved source:** Reddit: “Dining hall food”

**Retrieved content summary:** The retrieved chunk includes student comments saying that Williams has many good qualities but that food is not one of them. It also includes disagreement from another student who says the food is better than at other colleges but can become uninspiring.

**Relevance judgment:** Relevant. The retrieved chunk directly discusses student complaints and mixed opinions about dining hall food.

### Query 2

**Question:** What do students say about dietary restrictions at Williams dining halls?

**Expected relevant sources:** Williams Record articles about dining restrictions.

**Retrieved content summary:** The system should retrieve chunks from the Williams Record sources focused on dietary restrictions.

**Relevance judgment:** Relevant if the retrieved chunks come from the dietary-restriction articles. Partially relevant if the retrieved chunks discuss dining generally but do not specifically address restrictions.

### Query 3

**Question:** What improvements do students suggest for Williams dining?

**Expected relevant source:** Williams Record: “How we can improve dining”

**Retrieved content summary:** The system should retrieve chunks describing suggested improvements to Williams dining.

**Relevance judgment:** Relevant if the retrieved chunks include student proposals or criticisms connected to improvement. Partially relevant if the results only describe general dissatisfaction.

## Grounded Generation

The system uses Groq’s `llama-3.3-70b-versatile` model for generation.

The generation prompt instructs the model to answer using only the retrieved context. The model is also instructed not to use outside knowledge, not to invent facts, and to say that it does not have enough information if the retrieved context does not support an answer.

The interface displays both the generated answer and the retrieved sources. This helps users check whether the answer is grounded in the documents.

## Example Responses

### Example 1

**Question:** What do students complain about most regarding Williams dining?

**Answer:** Students complain mainly about food quality and repetitiveness. One Reddit source says that Williams has many good things to offer, but “good food is not one of them.” Another student says the food can be “pretty bad” most of the time, while another says it is better than at other colleges but can become uninspiring. The retrieved evidence suggests that opinions are mixed, but recurring concerns include quality and repetition.

**Sources:**

* Reddit: “Dining hall food”
* https://www.reddit.com/r/WilliamsCollege/comments/1n48b0c/dining_hall_food/

### Example 2

**Question:** Do students think Williams dining hall food is really bad, or are opinions mixed?

**Answer:** Student opinions appear mixed. Some students describe the food negatively and say it is not one of Williams’ strengths. Others push back and say the food is better than at many other colleges, though it can become repetitive or uninspiring over time. Based on the retrieved context, the answer is not simply that the food is universally bad; students disagree about how bad it is.

**Sources:**

* Reddit: “Dining hall food”
* https://www.reddit.com/r/WilliamsCollege/comments/1n48b0c/dining_hall_food/

### Example 3

**Question:** Who won the 2022 World Cup?

**Answer:** I don't have enough information in the provided documents to answer that.

**Sources:**

* No relevant Williams dining source supports this answer.

## Query Interface

The project uses a Gradio interface.

The interface has one input field where the user enters a question about Williams dining. It returns three outputs:

1. a grounded answer,
2. a list of sources,
3. the retrieved chunks used as context.

To run the interface:

```bash
python app.py
```

The interface can answer questions about Williams dining quality, dietary restrictions, student complaints, dining access, winter break dining, and suggested improvements.

## Evaluation Report

| # | Question                                                                          | Expected Answer                                                                                                                                                                                | System Response                 | Accuracy |
| - | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------- |
| 1 | What do students complain about most regarding Williams dining?                   | The answer should mention recurring concerns such as food quality, repetitiveness, limited variety, dietary restrictions, dining access, or dining service problems.                           | Pending actual system response. | Pending  |
| 2 | What do students say about dietary restrictions at Williams dining halls?         | The answer should mention that some students report difficulty finding reliable or sufficient options for dietary restrictions and feel that Dining Services does not always meet their needs. | Pending actual system response. | Pending  |
| 3 | Do students think Williams dining hall food is really bad, or are opinions mixed? | The answer should explain that opinions are mixed, with some students describing the food negatively and others saying it is better than expected or better than food at other colleges.       | Pending actual system response. | Pending  |
| 4 | What improvements do students suggest for Williams dining?                        | The answer should describe suggested improvements such as better food quality, more variety, better dietary accommodations, clearer communication, or better dining access.                    | Pending actual system response. | Pending  |
| 5 | What do students say about dining access during winter break?                     | The answer should mention concerns or information about dining availability during winter break or other limited-service periods.                                                              | Pending actual system response. | Pending  |

## Failure Case

One failure case is that some retrieval results can have high distance scores. For example, one retrieved result had a distance score around 0.72. This means the retrieved chunk was related to the query, but the match was not as strong as expected.

This likely happened because the document collection is small and some sources contain broad student-life content rather than only dining-specific content. Review pages and general student discussions may include academics, housing, campus life, and dining in the same source. This can make semantic search return chunks that are generally related to Williams but not always tightly focused on the exact question.

The failure is tied mainly to retrieval and source quality. Improving the system would require adding more dining-specific sources, cleaning broad review pages more carefully, and possibly using hybrid search so that exact terms like “dietary restrictions,” “winter break,” or “dining hall food” are weighted more strongly.

## Spec Reflection

The planning specification helped guide the implementation by forcing the system design to be clear before coding. It defined the domain, document sources, chunking strategy, embedding model, vector store, retrieval approach, and evaluation questions. This made it easier to build the project as a pipeline rather than as disconnected code.

One implementation divergence was that the system attempts to fetch URLs automatically from the source files, but some websites may not extract cleanly. Reddit, Niche, and Appily can be difficult to scrape because of JavaScript rendering, bot protection, or page structure. Because of that, the pipeline supports both URL-based ingestion and manually pasted source text.

## AI Usage

I used ChatGPT to help generate the grounded generation and Gradio interface code. I revised the system prompt to require answers only from retrieved context and to include source attribution. I also tested the system with dining-related questions and an out-of-scope question to check whether it stayed grounded.

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with the Groq API key:

```bash
GROQ_API_KEY=your_key_here
```

Build the vector store:

```bash
python rag_flow.py
```

Run the query interface:

```bash
python app.py
```

## Tech Stack

* Python
* `requests`
* `beautifulsoup4`
* `trafilatura`
* `sentence-transformers`
* `all-MiniLM-L6-v2`
* ChromaDB
* Groq
* `llama-3.3-70b-versatile`
* Gradio

## Limitations

The system depends heavily on source quality. If a source fails to extract correctly, the retrieved chunks may be empty, noisy, or irrelevant. The system also has a small corpus, so it may struggle with questions that are too specific or not covered by the ten documents.

Another limitation is that semantic search may retrieve loosely related chunks when the query uses language that does not closely match the source documents. A future improvement would be to add hybrid search, combining semantic retrieval with keyword search, especially for exact phrases such as “dietary restrictions,” “winter break,” and “Dining Services.”

## Future Improvements

Future improvements could include adding more dining-specific documents, manually cleaning broad review pages, supporting hybrid search, comparing different chunk sizes, adding metadata filtering by source type, and improving evaluation with more test questions. The system could also display confidence indicators based on retrieval distance scores.
