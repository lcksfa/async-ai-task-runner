"""
AI服务模块
统一处理不同AI提供商的API调用
支持OpenAI、Anthropic、DeepSeek等多个AI服务
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import requests
import json
from app.core.config import settings


class AIProvider(ABC):
    """AI提供商抽象基类"""

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本的抽象方法"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API提供商"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo",
                     temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """调用OpenAI API生成文本"""
        try:
            url = f"{self.base_url}/chat/completions"
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")


class DeepSeekProvider(AIProvider):
    """DeepSeek API提供商"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_text(self, prompt: str, model: str = "deepseek-chat",
                     temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """调用DeepSeek API生成文本"""
        try:
            url = f"{self.base_url}/v1/chat/completions"
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            raise Exception(f"DeepSeek API调用失败: {str(e)}")


class AnthropicProvider(AIProvider):
    """Anthropic Claude API提供商"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

    def generate_text(self, prompt: str, model: str = "claude-3-sonnet-20240229",
                     temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> str:
        """调用Anthropic Claude API生成文本"""
        try:
            url = f"{self.base_url}/v1/messages"
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["content"][0]["text"]

        except Exception as e:
            raise Exception(f"Anthropic API调用失败: {str(e)}")


class AIService:
    """AI服务管理器"""

    def __init__(self):
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化可用的AI提供商"""

        # 初始化OpenAI
        if settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(
                settings.openai_api_key,
                settings.openai_base_url
            )
            print("✅ OpenAI提供商已初始化")

        # 初始化DeepSeek
        if settings.deepseek_api_key:
            self.providers["deepseek"] = DeepSeekProvider(
                settings.deepseek_api_key,
                settings.deepseek_base_url
            )
            print("✅ DeepSeek提供商已初始化")

        # 初始化Anthropic
        if settings.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(
                settings.anthropic_api_key,
                settings.anthropic_base_url
            )
            print("✅ Anthropic提供商已初始化")

    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        """获取AI提供商"""
        if not self.providers:
            raise Exception("❌ 没有可用的AI提供商。请配置API密钥。")

        if provider_name:
            if provider_name not in self.providers:
                available = ", ".join(self.providers.keys())
                raise Exception(f"❌ AI提供商 '{provider_name}' 不可用。可用提供商: {available}")
            return self.providers[provider_name]

        # 如果没有指定提供商，返回第一个可用的
        return list(self.providers.values())[0]

    def generate_text(self, prompt: str, provider_name: Optional[str] = None,
                     model: Optional[str] = None, **kwargs) -> str:
        """使用指定的AI提供商生成文本"""
        try:
            provider = self.get_provider(provider_name)

            # 如果没有指定模型，使用默认模型
            if not model:
                if isinstance(provider, DeepSeekProvider):
                    model = "deepseek-chat"
                elif isinstance(provider, OpenAIProvider):
                    model = settings.default_ai_model
                elif isinstance(provider, AnthropicProvider):
                    model = "claude-3-sonnet-20240229"
                else:
                    model = settings.default_ai_model

            # 设置默认参数
            generation_params = {
                "temperature": settings.ai_temperature,
                "max_tokens": settings.ai_max_tokens,
                **kwargs
            }

            print(f"🤖 使用 {provider.__class__.__name__} 生成文本...")
            print(f"📝 Prompt: {prompt[:100]}...")
            print(f"🧠 Model: {model}")

            result = provider.generate_text(prompt, model=model, **generation_params)

            print(f"✅ 文本生成完成")
            return result

        except Exception as e:
            error_msg = f"AI文本生成失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

    def list_available_providers(self) -> Dict[str, str]:
        """列出所有可用的AI提供商"""
        return {
            name: provider.__class__.__name__
            for name, provider in self.providers.items()
        }

    def is_available(self) -> bool:
        """检查是否有可用的AI提供商"""
        return len(self.providers) > 0


# 全局AI服务实例
ai_service = AIService()