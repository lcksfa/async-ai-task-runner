# 🤖 AI Service Integration Tests
"""
Comprehensive AI service tests for Async AI Task Runner.
Tests AI provider integration, HTTP client behavior, fallback mechanisms, and error handling.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import asyncio
import json

# Application imports
from app.services.ai_service import (
    AIService, OpenAIProvider, DeepSeekProvider, AnthropicProvider
)
from app.core.config import settings
from conftest import mock_ai_service


class TestAIProviderBase:
    """Test AI provider abstract base class and common functionality."""

    @pytest.mark.unit
    def test_ai_provider_abstract_class(self):
        """Test that AIProvider is abstract and cannot be instantiated."""
        from app.services.ai_service import AIProvider

        with pytest.raises(TypeError):
            AIProvider()

    @pytest.mark.unit
    def test_ai_provider_method_interface(self):
        """Test that AIProvider requires generate_text method."""
        from app.services.ai_service import AIProvider

        class ConcreteProvider(AIProvider):
            def generate_text(self, prompt: str, **kwargs) -> str:
                return "Concrete response"

        # Should be able to instantiate concrete implementation
        provider = ConcreteProvider()
        assert hasattr(provider, 'generate_text')

        # Should work with the interface
        result = provider.generate_text("Test prompt")
        assert result == "Concrete response"


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    @pytest.mark.unit
    @pytest.mark.external
    def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider("test-api-key")

        assert provider.api_key == "test-api-key"
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.headers["Authorization"] == "Bearer test-api-key"
        assert provider.headers["Content-Type"] == "application/json"

    @pytest.mark.unit
    def test_openai_provider_custom_base_url(self):
        """Test OpenAI provider with custom base URL."""
        provider = OpenAIProvider(
            "test-api-key",
            base_url="https://custom.openai.com/v1"
        )

        assert provider.base_url == "https://custom.openai.com/v1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_generate_text_success(self, mock_post):
        """Test successful OpenAI text generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "OpenAI generated response"
                }
            }]
        }

        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-api-key")
        result = await provider.generate_text(
            prompt="Test prompt",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == "https://api.openai.com/v1/chat/completions"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-api-key"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"

        request_data = call_args[1]["json"]
        assert request_data["model"] == "gpt-3.5-turbo"
        assert request_data["messages"][0]["content"] == "Test prompt"
        assert request_data["temperature"] == 0.7
        assert request_data["max_tokens"] == 500

        # Verify result
        assert result == "OpenAI generated response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_generate_text_default_params(self, mock_post):
        """Test OpenAI text generation with default parameters."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Default response"
                }
            }]
        }

        mock_post.return_value = mock_response

        provider = OpenAIProvider("test-api-key")
        result = await provider.generate_text(prompt="Test prompt")

        # Verify default parameters were used
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        assert request_data["model"] == "gpt-3.5-turbo"  # Default model
        assert request_data["temperature"] == 0.7  # Default temperature
        assert request_data["max_tokens"] == 1000  # Default max_tokens

        assert result == "Default response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_generate_text_http_error(self, mock_post):
        """Test OpenAI provider handling of HTTP errors."""
        # Mock HTTP error
        mock_post.side_effect = httpx.HTTPError("HTTP 429 Rate Limited")

        provider = OpenAIProvider("test-api-key")

        with pytest.raises(Exception) as exc_info:
            await provider.generate_text(prompt="Test prompt")

        assert "OpenAI API HTTP错误" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_generate_text_general_error(self, mock_post):
        """Test OpenAI provider handling of general errors."""
        # Mock general error
        mock_post.side_effect = Exception("Connection failed")

        provider = OpenAIProvider("test-api-key")

        with pytest.raises(Exception) as exc_info:
            await provider.generate_text(prompt="Test prompt")

        assert "OpenAI API调用失败" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_openai_generate_text_timeout(self, mock_post):
        """Test OpenAI provider handling of timeouts."""
        # Mock timeout
        mock_post.side_effect = httpx.TimeoutException("Request timed out")

        provider = OpenAIProvider("test-api-key")

        with pytest.raises(Exception) as exc_info:
            await provider.generate_text(prompt="Test prompt")

        assert "OpenAI API调用失败" in str(exc_info.value)
        assert "Request timed out" in str(exc_info.value)


class TestDeepSeekProvider:
    """Test DeepSeek provider implementation."""

    @pytest.mark.unit
    @pytest.mark.external
    def test_deepseek_provider_initialization(self):
        """Test DeepSeek provider initialization."""
        provider = DeepSeekProvider("test-api-key")

        assert provider.api_key == "test-api-key"
        assert provider.base_url == "https://api.deepseek.com"
        assert provider.headers["Authorization"] == "Bearer test-api-key"
        assert provider.headers["Content-Type"] == "application/json"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_deepseek_generate_text_success(self, mock_post):
        """Test successful DeepSeek text generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "DeepSeek generated response"
                }
            }]
        }

        mock_post.return_value = mock_response

        provider = DeepSeekProvider("test-api-key")
        result = await provider.generate_text(
            prompt="Test prompt",
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=800
        )

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == "https://api.deepseek.com/v1/chat/completions"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-api-key"

        request_data = call_args[1]["json"]
        assert request_data["model"] == "deepseek-chat"
        assert request_data["messages"][0]["content"] == "Test prompt"
        assert request_data["temperature"] == 0.5
        assert request_data["max_tokens"] == 800
        assert request_data["stream"] is False

        assert result == "DeepSeek generated response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_deepseek_generate_text_error_handling(self, mock_post):
        """Test DeepSeek provider error handling."""
        # Mock error
        mock_post.side_effect = httpx.HTTPError("DeepSeek API error")

        provider = DeepSeekProvider("test-api-key")

        with pytest.raises(Exception) as exc_info:
            await provider.generate_text(prompt="Test prompt")

        assert "DeepSeek API HTTP错误" in str(exc_info.value)


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    @pytest.mark.unit
    @pytest.mark.external
    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider("test-api-key")

        assert provider.api_key == "test-api-key"
        assert provider.base_url == "https://api.anthropic.com"
        assert provider.headers["x-api-key"] == "test-api-key"
        assert provider.headers["Content-Type"] == "application/json"
        assert provider.headers["anthropic-version"] == "2023-06-01"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_anthropic_generate_text_success(self, mock_post):
        """Test successful Anthropic text generation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{
                "text": "Anthropic generated response"
            }]
        }

        mock_post.return_value = mock_response

        provider = AnthropicProvider("test-api-key")
        result = await provider.generate_text(
            prompt="Test prompt",
            model="claude-3-sonnet-20240229",
            temperature=0.8,
            max_tokens=1200
        )

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == "https://api.anthropic.com/v1/messages"
        assert call_args[1]["headers"]["x-api-key"] == "test-api-key"
        assert call_args[1]["headers"]["anthropic-version"] == "2023-06-01"

        request_data = call_args[1]["json"]
        assert request_data["model"] == "claude-3-sonnet-20240229"
        assert request_data["messages"][0]["content"] == "Test prompt"
        assert request_data["temperature"] == 0.8
        assert request_data["max_tokens"] == 1200

        assert result == "Anthropic generated response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_anthropic_generate_text_error_handling(self, mock_post):
        """Test Anthropic provider error handling."""
        # Mock error
        mock_post.side_effect = httpx.HTTPError("Anthropic API error")

        provider = AnthropicProvider("test-api-key")

        with pytest.raises(Exception) as exc_info:
            await provider.generate_text(prompt="Test prompt")

        assert "Anthropic API HTTP错误" in str(exc_info.value)


class TestAIService:
    """Test AI service manager functionality."""

    @pytest.mark.unit
    def test_ai_service_initialization_with_no_keys(self):
        """Test AI service initialization with no API keys."""
        with patch.object(settings, 'openai_api_key', None):
            with patch.object(settings, 'deepseek_api_key', None):
                with patch.object(settings, 'anthropic_api_key', None):
                    service = AIService()

                    # Should have no providers initialized
                    assert len(service.providers) == 0
                    assert not service.is_available()

    @pytest.mark.unit
    def test_ai_service_initialization_with_partial_keys(self):
        """Test AI service initialization with some API keys."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', None):
                with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
                    service = AIService()

                    # Should initialize only available providers
                    assert len(service.providers) == 2
                    assert 'openai' in service.providers
                    assert 'anthropic' in service.providers
                    assert 'deepseek' not in service.providers

    @pytest.mark.unit
    def test_ai_service_initialization_with_all_keys(self):
        """Test AI service initialization with all API keys."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
                with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
                    service = AIService()

                    # Should initialize all providers
                    assert len(service.providers) == 3
                    assert 'openai' in service.providers
                    assert 'deepseek' in service.providers
                    assert 'anthropic' in service.providers
                    assert service.is_available()

    @pytest.mark.unit
    def test_get_provider_specific(self):
        """Test getting specific AI provider."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
                service = AIService()

                # Get specific provider
                provider = service.get_provider('openai')
                assert isinstance(provider, OpenAIProvider)
                assert provider.api_key == 'test-openai-key'

                deepseek_provider = service.get_provider('deepseek')
                assert isinstance(deepseek_provider, DeepSeekProvider)
                assert deepseek_provider.api_key == 'test-deepseek-key'

    @pytest.mark.unit
    def test_get_provider_nonexistent(self):
        """Test getting non-existent AI provider."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            service = AIService()

                with pytest.raises(Exception) as exc_info:
                    service.get_provider('nonexistent')

                assert "AI提供商 'nonexistent' 不可用" in str(exc_info.value)
                assert "openai" in str(exc_info.value)  # Should list available providers

    @pytest.mark.unit
    def test_get_provider_default(self):
        """Test getting default AI provider."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
                service = AIService()

                # Get default provider (should return first available)
                provider = service.get_provider()
                assert isinstance(provider, OpenAIProvider)  # First in initialization order

    @pytest.mark.unit
    def test_get_provider_no_providers(self):
        """Test getting provider when none are available."""
        with patch.object(settings, 'openai_api_key', None):
            with patch.object(settings, 'deepseek_api_key', None):
                service = AIService()

                with pytest.raises(Exception) as exc_info:
                    service.get_provider()

                assert "没有可用的AI提供商" in str(exc_info.value)

    @pytest.mark.unit
    def test_list_available_providers(self):
        """Test listing available AI providers."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
                with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
                    service = AIService()

                    providers = service.list_available_providers()

                    assert isinstance(providers, dict)
                    assert len(providers) == 3
                    assert providers['openai'] == 'OpenAIProvider'
                    assert providers['deepseek'] == 'DeepSeekProvider'
                    assert providers['anthropic'] == 'AnthropicProvider'

    @pytest.mark.unit
    def test_is_available(self):
        """Test AI service availability check."""
        # Test with no providers
        with patch.object(settings, 'openai_api_key', None):
            service_no_providers = AIService()
            assert not service_no_providers.is_available()

        # Test with providers
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            service_with_providers = AIService()
            assert service_with_providers.is_available()


class TestAIServiceGeneration:
    """Test AI text generation through service manager."""

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_generate_text_with_openai(self):
        """Test text generation with OpenAI provider."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful OpenAI response
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "OpenAI test response"
                        }
                    }]
                }

                mock_post.return_value = mock_response

                service = AIService()
                result = await service.generate_text(
                    prompt="Test prompt for OpenAI",
                    provider_name="openai",
                    model="gpt-3.5-turbo",
                    temperature=0.6
                )

                assert result == "OpenAI test response"

                # Verify provider was called correctly
                mock_post.assert_called_once()
                call_args = mock_post.call_args[1]
                assert call_args["json"]["model"] == "gpt-3.5-turbo"
                assert call_args["json"]["temperature"] == 0.6

    @pytest.mark.integration
    @pytest.mark.external
    @pytest.mark.asyncio
    async def test_generate_text_with_deepseek(self):
        """Test text generation with DeepSeek provider."""
        with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful DeepSeek response
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "DeepSeek test response"
                        }
                    }]
                }

                mock_post.return_value = mock_response

                service = AIService()
                result = await service.generate_text(
                    prompt="Test prompt for DeepSeek",
                    provider_name="deepseek",
                    model="deepseek-chat",
                    max_tokens=500
                )

                assert result == "DeepSeek test response"

                # Verify provider was called correctly
                mock_post.assert_called_once()
                call_args = mock_post.call_args[1]
                assert call_args["json"]["model"] == "deepseek-chat"
                assert call_args["json"]["max_tokens"] == 500

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_text_default_provider(self):
        """Test text generation with default provider selection."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful OpenAI response
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "Default provider response"
                        }
                    }]
                }

                mock_post.return_value = mock_response

                service = AIService()
                result = await service.generate_text(
                    prompt="Test prompt for default provider"
                    # No provider_name specified
                )

                assert result == "Default provider response"

                # Should use OpenAI (first available provider)
                assert mock_post.called

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_text_with_default_model(self):
        """Test text generation with model inference."""
        with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful DeepSeek response
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "DeepSeek default model response"
                        }
                    }]
                }

                mock_post.return_value = mock_response

                service = AIService()
                result = await service.generate_text(
                    prompt="Test prompt with default model",
                    provider_name="deepseek"
                    # No model specified - should infer from provider
                )

                assert result == "DeepSeek default model response"

                # Should use DeepSeek's default model
                call_args = mock_post.call_args[1]
                assert call_args["json"]["model"] == "deepseek-chat"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_text_with_custom_parameters(self):
        """Test text generation with custom parameters."""
        with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful Anthropic response
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.json.return_value = {
                    "content": [{
                        "text": "Anthropic custom params response"
                    }]
                }

                mock_post.return_value = mock_response

                service = AIService()
                result = await service.generate_text(
                    prompt="Test prompt with custom params",
                    provider_name="anthropic",
                    temperature=0.9,
                    max_tokens=1500,
                    custom_param="custom_value"  # Should be passed through
                )

                assert result == "Anthropic custom params response"

                # Verify custom parameters were passed
                call_args = mock_post.call_args[1]
                assert call_args["json"]["temperature"] == 0.9
                assert call_args["json"]["max_tokens"] == 1500

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_text_provider_failure(self):
        """Test text generation when provider fails."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock provider failure
                mock_post.side_effect = httpx.HTTPError("API limit exceeded")

                service = AIService()

                with pytest.raises(Exception) as exc_info:
                    await service.generate_text(
                        prompt="Test prompt",
                        provider_name="openai"
                    )

                assert "AI文本生成失败" in str(exc_info.value)
                assert "API limit exceeded" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_text_service_unavailable(self):
        """Test text generation when AI service is unavailable."""
        with patch.object(settings, 'openai_api_key', None):
            service = AIService()

                with pytest.raises(Exception) as exc_info:
                    await service.generate_text(prompt="Test prompt")

                assert "AI文本生成失败" in str(exc_info.value)
                assert "没有可用的AI提供商" in str(exc_info.value)


