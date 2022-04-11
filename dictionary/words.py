from typing import List

class Words:
    def __init__(self, request, dictionary):
        self.session = request.session
        self.dictionary = dictionary
        self.object_key = f"dictionary_{dictionary.id}"

        if self.object_key not in self.session:
            self.session[self.object_key] = dictionary.words.copy()
        self.words = self.session[self.object_key]

    def add_word(self, word: str, definition: str) -> None:
        if definition in self.words:
            raise DuplicateError()
        self.words[definition.strip()] = word.strip()
        self.save()

    def remove_word(self, definition: str) -> None:
        if definition not in self.words:
            raise DefinitionDoesNotExist()
        del self.words[definition]
        self.save()

    def get_words(self) -> List[tuple]:
        """
        Returns sorted by word list of tuples.
        """
        return sorted(self.words.items(),
                      key=lambda items: items[1].lower())

    def clear_list(self):
        """
        Removes all words from session.
        """
        self.words.clear()
        self.save()

    def refresh_list(self):
        """
        Reverses changes by copying words from `Dictionary` object.
        """
        self.session[self.object_key] = self.dictionary.words.copy()
        self.words = self.session[self.object_key]

    def clear_session(self):
        del self.session[self.object_key]
        self.save()

    def save_to_db(self):
        """
        Saves words to `Dictionary.words`.
        """
        self.dictionary.words = dict(self.get_words())
        self.dictionary.save()
        self.clear_session()

    def save(self):
        self.session.modified = True


class DuplicateError(Exception):
    def __init__(self):
        super().__init__("Word with the same definition is already exist in this dictionary.")


class DefinitionDoesNotExist(Exception):
    def __init__(self):
        super().__init__("There is not such definition in this session.")
