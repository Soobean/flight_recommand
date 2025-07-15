import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import anthropic
import openai

from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 기반 분석 서비스"""

    def __init__(self):
        """LLM 클라이언트 초기화"""
        self.client = self._initialize_client()
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

    def _initialize_client(self):
        """LLM 클라이언트 초기화"""
        if settings.LLM_PROVIDER == "azure_openai":
            if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
                return None

            return openai.AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
        elif settings.LLM_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY:
                return None
            return openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif settings.LLM_PROVIDER == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                return None
            return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            return None

    async def analyze_flights(
        self, flights_data: List[Dict], context: Dict = None
    ) -> Dict[str, Any]:
        """항공편 데이터 분석"""
        try:
            if not self.client:
                return await self._get_dummy_analysis(flights_data)

            if len(flights_data) > settings.MAX_FLIGHTS_PER_ANALYSIS:
                flights_data = flights_data[: settings.MAX_FLIGHTS_PER_ANALYSIS]

            analysis_results = []
            for flight in flights_data:
                efficiency_result = await self.calculate_efficiency_score(
                    flight, context
                )
                analysis_results.append(efficiency_result)

            return {
                "success": True,
                "results": analysis_results,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "context": context or {},
            }
        except Exception as e:
            logger.error(f"항공편 분석 오류:{str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "analysis_timestamp": datetime.now().isoformat(),
            }

    async def calculate_efficiency_score(
        self, flight_data: Dict, context: Dict = None
    ) -> Dict[str, Any]:
        """항공편의 효율성 점수 계산"""

        try:
            if not self.client:
                return await self._get_dummy_efficiency_score(flight_data)

            from app.utils.prompts.efficiency_prompts import EfficiencyPromptBuilder

            prompt_builder = EfficiencyPromptBuilder()
            prompt = prompt_builder.build_efficiency_prompt(flight_data, context)

            response = await self._call_llm(prompt)
            parsed_response = self._parse_efficiency_response(response)

            parsed_response.update(
                {
                    "flight_id": flight_data.get("id", "unknown"),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "model_used": self.model,
                }
            )

            return parsed_response

        except Exception as e:
            logger.error(f"효율성 점수 계산 실패: {str(e)}")
            return self._get_fallback_analysis(flight_data)

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """LLM 호출"""
        try:
            if settings.LLM_PROVIDER == "azure_openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content

            elif settings.LLM_PROVIDER == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            else:
                response = await self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API 호출 실패: {str(e)}")
            raise

    async def _parse_efficiency_response(self, response: str) -> Dict[str, Any]:
        """효율적인 답변 파싱"""
        try:
            if response.strip().startswith("{"):
                parsed = json.loads(response)
                return {
                    "efficiency_score": parsed.get("efficiency_score", 0),
                    "summary": parsed.get("summary", "분석 결과 없음"),
                    "breakdown": parsed.get("breakdown", {}),
                    "recommendations": parsed.get("recommendations", ""),
                }
            else:
                return {
                    "efficiency_score": 75,
                    "summary": response[:200],
                    "breakdown": {},
                    "recommendations": "",
                }

        except json.JSONDecodeError:
            logger.warning("LLM 응답 파싱 실패, 기본값 사용")
        return {
            "efficiency_score": 75,
            "summary": "분석 결과를 파싱할 수 없습니다.",
            "breakdown": {},
            "recommendations": "",
        }

    def _parse_price_response(self, response: str) -> Dict[str, Any]:
        """가격 분석 응답 파싱"""
        try:
            if response.strip().startswith("{"):
                parsed = json.loads(response)
                return {
                    "success": True,
                    "factors": parsed.get("factors", []),
                    "summary": parsed.get("summary", ""),
                    "price_prediction": parsed.get("price_prediction", ""),
                    "booking_advice": parsed.get("booking_advice", ""),
                }
            else:
                return {
                    "success": True,
                    "factors": [],
                    "summary": response[:200],
                    "price_prediction": "",
                    "booking_advice": "",
                }

        except json.JSONDecodeError:
            return {"success": False, "error": "응답 파싱 실패", "factors": [], "summary": ""}
