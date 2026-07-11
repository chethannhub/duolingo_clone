import os
import tempfile
import unittest
import uuid

database_file = tempfile.NamedTemporaryFile(delete=False)
database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{database_file.name}"

from app import models
from app.api.dependencies import get_current_learner
from app.database import SessionLocal
from app.evaluators.multiple_choice import MultipleChoiceEvaluator
from app.seed import seed_database
from app.services import v1_learning_service as service
from app.v1_schemas import SubmitAnswerRequest


class V1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(reset=True)

    def setUp(self):
        self.db = SessionLocal()
        self.learner = get_current_learner(self.db)

    def tearDown(self):
        self.db.close()

    def test_lesson_starts_with_eight_safe_exercises(self):
        response = service.start_lesson_attempt(
            self.db,
            self.learner,
            1,
            "standard",
            str(uuid.uuid4()),
        )

        attempt = service.get_attempt_by_token(self.db, self.learner, response["attemptToken"])
        self.assertEqual(attempt.total_exercises, 8)
        exercise = response["currentExercise"]
        self.assertNotIn("correct_order", str(exercise))
        self.assertNotIn("accepted_answers", str(exercise))
        self.assertNotIn("normalized_answer", str(exercise))

    def test_multiple_choice_evaluator_uses_server_truth(self):
        exercise = (
            self.db.query(models.Exercise)
            .filter(models.Exercise.exercise_type == "multiple_choice")
            .first()
        )
        correct = next(option for option in exercise.options if option.is_correct)
        payload = type("Answer", (), {"selected_option_id": correct.id})()

        result = MultipleChoiceEvaluator().evaluate(exercise, payload)

        self.assertTrue(result.is_correct)

    def test_duplicate_answer_does_not_deduct_another_heart(self):
        start = service.start_lesson_attempt(
            self.db,
            self.learner,
            1,
            "standard",
            str(uuid.uuid4()),
        )
        payload = SubmitAnswerRequest(
            exercise_id=start["currentExercise"]["id"],
            client_submission_id=str(uuid.uuid4()),
            response_time_ms=100,
            answer={"type": "match_pairs", "matches": []},
        )

        first = service.submit_answer(self.db, self.learner, start["attemptToken"], payload, str(uuid.uuid4()))
        hearts_after_first = first["currentHearts"]
        second = service.submit_answer(self.db, self.learner, start["attemptToken"], payload, str(uuid.uuid4()))

        self.assertEqual(second["learner"]["hearts"], hearts_after_first)

    def test_learning_path_has_reward_states(self):
        path = service.learning_path(self.db, self.learner)
        reward_items = [
            item
            for section in path["sections"]
            for unit in section["units"]
            for item in unit["pathItems"]
            if item["type"] == "reward"
        ]

        self.assertTrue(reward_items)
        self.assertIn(reward_items[0]["state"], {"locked", "claimable", "claimed"})


if __name__ == "__main__":
    unittest.main()
