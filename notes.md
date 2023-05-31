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

# 2023-May-27

Just doing the basic thing. Citations counts. Making plots.

# 2023-May-29

## Building on the citation count plots

Adding more institutions

- Microsoft (choose the most-cited search result for Microsoft; maybe it's Microsoft Research)

```python
microsoft_results = Institutions().search("Microsoft").get()
for ins in microsoft_results:
    print(f"{ins['display_name']}: {ins['cited_by_count']}")
```

```
Microsoft (United States): 1070588 citations; 25120 works
Microsoft Research (United Kingdom): 680187 citations; 12026 works
Microsoft Research Asia (China): 332476 citations; 6266 works
Microsoft Research (India): 64316 citations; 1903 works
Microsoft (Finland): 31806 citations; 899 works
Microsoft (Germany): 9202 citations; 469 works
Microsoft (Israel): 5335 citations; 311 works
Microsoft (India): 4329 citations; 292 works
Microsoft (Brazil): 3708 citations; 517 works
Microsoft (Canada): 3169 citations; 160 works
Microsoft (Netherlands): 2584 citations; 36 works
Microsoft (France): 2559 citations; 99 works
Microsoft (Denmark): 1464 citations; 74 works
Microsoft (United Kingdom): 1751 citations; 123 works
The Microsoft Research - University of Trento Centre for Computational and Systems Biology: 6296 citations; 369 works
Microsoft (Switzerland): 898 citations; 60 works
Microsoft (Norway): 861 citations; 92 works
Microsoft (Ireland): 608 citations; 36 works
Microsoft (Portugal): 324 citations; 53 works
Microsoft (Belgium): 29 citations; 12 works
```

  - Maybe I could just include all of these?
  - Seems pretty important to include "Microsoft Research (United Kingdom)"
  - How would I include them all?
    - Come back to this.
  - There's only 20 results, so this is all of them (default limit in OpenAlex is 25 results).
  - Including MS and MSRUK separately, for now

- Meta
  - No results for "Facebook". I guess OpenAlex updated all the references?
    - No relevant results for "Facebook AI Research", "FAIR", "Meta AI Research", "MAIR"
  - Wow, Meta (Israel) has more citations and works than Meta (United States). I would not have predicted that.
  - Including Meta (Israel) and Meta (United States) separately, for now.

```
https://openalex.org/I2252078561 Meta (Israel): 259530 citations; 4347 works
https://openalex.org/I4210114444 Meta (United States): 164929 citations; 2220 works
https://openalex.org/I4210149973 ARC Centre of Excellence for Transformative Meta-Optical Systems: 11813 citations; 543 works
https://openalex.org/I4210111288 Meta (United Kingdom): 2100 citations; 140 works
https://openalex.org/I4210120172 Meta Vision Systems (United Kingdom): 1994 citations; 63 works
https://openalex.org/I4210099706 Center For Advanced Meta-Materials: 710 citations; 40 works
https://openalex.org/I4210118911 META Group: 314 citations; 61 works
https://openalex.org/I4210131362 Corporación Universitaria del Meta: 469 citations; 246 works
https://openalex.org/I4210128585 META Health: 129 citations; 141 works
https://openalex.org/I4210158286 International Platform of Registered Systematic Review and Meta-analysis Protocols: 212 citations; 81 works
https://openalex.org/I4210158323 Meta House: 0 citations; 0 works
```

- Top unis
  - https://csrankings.org/#/fromyear/2010/toyear/2023/index?ai&vision&mlmining&nlp&world
  - First US uni is CMU
  - First China uni is Peking
  - Same as above on https://airankings.org/ (#publications metric)
  - Different in AI Index (p.44): https://aiindex.stanford.edu/wp-content/uploads/2023/04/HAI_AI-Index-Report_2023.pdf
    - The top is Chinese Academy of Sciences, always, from 2010 to 2021
    - Only US uni in top 10 is MIT
  - Ok, I'll include CMU, MIT, Peking and CAS

"Massachusetts Institute of Technology"

```
1
https://openalex.org/I63966007 Massachusetts Institute of Technology: 13314963 citations; 236903 works
```

"MIT"

```
23
https://openalex.org/I63966007 Massachusetts Institute of Technology: 13314963 citations; 236903 works
https://openalex.org/I4210110987 IIT@MIT: 460441 citations; 11271 works
https://openalex.org/I4210122954 MIT Lincoln Laboratory: 380910 citations; 11383 works
https://openalex.org/I4210092658 Harvard–MIT Division of Health Sciences and Technology: 530463 citations; 5324 works
https://openalex.org/I2802422659 Ragon Institute of MGH, MIT and Harvard: 171263 citations; 3154 works
https://openalex.org/I4210095297 MIT University: 56815 citations; 8865 works
https://openalex.org/I4210167254 Singapore-MIT Alliance for Research and Technology: 116037 citations; 3333 works
https://openalex.org/I4210159271 MIT-Harvard Center for Ultracold Atoms: 59807 citations; 704 works
https://openalex.org/I4210167301 Institut für das Bauen mit Kunststoffen: 19665 citations; 1003 works
https://openalex.org/I4210088227 MIT World Peace University: 2050 citations; 1434 works
https://openalex.org/I125931852 Manukau Institute of Technology: 6625 citations; 580 works
https://openalex.org/I4210125891 MIT Sea Grant: 3522 citations; 168 works
https://openalex.org/I4210129287 Novartis-MIT Center for Continuous Manufacturing: 3823 citations; 66 works
https://openalex.org/I4210162439 Maharashtra Institute of Technology - Art, Design and Technology University: 2704 citations; 797 works
https://openalex.org/I138660223 University of Southern Mindanao: 1361 citations; 237 works
https://openalex.org/I4210118768 Ministry of Infrastructures and Transport: 405 citations; 51 works
https://openalex.org/I4210154469 Management Intelligenter Technologien (Germany): 370 citations; 42 works
https://openalex.org/I4210093068 Cambridge–MIT Institute: 216 citations; 28 works
https://openalex.org/I4210119490 International Tourism Institute: 38 citations; 51 works
https://openalex.org/I4210165498 Stiftung Leben mit Krebs: 10 citations; 2 works
https://openalex.org/I4210103124 Poliklinik für Zahnärztliche Prothetik mit Propädeutik: 14 citations; 7 works
https://openalex.org/I3132832342 Myanmar Institute of Theology: 11 citations; 34 works
https://openalex.org/I4210093988 Studio Promocji MIT (Poland): 0 citations; 0 works
```

"Carnegie Mellon University"

```
4
https://openalex.org/I74973139 Carnegie Mellon University: 4474709 citations; 111418 works
https://openalex.org/I4210089979 Carnegie Mellon University Qatar: 8163 citations; 607 works
https://openalex.org/I4210091826 Carnegie Mellon University Australia: 1643 citations; 80 works
https://openalex.org/I4210130200 Carnegie Mellon University Africa: 534 citations; 121 works
```

"CMU"

```
20
https://openalex.org/I74973139 Carnegie Mellon University: 4474709 citations; 111418 works
https://openalex.org/I91656880 China Medical University: 392164 citations; 34757 works
https://openalex.org/I184693016 China Medical University: 383688 citations; 20172 works
https://openalex.org/I48076826 Chiang Mai University: 348706 citations; 25902 works
https://openalex.org/I183519381 Capital Medical University: 806246 citations; 67150 works
https://openalex.org/I1629065 Central Michigan University: 187325 citations; 13526 works
https://openalex.org/I1354457 Colorado Mesa University: 15029 citations; 826 works
https://openalex.org/I4210129003 SYSU-CMU International Joint Research Institute: 6516 citations; 362 works
https://openalex.org/I4210096424 Chabahar Maritime University: 5117 citations; 732 works
https://openalex.org/I4210089979 Carnegie Mellon University Qatar: 8163 citations; 607 works
https://openalex.org/I115765903 Central Methodist University: 2032 citations; 237 works
https://openalex.org/I242057862 Central Mindanao University: 1818 citations; 380 works
https://openalex.org/I4210091826 Carnegie Mellon University Australia: 1643 citations; 80 works
https://openalex.org/I4210140482 Constanta Maritime University: 1590 citations; 827 works
https://openalex.org/I2802039673 California Miramar University: 1206 citations; 110 works
https://openalex.org/I54088770 Canadian Mennonite University: 757 citations; 164 works
https://openalex.org/I4210144920 Cambodian Mekong University: 687 citations; 30 works
https://openalex.org/I4210130200 Carnegie Mellon University Africa: 534 citations; 121 works
https://openalex.org/I4210133525 Community of Mediterranean Universities: 274 citations; 41 works
https://openalex.org/I4210116378 Carolus Magnus University: 0 citations; 0 works
```

"Peking University"

```
10
https://openalex.org/I20231570 Peking University: 3475214 citations; 159921 works
https://openalex.org/I4210130930 Peking University First Hospital: 177754 citations; 14769 works
https://openalex.org/I4210124809 Peking University People's Hospital: 140956 citations; 13021 works
https://openalex.org/I4210141942 Peking University Third Hospital: 138540 citations; 13243 works
https://openalex.org/I4210093964 Peking University Cancer Hospital: 115575 citations; 6385 works
https://openalex.org/I4210128628 Peking University Shenzhen Hospital: 61055 citations; 5482 works
https://openalex.org/I4210162420 Peking University Sixth Hospital: 55355 citations; 1892 works
https://openalex.org/I4210133846 Peking University International Hospital: 14993 citations; 1658 works
https://openalex.org/I4210139292 Peking University Shougang Hospital: 4487 citations; 697 works
https://openalex.org/I4210095659 Peking University Stomatological Hospital: 275 citations; 79 works
```

"Chinese Academy of Sciences"

```
20
https://openalex.org/I19820366 Chinese Academy of Sciences: 14090584 citations; 541868 works
https://openalex.org/I4210165038 University of Chinese Academy of Sciences: 3602009 citations; 193937 works
https://openalex.org/I4210138501 Chinese Academy of Agricultural Sciences: 739547 citations; 39838 works
https://openalex.org/I4210131870 Institute of Psychology, Chinese Academy of Sciences: 88423 citations; 3805 works
https://openalex.org/I200296433 Chinese Academy of Medical Sciences & Peking Union Medical College: 718070 citations; 45759 works
https://openalex.org/I2802497816 Chinese Academy of Geological Sciences: 206880 citations; 10933 works
https://openalex.org/I4210156332 Chinese Research Academy of Environmental Sciences: 146132 citations; 7805 works
https://openalex.org/I4210141683 China Academy of Chinese Medical Sciences: 145894 citations; 14953 works
https://openalex.org/I46529539 Chinese Academy of Fishery Sciences: 121885 citations; 12473 works
https://openalex.org/I4210133131 Chinese Academy of Meteorological Sciences: 116426 citations; 6247 works
https://openalex.org/I114218197 Chinese Academy of Social Sciences: 58211 citations; 9090 works
https://openalex.org/I107851509 Chinese Academy of Tropical Agricultural Sciences: 59328 citations; 5474 works
https://openalex.org/I4210141458 Cancer Hospital of Chinese Academy of Medical Sciences: 34240 citations; 2577 works
https://openalex.org/I4210117959 Key Laboratory of Chemistry for Natural Products of Guizhou Province and Chinese Academy of Sciences: 6866 citations; 709 works
https://openalex.org/I4210111590 Chinese Academy of Medical Sciences Dermatology Hospital: 7861 citations; 743 works
https://openalex.org/I4210129227 Chinese Academy of Agricultural Mechanization Sciences: 6139 citations; 677 works
https://openalex.org/I4210126517 Wangjing Hospital of China Academy of Chinese Medical Sciences: 3282 citations; 864 works
https://openalex.org/I4210108135 Guangzhou Institute of Applied Software Technology, Chinese Academy of Sciences: 203 citations; 51 works
https://openalex.org/I2802603554 Academy of Chinese Culture and Health Sciences: 123 citations; 2 works
https://openalex.org/I4210124088 Institute of Taiwan Studies Chinese Academy of Social Sciences: 53 citations; 45 works
```

Updated institution list:

```
selected_institution_ids = [
    "https://openalex.org/I1291425158",  # Google (United States)
    "https://openalex.org/I4210090411",  # DeepMind
    "https://openalex.org/I4210161460",  # OpenAI
    "https://openalex.org/I1290206253",  # Microsoft (United States)
    "https://openalex.org/I4210164937",  # Microsoft Research (United Kingdom)
    "https://openalex.org/I2252078561",  # Meta (Israel)
    "https://openalex.org/I4210114444",  # Meta (United States)
    "https://openalex.org/I63966007",  # Massachusetts Institute of Technology
    "https://openalex.org/I74973139",  # Carnegie Mellon University
    "https://openalex.org/I20231570",  # Peking University
    "https://openalex.org/I19820366",  # Chinese Academy of Sciences
]
```

- Total number of works: 134178
- 

# 2023-May-30

- AI total citations: 92571279
- Selected works total citations: 3927129

## Regression modeling

From Jaime:

```
The model I am most interested in you fitting is a linear regression of the type \log \dot A = \phi \log A + \lambda \log R, where \dot A are citation-weighted publications in a year, A = \sum_t \delta^(T-t) \dot A are cumulative citation-weighted publications in the whole field (possibly exponentially discounted \delta = 0.1) and R is the number of researchers in major corporations (edited) 

Jaime Sevilla
  19 hours ago
Secondly, I want the same but instead of for the whole field I want it for each company
We would have \log \dot A_i = \phi \log A + \lambda \log R_i
Note that \dot A_i and R_i would be company-specific, but the stock of accumulated research A would be industry wide

Jaime Sevilla
  19 hours ago
(should add a constant term to these regressions)

Jaime Sevilla
  19 hours ago
A 1h investigation that I would be interested in is seeing whether we can predicting citation count by date T given citations by date t. This would help decide how to do the citation-weighting
```

- Citation-weighted publications
  - Start with raw citations for the weight, as MVP. This just means total citations over the set of publications.
- Cumulative citation-weighted publications
  - Measures the size of the field I guess. Makes sense. The bigger the field, the more citations you should expect. Wait, that's not necessarily true. There's competing forces: number of people,

# 2023-May-31

## Regression modeling

- Running regression on year's citation-weighted publications as a function of cumulative citation-weighted publications and number of researchers.
  - Inputs: 2012 to 2021
  - Outputs: 2013 to 2022
  - Limitations
    - Small sample
    - Citations are for the AI concept, while authors are for AI|ML
  - Result

```
OLS Regression Results
Dep. Variable:	y	R-squared:	0.966
Model:	OLS	Adj. R-squared:	0.956
Method:	Least Squares	F-statistic:	98.13
Date:	Wed, 31 May 2023	Prob (F-statistic):	7.58e-06
Time:	15:07:38	Log-Likelihood:	23.595
No. Observations:	10	AIC:	-41.19
Df Residuals:	7	BIC:	-40.28
Df Model:	2		
Covariance Type:	nonrobust		
coef	std err	t	P>|t|	[0.025	0.975]
const	4.0563	0.205	19.769	0.000	3.571	4.541
x1	-0.0012	0.060	-0.020	0.985	-0.144	0.142
x2	0.7216	0.127	5.680	0.001	0.421	1.022
Omnibus:	0.231	Durbin-Watson:	1.687
Prob(Omnibus):	0.891	Jarque-Bera (JB):	0.276
Skew:	-0.264	Prob(JB):	0.871
Kurtosis:	2.381	Cond. No.	214
```

    - Looks like a good fit based on R-squared
    - But x1 (cumulative citation-weighted publications) seems to basically explain nothing. This is confusing to me.
    - OTOH, x2 (number of researchers) seems very explanatory.
    - Let's plot the predictions.
  - Predictions
    - I mean...this just doesn't seem that informative.
    - Yes, the model can predict fairly well.
    - But I feel like this just reduces to "yep, you can express one linear function as a linear transformation of some other linear function".
    - Number of researchers is roughly log-linear; citation-weighted publications is roughly log-linear. It then seems unremarkable that you can predict one from the other.
    - What would be more interesting is if the inputs followed a less smooth trajectory, and the output was still predictable then.
    - 
