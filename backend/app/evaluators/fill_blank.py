from app.evaluators.base import AnswerEvaluator, EvaluationResult, normalize_answer, primary_accepted_answer


class FillBlankEvaluator(AnswerEvaluator):
    def evaluate(self, exercise, answer) -> EvaluationResult:
        accepted = {item.normalized_answer for item in exercise.accepted_answers}
        return EvaluationResult(
            normalize_answer(answer.text) in accepted,
            primary_accepted_answer(exercise),
        )
