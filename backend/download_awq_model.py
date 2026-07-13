#!/usr/bin/env python3
"""
Qwen3-4B-Instruct-AWQ模型下载脚本

使用方法：
1. 确保网络连接正常
2. 运行：python download_awq_model.py

注意：
- 如果官方未提供AWQ版本，脚本会先下载原始模型再进行量化
- 模型文件较大，请确保有足够磁盘空间（约8GB原始模型 + 2GB量化后模型）
- 需要CUDA环境支持
"""

import os
import sys
import subprocess
import platform

def check_environment():
    """检查环境"""
    print("=" * 60)
    print("【环境检查】")
    print("=" * 60)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 8):
        print("❌ Python版本需要3.8+")
        return False
    
    # 检查CUDA
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ CUDA可用")
            # 提取GPU信息
            for line in result.stdout.split('\n'):
                if "NVIDIA-SMI" in line:
                    print(f"   {line.strip()}")
                if "GeForce" in line or "RTX" in line:
                    print(f"   GPU: {line.strip().split('|')[1].strip()}")
        else:
            print("❌ CUDA不可用，将尝试CPU模式")
    except FileNotFoundError:
        print("❌ 未检测到NVIDIA GPU，将尝试CPU模式")
    
    # 检查磁盘空间
    if platform.system() == "Windows":
        free_space = subprocess.check_output(
            ["wmic", "logicaldisk", "get", "freespace", "where", "deviceid='C:'"]
        ).decode().split()[1]
        free_gb = int(free_space) / (1024 ** 3)
    else:
        stat = os.statvfs('.')
        free_space = stat.f_frsize * stat.f_bfree
        free_gb = free_space / (1024 ** 3)
    
    print(f"可用磁盘空间: {free_gb:.1f} GB")
    if free_gb < 15:
        print("⚠️ 磁盘空间不足，建议至少保留15GB")
    
    return True

def download_model_from_huggingface(repo_id, local_dir):
    """从HuggingFace下载模型"""
    print(f"\n【下载模型】{repo_id}")
    print("=" * 60)
    
    try:
        from huggingface_hub import snapshot_download
        
        print(f"开始下载模型到: {local_dir}")
        print("提示：如果下载速度慢，可以尝试设置环境变量 HF_ENDPOINT=https://hf-mirror.com")
        
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        
        print(f"✅ 模型下载完成")
        return True
    except ImportError:
        print("❌ 需要安装 huggingface_hub")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        return download_model_from_huggingface(repo_id, local_dir)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def quantize_to_awq(model_path, quant_path):
    """将模型量化为AWQ格式"""
    print(f"\n【AWQ量化】{model_path} -> {quant_path}")
    print("=" * 60)
    
    try:
        from awq import AutoAWQForCausalLM
        from transformers import AutoTokenizer
        
        print("加载原始模型...")
        quantizer = AutoAWQForCausalLM.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        print("开始量化（4-bit）...")
        quantizer.quantize(tokenizer, quant_path=quant_path, bits=4)
        
        print(f"✅ AWQ量化完成")
        return True
    except ImportError:
        print("❌ 需要安装 autoawq")
        print("提示：autoawq需要CUDA编译，建议使用pip install autoawq==0.2.8")
        return False
    except Exception as e:
        print(f"❌ 量化失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Qwen3-4B-Instruct-AWQ模型下载与量化脚本")
    print("=" * 60)
    
    # 检查环境
    if not check_environment():
        return
    
    # 配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    
    RAW_MODEL_NAME = "Qwen/Qwen3-4B-Instruct"
    RAW_MODEL_PATH = os.path.join(MODELS_DIR, "Qwen3-4B-Instruct")
    
    AWQ_MODEL_NAME = "Qwen/Qwen3-4B-Instruct-AWQ"
    AWQ_MODEL_PATH = os.path.join(MODELS_DIR, "Qwen3-4B-Instruct-AWQ")
    
    # 创建目录
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # 检查是否已有AWQ模型
    if os.path.exists(AWQ_MODEL_PATH) and len(os.listdir(AWQ_MODEL_PATH)) > 0:
        print(f"\n✅ AWQ模型已存在: {AWQ_MODEL_PATH}")
        print("跳过下载和量化")
        return
    
    # 尝试直接下载AWQ模型（如果官方提供）
    print("\n【尝试直接下载AWQ模型】")
    if download_model_from_huggingface(AWQ_MODEL_NAME, AWQ_MODEL_PATH):
        print("✅ 直接下载AWQ模型成功")
        return
    
    # 如果官方没有提供AWQ版本，先下载原始模型再量化
    print("\n【官方未提供AWQ版本，将先下载原始模型再进行量化】")
    
    # 下载原始模型
    if not os.path.exists(RAW_MODEL_PATH) or len(os.listdir(RAW_MODEL_PATH)) == 0:
        if not download_model_from_huggingface(RAW_MODEL_NAME, RAW_MODEL_PATH):
            print("❌ 无法下载原始模型，退出")
            return
    else:
        print(f"✅ 原始模型已存在: {RAW_MODEL_PATH}")
    
    # 安装量化工具
    print("\n【安装AWQ量化工具】")
    subprocess.run([sys.executable, "-m", "pip", "install", "autoawq==0.2.8", "transformers", "accelerate", "-q"])
    
    # 执行量化
    if quantize_to_awq(RAW_MODEL_PATH, AWQ_MODEL_PATH):
        print("\n" + "=" * 60)
        print("🎉 模型下载和量化完成！")
        print(f"AWQ模型路径: {AWQ_MODEL_PATH}")
        print("请更新.env配置:")
        print("  VLLM_MODEL_NAME=Qwen/Qwen3-4B-Instruct-AWQ")
        print(f"  VLLM_MODEL_PATH={AWQ_MODEL_PATH}")
        print("  CHAT_MODEL_TYPE=vllm")
        print("=" * 60)
    else:
        print("\n❌ 量化失败，请检查CUDA环境")

if __name__ == "__main__":
    main()