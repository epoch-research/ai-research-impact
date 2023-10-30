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

# 2023-Jun-02

Same regression as before but per company

- I'll start with just one company, and then I can extend this to iterate over companies.
- It's going to be a bit tricky to handle all the results, esp. if we want to do abalations.
- Ok I need to migrate everything to DataArrays. Don't want to propagate this inconsistency any longer.
- Hmm, regression on Google citations in 3y window is poor. BIC=19.35, R^2 0.16.
- I think the choice of metric is problematic. The 3y window means we get that dropoff after 2018. 
- I should try the cited-by count by year for the institution.
  - Problem with this is it's not limited to AI.
  - Ok. So what do we need to do?
    - For each AI work by Google, look at the counts by year.
    - Put the count for each year into the bucket for each year.
  - How is that different to what's currently done, using a 0-year window?
    - Right now the "buckets" are _publication_ year. Instead, we just want the year that the citations occurred.
- Ok, with new citations each year, it's a much better fit: BIC=-5.060, R^2=0.95.
  - Interesting that this fit puts about equal weight on the citations in the whole AI field. Whereas the global fit put zero weight on it.
- I'd be curious to try citations by publication year with a smaller window though. 1 year or 0 years.
- Removing 2022
- Citations in publication year: BIC -10.55, R^2 0.97
- New citations from any publication: BIC -24.56, R^2 0.995

Is it appropriate to compare BIC across different choices of input data?

- According to GPT-4, not really. 

Hmm... I just realised, new citations from any work per year isn't a measure of citation-weighted works anymore.

- Yet this appears to be more predictable from the number of researchers than citation-weighted works is.
- Partly it could just be the data staleness issue.
- But I wouldn't actually expect a better fit between researchers and new citations. New researchers shouldn't cause new citations from works that pre-date those new researchers.
- Rather, new researchers should be associated with _future_ citations. That's why I'd expect a better fit with works published that year, weighted by the future citations of those works.

Fitting researchers -> new citations for all selected institutions

```
Meta (United States): R^2=0.83, w1=1.13
Google (United States): R^2=0.96, w1=2.03
Massachusetts Institute of Technology: R^2=0.97, w1=3.01
Microsoft (United States): R^2=0.65, w1=2.54
Chinese Academy of Sciences: R^2=0.96, w1=2.77
```

- OpenAI errors, I think that's because I don't have data for all the years
- DeepMind also errors though. I wouldn't expect that. Should look into it later.
- Some fits are good (Google, MIT, CAS), while others are bad (Meta, and especially MS).
  - With Meta, if I eyeball the plots I already had for author count, and future citations, they look more correlated than this.
  - With MS, it's not so clear.
- Let's try switching to future citations (0-year window).

```
Meta (United States): R^2=0.69, w1=1.10
Google (United States): R^2=0.85, w1=1.65
Massachusetts Institute of Technology: R^2=0.92, w1=2.24
Microsoft (United States): R^2=0.77, w1=2.30
Chinese Academy of Sciences: R^2=0.99, w1=2.69
```

- Well that didn't go as expected.
- Visually inspecting, Meta didn't go how I expected because I was matching up the data in the _same_ year. Whereas this is supposed to predict the next year.
- Did Jaime in fact intend to predict the next year? Or was he thinking of the same year?
- The thing is, you'd expect a correlation between the number of researchers that you found in a set of works, and the citation-weighted number of works. The fewer works you found, the fewer unique authors you expect to find.
  - Again, makes me wonder if there's really anything interesting to be gleaned here.
  - I guess the relationship between them is still interesting - the log-scaling factor between them. That's the `w1` above. Suggests that for Google, the addition of one researcher results in (x+1)^1.65 - x citations. So from 1 to 2 gets you 2.1 more citations, 2 to 3 gets you 3 more citations, 3 to 4 gets you 3.7 more citations, 4 to 5 gets you 4.4 more citations, and so on. If you 2x your researchers, you 3.1x your citations.

# 2023-Jun-05

Testing whether Google Scholar can feasibly help improve our citation data (esp. in 2022).

- Trying out the python package, `scholarly`
- With proxy: 
  - Proxy might not be important if I just call `search_authors`
  - I stopped it after 21 minutes
  - 18 works in 21 minutes - that's intractable. Thousands of hours.

```
 67%|██████▋   | 18/27 [16:52<08:26, 56.24s/it]
  0%|          | 0/10 [21:06<?, ?it/s]
```

- Without proxy: 264 seconds to get through 140 works - about 2 seconds per work.
  - It seems like most of the time is taken up by getting the author data. The publication progress bar completes ~instantly based on one observation.
  - Hmm, but the time estimate from tqdm suggests it is taking time... am I just not using tqdm correctly here?
  - Perhaps I should use `tqdm.notebook`.

```
100%|██████████| 27/27 [01:40<00:00,  3.72s/it]
 10%|█         | 1/10 [01:52<16:48, 112.06s/it]
```

- Anyway, let's assume we can do 2 seconds per work on average.
- We have ~100,000 works to get through. Probably more when we add more institutions.
- 100,000 * 2 = 200,000 seconds. That's about 56 hours.
  - Well, it's not out of the question.
  - Might take a week, ultimately.
- `MaxTriesExceededException` happened. We'd need a way to handle that.
  - Unless proxies avoid this?
- Also, this time it was 382 works in about 26 minutes. That's about 4.1 seconds per work.

```
100%|██████████| 27/27 [01:40<00:00,  3.72s/it]
100%|██████████| 113/113 [07:00<00:00,  3.72s/it]
100%|██████████| 35/35 [02:14<00:00,  3.83s/it]
100%|██████████| 25/25 [01:34<00:00,  3.77s/it]
100%|██████████| 156/156 [09:45<00:00,  3.75s/it]
  9%|▊         | 26/301 [02:01<21:21,  4.66s/it]
 70%|███████   | 7/10 [26:01<11:09, 223.13s/it]
---------------------------------------------------------------------------
MaxTriesExceededException                 Traceback (most recent call last)
Cell In[9], line 17
     15     num_works += len(author_works)
     16     for work in tqdm(author_works):
---> 17         work_filled = scholarly.fill(work)
     18         cites_per_year = work_filled['cites_per_year']
     20 print(f"took {time.time() - t0} seconds to process {num_works} works: average {num_works / (time.time() - t0)} works per second")

File ~/miniconda3/envs/epoch/lib/python3.11/site-packages/scholarly/_scholarly.py:238, in _Scholarly.fill(self, object, sections, sortby, publication_limit)
    236 elif object['container_type'] == "Publication":
    237     publication_parser = PublicationParser(self.__nav)
--> 238     object = publication_parser.fill(object)
    239 return object

File ~/miniconda3/envs/epoch/lib/python3.11/site-packages/scholarly/publication_parser.py:278, in PublicationParser.fill(self, publication)
    276 if publication['source'] == PublicationSource.AUTHOR_PUBLICATION_ENTRY:
    277     url = _CITATIONPUB.format(publication['author_pub_id'])
--> 278     soup = self.nav._get_soup(url)
    279     publication['bib']['title'] = soup.find('div', id='gsc_oci_title').text
    280     if publication['bib']['title'][-1] == '\u2026':

File ~/miniconda3/envs/epoch/lib/python3.11/site-packages/scholarly/_navigator.py:239, in Navigator._get_soup(self, url)
    237 def _get_soup(self, url: str) -> BeautifulSoup:
    238     """Return the BeautifulSoup for a page on scholar.google.com"""
...
    188     return self._get_page(pagerequest, True)
    189 else:
--> 190     raise MaxTriesExceededException("Cannot Fetch from Google Scholar.")

MaxTriesExceededException: Cannot Fetch from Google Scholar.
```

- Is this tractable? It's borderline. We'd have to execute one clean run to get the data.
- I could limit to 2022 but then I'm concerned about the mismatch between OpenAlex and Scholar data.
  - Why don't we make a comparison? Grab like 100 works and compare the citation counts.
  - Consider: if the citation counts are similar enough in previous years, we could cut the runtime we need by ~90%. It would only take a day and then it would be tractable.
- The original prompt from David was actually just about DM and OAI, which is a very small number of works: "Using google scholar scraper to cross-check DeepMind and OAI (because they have a small number of works)"

Comparing citation counts of OpenAlex and Google Scholar

- Taking a random sample of the works that I saved for the selected institutions.
  - Limitation: the first search result on Google Scholar won't necessarily match
  - Takes a long time to query Google Scholar. I'm using the proxy. 5 minutes and it's only on the 4th work.
  - In contrast, 18 seconds for 10 works without the proxy.
  - Ok, from a sample of 10, I get:
    - Mean signed error: 14.4
    - Mean absolute error: 14.4
    - Mean squared error: 24.2
    - Mean relative error (excluding the two zero values): 3.27
  - Now I keep hitting 'MaxTriesExceededError`. That's what the proxy is for...
    - But it backs off. If I wait a few minutes I can query again.
- What about the first twenty sequentially? These are the top-cited, or at least tend to be highly cited, and that's where most of the weight is going to come from in my analysis.
  - Ok, managed to get the first ten before max tries error.
  - Mean relative error: 2.94x
  - Std of relative error: 2.24x

Overall take:

- Scholar citations differ drastically (~3x larger on average, with high variance). So it's problematic to mix the two.

Tangent: ratio of references mentioning ImageNet to references not mentioning ImageNet (in the Abstract), for papers that mention ImageNet. Tamay seemed interested in this from the WiP today.

```python
import numpy as np
from numpy.random import default_rng
import pickle
import pyalex
from pyalex import Authors, Concepts, Institutions, Works
from scholarly import scholarly
from scholarly import ProxyGenerator
import tqdm


def merge_sample(query, sample_size=1000, seed=None):
    sampler = query.sample(sample_size, seed=seed)
    items = []
    for i in range(int(np.ceil(sample_size / 200)) + 1):  # 200 is the max page size
        page = sampler.get(per_page=200, page=i+1)
        items.extend(page)
    return items

# The polite pool has much faster and more consistent response times. To get into the polite pool, you set your email:
pyalex.config.email = "ben@epochai.org"

data_file_location = 'data/'

SEED = 20230105
rng = default_rng(seed=SEED)

works_sample = merge_sample(
    Works().search_filter(abstract="imagenet"),
    sample_size=1000,
    seed=SEED,
)

imagenet_papers = 0
imagenet_count = 0
non_imagenet_count = 0
null_count = 0
for work in tqdm.tqdm(works_sample):
    inv_idx = work['abstract_inverted_index']
    if inv_idx is None:
        continue
    if 'ImageNet' in inv_idx.keys():
        imagenet_papers += 1
        for referenced_work_id in work['referenced_works']:
            referenced_work = Works()[referenced_work_id]
            referenced_inv_idx = referenced_work['abstract_inverted_index']
            if referenced_inv_idx is None:
                null_count += 1
            else:
                if 'ImageNet' in referenced_work['abstract_inverted_index'].keys():
                    imagenet_count += 1
                else:
                    non_imagenet_count += 1
```

- Old result that randomly sampled 10,000 papers from the "AI papers by selected institutions" dataset (N.B. only 70 of those papers mentioned ImageNet):

```python
print(imagenet_papers, imagenet_count, non_imagenet_count, null_count)
70 326 1224 54
```

  - Ratio: 326 / (326 + 1224) = 21%

