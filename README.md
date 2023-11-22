# AI industry research impact

This repository contains code to reproduce the analysis from "Who is leading in AI? An analysis of industry AI research".

Main notebooks:
- `publications_analysis.ipynb` runs the main analysis of the publication dataset, reproducing Figure 1 (a) and (c) in the paper
- `compute_analysis.ipynb` runs the analysis of companies' frontier training compute, reproducing Figure 1 (b) in the paper
- `innovations_analysis.ipynb` runs the analysis of the adoption frequency of algorithmic innovations that underpin large language models, reproducing Figure 1 (d) in the paper

Supporting notebooks:
- `select_institutions.ipynb` selects the companies to include in the publication dataset, by analysing top-cited publication data and notable ML systems data from the PCD database [1]
- `initial_publications_dataset.ipynb` creates and saves the initial set of deduplicated publications affiliated with the selected companies
- `openai_dataset.ipynb` creates and saves the additional set of publications affiliated with OpenAI, with improved affiliation data
- `final_publications_dataset.ipynb` merges the initial dataset and OpenAI dataset into the final publications dataset
- `publications_checks.ipynb` runs additional analysis (e.g. statistical significance), accuracy checks, and other sense checks on the publication dataset
- `openalex_semanticscholar_comparison.ipynb` measures agreement between the citation counts in OpenAlex and Semantic Scholar
- `openalex_sources_investigation.ipynb` investigates publications from different sources used by OpenAlex over time, which tipped us off to Microsoft Academic Graph no longer being updated as of 2021

Supporting code:
- `research_impact` subfolder contains common supporting code; e.g. `processors.py` implements the extraction of author and citation data

[1] https://docs.google.com/spreadsheets/d/1AAIebjNsnJj_uKALHbXNfn3_YsT6sHXtCU0q7OIPuc4/
