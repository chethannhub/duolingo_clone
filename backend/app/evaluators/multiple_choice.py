from app.evaluators.base import AnswerEvaluator, EvaluationResult


class MultipleChoiceEvaluator(AnswerEvaluator):
    def evaluate(self, exercise, answer) -> EvaluationResult:
        selected = next((option for option in exercise.options if option.id == answer.selected_option_id), None)
        correct = next((option for option in exercise.options if option.is_correct), None)
        return EvaluationResult(
            bool(selected and selected.is_correct),
            correct.option_text if correct else None,
        )
