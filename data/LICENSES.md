# Data licences

The task files here are small subsets of public benchmarks, reformatted to one JSON object per line.
They keep the licence of their source. The code of this repo is MIT (see ../LICENSE); that licence
does not cover these subsets.

| File | Source | Licence | What we changed |
|---|---|---|---|
| `wikiqa/tasks.jsonl` | [HotpotQA](https://hotpotqa.github.io/) (Yang et al., 2018), distractor validation set via the Hugging Face dataset `hotpotqa/hotpot_qa` | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 100 questions sampled (80 test, 20 dev); kept `id`, `question`, `answer`, `type`, `supporting_titles`; added `split`. This subset is shared under CC BY-SA 4.0. |
| `research/tasks.jsonl` | [FRAMES](https://huggingface.co/datasets/google/frames-benchmark) (Krishna et al., 2024), test split | Apache 2.0 (copy: [`research/LICENSE-APACHE-2.0.txt`](research/LICENSE-APACHE-2.0.txt)) | 90 questions sampled (80 test, 10 dev) with at most 3 linked pages and no tabular reasoning; kept `question`, `answer`, `reasoning_types`, `wiki_links`; new `id` and `split`. |
| `../src/similitude/third_party/tau_retail/` | [τ-bench](https://github.com/sierra-research/tau-bench) retail environment | MIT (copy in that folder) | See the README in that folder. |
| `*/edits.json`, `wikiqa/fixes.json` | Written by Claude (Anthropic) for this study | MIT, as the code | – |

`scripts/prepare_wikiqa.py` and `scripts/prepare_research.py` rebuild the two task files from their
sources.
