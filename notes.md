# 2023-May-18

## Implementing Field-Weighted Citation Impact

Before I start - is there already code for this? Or some other solution?

- Elsevier SciVal seems to have Field-Weighted Citation Impact in their data, based on the table header given in the README of [this repo](https://github.com/cu-library/scival-export-tools)
  - SciVal is a paid service. Unclear what the pricing is. It could be worth the money.
  - Elsevier is probably the best data source too just based on the fact that they charge a lot of money.
  - To some extent I want to protest against this closed-source business but that's not important for the bottom line of this research project.
- I looked at the first page of code results on GitHub for "field-weighted citation impact". None of the results look relevant, in terms of being open-source code that calculates the metric.

Ok, I'm going to proceed with implementing FWCI myself.

# 2023-May-23

## Implementing Field-Weighted Citation Impact

- Working on the expected number of citations for the field
- My prior for FWCI for a top AI lab, such as Meta Inc., is between 10 and 1000.
  - The most-cited works in ML are on the order of 10,000 citations. So getting 10,000x more citations than _average_ seems like a stretch.
  - On the other hand, I imagine that most works would get on the order of 1 to 10 citations. So it seems very likely that the top labs can do at least 10x better than that.
- Small test with the first work retrieved for Meta Inc. Limiting to level-1 concepts. Only retrieving the first 10 papers per concept.

```
Work: Deep learning (1 of 1)
Citation count: 9046
Concept: Artificial intelligence (1 of 5)
Expected citations: 1720.16
Concept: Speech recognition (2 of 5)
Expected citations: 494.52
Concept: Organic chemistry (3 of 5)
Expected citations: 1309.32
Concept: Epistemology (4 of 5)
Expected citations: 1039.68
Concept: Law (5 of 5)
Expected citations: 1170.32
Overall expected citation count: 964.5878627478993
9.378098511658575
```

- Final result seems on the low end.
- I'm surprised that the expected citations within each concept are so high. What's going on there?
  - Maybe they are (roughly) sorted by descending citation count already?
    - Increasing the number of works fetched per concept would test this hypothesis. This hypothesis predicts the citation counts will go down.

Increasing number of works fetched per concept to 100:

```
Work: Deep learning (1 of 1)
Citation count: 9046
Concept: Artificial intelligence (1 of 5)
Expected citations: 719.63
Concept: Speech recognition (2 of 5)
Expected citations: 169.49
Concept: Organic chemistry (3 of 5)
Expected citations: 679.87
Concept: Epistemology (4 of 5)
Expected citations: 402.31
Concept: Law (5 of 5)
Expected citations: 499.51
Overall expected citation count: 377.4116744981545
23.968521938354172
```

- As predicted, the citation counts went down.
- Increasing to 1000:

```
Work: Deep learning (1 of 1)
Citation count: 9046
Concept: Artificial intelligence (1 of 5)
Expected citations from 1000 works: 192.325
Concept: Speech recognition (2 of 5)
Expected citations from 1000 works: 34.548
Concept: Organic chemistry (3 of 5)
Expected citations from 1000 works: 252.004
Concept: Epistemology (4 of 5)
Expected citations from 1000 works: 105.19
Concept: Law (5 of 5)
Expected citations from 1000 works: 146.048
Overall expected citation count: 91.79932789628492
98.5410264683004
```

- Yeah so, sample size is important and I think this is strong evidence of a bias towards earlier-fetched works being more highly cited.
- The above took about 2 minutes to run. That's for a single work, and without exhausting the works in each field.
- Even keeping related work limit to 1000 and concept level to 1, processing all of e.g. Google's ~10,000 works would take 20,000 minutes or 300 hours.
- So we need a much more efficient approach.

Can I solve this using `sample`?

- Only supported with basic paging. I can probably deal with that.
- Max 10,000 items per sample - that seems fine.
- Just trying a sample of 200 first.

```
Work: Deep learning (1 of 1)
Citation count: 9046
Concept: Artificial intelligence (1 of 5)
Expected citations from 200 works: 3.75
Concept: Speech recognition (2 of 5)
Expected citations from 200 works: 5.89
Concept: Organic chemistry (3 of 5)
Expected citations from 200 works: 6.465
Concept: Epistemology (4 of 5)
Expected citations from 200 works: 1.255
Concept: Law (5 of 5)
Expected citations from 200 works: 2.045
Overall expected citation count: 2.66391708000269
3395.751342226788
```

- Woah, alright. That's very different. More in line with expectations.
- Tried without a seed 10 times to check the variance: mean 3404.515142781751, std 367.53528079918726. That's fairly low variance but I'd want it lower.
  - Second publication retrieved for Meta: (1397.0421067552493, 254.32779527860404)
  - 1000th publication: (1.3905152115240829, 0.16317888977945175)
- 1000 samples, work 1: (2962.620614710257, 336.11310603602965)


## Efficiency improvements for FWCI

- Limiting the concepts to "Artificial Intelligence" or "Computer Science" or "Machine Learning". Using pre-calculated values for expected citations in those concepts.
  - Definitely viable at least as a first hacky attempt.
- Using downloaded data for works by concept
  - If we use downloaded data but still keep all the concepts and compute those on the fly, then we will basically need to download the entirety of OpenAlex. This might be intractable but then again it might not.
  - According to ChatGPT (3.5), there are on the order of 100 million research papers indexed in databases like PubMed and Google Scholar.
  - O(100 million) papers, O(10,000) chars of data per paper (based on 1 example having about 20,000). 10,000 chars ~= 10,000 bytes I think? 10 kB. That's 1e12 bytes. 1 TB. Ok. Loading that much data all at once won't work, but it's feasible to keep on a hard drive.
    - Could also pre-process to remove most of the data for each paper. So 1 TB is an upper bound. 
- Using downloaded data for works by institution
  - This seems more feasible than the above. We just need to get all the institutions who published in AI, or ML. That should be a much . Though it could still take hours or days to download all of it, I'd imagine.
  - We could download all works in say, AI. Then precompute average citation count, AND organise the works by each institution.
    - If we want to get fancier, precopute citation count for each subconcept of AI but that's not necessary for the first pass.
- Caching results for repeated concepts
  - Seems very useful. A middle ground between pre-calculating results for 1-3 concepts, and computing all concepts on the fly.
- Use `select` https://docs.openalex.org/api-entities/works/get-lists-of-works#select-fields to only fetch the data I need for each work

# 2023-May-24

## Random sampling

- Let's review how random sampling goes.
  - With a sample of 10 seeds, at 1000 samples per field, for the first work retrieved for Meta Inc.
  - Result: (mean=2962.620614710257, std=336.11310603602965)
    - The std is about 11% of the mean
    - I didn't write down an exact runtime, but I recall that it took ~minutes
- Runtime
  - Baseline: 1 work with 5 selected concepts, 1000 samples per concept: 38s
    - Intractable. 1M works would take 2 years.
  - 10 works, no caching: 

## Pivot

- Pre-select institutions
- Just look at AI (maybe union with ML)
- Institutions
  - Google
  - DeepMind
  - OpenAI
  - Meta/Facebook
  - Microsoft
  - Baidu

# 2023-May-26

Do Concept objects have citation info?

- 
