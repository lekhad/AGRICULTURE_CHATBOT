from safetensors.torch import load_file
import torch

state_dict = load_file("bert_intent_model/model.safetensors")
torch.save(state_dict, "bert_intent_model/pytorch_model.bin")
