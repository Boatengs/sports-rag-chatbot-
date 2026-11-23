# SPORTZBOT benchmark results

Share of questions, in %. Brackets are 95% bootstrap intervals.

## SimpleQA, sports questions

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 360 | 0.8 (0.0 to 1.9) | 3.3 (1.7 to 5.3) | 95.8 | 20.0 (0.0 to 42.1) | 1.6 |
| Version 1 (curated documents) | 360 | 1.7 (0.6 to 3.1) | 25.0 (20.6 to 29.4) | 73.3 | 6.2 (2.0 to 11.4) | 2.6 |
| Version 2 (live Wikipedia) | 360 | 44.4 (39.4 to 49.7) | 8.9 (6.1 to 11.9) | 46.7 | 83.3 (77.9 to 88.3) | 58.0 |

## Winners of sports events in 2024 and 2025 (Wikidata)

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 292 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.0) | 100.0 | 0.0 (0.0 to 0.0) | 0.0 |
| Version 1 (curated documents) | 292 | 1.4 (0.3 to 2.7) | 6.5 (4.1 to 9.6) | 92.1 | 17.4 (4.0 to 33.3) | 2.5 |
| Version 2 (live Wikipedia) | 292 | 50.7 (44.9 to 56.5) | 12.7 (9.2 to 16.8) | 36.6 | 80.0 (74.0 to 85.4) | 62.1 |

## Both sets together

| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |
|---|---|---|---|---|---|---|
| Llama 3.2 3B alone | 652 | 0.5 (0.0 to 1.1) | 1.8 (0.9 to 2.9) | 97.7 | 20.0 (0.0 to 42.9) | 0.9 |
| Version 1 (curated documents) | 652 | 1.5 (0.6 to 2.6) | 16.7 (14.0 to 19.6) | 81.7 | 8.4 (3.7 to 13.7) | 2.6 |
| Version 2 (live Wikipedia) | 652 | 47.2 (43.4 to 50.9) | 10.6 (8.3 to 13.0) | 42.2 | 81.7 (77.6 to 85.4) | 59.9 |

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
| contain the gold answer | 320 | 66.2 | 12.2 | 21.6 |
| do not contain it word for word | 332 | 28.9 | 9.0 | 62.0 |
