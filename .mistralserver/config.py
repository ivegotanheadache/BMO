
MODELPATH =""#YOUR MISTRAL MODEL PATH
default_llm_config = { #CHANGE IT FOR YOUR SYSTEM
    "verbose": False,
    "model_path": MODELPATH,
    "n_ctx": 32768,
    "n_threads": 10,
    "n_batch": 254,
    "use_mlock": True
}

