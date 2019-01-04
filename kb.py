
import datetime
import random
import os

from sortedcontainers import SortedList

import module
import util


class Answers:
    def __init__(self, match_list, kbis_involved):
        self.sequence = match_list
        self.kbis_involved = kbis_involved
    def accept(self, tentative):
        return Answers.match(util.normalize_caseless(tentative), self.sequence)

    @staticmethod
    def match(str, sequence):
        for possibilities in sequence:
            for possibility in possibilities:
                if str.startswith(util.normalize_caseless(possibility)):
                    if Answers.match(str[len(possibility):], sequence[1:]):
                        return True
        return len(sequence) == 0 and len(str) == 0

    def get_possible_solution(self):
        result = ''
        for possibilities in self.sequence:
            result += random.choice(possibilities)
        return result

class KnowledgeItem:
    repeat_intervals = \
        [datetime.timedelta(minutes=0)\
        ,datetime.timedelta(minutes=0)\
        ,datetime.timedelta(minutes=1)\
        ,datetime.timedelta(minutes=1)\
        ,datetime.timedelta(minutes=10)\
        ,datetime.timedelta(minutes=10)\
        ,datetime.timedelta(hours=1)\
        ,datetime.timedelta(hours=1)\
        ,datetime.timedelta(days=1)\
        ,datetime.timedelta(days=1)\
        ,datetime.timedelta(days=1)\
        ,datetime.timedelta(days=1)\
        ,datetime.timedelta(days=1)\
        ,datetime.timedelta(days=5)\
        ,datetime.timedelta(days=5)\
        ,datetime.timedelta(days=5)\
        ,datetime.timedelta(days=5)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=31)\
        ,datetime.timedelta(days=90)\
        ]

    def __init__(self, translation):
        self.translation = translation
        self.next_revision_datetime = datetime.datetime.now()
        self.times_got_right = 0
        self.hidden = translation.hidden

    def serialize(self):
        return {u'translation': self.translation.serialize(), \
            u'next_revision_datetime': datetime.datetime.strftime(self.next_revision_datetime, "%Y-%m-%d %H:%M:%S"), \
            u'times_got_right': self.times_got_right}

    def deserialize(self, j):
        self.next_revision_datetime = datetime.datetime.strptime(j['next_revision_datetime'], "%Y-%m-%d %H:%M:%S")
        self.times_got_right = j['times_got_right']

    def consolidate(self, step_count):
        self.times_got_right += step_count
        delay_idx = min(self.times_got_right, len(KnowledgeItem.repeat_intervals) - 1)
        self.next_revision_datetime = datetime.datetime.now() + KnowledgeItem.repeat_intervals[delay_idx]


def tags_are_compatible(true_tags, value_tags, kbi_tags):
    if not true_tags.viewitems() <= kbi_tags.viewitems():
        return False
    for k,v in value_tags.iteritems():
        if k in kbi_tags:
            if len(list(set(v) & set(kbi_tags[k]))) == 0:
                return False
    return True


