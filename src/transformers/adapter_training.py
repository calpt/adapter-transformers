from dataclasses import dataclass, field
from typing import Optional

from .adapter_bert import BertModelHeadsMixin
from .adapter_config import AdapterType


@dataclass
class AdapterArguments:
    """
    The subset of arguments related to adapter training.
    """

    train_adapter: bool = field(
        default=False, metadata={"help": "Train a text task adapter instead of the full model."}
    )
    load_task_adapter: Optional[str] = field(
        default="", metadata={"help": "Pre-trained task adapter to be loaded for further training."}
    )
    load_lang_adapter: Optional[str] = field(
        default=None, metadata={"help": "Pre-trained language adapter to be loaded."}
    )
    adapter_config: Optional[str] = field(default="pfeiffer", metadata={"help": "Adapter configuration."})
    lang_adapter_config: Optional[str] = field(default=None, metadata={"help": "Language adapter configuration."})


def setup_task_adapter_training(model, task_name: str, adapter_args: AdapterArguments):
    """Sets up task adapter training for a given pre-trained model.

    Args:
        model (PretrainedModel): The model for which to set up task adapter training.
        task_name (str): The name of the task to train.
        adapter_args (AdapterArguments): Adapter traininf arguments.
    """
    language = adapter_args.load_lang_adapter
    if adapter_args.train_adapter:
        # task adapter - only add if not existing
        if task_name not in model.config.adapters.adapter_list(AdapterType.text_task):
            model.set_adapter_config(AdapterType.text_task, adapter_args.adapter_config)
            # load a pre-trained adapter for fine-tuning if specified
            if adapter_args.load_task_adapter:
                model.load_adapter(adapter_args.load_task_adapter, AdapterType.text_task, load_as=task_name)
            # otherwise, add a new adapter
            else:
                model.add_adapter(task_name, AdapterType.text_task)
        # language adapter - only add if not existing
        if language and language not in model.config.adapters.adapter_list(AdapterType.text_lang):
            model.set_adapter_config(
                AdapterType.text_lang, adapter_args.lang_adapter_config or adapter_args.adapter_config
            )
            model.load_adapter(language, AdapterType.text_lang)
        # enable adapter training
        model.train_task_adapter()
    # set adapters as default if possible
    if isinstance(model, BertModelHeadsMixin):
        if language:
            model.set_active_language(language)
        model.set_active_task(task_name)
