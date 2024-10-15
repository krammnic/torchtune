# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from typing import Any, Callable, Dict, Optional, Union

from torchtune.data import InputOutputToMessages
from torchtune.datasets._packed import PackedDataset
from torchtune.datasets._sft import SFTDataset
from torchtune.modules.transforms import Transform


def multimodal_instruct_dataset(
    model_transform: Transform,
    *,
    source: str,
    column_map: Optional[Dict[str, str]] = None,
    new_system_prompt: Optional[str] = None,
    filter_fn: Optional[Callable] = None,
    split: str = "train",
    **load_dataset_kwargs: Dict[str, Any],
) -> Union[SFTDataset, PackedDataset]:
    """
    Configure a custom text+image dataset with separate columns for user instruction, image, and model response.

    This builder function can be used to configure a custom multimodal instruct dataset directly from the yaml config
    as an alternative to :class:`~torchtune.datasets.SFTDataset`, as it is made to be config friendly.

    The dataset should follow this format:

    .. code-block:: text

        |  input          |  image          |  output          |
        |-----------------|-----------------|------------------|
        | "user prompt"   | images/1.jpg    | "model response" |

    If your column names are different, you can use the ``column_map`` parameter to change
    the expected column names. For example, if your dataset has columns ``"question"``,
    ``"answer"`` and ``"picture"`` you can use:

        column_map = {"input": "question", "output": "answer", "image": "picture"}

    Masking of the prompt during training is controlled by the ``train_on_input`` flag, which is
    set to ``False`` by default
    - If ``train_on_input`` is True, the prompt is used during training and
    contributes to the loss.
    - If ``train_on_input`` is False, the prompt is masked out (tokens replaced with -100)

    Args:
        model_transform (Transform): callable that applies model-specific pre-processing to the sample.
            This includes tokenization and any modality-specific transforms. It is expected to return at
            minimum ``"tokens"`` and ``"mask"`` keys.
        source (str): path to dataset repository on Hugging Face. For local datasets,
            define source as the data file type (e.g. "json", "csv", "text"), pass
            in the filepath in ``data_files``, and set ``split="train"``. See `Hugging Face's
            <https://huggingface.co/docs/datasets/en/package_reference/loading_methods#datasets.load_dataset.path>`_
            ``load_dataset`` for more details.
        column_map (Optional[Dict[str, str]]): a mapping to change the expected "input"
            and "output" column names to the actual column names in the dataset. Keys should be "input" and
            "output" and values should be the actual column names. Default is None, keeping the default "input"
            and "output" column names.
        new_system_prompt (Optional[str]): if specified, prepend a system message. This can
            serve as instructions to guide the model response. Default is None.
        filter_fn (Optional[Callable]): callable used to filter the dataset prior to any pre-processing. See
            the Hugging Face `docs <https://huggingface.co/docs/datasets/v2.20.0/process#select-and-filter>`_ for more
            details.
        split (str): ``split`` argument for ``datasets.load_dataset``. You can use this argument to load a subset
            of a given split, e.g. ``split="train[:10%]"``. Default is "train".
        **load_dataset_kwargs (Dict[str, Any]): additional keyword arguments to pass to ``load_dataset``,
            such as ``data_files`` or ``split``.

    Examples:

    ::

        my_dataset.json
        [
            {
                "question": "What is presented on the image?",
                "answer": "PyTorch logo.",
                "picture": "rgb_pytorch.png"
            },
            {
                ...
            },
            ...,
        ]

    ::

        >>> from torchtune.datasets.multimodal import multimodal_instruct_dataset
        >>> dataset = multimodal_instruct_dataset(
        ...     model_transform=model_transform,
        ...     source="json",
        ...     data_files="my_dataset.json",
        ...     column_map={
        ...         "input": "question",
        ...         "output": "answer",
        ...         "image": "picture"
        ...     },
        ...     split="train",
        ... )
        >>> tokens = dataset[0]["tokens"]
        >>> model_transform.decode(tokens)
        "What is presented on the image?PyTorch logo."

    This can also be accomplished via the yaml config:

    .. code-block:: yaml

        dataset:
          _component_: torchtune.datasets.multimodal.multimodal_instruct_dataset
          source: json
          data_files: my_dataset.json
          column_map:
            input: question
            output: answer
          train_on_input: False
          packed: False
          split: train

    Returns:
        Union[SFTDataset, PackedDataset]: the configured :class:`~torchtune.datasets.SFTDataset`
            or :class:`~torchtune.datasets.PackedDataset` if ``packed=True``
    """
    message_transform = InputOutputToMessages(
        column_map=column_map, new_system_prompt=new_system_prompt
    )

    ds = SFTDataset(
        source=source,
        message_transform=message_transform,
        model_transform=model_transform,
        filter_fn=filter_fn,
        split=split,
        **load_dataset_kwargs,
    )
    return ds