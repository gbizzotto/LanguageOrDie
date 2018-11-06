import os
import io

kodule_extenstion = '.kodule'
kourse_extenstion = '.kourse'

def remove_comments(line):
    return line.split('//')[0]

class Translation:
    def __init__(self, line):
        self.secret = False
        self.data = ''
        self.natives = []
        self.targets = []
        self.tags = {}

        # secret
        if line[0] == '*':
            self.secret = True
            line = line[1:].strip()
        # tags
        tags = [x.strip() for x in line.split('#')]
        self.data = tags[0]
        del tags[0]
        self.tags = {t.split('=')[0]:[t.split('=')[1]] if len(t.split('='))>1 else [True] for t in tags}
        # translations
        native, target = self.data.split('->')
        self.natives = [x.strip() for x in native.split('|')]
        self.targets = [x.strip() for x in target.split('|')]
        
    def __unicode__(self):
        return ('* ' if self.secret else '') + unicode(self.data) + ' #' + unicode(self.tags)
        

class Kesson:
    def __init__(self, fin):
        self.initial_material = []
        self.translations = []
        # self.translations_by_tag = {}
        # title
        for line in fin:
            self.title = remove_comments(line).strip()
            break
        # contents
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
        self.is_kourse = fullname.endswith(kourse_extenstion)
        self.dependencies = []
        self.kessons = []
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
                if line[0] == '@':
                    dependency_fullpath = os.path.join(basepath, line[1:].strip())
                    if dependency_fullpath in kodules:
                        if kodules[dependency_fullpath] is None:
                            print "Circular references between kodules, can't load. Aborting"
                        else:
                            self.dependencies.append(kodules[dependency_fullpath])
                    else:
                        kodules[dependency_fullpath] = None # mark as loading
                        kodules[dependency_fullpath] = Kodule(kodules, basepath, dependency_fullpath)
                        self.dependencies.append(kodules[dependency_fullpath])
            # lessons
            self.kessons.append(Kesson(fin))

    def answers(self, question):
        result = []
        for dep in self.dependencies:
            result.extend(dep.answers(question))
        for k in self.kessons:
            result.extend(k.answers(question))
        return result

def load_all(basepath):
    kodules = {}
    for (dirpath, dirnames, filenames) in os.walk(basepath):
        for f in filenames:
            f = unicode(f)
            if not f.endswith(kourse_extenstion) and not f.endswith(kodule_extenstion):
                continue
            fullname = os.path.join(dirpath, f)
            if fullname not in kodules:
                kodules[fullname] = None # mark as loading
                kodules[fullname] = Kodule(kodules, basepath, fullname)
    return kodules