from abc import ABC, abstractmethod

from app import models


def normalize_answer(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


class EvaluationResult:
    def __init__(self, is_correct: bool, correct_answer: str | None = None):
        self.is_correct = is_correct
        self.correct_answer = correct_answer


class AnswerEvaluator(ABC):
    @abstractmethod
    def evaluate(self, exercise: models.Exercise, answer) -> EvaluationResult:
        raise NotImplementedError


def primary_accepted_answer(exercise: models.Exercise) -> str | None:
    primary = next((item.answer_text for item in exercise.accepted_answers if item.is_primary), None)
    return primary or next((item.answer_text for item in exercise.accepted_answers), None)
