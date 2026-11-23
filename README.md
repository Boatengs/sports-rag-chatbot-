# SPORTZBOT: sports questions answered from Wikipedia, with sources

SPORTZBOT is a sports chatbot that runs on a small local model (Llama 3.2, 3 billion parameters). Version 1 answered from 10 handwritten text files. Version 2 searches Wikipedia for every question, answers only from the passages it finds, cites them, and says "I don't know" when they don't contain the answer.

This version also measures the bot for the first time, on 652 questions with known answers. Version 2 answered 47.2% of them correctly and was right 81.7% of the time when it gave an answer. Version 1 got 1.5% right.

All numbers below come from `results/full_judge_qwen14b/RESULTS.md`.

## What was wrong with version 1

* The whole knowledge base was 10 text files, 17.5 KB in total, cut into 57 chunks. Anything outside them was unknown to the bot.
* Some of those files were wrong. `latest_football_2024_2025.txt` says Lamine Yamal scored Spain's equaliser in the Euro 2024 final; Nico Williams scored Spain's first goal from Yamal's pass, Cole Palmer equalised for England and Mikel Oyarzabal won it. It also says Messi finished fifth for the 2024 Ballon d'Or; he was not on the list of 30 nominees. `tennis.txt` calls Carlos Alcaraz the current world number one a few lines above saying Jannik Sinner became world number one in 2024.
* The prompt told the model it "MAY expand on the context with your general sports knowledge" and to "cite real statistics". That invites invented facts, even though the README said RAG prevents them.
* The README listed Formula 1, but there was no Formula 1 file.

## How version 2 works

For each question:

1. The model writes a short Wikipedia search query, using only words from the question.
2. Three searches run on Wikipedia: that query, the question's keywords, and the question itself. The top 2 pages of each are kept, up to 6 pages.
3. Each page is fetched as HTML and cut into passages of about 120 words. Infoboxes and results tables are kept, one line per table row with the column names repeated, because that is where most sports results live.
4. Passages are ranked in two steps: a small embedding model (`all-MiniLM-L6-v2`) keeps the best 40, then a cross encoder (`ms-marco-MiniLM-L-6-v2`) picks the best 6.
5. The model answers in one or two sentences from those 6 passages only, cites them as [1], [2], and otherwise replies "I don't know based on the sources I found."

The web app shows the cited Wikipedia pages as links under each answer.

## The test

Two sets of questions with known answers:

| Set | Questions | Where they come from |
|---|---|---|
| SimpleQA, sports | 360 | Every question in OpenAI's SimpleQA test set whose topic is sports (368, MIT licence), minus the 8 used while building |
| Sports winners, 2024 and 2025 | 292 | "Who won the ...?" for events that ended in 2024 or 2025, with the winner from Wikidata. 300 drawn from 3,487 eligible events, at most 25 per sport (56 sports), minus the 8 used while building |

For the Wikidata set, an event was only kept if it had exactly one winner with no qualifiers, a year in its name that matched its date, an end date at least 14 days before the build, and a name that did not already contain the winner.

Three systems answered every question, all with the same model (Llama 3.2 3B, `Q4_K_M`, through llama.cpp):

* Llama 3.2 3B alone, told to say "I don't know" when unsure.
* Version 1 as shipped: the 10 files, the same chunking, embeddings, MMR retrieval and prompt as `src/app.py` in version 1, at temperature 0.2.
* Version 2.

Each answer was graded correct, incorrect or not attempted with OpenAI's SimpleQA grading prompt, unchanged. A "not attempted" is an answer that does not give the asked fact and does not contradict it, such as "I don't know". The grader was Qwen2.5 14B Instruct, run locally.

## Results

All 652 questions. Brackets are 95% bootstrap intervals.

| System | Correct | Incorrect | Not attempted | Accuracy when it answered |
|---|---|---|---|---|
| Llama 3.2 3B alone | 0.5% | 1.8% | 97.7% | 20.0% (0.0 to 42.9) |
| Version 1 | 1.5% (0.6 to 2.6) | 16.7% (14.0 to 19.6) | 81.7% | 8.4% (3.7 to 13.7) |
| Version 2 | 47.2% (43.4 to 50.9) | 10.6% (8.3 to 13.0) | 42.2% | 81.7% (77.6 to 85.4) |

By question set:

