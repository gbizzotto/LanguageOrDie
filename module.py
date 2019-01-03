#coding: utf8
 
import os
import io
import util

module_extenstion = '.module'
course_extenstion = '.course'

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

class lesson:
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

class module:
    def __init__(self, modules, basepath, fullname):
        self.initial_material = []
        self.is_course = fullname.endswith(course_extenstion)
        self.dependencies = []
        self.lessons = []
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
                    if dependency_fullpath in modules:
                        if modules[dependency_fullpath] is None:
                            util.log(u"Circular references between modules, can't load. Aborting")
                            raise Exception()
                        else:
                            self.dependencies.append(modules[dependency_fullpath])
                    else:
                        modules[dependency_fullpath] = None # mark as loading
                        modules[dependency_fullpath] = module(modules, basepath, dependency_fullpath)
                        self.dependencies.append(modules[dependency_fullpath])
            # lessons
            for line in fin:
                title = remove_comments(line).strip()
                if len(title) == 0:
                    continue
                self.lessons.append(lesson(title, fin))

    def get_submodule(self, title):
        for d in self.dependencies:
            if d.title == title:
                return d
        return None
    
    def get_lesson(self, title):
        for k in self.lessons:
            if k.title == title:
                return k
        return None

def load_all(basepath):
    modules = {}
    for (dirpath, dirnames, filenames) in os.walk(basepath):
        util.log(dirpath, dirnames, filenames)
        for f in filenames:
            if not f.endswith(course_extenstion) and not f.endswith(module_extenstion):
                continue
            fullname = os.path.join(dirpath, f)
            if fullname not in modules:
                modules[fullname] = None # mark as loading
                modules[fullname] = module(modules, basepath, fullname)
    return modules

all_modules = load_all('./modules')
all_courses = [k for (n,k) in all_modules.iteritems() if k.is_course]
all_courses_by_pathname = {k.pathname:k for k in all_courses}