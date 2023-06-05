import numpy as np
import pyalex
from pyalex import Works
import tqdm


# The polite pool has much faster and more consistent response times. To get into the polite pool, you set your email:
pyalex.config.email = "ben@epochai.org"

seed = 20230105
sample_size = 1000

def merge_sample(query, sample_size=1000, seed=None):
    sampler = query.sample(sample_size, seed=seed)
    items = []
    for i in range(int(np.ceil(sample_size / 200)) + 1):  # 200 is the max page size
        page = sampler.get(per_page=200, page=i+1)
        items.extend(page)
    return items

works_sample = merge_sample(
    Works().search_filter(abstract="imagenet"),
    sample_size=sample_size,
    seed=seed,
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

print(imagenet_papers, imagenet_count, non_imagenet_count, null_count)
