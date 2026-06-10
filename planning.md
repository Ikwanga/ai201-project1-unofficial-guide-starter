# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

My project focuses on student opinions and lived experiences about food and dining at Williams College. This knowledge is valuable because official Williams Dining pages can explain menus, meal plans, and policies, but they do not fully capture how students actually experience dining on campus. Students often want practical, informal information: whether the food is considered good or bad, what problems students with dietary restrictions face, how dining changes affect daily life, what students complain about, and what improvements students suggest.

This knowledge is hard to find through official channels because it is scattered across Reddit threads, Williams Record opinion articles, college review sites, and student discussions. My RAG system will collect these scattered sources and make them searchable through plain-language questions.

---

## Documents

| #  | Source                                                                                    | Description                                                                                                                                                           | URL or location                                                                                                                             |
| -- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | Reddit: “Is the dining hall food really that bad?”                                        | Student discussion about whether Williams dining hall food is actually poor or whether complaints are exaggerated. Useful for general positive and negative opinions. | `documents/source1.txt` — https://www.reddit.com/r/WilliamsCollege/comments/1scugjz/is_the_dining_hall_food_really_that_bad/                |
| 2  | College Confidential: “Experience from a sophomore at Williams for incoming freshmen”     | Student perspective for incoming students, potentially including dining, campus life, and practical student experiences.                                              | `documents/source2.txt` — https://talk.collegeconfidential.com/t/experience-from-a-sophomore-at-williams-for-incoming-freshmen/1262074      |
| 3  | Williams Record: “Tales from a dieter: Navigating college dining halls with restrictions” | Opinion article about dining with dietary restrictions. Useful for questions about accessibility, restrictions, and student frustration.                              | `documents/source3.txt` — https://williamsrecord.com/253277/opinions/tales-from-a-dieter-navigating-college-dining-halls-with-restrictions/ |
| 4  | Williams Record: “How we can improve dining”                                              | Opinion article proposing improvements to Williams Dining. Useful for questions about student complaints and suggested reforms.                                       | `documents/source4.txt` — https://williamsrecord.com/457572/opinions/how-we-can-improve-dining/                                             |
| 5  | Reddit: “Dining hall food”                                                                | Student discussion specifically about dining hall food. Useful for informal student judgments of food quality, variety, and expectations.                             | `documents/source5.txt` — https://www.reddit.com/r/WilliamsCollege/comments/1n48b0c/dining_hall_food/                                       |
| 6  | Niche: Williams College Reviews                                                           | Review page that may include student comments about campus life, food, dorms, and general experience. Useful as a broader student-review source.                      | `documents/source6.txt` — https://www.niche.com/colleges/williams-college/reviews/                                                          |
| 7  | Appily: Williams College                                                                  | College profile/review source that may include student experience information, including campus life and dining-related comments.                                     | `documents/source7.txt` — https://www.appily.com/colleges/williams-college                                                                  |
| 8  | Williams Record: “Dining Services continues to fail students with dietary restrictions”   | Opinion article focused on problems faced by students with dietary restrictions. Useful for questions about accessibility and repeated dining failures.               | `documents/source8.txt` — https://williamsrecord.com/463404/opinions/dining-services-continues-to-fail-students-with-dietary-restrictions/  |
| 9  | Reddit: “Dining during winter break at Williams College”                                  | Student discussion about dining availability during winter break. Useful for questions about dining access outside the regular semester.                              | `documents/source9.txt` — https://www.reddit.com/r/WilliamsCollege/comments/1ojj89m/dining_during_winter_break_at_williams_college/         |
| 10 | Additional dining source                                                                  | Additional source related to Williams dining, student food opinions, dining policy, dining access, or a PDF/source used to complete the 10-document requirement.      | `documents/source10.txt`                                                                                                                    |

---

## Chunking Strategy

**Chunk size:** Approximately 900 characters per chunk.

**Overlap:** Approximately 150 characters of overlap between adjacent chunks.

**Reasoning:**

My documents are a mixture of Reddit threads, opinion articles, and college review pages. These are not long technical manuals where every section has a formal heading. They are mostly student-centered opinion texts, where one useful idea often appears in a short paragraph or a few connected comments. Because of that, I will use paragraph-aware chunking rather than blindly splitting every fixed number of characters.

The chunker will first split text around paragraph or line breaks, then combine nearby paragraphs until the chunk is about 900 characters. This size should be large enough to preserve a complete student opinion, complaint, or explanation, but not so large that one chunk mixes many unrelated topics. The 150-character overlap helps preserve context when an important thought crosses a chunk boundary.

