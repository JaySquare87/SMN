import spacy
from spacy.lang.en import STOP_WORDS
from spacy import displacy
from queue import Queue
from cleantext import clean

nlp = spacy.load('en_core_web_lg')

roots = Queue()
ling_signs = ['i', 'you', 'he', 'she', 'they', 'it', 'him', 'her', 'their', 'those', 'them', 'who', 'whome', 'whose']

class sentence:

    def __init__(self, text):
        self.text = self.clean_text(text) 
        self.doc = nlp(self.text)
        self.ling_signs = self.get_ling_signs()
        self.objects = list(self.doc.ents)
        self.narration = self.get_narration()

    def get_narration(self):
        narration = []
        for token in self.doc:
            if token.pos_ == 'VERB' and not token.text.lower() in STOP_WORDS:
                narration.append(token)
        return narration

    def get_ling_signs(self):
        signs = []
        for token in self.doc:
            if token.text.lower() in ling_signs:
                signs.append(token)
        return signs

    def get_sign_object_narration_relation(self):
        object_verb_relation = {}
        for verb in self.narration:
            signs_objects = self.get_signs_objects_in_children(verb)
            if len(signs_objects) > 0: 
                for sign_object in signs_objects:
                    object_verb_relation[sign_object] = verb
        return object_verb_relation
    
    def get_signs_objects_in_children(self, token):
        signs_objects = []
        for token in token.children: 
            if token.ent_type > 0:
                signs_objects.append(token)
            if token in self.ling_signs:
                signs_objects.append(token)
        return signs_objects

    def get_who(self):
        verb_who = {}
        for verb in self.narration:
            who = []
            temp = []
            for child in verb.children:
                if 'sub' in child.dep_ or 'aux' in child.dep_:
                    who.append([branch.text for branch in child.subtree])
            for child in verb.children:
                if child.text in who:
                    temp.append(child)

            verb_who[verb] = temp
        return verb_who

    def get_details(self):
        verb_details = {}
        for verb in self.narration:
            details = []
            for child in verb.children:
                if child.dep_ in ['dobj', 'pobj', 'ccomp', 'acomp', 'xcomp', 'pcomp', 'acl', 'prep', 'compound', 'attr', 'conj']:
                    details.append(child)
                    details.extend([child.text for child in child.children])
                    #worthy_children = self.check_worthy_children(child)
                    #details.extend(worthy_children)
            verb_details[verb] = details
        return verb_details

    def clean_text(self, text):
        cleaned_text = clean(text,
                fix_unicode=True,               # fix various unicode errors
                to_ascii=True,                  # transliterate to closest ASCII represobjectation
                lower=False,                     # lowercase text
                no_line_breaks=True,           # fully strip line breaks as opposed to only normalizing them
                no_urls=False,                  # replace all URLs with a special token
                no_emails=False,                # replace all email addresses with a special token
                no_phone_numbers=False,         # replace all phone numbers with a special token
                no_numbers=False,               # replace all numbers with a special token
                no_digits=False,                # replace all digits with a special token
                no_currency_symbols=False,      # replace all currency symbols with a special token
                no_punct=False,                 # fully remove punctuation
                replace_with_url="<URL>",
                replace_with_email="<EMAIL>",
                replace_with_phone_number="<PHONE>",
                replace_with_number="<NUMBER>",
                replace_with_digit="0",
                replace_with_currency_symbol="<CUR>",
                lang="en"                       # set to 'de' for German special handling
            )
        return cleaned_text

    # %%
    def check_worthy_children(self, child):
        child_queue = Queue()
        return_children = []
        for child in child.children:
            if child.pos_ == 'VERB':
                roots.put(child)
            child_queue.put(child)
        while not child_queue.empty():
            child = child_queue.get()
            for c in child.children:
                if c.dep_ in ['dobj', 'pobj', 'compound', 'npadvmod', 'relcl', 'prep']:
                    if c.pos_ == 'VERB':
                        roots.put(child)
                    else:
                        child_queue.put(c)
                        #print(c)
                        #print('Details from:', c, [c.text for c in c.children])
                        return_children.append(c.text)
                        return_children.extend([c.text for c in c.children if c.dep_ in ['pobj', 'compound', 'npadvmod']])
        return return_children


    # %%
    def do_summary_root(self, root):
        words = []
        words_from = []
        words_to = []
        print('What happened?:', root)
        words.append(root.text)
        for child in root.children:
            if child.pos_ == 'SPACE':
                continue
            if child.dep_ in ['nsubj', 'nsubjpass', 'csubj']:
                if child.pos_ == 'VERB':
                    roots.put(child)
                print('Who_from?:', child, [child.text for child in child.children])
                words_from.append(child.text)
                words_from.extend([child.text for child in child.children ])
                worthy_children = self.check_worthy_children(child)
                words_from.extend(worthy_children)
            if child.dep_ in ['dobj', 'pobj', 'ccomp', 'acomp', 'xcomp', 'pcomp', 'acl', 'prep', 'compound', 'attr', 'conj']:
                if child.pos_ == 'VERB':
                    roots.put(child)
                else:
                    print('Who_to?:', child, [child.text for child in child.children])
                    words_to.append(child.text)
                    words_to.extend([child.text for child in child.children])
                    worthy_children = self.check_worthy_children(child)
                    words_to.extend(worthy_children)
            if child.dep_ in ['neg']:
                print('Negation:', child, [child.text for child in child.children])
                words.append(child.text)
                words.extend([child.text for child in child.children])
            if child.dep_ in ['aux']:
                words.append(child.text)
        return words, words_from, words_to

    # %%

    def get_summaries(self):
        summaries = []
        summaries_nostop = []
        sents = self.doc.sents
        for sent in sents:
            words = []
            words_from = []
            words_to = []
            roots.put(sent.root)
            while not roots.empty():
                root = roots.get()
                x, y, z = self.do_summary_root(root)
                words.extend(x)
                words_from.extend(y)
                words_to.extend(z)
                summary = []
                for token in sent:
                    if token.text in words_from:
                        summary.append(token)
                        words_from.remove(token.text)
                for token in sent:
                    if token.text in words:
                        summary.append(token)
                        words.remove(token.text)
                for token in sent:
                    if token.text in words_to:
                        summary.append(token)
                        words_to.remove(token.text)
                summaries.append(summary)
                summary_nostop = []
                for word in summary:
                    if not word.is_stop:
                        summary_nostop.append(word)
                summaries_nostop.append(summary_nostop)

            #print(' '.join(word.text for word in summary))
            #print(' '.join(word.text for word in summary_nostop))
        return summaries, summaries_nostop

    def displacy_serve(self, ents=False):
        if ents:
            displacy.serve(self.doc, style='ents')
        else:
            displacy.serve(self.doc)

    def displacy_render(self, ents=False):
        if ents:
            dispalcy.render(self.doc, style='ents')
        else:
            displacy.render(self.doc)



