import numpy as np
import pyalex
from pyalex import Works
import tqdm


# The polite pool has much faster and more consistent response times. To get into the polite pool, you set your email:
pyalex.config.email = "ben@epochai.org"

SEED = 20230105
SAMPLE_SIZE = 10  # TODO 1000

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
imagenet_ref_count = 0
non_imagenet_ref_count = 0
null_ref_count = 0

for work in tqdm.tqdm(works_sample):
    inv_idx = work['abstract_inverted_index']
    if inv_idx is None:
        null_count += 1
        continue
    inv_idx = {k.lower(): v for k, v in inv_idx.items()}
    if 'imagenet' in inv_idx.keys():
        imagenet_paper_count += 1
        for referenced_work_id in work['referenced_works']:
            try:
                referenced_work = Works()[referenced_work_id]
            except:
                null_ref_count += 1
                continue
            referenced_inv_idx = referenced_work['abstract_inverted_index']
            if referenced_inv_idx is None:
                null_ref_count += 1
            else:
                referenced_inv_idx = {k.lower(): v for k, v in referenced_inv_idx.items()}
                if 'imagenet' in referenced_inv_idx.keys():
                    imagenet_ref_count += 1
                else:
                    non_imagenet_ref_count += 1


print(f"Papers with no abstract inverted index available: {null_count}")
print(f"Papers mentioning ImageNet in their Abstract: {imagenet_paper_count}")
print(f"References with no abstract inverted index available: {null_ref_count}")
print(f"References mentioning ImageNet in their Abstract: {imagenet_ref_count}")
print(f"References not mentioning ImageNet in their Abstract: {non_imagenet_ref_count}")
print(f"Fraction: {imagenet_ref_count / (imagenet_ref_count + non_imagenet_ref_count):.2f}")
