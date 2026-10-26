import copy
import json
import math
import os
from pathlib import Path
import runpy
import tempfile
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


class KidFriendlyHelperTests(unittest.TestCase):
    def test_star_rating(self):
        star_rating = application['star_rating']
        self.assertEqual([star_rating(w) for w in (0, 1, 3, 4, 10)], [3, 2, 2, 1, 1])

    def test_format_duration(self):
        format_duration = application['format_duration']
        self.assertEqual(format_duration(42.4), '42s')
        self.assertEqual(format_duration(125), '2m 05s')
        self.assertEqual(format_duration(218943.52), '60h 49m')


class QuizProgressTests(unittest.TestCase):
    def setUp(self):
        self.storage = {}
        self.ui = SimpleNamespace(notify=Mock(), timer=Mock())
        stats_dir = tempfile.TemporaryDirectory()
        self.addCleanup(stats_dir.cleanup)
        self.stats_path = Path(stats_dir.name) / 'data' / 'stats.json'
        self.globals_patch = patch.dict(MathQuizGame.start.__globals__, {
            'app': SimpleNamespace(storage=SimpleNamespace(user=self.storage)),
            'ui': self.ui,
            'STATS_PATH': self.stats_path,
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
                    with patch('handlers.common_multiples.random.randint', side_effect=[a, b]), \
                            patch('handlers.common_multiples.random.random', return_value=0):
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

    def test_picture_hint_appears_after_miss_and_survives_refresh(self):
        quiz = self.quiz(ops=['*'])
        quiz.start()
        self.assertEqual(quiz.hint['kind'], 'dots')
        self.assertEqual(quiz.hint_level, 0)
        quiz.input_text = str(quiz.solution + 1)
        quiz.check_answer()
        self.assertEqual(quiz.hint_level, 1)
        restored = self.quiz(ops=['*'])
        restored.restore_progress(copy.deepcopy(self.storage['test']))
        self.assertEqual(restored.hint, quiz.hint)
        self.assertEqual(restored.hint_level, 1)
        self.answer_correctly(restored)
        restored.advance_problem()
        self.assertEqual(restored.hint_level, 0)
        # Saves from before stepped hints stored a yes/no flag.
        old = self.quiz(ops=['*'])
        old.restore_progress({'question': '3 × 5 = ?', 'solution': '15', 'symbol': '*', 'hint_shown': True})
        self.assertEqual(old.hint_level, 1)

    def test_saves_from_before_hints_get_a_picture(self):
        import handlers.common_multiples as common
        cases = [('+', '47 + 25 = ?', {'kind': 'blocks', 'a': 47, 'b': 25, 'op': '+'}),
                 ('-', '75 - 56 = ?', {'kind': 'blocks', 'a': 75, 'b': 56, 'op': '-'}),
                 ('*', '3 × 5 = ?', {'kind': 'dots', 'a': 3, 'b': 5})]
        for op, stories in (('lcm', common.LCM_STORIES), ('gcf', common.GCF_STORIES)):
            for story in stories:
                cases.append((op, story.format(a=96, b=72), {'kind': 'venn', 'a': 96, 'b': 72}))
                for follow_up in common.make_follow_ups(op, story, 96, 72):
                    cases.append((op, follow_up['question'], {'kind': 'venn', 'a': 96, 'b': 72}))
        for op, question, hint in cases:
            with self.subTest(question=question):
                quiz = self.quiz(ops=[op])
                quiz.restore_progress({'question': question, 'solution': '1', 'symbol': op,
                                       'follow_up_questions': [{'question': 'next', 'solution': 1}]})
                self.assertEqual(quiz.hint, hint)

    def test_common_factor_of_one_is_rare(self):
        import handlers.common_multiples as common
        with patch.object(common.random, 'randint', side_effect=[97, 100, 12, 18]), \
                patch.object(common.random, 'random', return_value=0.5):
            self.assertEqual(common.pick_pair(), (12, 18))
        with patch.object(common.random, 'randint', side_effect=[97, 100]), \
                patch.object(common.random, 'random', return_value=0.05):
            self.assertEqual(common.pick_pair(), (97, 100))
        ones = sum(math.gcd(*common.pick_pair()) == 1 for _ in range(2000))
        self.assertLess(ones, 2000 * 0.2)

    def test_show_me_button_reveals_each_kind_of_picture(self):
        import handlers.visuals
        for op, kind in (('+', 'blocks'), ('-', 'blocks'), ('*', 'dots'), ('lcm', 'venn'), ('gcf', 'venn')):
            with self.subTest(op=op):
                quiz = self.quiz(ops=[op])
                quiz.start()
                quiz.show_hint()
                self.assertEqual(quiz.hint_level, 1)
                self.assertEqual(quiz.hint['kind'], kind)
                self.assertIn('<svg', handlers.visuals.build_svg(quiz.hint))

    def test_percent_word_problems_ask_for_the_part_then_the_total(self):
        import handlers.percent as percent
        expected = {  # story index: (part, total) for $48 at the given percent
            0: (15, '7.20', '40.80'), 1: (6, '2.88', '50.88'), 2: (12, '5.76', '53.76'),
            3: (25, '12', '36'), 4: (3, '1.44', '49.44'),
        }
        for index, (pct, part, total) in expected.items():
            story = percent.PART_STORIES[index]
            with self.subTest(story=story[0]):
                quiz = self.quiz(total=1, ops=['percent'])
                with patch.object(percent.random, 'random', return_value=0.9), \
                        patch.object(percent.random, 'choice', side_effect=['percent', story, pct]), \
                        patch.object(percent.random, 'randint', return_value=48):
                    quiz.start()
                self.assertIn('$48', quiz.question)
                self.assertEqual(quiz.hint_level, 0)
                quiz.input_text = f'${part}'
                quiz.check_answer()
                self.assertTrue(quiz.answer_pending)
                quiz.advance_problem()
                self.assertIn(f'is ${part}', quiz.question)
                # A refresh mid-problem keeps the follow-up.
                restored = self.quiz(total=1, ops=['percent'])
                restored.restore_progress(copy.deepcopy(self.storage['test']))
                restored.input_text = total
                with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
                    restored.check_answer()
                    restored.advance_problem()
                self.assertIn('Finished!', restored.question)

    def test_percent_word_problems_can_ask_for_the_percent(self):
        import handlers.percent as percent
        quiz = self.quiz(ops=['percent'])
        with patch.object(percent.random, 'random', return_value=0.1), \
                patch.object(percent.random, 'choice', side_effect=['percent', percent.FIND_PERCENT_STORIES[0], 25]), \
                patch.object(percent.random, 'randint', return_value=3):
            quiz.start()
        self.assertIn('$60', quiz.question)
        self.assertIn('$15 off', quiz.question)
        self.assertEqual(quiz.follow_up_questions, [])
        quiz.input_text = '25%'
        quiz.check_answer()
        self.assertTrue(quiz.answer_pending)

    def test_percent_hints_never_say_the_answer(self):
        import re
        import xml.dom.minidom
        import handlers.percent as percent
        import handlers.visuals as visuals
        for _ in range(300):
            quiz = SimpleNamespace(clear_plot=lambda: None, follow_up_questions=[])
            percent.generate(quiz)
            for step in (1, 2):
                svg = visuals.build_svg(quiz.hint, step)
                xml.dom.minidom.parseString(svg)
                texts = re.findall(r'>([^<]+)</text>', svg)
                if 'pct' in quiz.hint:
                    answers = {percent.money(quiz.solution), percent.money(quiz.follow_up_questions[0]['solution'])}
                    self.assertFalse([t for t in texts if t.split(' = ')[-1] in answers], (texts, answers))
                else:
                    self.assertFalse([t for t in texts if f'{quiz.solution}%' in t and t != '100%'], texts)
                    self.assertNotIn('<line', svg)

    def test_venn_hints_reveal_one_step_at_a_time(self):
        import handlers.visuals as visuals
        quiz = self.quiz(ops=['gcf'])
        quiz.start()
        a, b = quiz.hint['a'], quiz.hint['b']
        factored = visuals._factorization(a)
        steps = []
        for _ in range(4):
            quiz.input_text = '0'
            quiz.check_answer()
            steps.append(visuals.build_svg(quiz.hint, quiz.hint_level))
        self.assertEqual(quiz.hint_level, 3)
        self.assertIn('Step 1', steps[0])
        self.assertNotIn(factored, steps[0])
        self.assertIn(factored, steps[1])
        self.assertNotIn('GCF: multiply', steps[1])
        self.assertIn('GCF: multiply', steps[2])
        self.assertEqual(steps[2], steps[3])

    def test_venn_hint_puts_shared_factors_in_the_middle(self):
        import handlers.visuals as visuals
        self.assertEqual(visuals.prime_factors(96), [2, 2, 2, 2, 2, 3])
        svg = visuals.factor_venn_svg(64, 81)
        self.assertIn('only 1', svg)

    def test_battle_misses_cost_two_hearts_and_hints_cost_one(self):
        quiz = self.quiz(ops=['lcm'])
        quiz.start()
        self.assertEqual(quiz.life, 10)
        self.assertEqual(quiz.enemy_hp, 3)  # the story plus two follow-ups
        quiz.show_hint()
        self.assertEqual((quiz.life, quiz.hint_level), (9, 1))
        quiz.input_text = '0'
        quiz.check_answer()
        # The miss costs 2; the hint step it opens is free.
        self.assertEqual((quiz.life, quiz.hint_level), (7, 2))
        quiz.show_hint()
        quiz.show_hint()  # already at the last hint step: no charge
        self.assertEqual((quiz.life, quiz.hint_level), (6, 3))
        restored = self.quiz(ops=['lcm'])
        restored.restore_progress(copy.deepcopy(self.storage['test']))
        self.assertEqual((restored.life, restored.enemy, restored.enemy_hp), (6, quiz.enemy, 3))

    def test_correct_answers_hit_the_enemy_until_it_is_beaten(self):
        quiz = self.gift_bag_quiz()
        enemy = quiz.enemy
        for hp_left in (2, 1, 0):
            self.answer_correctly(quiz)
            self.assertEqual(quiz.enemy, enemy)  # the same enemy through the follow-ups
            self.assertEqual(quiz.enemy_hp, hp_left)
            with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
                quiz.advance_problem()
        self.assertEqual(quiz.defeated, 1)
        self.assertEqual(quiz.life, 10)

    def test_running_out_of_hearts_is_game_over(self):
        quiz = self.quiz(total=15, ops=['*'])
        quiz.start()
        quiz.end_card = SimpleNamespace(visible=False)
        quiz.end_title_label, quiz.end_avatar_label, quiz.end_stars_label = Mock(), Mock(), Mock()
        quiz.end_details_label, quiz.end_message_label = Mock(), Mock()
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True) as scores:
            for _ in range(5):
                quiz.input_text = str(quiz.solution + 1)
                quiz.check_answer()
            scores.assert_called_once()
        self.assertEqual(quiz.life, 0)
        self.assertIn('Game over', quiz.question)
        self.assertTrue(quiz.end_card.visible)
        quiz.end_title_label.set_text.assert_called_with('💀 Game over!')
        self.assertNotIn('test', self.storage)
        # No more answers or hints once the game is over.
        quiz.input_text = '1'
        quiz.check_answer()
        quiz.show_hint()
        self.assertEqual((quiz.wrong, quiz.life), (5, 0))
        quiz.start()
        self.assertEqual((quiz.life, quiz.wrong, quiz.current_index), (10, 0, 0))
        self.assertFalse(quiz.end_card.visible)

    def win_quiz(self, quiz=None):
        quiz = quiz or self.quiz(total=1, ops=['*'])
        quiz.start()
        self.answer_correctly(quiz)
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
            quiz.advance_problem()
        return quiz

    def test_seven_wins_earn_a_treat(self):
        record = MathQuizGame.start.__globals__['record_result']
        for win in range(1, 7):
            self.win_quiz()
            self.assertEqual(MathQuizGame.start.__globals__['kid_stats']('test')['streak'], win)
        quiz = self.quiz(total=1, ops=['*'])
        quiz.end_card = SimpleNamespace(visible=False)
        quiz.end_title_label, quiz.end_avatar_label, quiz.end_stars_label = Mock(), Mock(), Mock()
        quiz.end_details_label, quiz.end_message_label = Mock(), Mock()
        self.win_quiz(quiz)
        quiz.end_title_label.set_text.assert_called_with('🎁 FREE TREAT! 🎁')
        stats = json.loads(self.stats_path.read_text())['test']
        self.assertEqual((stats['wins'], stats['streak'], stats['treats']), (7, 0, 1))
        # The next treat needs another 7 wins.
        self.assertFalse(record('test', won=True)['treat'])

    def test_treat_sends_one_email(self):
        import notify
        sent = []
        with patch.object(notify, 'send_in_background', side_effect=lambda subject, body: sent.append(subject)):
            for _ in range(7):
                self.win_quiz()
        self.assertEqual(sent, ['🎁 Test earned free treat #1!'])

    def test_email_uses_gmail_settings_and_is_skipped_when_not_set(self):
        import notify
        with patch.dict(os.environ, {}, clear=True), patch.object(notify.smtplib, 'SMTP') as smtp:
            self.assertFalse(notify.send_email('hi', 'there'))
            smtp.assert_not_called()
        settings = {'NOTIFY_EMAIL_TO': 'parent@example.com', 'SMTP_USER': 'me@gmail.com', 'SMTP_PASSWORD': 'app-pass'}
        with patch.dict(os.environ, settings, clear=True), patch.object(notify.smtplib, 'SMTP') as smtp:
            self.assertTrue(notify.send_email('🎁 Treat!', 'body'))
            smtp.assert_called_once_with('smtp.gmail.com', 587, timeout=20)
            server = smtp.return_value.__enter__.return_value
            server.login.assert_called_once_with('me@gmail.com', 'app-pass')
            message = server.send_message.call_args.args[0]
            self.assertEqual((message['To'], message['Subject']), ('parent@example.com', '🎁 Treat!'))

    def test_game_over_keeps_wins_toward_a_treat(self):
        for _ in range(3):
            self.win_quiz()
        quiz = self.quiz(total=15, ops=['*'])
        quiz.start()
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
            for _ in range(5):
                quiz.input_text = str(quiz.solution + 1)
                quiz.check_answer()
        stats = json.loads(self.stats_path.read_text())['test']
        self.assertEqual((stats['wins'], stats['streak'], stats['games_over']), (3, 3, 1))
        for _ in range(4):
            self.win_quiz()
        stats = json.loads(self.stats_path.read_text())['test']
        self.assertEqual((stats['wins'], stats['streak'], stats['treats']), (7, 0, 1))

    def test_treat_progress_banner(self):
        progress = MathQuizGame.start.__globals__['treat_progress']
        self.assertEqual(progress({'streak': 3}), '3 of 7 wins · 4 more to the castle 🎁')
        import xml.dom.minidom
        road = MathQuizGame.start.__globals__['castle_road_svg']
        for wins in range(7):
            svg = road(wins, '🦄')
            xml.dom.minidom.parseString(svg)
            self.assertEqual(svg.count('fill="#facc15"'), wins)  # one gold stone per win

    def test_finishing_shows_end_card_with_stars(self):
        quiz = self.quiz(total=1)
        quiz.end_card = SimpleNamespace(visible=False)
        quiz.end_avatar_label, quiz.end_stars_label, quiz.end_details_label, quiz.end_message_label = (
            Mock() for _ in range(4))
        quiz.start()
        quiz.wrong = 2
        self.answer_correctly(quiz)
        with patch.object(os, 'makedirs'), patch('builtins.open', create=True):
            quiz.advance_problem()
        self.assertTrue(quiz.end_card.visible)
        quiz.end_stars_label.set_text.assert_called_once_with('⭐⭐')
        quiz.start()
        self.assertFalse(quiz.end_card.visible)

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
