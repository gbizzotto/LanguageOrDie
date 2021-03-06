
import datetime
import random
import os

from sortedcontainers import SortedList

import kodule
import util


class Answers:
    def __init__(self, match_list):
        self.sequence = match_list
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
    time_interval = datetime.timedelta(minutes=1)

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
        self.next_revision_datetime = d = datetime.datetime.strptime(j['next_revision_datetime'], "%Y-%m-%d %H:%M:%S")
        self.times_got_right = j['times_got_right']

    def consolidate(self, step_count):
        self.times_got_right += step_count
        self.next_revision_datetime = datetime.datetime.now() + KnowledgeItem.time_interval * (3**self.times_got_right - 1)

class KnowledgeBase:
    def __init__(self):
        self.kessons_pathnames = set()
        self.knowledge_items = SortedList(key=lambda kbi:kbi.next_revision_datetime)
        self.hidden_knowledge_items = []
    
    def serialize(self):
        return {u'kessons_pathnames': [t for t in self.kessons_pathnames], u'knowledge_items': [kbi.serialize() for kbi in self.knowledge_items]}
    
    def deserialize(self, j, kourse_pathname):
        self.kessons_pathnames = set(j['kessons_pathnames'])

        all_kbis_by_translation_data = {}
        for kesson_pathname in self.kessons_pathnames:
            kodule_path = os.path.dirname(kesson_pathname)
            kesson_name = os.path.basename(kesson_pathname)
            kdl = kodule.all_kodules[kodule_path]
            kesson = kdl.get_kesson(kesson_name)
            if kesson is None:
                print "Error finding kesson from name."
                raise Exception
            for tr in kesson.translations:
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

    def has_kesson(self, pathname):
        return pathname in self.kessons_pathnames

    def add_kesson(self, kesson, pathname, skip):
        if pathname in self.kessons_pathnames:
            return
        self.kessons_pathnames.add(pathname)
        for tr in kesson.translations:
            kbi = KnowledgeItem(tr)
            if kbi.hidden:
                self.hidden_knowledge_items.append(kbi)
            else:
                if skip:
                    kbi.consolidate(10)
                self.knowledge_items.add(kbi)

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
                print 'Malformed tag', t
                raise Exception
            if parts[1] in variables:
                value_tags[parts[0]] = variables[parts[1]]
            else:
                new_variables[parts[0]] = parts[1]

        candidate_kbis = [kbi for kbi in self.hidden_knowledge_items \
            if true_tags.viewitems() <= kbi.translation.tags.viewitems() \
            and value_tags.viewitems() <= kbi.translation.tags.viewitems() ]
        candidate_kbis.extend([kbi for kbi in self.knowledge_items \
            if true_tags.viewitems() <= kbi.translation.tags.viewitems() \
            and value_tags.viewitems() <= kbi.translation.tags.viewitems() ])
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
        while idx != -1:
            if idx > 0:
                question_parts.append(question_str[:idx])
            question_str = question_str[idx+1:]
            idx = question_str.find(']')
            if idx == -1:
                print u"Malformed input, missing ']'. Aborting."
                print initial_question
                raise Exception()

            tags = question_str[:idx]
            tags = {t.strip() for t in tags.split('@') if len(t.strip()) > 0} # set comprehension
            selected_kbi = self.get_random_kbi_by_tags(tags, tag_values)

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
                print u"Malformed input, missing ']'. Aborting."
                print initial_answer
                raise Exception()
            answer_idx = int(answer_str[:idx])
            answer_parts.append(answer_matches[answer_idx])

            answer_str = answer_str[idx+1:]
            idx = answer_str.find('[')
        if len(answer_str) > 0:
            answer_parts.append([answer_str])

        return ''.join(question_parts), Answers(answer_parts)