| System | SimpleQA correct | SimpleQA incorrect | 2024 to 2025 winners correct | 2024 to 2025 winners incorrect |
|---|---|---|---|---|
| Llama 3.2 3B alone | 0.8% | 3.3% | 0.0% | 0.0% |
| Version 1 | 1.7% | 25.0% | 1.4% | 6.5% |
| Version 2 | 44.4% | 8.9% | 50.7% | 12.7% |

What this shows:

* On its own, the 3B model knows almost none of these answers, and with permission to say "I don't know" it says so 97.7% of the time.
* Version 1 adds little. When it did give an answer, it was right 8.4% of the time. Its prompt pushes long answers (median 173 words, with emoji), and on SimpleQA a quarter of its answers stated something that contradicts the known answer.
* Version 2 gets about half of the questions right and declines most of the rest. When it answers, it is right about 4 times in 5.
* Retrieval is the limit. The known answer appears word for word in version 2's 6 passages for 320 of the 652 questions (this undercounts, since "Bayern Munich" does not match "FC Bayern Munich Women"). With the answer in the passages, version 2 was correct 66.2% of the time; without it, 28.9%. For 28 questions the searches found no page at all.

## How far to trust the grading

Both graders were checked against a random sample of 150 answers (50 per system), each graded again under the same SimpleQA rules by Claude (Anthropic's model), reading the question, the known answer and the full response. The sample and all three sets of grades are in `results/full_judge_qwen14b/audit_150.json`.

| Grader | Agrees with the second grading |
|---|---|
| Qwen2.5 14B (used above) | 147 of 150 |
| Qwen2.5 7B (first run) | 138 of 150 |

The 7B grader marked 8 of version 1's "I could not find that" answers as incorrect and 4 of version 2's correct answers with a name variant ("Australia" for the full Wikidata team name) as incorrect. With it, version 1 looked worse (47.7% incorrect) and version 2 slightly worse (43.9% correct). Its full results are in `results/full/`. The 14B grader still marked 2 of version 2's correct answers in the sample as incorrect, so version 2's figures are, if anything, a little low.

## Where version 2 goes wrong

Real examples from the run:

* The right page, the wrong row. Asked who won the 60 metres hurdles at the 2024 World Indoor Championships, it read the hurdles leg of the heptathlon and named Simon Ehammer.
* The wrong event with a similar name. Asked about the 2024 Argentina Open singles (a men's event), it named the winner of a women's tournament.
* Bad arithmetic from a table. It gave Brighton's 2021 to 22 goal difference as +29.
* Ambiguous questions. "The 2024 British Women's Open" is a snooker event in Wikidata; Wikipedia's search found the golf one.

## Limits

* The Wikidata winners can be wrong or oddly labelled, for example an under 17 national team listed as the winner of an under 16 tournament.
* SimpleQA questions were written to be hard for large models, so they are not a sample of what fans usually ask.
* Wikipedia changes. Each source in the results records the page revision used, but a rerun today would fetch newer pages.
* One question takes about 36 seconds (median) on a 4 core GitHub runner, so this is a demo speed, not a product speed. A larger model or a GPU would help both speed and the reading errors above.
* Wikipedia is the only source. If a fact is not there, the bot will not find it.

## Run it

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"
ollama pull llama3.2          # or run llama-server and set SPORTZBOT_LLM_URL=http://127.0.0.1:8080
uvicorn app:app --app-dir src --port 8000
```

Then open http://localhost:8000. The benchmark runs on GitHub Actions: `questions.yml` builds the question sets, `bench.yml` answers and grades them, `regrade.yml` grades saved answers with another model.

## Files

* `src/sportzbot/`: question sets (`questions.py`), Wikipedia search and page parsing (`wiki.py`), the three systems (`systems.py`), the model client (`llm.py`), answering and grading (`run.py`), the report (`report.py`), and the SimpleQA grader prompt (`grader_template.txt`, MIT licence, from `github.com/openai/simple-evals`).
* `src/app.py` and `src/static/index.html`: the web app.
* `data/questions/`: both question sets and how they were built.
* `results/full/`: every answer with its sources, graded by the 7B model. `results/full_judge_qwen14b/`: the same answers graded by the 14B model, and the 150 answer check. `results/pilot/`: the 16 questions used while building.
* `documents/`: version 1's 10 files, kept so the comparison can be rerun.
* `notebooks/`: the version 1 notebooks.
