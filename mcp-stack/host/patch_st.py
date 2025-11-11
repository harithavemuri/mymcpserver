"""Patch the sentence-transformers package to fix the cached_download import."""
import sys
import os
import importlib
import warnings

def patch_sentence_transformers():
    """Patch the sentence-transformers package to use our compatibility layer."""
    try:
        # Import our compatibility shim first
        from huggingface_compat import cached_download
        
        # Patch the sentence_transformers.util module
        import sentence_transformers.util as util
        
        # Replace the cached_download function in the module
        util.cached_download = cached_download
        
        # Also patch the __init__ function to ensure our patch is always applied
        original_init = util.__init__
        
        def patched_init(*args, **kwargs):
            original_init(*args, **kwargs)
            util.cached_download = cached_download
        
        util.__init__ = patched_init
        
        # Also patch the huggingface_hub module directly
        try:
            import huggingface_hub
            huggingface_hub.cached_download = cached_download
            
            # Patch the __getattr__ to handle the case when cached_download is accessed as an attribute
            original_getattr = huggingface_hub.__getattr__ if hasattr(huggingface_hub, '__getattr__') else None
            
            def patched_getattr(name):
                if name == 'cached_download':
                    return cached_download
                if original_getattr is not None:
                    return original_getattr(name)
                raise AttributeError(f"module 'huggingface_hub' has no attribute '{name}'")
            
            huggingface_hub.__getattr__ = patched_getattr
            
        except ImportError:
            warnings.warn("Could not import huggingface_hub to patch it directly.")
        
        return True
    except Exception as e:
        warnings.warn(f"Failed to patch sentence-transformers: {str(e)}")
        return False

# Apply the patch when this module is imported
patch_sentence_transformers()
