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
