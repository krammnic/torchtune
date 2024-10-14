# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from PIL.PngImagePlugin import PngImageFile
from tests.common import ASSETS
from tests.test_utils import DummyTokenizer

from torchtune.datasets.multimodal import multimodal_instruct_dataset


class TestMultimodalInstructDataset:
    @pytest.fixture
    def tokenizer(self):
        return DummyTokenizer()

    @pytest.mark.parametrize("train_on_input", [True, False])
    def test_get_item(self, tokenizer, train_on_input):
        system_prompt = "follow this prompt"

        dataset = multimodal_instruct_dataset(
            model_transform=tokenizer,
            source="json",
            data_files=str(ASSETS / "multimodal_instruct_tiny.json"),
            split="train",
            new_system_prompt=system_prompt,
        )

        system_prompt_offset = len(system_prompt.split(" ")) + 1

        expected_tokens = [
            [0, 6, 4, 6, -2, 4, 2, 9, 2, 6, 7, 5, -1],
        ]

        expected_labels = [
            [-100, -100, -100, -100, -100, -100, -100, -100, -100, -100, 7, 5, -1]
        ]

        assert len(dataset) == 1

        for i in range(len(dataset)):
            prompt, label, image = (
                dataset[i]["tokens"],
                dataset[i]["labels"],
                dataset[i]["images"],
            )
            assert prompt == expected_tokens[i]
            assert label == expected_labels[i]
            assert isinstance(image[0], PngImageFile) is True
