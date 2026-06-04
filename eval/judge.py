"""Task 27: LLM-as-a-judge — automated quality evaluation pipeline."""
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

EVAL_DATASET = [
    {"question": "Что такое Python?", "expected_keywords": ["программирование", "язык", "интерпретируемый"]},
    {"question": "Объясни принцип работы ООП", "expected_keywords": ["объект", "класс", "наследование", "инкапсуляция"]},
    {"question": "Что такое HTTP?", "expected_keywords": ["протокол", "запрос", "ответ", "веб"]},
    {"question": "Что такое база данных?", "expected_keywords": ["данные", "хранение", "таблица", "SQL"]},
    {"question": "Расскажи о Git", "expected_keywords": ["версия", "коммит", "ветка", "репозиторий"]},
    {"question": "Что такое Docker?", "expected_keywords": ["контейнер", "образ", "виртуализация"]},
    {"question": "Что такое REST API?", "expected_keywords": ["HTTP", "запрос", "JSON", "эндпоинт"]},
    {"question": "Объясни машинное обучение", "expected_keywords": ["данные", "модель", "обучение", "нейронная"]},
    {"question": "Что такое CI/CD?", "expected_keywords": ["интеграция", "доставка", "автоматизация"]},
    {"question": "Казахстан туралы айт", "expected_keywords": ["Қазақстан", "Алматы", "Астана", "республика"]},
]

JUDGE_SYSTEM_PROMPT = """Ты — экспертный оценщик качества ответов AI-ассистента.
Оценивай ответ по трём критериям от 1 до 10:
- accuracy (точность): соответствует ли ответ вопросу?
- relevance (релевантность): насколько ответ по теме?
- no_hallucination (отсутствие галлюцинаций): нет ли ложной информации?

Ответь строго в JSON формате:
{"accuracy": <1-10>, "relevance": <1-10>, "no_hallucination": <1-10>, "comment": "<краткий комментарий>"}
"""


@dataclass
class EvalResult:
    question: str
    answer: str
    accuracy: float
    relevance: float
    no_hallucination: float
    avg_score: float
    comment: str
    error: str = ""


async def evaluate_answer(groq_service, question: str, answer: str) -> dict:
    """Ask judge LLM to score the answer."""
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Вопрос: {question}\n\nОтвет бота: {answer}\n\nОцени ответ:"},
    ]
    try:
        raw = await groq_service.get_simple_response(messages, model=groq_service.settings.complex_model)
        # Extract JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        logger.warning(f"Judge eval error: {e}")
    return {"accuracy": 5, "relevance": 5, "no_hallucination": 5, "comment": "eval error"}


async def run_evaluation(groq_service, questions: Optional[list] = None) -> list[EvalResult]:
    """Run full evaluation pipeline."""
    dataset = questions or EVAL_DATASET
    results = []

    for item in dataset:
        question = item["question"]
        logger.info(f"Evaluating: {question[:50]}")

        # Get bot answer
        answer_chunks = []
        try:
            async for chunk in groq_service.get_ai_stream_response(999999, question):
                answer_chunks.append(chunk)
            bot_answer = answer_chunks[-1] if answer_chunks else ""
        except Exception as e:
            results.append(EvalResult(question, "", 0, 0, 0, 0, "", str(e)))
            continue

        # Judge evaluation
        scores = await evaluate_answer(groq_service, question, bot_answer)
        accuracy = float(scores.get("accuracy", 5))
        relevance = float(scores.get("relevance", 5))
        no_hallucination = float(scores.get("no_hallucination", 5))
        avg = (accuracy + relevance + no_hallucination) / 3

        results.append(EvalResult(
            question=question,
            answer=bot_answer[:200],
            accuracy=accuracy,
            relevance=relevance,
            no_hallucination=no_hallucination,
            avg_score=avg,
            comment=scores.get("comment", ""),
        ))

    return results


def print_report(results: list[EvalResult]) -> float:
    """Print evaluation report and return average score."""
    total = sum(r.avg_score for r in results if not r.error)
    count = sum(1 for r in results if not r.error)
    avg = total / count if count else 0

    print(f"\n{'='*60}")
    print(f"ОТЧЁТ ОЦЕНКИ КАЧЕСТВА БОТА ({count} вопросов)")
    print(f"{'='*60}")
    for r in results:
        status = "❌" if r.error else f"{'✅' if r.avg_score >= 7 else '⚠️'}"
        print(f"{status} {r.question[:45]:<45} avg={r.avg_score:.1f}")
        if r.comment:
            print(f"   └─ {r.comment}")
    print(f"{'='*60}")
    print(f"СРЕДНИЙ БАЛЛ: {avg:.2f}/10")
    print(f"{'='*60}\n")
    return avg


async def regression_check(groq_service, threshold: float = 6.5) -> bool:
    """Task 27: CI regression check — fails if avg score drops below threshold."""
    results = await run_evaluation(groq_service, EVAL_DATASET[:5])
    avg = print_report(results)
    if avg < threshold:
        logger.error(f"REGRESSION: средний балл {avg:.2f} ниже порога {threshold}")
        return False
    logger.info(f"Качество в норме: {avg:.2f} >= {threshold}")
    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from config.settings import settings
    from services.groq_service import GroqService

    async def main():
        svc = GroqService(settings=settings)
        ok = await regression_check(svc)
        sys.exit(0 if ok else 1)

    asyncio.run(main())
