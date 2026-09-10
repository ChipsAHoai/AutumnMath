import copy
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from nicegui import ui


# Load the real application without starting a server.
with patch.object(ui, 'run'):
    application = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'Autumn_Math_NiceGUI.py'))
MathQuizGame = application['MathQuizGame']


class QuizProgressTests(unittest.TestCase):
    def setUp(self):
        self.storage = {}
        self.ui = SimpleNamespace(notify=Mock(), timer=Mock())
        self.globals_patch = patch.dict(MathQuizGame.start.__globals__, {
            'app': SimpleNamespace(storage=SimpleNamespace(user=self.storage)),
            'ui': self.ui,
        })
        self.globals_patch.start()
        self.addCleanup(self.globals_patch.stop)

    def quiz(self, total=3, ops=None):
        return MathQuizGame(total_problems=total, allowed_ops=ops or ['+'], name='test')

    def answer_correctly(self, quiz):
        quiz.input_text = str(quiz.solution)
        quiz.check_answer()

    def test_start_saves_first_question(self):
        quiz = self.quiz()
        quiz.start()
        restored = self.quiz()
        restored.restore_progress(self.storage['test'])
        self.assertEqual(restored.question, quiz.question)
        self.assertEqual(restored.solution, quiz.solution)
        self.assertEqual(restored.start_time, quiz.start_time)

    def test_refresh_during_correct_feedback_advances_once(self):
        quiz = self.quiz()
        quiz.start()
        self.answer_correctly(quiz)
        self.assertTrue(self.storage['test']['answer_pending'])
        restored = self.quiz()
        restored.restore_progress(copy.deepcopy(self.storage['test']))
        self.assertEqual(restored.current_index, 1)
        self.assertFalse(self.storage['test']['answer_pending'])
        restored.advance_problem()
        self.assertEqual(restored.current_index, 1)

    def test_delayed_advance_saves_new_question_and_blocks_double_submit(self):
        quiz = self.quiz()
        quiz.start()
        self.answer_correctly(quiz)
        self.answer_correctly(quiz)
        self.ui.timer.assert_called_once()
        self.ui.timer.call_args.args[1]()
        self.assertEqual(self.storage['test']['current_index'], 1)
        self.assertEqual(self.storage['test']['question'], quiz.question)
        self.assertEqual(self.storage['test']['solution'], str(quiz.solution))

    def test_wrong_answer_is_saved_without_advancing(self):
        quiz = self.quiz()
        quiz.start()
        quiz.input_text = str(quiz.solution + 1)
        quiz.check_answer()
        self.assertEqual(self.storage['test']['wrong'], 1)
        self.assertEqual(self.storage['test']['current_index'], 0)
        self.ui.timer.assert_not_called()

    def test_negative_integer_restores_and_can_be_answered(self):
        quiz = self.quiz(ops=['slope'])
        quiz.restore_progress({
            'solution': '-2', 'symbol': 'slope',
            'question': 'Slope through (0,2) and (1,0) = ? (fraction)',
        })
        self.assertEqual(quiz.solution, -2)
        self.assertEqual(quiz.slope_points, [(0, 2), (1, 0)])
        self.answer_correctly(quiz)
        self.assertTrue(quiz.answer_pending)

    def test_slope_save_restores_same_graph(self):
        quiz = self.quiz(ops=['slope'])
        quiz.start()
        # Mimic storage's JSON round-trip of tuples to lists.
        import json
        saved = json.loads(json.dumps(self.storage['test']))
        restored = self.quiz(ops=['slope'])
        import handlers.slope
        with patch.object(handlers.slope, 'draw_plot') as draw:
            restored.restore_progress(saved)
        draw.assert_called_once_with(restored)
        self.assertEqual(restored.slope_points, saved['slope_points'])
        self.assertEqual(restored.question, quiz.question)
        self.assertEqual(restored.solution, quiz.solution)

    def test_completion_clears_save_and_restart_resets_quiz(self):
        quiz = self.quiz(total=1)
        quiz.start()
        quiz.wrong = 4
        self.answer_correctly(quiz)
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True) as output:
            quiz.advance_problem()
            output.assert_called_once()
        self.assertNotIn('test', self.storage)
        self.assertEqual(quiz.current_index, 1)
        quiz.check_answer()
        self.assertNotIn('test', self.storage)
        quiz.start()
        self.assertEqual(quiz.current_index, 0)
        self.assertEqual(quiz.wrong, 0)
        self.assertEqual(quiz.feedback, '')
        self.assertIsNotNone(quiz.solution)
        self.assertIn('test', self.storage)

    def test_refresh_after_final_answer_finishes_quiz(self):
        quiz = self.quiz(total=1)
        quiz.start()
        self.answer_correctly(quiz)
        restored = self.quiz(total=1)
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
            restored.restore_progress(copy.deepcopy(self.storage['test']))
        self.assertEqual(restored.current_index, 1)
        self.assertNotIn('test', self.storage)
        self.assertIn('Finished!', restored.question)


if __name__ == '__main__':
    unittest.main()
