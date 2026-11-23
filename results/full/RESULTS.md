# SPORTZBOT benchmark results

Share of questions, in %. Brackets are 95% bootstrap intervals.

## SimpleQA, sports questions

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 360 | 1.1 (0.3 to 2.2) | 3.6 (1.9 to 5.6) | 95.3 | 23.5 (5.3 to 44.4) | 2.1 |
| Version 1 (curated documents) | 360 | 0.8 (0.0 to 1.9) | 53.3 (47.8 to 58.9) | 45.8 | 1.5 (0.0 to 3.5) | 1.1 |
| Version 2 (live Wikipedia) | 360 | 43.1 (38.1 to 48.3) | 11.7 (8.3 to 15.3) | 45.3 | 78.7 (72.8 to 84.4) | 55.7 |

## Winners of sports events in 2024 and 2025 (Wikidata)

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 292 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.0) | 100.0 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 1 (curated documents) | 292 | 0.7 (0.0 to 1.7) | 40.8 (35.3 to 46.6) | 58.6 | 1.7 (0.0 to 4.2) | 1.0 |
| Version 2 (live Wikipedia) | 292 | 44.9 (39.0 to 50.7) | 19.9 (15.4 to 24.7) | 35.3 | 69.3 (62.8 to 75.7) | 54.5 |

## Both sets together

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 652 | 0.6 (0.2 to 1.2) | 2.0 (1.1 to 3.1) | 97.4 | 23.5 (5.3 to 46.2) | 1.2 |
| Version 1 (curated documents) | 652 | 0.8 (0.2 to 1.5) | 47.7 (44.0 to 51.7) | 51.5 | 1.6 (0.3 to 3.1) | 1.0 |
| Version 2 (live Wikipedia) | 652 | 43.9 (40.2 to 47.5) | 15.3 (12.7 to 18.3) | 40.8 | 74.1 (69.6 to 78.4) | 55.1 |

## Retrieval and speed

| System | Set | Gold answer appears word for word in the sources (%) | Median seconds per question | Errors | Ungraded |
|---|---|---|---|---|---|
| Llama 3.2 3B alone | simpleqa_sports |  | 1.0 | 0 | 0 |
| Llama 3.2 3B alone | wikidata_recent |  | 0.8 | 0 | 0 |
| Version 1 (curated documents) | simpleqa_sports | 11.9 | 33.2 | 0 | 0 |
| Version 1 (curated documents) | wikidata_recent | 2.4 | 33.8 | 0 | 0 |
| Version 2 (live Wikipedia) | simpleqa_sports | 55.0 | 35.5 | 0 | 0 |
| Version 2 (live Wikipedia) | wikidata_recent | 41.8 | 36.2 | 0 | 0 |

## Version 2, split by whether the gold answer was in the retrieved passages

| Retrieved passages | Questions | Correct | Incorrect | Not attempted |
|---|---|---|---|---|
| contain the gold answer | 320 | 63.7 | 15.6 | 20.6 |
| do not contain it word for word | 332 | 24.7 | 15.1 | 60.2 |
