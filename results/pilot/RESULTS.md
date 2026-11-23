# SPORTZBOT benchmark results

Share of questions, in %. Brackets are 95% bootstrap intervals.

## SimpleQA, sports questions

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 8 | 0.0 (0.0 to 0.0) | 12.5 (0.0 to 37.5) | 87.5 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 1 (curated documents) | 8 | 0.0 (0.0 to 0.0) | 62.5 (25.0 to 87.5) | 37.5 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 2 (live Wikipedia) | 8 | 37.5 (12.5 to 75.0) | 0.0 (0.0 to 0.0) | 62.5 | 100.0 (100.0 to 100.0) | 54.5 |

## Winners of sports events in 2024 and 2025 (Wikidata)

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 8 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.0) | 100.0 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 1 (curated documents) | 8 | 0.0 (0.0 to 0.0) | 25.0 (0.0 to 50.0) | 75.0 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 2 (live Wikipedia) | 8 | 50.0 (12.5 to 87.5) | 25.0 (0.0 to 50.0) | 25.0 | 66.7 (25.0 to 100.0) | 57.1 |

## Both sets together

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 16 | 0.0 (0.0 to 0.0) | 6.2 (0.0 to 18.8) | 93.8 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 1 (curated documents) | 16 | 0.0 (0.0 to 0.0) | 43.8 (18.8 to 68.8) | 56.2 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 2 (live Wikipedia) | 16 | 43.8 (18.8 to 68.8) | 12.5 (0.0 to 31.2) | 43.8 | 77.8 (50.0 to 100.0) | 56.0 |

## Retrieval and speed

| System | Set | Gold answer appears word for word in the sources (%) | Median seconds per question | Errors | Ungraded |
|---|---|---|---|---|---|
| Llama 3.2 3B alone | simpleqa_sports |  | 1.4 | 0 | 0 |
| Llama 3.2 3B alone | wikidata_recent |  | 0.8 | 0 | 0 |
| Version 1 (curated documents) | simpleqa_sports | 12.5 | 40.0 | 0 | 0 |
| Version 1 (curated documents) | wikidata_recent | 0.0 | 37.1 | 0 | 0 |
| Version 2 (live Wikipedia) | simpleqa_sports | 37.5 | 49.7 | 0 | 0 |
| Version 2 (live Wikipedia) | wikidata_recent | 37.5 | 35.2 | 0 | 0 |

## Version 2, split by whether the gold answer was in the retrieved passages

| Retrieved passages | Questions | Correct | Incorrect | Not attempted |
|---|---|---|---|---|
| contain the gold answer | 6 | 50.0 | 33.3 | 16.7 |
| do not contain it word for word | 10 | 40.0 | 0.0 | 60.0 |