class KnowledgeBase:
    def __init__(self):
        self.lessons_pathnames = set()
        self.knowledge_items = SortedList(key=lambda kbi:kbi.next_revision_datetime)
        self.hidden_knowledge_items = []
    
    def serialize(self):
        return {u'lessons_pathnames': [t for t in self.lessons_pathnames], u'knowledge_items': [kbi.serialize() for kbi in self.knowledge_items]}
    
    def deserialize(self, j, course_pathname):
        self.lessons_pathnames = set(j['lessons_pathnames'])

        all_kbis_by_translation_data = {}
        for lesson_pathname in self.lessons_pathnames:
            module_path = os.path.dirname(lesson_pathname)
            lesson_name = os.path.basename(lesson_pathname)
            kdl = module.all_modules[module_path]
            lesson = kdl.get_lesson(lesson_name)
            if lesson is None:
                util.log("Error finding lesson from name.")
                raise Exception
            for tr in lesson.translations:
                kbi = KnowledgeItem(tr)
                if kbi.hidden:
                    self.hidden_knowledge_items.append(kbi)
                else:
                    all_kbis_by_translation_data[kbi.translation.data] = kbi
            
        for j_kbi in j['knowledge_items']:
            if j_kbi['translation'] in all_kbis_by_translation_data:
                kbi = all_kbis_by_translation_data[j_kbi['translation']]
                try:
                    kbi.deserialize(j_kbi)
                except Exception, e:
                    ok = 1
                self.knowledge_items.add(kbi)

        return self

    def has_lesson(self, pathname):
        return pathname in self.lessons_pathnames

    def add_lesson(self, lesson, pathname, skip):
        if pathname in self.lessons_pathnames:
            return
        self.lessons_pathnames.add(pathname)
        for tr in lesson.translations:
            kbi = KnowledgeItem(tr)
            if kbi.hidden:
                self.hidden_knowledge_items.append(kbi)
            else:
                if skip:
                    kbi.consolidate(10)
                self.knowledge_items.add(kbi)

    def incorporate(self, other):
        self.lessons_pathnames = self.lessons_pathnames.union(other.lessons_pathnames)
        self.knowledge_items.update(other.knowledge_items)
        self.hidden_knowledge_items += other.hidden_knowledge_items

    def get_kbis_to_revise(self):
        return self.knowledge_items

    def get_next_revision_datetime(self):
        return self.knowledge_items[0].next_revision_datetime

    def get_random_kbi_by_tags(self, tags, variables):
        assert(isinstance(tags, set))
        assert(isinstance(variables, dict))

        true_tags = {t:[True] for t in tags if t.find('=') == -1}
        split_tags = [t for t in tags if t.find('=') != -1]
        value_tags = {}
        new_variables = {}
        for t in split_tags:
            parts = t.split('=')
            if len(parts) > 2 or len(parts[0]) == 0 or len(parts[1]) == 0:
                util.log('Malformed tag', t)
                raise Exception
            if parts[1] in variables:
                value_tags[parts[0]] = variables[parts[1]]
            elif len(parts[1]) >= 3 and parts[1][0] == "'" and parts[1][-1] == "'":
                value_tags[parts[0]] = [parts[1][1:-1]]
            else:
                new_variables[parts[0]] = parts[1]

        candidate_kbis = [kbi for kbi in self.hidden_knowledge_items if tags_are_compatible(true_tags, value_tags, kbi.translation.tags)]
        candidate_kbis.extend([kbi for kbi in self.knowledge_items if tags_are_compatible(true_tags, value_tags, kbi.translation.tags)])
        if len(candidate_kbis) == 0:
            return None
        selected_kbi = random.choice(candidate_kbis)

        # set variables
        for k,v in new_variables.iteritems():
            if v in selected_kbi.translation.tags:
                if k not in variables:
                    variables[k] = []
                variables[k].extend(selected_kbi.translation.tags[v])

        return selected_kbi

    def get_question_from_kbi(self, kbi):
        initial_question = random.choice(kbi.translation.natives)
        question_str = initial_question
        question_parts = []
        answer_matches = []
        idx = question_str.find('[')
        tag_values = {}
        kbis_involved = set()
        kbis_involved.add(kbi)
        while idx != -1:
            if idx > 0:
                question_parts.append(question_str[:idx])
            question_str = question_str[idx+1:]
            idx = question_str.find(']')
            if idx == -1:
                util.log(u"Malformed input, missing ']'. Aborting.")
                util.log(initial_question)
                raise Exception()

            tags = question_str[:idx]
            tags = {t.strip() for t in tags.split('@') if len(t.strip()) > 0} # set comprehension
            selected_kbi = self.get_random_kbi_by_tags(tags, tag_values)
            if selected_kbi is None:
                util.log(u'No matching knowledge base item for', question_str, ', tags:', tags, ', tag_values:', tag_values)
                return None, None

            kbis_involved.add(selected_kbi)
            question_parts.append(random.choice(selected_kbi.translation.natives))
            answer_matches.append(selected_kbi.translation.targets)

            question_str = question_str[idx+1:]
            idx = question_str.find('[')
        if len(question_str) > 0:
            question_parts.append(question_str)

        initial_answer = random.choice(kbi.translation.targets)
        answer_str = initial_answer
        answer_parts = []
        idx = answer_str.find('[')
        while idx != -1:
            if idx > 0:
                answer_parts.append([answer_str[:idx]])
            answer_str = answer_str[idx+1:]
            idx = answer_str.find(']')
            if idx == -1:
                util.log(u"Malformed input, missing ']'. Aborting.")
                util.log(initial_answer)
                raise Exception()
            answer_idx = int(answer_str[:idx])
            answer_parts.append(answer_matches[answer_idx])

            answer_str = answer_str[idx+1:]
            idx = answer_str.find('[')
        if len(answer_str) > 0:
            answer_parts.append([answer_str])

        return ''.join(question_parts), Answers(answer_parts, kbis_involved)