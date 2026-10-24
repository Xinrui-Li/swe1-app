from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Choice, Question


def create_question(question_text, days):
    """Create a question published a given number of days from now."""
    pub_date = timezone.now() + timedelta(days=days)
    return Question.objects.create(
        question_text=question_text,
        pub_date=pub_date,
    )


class QuestionModelTests(TestCase):
    def test_question_str(self):
        question = create_question("Test question", -1)
        self.assertEqual(str(question), "Test question")

    def test_choice_str(self):
        question = create_question("Test question", -1)
        choice = Choice.objects.create(
            question=question,
            choice_text="Test choice",
        )
        self.assertEqual(str(choice), "Test choice")

    def test_was_published_recently_with_recent_question(self):
        question = create_question("Recent question", -1 / 24)
        self.assertTrue(question.was_published_recently())

    def test_was_published_recently_with_old_question(self):
        question = create_question("Old question", -8)
        self.assertFalse(question.was_published_recently())

    def test_was_published_recently_with_future_question(self):
        question = create_question("Future question", 1)
        self.assertFalse(question.was_published_recently())


class IndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse("polls:index"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [],
        )

    def test_questions_are_ordered_by_publication_date(self):
        old_question = create_question("Old question", -2)
        new_question = create_question("New question", -1)

        response = self.client.get(reverse("polls:index"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [new_question, old_question],
        )

    def test_index_displays_only_five_questions(self):
        for i in range(6):
            create_question(f"Question {i}", -i)

        response = self.client.get(reverse("polls:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.context["latest_question_list"]),
            5,
        )


class DetailViewTests(TestCase):
    def test_existing_question(self):
        question = create_question("Test question", -1)

        response = self.client.get(reverse("polls:detail", args=(question.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question"], question)

    def test_nonexistent_question_returns_404(self):
        response = self.client.get(reverse("polls:detail", args=(9999,)))

        self.assertEqual(response.status_code, 404)


class ResultsViewTests(TestCase):
    def test_existing_question(self):
        question = create_question("Test question", -1)

        response = self.client.get(reverse("polls:results", args=(question.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question"], question)

    def test_nonexistent_question_returns_404(self):
        response = self.client.get(reverse("polls:results", args=(9999,)))

        self.assertEqual(response.status_code, 404)


class VoteViewTests(TestCase):
    def setUp(self):
        self.question = create_question("Test question", -1)
        self.choice = Choice.objects.create(
            question=self.question,
            choice_text="First choice",
            votes=0,
        )

    def test_vote_with_valid_choice(self):
        response = self.client.post(
            reverse("polls:vote", args=(self.question.id,)),
            {"choice": self.choice.id},
        )

        self.assertRedirects(
            response,
            reverse("polls:results", args=(self.question.id,)),
        )

        self.choice.refresh_from_db()
        self.assertEqual(self.choice.votes, 1)

    def test_vote_without_selecting_choice(self):
        response = self.client.post(
            reverse("polls:vote", args=(self.question.id,)),
            {},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

    def test_vote_with_invalid_choice(self):
        response = self.client.post(
            reverse("polls:vote", args=(self.question.id,)),
            {"choice": 9999},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You didn&#x27;t select a choice.")

    def test_vote_for_nonexistent_question_returns_404(self):
        response = self.client.post(
            reverse("polls:vote", args=(9999,)),
            {"choice": self.choice.id},
        )

        self.assertEqual(response.status_code, 404)
