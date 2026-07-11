from app.evaluators.base import AnswerEvaluator, EvaluationResult


class MatchPairsEvaluator(AnswerEvaluator):
    def evaluate(self, exercise, answer) -> EvaluationResult:
        pair_by_left = {f"left-{pair.id}": f"right-{pair.id}" for pair in exercise.match_pairs}
        submitted = {match.left_id: match.right_id for match in answer.matches}
        correct_answer = ", ".join(f"{pair.left_text} = {pair.right_text}" for pair in exercise.match_pairs)
        return EvaluationResult(submitted == pair_by_left, correct_answer)
