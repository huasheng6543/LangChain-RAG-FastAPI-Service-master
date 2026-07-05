import os
import sys

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download

model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
os.makedirs(model_dir, exist_ok=True)

print(f"模型下载目录: {model_dir}")

reranker_dir = os.path.join(model_dir, 'Qwen3-Reranker-0.6B')
llm_dir = os.path.join(model_dir, 'Qwen3-7B-Instruct-AWQ')

print("\n=== 开始下载 Qwen3-Reranker-0.6B ===")
try:
    snapshot_download(
        repo_id='Qwen/Qwen3-Reranker-0.6B',
        local_dir=reranker_dir,
        local_dir_use_symlinks=False
    )
    print("✅ Qwen3-Reranker-0.6B 下载完成")
except Exception as e:
    print(f"❌ Qwen3-Reranker-0.6B 下载失败: {e}")

print("\n=== 开始下载 Qwen3-7B-Instruct-AWQ ===")
try:
    snapshot_download(
        repo_id='Qwen/Qwen3-7B-Instruct-AWQ',
        local_dir=llm_dir,
        local_dir_use_symlinks=False
    )
    print("✅ Qwen3-7B-Instruct-AWQ 下载完成")
except Exception as e:
    print(f"❌ Qwen3-7B-Instruct-AWQ 下载失败: {e}")

print("\n=== 下载完成 ===")
