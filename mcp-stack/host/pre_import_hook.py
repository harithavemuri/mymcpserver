"""Pre-import hook to patch the sentence-transformers package."""
import sys
import importlib

# This will be called before any other imports
def _monkey_patch():
    # Import the huggingface_hub module and patch it
    import huggingface_hub

    # Define a dummy cached_download function
    def cached_download(*args, **kwargs):
        from huggingface_hub import hf_hub_download
        return hf_hub_download(*args, **kwargs)

    # Add the cached_download function to the huggingface_hub module
    huggingface_hub.cached_download = cached_download

    # Also patch the __getattr__ to handle the case when cached_download is accessed as an attribute
    original_getattr = huggingface_hub.__getattr__

    def patched_getattr(name):
        if name == 'cached_download':
            return cached_download
        return original_getattr(name)

    huggingface_hub.__getattr__ = patched_getattr

# Apply the monkey patch
_monkey_patch()
