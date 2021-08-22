#! /usr/bin/env python
# coding=utf-8
# Copyright (c) 2019 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
from sys import path
import pandas as pd
import re
from collections import defaultdict
from tqdm import tqdm
from typing import List
from urllib.request import urlretrieve

from ludwig.datasets.base_dataset import DEFAULT_CACHE_LOCATION, BaseDataset
from ludwig.datasets.mixins.download import S3FileDownloadMixin
from ludwig.datasets.mixins.load import CSVLoadMixin
from ludwig.utils.fs_utils import makedirs, rename


def load(cache_dir=DEFAULT_CACHE_LOCATION, split=False):
    dataset = InsuranceLite(cache_dir=cache_dir)
    return dataset.load(split=split)


class InsuranceLite(CSVLoadMixin, S3FileDownloadMixin, BaseDataset):
    """The InsuranceLite dataset.

    This pulls in an array of mixins for different types of functionality
    which belongs in the workflow for ingesting and transforming training data into a destination
    dataframe that can fit into Ludwig's training API.
    """

    def __init__(self, cache_dir=DEFAULT_CACHE_LOCATION):
        super().__init__(dataset_name="insurance_lite", cache_dir=cache_dir)

    def process_downloaded_dataset(self):
        makedirs(self.processed_temp_path, exist_ok=True)
        
        url = self.config['s3_download_urls']
        file_name = os.path.join(self.raw_dataset_path, url.split('/')[-1])
        # TODO(shreya): DataFrame created twice: here + CSVMixin. Figure out
        # options for using it once.
        df = pd.read_csv(
            file_name, header=0,
            names=['id', 'image_path', 'insurance_company',
                    'cost_of_vehicle', 'min_coverage', 'expiry_date',
                    'max_coverage', 'condition', 'amount'],
            usecols=list(range(1, 9))
            )
        urls = df['image_path']
        # self.download_images(urls)
        df['image_path'] = df['image_path'].apply(
            lambda x: os.path.join(self.raw_dataset_path, 'images', x.split('/')[-1]))
        df.to_csv(os.path.join(self.processed_temp_path, self.csv_filename),
                  columns=['image_path', 'insurance_company',
                           'cost_of_vehicle', 'min_coverage', 'expiry_date',
                           'max_coverage', 'condition', 'amount'])

        # Note: csv is stored in /processed while images are stored in /raw
        rename(self.processed_temp_path, self.processed_dataset_path)

    def download_images(self, image_urls: List[str]):
        # TODO(shreya): Parallelize this.
        makedirs(os.path.join(self.raw_dataset_path, 'images'), exist_ok=True)
        for url in tqdm(image_urls):
            file_name = url.split('/')[-1]
            urlretrieve(
                url,
                os.path.join(self.raw_dataset_path, 'images', file_name))
