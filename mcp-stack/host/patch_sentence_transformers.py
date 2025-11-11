import sys
import os
from pathlib import Path

# Find the site-packages directory
site_packages = None
for path in sys.path:
    if 'site-packages' in path and 'venv' in path:
        site_packages = Path(path)
        break

if not site_packages:
    print("Could not find site-packages directory in the virtual environment")
    sys.exit(1)

# Path to the file we need to patch
sentence_transformers_path = site_packages / 'sentence_transformers' / 'SentenceTransformer.py'

if not sentence_transformers_path.exists():
    print(f"Could not find {sentence_transformers_path}")
    sys.exit(1)

# Read the file content
with open(sentence_transformers_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the import statement
new_content = content.replace(
    'from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download',
    'from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url\nfrom huggingface_compat import cached_download'
)

# Write the modified content back to the file
with open(sentence_transformers_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully patched {sentence_transformers_path}")