- New result with 200 papers that have "ImageNet" in the abstract (execution was interrupted on 1000 papers, but I think it's valid data at any point in time):

```
print(imagenet_papers, imagenet_count, non_imagenet_count, null_count)
200 650 2546 202
```

  - Ratio: 650 / (650 + 2546) = 20%

- Full sample of 1000, matching "imagenet" on lower-cased abstract: 649 2226 8579 585. 
  - Huh. So still only 649 out of 1000. 404 errors perhaps? Unclear.
  - 2226 / (2226 + 8579) = 21%.
- The 20% result looks pretty robust.

# 2023-Jun-06

Plotting histograms of citations by institution

# 2023-Jun-07

Plotting histograms of citations by institution

- What was this for again?
  - Getting an idea of different institutions' different strategies (a few highly cited papers vs lots of less cited ones).
  - Just a base sense of what the distribution of citations looks like.
- David asks: Can you do it more like a kdeplot per institution?

====
Papers with no abstract inverted index available: 0
Papers with ImageNet in the Abstract inverted index: 1000
Mean fraction of references mentioning ImageNet: 0.26
Std fraction of references mentioning ImageNet: 0.19

Papers with no Abstract available: 0
Papers with ImageNet in the Abstract: 1000
Mean fraction of references mentioning ImageNet in the Abstract: 0.26
Std fraction of references mentioning ImageNet in the Abstract: 0.19

# 2023-Jun-14

Ranking institutions

- Explained method in Slack

```
Google: 26.7%
Microsoft: 17.1%
Meta: 11.4%
DeepMind: 9.4%
OpenAI: 5.3%
Amazon: 4.2%
Huawei: 3.5%
Alibaba: 3.4%
Tencent: 2.3%
Baidu: 2.2%
Tata Consultancy Services: 1.8%
China Mobile: 1.7%
NVIDIA: 1.7%
Adobe Systems: 1.7%
Decision Systems: 1.4%
Aditya Birla: 1.3%
Management Sciences: 1.2%
Aselsan: 0.9%
Stability: 0.4%
Twitter: 0.4%
Runway: 0.4%
Netflix: 0.4%
Megvii: 0.4%
Xerox: 0.4%
Salesforce: 0.4%
```

# 2023-Jun-15

Ranking institutions

- Should I download all the works of the 200 institutions?
- The point would be to filter out low-cited works. Like less than 10 citations.
  - Could probably do that at the fetching stage.
- I think these companies don't have as many works as MIT + CAS. It might be manageable.
- About 4 minutes for the top 10 institutions by works count
  - So worst case would be 10 times that, 40 minutes.
  - 1000 institutions would be 400 minutes worst case. 
- There's an error when I try to do 100 institutions.
- DM and OAI are in the top 100 companies by citation count. So that should suffice.
- I think I should select the initial pool of institutions by citation count and then filter after.
- How many should I start with? To be safe I want to end up with a top 20, max.
  - I'm going to filter by recency (>= 2010) and non-trivial citations (>= 10)
    - Just checking: i10-index is "at least 10 citations", so it is >=10 https://guides.library.cornell.edu/c.php?g=32272&p=203393
  - 200 seems safe.
- When I use 200 institutions I get

```
HTTPError: 400 Client Error: Bad Request for url: https://api.openalex.org/works?filter=authorships.institutions.id:https://openalex.org/I1283103587%7Chttps://openalex.org/I1291425158%7Chttps://openalex.org/I1290206253%7C [and so on]
```

- 10 institutions works. Is there a limit to the number of institutions in the disjunction, or is it a bad URL, or is the format causing an error?
- I can test the institutions one-by-one to see if there's a bad URL
  - No error
- Testing subsets of the institutions
  - 10: PASS
  - 100: FAIL
  - 50: PASS
  - 99: FAIL
  - 60: FAIL
    - There we are:

```
QueryError: Maximum number of values exceeded for authorships.institutions.id. Decrease values to 50 or below, or consider downloading the full dataset at https://docs.openalex.org/download-snapshot
```

- So I could just download each slice and merge. Quite easy because it is just a list.
- Download looks like a success!

## New ranking

- At least 10 citations (already filtered)
- Rank institutions by their citations per ~~author~~ publication over the entire period?
  - I.e. total citations on works in the period, divided by total authors that are unique to the entire period
  - Or, should I just do citations per publication? Yeah, I think that's simpler.
- New list

```
Quansight (United States): 8353.8125
Enthought (United States): 8258.392857142857
Google (United Kingdom): 936.1561822125814
DeepMind (United Kingdom): 561.7433206106871
Magic Leap (United States): 457.55
Google (Switzerland): 209.47852760736197
Meta (Israel): 156.28400780107265
Twitter (United States): 120.97025171624713
Brain (Germany): 120.55371900826447
Google (United States): 117.81490469989345
Meta (United States): 115.91536748329621
Nvidia (United Kingdom): 103.94866310160428
Microsoft Research (United Kingdom): 79.06314774644493
Group Sense (China): 76.76696542893725
Intel (Israel): 71.07368421052631
Nvidia (United States): 67.42679127725857
Baidu (China): 63.36908077994429
Amazon (Germany): 62.11317567567568
Microsoft Research Asia (China): 61.20832169784976
Amazon (United States): 55.60176991150443
Huawei Technologies (Sweden): 54.59508196721311
NEC (United States): 53.99588477366255
Intel (United States): 51.47703464947623
```

- Hmm
- Quansight and Enthought don't seem right. I've never heard of them.
- I mean, they could be legit.
- I feel like I should have a threshold on the number of publications.

```
Google (United Kingdom): 936.1561822125814
DeepMind (United Kingdom): 561.7433206106871
Google (Switzerland): 209.47852760736197
Meta (Israel): 156.28400780107265
Twitter (United States): 120.97025171624713
Brain (Germany): 120.55371900826447
Google (United States): 117.81490469989345
Meta (United States): 115.91536748329621
Nvidia (United Kingdom): 103.94866310160428
Microsoft Research (United Kingdom): 79.06314774644493
Group Sense (China): 76.76696542893725
Nvidia (United States): 67.42679127725857
Baidu (China): 63.36908077994429
Amazon (Germany): 62.11317567567568
Microsoft Research Asia (China): 61.20832169784976
Amazon (United States): 55.60176991150443
Huawei Technologies (Sweden): 54.59508196721311
NEC (United States): 53.99588477366255
Intel (United States): 51.47703464947623
Jingdong (China): 50.287090558766856
Willow Wood (United States): 48.323076923076925
Adobe Systems (United States): 48.31728045325779
Management Sciences (United States): 45.98395721925134
Microsoft (United States): 44.159808835528615
Tencent (China): 43.87391455366447
```

- What is Willow Wood?
  - One of the papers lists it as Willow Garage, which developed Robot Operating System (ROS).
- I'm again feeling like I should limit to Machine Learning.
  - Done. Only 10636 works.
- This looks pretty on-point:

```
Google (United Kingdom): 1735.602510460251
DeepMind (United Kingdom): 875.7429078014185
Microsoft Research (United Kingdom): 134.41444866920153
Google (United States): 117.09986431478968
Meta (Israel): 108.39317319848293
Meta (United States): 106.97165991902834
Naver (South Korea): 93.8896103896104
Nvidia (United Kingdom): 93.4968944099379
Uber AI (United States): 82.41
NEC (United States): 73.67796610169492
Group Sense (China): 68.96969696969697
Nvidia (United States): 58.849840255591054
Adobe Systems (United States): 54.38054607508533
Baidu (China): 50.42124542124542
Microsoft Research Asia (China): 50.24925816023739
Huawei Technologies (China): 49.14693877551021
Amazon (Germany): 47.5945945945946
Tencent (China): 45.61834561834562
Huawei Technologies (Sweden): 43.93700787401575
Alibaba Group (China): 43.57687420584498
Microsoft (United States): 42.725121781489214
Alibaba Group (United States): 39.65384615384615
Jingdong (China): 38.743718592964825
LinkedIn (United States): 37.40397350993378
Amazon (United States): 36.41914191419142
```

- Still wonder if I should threshold 1000 pubs. Currently at 100.
- Nah, I shouldn't. There's only 30.

New rankings:

```
1. DeepMind: 30.9%
2. Google: 21.3%
3. Meta: 10.8%
4. Microsoft: 5.7%
5. OpenAI: 5.3%
6. NVIDIA: 2.7%
7. Naver: 2.3%
8. Baidu: 2.1%
9. Uber: 2.0%
10. Alibaba: 1.9%
11. NEC: 1.8%
12. Group Sense: 1.7%
13. Amazon: 1.4%
14. Adobe Systems: 1.3%
15. Huawei: 1.2%
16. Tencent: 1.1%
17. Jingdong: 0.9%
18. LinkedIn: 0.9%
19. Dascena: 0.9%
20. Yahoo: 0.5%
21. Tata Consultancy Services: 0.4%
22. Stability: 0.4%
23. Twitter: 0.4%
24. Runway: 0.4%
25. Netflix: 0.4%
26. Megvii: 0.4%
27. Salesforce: 0.4%
28. Xerox: 0.4%
```

- Feel like this is worse.
- Feel like I _should_ account more for scale rather than just efficiency.
- Differences in top 10:
  - Before: Tencent, Huawei, Amazon 
  - Now: NVIDIA, Naver, Uber
- Trying just citations, not averaged

```
1. Google: 37.1%
2. DeepMind: 24.8%
3. Meta: 11.7%
4. Microsoft: 9.5%
5. OpenAI: 5.3%
6. Alibaba: 1.6%
7. NVIDIA: 1.6%
8. Baidu: 1.5%
9. Amazon: 1.0%
10. Tencent: 0.9%
11. Huawei: 0.5%
12. Adobe Systems: 0.5%
13. Stability: 0.4%
14. Twitter: 0.4%
15. Runway: 0.4%
16. Netflix: 0.4%
17. Megvii: 0.4%
18. Salesforce: 0.4%
19. Xerox: 0.4%
20. Group Sense: 0.3%
21. Naver: 0.2%
22. Yahoo: 0.1%
23. NEC: 0.1%
24. Uber: 0.1%
25. Jingdong: 0.1%
26. LinkedIn: 0.1%
27. Dascena: 0.1%
28. Tata Consultancy Services: 0.0%
```

- Looks more appropriate to me
- Still a question around Huawei.
- As one more variation I'll try including all ML systems in the PCD database, not just notable systems.
- You know what, I don't have enough time. Leaving it.

## Updating data processing with new institutions

- **Also limiting to the Machine Learning concept**
- Citation histogram
  - Hmm. Before, OpenAI had more citations in the 100 - 999 range than DeepMind. Now it has less than DeepMind.
  - This makes me question just using ML pubs.
  - Let me investigate which OpenAI works are tagged AI vs. ML.
  - I think it would be fair to select institutions by ML only (due to noise in AI tag), but then once we've narrowed down the top ML-focused institutions, it's reasonable to include AI pubs because those AI pubs are more likely still about cutting-edge ML.
  - OpenAI and DeepMind are good ones to test because they are focused on AGI.
- Ok, after looking at what is tagged AI vs. ML for OpenAI and DeepMind, I'm convinced that we should include the AI tag. There are lots of important, highly-cited works that are tagged AI but not ML.

DeepMind - AI but not ML:

```
Distilling Policy Distillation: 17
Meta-learning in natural and artificial intelligence: 34
A probabilistic approach to demixing odors: 51
High Fidelity Speech Synthesis with Adversarial Networks: 52
Computations Underlying Social Hierarchy Learning: Distinct Neural Mechanisms for Updating and Representing Self-Relevant Information: 104
Distilling Policy Distillation: 15
Applying and improving <scp>AlphaFold</scp> at <scp>CASP14</scp>: 137
Cross-Lingual Word Embeddings: 15
Deep Reinforcement Learning for Tactile Robotics: Learning to Type on a Braille Keyboard: 14
Mental labour: 105
Sample-efficient adaptive text-to-speech: 31
Massively Parallel Video Networks: 23
The NarrativeQA Reading Comprehension Challenge: 19
Protein complex prediction with AlphaFold-Multimer: 636
Agent57: Outperforming the Atari Human Benchmark: 46
Efficient Neighbourhood Consensus Networks via Submanifold Sparse Convolutions: 46
Placing language in an integrated understanding system: Next steps toward human-level performance in neural language models: 36
Decoupled neural interfaces using synthetic gradients: 100
Deep Learning with Dynamic Spiking Neurons and Fixed Feedback Weights: 60
Grounded Language Learning Fast and Slow: 12
Exact sampling of determinantal point processes with sublinear time preprocessing: 23
Cross-View Policy Learning for Street Navigation: 16
Piano Genie: 22
People construct simplified mental representations to plan: 10
Toward a universal decoder of linguistic meaning from brain activation: 175
...
Recurrent Neural Network Transducer for Audio-Visual Speech Recognition: 45
Convolutional Neural Network Architecture for Geometric Matching: 347
The Lipschitz Constant of Self-Attention: 19
Temporal Query Networks for Fine-grained Video Understanding: 22
```

Bug

- I think I just noticed a bug. I cleaned up the `OpenAlexProcessor` and I was looking at the individual citations and noticed heaps of duplication.
- So then I realised: is it appending the citation count repeatedly for every author x affiliation on the paper? I think so.
  - Not certain if this bug was present in the previous code but I'm pretty sure it was.
- This is an output of the old code - the problem is there too:

```
> institution_cited_by_distribution
defaultdict(list,
            {'Meta': array([9052,  409,  940, ...,  242,   36,   21]),
             'Google': array([9052, 6655, 6655, ...,   17,   13,   13]),
             'OpenAI': array([4964,  498,  241,   18,   18,   11,   11,   67,   67,   62,   62,
                      35, 4964, 2012,  498, 1274,  700,  700,  700,  700,  700,  700,
                     674,  674,  674,  674,  674,  674,  674,  674,  674,  674,  674,
                     674,  674,  674,  674,  674,  725,  725,  725,  725,  725,  725,
                     725,  725,  725,  725,  725,  725,  725,  725,  725,  725,  451,
                     451,  451,  451,  319,  319,  319,  241,  197,   85,  108,   81,
                     132,  132,   90,   72,   72,   72,   72,   72,   72,   72,   65,
                      83,   83,   83,   83,   83,   40,   58,   67,   67,   63,   62,
                      62,   57,   57,   57,   57,   57,   56,   40,   29,   35,   17,
                      24,   26,   24,   17,   21,   18,   18,   12,   14,   13,   11,
                      10,   11,   72,   72,   72,   72,   72,   72,   72,   13,   13,
                      13]),
             'DeepMind': array([4592, 4592, 4592, ...,   10,   75,   75]),
             'Microsoft': array([872,  85,  85, ...,   9,  10,  10]),
             'Amazon': array([6842,  455,  267, ...,   20,   17,   12]),
             'Baidu': array([153, 153, 153, ...,  10,  10,  10]),
             'Nvidia': array([205, 205, 205, ...,  40,  40,  34]),
             'Tencent': array([116, 116,  70, ...,   9,   9,   9]),
             'Alibaba': array([10, 19, 16, ..., 13, 13, 12])})
```

- The difficulty to fix this is that we need the institution name (which is inside the authorship x institution loops) before adding the citation count.
- Is there a way we can know whether the count has already been added for this institution?
- We _do_ want to add the same citation count to _different_ institutions.
- So I think the problem is when multiple authors have the same affiliation.
- Using a dictionary to flag which institutions have had citations added, for each work.
- Cool.
- Repetition has been greatly reduced:

```
{'Meta': array([9052,  312,  282, ...,    5,    5,   18]),
 'Google': array([9052, 6655, 3124, ...,   14,   17,   12]),
 'OpenAI': array([4964, 4964, 1274,  700,   85,   65,   40,   40,   17,   17,  498,
         498,  241, 2012,  451,  319,  241,  197,  108,   81,   90,   72,
          58,   29,   72,   18,   67,  674,   67,   18,   14,   11,   62,
          83,   62,   57,   56,   13,   11,   10,   13,   13,   13,   11,
          11,   62,   35,  725,  132,   62,   35,   24,   26,   24,   21,
          63,   12]),
 'DeepMind': array([4592,  164,  259,   40,   11,   11,    8, 4592,  550,  467,  188,
         159,  101,   41,   27,   36,   31,   32,   25,    2,   15,   10,
        4592,  550,  164,  467,  259,  188,  159,  167,   89,  101,   23,
          41,   27,   40,   36,   31,   29,   32,   25,   23,   34,   25,
           2,   15,   10,   11,   11,    9,    8,   64,   91,   13,   11,
        3388,   47,   16,   15, 3388,   64,   91,   47,   16,   10,   15,
          13,   11,    9,    9, 1182,  105,   94,   89,   63,   62,   52,
          52,   50,   46,   36,   32,   31,   31,   27,   24,   24,   21,
          20,   19,   19,   17,   12,   12,   11,   10, 1182,  127,  101,
          42,   14,  348,  117, 1782, 1321, 1182,  621,  387,  348,  320,
         279,  223,  204,  203,  180,  127,  129,  126,  117,  105,  101,
          98,   94,   90,   89,   85,   63,   62,   55,   52,   52,   52,
          50,   50,   46,   46,   44,   42,   39,   37,   36,   36,   35,
          33,   33,   32,   31,   31,   31,   30,   27,   27,   27,   25,
          24,   24,   24,   22,   21,   20,   19,   18,   19,   18,   17,
          17,   17,   17,   16,   16,   15,   15,   15,   14,   13,   13,
          12,   12,   12,   12,   12,   12,   12,   12,   11,   11,   11,
...
          28,   14,   11,   12,    5,    5,    6,    0,    9,   18,    5,
           2,   25,   37,   23,   10,    8,    7,    7,    9,   25,   14,
          13,   20,    5,    4,   11]),
 'Tencent': array([116,  27,  17, ...,   4,  12,  12]),
 'Alibaba': array([10, 30, 10, ..., 19, 18,  6])}
 ```

 - ...but there's still a bit of suspicious repetition e.g. OpenAI with 4964 twice. 
  - This could be due to duplicate works. I've already seen duplicate works when listing OpenAI's papers.
  - If this is right, then we'd have to go one step further and do some (fuzzy) string matching in order to de-duplicate.
  - The suspicious repetition isn't generally adjacent, it can appear after several other counts.
- Check for repeated IDs in the dataset
  - Yes:

```
> len(works)
19988
> len(set([work['id'] for work in works]))
17957
```

- My guess is that the disjunction of the institutions means OpenAlex fetches duplicates. And duplicates exist because sometimes these top 10 institutions collaborate.
- Ok, let's try removing duplicate works.
- Done.
- Looks good now:

```
{'Meta': array([9052,  312,  282, ...,   11,    1,    5]),
 'Google': array([9052, 6655, 3124, ...,   11,    9,   12]),
 'OpenAI': array([4964, 1274,  700,   85,   65,   40,   40,   17,   17,  498,  241,
        2012,  451,  319,  197,   81,   90,   72,   58,   29,   18,   67,
         674,   14,   11,   83,   57,   56,   13,   10,   62,   35,  132,
          24,   26,   24,   21,   63,   12]),
 'DeepMind': array([4592,  164,  259,   40,   11,    8,  550,  467,  188,  159,  101,
          41,   27,   36,   31,   32,   25,    2,   15,   10,  167,   89,
          23,   29,   23,   34,   25,    9, 1182,  105,   89,   63,   62,
          52,   52,   50,   46,   36,   32,   31,   31,   27,   24,   24,
          21,   20,   19,   19,   17,   12,   11,   10,  127,  101,   42,
          14,  348,  117, 1782, 1321,  621,  387,  320,  279,  223,  204,
         203,  180,  129,  126,   98,   90,   85,   55,   52,   50,   46,
          44,   39,   37,   35,   33,   33,   31,   30,   27,   27,   25,
          24,   22,   18,   18,   17,   17,   17,   16,   16,   15,   15,
          15,   13,   13,   12,   12,   12,   12,   12,   12,   11,   11,
          10,   10,   10,   10,  500,  120,  135,  105,   89,  118,   67,
          78,   47,   45,   27,   22,  267,  122,   95,   54,   36,   19,
          27, 3158, 2175, 1169,  376,  261,  230,  185,  192,  190,  228,
         141,  129,  132,  104,   98,   92,   46,   78,   73,   35,   70,
          65,   47,   50,   45,   29,   52,   39,   40,   41,   43,   32,
          31,   30,   31,   26,   18,   18,   16,   16,    7,   11,   10,
          11,  593,  428,  212,  155,  148,  118,   41,   34,   30,   34,
          25,   22,   17,   17,   17,   16,   14,   15,   14,   13,   12,
          11,   11,   10,   82,   56,   37, 1443,  654,  552,  403,  302,
...
         15,  16,  13,  14,  12,  12,  78,  12,  27,  10,  10,  20,  20,
         12,   5,   6,  49,   7,  33,  27,  26,  21,  16,  14,  14,  12,
         12,  10,  11,  11,  11,  11,   9,  10,   9,  10,  10,   9,  38,
         35,  22,  19,  18,  14,  12,  13,  10,   9,  18,  28,  19,  18,
          6])}
```

## Process all Machine Learning papers?

- The i10-index of the Machine Learning concept is only about 600K.
  - I think that would make calculating future citations of works each year tractable.
    - Previously I was only considering citations of past works for the concept of Artificial Intelligence.
  - In fact, it might even make FWCI tractable, though that might be pointless.
    - Nah, FWCI still has to consider all the other fields. 

## Ranking

New rankings after bug fixes discussed above:

```
1. Google: 33.2%
2. Microsoft: 13.7%
3. Meta: 13.5%
4. DeepMind: 12.9%
5. OpenAI: 5.3%
6. Alibaba: 2.1%
7. Baidu: 2.0%
8. NVIDIA: 1.6%
9. Tencent: 1.5%
10. Amazon: 1.5%
11. Adobe Systems: 1.2%
12. Huawei: 1.0%
13. Group Sense: 0.6%
14. https://openalex.org/I4210148872: 0.6%
15. Naver: 0.5%
16. Megvii: 0.4%
17. Twitter: 0.4%
18. Runway: 0.4%
19. Stability: 0.4%
20. Salesforce: 0.4%
21. Xerox: 0.4%
22. Netflix: 0.4%
23. Yahoo: 0.3%
24. Jingdong: 0.3%
25. NEC: 0.2%
...
```

- Same top 10, different order.
- There's more aliasing I could have done but I think this is good enough.
  - Could consider using GPT spreadsheet-style

# 2023-Jun-16

Unit tests for OpenAlexProcessor

- Found a bug where if there are any spurious citation counts before the publication year (which there often are)
- Also noticed that yearly counts seem to never be before 2012. This is problematic for measuring works and citations prior to 2012.
  - And yet I have counted many citations in 2010 and 2011, for most institutions.
  - But the three year window might be enough to capture that.
  - **We should see what happens to 2010 and 2011 with a 0-year bound.**

## Data quality issues

- Can confirm: OpenAlex includes arXiv papers because it includes the "Language models are few-shot learners" arXiv paper.
- GPT-3 paper has no OpenAI affiliations! So it doesn't get included in my processed data at all.
  - Could we rectify this by looking people up?
  - E.g. Match display name => search that name => consolidate to the most relevant search result
  - Ok let's try an example.
    - Tom Brown
      - University of Oxford. Dang.
    - OpenAI doesn't appear in first 25 search results for Tom Brown.
    - Ok probably not a great first choice because it's such a common name.
  - Girish Sastry
    - That's a hit. OpenAI is the last known institution.
    - Ok so maybe we could search, and if their last known institution is one of the aliases, go with that search result.
  - Problem is, the Author object only has their last known institution, rather than the institution at the time.
    - Ok so that's bad...
  - What if we have a step after the initial processing...
    - Go through the works again
    - If an author name is already in `author_names_data`, then we can infer that they belonged to the given institution in the given year where we found that name.
    - But the only way that would happen is if that author published another paper that year, where there affiliation was included.
- There is a lot of author duplication!
  - Could search for the author and consolidate to the first search result
    - Maybe needs additional checks for common names - check that they've published in Artificial Intelligence?
    - I don't think there's any way to be sure that you've found duplicates.
    - But I think it's more important to _not_ have duplicate names for each institution, than it is for the Author ID to correspond to the actual person.
  - OOPS. This was mostly due to a bug. There's actually only about 5% duplication.

```
> institution_author_name_data['OpenAI'][2018]
['Rafal Jozefowicz',
 'Phillip Isola',
 'Xue Bin Peng',
 'Marcin Andrychowicz',
 'Wojciech Zaremba',
 'Pieter Abbeel',
 'Bob McGrew',
 'Marcin Andrychowicz',
 'Wojciech Zaremba',
 'Phillip Isola',
 'Harrison Edwards',
 'Pieter Abbeel',
 'Josh Tobin',
 'Marcin Andrychowicz',
 'Bob McGrew',
 'Alex K. Ray',
 'Jonas Schneider',
 'Peter Welinder',
 'Wojciech Zaremba',
 'Phillip Isola',
 'Jonathan Raiman']
```

- Implementing consolidate-to-first-author-encountered solution
- Looks good

```
Amazon: 1284 authors, 1284 unique authors (0.00% duplication)
Microsoft: 7562 authors, 7562 unique authors (0.00% duplication)
Nvidia: 921 authors, 921 unique authors (0.00% duplication)
OpenAI: 80 authors, 80 unique authors (0.00% duplication)
Tencent: 1360 authors, 1360 unique authors (0.00% duplication)
DeepMind: 1021 authors, 1021 unique authors (0.00% duplication)
Alibaba: 1571 authors, 1571 unique authors (0.00% duplication)
Meta: 2327 authors, 2327 unique authors (0.00% duplication)
Baidu: 1105 authors, 1105 unique authors (0.00% duplication)
Google: 8252 authors, 8252 unique authors (0.00% duplication)
```

# 2023-Jun-22

## Measuring OpenAlex data lag

### OpenAlex snapshots

Taking stock

- https://docs.openalex.org/download-all-data/openalex-snapshot 
- When are snapshots dated?
  - Updated about once per month
  - https://github.com/ourresearch/openalex-guts/blob/main/files-for-datadumps/standard-format/RELEASE_NOTES.txt
  - First release: RELEASE 2022-01-02
    - Possibly not a complete snapshot, or not as complete as the later snapshots. Something to investigate.
    - This is good news if the snapshot is complete enough. We have more than one year to backtrack to.
  - But in the actual S3 bucket, author snapshots only go back to March 2023: https://openalex.s3.amazonaws.com/browse.html#data/authors/
    - Oh, `updated_date` isn't what I thought it was. Each `updated_date` folder has the _changes_ on top of the previous `updated_date`. Like a diff. Except the previous `updated_date` is also changed to remove the records that changed...
- How is the data structured?
  - "The snapshot consists of five files (split into smaller files for convenience), with one file for each of our five entity types. The files are in the JSON Lines format; each line is a JSON object, exactly the same as you'd get from our API."
- How big is the snapshot?
  - "The gzip-compressed snapshot takes up about 330 GB and decompresses to about 1.6 TB."
  - I have about 100GB available on my laptop, so I can't download the whole thing.
- Could also consider OpenAlex data that has been downloaded by others, if accessing older snapshots isn't possible, or the storage requirements are unworkable.
  - Tamay was using some other snapshot, let's check that notebook

Comparing Experimental AI Corpus with current OpenAlex

- See https://epochai.slack.com/archives/C052LFSD17W/p1687443457674329
- Data looks similar up to and including 2021, but I expected a dropoff in EAC data in 2021 similar to the dropoff in current OpenAlex data in 2022. I don't observe such a dropoff.
  - My model for what's going on was that there is a lag in getting data, which reduces the amount of data available for current_year - 1.
- Hypothesis: false positives or duplicates were reduced by some method in 2022, but this was not applied retroactively.
  - But it seems unlikely that they wouldn't apply it retroactively.
- Check out the OpenAlex snapshot release notes: https://github.com/ourresearch/openalex-guts/blob/e6cb16bc6f1eab74aeb63d3d51b446531f9669ee/files-for-datadumps/standard-format/RELEASE_NOTES.txt
  - Evidence of data removal

```
RELEASE 2022-09-16
[...]
- removed 700 thousand duplicate Authors

RELEASE 2022-08-09
- [...] merged 1M sets of works with the same DOI.

RELEASE 2022-07-09
[...]
- removed duplicate Authors and Works
```

  - But this isn't evidence of the data removal _only_ being applied to 2022 publications.

Ask the OpenAlex team?

Look at underlying sources

- Oh yeah, I forgot! MAG was apparently retired at the end of 2021!
  - https://www.microsoft.com/en-us/research/project/academic/
  - "Editor’s note, May 4, 2021 – In a recent blog post, it was announced the Microsoft Academic website and underlying APIs will be retired on Dec. 31, 2021."
- David: Is it easy to see where info has been sourced from? i.e. could you easily get an idea how many of the pre-2022 works came from MAG?
  - OpenAlex has a Sources API
- Looking at `Sources().get()`
  - All sources have an 'ids' field
    - Some 'ids' fields in turn have a 'mag' field. What does that mean? My guess is that it means it comes from MAG.
    - Examples:

```
  'ids': {'openalex': 'https://openalex.org/S2764455111',
   'mag': '2764455111',
   'wikidata': 'https://www.wikidata.org/entity/Q229883'},

  'ids': {'openalex': 'https://openalex.org/S4210172589',
   'issn_l': '1556-5068',
   'issn': ['1556-5068'],
   'wikidata': 'https://www.wikidata.org/wiki/Q7550801',
   'fatcat': 'https://fatcat.wiki/container/tol7woxlqjeg5bmzadeg6qrg3e'},

  'ids': {'openalex': 'https://openalex.org/S4306401840',
   'wikidata': 'https://www.wikidata.org/wiki/Q56101155'},

  'ids': {'openalex': 'https://openalex.org/S4306463937'},
```

- I don't know if having a 'mag' ID necessarily means that all data retrieved for this source comes from MAG. After all, there are often multiple IDs, so the data might come from any of them.
- https://docs.openalex.org/api-entities/sources/get-a-single-source#external-ids
  - The only external IDs are ISSN, Fatcat, MAG, and Wikidata.
  - ISSN is also listed as a source that OpenAlex uses: https://openalex.org/about
- Still...
- Bingo

```
% of works with MAG IDs
2010: 86%
2011: 88%
2012: 89%
2013: 87%
2014: 86%
2015: 88%
2016: 88%
2017: 84%
2018: 85%
2019: 83%
2020: 81%
2021: 69%
2022: 5%

% of works with PubMed IDs
2010: 11%
2011: 11%
2012: 14%
2013: 13%
2014: 13%
2015: 13%
2016: 13%
2017: 12%
2018: 12%
2019: 15%
2020: 14%
2021: 19%
2022: 20%
```

- Now I want to know - what does the presence of a MAG ID mean? I don't think it necessarily means that the work wouldn't be there if not for MAG. Because there is probably some redundancy.
- How can I measure redundancy?

Measuring redundancy of sources

- I think we can get an imperfect but decent measure by measuring the frequency at which there are at least two of MAG, ISSN, Wikidata, Fatcat in the source IDs.
  - But Sources are things like journals. A journal itself might have multiple IDs, while specific works from that journal do not.
    - But if a Source is getting data from a Journal, it should know about all the works from the Journal.
      - Depends how direct the source is.

Imputation

- Getting a sample of AI/ML works first, so it's more domain-specific adjustment
- Fraction of MAG IDs looks very similar to all-fields sample
  - Nevermind, typo - see below.
- But why are the samples quite uniform in total work count across the years? Is uniform sampling a feature?
- Testing if the distribution across years is any different when I fetch a non-random sample (the first 9,000 works returned by paginate)
  - Oops, nah. I just forgot to change a variable name. D'oh.

MAG fraction:

```
array([0.98758278, 0.99089253, 0.98365679, 0.99205448, 0.98086124,
       0.99505562, 0.99186047, 0.99204545, 0.98982558, 0.99380165,
       0.97382199, 0.97368421, 0.7       ])
```

PubMed fraction:

```
array([0.42549669, 0.40983607, 0.4473953 , 0.415437  , 0.3923445 ,
       0.36464771, 0.3372093 , 0.3125    , 0.3502907 , 0.34090909,
       0.40314136, 0.48684211, 0.3       ])
```

- Ok. Similar basic story, but very different fractions. The drop is merely to 0.7.
- Super high MAG fractions for AI/ML works! And these would tend to be top-cited works, I think.
- I guess top-cited works are more likely to have redundant sources.

Total counts:
```
array([1208., 1098.,  979.,  881.,  836.,  809.,  860.,  880.,  688.,
        484.,  191.,   76.,   10.])
```

- Makes sense because top-cited works are more likely to be older. In fact it's interesting that the effect still shows up in this case.
- Let's go back to the random sample now...
- Ok, with random sample the ratios are pretty similar to the all-fields sample.

```
array([0.95131846, 0.95042735, 0.94940978, 0.95392491, 0.96097561,
       0.94072948, 0.95924765, 0.90372671, 0.92032967, 0.904474  ,
       0.90434783, 0.773746  , 0.05387205])
```

- Plus, the total number of works is trending up until 2022, as expected. There's a dip in 2020 but that could just be noise.

Imputation

- The method I'm trying first is to take the ratio of:
  - Average ratio of MAG IDs to total works from 2010 to 2020
  - Ratio of MAG IDs to total works in 2021, and 2022
- Then multiply the data (e.g. author count) by that ratio, in each of 2021 and 2022
- Result:
  - 2022 looks too big. Maybe like 3x too big based on the past trend.

# 2023-Jun-26

## Can I use the Experimental AI Corpus to filter works? How long will that take?

- Actually, this should be easy and fast. List of IDs from EAC. IDs are stored locally once I load the dataset. So just filter everything locally!
- EAC data goes up to end of 2021
- After filtering, 17343 works compared to 47625 works before that.
- Hmm. I think it's missing too many true positives based on the below result:

```python
for work in works[:100]:
    if work['id'] not in eac_work_ids and work['publication_year'] < 2022:
        print(work['title'])
```

```
SciPy 1.0: fundamental algorithms for scientific computing in Python
The Pascal Visual Object Classes (VOC) Challenge
DeepLab: Semantic Image Segmentation with Deep Convolutional Nets, Atrous Convolution, and Fully Connected CRFs
Highly accurate protein structure prediction with AlphaFold
MobileNetV2: Inverted Residuals and Linear Bottlenecks
Scikit-learn: Machine Learning in Python
Deep Neural Networks for Acoustic Modeling in Speech Recognition: The Shared Views of Four Research Groups
Array programming with NumPy
FaceNet: A unified embedding for face recognition and clustering
Overview of the High Efficiency Video Coding (HEVC) Standard
Mastering the game of Go without human knowledge
Spatial Pyramid Pooling in Deep Convolutional Networks for Visual Recognition
Google Earth Engine: Planetary-scale geospatial analysis for everyone
Learning Spatiotemporal Features with 3D Convolutional Networks
Robust principal component analysis?
Quo Vadis, Action Recognition? A New Model and the Kinetics Dataset
3D Convolutional Neural Networks for Human Action Recognition
Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation
Image Super-Resolution Via Sparse Representation
Adaptive Subgradient Methods for Online Learning and Stochastic Optimization
Guided Image Filtering
Single Image Haze Removal Using Dark Channel Prior
LINE
Deformable Convolutional Networks
Natural Language Processing (Almost) from Scratch
...
Deep Compression: Compressing Deep Neural Networks with Pruning, Trained Quantization and Huffman Coding
Searching for MobileNetV3
CIDEr: Consensus-based image description evaluation
Accurate, Dense, and Robust Multiview Stereopsis
```

- Still, this is something we could use to check the robustness of our conclusions.

## Implementing additional metrics

Work-by-work author count

- Should I count the number of people with the same affiliation, or the number of people on the paper?
  - The latter is going to be more robust.
  - Why not both, then we can check how the numbers shake out. My guess is that the former is going to yield low, noisy counts.

# 2023-Jul-04

## Setting environment back up

- Install conda
  -   
- Set up `epoch` environment

# 2023-Jul-18

- Making short letter version of report

## Distribution of authors found per paper

- Not currently getting this data
- We're iterating papers. So we'll know all the affiliated authors once we're done processing a given paper.
- We just need to have a data structure that bundles the affiliated authors by paper.
  - `dict<institution, dict<work_id, set<work_authors_affiliated_with_institution>>>`
- Hmm
- Distribution is very wide
- Mean is 2.3 authors per institution per paper. That is closer to my intuition than 1 author per institution.
- Looking at outliers - >50 authors
  - Paper on augmented reality from Microsoft - probably not AI
  - Paper on hardware-software co-design for deep learning from Meta - legit
  - Paper on quantum computing from Google - probably not AI
    - Two of these in fact
  - Deep speech 2 - legit AI paper from Baidu - but I only count 32 authors on the arxiv PDF, rather than 69
    - Apparent misattributions, e.g. Bin Yuan
    - Ah, but the PLMR version does have 69 authors: http://proceedings.mlr.press/v48/amodei16.html 
- What does this mean? I feel like this doesn't square with the number of publications
- _Unique_ authors...does that matter here?
  - The same author can appear on more than one work per year

# 2023-Jul-19

## Single-affiliated authors check

- Random sample of 10 works with one affiliated author found
  - [PASS] https://openalex.org/W3026508739
    - [PASS] 1 author from Alibaba
    - [PASS] AI
      - Doesn't seem like Deep Learning, but has planning algorithms for autonomous vehicles, so I'd count it as AI.
  - [FAIL] https://openalex.org/W3018307512
    - [FAIL] 2 authors from Alibaba
      - OpenAlex incorrectly affiliates Daoyuan Chen with Peking University; should be Alibaba
      - OpenAlex correctly affiliates Yaliang Li with Alibaba
      - OpenAlex incorrectly affiliates Ying H. Shen with Peking University
    - [PASS] ML
      - Entity and relation extraction; talks about training models
  - [PASS] https://openalex.org/W3112458135
    - [PASS] 1 author from Alibaba
    - [PASS] AI
      - Involves a Bayesian network - close enough
  - https://openalex.org/W3111342233
- Meta: suspicious that the first 4 samples are Alibaba.
  - Could be that most of the single-author cases are Alibaba?
- New sample
  - [FAIL] https://openalex.org/W2806128650
    - [FAIL] All 6 authors should be Alibaba, but OpenAlex only finds Luo Si
    - [PASS] ML
      - Involves neural network
  - [PASS] https://openalex.org/W4327644595
    - [PASS] 1 author from Alibaba
    - [PASS] ML
      - Involves neural network
  - [PASS] https://openalex.org/W2991451943
    - [PASS] 1 author from Alibaba
    - [PASS] ML
      - Involves attention mechanism
  - [PASS] https://openalex.org/W3103338449
    - [PASS] 1 author from Alibaba
    - [PASS] ML
      - Involves neural network
  - [PASS] https://openalex.org/W4206473782
    - [PASS] 1 author from Alibaba
    - [PASS] ML
      - Involves RL
  - [PASS] https://openalex.org/W3105000568
    - [PASS] 1 author from Alibaba
- Ugh, I still messed up. All Alibaba.
- Sample #3
  - [PASS] https://openalex.org/W2977955221
    - [PASS] 1 author from Microsoft Research Asia
    - [PASS] ML
      - Involves CNNs
  - [FAIL] https://openalex.org/W2913676469
    - [FAIL] All from Rakuten Institute of Technology, but one listed as Amazon
      - Was previously Amazon: https://www.difabbrizio.com/
    - [PASS] ML
      - Involves RNNs
  - [PASS] https://openalex.org/W3111145724
    - [PASS] 1 author from Amazon
    - [PASS] AI
      - Borderline - uses prediction algorithms
  - [PASS] https://openalex.org/W2963811641
    - [PASS] 1 author from FAIR (now MAIR)
    - [PASS] ML
      - Involves GANs
  - [PASS] https://openalex.org/W2144058993
    - [PASS] 1 author from Microsoft Research Cambridge
    - [FAIL] CS
      - Doesn't sound like anything that could be called "AI"
      - But not completely off
  - [PASS] https://openalex.org/W3046888428
    - [PASS] 1 author from Alibaba
    - [PASS] ML
      - RNNs
  - [PASS] https://openalex.org/W1913744585
    - [PASS] 1 author from Google Research
    - [FAIL] Stats
      - Doesn't sound like anything that could be called "AI"
      - But not completely off
  - [PASS] https://openalex.org/W4221156617
    - [PASS] 1 author from Tencent
    - [PASS] ML
      - Involves deep learning
  - [PASS] https://openalex.org/W4375948571
    - [PASS] 1 author from Google
    - [PASS] ML
      - Sounds like a lit review of ML applied to health
  - [PASS] https://openalex.org/W4312903731
    - [PASS] 1 author from Amazon
    - [PASS] ML
      - GNN
- Summary:
  - 9/10 correctly affiliated single author
    - Other samples: 5/6 and 2/3
  - 8/10 correctly labeled as AI/ML
    - Other samples: 3/3 and 5/5

## AI/ML labeling check

Random sample of 10

- [PASS] https://openalex.org/W4312191413
  - Machine learning mentioned
- [PASS] https://openalex.org/W2964046272
  - Statistical learning
- [PASS] https://openalex.org/W2402827806
  - "training a speech translation system"
- [PASS] https://openalex.org/W3130665016
  - "Self-supervised learning"
- [PASS] https://openalex.org/W3123614573
  - "supervised learning"
- [PASS] https://openalex.org/W2105103433
  - "semi-supervised learning"
- [PASS] https://openalex.org/W4226028923
  - "Vision transformer"
- [PASS] https://openalex.org/W3175300676
  - "Self-supervised learning"
- [PASS] https://openalex.org/W3214495016
  - "Transfer learning"
- [FAIL] https://openalex.org/W2810972835
  - "This proposal deals with the mechanisms of the navigation technologies used to develop the 2-Dimensional and 3-Dimensional models."
  - Doesn't sound like AI


## OpenAI reliability check

Full sample, default order.

- https://openalex.org/W2618530766
  - Debatable affiliation. Ilya Sutskever was at OpenAI at the time of publication for this version of the paper (2017). But Ilya Sutskever was not at OpenAI at the time of publication for the original version of the paper (2012).
- https://openalex.org/W2962785568
  - Affiliates Phillip Isola
  - Paper published in 2018
  - Phillip Isola contributed to this blog post from October 2018: https://openai.com/research/reinforcement-learning-with-prediction-based-rewards
  - December 2017: "Phillip Isola will join the [MIT] Department of Electrical Engineering and Computer Science as an assistant professor in July 2018...Currently a fellow at OpenAI..."
  - Passable
- Just browsing titles now
  - There are 64 in total, including 2023
- False positives:
  - A machine’s perspective https://doi.org/10.3997/1365-2397.fb2023046
    - ChatGPT credited to OpenAI
  - Does GPT-3 qualify as a co-author of a scientific paper publishable in peer-review journals according to the ICMJE criteria? - A Case Study. https://doi.org/10.21203/rs.3.rs-2404314/v1 ['https://openalex.org/A4315473491']
    - GPT is listed as an author, affiliated with OpenAI
      - I mean, this could actually count. This could be the future of paper-writing. This will reflect some of the research labour at OpenAI in future.
- False negatives:
  - Language models are few-shot learners
    - This is in OpenAlex, but missing any affiliation
  - Scaling laws
  - 
- Sense check: OpenAI research index
  - https://openai.com/research?topics=adversarial-examples,audio-generation,compute,computer-vision,contrastive-learning,domain-randomization,dota-2,environments,exploration,games,generative-models,human-feedback,image-generation,interpretability,language,memory,meta-learning,multi-agent,open-source,policy-optimization,procedural-generation,reasoning,reinforcement-learning,representation-learning,research,robotics,robustness,scaling-properties,self-play,sim-to-real,software-engineering,sparsity,speech-recognition,summarization,supervised-learning,transfer-learning,transformers,unsupervised-learning&contentTypes=publication
  - 113 listed when filtering out "safety & alignment" and "responsible AI"
  - 163 in total (no filters)
- Method we could use to add false negatives:
  - Scrape all the paper URLs from openai.com/research
  - For each paper URL, search OpenAlex for a match
  - Accept the first match if the relevance score is over some threshold (not sure what threshold)
  - Working on this, but taking a while to handle Javascript pagination.
  - Probably faster to just copy-paste every HTML.

Rejects

```
Original title:  Language models can explain neurons in language models
Search result title:  RECEPTIVE FIELDS AND FUNCTIONAL ARCHITECTURE IN TWO NONSTRIATE VISUAL AREAS (18 AND 19) OF THE CAT
Relevance score:  183.50458
Match score:  3.7630586132250228

Original title:  Frontier AI Regulation: Managing Emerging Risks to Public Safety
Search result title:  Bounded Rationality and Organizational Learning
Relevance score:  117.12347
Match score:  3.524775887675073

Original title:  Self-critiquing models for assisting human evaluators
Search result title:  The Role of Debriefing in Simulation-Based Learning
Relevance score:  67.881134
Match score:  2.0000079256679766

Original title:  Activation Atlas
Search result title:  MAP kinase in situ activation atlas during <i>Drosophila</i> embryogenesis
Relevance score:  1023.1317
Match score:  59.75997266773872

Original title:  Scaling Laws for Reward Model Overoptimization
Search result title:  From initial idea to unique advantage: The entrepreneurial challenge of constructing a resource base
Relevance score:  17.621124
Match score:  0.6890404743301375

Original title:  Let's Verify Step by Step
Search result:  The Essential Guide to Semiconductors
https://openalex.org/W612923280
Relevance score:  27.246555
Match score:  4.8936257399641345

Original title:  Generative Language Models and Automated Influence Operations: Emerging Threats and Potential Mitigations
Search result:  Emergent by Design: Performance and Transformation at Infosys Technologies
https://openalex.org/W1988667557
Relevance score:  19.248081
Match score:  1.6881683797321263

Original title:  Evolution through Large Models
Search result:  Dynamic topic models
https://openalex.org/W2072644219
Relevance score:  221.00365
Match score:  5.193261855393698

Original title:  Formal Mathematics Statement Curriculum Learning
Search result:  Learning Styles and Learning Spaces: Enhancing Experiential Learning in Higher Education
https://openalex.org/W2147454772
Relevance score:  62.167454
Match score:  1.114540335250958
```

Accepts with low relevance scores

```
Original title:  Measuring the Algorithmic Efficiency of Neural Networks
Search result title:  Measuring the Algorithmic Efficiency of Neural Networks.
Relevance score:  644.3169
Match score:  147.81643445870534

Original title:  A Hazard Analysis Framework for Code Synthesis Large Language Models
Search result title:  A Hazard Analysis Framework for Code Synthesis Large Language Models
Relevance score:  197.26831
Match score:  197.26831

Original title:  Extensions and Limitations of the Neural GPU
Search result title:  Extensions and Limitations of the Neural GPU
Relevance score:  396.24777
Match score:  177.20738993054036

Original title:  Understanding the Capabilities, Limitations, and Societal Impact of Large Language Models
Search result title:  Understanding the Capabilities, Limitations, and Societal Impact of Large Language Models.
Relevance score:  671.98834

Original title:  AI Safety Needs Social Scientists
Search result title:  AI Safety Needs Social Scientists
Relevance score:  883.25287

Original title:  Efficient Training of Language Models to Fill in the Middle
Search result title:  Efficient Training of Language Models to Fill in the Middle
Relevance score:  304.83688

Original title:  Teaching Models to Express Their Uncertainty in Words
Search result title:  Teaching Models to Express Their Uncertainty in Words
Relevance score:  241.08252

Original title:  Learning Policy Representations in Multiagent Systems
Search result title:  Learning Policy Representations in Multiagent Systems
Relevance score:  895.31226

Original title:  WebGPT: Browser-assisted question-answering with human feedback
Search result title:  WebGPT: Browser-assisted question-answering with human feedback
Relevance score:  493.95328

Original title:  Text and Code Embeddings by Contrastive Pre-Training
Search result title:  Text and Code Embeddings by Contrastive Pre-Training
Relevance score:  204.86462
Match score:  204.86462

Original title:  Training Verifiers to Solve Math Word Problems
Search result title:  Training Verifiers to Solve Math Word Problems
Relevance score:  292.2497

Original title:  Transfer of Adversarial Robustness Between Perturbation Types
Search result title:  Transfer of Adversarial Robustness Between Perturbation Types.
Relevance score:  819.5312
```

# 2023-Jul-20

Checking Microsoft having similar number of publications all the time

- Confirming work counts

```
2010 977
2011 1015
2012 1065
2013 1168
2014 1133
2015 1051
2016 1092
2017 1113
2018 1300
2019 1616
2020 1887
2021 1937
2022 946
2023 363
```

- Looks kinda legit

```python
rng.choice(works_by_year[2010], 10)
[work["title"] for work in works_sample]

# Output:

['Near-Strong Equilibria in Network Creation Games',
 'Automatic verification of Java programs with dynamic frames',
 'Discovering frequent patterns in sensitive data',
 '10421 Summary - Model-Based Testing in Practice.',
 'Affine Invariant Topic Model for Generic Object Recognition',
 'Analyzing bandit-based adaptive operator selection mechanisms',
 'Efficiently learning mixtures of two Gaussians',
 'Compress Compound Images in H.264/MPGE-4 AVC by Exploiting Spatial Correlation',
 'Image deblurring using inertial measurement sensors',
 'Session details: Research track 18: ranking and multi-label learning']

# 2014:

['A new Neural Network based logistic regression classifier for improving mispronunciation detection of L2 language learners',
 'Dynamic joint outage identification and state estimation in power systems',
 'Bilu-linial stable instances of max cut and minimum multiway cut',
 'Keynote Address 1: Some Recent Research Results on Boosting Gadget Battery Life',
 'A computational approach to measuring the correlation between expertise and social media influence for celebrities on microblogs',
 'Safe zero-cost coercions for Haskell',
 'Pre-Trained Multi-View Word Embedding Using Two-Side Neural Network',
 'Analyze this! 145 questions for data scientists in software engineering',
 'On the Convergence of Stochastic Variational Inference in Bayesian Networks',
 'Black-box obfuscation for d-CNFs']

# 2018:

['Boosting Information Spread: An Algorithmic Approach',
 'High-order Proximity Preserving Information Network Hashing',
 'Weighted Rate-Distortion Optimization for Screen Content Coding',
 'Multi-Task Neural Models for Translating Between Styles Within and Across Languages',
 'Deep Attention Neural Tensor Network for Visual Question Answering',
 'Neural Architecture Optimization',
 'Stochastic Answer Networks for Natural Language Inference',
 'M-Walk: Learning to Walk over Graphs using Monte Carlo Tree Search',
 'MiCT: Mixed 3D/2D Convolutional Tube for Human Action Recognition',
 'Learning deep representations by mutual information estimation and maximization']

# 2022:

['Exploring and evaluating personalized models for code generation',
 'Towards Proactively Forecasting Sentence-Specific Information Popularity within Online News Documents',
 'Efficient and Stable Information Directed Exploration for Continuous Reinforcement Learning',
 'Bringing Old Films Back to Life',
 'Learning Models of Individual Behavior in Chess',
 'Integrating ANFIS and Qt Framework to Develop a Mobile-Based Typhoon Rainfall Forecasting System',
 'App usage on-the-move: Context- and commute-aware next app prediction',
 'Question-aware transformer models for consumer health question summarization',
 'RSTT: Real-time Spatial Temporal Transformer for Space-Time Video Super-Resolution',
 'CERT: Continual Pre-training on Sketches for Library-oriented Code Generation']
```

- Maybe there's more false-positives in earlier years.
- But maybe I also am worse at recognising what was "AI" in earlier years.
- Papers that I'm _confident_ are AI/ML from the title
  - 2010: 5/10
  - 2014: 4/10
  - 2018: 7/10
  - 2022: 7/10
- Earlier years included:

```
2000 207
2001 225
2002 405
2003 376
2004 419
2005 546
2006 652
2007 674
2008 830
2009 915
2010 977
2011 1015
2012 1065
2013 1168
2014 1133
2015 1051
2016 1092
2017 1113
2018 1300
2019 1616
2020 1887
2021 1937
2022 946
2023 363
```

## New charts

- Phase plot

# 2023-Jul-26

## Bootstrapping

- How
- Need resampling of the data.
- Resample all works? Or resample by company?
- How to easily hook this in?
- I think the easiest thing is to separate into steps: (a) sampling, (b) statistics of the sample
  - (a) sampling
    - For `result = func(data)`, we want to add a wrapper like so:
    - Actually I'll just mock this in the code file.
- I'm thinking we should just handle the specific case of a list of dict of instition => data

### Bootstrap CI results

- Sample size 100
  - For reference, any given Work in the original dataset has about a 63% chance of appearing in a given member of this sample. (1 - 1/e ~= 63%; the limit as dataset size approaches infinity).

Average unique authors per year:

```
{'Google': {'mean': 770.1428571428571,
  'median': 770.1428571428571,
  'std': 0.5714285714285552,
  'ci': array([ 7.70e+02,  7.71e+02])},
  'Tencent': {'mean': 198.03571428571428,
  'median': 198.03571428571428,
  'std': 3.25,
  'ci': array([ 1.95e+02,  2.01e+02])},
  'Microsoft': {'mean': 738.1071428571429,
  'median': 738.1071428571429,
  'std': 5.678571428571445,
  'ci': array([ 7.33e+02,  7.43e+02])},
  'Meta': {'mean': 233.32142857142856,
  'median': 233.32142857142856,
  'std': 2.035714285714292,
  'ci': array([ 2.31e+02,  2.35e+02])},
  'Nvidia': {'mean': 109.35714285714286,
  'median': 109.35714285714286,
  'std': 1.0,
  'ci': array([ 1.08e+02,  1.10e+02])},
  'Baidu': {'mean': 129.17857142857144,
  'median': 129.17857142857144,
  'std': 0.392857142857153,
  'ci': array([ 1.29e+02,  1.30e+02])},
  'Amazon': {'mean': 223.46428571428572,
  'median': 223.46428571428572,
  'std': 0.5357142857142918,
  'ci': array([ 2.23e+02,  2.24e+02])},
  'Alibaba': {'mean': 253.70054945054946,
  'median': 253.70054945054946,
  'std': 9.914835164835182,
  'ci': array([ 2.45e+02,  2.63e+02])},
  'DeepMind': {'mean': 102.875,
  'median': 102.875,
  'std': 0.7916666666666714,
  'ci': array([ 1.02e+02,  1.04e+02])},
  'OpenAI': {'mean': 7.035714285714286,
  'median': 7.035714285714286,
  'std': 0.5357142857142856,
  'ci': array([ 6.55e+00,  7.52e+00])}}
```

- Generally very low variation
- OpenAI is the most uncertain but the number of authors is very low to begin with

Average citation metric per year

```
{'Meta': {'mean': 14764.663571428573,
  'median': 14661.25,
  'std': 1452.6431890605413,
  'ci': array([ 1.28e+04,  1.74e+04])},
  'Google': {'mean': 33572.588571428576,
  'median': 33301.107142857145,
  'std': 2141.1214653064217,
  'ci': array([ 3.04e+04,  3.75e+04])},
  'Alibaba': {'mean': 2798.211813186813,
  'median': 2780.75,
  'std': 145.49491691655044,
  'ci': array([ 2.59e+03,  3.05e+03])},
  'Nvidia': {'mean': 3518.3657142857137,
  'median': 3485.607142857143,
  'std': 436.78606439420616,
  'ci': array([ 2.79e+03,  4.28e+03])},
  'Tencent': {'mean': 3880.2943406593404,
  'median': 3881.535714285714,
  'std': 186.7684319859331,
  'ci': array([ 3.57e+03,  4.20e+03])},
  'Microsoft': {'mean': 24529.83357142858,
  'median': 24323.571428571428,
  'std': 2054.2339398665113,
  'ci': array([ 2.16e+04,  2.77e+04])},
  'Baidu': {'mean': 2636.6207142857143,
  'median': 2648.4285714285716,
  'std': 210.51588570020755,
  'ci': array([ 2.29e+03,  2.95e+03])},
  'Amazon': {'mean': 2955.1371428571424,
  'median': 2887.0,
  'std': 460.823677343081,
  'ci': array([ 2.35e+03,  3.88e+03])},
  'DeepMind': {'mean': 5491.3116666666665,
  'median': 5387.166666666666,
  'std': 1019.0023638495716,
  'ci': array([ 3.93e+03,  7.42e+03])},
  'OpenAI': {'mean': 1589.0250000000003,
  'median': 1486.5892857142858,
  'std': 724.81075982452,
  'ci': array([ 6.33e+02,  2.82e+03])}}
```

- Bigger variation here
- OpenAI particularly big CI


Summary post:

Quick analysis of uncertainty in results via bootstrapping:

- My method was to resample at the level of the publications (~50k publications). The analysis is the same as before for each resample, until I compute the mean/std/CI of the final outputs.
- Bootstrap size 100
- The average number of unique authors per year for each company didn't vary much. 
  - E.g. 90% CIs: OpenAI [ 6.55e+00,  7.52e+00], DeepMind [ 1.02e+02,  1.04e+02], Google [ 7.70e+02,  7.71e+02]
- Citations per author for each company varied moderately, most of all OpenAI (note this is without improvements to the OpenAI data). But the CIs mostly didn't overlap.

```
OpenAI [ 1.66e+02  2.72e+02]
Meta [ 7.63e+01  8.98e+01]
DeepMind [ 5.17e+01  6.08e+01]
Google [ 3.86e+01  4.66e+01]
Microsoft [ 3.55e+01  3.59e+01]
Nvidia [ 2.93e+01  3.03e+01]
Baidu [ 2.21e+01  2.62e+01]
Tencent [ 1.48e+01  1.85e+01]
Amazon [ 1.41e+01  1.56e+01]
Alibaba [ 1.31e+01  1.32e+01]
```

- Stats for average team size are forthcoming

# 2023-Aug-03

## Company compute analysis write-up

## OpenAI extra data

- I want to check which papers overlap, what the unique authors are
- If it seems tractable to label the affiliation of all the unique authors, I'll do that

Examining the extra papers

- There were 102 found in OpenAlex
- 6 overlapped with my existing set found via affiliations, leaving 96
- Those 96 have 348 unique authors. Yikes.
  - Haven't checked name duplication yet.
- Looking through the authorships of each work, there are some which still have an _identified_ affiliation with OpenAI. I don't think that should be possible. The original search by affiliation should have picked up those works.
  - Is it possible by some duplication of works?
- From a skim, there's a bit of duplication but not a lot.
  - E.g. "Pieter Abbeel" vs. "OpenAI Peter Abbeel", "Jonathan Ho" vs. "OpenAI Jonathan Ho", "Xi Chen" 3 times (maybe), "Yi Sun" 2 times (maybe).
- I should check the overlap of authors with the original set of works
  - Of the 283 unique authors from OpenAlex affiliations, and the 348 unique authors from OpenAI Research, 61 authors overlap.
    - Not bad.
    - Wait, don't we just want the authors definitely affiliated with OpenAI? Not the extra ones. Should check that.
    - Ok, now it's 42 rather than 61. And 62 unique OpenAI authors from OpenAlex affiliations.
- There are 15 authors whose last known institution in OpenAlex is OpenAI
- Ok so we have a set of publications that are definitely by OpenAI, and we have a set of authors on those publications that have been affiliated with at OpenAI at some point. It seems highly unlikely that any one of those authors was on any one of those papers and _not_ affiliated with OpenAI _at the time of publication_.
  - Where I'm going with this: we _assume_ that if an author from this overlapping set of 42 appears on one of these extra 96 papers, that they were affiliated with OpenAI at the time.
    - This seems like the quickest way to proceed with a decently accurate set of extra OpenAI papers.
    - Let's see how many extra works we get via this route, and what those works are.
    - I think a problem that will arise here is, something like the GPT-3 paper will have spuriously high citations per author because we don't identify all the authors.
    - I think we should also process "raw affiliation string". But maybe then we should do the same for all the other companies. ("Meta" I'm not so sure about, but "Facebook" and other company names seem unique enough.
      - We can handle that another time in another place.
      - Nah, still gonna pilot it here.

# 2023-Aug-11

## Top labs (academic or industry)

Investigating why a priori top AI universities are not showing up

- Baseline: "Machine Learning" concept only; top 200

```
Google: True
DeepMind: True
OpenAI: True
Toronto: False
Montréal: True
```

- "Machine Learning" concept only; top 500

```
Google: True
DeepMind: True
OpenAI: True
Toronto: False
Montréal: True
```

- "Artificial Intelligence" and "Machine Learning" concepts; top 200

```
Google: True
DeepMind: False
OpenAI: False
Toronto: True
Montréal: True
```

- "Artificial Intelligence" and "Machine Learning" concepts; top 500

```
Google: True
DeepMind: True
OpenAI: False
Toronto: True
Montréal: True
```

- So it seems that "Artificial Intelligence" crowds out OpenAI, and Toronto doesn't have enough papers tagged "Machine Learning"
  - Not even 1000 catches OpenAI, but 2000 does.
- Top 25 most cited papers from U of T have 5 in 'Machine learning', 11 in 'Artificial intelligence', 2 in 'Deep learning'
- I think the issue with some institutions being utterly excluded (e.g. Stanford) is that 'x_concepts' doesn't contain AI or ML.
  - I assume x_concepts is something like "the concepts this institution is most known for or most cited for"
  - "The Concepts most frequently applied to works affiliated with this institution. Each is represented as a dehydrated Concept object, with one additional attribute:"

# 2023-Aug-14

## Finding top researchers at a given institution

Guess:

1. Get institution ID
2. Filter Authors by institution ID, concept, and sort by citation count
  1. Can we filter by concept?
  2. Yes but it has a similar limitation to filtering Institution by concept.
     1. Probably better for Authors though; they are less diverse in which fields they publish in.
3. University of Montreal has a sensible-looking top 5:

```
Yoshua Bengio
- Obvious
Aaron Courville
- Obvious
David Warde-Farley
- GAN paper
Mehdi Mirza
- GAN and cGAN
René Doyon
- Less clear - astronomy?
```

- Limitations
  - Citation count metric is biased by single outliers => h-index is better?
  - Can only match on last known institution
    - But isn't this what we want? If they are no longer at the lab then we'd want to know where they are now.
    - There's still a problem with this field often being out of date.

h-index top 5:

```
Yoshua Bengio
Aaron Courville
Jennifer O'Loughlin
- Health
René Doyon
- Astronomy
J. M. Pearson
- CS
```

Number of publications:

```
Yoshua Bengio
René Doyon
Pierre Jolicoeur
- History
- Does have AI as a concept, but not ML
Guy Cloutier
Jennifer O'Loughlin
```

Just ML concept, number of publications:

```
Yoshua Bengio
Jennifer O'Loughlin
Aaron Courville
Jack Siemiatycki
- Health
Jian-Yun Nie
- NLP
```

AI AND ML, number of publications:

```
Yoshua Bengio
Aaron Courville
Jian-Yun Nie
Gerhard Wolf
Houari Sahraoui
- Automated software engineering
```

DL, number of publications:

```
Yoshua Bengio
Aaron Courville
Roland Memisevic
- Good
David Warde-Farley
Pouya Bashivan
- Good
```

DL, h-index:

```
Yoshua Bengio
Aaron Courville
Roland Memisevic
David Warde-Farley
Mehdi Mirza
```

Now Stanford:

```
YoungJu Jo
- Surprising for the top, but relevant
Jeremy Irvin
Bharath Ramsundar
Avanti Shrikumar
Xianjin Dai
```

Stanford, works count:

```
Shreyas Vasanawala
Sulaiman Vesal
Xianjin Dai
Avanti Shrikumar
Arjun Desai
```

MIT, h-index:

```
Song Han
- Good
Alexey A. Shvets
Jonathan Frankle
Otkrist Gupta
Qianli Liao
```

Berkeley, h-index:

```
Fang-Chieh Chou
Forrest Iandola
Jonathan Long
Mayur Mudigonda
Yunhui Guo
```

Berkeley, ML and DL:

```
Michael I. Jordan
Rasmus Nielsen
Jitendra Malik
Trevor Darrell
Leon O. Chua
Pieter Abbeel
S. Shankar Sastry
Dawn Song
```

Alternative methods:

- Get all the AI/ML works of the institution. Then run the processor on that. Then get the list of authors from that. Then sort by h-index or whatever metric.
  - Quite slow
- Get the top-cited AI/ML works. Then run the processor on that. Then get the list of authors that are bucketed into the given institution. Then sort by h-index or whatever metric.
- Use number of papers as the metric

# 2023-Aug-17

## Counting occurrences of algorithms via citations of origin papers

Planning this out

- We need to get the list of origin papers - `algorithm_origin_works`
  - We also want a mapping from work to affiliation
  - So it would be a good idea to work with the spreadsheet data directly
- Then we need the list of top training run papers - `notable_works`
  - Alternatively, all of the notable ML systems from the PCD database since 2021
  - We need to make sure these papers are matched in OpenAlex, via `search` and relevance score
- Then we need a occurence dict for `algorithm_origin_works`
  - To preserve information, we could start with each value being a list of IDs from `notable_works` that cite the origin work. Then we simply take the `len`.
- For each work in `notable_works`
  - Fetch the list of references
  - For each reference
    - If its ID is in `algorithm_origin_works`
    - Append the ID of the work to the occurrence dict
- Then to count the number of key algorithms used, by institution, use a occurrence-by-institution dict:
  - For each origin work in occurrence dict
    - Get occurrence count
    - Map to institution
    - Accumulate the count in the occurrence-by-institution dict

# 2023-Aug-18

## Counting occurrences of algorithms via citations of origin papers

- Damn. This method is a flop with OpenAlex, because most works have empty `referenced_works`
- So the alternatives:
  - Manually go through each notable paper myself, copy-paste the list of references into a data file
    - That might not be much faster than reading the implementation details of the paper, which would be more accurate
  - Give each notable paper to Claude, ask for key algorithms based on references
    - Many of the papers' files are too large to upload to Claude
    - But maybe Claude could handle it as raw text

# 2023-Aug-25

Redoing the initial selection of institutions

- Freezing the PCD
- Going with non-log z-score. The results turn out pretty well.
- The set of top 5 is robust. It's robustly the big 5 US labs: Google, DeepMind, Microsoft, Meta, OpenAI.
- Ah, if I'm going to add zeros for institutions that are in the OA rankings, I should add the academic institutions too.
  - Or filter out the academic institutions. But that seems too time consuming.
    - Not necessarily, if I do it at the stage where I have the institution IDs.
      - Wait no, I need the Institution object.
    - Also no because I'm normalising over the whole PCD.
- Duplication of works by title doesn't seem like a big problem
  - This is for the 100K top-cited works
  - Unique titles (exact match): 99371
  - Lowercase: 99161
  - Lowercase, and without punctuation and symbols and spaces: 99123
  - Yeah it doesn't seem like a big problem for this set of works. Less than 1% duplication of works, 1.24% of citations.
- Current company dataset (will probably be updated for final results in paper, but this is still representative):
  - Initial: 49708
  - Unique IDs: 47625
  - Titles not None: 49697
  - Unique titles (exact match): 42619
  - Lowercase: 41284
  - Lowercase, and without punctuation and symbols and spaces: 40622
  - Ok, there's a way bigger problem here. 18% of works, 9% of citations.
  - Worth dealing with.
  - How to deal?
  - I think the easiest thing at this stage would be to manually merge the Work object.
    - What would I need to merge?
    - Hmm, it is a bit tricky.
    - First and easiest thing is to accumulate citations per year and cited-by count.
    - But ideally I'd also merge authorship so that affiliations can be found when missing.
  - Mm, first let's inspect how the citation count varies for duplicate titles
    - Not clear if we _should_ add the citation counts together - what if they overlap?
    - ~~Sometimes the citation counts are similar (even identical), sometimes very different~~
      - Oh wait I didn't actually deduplicate IDs yet
    - Correction: sometimes the citation counts are similar, but usually significantly different
    - Eyeballing a bunch of titles, the duplicate detection method seems sound
    - I think the safest strategy is to remove the less-cited duplicates.

# 2023-Aug-28

New dataset from new top 25 companies

- Can I query with 25 institutions at once?
- "You can combine up to 50 values for a given filter in this way." https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/filter-entity-lists
- But I'm getting an error
- Oh right, we actually have 106 institution IDs due to aliases.
- So I'll need to use the one-at-a-time method. I think that will be fine. I can avoid duplicates as it iterates.

Bug in analysis notebook

- I'm not handling the case where an institution has no data
- This can happen with bootstrapping
- Solutions
  - Populate the data with empty lists

# 2023-Sep-07

## Results with OpenAI data added

- Firstly I just want to get a feel for the effect of adding this data. Not worried about fairness, rigor etc.
- New OpenAI dist for mean citations per author: 249 (90% CI: 95 to 458) (width: 363)
  - Old: ~290 (90% CI: 117 to 684) (width: 567)
  - As expected, CI width has decreased. But by less than I expected.
  - EDIT: this was probably just variance in the bootstrap!
  - Mean has also decreased. Is it more the citations or the authors?
  - Citations
    - 1722.385 [657,  2740]
    - Old: 1589.0250000000003 [633, 2820]
    - Similar
  - Authors
    - 11.06 [8.49, 13.9]
    - Old: 7.04 [6.55, 7.52]
    - Ok, it has increased but not by a large margin. Also more variance now.
    - More recent results seem more similar? Going off the old chart of citations per author vs. authors.
- Bug? EDIT: No
  - Mean of the samples is not the same as the mean returned by `bootstrap_stats`
  - E.g. OpenAI `bootstrap_stats` result: 1722.385 vs. OpenAI mean: 1519.25
  - There's two different variables: `institution_citations` (used for )
  - Ohhh, one is the mean for each bootstrap iteration over years, and then `boostrap_stats` aggregates the boostrap iterations
  - Cool
- Hold up. Let's scrutinise.
  - Am I really using the data that replaces the affiliations?
    - I think not! That code comes after the point of saving the data
  - Oh, I'm also a dingus. I didn't assign `works` to `new_works`!
- New-New OpenAI dist for mean citations per author: 155 [97 to 215] (width: 118)
  - Expected - much lower average, much narrower CI
  - Nice
- So this seems like an improvement. Do I just want to leave this as-is?
  - The rationale is that OpenAI data seemed particularly noisy and underrepresented when just searching OpenAlex publications.
  - So we've searched for more publications by cross-referencing the OpenAI research database.
  - To actually get more OpenAI authorships, we then used two methods:
    - For authors who, according to OpenAlex, definitely were at OpenAI _at some point in time_, and appeared on one of the newly found OpenAI works, add OpenAI to their authorship.
      - Note that I didn't use raw affiliation strings for this
    - Use the raw affiliation strings to find other authors

# 2023-Sep-26

## Change point in compute concentration

- Step function model
  - Biggest diff in BIC: 2019-09-30, full=190.80162007074375, broken=167.63444416049688
    - R^2: -2.220446049250313e-16 vs. 0.3204578368130502
- Linear model
  - Biggest diff in BIC: 2019-09-30, full=182.65422818806846, broken=171.49353236541617
    - R^2: 0.16036645903874558 vs. 0.3243096613113271
- Dual linear model
  - Restrict so that segments must have at least 3 data points
  - Biggest diff in BIC: 2019-10-31, full=182.65422818806846, broken=172.20923670037925
    - But the R^2 values are really bad: 0.0024 and 0.0115
- Step function is the best in terms of BIC because it accounts for difference in number of parameters

# 2023-Oct-13

## Proportion of Chinese research in English

- Map of Science (Zach says this feature will disappear soon): https://sciencemap.eto.tech/?us_affiliation_share=0%2C0&chinese_language_share=0%2C0&mode=summary
- China-affiliated, English-language articles in last five years: 35,566
  - AI relevant: 1.62%
- China-affiliated, Chinese-language articles in last five years: 174,634
  - AI relevant: 0.86%
- China-affiliated, all articles in last five years: 2,578,283
  - AI relevant: 1.24%
- I'm confused why the first two numbers don't sum to the third number. Maybe most articles are a mixture of languages in some way?
  - Ah, it's measuring the percentage of articles in the cluster that are Chinese. So it's the _clusters_ that are a mixture of languages. That makes sense.
- So these numbers indicate that there are more clusters of "research that has a Chinese-language body, title or abstract", than there are clusters of "research that _only_ has a version with an English title or abstract".
  - The latter has twice the rate of AI-relevant articles. So AI article count has a smaller difference: 576 English-language vs. 1500 Chinese-language.
    - This sample size is pretty small.
  - Publications in the former category may still have English versions available.
  - Overall this updates me towards more Chinese-language AI research than I thought. But it's still pretty unclear what the fraction of exclusively Chinese-language articles vs. English articles is.

## Persistence analysis

- How to do this?
  - Cut off the data at 2020, or the halfway point 2017
  - Look at the period of 2017 to present
  - 2010, 2013, 2016, 2019, 2022
  - 2011, 2014, 2017, 2020, 2023
  - 2010, 2014, 2018, 2022
  - How do I cut off the data to a certain start and end date?
  - Well, I think we may already have this functionality. We used to do it for the time series. We just need to do it for the aggregate results.
  - Intervene at the stage where data is bucketed by year. Then filter the years.
- Ok, how to keep the results safe?
  - Copy the current results to archive them, AND make a custom results directory for filtering.
- Execution
  - 1000 bootstrap samples took about 10 minutes to process
- Results - 2020 cutoff
  - Includes 2020
  - Hmm, maybe I should have cut off at 2019
  - At any rate, the publication results are similar. Most high-level conclusions hold.
  - IBM has more publications than Google.
  - Google then Microsoft still lead on citations.
  - Chinese labs still lag on citations
  - Average number of authors is lower for the middle cluster of labs in the citations-authors phase plot. NVIDIA, Baidu and Tencent are a bit closer together. But broadly the same picture.
- Sense check: are the authors counts moving?
  - Yeah definitely. It's just that IBM doesn't move much.
  - Oops, mucked up. Should cut off at 2016 inclusive if the other set is 2017 - 2023.

## Effect of 2017 AlexNet paper

- This paper has wrong affiliations. And I don't think we should count it at all because it's a reprint of a 2012 paper.
- Removing the 2017 AlexNet paper
- Using the original dataset rather than bootstrapping - but to preserve code, I'm putting in a "mock" feature into the bootstrapping code.
- Effect on citation count
  - Everything looks unchanged except OpenAI, which changes by a relatively small amount and doesn't change OpenAI's rank.
  - Google also changes ever-so-slightly because it also had affiliation on the 2017 AlexNet paper.
- Effect on citations per author
  - All companies look much more different here - why?
  - Not a drastic change but a notable change. Maybe almost the kind of change between 2010--2016 and 2017--2023.
  - Given the citation counts were basically unchanged but for OpenAI, it must be the author counts that differ.
  - Could bootstrapping really be having this effect? I'd expect it to 
- Current author counts without AlexNet paper:

```
[{'Meta': <xarray.DataArray (year: 14)>
  array([ 1.00e+01,  2.90e+01,  2.50e+01,  4.20e+01,  7.30e+01,  9.10e+01,
          1.21e+02,  1.96e+02,  3.40e+02,  6.03e+02,  9.27e+02,  1.10e+03,
          4.53e+02,  9.60e+01])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Google': <xarray.DataArray (year: 14)>
  array([ 2.41e+02,  2.89e+02,  3.27e+02,  3.53e+02,  3.84e+02,  5.27e+02,
          7.96e+02,  8.71e+02,  1.32e+03,  1.86e+03,  2.15e+03,  2.22e+03,
          1.51e+03,  8.90e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Quansight': <xarray.DataArray (year: 2)>
  array([ 4.00e+00,  1.00e+00])
  Coordinates:
    * year     (year) int64 2020 2022,
  'Enthought': <xarray.DataArray (year: 8)>
  array([ 1.00e+00,  1.00e+00,  1.00e+00,  2.00e+00,  1.00e+00,  7.00e+00,
          3.00e+00,  3.00e+00])
  Coordinates:
    * year     (year) int64 2010 2011 2014 2016 2017 2019 2020 2021,
  'DeepMind': <xarray.DataArray (year: 12)>
  array([ 1.00e+00,  7.00e+00,  4.00e+00,  3.40e+01,  8.70e+01,  1.00e+02,
          1.75e+02,  2.10e+02,  2.61e+02,  2.77e+02,  2.57e+02,  9.20e+01])
  Coordinates:
    * year     (year) int64 2011 2013 2014 2015 2016 ... 2019 2020 2021 2022 2023,
  'Microsoft': <xarray.DataArray (year: 14)>
  array([ 7.63e+02,  7.46e+02,  8.14e+02,  8.75e+02,  8.90e+02,  8.13e+02,
          8.01e+02,  8.20e+02,  9.63e+02,  1.18e+03,  1.46e+03,  1.60e+03,
          1.18e+03,  7.33e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'IBM': <xarray.DataArray (year: 14)>
  array([ 9.37e+02,  1.07e+03,  9.56e+02,  1.01e+03,  9.70e+02,  9.03e+02,
          9.66e+02,  1.06e+03,  1.22e+03,  1.34e+03,  1.26e+03,  1.32e+03,
          8.85e+02,  4.48e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Amazon': <xarray.DataArray (year: 14)>
  array([ 9.00e+00,  1.30e+01,  1.80e+01,  2.50e+01,  4.30e+01,  6.10e+01,
          6.20e+01,  1.37e+02,  2.84e+02,  5.15e+02,  7.17e+02,  1.01e+03,
          8.82e+02,  4.81e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'OpenAI': <xarray.DataArray (year: 8)>
  array([ 1.20e+01,  2.30e+01,  3.20e+01,  4.90e+01,  4.30e+01,  4.90e+01,
          2.90e+01,  1.00e+01])
  Coordinates:
    * year     (year) int64 2016 2017 2018 2019 2020 2021 2022 2023,
  'Adobe': <xarray.DataArray (year: 14)>
  array([ 2.50e+01,  4.30e+01,  3.90e+01,  4.60e+01,  5.20e+01,  6.10e+01,
          8.50e+01,  1.35e+02,  1.75e+02,  2.04e+02,  2.30e+02,  2.35e+02,
          2.17e+02,  1.65e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Netflix': <xarray.DataArray (year: 12)>
  array([ 4.00e+00,  4.00e+00,  3.00e+00,  1.10e+01,  1.50e+01,  9.00e+00,
          2.00e+01,  2.50e+01,  3.20e+01,  4.20e+01,  2.70e+01,  1.10e+01])
  Coordinates:
    * year     (year) int64 2012 2013 2014 2015 2016 ... 2019 2020 2021 2022 2023,
  'Intel': <xarray.DataArray (year: 14)>
  array([ 3.37e+02,  3.84e+02,  3.71e+02,  4.74e+02,  4.48e+02,  4.82e+02,
          4.73e+02,  4.66e+02,  6.09e+02,  7.02e+02,  7.50e+02,  8.40e+02,
          7.21e+02,  3.30e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Huawei': <xarray.DataArray (year: 14)>
  array([ 9.50e+01,  1.11e+02,  1.63e+02,  1.48e+02,  1.70e+02,  2.70e+02,
          2.65e+02,  3.14e+02,  3.61e+02,  5.82e+02,  7.48e+02,  1.24e+03,
          1.19e+03,  7.23e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Salesforce': <xarray.DataArray (year: 11)>
  array([ 2.00e+00,  4.00e+00,  1.00e+00,  3.00e+00,  5.00e+00,  1.10e+01,
          1.40e+01,  3.70e+01,  6.20e+01,  4.60e+01,  3.40e+01])
  Coordinates:
    * year     (year) int64 2011 2012 2013 2016 2017 2018 2019 2020 2021 2022 2023,
  'NEC': <xarray.DataArray (year: 14)>
  array([ 1.71e+02,  1.60e+02,  1.46e+02,  1.96e+02,  1.37e+02,  1.08e+02,
          1.11e+02,  1.02e+02,  1.28e+02,  1.84e+02,  1.81e+02,  1.83e+02,
          1.84e+02,  9.80e+01])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Baidu': <xarray.DataArray (year: 14)>
  array([ 3.10e+01,  2.10e+01,  3.50e+01,  5.10e+01,  3.60e+01,  7.60e+01,
          1.59e+02,  1.12e+02,  1.73e+02,  3.32e+02,  3.68e+02,  4.57e+02,
          4.05e+02,  2.09e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Nvidia': <xarray.DataArray (year: 14)>
  array([ 2.50e+01,  2.90e+01,  3.60e+01,  3.60e+01,  3.30e+01,  5.00e+01,
          7.90e+01,  9.70e+01,  1.76e+02,  2.91e+02,  3.39e+02,  3.22e+02,
          2.83e+02,  1.92e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Yandex': <xarray.DataArray (year: 14)>
  array([ 6.00e+00,  1.40e+01,  1.30e+01,  1.50e+01,  2.10e+01,  3.00e+01,
          3.20e+01,  1.80e+01,  2.50e+01,  2.50e+01,  3.30e+01,  2.80e+01,
          1.80e+01,  6.00e+00])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Twitter': <xarray.DataArray (year: 14)>
  array([ 1.00e+00,  1.00e+01,  7.00e+00,  1.20e+01,  2.20e+01,  2.00e+01,
          1.30e+01,  1.05e+02,  7.60e+01,  1.29e+02,  1.71e+02,  7.70e+01,
          6.00e+01,  1.20e+01])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Uber': <xarray.DataArray (year: 9)>
  array([ 4.00e+00,  1.30e+01,  2.70e+01,  3.90e+01,  7.50e+01,  8.30e+01,
          4.10e+01,  1.50e+01,  3.00e+00])
  Coordinates:
    * year     (year) int64 2011 2016 2017 2018 2019 2020 2021 2022 2023,
  'Tencent': <xarray.DataArray (year: 14)>
  array([ 6.00e+00,  8.00e+00,  2.00e+01,  6.00e+00,  1.50e+01,  3.50e+01,
          4.20e+01,  1.04e+02,  2.36e+02,  4.15e+02,  6.07e+02,  7.63e+02,
          9.65e+02,  4.94e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Naver': <xarray.DataArray (year: 14)>
  array([ 2.00e+00,  2.00e+00,  1.00e+00,  6.00e+00,  6.00e+00,  8.00e+00,
          2.80e+01,  5.00e+01,  5.10e+01,  1.09e+02,  1.32e+02,  1.51e+02,
          1.73e+02,  7.20e+01])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Alibaba': <xarray.DataArray (year: 14)>
  array([ 5.00e+00,  1.50e+01,  9.00e+00,  8.00e+00,  2.60e+01,  2.70e+01,
          3.60e+01,  9.80e+01,  2.86e+02,  5.94e+02,  8.66e+02,  1.20e+03,
          1.10e+03,  5.65e+02])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2019 2020 2021 2022 2023,
  'Xerox': <xarray.DataArray (year: 13)>
  array([ 6.10e+01,  6.80e+01,  8.40e+01,  6.90e+01,  6.30e+01,  8.30e+01,
          9.40e+01,  5.40e+01,  1.60e+01,  7.00e+00,  1.30e+01,  9.00e+00,
          2.00e+00])
  Coordinates:
    * year     (year) int64 2010 2011 2012 2013 2014 ... 2018 2019 2020 2021 2022,
  'Group Sense': <xarray.DataArray (year: 12)>
  array([ 2.00e+00,  1.00e+00,  1.00e+00,  4.00e+00,  2.30e+01,  4.40e+01,
          6.50e+01,  1.15e+02,  1.68e+02,  1.52e+02,  1.98e+02,  1.02e+02])
  Coordinates:
    * year     (year) int64 2010 2012 2013 2015 2016 ... 2019 2020 2021 2022 2023}]
```

- `institution_mean_authors_stats` without bootstrap:

```
defaultdict(dict,
            {'Meta': {'mean': 293.42857142857144,
              'median': 293.42857142857144,
              'std': 0.0,
              'ci': array([ 2.93e+02,  2.93e+02])},
             'Google': {'mean': 980.9285714285714,
              'median': 980.9285714285714,
              'std': 0.0,
              'ci': array([ 9.81e+02,  9.81e+02])},
             'Quansight': {'mean': 2.5,
              'median': 2.5,
              'std': 0.0,
              'ci': array([ 2.50e+00,  2.50e+00])},
             'Enthought': {'mean': 2.375,
              'median': 2.375,
              'std': 0.0,
              'ci': array([ 2.38e+00,  2.38e+00])},
             'DeepMind': {'mean': 125.41666666666667,
              'median': 125.41666666666667,
              'std': 0.0,
              'ci': array([ 1.25e+02,  1.25e+02])},
             'Microsoft': {'mean': 973.9285714285714,
              'median': 973.9285714285714,
              'std': 0.0,
              'ci': array([ 9.74e+02,  9.74e+02])},
             'IBM': {'mean': 1024.5714285714287,
              'median': 1024.5714285714287,
              'std': 0.0,
              'ci': array([ 1.02e+03,  1.02e+03])},
             'Amazon': {'mean': 303.92857142857144,
              'median': 303.92857142857144,
              'std': 0.0,
              'ci': array([ 3.04e+02,  3.04e+02])},
             'OpenAI': {'mean': 30.875,
              'median': 30.875,
              'std': 0.0,
              'ci': array([ 3.09e+01,  3.09e+01])},
             'Adobe': {'mean': 122.28571428571429,
              'median': 122.28571428571429,
              'std': 0.0,
              'ci': array([ 1.22e+02,  1.22e+02])},
             'Netflix': {'mean': 16.916666666666668,
              'median': 16.916666666666668,
              'std': 0.0,
              'ci': array([ 1.69e+01,  1.69e+01])},
             'Intel': {'mean': 527.6428571428571,
              'median': 527.6428571428571,
              'std': 0.0,
              'ci': array([ 5.28e+02,  5.28e+02])},
             'Huawei': {'mean': 456.2142857142857,
              'median': 456.2142857142857,
              'std': 0.0,
              'ci': array([ 4.56e+02,  4.56e+02])},
             'Salesforce': {'mean': 19.90909090909091,
              'median': 19.90909090909091,
              'std': 0.0,
              'ci': array([ 1.99e+01,  1.99e+01])},
             'NEC': {'mean': 149.21428571428572,
              'median': 149.21428571428572,
              'std': 0.0,
              'ci': array([ 1.49e+02,  1.49e+02])},
             'Baidu': {'mean': 176.07142857142858,
              'median': 176.07142857142858,
              'std': 0.0,
              'ci': array([ 1.76e+02,  1.76e+02])},
             'Nvidia': {'mean': 142.0,
              'median': 142.0,
              'std': 0.0,
              'ci': array([ 1.42e+02,  1.42e+02])},
             'Yandex': {'mean': 20.285714285714285,
              'median': 20.285714285714285,
              'std': 0.0,
              'ci': array([ 2.03e+01,  2.03e+01])},
             'Twitter': {'mean': 51.07142857142857,
              'median': 51.07142857142857,
              'std': 0.0,
              'ci': array([ 5.11e+01,  5.11e+01])},
             'Uber': {'mean': 33.333333333333336,
              'median': 33.333333333333336,
              'std': 0.0,
              'ci': array([ 3.33e+01,  3.33e+01])},
             'Tencent': {'mean': 265.42857142857144,
              'median': 265.42857142857144,
              'std': 0.0,
              'ci': array([ 2.65e+02,  2.65e+02])},
             'Naver': {'mean': 56.5,
              'median': 56.5,
              'std': 0.0,
              'ci': array([ 5.65e+01,  5.65e+01])},
             'Alibaba': {'mean': 345.07142857142856,
              'median': 345.07142857142856,
              'std': 0.0,
              'ci': array([ 3.45e+02,  3.45e+02])},
             'Xerox': {'mean': 47.92307692307692,
              'median': 47.92307692307692,
              'std': 0.0,
              'ci': array([ 4.79e+01,  4.79e+01])},
             'Group Sense': {'mean': 72.91666666666667,
              'median': 72.91666666666667,
              'std': 0.0,
              'ci': array([ 7.29e+01,  7.29e+01])}})
```

- Running with the 1000-iter bootstrap, the author counts are exactly the same and I only see a difference in OpenAI citations per author.
- `institution_mean_authors_stats`:

```
defaultdict(dict,
            {'Intel': {'mean': 361.3795,
              'median': 361.07142857142856,
              'std': 4.952961920993975,
              'ci': array([ 3.54e+02,  3.70e+02])},
             'Microsoft': {'mean': 729.8762142857144,
              'median': 729.7857142857143,
              'std': 6.160819134097449,
              'ci': array([ 7.20e+02,  7.40e+02])},
             'Huawei': {'mean': 322.7213571428572,
              'median': 322.6071428571429,
              'std': 3.9656247410382512,
              'ci': array([ 3.16e+02,  3.29e+02])},
             'Google': {'mean': 722.2392142857143,
              'median': 722.5,
              'std': 8.03439646305248,
              'ci': array([ 7.09e+02,  7.35e+02])},
             'Nvidia': {'mean': 103.11407142857142,
              'median': 103.10714285714286,
              'std': 2.363554689531884,
              'ci': array([ 9.93e+01,  1.07e+02])},
             'Alibaba': {'mean': 250.10863736263738,
              'median': 249.92857142857142,
              'std': 4.016567075753233,
              'ci': array([ 2.44e+02,  2.57e+02])},
             'Tencent': {'mean': 196.82499450549452,
              'median': 196.75,
              'std': 3.0242102984025254,
              'ci': array([ 1.92e+02,  2.02e+02])},
             'Amazon': {'mean': 214.80407142857143,
              'median': 214.85714285714286,
              'std': 3.778778654188009,
              'ci': array([ 2.08e+02,  2.21e+02])},
             'Group Sense': {'mean': 56.930034343434336,
              'median': 56.45454545454545,
              'std': 4.566981631512569,
              'ci': array([ 5.08e+01,  6.50e+01])},
             'Adobe': {'mean': 96.0182142857143,
              'median': 96.07142857142857,
              'std': 1.5909501316598744,
              'ci': array([ 9.34e+01,  9.86e+01])},
             'DeepMind': {'mean': 93.40836212121212,
              'median': 92.75,
              'std': 5.62292233145222,
              'ci': array([ 8.52e+01,  1.04e+02])},
             'Meta': {'mean': 216.2165,
              'median': 216.28571428571428,
              'std': 3.8169466634513842,
              'ci': array([ 2.10e+02,  2.22e+02])},
             'IBM': {'mean': 734.613,
              'median': 734.7142857142857,
              'std': 7.444262026718899,
              'ci': array([ 7.23e+02,  7.47e+02])},
             'Naver': {'mean': 41.83186213786214,
              'median': 41.57142857142857,
              'std': 2.6909020312556002,
              'ci': array([ 3.79e+01,  4.67e+01])},
             'Uber': {'mean': 23.341488095238095,
              'median': 23.333333333333332,
              'std': 1.595907580213337,
              'ci': array([ 2.09e+01,  2.60e+01])},
             'Netflix': {'mean': 12.17019696969697,
              'median': 12.166666666666666,
              'std': 0.7925127001731398,
              'ci': array([ 1.09e+01,  1.35e+01])},
             'Baidu': {'mean': 127.67914285714285,
              'median': 127.78571428571429,
              'std': 3.2012417361176,
              'ci': array([ 1.22e+02,  1.33e+02])},
             'NEC': {'mean': 104.54792857142859,
              'median': 104.71428571428571,
              'std': 2.427057047797869,
              'ci': array([ 1.00e+02,  1.08e+02])},
             'Twitter': {'mean': 33.75693956043956,
              'median': 33.785714285714285,
              'std': 2.1722442162709443,
              'ci': array([ 3.03e+01,  3.73e+01])},
             'Xerox': {'mean': 34.81775641025641,
              'median': 34.69230769230769,
              'std': 1.528238995440851,
              'ci': array([ 3.25e+01,  3.76e+01])},
             'Salesforce': {'mean': 15.579245454545454,
              'median': 15.363636363636363,
              'std': 1.3052925346746762,
              'ci': array([ 1.36e+01,  1.81e+01])},
             'Yandex': {'mean': 13.920846153846155,
              'median': 13.928571428571429,
              'std': 0.7151118883086662,
              'ci': array([ 1.27e+01,  1.51e+01])},
             'OpenAI': {'mean': 23.315375,
              'median': 23.375,
              'std': 1.6766478414905737,
              'ci': array([ 2.04e+01,  2.59e+01])},
             'Enthought': {'mean': 2.080461904761905,
              'median': 2.1666666666666665,
              'std': 0.5273604562501122,
              'ci': array([ 1.25e+00,  3.00e+00])},
             'Quansight': {'mean': 2.378,
              'median': 2.5,
              'std': 1.06986728148869,
              'ci': array([ 1.00e+00,  4.00e+00])}})
```

- Let's look at Google as an example. No-bootstrap followed by bootstrap.

```
             'Google': {'mean': 980.9285714285714,
              'median': 980.9285714285714,
              'std': 0.0,
              'ci': array([ 9.81e+02,  9.81e+02])},

             'Google': {'mean': 722.2392142857143,
              'median': 722.5,
              'std': 8.03439646305248,
              'ci': array([ 7.09e+02,  7.35e+02])},  
```

- Yeah so the no-boostrap result is quite a bit higher than the bootstrap result
- What's more, the no-bootstrap result is way outside the 95th percentile given by the bootstrap
- Why would this bias be present?
- Eyeballing it, the direction of this bias is consistent, or at least the prevailing direction. Unbootstrapped gives higher author counts than bootstrapped.
- The bootstrap is supposed to vary which publications are in the set.
- Some publications will be missing, while others will be duplicated.
- Assume the distribution of author counts is heavy-tailed
- So when you bootstrap, low-author-count publications are more likely to appear in the sample because those are more common.
  - I don't think this is true. Bootstrapping should be unbiased. This small experiment written by GPT-4 provides support:

```
import numpy as np
import matplotlib.pyplot as plt

# Generate log-normal data
np.random.seed(0)
original_data = np.random.lognormal(mean=0, sigma=1, size=1000)

# Bootstrap
n_bootstrap = 1000
bootstrap_means = np.zeros(n_bootstrap)

for i in range(n_bootstrap):
    bootstrap_sample = np.random.choice(original_data, size=len(original_data), replace=True)
    bootstrap_means[i] = np.mean(bootstrap_sample)

# Plot
plt.hist(bootstrap_means, bins=30, alpha=0.75)
plt.xlabel('Bootstrap Means')
plt.ylabel('Frequency')
plt.show()
```

- The mean of bootstrap means and the original data mean are very close together - 1.554 vs. 1.556.
- So there's some other effect. Can't rule out a bug at this point.
- At this point it would be best to re-run all the results without bootstrapping just to be safe.

# 2023-Oct-24

## Searching works using raw affiliation string

```python
institution_works = merge_pages(
    Works() \
        .filter(raw_affiliation_string={'search': 'open ai'}) \
        .filter(concepts={"id": 'https://openalex.org/C154945302|https://openalex.org/C119857082'}) \
        .filter(from_publication_date="2010-01-01") \
        .filter(to_publication_date="2023-06-01") \
        .paginate(per_page=200, n_max=int(1e6))        
)
len(institution_works)
```

- 'openai' returns 156 works
  - Quick Ctrl+F doesn't show false positives
- 'open ai' returns 83 works
  - Some of these are legit, others are not e.g. 'Norwegian Open AI Lab'
- Maybe should just use raw affiliation string rather than manually add OpenAI works?

```
Salesforce
2page [00:03,  1.86s/page]
Raw affiliation keywords: ['salesforce', 'sales force']
    Works: 236
    Raw affiliation count: 236
    Raw affiliation fraction: 1.0
```

- Weird stuff going on with Amazon
  - Could be a multiple IDs issue

```
Raw affiliation keywords: ['amazon']
No raw affiliation match: https://openalex.org/W2963961878 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963423916 ['', '', '']
No raw affiliation match: https://openalex.org/W2405578611 ['']
No raw affiliation match: https://openalex.org/W2964222566 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2890410208 ['', '', '']
No raw affiliation match: https://openalex.org/W2970697704 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962717849 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963352809 ['', '']
No raw affiliation match: https://openalex.org/W2971105107 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2889928394 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2804292122 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995589713 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963419583 ['', '', '']
No raw affiliation match: https://openalex.org/W2787733970 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2803023299 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963633299 ['', '']
No raw affiliation match: https://openalex.org/W3034255912 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2792839479 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964224652 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2952113915 ['', '', '']
No raw affiliation match: https://openalex.org/W2963809789 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2964092925 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962739340 ['', '', '']
No raw affiliation match: https://openalex.org/W2963569817 ['', '', '']
No raw affiliation match: https://openalex.org/W3030754432 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2798761464 ['']
No raw affiliation match: https://openalex.org/W2785542264 ['', '', '']
No raw affiliation match: https://openalex.org/W2789566302 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2891146651 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2908007030 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963973577 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2991522342 ['', '', '']
No raw affiliation match: https://openalex.org/W2987154291 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2885950361 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2739473244 ['', '', '']
No raw affiliation match: https://openalex.org/W2897003273 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114916066 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2898917980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971274354 ['', '', '']
No raw affiliation match: https://openalex.org/W2995636882 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3106484161 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2985353426 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963547384 ['', '']
No raw affiliation match: https://openalex.org/W2963756980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2803533564 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963499433 ['', '', '']
No raw affiliation match: https://openalex.org/W2970176896 ['', '', '']
No raw affiliation match: https://openalex.org/W2572670101 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963162885 ['', '', '']
No raw affiliation match: https://openalex.org/W2972425456 ['', '', '']
No raw affiliation match: https://openalex.org/W2950695840 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970421227 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963532386 ['']
No raw affiliation match: https://openalex.org/W2964123521 ['', '', '']
No raw affiliation match: https://openalex.org/W2963355572 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2396230943 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2945315238 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962682420 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2986068180 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963882293 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964022663 ['', '', '']
No raw affiliation match: https://openalex.org/W2932319281 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3035131649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2971342441 ['', '', '']
No raw affiliation match: https://openalex.org/W3037724138 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3115851078 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2740210681 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963062785 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2404620314 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964168155 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2970562710 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3146670357 ['', '', '']
No raw affiliation match: https://openalex.org/W2053878386 ['Embrapa Amazônia Oriental, Trav. Dr. Enéas Pinheiro s/n°, Caixa Postal, 48, CEP 66095-100 Belém, PA, Brazil', 'Embrapa Amazônia Oriental, Trav. Dr. Enéas Pinheiro s/n°, Caixa Postal, 48, CEP 66095-100 Belém, PA, Brazil', 'Departamento de Biologia Geral Universidade Federal de Viçosa (UFV) Viçosa Minas Gerais Brazil', 'Embrapa Amazônia Ocidental, Rodovia AM 010, km 29, Caixa Postal 319, CEP 69010-970 Manaus, AM, Brazil', 'Embrapa Amazônia Ocidental, Rodovia AM 010, km 29, Caixa Postal 319, CEP 69010-970 Manaus, AM, Brazil', 'Marborges Agroindústria S.A., Rodovia Virgílio Serrão Sacramento, km 56, s/n, Caixa Postal 17, CEP 68 450-000 Mojú, Pará, Brazil', 'Marborges Agroindústria S.A., Rodovia Virgílio Serrão Sacramento, km 56, s/n, Caixa Postal 17, CEP 68 450-000 Mojú, Pará, Brazil']
No raw affiliation match: https://openalex.org/W2752630748 ['', '']
No raw affiliation match: https://openalex.org/W2941649920 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2530797269 ['Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Embrapa Amazônia Oriental, Travessa Doutor Enéas Pinheiro, CEP 66.095-903, Belém, PA, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Embrapa Amazônia Oriental, Travessa Doutor Enéas Pinheiro, CEP 66.095-903, Belém, PA, Brazil']
No raw affiliation match: https://openalex.org/W2950846878 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2440926996 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2798583685 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964315715 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3037181583 ['', '', '']
No raw affiliation match: https://openalex.org/W2972954809 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2748594250 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2949270253 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2952307697 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2787049730 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2962700197 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963866450 ['', '', '']
No raw affiliation match: https://openalex.org/W3102847511 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2513928851 ['', '', '']
No raw affiliation match: https://openalex.org/W2965145066 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W2741511332 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2935542736 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2955711416 ['', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3000642987 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2771630689 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2913153410 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962693275 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963471154 ['', '']
No raw affiliation match: https://openalex.org/W2995455605 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2995653869 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2996463194 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2962830484 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963546161 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2977910558 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2990176236 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3030045039 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3168663263 ['Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', '', "King's College London", 'Facebook']
No raw affiliation match: https://openalex.org/W2739724844 ['', '', '']
No raw affiliation match: https://openalex.org/W2965158072 ['', '']
No raw affiliation match: https://openalex.org/W2970799668 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2972838300 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2973230496 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3007978994 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3105081824 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2797297135 ['', '']
No raw affiliation match: https://openalex.org/W2949370368 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965734314 ['', '']
No raw affiliation match: https://openalex.org/W2966246399 ['', '', '']
No raw affiliation match: https://openalex.org/W2971200681 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2972549707 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3036435426 ['University of Washington ;', 'University of Washington ;', '', 'University of Washington ;']
No raw affiliation match: https://openalex.org/W3037333676 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3098938591 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3102021588 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3102649892 ['', '', '']
No raw affiliation match: https://openalex.org/W3198664535 ['Bristol Doctoral College', '', '']
No raw affiliation match: https://openalex.org/W2568095718 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2759511005 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2808456396 ['', '', '']
No raw affiliation match: https://openalex.org/W2963891006 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2969307504 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W2970687683 ['', '', '']
No raw affiliation match: https://openalex.org/W3093818688 ['', '', '']
No raw affiliation match: https://openalex.org/W3115091907 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3170943566 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2921071577 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2951575093 ['', '#N#‡#N#Georgia Institute of Technology#N#', '#N#‡#N#Georgia Institute of Technology#N#']
No raw affiliation match: https://openalex.org/W2970403389 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2996680032 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3102303514 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104866818 ['', '']
No raw affiliation match: https://openalex.org/W3111605943 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3117752211 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3169436550 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2609616693 ['', '', '']
No raw affiliation match: https://openalex.org/W2741018521 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2748488613 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2787178450 ['Carnegie Mellon University', 'Carnegie Mellon University', '', '']
No raw affiliation match: https://openalex.org/W2790259362 ['', '', '']
No raw affiliation match: https://openalex.org/W2889736774 ['', '']
No raw affiliation match: https://openalex.org/W2972384212 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2973227003 ['', 'Amazon', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2985600242 ['', '', '']
No raw affiliation match: https://openalex.org/W3035753785 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3094953545 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3095735913 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3099225546 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3100879603 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2574856563 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2607593044 ['', '', '']
No raw affiliation match: https://openalex.org/W2764124976 ['', '']
No raw affiliation match: https://openalex.org/W2783719374 ['', '', '']
No raw affiliation match: https://openalex.org/W2803971899 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2805097732 ['', '', '']
No raw affiliation match: https://openalex.org/W2907475315 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2912901814 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2912918913 ['', '', '']
No raw affiliation match: https://openalex.org/W2949176913 ['Massachusetts Institute Of Technology#TAB#', 'Google,,,,,', 'Google,,,,,', '']
No raw affiliation match: https://openalex.org/W2964038586 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2972930415 ['', '', '']
No raw affiliation match: https://openalex.org/W3034272764 ['', '', '']
No raw affiliation match: https://openalex.org/W3037093830 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3043574444 ['University of California–Berkeley.', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093155142 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3100400430 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104194380 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3105184920 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2784023976 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2834342720 ['', '']
No raw affiliation match: https://openalex.org/W2965920802 ['', '', '']
No raw affiliation match: https://openalex.org/W2970020110 ['']
No raw affiliation match: https://openalex.org/W2971064282 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971310236 ['']
No raw affiliation match: https://openalex.org/W2983689619 ['', '', '']
No raw affiliation match: https://openalex.org/W2983722336 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3037600752 ['', '', '']
No raw affiliation match: https://openalex.org/W3103978933 ['', '', '']
No raw affiliation match: https://openalex.org/W3105580455 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3129089995 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3190185140 ['', '', '']
No raw affiliation match: https://openalex.org/W3211005660 ['', '', '']
No raw affiliation match: https://openalex.org/W2572569512 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2591784896 ['', '', '']
No raw affiliation match: https://openalex.org/W2606602301 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2607957941 ['Universidade Federal de Vicosa, Viçosa, Brazil', 'Universidade Federal de Vicosa, Viçosa, Brazil', 'Embrapa Amazônia Ocidental', 'EMBRAPA/Florestas, Colombo, Brazil', 'Embrapa Amazônia Ocidental', 'Universidade Federal de Vicosa, Viçosa, Brazil']
No raw affiliation match: https://openalex.org/W2885826215 ['', '']
No raw affiliation match: https://openalex.org/W2962985479 ['', '', '']
No raw affiliation match: https://openalex.org/W2963360277 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2966111260 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995444997 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3092956463 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3099971460 ['', '', '']
No raw affiliation match: https://openalex.org/W1977557220 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2251165721 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2748606298 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2806804106 ['', '', '']
No raw affiliation match: https://openalex.org/W2809456172 ['', '', '']
No raw affiliation match: https://openalex.org/W2929139284 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2942943100 ['', '', '']
No raw affiliation match: https://openalex.org/W2951657084 ['', '', '']
No raw affiliation match: https://openalex.org/W2951688832 ['Univ. of Cambridge', 'Univ. of Cambridge', '', '']
No raw affiliation match: https://openalex.org/W2951876757 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2954465950 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963710187 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965435631 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2966441967 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970192826 ['University of California Santa Barbara', 'Google,,,,,', 'Carnegie Mellon University', '']
No raw affiliation match: https://openalex.org/W2970379104 ['Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', '']
No raw affiliation match: https://openalex.org/W2971715690 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2975704529 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995574330 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3028954259 ['', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3035639219 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3038036095 ['', '']
No raw affiliation match: https://openalex.org/W3093557617 ['', '', '', 'National University of Singapore,']
No raw affiliation match: https://openalex.org/W3099417667 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3100387437 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3101154177 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3120777408 ['', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3130986574 ['Amazon', '', '', '', '']
No raw affiliation match: https://openalex.org/W3138310836 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3199004261 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214013345 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W1893496786 ['Universidade Federal de Viçosa, Viçosa, Brasil', 'Universidade Federal de Viçosa, Viçosa, Brasil', 'Embrapa Amazônia Oriental,  Brasil', 'Embrapa Florestas, Colombo, Brasil', 'Universidade Federal de Viçosa, Viçosa, Brasil']
No raw affiliation match: https://openalex.org/W2186169017 ['Centro de Pesquisa Agloflorestal de Roraima, Brasil', 'Embrapa Agrossilvipastoril, Sinop, Brasil.', 'Centro Nacional de Pesquisa de Florestas, Colombo, Brasil', 'Embrapa Amazônia Oriental, Brasil']
No raw affiliation match: https://openalex.org/W2294378299 ['', '']
No raw affiliation match: https://openalex.org/W2476743944 ['', '', '']
No raw affiliation match: https://openalex.org/W2741102098 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2755926663 ['', '']
No raw affiliation match: https://openalex.org/W2762483932 ['', '', '']
No raw affiliation match: https://openalex.org/W2802455203 ['', '', '']
No raw affiliation match: https://openalex.org/W2804744697 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2806957444 ['', '']
No raw affiliation match: https://openalex.org/W2888195294 ['', '']
No raw affiliation match: https://openalex.org/W2890884631 ['', '', '']
No raw affiliation match: https://openalex.org/W2924551963 ['', 'Google,,,,,']
No raw affiliation match: https://openalex.org/W2949488962 ['', '', '']
No raw affiliation match: https://openalex.org/W2952907575 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962896386 ['', '', '']
No raw affiliation match: https://openalex.org/W2963645036 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971327614 ['', '']
No raw affiliation match: https://openalex.org/W2972297975 ['', '', 'Amazon']
No raw affiliation match: https://openalex.org/W2986670164 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3021046937 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3034799022 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3047199820 ['', '', '']
No raw affiliation match: https://openalex.org/W3054608853 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3096746890 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3108508289 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3158088536 ['', '', '']
No raw affiliation match: https://openalex.org/W3163695726 ['', '', '', '', '', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W2293535060 ['SRI-International', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2606847791 [', , Brasil.', 'Embrapa Amazônia Oriental, Brasil', 'Embrapa Amazônia Oriental, Brasil', 'Embrapa Mandioca e Fruticultura, Cruz das Almas, BA, Brasil', 'Embrapa Amazônia Oriental, Brasil']
No raw affiliation match: https://openalex.org/W2771346320 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2787770455 ['', '']
No raw affiliation match: https://openalex.org/W2799150749 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2900175074 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2922234509 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2942580059 ['', '', '']
No raw affiliation match: https://openalex.org/W2946444035 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2947647530 ['Univ. of California Davis', '', '', 'Univ. of California Davis', 'University of California-Los Angeles']
No raw affiliation match: https://openalex.org/W2950420475 ['', '', '']
No raw affiliation match: https://openalex.org/W2963054052 ['', '']
No raw affiliation match: https://openalex.org/W2980075309 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2985638129 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3006210468 ['', '', '']
No raw affiliation match: https://openalex.org/W3048758284 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3092630929 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3093159647 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097469673 ['', '', '']
No raw affiliation match: https://openalex.org/W3098331497 ['', '']
No raw affiliation match: https://openalex.org/W3099372209 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3112707533 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3113459090 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3116343068 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3128997953 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3153899207 ['', '']
No raw affiliation match: https://openalex.org/W3170280676 ['', '']
No raw affiliation match: https://openalex.org/W3174293169 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3177112880 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3179307988 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3195529751 ['University of Macau,Department of Computer and Information Science,Macau,China', '', 'University of Macau,Department of Computer and Information Science,Macau,China']
No raw affiliation match: https://openalex.org/W3212387080 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2143350841 ['', '', 'Universidade Federal do Espírito Santo', '', '', '', '', 'Universidade\xa0Federal do Rio Grande do Sul', '']
No raw affiliation match: https://openalex.org/W2221612594 ['Indian Institute of Technology Kanpur', '']
No raw affiliation match: https://openalex.org/W2741325996 ['', '', '']
No raw affiliation match: https://openalex.org/W2745931053 ['', '', '']
No raw affiliation match: https://openalex.org/W2747937300 ['LANCASTER UNIVERSITY,', 'Linköping University', '', '']
No raw affiliation match: https://openalex.org/W2772956802 ['', '', '']
No raw affiliation match: https://openalex.org/W2778098837 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2898152919 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2949736580 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2954154738 ['Instituto de Desenvolvimento Sustentável Mamirauá, Tefé, AM', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'EMBRAPA Amazônia Oriental, Belém, PA', 'Universidade Federal Rural da Amazônia, Campus Capitão Poço, Capitão Poço, PA', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'EMBRAPA Amazônia Oriental, Belém, PA', 'Universidade Federal do Recôncavo da Bahia, Cruz das Almas-BA', 'Universidade Federal do Sul da Bahia, Itabuna, BA']
No raw affiliation match: https://openalex.org/W2963489350 ['', '']
No raw affiliation match: https://openalex.org/W2966061665 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970001856 ['Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', '', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society']
No raw affiliation match: https://openalex.org/W2971727319 ['', '', '']
No raw affiliation match: https://openalex.org/W2989919526 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3002279815 ['', '']
No raw affiliation match: https://openalex.org/W3010872790 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3037361235 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3037501086 ['', '']
No raw affiliation match: https://openalex.org/W3037562253 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3047821330 ['', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3092973380 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093898938 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097484451 ['', '']
No raw affiliation match: https://openalex.org/W3100679627 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3105973526 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3110740243 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114972653 ['', '']
No raw affiliation match: https://openalex.org/W3117968175 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3157624638 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3157793776 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3158811267 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3166512924 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3198633256 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3198973235 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3201234832 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3202216017 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3203598579 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214125927 ['', '', '', '']
No raw affiliation match: https://openalex.org/W1842617815 ['Dept. of Electr. Eng. & Comput. Sci, Univ. of Michigan, Ann Arbor, MI, USA', '', 'Inst. for Robot. & Intell. Machines, Georgia Inst. of Technol., Atlanta, GA, USA', 'Dept. of Electr. Eng. & Comput. Sci, Univ. of Michigan, Ann Arbor, MI, USA', 'Dept. of Computer Science and Information Engineering, National Taiwan University of Science and Technology, Taipei, Taiwan#TAB#']
No raw affiliation match: https://openalex.org/W2405490700 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2517120700 ['', '', '']
No raw affiliation match: https://openalex.org/W2556277930 ['', '', '']
No raw affiliation match: https://openalex.org/W2613023307 ['', '', '']
No raw affiliation match: https://openalex.org/W2761970834 ['Universidade Federal do Amazonas – UFAM, Avenida General Rodrigo Otávio, 6200, Coroado I, 69.800-900, Manaus, AM, Brasil', 'Instituto de Ciências Exatas e Tecnologia, Universidade Federal do Amazonas -UFAM, Rua Nossa Senhora do Rosário, 3863, Tiradentes, 69.103-128, Itacoatiara, AM, Brasil', 'Embrapa Rondônia, Rodovia Br-364, km 5,5, Zona Rural, caixa postal 127, 76.815-800, Porto Velho, RO, Brasil', 'Embrapa Amazônia Ocidental, Rodovia AM-10, km 29, (Estrada Manaus/Itacoatiara), caixa postal 319, 69.010-970, Manaus, AM, Brasil', 'Embrapa Rondônia, Rodovia Br-364, km 5,5, Zona Rural, caixa postal 127, 76.815-800, Porto Velho, RO, Brasil']
No raw affiliation match: https://openalex.org/W2794607286 ['', '', '']
No raw affiliation match: https://openalex.org/W2835534053 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2941044520 ['', '', 'Amazon', 'Amazon', 'Amazon']
No raw affiliation match: https://openalex.org/W2944332845 ['', 'Stanford University ()', '', '', 'Nanyang Technological Univ']
No raw affiliation match: https://openalex.org/W2947329949 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2949126650 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2949336561 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2951539692 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2955318955 ['', '', 'Amazon']
No raw affiliation match: https://openalex.org/W2962702400 ['', '', '']
No raw affiliation match: https://openalex.org/W2963431600 ['', '']
No raw affiliation match: https://openalex.org/W2964532051 ['Carnegie Mellon University', 'Google,,,,,', 'University of California Santa Barbara', '', 'Google,,,,,', 'Carnegie Mellon University']
No raw affiliation match: https://openalex.org/W2964713509 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2970751055 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2971019013 ['', '', '']
No raw affiliation match: https://openalex.org/W2974803251 ['', 'University of Edinburgh,']
No raw affiliation match: https://openalex.org/W2979618889 ['', '']
No raw affiliation match: https://openalex.org/W2980596743 ['', '', '', '', 'University of Notre Dame.']
No raw affiliation match: https://openalex.org/W2990201487 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995686152 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3009752645 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3015442441 ['', '', '']
No raw affiliation match: https://openalex.org/W3021802247 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3023778123 ['', '', '']
No raw affiliation match: https://openalex.org/W3037386667 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3045737996 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3046609253 ['Amazon', '', '', '', '']
No raw affiliation match: https://openalex.org/W3048118011 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3088291589 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3088860656 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093346478 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3095995205 ['', '', '']
No raw affiliation match: https://openalex.org/W3096157982 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3096572584 ['', 'Institute of Automation. Chinese Academy of Sciences', 'Institute of Automation. Chinese Academy of Sciences', '', '', '']
No raw affiliation match: https://openalex.org/W3096588269 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097731397 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3098281389 ['', '']
No raw affiliation match: https://openalex.org/W3099438082 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104098714 ['', '', '']
No raw affiliation match: https://openalex.org/W3104752986 ['', '', '']
No raw affiliation match: https://openalex.org/W3109833210 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114586309 ['Amazon', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3115419395 ['', '']
No raw affiliation match: https://openalex.org/W3117732268 ['', '', '']
No raw affiliation match: https://openalex.org/W3137189276 ['Embrapa  Amazônia  Oriental', 'Embrapa  Amazônia  Ocidental', 'Embrapa  Amazônia  Ocidental', 'Grupo  Marborges', 'Embrapa Café', 'Embrapa  Amazônia  Oriental']
No raw affiliation match: https://openalex.org/W3153201663 ['', '', 'Speechly', 'Speechly', '']
No raw affiliation match: https://openalex.org/W3154151461 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3157777096 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3158218109 ['', '', '']
No raw affiliation match: https://openalex.org/W3158731518 ['Statistics', '', 'Computer Science', '']
No raw affiliation match: https://openalex.org/W3161801451 ['', '', '', '', 'Amazon', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3165877604 ['', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3166129584 ['', 'Amazon']
No raw affiliation match: https://openalex.org/W3168415639 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3168872064 ['', '', '', '', '', 'Amazon', '']
No raw affiliation match: https://openalex.org/W3170730117 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3170752662 ['', '']
No raw affiliation match: https://openalex.org/W3171469166 ['', '', '']
No raw affiliation match: https://openalex.org/W3175179074 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3176048559 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3182974197 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183691183 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183925776 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3196193831 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3197575580 ['', '', '']
No raw affiliation match: https://openalex.org/W3198028464 ['', '']
No raw affiliation match: https://openalex.org/W3198604552 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3199117450 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3202074632 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3209015562 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211589367 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213189432 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213249234 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W4220969210 ['ISAC-Institute of Atmospheric Sciences and Climate, CNR, Italy', 'Departamento de Fisica, Universidade Federal de Santa Maria, Santa Maria, RS, Brazil; ISAC-Institute of Atmospheric Sciences and Climate, CNR, Italy', 'Department of Physics, Federal Institute of Para (IFPA), Belem, PA, Brazil; Instituto Nacional de Pesquisas da Amazonia (INPA-CLIAMB), Manaus, AM, Brazil', 'Instituto Nacional de Pesquisas da Amazonia (INPA-CLIAMB), Manaus, AM, Brazil', 'Departamento de Fisica, Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Universidade Federal do Rio Grande do Norte, Natal, RN, Brazil', 'Department of Pure and Applied Sciences (DiSPeA), Universit`a degli Studi di Urbino ‘Carlo Bo’,Italy', 'Instituto Nacional de Pesquisas Espaciais (INPE), Cachoeira Paulista, SP, Brazil', 'Embrapa Amazônia Oriental, Tv. Dr. Enéas Piheiro, s/n, Marco, CEP 66095-903, Caixa postal 48, Belém, Pará, Brasil', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, 55020 Mainz, Germany', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, 55020 Mainz, Germany']
No raw affiliation match: https://openalex.org/W4280591069 ['Institute of Atmospheric Sciences and Climate, Consiglio Nazionale delle Ricerche (ISAC-CNR), Italy; Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Department of Physics, Federal Institute of Pará (IFPA), Belém, PA, Brazil; Instituto Nacional de Pesquisas da Amazônia (INPA-CLIAMB), Manaus, AM, Brazil', 'Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Universidade Federal do Rio Grande do Norte, Natal, RN, Brazil', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, Mainz 55020, Germany', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, Mainz 55020, Germany', 'Instituto Nacional de Pesquisas Espaciais (INPE), Cachoeira Paulista, SP, Brazil', 'Embrapa Amazônia Oriental, Tv. Dr. Enéas Piheiro, s/n, Marco, Caixa postal 48, Belém, Pará CEP 66095-903, Brasil', 'Instituto Nacional de Pesquisas da Amazônia (INPA-CLIAMB), Manaus, AM, Brazil', 'Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Department of Pure and Applied Sciences (DiSPeA), Università degli Studi di Urbino ‘Carlo 20 \xa0Bo,Italy', 'Institute of Atmospheric Sciences and Climate, Consiglio Nazionale delle Ricerche (ISAC-CNR), Italy']
No raw affiliation match: https://openalex.org/W4295736883 ['Universidade Federal Rural da Amazônia', 'Universidade Estadual de Santa Cruz', 'Universidade Federal do Pará', 'Universidade Federal Rural da Amazônia', 'Universidade Federal Rural da Amazônia', 'Universidade Federal Rural da Amazônia', 'Universidade Federal do Pará', 'Universidade Federal do Pará', 'EMBRAPA - Amazônia Oriental', 'EMBRAPA - Amazônia Oriental']
No raw affiliation match: https://openalex.org/W4311799494 ['Embrapa Amazônia Oriental,  Brasil', 'Associação em Áreas de Assentamento no Estado do Maranhão,  Brasil']
No raw affiliation match: https://openalex.org/W1604162242 ['', '']
No raw affiliation match: https://openalex.org/W1605239498 ['Universidade Federal Rural da Amazônia/Laboratório de Química Ambiental', 'Instituto Sócio Ambiental e dos Recursos Hídricos, Universidade Federal Rural da Amazônia', 'Laboratório de Ecologia Tropical, Universidade Federal Rural da Amazônia', 'Instituto de Saúde e Produção Animal, Universidade Federal Rural da Amazônia', 'Laboratório de Oceanografia Química, Universidade Federal do Pará', 'Laboratório de Modelagem de Oceano e Estuários Amazônicos, Universidade Federal do Pará,']
No raw affiliation match: https://openalex.org/W2252121457 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2274713498 ['Fiocruz Amazônia, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil']
No raw affiliation match: https://openalex.org/W2407574685 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2561366912 ['', '']
No raw affiliation match: https://openalex.org/W2589171594 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2734873886 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2745331734 ['', '']
No raw affiliation match: https://openalex.org/W2748059655 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2786558381 ['']
No raw affiliation match: https://openalex.org/W2795142274 ['', '']
No raw affiliation match: https://openalex.org/W2796310298 ['', '', '']
No raw affiliation match: https://openalex.org/W2798400986 ['', '']
No raw affiliation match: https://openalex.org/W2809544018 ['', '', '']
No raw affiliation match: https://openalex.org/W2886787567 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2889261359 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2891581340 ['', '', '']
No raw affiliation match: https://openalex.org/W2900742068 ['', '']
No raw affiliation match: https://openalex.org/W2901786754 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2905963024 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2907718847 ['', '', '']
No raw affiliation match: https://openalex.org/W2913321241 ['', '', '']
No raw affiliation match: https://openalex.org/W2913676469 ['', '', '']
No raw affiliation match: https://openalex.org/W2913895095 ['', '']
No raw affiliation match: https://openalex.org/W2918708074 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2925841463 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2929514213 ['[Polytechnic University of Catalonia]', '', '']
No raw affiliation match: https://openalex.org/W2943283021 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2946120184 ['', '']
No raw affiliation match: https://openalex.org/W2946918168 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2947805651 ['', '', '']
No raw affiliation match: https://openalex.org/W2950085610 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2951945518 ['', '', '']
No raw affiliation match: https://openalex.org/W2952073206 ['', '']
No raw affiliation match: https://openalex.org/W2952181946 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2952573022 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2953343164 ['#N#Ghent University#N#', 'Amazon', '']
No raw affiliation match: https://openalex.org/W2953829678 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962852244 ['', '']
No raw affiliation match: https://openalex.org/W2962994328 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963005132 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965719710 ['', '', '']
No raw affiliation match: https://openalex.org/W2967996202 ['', 'University of Trento', '', '', '', 'University of Trento']
No raw affiliation match: https://openalex.org/W2973259188 ['', '', 'Amazon', '']
No raw affiliation match: https://openalex.org/W2975039599 ['', '', '', 'Amazon', '']
No raw affiliation match: https://openalex.org/W2977857619 ['']
No raw affiliation match: https://openalex.org/W2982191902 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2984941262 ['', '', '']
No raw affiliation match: https://openalex.org/W2985401038 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2992448548 ['', 'Amazon']
No raw affiliation match: https://openalex.org/W2995912923 ['', '', '']
No raw affiliation match: https://openalex.org/W2998188541 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3006583220 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3009224979 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3012821910 ['', '', '']
No raw affiliation match: https://openalex.org/W3022047811 ['', '', '']
No raw affiliation match: https://openalex.org/W3022504608 ['AMC-UvA, Faculteit der Geneeskunde, Amsterdam.; Contact: E.M. Corazolla (e.m.corazolla@amc.uva.nl).', 'AMC-UvA, Faculteit der Geneeskunde, Amsterdam.']
No raw affiliation match: https://openalex.org/W3028344666 ['', '']
No raw affiliation match: https://openalex.org/W3030853545 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3032085273 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3032479101 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3035971792 ['', '', '']
No raw affiliation match: https://openalex.org/W3037625829 ['', '', '']
No raw affiliation match: https://openalex.org/W3043672964 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3046037827 ['', '', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3047765285 ['University of California-Los Angeles', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3047778367 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3049700909 ['Embrapa Amazônia Oriental', 'Embrapa Amapá', 'EMBRAPA Café']
No raw affiliation match: https://openalex.org/W3082961799 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3088026546 ['', '', 'University of Illinois at #TAB#Chicago', '', '', '', '', 'Stanford University ()']
No raw affiliation match: https://openalex.org/W3089408321 ['', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3091291905 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3091930027 ['University of Washington ;', 'University of Washington ;', '', '']
No raw affiliation match: https://openalex.org/W3092244061 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3092330976 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3092597737 ['', 'Amazon', '', '', '']
No raw affiliation match: https://openalex.org/W3092751673 ['', '', '', 'University of Illinois at #TAB#Chicago']
No raw affiliation match: https://openalex.org/W3092858501 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3092898576 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3093318556 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3094200245 ['', 'Amazon']
No raw affiliation match: https://openalex.org/W3095483206 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3097696666 ['', '', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3099478794 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3102851939 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3103946812 ['', '', '']
No raw affiliation match: https://openalex.org/W3104956656 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3105510767 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3107050089 ['', '', '']
No raw affiliation match: https://openalex.org/W3110060343 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3110116204 ['', '']
No raw affiliation match: https://openalex.org/W3111720488 ['', '', 'Amazon', '', '', '']
No raw affiliation match: https://openalex.org/W3112578001 ['', '']
No raw affiliation match: https://openalex.org/W3114052161 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114054075 ['', '', '']
No raw affiliation match: https://openalex.org/W3114469455 ['', '', '']
No raw affiliation match: https://openalex.org/W3116743531 ['']
No raw affiliation match: https://openalex.org/W3116836881 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3117576622 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3130744522 ['Statistics', '', 'Computer Science', '']
No raw affiliation match: https://openalex.org/W3132094881 ['', '']
No raw affiliation match: https://openalex.org/W3134456927 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3134968238 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3138743673 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3139291533 ['', '', '']
No raw affiliation match: https://openalex.org/W3139395121 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3145814661 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3148242746 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3148717649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3153403682 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3153823621 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3154023792 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3154697502 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3156856719 ['university of liverpool', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3159484337 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3161318417 ['Univ. of Cambridge', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3163149064 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3163416817 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3164019749 [' University of Alberta.', '', '', '']
No raw affiliation match: https://openalex.org/W3165500975 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3166077906 ['Amazon', '', '', '', '']
No raw affiliation match: https://openalex.org/W3167217740 ['', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3167597168 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3168898150 ['', '']
No raw affiliation match: https://openalex.org/W3170116649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3171023288 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3171338328 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3171586554 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3172741267 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3172759730 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3172843532 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3174968164 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3175392547 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3176594410 ['', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3176922303 ['University of Tübingen', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3177245035 ['', '']
No raw affiliation match: https://openalex.org/W3177924560 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3178511319 ['', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3178969538 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3180451736 ['', '', '', '', '', '', '', '', 'Amazon']
No raw affiliation match: https://openalex.org/W3182650612 ['', '', '']
No raw affiliation match: https://openalex.org/W3183101145 ['', '', '']
No raw affiliation match: https://openalex.org/W3183487010 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183764363 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183773282 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183961407 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3184769649 ['Amazônia Azul Tecnologias de Defesa S.A', 'Universidade Federal do ABC']
No raw affiliation match: https://openalex.org/W3185363765 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3186326110 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3187629856 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3191229722 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3193142144 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3195005096 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3196742893 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3197859266 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3198090350 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3198298942 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3198802347 ['', '']
No raw affiliation match: https://openalex.org/W3201464248 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3201691278 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3202220749 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3202695546 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3204383925 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3204711568 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3204884380 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3204887348 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3206097584 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3206758163 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3208285837 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211094980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211326730 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211347421 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211416406 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211471094 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211483953 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211537168 ['', '', '']
No raw affiliation match: https://openalex.org/W3211621949 ['', '', '']
No raw affiliation match: https://openalex.org/W3211655567 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211689061 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211785525 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211807237 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211907575 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3212018716 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212022443 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212072588 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3212279921 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212331733 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212393417 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212512850 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212589816 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212667563 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212813607 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213019773 ['', '', '']
No raw affiliation match: https://openalex.org/W3213244327 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213295925 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213388042 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213517177 ['', '', '']
No raw affiliation match: https://openalex.org/W3213548503 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213581612 ['', '']
No raw affiliation match: https://openalex.org/W3213611638 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213622222 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213629725 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213633136 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213666479 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213810112 ['', '', '']
No raw affiliation match: https://openalex.org/W3213870597 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213941187 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213952306 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214103984 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214117304 ['', '']
No raw affiliation match: https://openalex.org/W3214138850 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214145914 ['', '']
No raw affiliation match: https://openalex.org/W3214234943 ['', '', '']
No raw affiliation match: https://openalex.org/W3214485347 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214495526 ['', '', '']
No raw affiliation match: https://openalex.org/W3216352276 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W4283021327 ['Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil', 'Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil', 'Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil; Instituto Nacional de Ciência e Tecnologia do Café  Lavras MG 37200‐900 Brazil', 'Embrapa Amazônia Oriental  Belém PA Brazil', 'Universidade Federal de Lavras  Lavras MG 37200‐900 Brazil', "Comissão Executiva do Plano da Lavoura Cacaueira – CEPLAC  Ouro Preto D'Oeste 76920‐000 Brazil"]
No raw affiliation match: https://openalex.org/W4287021305 ['Amazônia Azul Tecnologias de Defesa S.A.', 'Polytechnic School of the University of São Paulo (Brazil)', 'Centre Automatique et Systèmes; QUANTum Information Circuits']
No raw affiliation match: https://openalex.org/W4296613428 ['Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Odontologia Conservadora, Divisão de Endodontia, Porto Alegre, Rio Grande do Sul, Brasil.', 'Escola Superior da Amazônia, Departamento de Diagnóstico Bucal, Belém, Pará, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil']
No raw affiliation match: https://openalex.org/W4299323293 ['Amazônia Azul Tecnologias de Defesa S.A.', 'Polytechnic School of the University of São Paulo (Brazil)', 'Centre Automatique et Systèmes; QUANTum Information Circuits']
    Works: 2405
    Raw affiliation count: 1768
    Raw affiliation fraction: 0.7351351351351352
```

- Using all Amazon institutions:

```
Raw affiliation keywords: ['amazon']
No raw affiliation match: https://openalex.org/W2963961878 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963423916 ['', '', '']
No raw affiliation match: https://openalex.org/W2405578611 ['']
No raw affiliation match: https://openalex.org/W2964222566 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2890410208 ['', '', '']
No raw affiliation match: https://openalex.org/W2970697704 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962717849 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963352809 ['', '']
No raw affiliation match: https://openalex.org/W2971105107 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2889928394 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2804292122 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995589713 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963419583 ['', '', '']
No raw affiliation match: https://openalex.org/W2787733970 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963633299 ['', '']
No raw affiliation match: https://openalex.org/W3034255912 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2792839479 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2952113915 ['', '', '']
No raw affiliation match: https://openalex.org/W2963809789 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2964092925 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962739340 ['', '', '']
No raw affiliation match: https://openalex.org/W2963569817 ['', '', '']
No raw affiliation match: https://openalex.org/W3030754432 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2798761464 ['']
No raw affiliation match: https://openalex.org/W2891146651 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2908007030 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963973577 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2991522342 ['', '', '']
No raw affiliation match: https://openalex.org/W2987154291 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2885950361 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2897003273 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114916066 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2898917980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971274354 ['', '', '']
No raw affiliation match: https://openalex.org/W2995636882 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3106484161 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2985353426 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963547384 ['', '']
No raw affiliation match: https://openalex.org/W2963756980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2803533564 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963499433 ['', '', '']
No raw affiliation match: https://openalex.org/W2970176896 ['', '', '']
No raw affiliation match: https://openalex.org/W2572670101 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963162885 ['', '', '']
No raw affiliation match: https://openalex.org/W2972425456 ['', '', '']
No raw affiliation match: https://openalex.org/W2950695840 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970421227 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963532386 ['']
No raw affiliation match: https://openalex.org/W2964123521 ['', '', '']
No raw affiliation match: https://openalex.org/W2396230943 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2945315238 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962682420 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2986068180 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963882293 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964022663 ['', '', '']
No raw affiliation match: https://openalex.org/W2932319281 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3035131649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2971342441 ['', '', '']
No raw affiliation match: https://openalex.org/W3115851078 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2740210681 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963062785 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2404620314 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964168155 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2970562710 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3146670357 ['', '', '']
No raw affiliation match: https://openalex.org/W2053878386 ['Embrapa Amazônia Oriental, Trav. Dr. Enéas Pinheiro s/n°, Caixa Postal, 48, CEP 66095-100 Belém, PA, Brazil', 'Embrapa Amazônia Oriental, Trav. Dr. Enéas Pinheiro s/n°, Caixa Postal, 48, CEP 66095-100 Belém, PA, Brazil', 'Departamento de Biologia Geral Universidade Federal de Viçosa (UFV) Viçosa Minas Gerais Brazil', 'Embrapa Amazônia Ocidental, Rodovia AM 010, km 29, Caixa Postal 319, CEP 69010-970 Manaus, AM, Brazil', 'Embrapa Amazônia Ocidental, Rodovia AM 010, km 29, Caixa Postal 319, CEP 69010-970 Manaus, AM, Brazil', 'Marborges Agroindústria S.A., Rodovia Virgílio Serrão Sacramento, km 56, s/n, Caixa Postal 17, CEP 68 450-000 Mojú, Pará, Brazil', 'Marborges Agroindústria S.A., Rodovia Virgílio Serrão Sacramento, km 56, s/n, Caixa Postal 17, CEP 68 450-000 Mojú, Pará, Brazil']
No raw affiliation match: https://openalex.org/W2941649920 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2530797269 ['Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Embrapa Amazônia Oriental, Travessa Doutor Enéas Pinheiro, CEP 66.095-903, Belém, PA, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Universidade Federal de Viçosa, Campus Universitário de Viçosa, Departamento de Engenharia Florestal, Avenida Peter Henry Rolfs, s/n, CEP 36.570-900, Viçosa, MG, Brazil', 'Embrapa Amazônia Oriental, Travessa Doutor Enéas Pinheiro, CEP 66.095-903, Belém, PA, Brazil']
No raw affiliation match: https://openalex.org/W2950846878 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2798583685 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2964315715 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3037181583 ['', '', '']
No raw affiliation match: https://openalex.org/W2748594250 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2952307697 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962700197 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963866450 ['', '', '']
No raw affiliation match: https://openalex.org/W3102847511 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2741511332 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2935542736 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3000642987 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2913153410 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962693275 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963471154 ['', '']
No raw affiliation match: https://openalex.org/W2995455605 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2995653869 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2996463194 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2962830484 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963546161 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2977910558 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2990176236 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3030045039 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3168663263 ['Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', 'Univ. of Cambridge', '', "King's College London", 'Facebook']
No raw affiliation match: https://openalex.org/W2739724844 ['', '', '']
No raw affiliation match: https://openalex.org/W2965158072 ['', '']
No raw affiliation match: https://openalex.org/W2970799668 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2972838300 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2973230496 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3105081824 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2949370368 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965734314 ['', '']
No raw affiliation match: https://openalex.org/W2966246399 ['', '', '']
No raw affiliation match: https://openalex.org/W2971200681 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2972549707 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3036435426 ['University of Washington ;', 'University of Washington ;', '', 'University of Washington ;']
No raw affiliation match: https://openalex.org/W3037333676 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3098938591 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3102021588 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3102649892 ['', '', '']
No raw affiliation match: https://openalex.org/W3198664535 ['Bristol Doctoral College', '', '']
No raw affiliation match: https://openalex.org/W2568095718 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2759511005 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2808456396 ['', '', '']
No raw affiliation match: https://openalex.org/W2963891006 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2970687683 ['', '', '']
No raw affiliation match: https://openalex.org/W3093818688 ['', '', '']
No raw affiliation match: https://openalex.org/W3115091907 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3170943566 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2921071577 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2951575093 ['', '#N#‡#N#Georgia Institute of Technology#N#', '#N#‡#N#Georgia Institute of Technology#N#']
No raw affiliation match: https://openalex.org/W2970403389 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2996680032 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3102303514 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104866818 ['', '']
No raw affiliation match: https://openalex.org/W3111605943 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3117752211 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3169436550 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2741018521 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2748488613 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2787178450 ['Carnegie Mellon University', 'Carnegie Mellon University', '', '']
No raw affiliation match: https://openalex.org/W2790259362 ['', '', '']
No raw affiliation match: https://openalex.org/W2889736774 ['', '']
No raw affiliation match: https://openalex.org/W2972384212 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2985600242 ['', '', '']
No raw affiliation match: https://openalex.org/W3035753785 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3094953545 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3095735913 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3099225546 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3100879603 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2574856563 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2607593044 ['', '', '']
No raw affiliation match: https://openalex.org/W2764124976 ['', '']
No raw affiliation match: https://openalex.org/W2783719374 ['', '', '']
No raw affiliation match: https://openalex.org/W2803971899 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2907475315 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2912901814 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2912918913 ['', '', '']
No raw affiliation match: https://openalex.org/W2949176913 ['Massachusetts Institute Of Technology#TAB#', 'Google,,,,,', 'Google,,,,,', '']
No raw affiliation match: https://openalex.org/W2964038586 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2972930415 ['', '', '']
No raw affiliation match: https://openalex.org/W3034272764 ['', '', '']
No raw affiliation match: https://openalex.org/W3037093830 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093155142 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3100400430 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104194380 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3105184920 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2784023976 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2834342720 ['', '']
No raw affiliation match: https://openalex.org/W2965920802 ['', '', '']
No raw affiliation match: https://openalex.org/W2970020110 ['']
No raw affiliation match: https://openalex.org/W2971064282 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971310236 ['']
No raw affiliation match: https://openalex.org/W2983689619 ['', '', '']
No raw affiliation match: https://openalex.org/W2983722336 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3037600752 ['', '', '']
No raw affiliation match: https://openalex.org/W3103978933 ['', '', '']
No raw affiliation match: https://openalex.org/W3105580455 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3129089995 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211005660 ['', '', '']
No raw affiliation match: https://openalex.org/W2572569512 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2591784896 ['', '', '']
No raw affiliation match: https://openalex.org/W2607957941 ['Universidade Federal de Vicosa, Viçosa, Brazil', 'Universidade Federal de Vicosa, Viçosa, Brazil', 'Embrapa Amazônia Ocidental', 'EMBRAPA/Florestas, Colombo, Brazil', 'Embrapa Amazônia Ocidental', 'Universidade Federal de Vicosa, Viçosa, Brazil']
No raw affiliation match: https://openalex.org/W2885826215 ['', '']
No raw affiliation match: https://openalex.org/W2962985479 ['', '', '']
No raw affiliation match: https://openalex.org/W2963360277 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3092956463 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3099971460 ['', '', '']
No raw affiliation match: https://openalex.org/W1977557220 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2251165721 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2806804106 ['', '', '']
No raw affiliation match: https://openalex.org/W2929139284 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2942943100 ['', '', '']
No raw affiliation match: https://openalex.org/W2951657084 ['', '', '']
No raw affiliation match: https://openalex.org/W2951688832 ['Univ. of Cambridge', 'Univ. of Cambridge', '', '']
No raw affiliation match: https://openalex.org/W2951876757 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2954465950 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2963710187 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965435631 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2966441967 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970192826 ['University of California Santa Barbara', 'Google,,,,,', 'Carnegie Mellon University', '']
No raw affiliation match: https://openalex.org/W2970379104 ['Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', '']
No raw affiliation match: https://openalex.org/W2975704529 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2995574330 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3028954259 ['', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3035639219 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3038036095 ['', '']
No raw affiliation match: https://openalex.org/W3093557617 ['', '', '', 'National University of Singapore,']
No raw affiliation match: https://openalex.org/W3100387437 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3138310836 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3199004261 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214013345 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W1893496786 ['Universidade Federal de Viçosa, Viçosa, Brasil', 'Universidade Federal de Viçosa, Viçosa, Brasil', 'Embrapa Amazônia Oriental,  Brasil', 'Embrapa Florestas, Colombo, Brasil', 'Universidade Federal de Viçosa, Viçosa, Brasil']
No raw affiliation match: https://openalex.org/W2186169017 ['Centro de Pesquisa Agloflorestal de Roraima, Brasil', 'Embrapa Agrossilvipastoril, Sinop, Brasil.', 'Centro Nacional de Pesquisa de Florestas, Colombo, Brasil', 'Embrapa Amazônia Oriental, Brasil']
No raw affiliation match: https://openalex.org/W2294378299 ['', '']
No raw affiliation match: https://openalex.org/W2476743944 ['', '', '']
No raw affiliation match: https://openalex.org/W2741102098 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2755926663 ['', '']
No raw affiliation match: https://openalex.org/W2762483932 ['', '', '']
No raw affiliation match: https://openalex.org/W2802455203 ['', '', '']
No raw affiliation match: https://openalex.org/W2806957444 ['', '']
No raw affiliation match: https://openalex.org/W2888195294 ['', '']
No raw affiliation match: https://openalex.org/W2890884631 ['', '', '']
No raw affiliation match: https://openalex.org/W2924551963 ['', 'Google,,,,,']
No raw affiliation match: https://openalex.org/W2949488962 ['', '', '']
No raw affiliation match: https://openalex.org/W2952907575 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2962896386 ['', '', '']
No raw affiliation match: https://openalex.org/W2963645036 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2971327614 ['', '']
No raw affiliation match: https://openalex.org/W2986670164 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3021046937 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3034799022 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3047199820 ['', '', '']
No raw affiliation match: https://openalex.org/W3096746890 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3108508289 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3158088536 ['', '', '']
No raw affiliation match: https://openalex.org/W2293535060 ['SRI-International', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2606847791 [', , Brasil.', 'Embrapa Amazônia Oriental, Brasil', 'Embrapa Amazônia Oriental, Brasil', 'Embrapa Mandioca e Fruticultura, Cruz das Almas, BA, Brasil', 'Embrapa Amazônia Oriental, Brasil']
No raw affiliation match: https://openalex.org/W2771346320 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2922234509 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2946444035 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2947647530 ['Univ. of California Davis', '', '', 'Univ. of California Davis', 'University of California-Los Angeles']
No raw affiliation match: https://openalex.org/W2950420475 ['', '', '']
No raw affiliation match: https://openalex.org/W2963054052 ['', '']
No raw affiliation match: https://openalex.org/W2980075309 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2985638129 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3006210468 ['', '', '']
No raw affiliation match: https://openalex.org/W3048758284 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097469673 ['', '', '']
No raw affiliation match: https://openalex.org/W3098331497 ['', '']
No raw affiliation match: https://openalex.org/W3099372209 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3112707533 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3113459090 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3128997953 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3153899207 ['', '']
No raw affiliation match: https://openalex.org/W3170280676 ['', '']
No raw affiliation match: https://openalex.org/W3177112880 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3179307988 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3195529751 ['University of Macau,Department of Computer and Information Science,Macau,China', '', 'University of Macau,Department of Computer and Information Science,Macau,China']
No raw affiliation match: https://openalex.org/W3212387080 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2143350841 ['', '', 'Universidade Federal do Espírito Santo', '', '', '', '', 'Universidade\xa0Federal do Rio Grande do Sul', '']
No raw affiliation match: https://openalex.org/W2221612594 ['Indian Institute of Technology Kanpur', '']
No raw affiliation match: https://openalex.org/W2741325996 ['', '', '']
No raw affiliation match: https://openalex.org/W2745931053 ['', '', '']
No raw affiliation match: https://openalex.org/W2747937300 ['LANCASTER UNIVERSITY,', 'Linköping University', '', '']
No raw affiliation match: https://openalex.org/W2778098837 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2898152919 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2949736580 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2954154738 ['Instituto de Desenvolvimento Sustentável Mamirauá, Tefé, AM', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'EMBRAPA Amazônia Oriental, Belém, PA', 'Universidade Federal Rural da Amazônia, Campus Capitão Poço, Capitão Poço, PA', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'Universidade Federal de Viçosa, Campus#R##N#Universitário, Viçosa, MG', 'EMBRAPA Amazônia Oriental, Belém, PA', 'Universidade Federal do Recôncavo da Bahia, Cruz das Almas-BA', 'Universidade Federal do Sul da Bahia, Itabuna, BA']
No raw affiliation match: https://openalex.org/W2963489350 ['', '']
No raw affiliation match: https://openalex.org/W2966061665 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2970001856 ['Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', '', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society', 'Dept. Empirical Inference, Max Planck Institute for Intelligent Systems, Max Planck Society']
No raw affiliation match: https://openalex.org/W2989919526 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3002279815 ['', '']
No raw affiliation match: https://openalex.org/W3010872790 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3037501086 ['', '']
No raw affiliation match: https://openalex.org/W3037562253 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3092973380 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093898938 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097484451 ['', '']
No raw affiliation match: https://openalex.org/W3105973526 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3110740243 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114972653 ['', '']
No raw affiliation match: https://openalex.org/W3117968175 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3157624638 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3157793776 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3158811267 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3198973235 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3201234832 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3203598579 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214125927 ['', '', '', '']
No raw affiliation match: https://openalex.org/W1842617815 ['Dept. of Electr. Eng. & Comput. Sci, Univ. of Michigan, Ann Arbor, MI, USA', '', 'Inst. for Robot. & Intell. Machines, Georgia Inst. of Technol., Atlanta, GA, USA', 'Dept. of Electr. Eng. & Comput. Sci, Univ. of Michigan, Ann Arbor, MI, USA', 'Dept. of Computer Science and Information Engineering, National Taiwan University of Science and Technology, Taipei, Taiwan#TAB#']
No raw affiliation match: https://openalex.org/W2405490700 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2517120700 ['', '', '']
No raw affiliation match: https://openalex.org/W2613023307 ['', '', '']
No raw affiliation match: https://openalex.org/W2761970834 ['Universidade Federal do Amazonas – UFAM, Avenida General Rodrigo Otávio, 6200, Coroado I, 69.800-900, Manaus, AM, Brasil', 'Instituto de Ciências Exatas e Tecnologia, Universidade Federal do Amazonas -UFAM, Rua Nossa Senhora do Rosário, 3863, Tiradentes, 69.103-128, Itacoatiara, AM, Brasil', 'Embrapa Rondônia, Rodovia Br-364, km 5,5, Zona Rural, caixa postal 127, 76.815-800, Porto Velho, RO, Brasil', 'Embrapa Amazônia Ocidental, Rodovia AM-10, km 29, (Estrada Manaus/Itacoatiara), caixa postal 319, 69.010-970, Manaus, AM, Brasil', 'Embrapa Rondônia, Rodovia Br-364, km 5,5, Zona Rural, caixa postal 127, 76.815-800, Porto Velho, RO, Brasil']
No raw affiliation match: https://openalex.org/W2835534053 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2951539692 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963431600 ['', '']
No raw affiliation match: https://openalex.org/W2964713509 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2971019013 ['', '', '']
No raw affiliation match: https://openalex.org/W2979618889 ['', '']
No raw affiliation match: https://openalex.org/W2980596743 ['', '', '', '', 'University of Notre Dame.']
No raw affiliation match: https://openalex.org/W2990201487 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3009752645 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3021802247 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3023778123 ['', '', '']
No raw affiliation match: https://openalex.org/W3045737996 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3088291589 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3088860656 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3093346478 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3096157982 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3096572584 ['', 'Institute of Automation. Chinese Academy of Sciences', 'Institute of Automation. Chinese Academy of Sciences', '', '', '']
No raw affiliation match: https://openalex.org/W3096588269 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3097731397 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3098281389 ['', '']
No raw affiliation match: https://openalex.org/W3099438082 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3104098714 ['', '', '']
No raw affiliation match: https://openalex.org/W3104752986 ['', '', '']
No raw affiliation match: https://openalex.org/W3109833210 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3115419395 ['', '']
No raw affiliation match: https://openalex.org/W3117732268 ['', '', '']
No raw affiliation match: https://openalex.org/W3137189276 ['Embrapa  Amazônia  Oriental', 'Embrapa  Amazônia  Ocidental', 'Embrapa  Amazônia  Ocidental', 'Grupo  Marborges', 'Embrapa Café', 'Embrapa  Amazônia  Oriental']
No raw affiliation match: https://openalex.org/W3153201663 ['', '', 'Speechly', 'Speechly', '']
No raw affiliation match: https://openalex.org/W3154151461 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3158218109 ['', '', '']
No raw affiliation match: https://openalex.org/W3158731518 ['Statistics', '', 'Computer Science', '']
No raw affiliation match: https://openalex.org/W3168415639 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3170730117 ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3170752662 ['', '']
No raw affiliation match: https://openalex.org/W3171469166 ['', '', '']
No raw affiliation match: https://openalex.org/W3175179074 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3176048559 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3182974197 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183691183 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3197575580 ['', '', '']
No raw affiliation match: https://openalex.org/W3198604552 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3199117450 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3202074632 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3209015562 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211589367 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213189432 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213249234 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W4220969210 ['ISAC-Institute of Atmospheric Sciences and Climate, CNR, Italy', 'Departamento de Fisica, Universidade Federal de Santa Maria, Santa Maria, RS, Brazil; ISAC-Institute of Atmospheric Sciences and Climate, CNR, Italy', 'Department of Physics, Federal Institute of Para (IFPA), Belem, PA, Brazil; Instituto Nacional de Pesquisas da Amazonia (INPA-CLIAMB), Manaus, AM, Brazil', 'Instituto Nacional de Pesquisas da Amazonia (INPA-CLIAMB), Manaus, AM, Brazil', 'Departamento de Fisica, Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Universidade Federal do Rio Grande do Norte, Natal, RN, Brazil', 'Department of Pure and Applied Sciences (DiSPeA), Universit`a degli Studi di Urbino ‘Carlo Bo’,Italy', 'Instituto Nacional de Pesquisas Espaciais (INPE), Cachoeira Paulista, SP, Brazil', 'Embrapa Amazônia Oriental, Tv. Dr. Enéas Piheiro, s/n, Marco, CEP 66095-903, Caixa postal 48, Belém, Pará, Brasil', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, 55020 Mainz, Germany', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, 55020 Mainz, Germany']
No raw affiliation match: https://openalex.org/W4280591069 ['Institute of Atmospheric Sciences and Climate, Consiglio Nazionale delle Ricerche (ISAC-CNR), Italy; Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Department of Physics, Federal Institute of Pará (IFPA), Belém, PA, Brazil; Instituto Nacional de Pesquisas da Amazônia (INPA-CLIAMB), Manaus, AM, Brazil', 'Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Universidade Federal do Rio Grande do Norte, Natal, RN, Brazil', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, Mainz 55020, Germany', 'Atmospheric Chemistry Department, Max Planck Institute for Chemistry, P.O. Box 3060, Mainz 55020, Germany', 'Instituto Nacional de Pesquisas Espaciais (INPE), Cachoeira Paulista, SP, Brazil', 'Embrapa Amazônia Oriental, Tv. Dr. Enéas Piheiro, s/n, Marco, Caixa postal 48, Belém, Pará CEP 66095-903, Brasil', 'Instituto Nacional de Pesquisas da Amazônia (INPA-CLIAMB), Manaus, AM, Brazil', 'Universidade Federal de Santa Maria, Santa Maria, RS, Brazil', 'Department of Pure and Applied Sciences (DiSPeA), Università degli Studi di Urbino ‘Carlo 20 \xa0Bo,Italy', 'Institute of Atmospheric Sciences and Climate, Consiglio Nazionale delle Ricerche (ISAC-CNR), Italy']
No raw affiliation match: https://openalex.org/W4295736883 ['Universidade Federal Rural da Amazônia', 'Universidade Estadual de Santa Cruz', 'Universidade Federal do Pará', 'Universidade Federal Rural da Amazônia', 'Universidade Federal Rural da Amazônia', 'Universidade Federal Rural da Amazônia', 'Universidade Federal do Pará', 'Universidade Federal do Pará', 'EMBRAPA - Amazônia Oriental', 'EMBRAPA - Amazônia Oriental']
No raw affiliation match: https://openalex.org/W4311799494 ['Embrapa Amazônia Oriental,  Brasil', 'Associação em Áreas de Assentamento no Estado do Maranhão,  Brasil']
No raw affiliation match: https://openalex.org/W1604162242 ['', '']
No raw affiliation match: https://openalex.org/W1605239498 ['Universidade Federal Rural da Amazônia/Laboratório de Química Ambiental', 'Instituto Sócio Ambiental e dos Recursos Hídricos, Universidade Federal Rural da Amazônia', 'Laboratório de Ecologia Tropical, Universidade Federal Rural da Amazônia', 'Instituto de Saúde e Produção Animal, Universidade Federal Rural da Amazônia', 'Laboratório de Oceanografia Química, Universidade Federal do Pará', 'Laboratório de Modelagem de Oceano e Estuários Amazônicos, Universidade Federal do Pará,']
No raw affiliation match: https://openalex.org/W2252121457 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2274713498 ['Fiocruz Amazônia, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil', 'Universidade Federal do Amazonas, Manaus, Brasil']
No raw affiliation match: https://openalex.org/W2407574685 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2561366912 ['', '']
No raw affiliation match: https://openalex.org/W2734873886 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2745331734 ['', '']
No raw affiliation match: https://openalex.org/W2748059655 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2796310298 ['', '', '']
No raw affiliation match: https://openalex.org/W2889261359 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2891581340 ['', '', '']
No raw affiliation match: https://openalex.org/W2900742068 ['', '']
No raw affiliation match: https://openalex.org/W2901786754 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2907718847 ['', '', '']
No raw affiliation match: https://openalex.org/W2913676469 ['', '', '']
No raw affiliation match: https://openalex.org/W2913895095 ['', '']
No raw affiliation match: https://openalex.org/W2918708074 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2925841463 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2929514213 ['[Polytechnic University of Catalonia]', '', '']
No raw affiliation match: https://openalex.org/W2946120184 ['', '']
No raw affiliation match: https://openalex.org/W2950085610 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2952181946 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W2952573022 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2963005132 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W2965719710 ['', '', '']
No raw affiliation match: https://openalex.org/W2967996202 ['', 'University of Trento', '', '', '', 'University of Trento']
No raw affiliation match: https://openalex.org/W2977857619 ['']
No raw affiliation match: https://openalex.org/W2982191902 ['', '', '', '']
No raw affiliation match: https://openalex.org/W2984941262 ['', '', '']
No raw affiliation match: https://openalex.org/W2995912923 ['', '', '']
No raw affiliation match: https://openalex.org/W2998188541 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3012821910 ['', '', '']
No raw affiliation match: https://openalex.org/W3022047811 ['', '', '']
No raw affiliation match: https://openalex.org/W3022504608 ['AMC-UvA, Faculteit der Geneeskunde, Amsterdam.; Contact: E.M. Corazolla (e.m.corazolla@amc.uva.nl).', 'AMC-UvA, Faculteit der Geneeskunde, Amsterdam.']
No raw affiliation match: https://openalex.org/W3028344666 ['', '']
No raw affiliation match: https://openalex.org/W3032085273 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3032479101 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3047778367 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3049700909 ['Embrapa Amazônia Oriental', 'Embrapa Amapá', 'EMBRAPA Café']
No raw affiliation match: https://openalex.org/W3082961799 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3088026546 ['', '', 'University of Illinois at #TAB#Chicago', '', '', '', '', 'Stanford University ()']
No raw affiliation match: https://openalex.org/W3092244061 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3092751673 ['', '', '', 'University of Illinois at #TAB#Chicago']
No raw affiliation match: https://openalex.org/W3092858501 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3095483206 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3102851939 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3105510767 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3107050089 ['', '', '']
No raw affiliation match: https://openalex.org/W3110060343 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3110116204 ['', '']
No raw affiliation match: https://openalex.org/W3114052161 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3114054075 ['', '', '']
No raw affiliation match: https://openalex.org/W3114469455 ['', '', '']
No raw affiliation match: https://openalex.org/W3116743531 ['']
No raw affiliation match: https://openalex.org/W3116836881 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3117576622 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3132094881 ['', '']
No raw affiliation match: https://openalex.org/W3134456927 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3138743673 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3139291533 ['', '', '']
No raw affiliation match: https://openalex.org/W3139395121 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3145814661 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3148717649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3153403682 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3154697502 ['', '', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3159484337 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3163149064 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3163416817 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3164019749 [' University of Alberta.', '', '', '']
No raw affiliation match: https://openalex.org/W3165500975 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3167597168 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3168898150 ['', '']
No raw affiliation match: https://openalex.org/W3170116649 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3171023288 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3171338328 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3171586554 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3172741267 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3172843532 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3174968164 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3175392547 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3176922303 ['University of Tübingen', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3177245035 ['', '']
No raw affiliation match: https://openalex.org/W3177924560 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3178969538 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3182650612 ['', '', '']
No raw affiliation match: https://openalex.org/W3183101145 ['', '', '']
No raw affiliation match: https://openalex.org/W3183487010 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3183764363 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3184769649 ['Amazônia Azul Tecnologias de Defesa S.A', 'Universidade Federal do ABC']
No raw affiliation match: https://openalex.org/W3186326110 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3191229722 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3193142144 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3196742893 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3197859266 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3198090350 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3198802347 ['', '']
No raw affiliation match: https://openalex.org/W3201464248 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3201691278 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3202220749 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3204383925 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3206097584 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3206758163 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3208285837 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211094980 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211326730 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211347421 ['', '', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211416406 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211471094 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211483953 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211537168 ['', '', '']
No raw affiliation match: https://openalex.org/W3211621949 ['', '', '']
No raw affiliation match: https://openalex.org/W3211655567 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3211689061 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3211785525 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3212072588 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3212279921 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212331733 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212393417 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3212667563 ['', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213019773 ['', '', '']
No raw affiliation match: https://openalex.org/W3213244327 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213295925 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213388042 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213611638 ['', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213633136 ['', '', '', '']
No raw affiliation match: https://openalex.org/W3213810112 ['', '', '']
No raw affiliation match: https://openalex.org/W3213870597 ['', '', '', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3213941187 ['', '', '', '', '', '']
No raw affiliation match: https://openalex.org/W3214117304 ['', '']
No raw affiliation match: https://openalex.org/W3214145914 ['', '']
No raw affiliation match: https://openalex.org/W3214234943 ['', '', '']
No raw affiliation match: https://openalex.org/W3214495526 ['', '', '']
No raw affiliation match: https://openalex.org/W4283021327 ['Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil', 'Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil', 'Departamento de agronomia Universidade Federal de Viçosa  Viçosa MG 36570‐900 Brazil; Instituto Nacional de Ciência e Tecnologia do Café  Lavras MG 37200‐900 Brazil', 'Embrapa Amazônia Oriental  Belém PA Brazil', 'Universidade Federal de Lavras  Lavras MG 37200‐900 Brazil', "Comissão Executiva do Plano da Lavoura Cacaueira – CEPLAC  Ouro Preto D'Oeste 76920‐000 Brazil"]
No raw affiliation match: https://openalex.org/W4287021305 ['Amazônia Azul Tecnologias de Defesa S.A.', 'Polytechnic School of the University of São Paulo (Brazil)', 'Centre Automatique et Systèmes; QUANTum Information Circuits']
No raw affiliation match: https://openalex.org/W4296613428 ['Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Odontologia Conservadora, Divisão de Endodontia, Porto Alegre, Rio Grande do Sul, Brasil.', 'Escola Superior da Amazônia, Departamento de Diagnóstico Bucal, Belém, Pará, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil', 'Universidade Federal do Rio Grande do Sul, Departamento de Cirurgia e Ortopedia, Divisão de Radiologia Odontológica e Imaginologia, Porto Alegre, Rio Grande do Sul, Brasil']
No raw affiliation match: https://openalex.org/W3158484638 ['Institute of Technology and Education Galileo da Amazônia - ITEGAM', 'Institute of Technology and Education Galileo da Amazônia - ITEGAM', 'Institute of Technology and Education Galileo da Amazônia - ITEGAM', 'Institute of Technology and Education Galileo da Amazônia - ITEGAM', 'Institute of Technology and Education Galileo da Amazônia - ITEGAM', 'Institute of Technology and Education Galileo da Amazônia - ITEGAM']
No raw affiliation match: https://openalex.org/W2550688362 ['Universidad Central “Marta Abreu” de Las Villas - Cuba', 'Universidad Central “Marta Abreu” de Las Villas - Cuba', 'Universidad Central “Marta Abreu” de Las Villas - Cuba', 'Universidad Central “Marta Abreu” de Las Villas - Cuba', 'Universidad Central “Marta Abreu” de Las Villas - Cuba', 'Instituto de Tecnologia Galileo da Amazônia']
No raw affiliation match: https://openalex.org/W2969384402 ['Escola Superior Batista da Amazônia', 'Escola Superior Batista da Amazônia', 'Universidade Federal de Itajubá']
No raw affiliation match: https://openalex.org/W3014098445 ['Instituto de Tecnologia Educação Galileo da Amazônia', 'Industrial and Systems Engineering Department, Technology Center, Federal University of Santa #R##N#Catarina', 'Industrial and Systems Engineering Department, Technology Center, Federal University of Santa #R##N#Catarina']
    Works: 3044
    Raw affiliation count: 2569
    Raw affiliation fraction: 0.8439553219448095
```

- Number of non-matches went down
- But still a lot of cases with entirely empty strings for raw affiliation
- Example: 'https://openalex.org/W2963961878'
  - Author: Christos Christodoulopoulos. Affiliated with Amazon (United States). But raw_affiliation_string is empty.
  - Website https://christos-c.com/ suggests that they are indeed with Amazon.
  - The paper https://aclanthology.org/N18-1074.pdf says "Amazon Research Cambridge"
  - So it is picking up on the info in the paper, it seems. Just failed to record the raw affiliation string.
  - Weird how this problem is so much more pronounced for Amazon than SenseTime, OpenAI, DeepMind. Is it partly because Amazon just has more papers, so it's more likely to occur? That can't explain all of it because the _rate_ of non-match is much lower.
- Google

```
    Works: 10292
    Raw affiliation count: 8424
    Raw affiliation fraction: 0.8184998056743101
```

  - Pretty low
  - But every non-match has empty raw affiliation strings for Google affiliations (verified this in code)
    - Checking one example of non-match with empty string, the affiliation is Google. Same as with the one example from Amazon.
    - Checking another example (https://openalex.org/W2963310665), the affiliation is DeepMind. Ok, so it's definitely not perfect in these cases.
    - A third example (https://openalex.org/W2962843773) is correctly Google 
    - Based on this evidence I bet that OpenAlex is mostly getting these cases right
- We could just cut all the potential false positives (even the ones with empty strings, that might be mostly right). We would only lose like 20% of the data. Potentially worth it to reduce error.
- Microsoft:

```
    Works: 14960
    Raw affiliation count: 13278
    Diff: 1682
    Affiliation with empty raw string count: 1674
    Raw affiliation fraction: 0.8875668449197861
```

  - Mostly the empty raw string case
  - Why is the number of no matches at all (155) much smaller than the number of no matches?
    - I think it's a case of any vs. all. If any Microsoft affiliations have no match in the raw string, that counts towards 1682. If all Microsoft affiliations have no match in the raw string, that counts towards 155. However, Microsoft does seem unusual in having a large difference between these numbers, compared to the companies I've looked at so far.

For now I'm just going to measure the rate of false positives in a rough way. It's better than nothing.

```
{'Adobe': 0.8805474906677727,
 'Alibaba': 0.9272624753312658,
 'Amazon': 0.8445901639344262,
 'Baidu': 0.8728943338437979,
 'DeepMind': 0.9824561403508771,
 'Google': 0.8185350689722168,
 'Group Sense': 0.9786931818181818,
 'Huawei': 0.9106606606606606,
 'IBM': 0.8880985774393909,
 'Intel': 0.9620328257860391,
 'NEC': 0.9565217391304348,
 'Naver': 0.8396694214876033,
 'Netflix': 0.9265536723163842,
 'Nvidia': 0.9189526184538653,
 'Meta': 0.8218934911242604,
 'Microsoft': 0.8883103010881901,
 'OpenAI': 1.0,
 'Salesforce': 1.0,
 'Tencent': 0.897364771151179,
 'Twitter': 0.9449275362318841,
 'Uber': 0.782051282051282,
 'Xerox': 0.8087954110898662,
 'Yandex': 0.8862745098039215,
 'Enthought': 1.0,
 'Quansight': 1.0}
```

# 2023-Oct-26

## Effect of citation count horizon

Default: 3-year horizon

Comparison to 1-year horizon

- Citations
  - 1-year horizon results in fewer total citations, as you'd expect
  - Ranking of top 5 companies is identical
  - Intel moves from 6th to 8th
  - Alibaba moves from 11th to 9th; Adobe moves from 9th to 11th
  - Twitter and Salesforce move up one rank
- Citations per author
  - Less citations all around as you'd expect.
  - Slightly less spread vertically; y-axis is 2 to 20 rather than 5 to 100
  - Meta moves down relative to OpenAI, gets around the same as DeepMind (~13 citations per author)
  - Other than that, not much relative change. Just small movements.

Comparison to 13-year horizon

- Citations
  - Ranking of top 6 companies is identical
  - Microsoft gets closer to Google; only 6.5k citations apart
  - Tencent moves from 7th to 9th; Adobe moves from 9th to 7th
  - Baidu moves from 13th to 11th
  - A couple other stragglers move ...
- Citations per author
  - More citations all around as you'd expect
  - More spread vertically; leaders pull further ahead (y-axis is 20 to 200)
  - Meta moves to just surpass OpenAI (!); DeepMind pulls away from SenseTime
  - Baidu pulls ahead of the remaining Chinese companies, but still well below the US leaders
  - Remaining Chinese companies are still bunched low down

Comparison from 5-year to 13-year horizon

- Citations
  - Only Baidu and Xerox move up two ranks

## Significance tests

Mann-Whitney U-test

Running 1000-iteration bootstrap

Without bootstrapping - just looking at citation distributions

- So basically comparing medians 

```
OpenAI: sample_size=163, mean=125.06, median=40.00
DeepMind: sample_size=755, mean=91.37, median=9.00
U statistic: 82856.5
Common language effect size: 0.6732742859464511
P-value: 3.3046184119745824e-12

DeepMind: sample_size=755, mean=91.37, median=9.00
Meta: sample_size=3329, mean=56.34, median=7.00
U statistic: 1321799.5
Common language effect size: 0.5259020169929518
P-value: 0.02550132814119708

Meta: sample_size=3329, mean=56.34, median=7.00
Google: sample_size=10094, mean=42.90, median=6.00
U statistic: 17509800.0
Common language effect size: 0.5210796226495276
P-value: 0.00024323255887518514

DeepMind: sample_size=755, mean=91.37, median=9.00
SenseTime: sample_size=677, mean=40.59, median=7.00
U statistic: 269390.5
Common language effect size: 0.5270437359992957
P-value: 0.07550946625709978

Meta: sample_size=3329, mean=56.34, median=7.00
SenseTime: sample_size=677, mean=40.59, median=7.00
U statistic: 1130491.5
Common language effect size: 0.5016084425262443
P-value: 0.8944704725031989

Google: sample_size=10094, mean=42.90, median=6.00
Microsoft: sample_size=14550, mean=23.11, median=5.00
U statistic: 77623307.5
Common language effect size: 0.5285253837297105
P-value: 1.7603900311941404e-14

Microsoft: sample_size=14550, mean=23.11, median=5.00
Baidu: sample_size=1920, mean=18.89, median=3.00
U statistic: 15209581.0
Common language effect size: 0.5444437643184421
P-value: 1.7926411666094342e-10

Microsoft: sample_size=14550, mean=23.11, median=5.00
Tencent: sample_size=3495, mean=16.06, median=3.00
U statistic: 27650282.0
Common language effect size: 0.5437376320615115
P-value: 5.800135862795158e-16

Microsoft: sample_size=14550, mean=23.11, median=5.00
Alibaba: sample_size=3424, mean=12.11, median=3.00
U statistic: 28288977.5
Common language effect size: 0.5678328335260301
P-value: 1.3954284708149238e-35

Baidu: sample_size=1920, mean=18.89, median=3.00
Tencent: sample_size=3495, mean=16.06, median=3.00
U statistic: 3351130.0
Common language effect size: 0.49939347877920837
P-value: 0.940426519267788

Baidu: sample_size=1920, mean=18.89, median=3.00
Alibaba: sample_size=3424, mean=12.11, median=3.00
U statistic: 3425506.5
Common language effect size: 0.5210624908732476
P-value: 0.009658506915015045

Tencent: sample_size=3495, mean=16.06, median=3.00
Alibaba: sample_size=3424, mean=12.11, median=3.00
U statistic: 6248270.0
Common language effect size: 0.5221302461460298
P-value: 0.0012645664688033977

Alibaba: sample_size=3424, mean=12.11, median=3.00
Huawei: sample_size=5140, mean=10.69, median=2.00
U statistic: 9516697.0
Common language effect size: 0.5407410837666824
P-value: 8.093556703400892e-11
```
