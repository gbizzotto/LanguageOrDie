
import datetime
import kodule
from sortedcontainers import SortedList

time_interval = datetime.timedelta(minutes=1)

class KnowledgeItem:
    def __init__(self, translation):
        self.translation = translation
        self.next_revision_time = datetime.datetime.now()
        self.times_got_right = 0

    def got_it_right_on_1st_try(self):
        self.times_got_right += 1
        self.next_revision_time = datetime.datetime.now() + time_interval * (3**self.times_got_right - 1)

    def got_it_right_eventually(self):
        self.next_revision_time = datetime.datetime.now() + time_interval * (3**self.times_got_right - 1)

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
        # now = datetime.datetime.now()
        # result = [kbi for kbi in self.knowledge_items if kbi.next_revision_time <= now]
        # result.sort(key=lambda kbi: kbi.next_revision_time)
        # result.reverse()
        # return result

    def get_next_revision_time(self):
        return self.knowledge_items[0].next_revision_time