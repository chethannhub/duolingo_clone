from app.evaluators.base import AnswerEvaluator, EvaluationResult, normalize_answer, primary_accepted_answer


class WordBankEvaluator(AnswerEvaluator):
    def evaluate(self, exercise, answer) -> EvaluationResult:
        option_by_id = {option.id: option for option in exercise.options}
        selected_text = " ".join(
            option_by_id[option_id].option_text
            for option_id in answer.selected_option_ids
            if option_id in option_by_id
        )
        expected_text = " ".join(
            option.option_text
            for option in sorted(
                (option for option in exercise.options if option.correct_order is not None),
                key=lambda item: item.correct_order,
            )
        )
        accepted = {item.normalized_answer for item in exercise.accepted_answers}
        normalized = normalize_answer(selected_text)
        return EvaluationResult(
            normalized == normalize_answer(expected_text) or normalized in accepted,
            primary_accepted_answer(exercise) or expected_text,
        )