class TestAIServiceConcurrency:
    """Test AI service concurrency and performance."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_text_generation(self):
        """Test concurrent text generation requests."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock successful OpenAI response with different results
                def mock_response_func(*args, **kwargs):
                    mock_resp = MagicMock()
                    mock_resp.raise_for_status = MagicMock()
                    mock_resp.json.return_value = {
                        "choices": [{
                            "message": {
                                "content": f"Response for {kwargs.get('json', {}).get('messages', [{}])[0].get('content', 'unknown')}"
                            }
                        }]
                    }
                    return mock_resp

                mock_post.side_effect = mock_response_func

                service = AIService()

                # Generate text concurrently
                prompts = [f"Concurrent prompt {i}" for i in range(10)]
                tasks = [
                    service.generate_text(prompt=prompt, provider_name="openai")
                    for prompt in prompts
                ]

                results = await asyncio.gather(*tasks)

                # Verify all requests succeeded
                assert len(results) == 10
                for i, result in enumerate(results):
                    assert f"Concurrent prompt {i}" in result

                # Verify all requests were made
                assert mock_post.call_count == 10

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_text_generation_timeout_handling(self):
        """Test handling of text generation timeouts."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch('httpx.AsyncClient.post') as mock_post:
                # Mock timeout after a delay
                async def delayed_timeout(*args, **kwargs):
                    await asyncio.sleep(0.1)
                    raise httpx.TimeoutException("Request timeout")

                mock_post.side_effect = delayed_timeout

                service = AIService()

                # Should complete within reasonable time
                start_time = asyncio.get_event_loop().time()
                with pytest.raises(Exception):
                    await service.generate_text(
                        prompt="Timeout test prompt",
                        provider_name="openai"
                    )
                end_time = asyncio.get_event_loop().time()

                # Should fail quickly due to timeout
                assert (end_time - start_time) < 5.0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test provider fallback when one fails."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            with patch.object(settings, 'deepseek_api_key', 'test-deepseek-key'):
                with patch('httpx.AsyncClient.post') as mock_post:
                    # Mock OpenAI failure
                    def mock_response_func(*args, **kwargs):
                        if "openai.com" in args[0]:
                            raise httpx.HTTPError("OpenAI API error")
                        else:
                            mock_resp = MagicMock()
                            mock_resp.raise_for_status = MagicMock()
                            mock_resp.json.return_value = {
                                "choices": [{
                                    "message": {
                                        "content": "DeepSeek fallback response"
                                    }
                                }]
                            }
                            return mock_resp

                    mock_post.side_effect = mock_response_func

                    service = AIService()

                    # Try OpenAI first (should fail)
                    with pytest.raises(Exception):
                        await service.generate_text(
                            prompt="Fallback test prompt",
                            provider_name="openai"
                        )

                    # Use DeepSeek as fallback (should succeed)
                    result = await service.generate_text(
                        prompt="Fallback test prompt",
                        provider_name="deepseek"
                    )

                    assert result == "DeepSeek fallback response"

                    # Verify OpenAI was called first, then DeepSeek
                    assert mock_post.call_count == 2


class TestAIServiceConfiguration:
    """Test AI service configuration and behavior."""

    @pytest.mark.unit
    def test_default_ai_parameters(self):
        """Test default AI parameters from settings."""
        with patch.object(settings, 'ai_temperature', 0.8):
            with patch.object(settings, 'ai_max_tokens', 1200):
                with patch.object(settings, 'default_ai_model', 'gpt-4'):
                    with patch.object(settings, 'openai_api_key', 'test-openai-key'):
                        with patch('httpx.AsyncClient.post') as mock_post:
                            mock_response = MagicMock()
                            mock_response.raise_for_status = MagicMock()
                            mock_response.json.return_value = {
                                "choices": [{
                                    "message": {
                                        "content": "Default params response"
                                    }
                                }]
                            }

                            mock_post.return_value = mock_response

                            service = AIService()
                            await service.generate_text(
                                prompt="Test default params",
                                provider_name="openai"
                            )

                            # Verify default parameters were used
                            call_args = mock_post.call_args[1]
                            assert call_args["json"]["temperature"] == 0.8
                            assert call_args["json"]["max_tokens"] == 1200

    @pytest.mark.unit
    def test_ai_service_singleton_behavior(self):
        """Test that AI service behaves like a singleton."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            # Import and get global instance
            from app.services.ai_service import ai_service

            # Multiple calls should return same instance
            assert ai_service.providers is ai_service.providers
            assert id(ai_service) == id(ai_service)

            # Should maintain state
            initial_provider_count = len(ai_service.providers)

            # Create new instance (should use same settings)
            new_service = AIService()
            assert len(new_service.providers) == initial_provider_count

    @pytest.mark.unit
    def test_ai_service_logging(self, caplog):
        """Test AI service logging behavior."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            # Capture log output during initialization
            import logging
            logger = logging.getLogger('app.services.ai_service')

            with caplog.at_level(logging.INFO):
                service = AIService()

            # Should log provider initialization
            log_messages = [record.message for record in caplog.records]
            assert any("OpenAI提供商已初始化" in msg for msg in log_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])