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


class HtmlCompatibilityTests(unittest.TestCase):
    def test_svg_container_supports_both_html_signatures(self):
        create = application['create_svg_container']
        element = Mock()
        element.classes.return_value = element

        def legacy_html(content=''):
            self.assertEqual(content, '')
            return element

        def modern_html(content='', *, sanitize):
            self.assertEqual(content, '')
            self.assertIs(sanitize, False)
            return element

        for html in (legacy_html, modern_html):
            with self.subTest(html=html.__name__), patch.dict(create.__globals__, {'ui': SimpleNamespace(html=html)}):
                self.assertIs(create(), element)

    def test_svg_container_with_installed_nicegui(self):
        element = application['create_svg_container']()
        self.addCleanup(element.delete)
        element.set_content('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        self.assertIn('<svg', element.content)


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

    def test_keyboard_entry_editing_and_submit(self):
        quiz = self.quiz()
        quiz.start()
        quiz.answer_label = Mock()
        key = application['handle_quiz_key']
        for char in '-12/3.5':
            key(quiz, char)
        self.assertEqual(quiz.input_text, '-12/3.5')
        key(quiz, 'Backspace')
        self.assertEqual(quiz.input_text, '-12/3.')
        quiz.answer_label.set_value.assert_called_with('-12/3.')
        key(quiz, 'Escape')
        self.assertEqual(quiz.input_text, '')
        key(quiz, 'Enter')
        self.assertEqual(quiz.wrong, 0)
        for char in str(quiz.solution):
            key(quiz, char)
        key(quiz, 'Enter')
        self.assertTrue(quiz.answer_pending)
        key(quiz, '9')
        self.assertEqual(quiz.input_text, '')
        self.ui.timer.assert_called_once()

    def test_keyboard_ignores_shortcuts_repeats_and_keyup(self):
        quiz = self.quiz()
        quiz.start()
        for keydown, repeat, modifier in ((False, False, None), (True, True, None),
                                         (True, False, 'ctrl'), (True, False, 'meta'), (True, False, 'alt')):
            event = SimpleNamespace(
                action=SimpleNamespace(keydown=keydown, repeat=repeat),
                modifiers=SimpleNamespace(ctrl=modifier == 'ctrl', meta=modifier == 'meta', alt=modifier == 'alt'),
                key=SimpleNamespace(name='1'),
            )
            application['handle_keyboard_event'](quiz, event)
        self.assertEqual(quiz.input_text, '')

    def test_keyboard_ignores_input_before_start_and_after_completion(self):
        quiz = self.quiz()
        application['handle_quiz_key'](quiz, '1')
        self.assertEqual(quiz.input_text, '')
        quiz.start()
        quiz.current_index = quiz.total_problems
        application['handle_quiz_key'](quiz, '1')
        self.assertEqual(quiz.input_text, '')

    def test_native_answer_input_binding_focus_and_keypad(self):
        quiz = self.quiz()
        field = ui.input('Your answer').bind_value(quiz, 'input_text')
        quiz.answer_label = field
        self.addCleanup(field.delete)
        with patch.object(field, 'run_method') as run_method:
            quiz.start()
            self.assertTrue(field.enabled)
            run_method.assert_called_with('focus')
            # Native input changes and keypad changes share the same answer.
            field.set_value('12')
            self.assertEqual(quiz.input_text, '12')
            application['add_char'](quiz, '3')
            self.assertEqual(field.value, '123')
            application['clear_input'](quiz)
            self.assertEqual(field.value, '')
            field.set_value(str(quiz.solution))
            application['handle_quiz_key'](quiz, 'Enter')
            self.assertTrue(quiz.answer_pending)
            self.assertFalse(field.enabled)
            quiz.advance_problem()
            self.assertTrue(field.enabled)
            self.assertEqual(field.value, '')
            run_method.assert_called_with('focus')

    def test_start_saves_first_question(self):
        quiz = self.quiz()
        quiz.start()
        restored = self.quiz()
        restored.restore_progress(self.storage['test'])
        self.assertEqual(restored.question, quiz.question)
        self.assertEqual(restored.solution, quiz.solution)
        self.assertEqual(restored.start_time, quiz.start_time)

    def test_lcm_and_gcf_can_be_restored_and_answered(self):
        for op in ('lcm', 'gcf'):
            for a, b, lcm, gcf in ((12, 18, 36, 6), (10, 100, 100, 10), (97, 100, 9700, 1), (10, 10, 10, 10)):
                with self.subTest(op=op, a=a, b=b):
                    expected = lcm if op == 'lcm' else gcf
                    quiz = self.quiz(ops=[op])
                    with patch('handlers.common_multiples.random.randint', side_effect=[a, b]):
                        quiz.start()
                    self.assertEqual(quiz.solution, expected)
                    self.assertIn(str(a), quiz.question)
                    self.assertIn(str(b), quiz.question)
                    restored = self.quiz(ops=[op])
                    restored.restore_progress(self.storage['test'])
                    self.assertEqual(restored.question, quiz.question)
                    # Reject a non-least multiple or a non-greatest common factor.
                    restored.input_text = str(expected * 2 if op == 'lcm' else (1 if expected > 1 else 2))
                    restored.check_answer()
                    self.assertFalse(restored.answer_pending)
                    self.assertEqual(restored.wrong, 1)
                    self.answer_correctly(restored)
                    self.assertTrue(restored.answer_pending)

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

    def gift_bag_quiz(self):
        import handlers.common_multiples as common
        quiz = self.quiz(total=1, ops=['gcf'])
        with patch.object(common, 'GCF_STORIES', (common.GCF_STORIES[0],)), \
                patch.object(common.random, 'randint', side_effect=[20, 42]):
            quiz.start()
        return quiz

    def test_every_story_has_follow_ups_and_finishes_after_refresh(self):
        import handlers.common_multiples as common
        for op, stories, answers in (
            ('lcm', common.LCM_STORIES, (420, 21, 10)),
            ('gcf', common.GCF_STORIES, (2, 10, 21)),
        ):
            for story in stories:
                with self.subTest(op=op, story=story):
                    quiz = self.quiz(total=1, ops=[op])
                    with patch.object(common.random, 'choice', side_effect=[op, story]), \
                            patch.object(common.random, 'randint', side_effect=[20, 42]):
                        quiz.start()
                    self.assertEqual(len(quiz.follow_up_questions), 2)
                    for answer in answers:
                        self.assertEqual(quiz.solution, answer)
                        self.assertEqual(quiz.current_index, 0)
                        self.answer_correctly(quiz)
                        restored = self.quiz(total=1, ops=[op])
                        with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
                            restored.restore_progress(copy.deepcopy(self.storage['test']))
                        quiz = restored
                    self.assertEqual(quiz.current_index, 1)
                    self.assertIn('Finished!', quiz.question)
                    self.assertNotIn('test', self.storage)

    def test_old_saved_stories_get_follow_ups(self):
        import handlers.common_multiples as common
        for op, stories, answer, follow_answers in (
            ('lcm', common.LCM_STORIES, 288, [3, 4]),
            ('gcf', common.GCF_STORIES, 24, [4, 3]),
        ):
            for story in stories:
                for pending in (False, True):
                    with self.subTest(op=op, story=story, pending=pending):
                        quiz = self.quiz(ops=[op])
                        quiz.restore_progress({
                            'question': story.format(a=96, b=72),
                            'solution': str(answer), 'symbol': op,
                            'follow_up_questions': [], 'answer_pending': pending,
                        })
                        if pending:
                            self.assertEqual(quiz.solution, follow_answers[0])
                            self.assertEqual(len(quiz.follow_up_questions), 1)
                        else:
                            self.assertEqual([q['solution'] for q in quiz.follow_up_questions], follow_answers)
                        self.assertEqual(quiz.current_index, 0)

    def test_gift_bag_follow_ups_count_as_one_problem(self):
        quiz = self.gift_bag_quiz()
        for answer, text in ((2, 'greatest number of bags'), (10, 'How many pencils'), (21, 'How many erasers')):
            self.assertEqual(quiz.solution, answer)
            self.assertIn(text, quiz.question)
            self.assertEqual(quiz.current_index, 0)
            self.answer_correctly(quiz)
            with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
                quiz.advance_problem()
        self.assertEqual(quiz.current_index, 1)
        self.assertIn('Finished!', quiz.question)
        self.assertNotIn('test', self.storage)

    def test_follow_ups_survive_refresh_before_and_after_advance(self):
        import json
        quiz = self.gift_bag_quiz()
        self.answer_correctly(quiz)
        restored = self.quiz(total=1, ops=['gcf'])
        restored.restore_progress(json.loads(json.dumps(self.storage['test'])))
        self.assertEqual(restored.solution, 10)
        self.assertEqual(restored.current_index, 0)
        again = self.quiz(total=1, ops=['gcf'])
        again.restore_progress(json.loads(json.dumps(self.storage['test'])))
        self.assertEqual(again.question, restored.question)
        again.input_text = '11'
        again.check_answer()
        self.assertEqual(again.wrong, 1)
        self.assertEqual(again.solution, 10)
        self.answer_correctly(again)
        again.advance_problem()
        self.assertEqual(again.solution, 21)
        self.assertEqual(again.current_index, 0)

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
