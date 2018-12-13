#coding: utf8
 
import os
import io

kodule_extenstion = '.kodule'
kourse_extenstion = '.kourse'

def remove_comments(line):
    return line.split('//')[0]

class Translation:
    def __init__(self, line):
        self.hidden = False
        self.data = u''
        self.natives = []
        self.targets = []
        self.tags = {}

        # hidden
        if line[0] == '*':
            self.hidden = True
            line = line[1:].strip()
        # tags
        tag_list = [x.strip() for x in line.split('#')]
        self.data = tag_list[0]
        del tag_list[0]
        self.tags = {t.split('=')[0]:[v for v in t.split('=')[1].split(',') if len(v)>0] if len(t.split('='))>1 else [True] for t in tag_list}
        # translations
        native, target = self.data.split('->')
        self.natives = [x.strip() for x in native.split('|')]
        self.targets = [x.strip() for x in target.split('|')]
    
    def serialize(self):
        return self.data        

class Kesson:
    def __init__(self, title, fin):
        self.initial_material = []
        self.translations = []
        self.title = title
        for line in fin:
            line = line.strip()
            if len(line) == 0:
                break
            line = remove_comments(line).strip()
            if len(line) == 0:
                continue
            if line[0] == '?':
                self.initial_material.append(line[1:].strip())
            elif line.find('->') != -1:
                translation = Translation(line)
                self.translations.append(translation)

class Kodule:
    def __init__(self, kodules, basepath, fullname):
        self.initial_material = []
        self.is_kourse = fullname.endswith(kourse_extenstion)
        self.dependencies = []
        self.kessons = []
        self.pathname = fullname
        # contents
        with io.open(fullname, mode="r", encoding="utf-8") as fin:
            # title
            for line in fin:
                line = remove_comments(line).strip()
                self.title = line
                break
            # header
            for line in fin:
                line = line.strip()
                if len(line) == 0:
                    break
                line = remove_comments(line).strip()
                if len(line) == 0:
                    continue
                if line[0] == '?':
                    self.initial_material.append(line[1:].strip())
                elif line[0] == '@':
                    dependency_fullpath = os.path.join(basepath, line[1:].strip())
                    if dependency_fullpath in kodules:
                        if kodules[dependency_fullpath] is None:
                            print u"Circular references between kodules, can't load. Aborting"
                            raise Exception()
                        else:
                            self.dependencies.append(kodules[dependency_fullpath])
                    else:
                        kodules[dependency_fullpath] = None # mark as loading
                        kodules[dependency_fullpath] = Kodule(kodules, basepath, dependency_fullpath)
                        self.dependencies.append(kodules[dependency_fullpath])
            # lessons
            for line in fin:
                title = remove_comments(line).strip()
                if len(title) == 0:
                    continue
                self.kessons.append(Kesson(title, fin))

    def get_subkodule(self, title):
        for d in self.dependencies:
            if d.title == title:
                return d
        return None
    
    def get_kesson(self, title):
        for k in self.kessons:
            if k.title == title:
                return k
        return None

def load_all(basepath):
    kodules = {}
    for (dirpath, dirnames, filenames) in os.walk(basepath):
        print dirpath, dirnames, filenames
        for f in filenames:
            if not f.endswith(kourse_extenstion) and not f.endswith(kodule_extenstion):
                continue
            fullname = os.path.join(dirpath, f)
            if fullname not in kodules:
                kodules[fullname] = None # mark as loading
                kodules[fullname] = Kodule(kodules, basepath, fullname)
    return kodules

all_kodules = load_all('./kodules')
all_kourses = [k for (n,k) in all_kodules.iteritems() if k.is_kourse]
all_kourses_by_pathname = {k.pathname:k for k in all_kourses}