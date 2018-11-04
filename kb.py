
import kodule

class KnowledgeItem:
    def __init__(self, translation, last_got_right=None, times_got_right=0):
        self.translation = translation
        self.last_got_right = last_got_right
        self.times_got_right = times_got_right

class KnowledgeBase:
    def __init__(self):
        self.kessons_titles = set()
        self.knowledge_items = []
        self.knowledge_items_by_tag = {}
    
    def has_kesson(self, kesson):
        return kesson.title in self.kessons_titles

    def add_kesson(self, kesson):
        if kesson.title in self.kessons_titles:
            return
        self.kessons_titles.add(kesson.title)
        for tr in kesson.translations:
            kbi = KnowledgeItem(tr)
            self.knowledge_items.append(kbi)
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

    def get_knoledge_items_by_age_desc(self):
        return self.knowledge_items.sort(key=lambda kbi: kbi.times_got_right).reverse()