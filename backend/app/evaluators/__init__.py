from app.evaluators.fill_blank import FillBlankEvaluator
from app.evaluators.match_pairs import MatchPairsEvaluator
from app.evaluators.multiple_choice import MultipleChoiceEvaluator
from app.evaluators.type_answer import TypeAnswerEvaluator
from app.evaluators.word_bank import WordBankEvaluator


EVALUATORS = {
    "multiple_choice": MultipleChoiceEvaluator(),
    "translate_word_bank": WordBankEvaluator(),
    "match_pairs": MatchPairsEvaluator(),
    "fill_blank": FillBlankEvaluator(),
    "type_answer": TypeAnswerEvaluator(),
}
