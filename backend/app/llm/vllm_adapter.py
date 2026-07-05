import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.core.logger_handler import logger

load_dotenv()


class VLLMAdapter:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
        self.model_name = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen3-7B-Instruct-AWQ")
        self.model_path = os.getenv("VLLM_MODEL_PATH", "./models/Qwen3-7B-Instruct-AWQ")
        self.gpu_memory_utilization = float(os.getenv("VLLM_GPU_MEMORY_UTILIZATION", "0.90"))
        self.max_model_len = int(os.getenv("VLLM_MAX_MODEL_LEN", "8192"))
        self.enforce_eager = os.getenv("VLLM_ENFORCE_EAGER", "true").lower() == "true"
        self.quantization = os.getenv("VLLM_QUANTIZATION", "AWQ")
        
        self._is_available = True
    
    @property
    def is_available(self):
        return self._is_available
    
    async def initialize(self):
        async with self._lock:
            if self._initialized:
                return
            
            try:
                from vllm import LLM, SamplingParams
                
                logger.info(f"【vLLM】开始加载模型: {self.model_name}")
                logger.info(f"【vLLM】模型路径: {self.model_path}")
                logger.info(f"【vLLM】配置参数 - GPU显存利用率: {self.gpu_memory_utilization}, "
                          f"最大上下文: {self.max_model_len}, 量化: {self.quantization}, "
                          f"enforce_eager: {self.enforce_eager}")
                
                self._model = LLM(
                    model=self.model_path if os.path.exists(self.model_path) else self.model_name,
                    quantization=self.quantization,
                    gpu_memory_utilization=self.gpu_memory_utilization,
                    max_model_len=self.max_model_len,
                    enforce_eager=self.enforce_eager,
                    trust_remote_code=True,
                )
                
                self._tokenizer = self._model.get_tokenizer()
                self._initialized = True
                logger.info(f"【vLLM】模型加载成功")
                
            except ImportError:
                logger.warning("【vLLM】vLLM库未安装，将使用备用模型")
                self._is_available = False
                self._initialized = True
            except Exception as e:
                logger.error(f"【vLLM】模型加载失败: {e}")
                self._is_available = False
                self._initialized = True
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()
        
        if not self._is_available or self._model is None:
            return {
                "success": False,
                "text": "",
                "error": "vLLM模型不可用"
            }
        
        try:
            from vllm import SamplingParams
            
            params = SamplingParams(
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                top_p=kwargs.get("top_p", 0.9),
                stop=kwargs.get("stop", ["<|end_of_text|>"]),
            )
            
            logger.debug(f"【vLLM】生成请求 - prompt长度: {len(prompt)}")
            
            outputs = self._model.generate([prompt], params)
            output = outputs[0]
            
            generated_text = output.outputs[0].text
            prompt_tokens = output.prompt_token_ids
            generated_tokens = output.outputs[0].token_ids
            
            metrics = {
                "prompt_tokens": len(prompt_tokens),
                "generated_tokens": len(generated_tokens),
                "total_tokens": len(prompt_tokens) + len(generated_tokens),
                "finish_reason": output.outputs[0].finish_reason,
            }
            
            logger.debug(f"【vLLM】生成完成 - 生成token数: {len(generated_tokens)}, "
                      f"finish_reason: {output.outputs[0].finish_reason}")
            
            return {
                "success": True,
                "text": generated_text,
                "error": "",
                "metrics": metrics
            }
        
        except Exception as e:
            logger.error(f"【vLLM】生成失败: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    async def tokenize(self, text: str) -> list:
        if not self._initialized:
            await self.initialize()
        
        if not self._is_available or self._tokenizer is None:
            return []
        
        try:
            return self._tokenizer.encode(text)
        except Exception as e:
            logger.error(f"【vLLM】tokenize失败: {e}")
            return []
    
    async def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "quantization": self.quantization,
            "max_model_len": self.max_model_len,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "is_available": self._is_available,
            "is_initialized": self._initialized,
        }


vllm_adapter = VLLMAdapter()