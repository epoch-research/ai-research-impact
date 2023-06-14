import numpy as np
import pyalex
from pyalex import Works
import tqdm


# The polite pool has much faster and more consistent response times. To get into the polite pool, you set your email:
pyalex.config.email = "ben@epochai.org"

SEED = 20230105
SAMPLE_SIZE = 1000  # TODO 1000

def merge_sample(query, sample_size=1000, seed=None):
    sampler = query.sample(sample_size, seed=seed)
    items = []
    for i in range(int(np.ceil(sample_size / 200)) + 1):  # 200 is the max page size
        page = sampler.get(per_page=200, page=i+1)
        items.extend(page)
    return items

works_sample = merge_sample(
    Works().search_filter(abstract="imagenet"),
    sample_size=SAMPLE_SIZE,
    seed=SEED,
)

null_count = 0
imagenet_paper_count = 0
imagenet_ref_fractions = []

for work in tqdm.tqdm(works_sample):
    abstract = work['abstract']
    if abstract is None:
        null_count += 1
        continue
    if 'imagenet' in abstract.lower():
        imagenet_paper_count += 1
        imagenet_ref_count = 0
        non_imagenet_ref_count = 0
        null_ref_count = 0
        for referenced_work_id in work['referenced_works']:
            try:
                referenced_work = Works()[referenced_work_id]
            except:
                null_ref_count += 1
                continue
            referenced_abstract = referenced_work['abstract']
            if referenced_abstract is None:
                null_ref_count += 1
                continue
            if 'imagenet' in referenced_abstract.lower():
                imagenet_ref_count += 1
            else:
                non_imagenet_ref_count += 1
        if imagenet_ref_count + non_imagenet_ref_count != 0:
            imagenet_ref_fractions.append(imagenet_ref_count / (imagenet_ref_count + non_imagenet_ref_count))

imagenet_ref_fractions = np.array(imagenet_ref_fractions)

print(f"Papers with no Abstract available: {null_count}")
print(f"Papers with ImageNet in the Abstract: {imagenet_paper_count}")
print(f"Mean fraction of references mentioning ImageNet in the Abstract: {imagenet_ref_fractions.mean():.2f}")
print(f"Std fraction of references mentioning ImageNet in the Abstract: {imagenet_ref_fractions.std():.2f}")