If chunks are too small, retrieval may return fragments like “the food is bad” without enough context to explain why. If chunks are too large, retrieval may return broad sections containing dining, academics, housing, and general campus life all mixed together. My goal is for each chunk to be readable and useful on its own.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` through the `sentence-transformers` library.

**Top-k:** 5 retrieved chunks per query.

**Production tradeoff reflection:**

I am using `all-MiniLM-L6-v2` because it is lightweight, free, runs locally, and is recommended for this project stack. It is appropriate for a small course project because I do not need an API key or paid embedding service. It should be good enough for semantic search over a small collection of student opinion documents.

For a production deployment, I would consider several tradeoffs. A stronger embedding model might improve retrieval accuracy, especially when student language is informal or when the query uses different wording from the source documents. 

The system will store chunk embeddings in ChromaDB. When a user asks a question, the query will be embedded using the same embedding model, and ChromaDB will return the top 5 most semantically similar chunks. These chunks will then be passed to the LLM for grounded answer generation.

---

## Evaluation Plan

| # | Question                                                                          | Expected answer                                                                                              
| 1 | What do students complain about most regarding Williams dining?                   | The answer should identify recurring complaints found in the sources, such as food quality, limited variety, dining access, dining hall operations, or dissatisfaction with how Dining Services responds to student needs. The exact answer should be supported by retrieved source chunks.                 |
| 2 | What do students say about dietary restrictions at Williams dining halls?         | The answer should mention that some students report difficulty navigating dining halls with dietary restrictions and feel that Dining Services does not always provide reliable, accessible, or sufficient options. It should cite the Williams Record dietary restriction sources if retrieval works well. |
| 3 | Do students think Williams dining hall food is really bad, or are opinions mixed? | The answer should explain whether the collected sources show mostly negative opinions, mixed opinions, or disagreement among students. It should distinguish between general food-quality opinions and specific complaints about access or restrictions.                                                    |
| 4 | What improvements do students suggest for Williams dining?                        | The answer should describe concrete student-suggested improvements, such as better food quality, more variety, better accommodation for dietary restrictions, clearer communication, improved access, or changes to dining operations, depending on what source4 and related documents contain.             |
| 5 | What do students say about dining access during breaks or unusual campus periods? | The answer should mention student concerns or questions about dining availability during winter break or limited-service periods. It should cite the winter break Reddit source if retrieval works correctly.                                                                                               |

---

## Anticipated Challenges

1. Some sources may be difficult to extract automatically from URLs. Reddit, Niche, and Appily may block automated requests, use JavaScript rendering, or return page text with navigation content instead of the actual student discussion. If this happens, I will manually paste the useful source text into the corresponding `source#.txt` file while keeping the URL at the top for attribution.

2. Some sources may contain broad campus-life information rather than dining-specific information. For example, review pages may discuss academics, dorms, location, social life, and food in the same document. This could cause retrieval to return chunks that are generally about Williams but not specifically about dining. To reduce this, I will clean obvious boilerplate and inspect sample chunks before embedding.

3. Chunking may split important context across boundaries. For example, a student may describe a dietary restriction problem over several paragraphs. If the chunker separates the problem from the explanation, retrieval may return incomplete context. The 150-character overlap is meant to reduce this risk.

4. The model may generate an answer that sounds plausible but is not fully supported by the retrieved chunks. To reduce this, the generation prompt will instruct the LLM to answer only from retrieved context and to say it does not have enough information when the documents do not support an answer.

---

## Architecture

```text
documents/source1.txt ... documents/source10.txt
        |
        v
Document Ingestion
- Python reads each source file
- If the file contains a URL, requests/trafilatura/BeautifulSoup try to fetch and extract page text
- If automatic extraction fails, manually pasted text is used instead
        |
        v
Cleaning
- Remove extra whitespace, HTML artifacts, navigation text where possible
- Save extracted text into data/raw/
- Save cleaned text into data/processed/
        |
        v
Chunking
- Paragraph-aware chunking
- About 900 characters per chunk
- About 150 characters overlap
        |
        v
Embedding + Vector Store
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Vector database: ChromaDB
- Store each chunk with metadata: source file, source URL or label, and chunk index
        |
        v
Retrieval
- User question is embedded with the same embedding model
- ChromaDB returns top 5 most semantically similar chunks
        |
        v
Generation
- Groq LLM: llama-3.3-70b-versatile
- Prompt instructs model to answer only from retrieved chunks
- Response includes source attribution
        |
        v
Interface
- Gradio app or command-line interface
- User enters a question
- System returns answer, source list, and retrieved chunks
```