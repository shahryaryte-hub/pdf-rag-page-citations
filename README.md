# How to make a RAG answer link to the exact page of a PDF

**Which three concepts does NIST emphasize in responsible AI?**

Human centricity, social responsibility, and sustainability. The supporting sentence is in the last paragraph of the Executive Summary’s first page. Open the citation and check it yourself. [NIST AI Risk Management Framework 1.0, printed page 1 (PDF page 6)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf#page=6)

The distinction between those page numbers matters. The PDF includes a cover and front matter, so a link ending in `#page=1` would open the cover. This example takes the citation from the retrieved passage. It uses the same page number a PDF viewer counts from the beginning of the file.

[Read the walkthrough and try the prefilled NIST extraction](https://solidscrape-pdf-page-citations.techmuhafiz.chatgpt.site/).

## Try it locally for free

Download or clone this repository. From its folder, run the following with Python 3.8 or later.

```sh
python example.py
```

The offline example uses an excerpt from a verified extraction. It selects the sentence answering the question and prints its source link. Python’s standard library is enough. You can also inspect the [example code](example.py).

## Extract the passages from NIST yourself

Open the prefilled example to try the same public PDF in your browser. It requests physical pages 6 and 7. The reference run returned six passages across the two pages, at a listed event cost of **$0.0074**. [Try the NIST PDF example on Apify](https://apify.com/solidscrape/pdf-to-rag-with-citations/examples/nist-ai-framework-to-page-cited-passages?utm_source=github&utm_medium=tutorial&utm_campaign=pdf_page_citations)

For a live Python run, store your own Apify token in your local environment or secret manager as `APIFY_TOKEN`. Run the script with the live option.

```sh
python example.py --live
```

The live example starts one extraction with a **$0.02 run cap**. It searches the returned passages for the same supporting sentence. The script answers this fixed question by selecting source text, so you can check the citation without an LLM account. [Current Actor pricing](https://apify.com/solidscrape/pdf-to-rag-with-citations/pricing)

## Carry the citation into your own RAG pipeline

1. **Index each passage with its source.** Embed the row’s `text` and use `chunkId` as the record key. Keep `citationUrl`, `pageNumber`, and `documentSha256` on that same record. Each passage stays within one physical page.
2. **Retrieve the evidence with the text.** When a user asks a question, return the matching passage and its metadata together. If you use a model to compose an answer, give it the retrieved passages as evidence and have it identify which passage supports each claim.
3. **Render the link from the selected record.** Look up the cited `chunkId` in your retrieved results and display that record’s `citationUrl`. This ties the clickable page to the evidence even if the model invents a plausible page number. If the retrieved passages do not support the answer, say that the supplied pages contain insufficient evidence.

Once your application has selected a dataset row called `passage`, this expression produces a Markdown link using the actual page and URL.

```python
f"[PDF page {passage['pageNumber']}]({passage['citationUrl']})"
```

To adapt the workflow, choose a public, text-based PDF you have permission to process and a small page range. For image-only scans, apply OCR first. Inspect the Actor’s `SUMMARY` output for blank pages and the last page it examined before treating the extracted passages as coverage of the whole document. [PDF to RAG with Citations on Apify](https://apify.com/solidscrape/pdf-to-rag-with-citations)
