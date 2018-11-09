
import datetime
import random

from sortedcontainers import SortedList

import kodule
import util


class Answers:
    def __init__(self, match_list):
        self.sequence = [match_list]
    def accept(self, tentative):
        return util.normalize_caseless(tentative) in [util.normalize_caseless(t) for t in self.sequence[0]]


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

    def answers(self, question):
        for kbi in self.knowledge_items:
            if question in kbi.translation.natives:
                return kbi.translation.targets
        return []

    def get_kbis_to_revise(self):
        return self.knowledge_items

    def get_next_revision_time(self):
        return self.knowledge_items[0].next_revision_time

    def get_question_from_kbi(self, kbi):
        question = random.choice(kbi.translation.natives)
        answers = Answers(self.answers(question))
        return question, answers