import sentence
from tqdm import tqdm

class corpus():

    def __init__(self, corpus):
        self.corpus = corpus

    def get_ranked_objects(self):
        objects_dict = {}
        for element in self.corpus:
            e = sentence.sentence(element)
            objects = e.objects
            for o in objects:
                if o.text in objects_dict:
                    objects_dict[o.text] += 1
                else:
                    objects_dict[o.text] = 1
        return {k: v for k, v in sorted(objects_dict.items(), key=lambda item: item[1], reverse=True)}

    def get_ranked_narration(self):
        narration_dict = {}
        for element in tqdm(self.corpus):
            e = sentence.sentence(element)
            narrations = e.narration
            for narration in narrations:
                if narration.text.lower() in narration_dict:
                    narration_dict[narration.text.lower()] += 1
                else:
                    narration_dict[narration.text.lower()] = 1
        return {k: v for k, v in sorted(narration_dict.items(), key=lambda item: item[1], reverse=True)}


