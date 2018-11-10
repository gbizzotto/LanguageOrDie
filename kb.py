
import datetime
import random

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
        return len(sequence) == 0


class KnowledgeItem:
    time_interval = datetime.timedelta(minutes=1)

    def __init__(self, translation):
        self.translation = translation
        self.next_revision_time = datetime.datetime.now()
        self.times_got_right = 0

    def got_it_right_on_1st_try(self):
        self.times_got_right += 1
        self.next_revision_time = datetime.datetime.now() + KnowledgeItem.time_interval * (3**self.times_got_right - 1)

    def got_it_right_eventually(self):
        self.next_revision_time = datetime.datetime.now() + KnowledgeItem.time_interval * (3**self.times_got_right - 1)

class KnowledgeBase:
    def __init__(self):
        self.kessons_titles = set()
        self.knowledge_items = SortedList(key=lambda kbi:kbi.next_revision_time)
        self.knowledge_items_by_tag = {}
    
    def has_kesson(self, kesson):
        return kesson.title in self.kessons_titles

    def add_kesson(self, kesson):
        if kesson.title in self.kessons_titles:
            return
        self.kessons_titles.add(kesson.title)
        for tr in kesson.translations:
            kbi = KnowledgeItem(tr)
            self.knowledge_items.add(kbi)
            for t,v in tr.tags.iteritems():
                if t not in self.knowledge_items_by_tag:
                    self.knowledge_items_by_tag[t] = {}
                for tag_value in v:
                    if tag_value not in self.knowledge_items_by_tag[t]:
                        self.knowledge_items_by_tag[t][tag_value] = []
                    self.knowledge_items_by_tag[t][tag_value].append(kbi)

    # def answers(self, question):
    #     for kbi in self.knowledge_items:
    #         if question in kbi.translation.natives:
    #             return kbi.translation.targets
    #     return []

    def get_kbis_to_revise(self):
        return self.knowledge_items

    def get_next_revision_time(self):
        return self.knowledge_items[0].next_revision_time

    def get_kbis_by_tags(self, tags):
        assert(isinstance(tags, list))
        result = {}
        for t in tags:
            for k,v in self.knowledge_items_by_tag[t].iteritems():
                if k not in result:
                    result[k] = []
                result[k].extend(v)
        return result
        # return [self.knowledge_items_by_tag[k] for k in tags]

    def get_question_from_kbi(self, kbi):
        initial_question = random.choice(kbi.translation.natives)
        question_str = initial_question
        question_parts = []
        answer_matches = []
        idx = question_str.find('[')
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
            tags = [t.strip() for t in tags.split('@') if len(t) > 0]
            tags_kbis = self.get_kbis_by_tags(tags)
            tags_kbi = random.choice(tags_kbis[True])
            question_parts.append(random.choice(tags_kbi.translation.natives))
            answer_matches.append(tags_kbi.translation.targets)

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