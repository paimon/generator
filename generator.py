import re
import pickle
from bisect import bisect
from random import randrange
from collections import defaultdict, Counter
from os.path import isfile


class WordGenerator:

    def __init__(self, distribution):
        self.words = []
        self.breakpoints = []
        breakpoint = 0
        for word, count in distribution.items():
            breakpoint += count
            self.words.append(word)
            self.breakpoints.append(breakpoint)
        self.total_count = breakpoint

    def generate(self):
        index = bisect(self.breakpoints, randrange(self.total_count))
        return self.words[index]


class TextGenerator:

    def __init__(self, filename):
        self.filename = filename
        if isfile(self.filename):
            with open(self.filename, 'rb') as f:
                self.first_statistic = pickle.load(f)
                self.triple_statistic = pickle.load(f)
        else:
            self.first_statistic = Counter()
            self.triple_statistic = defaultdict(Counter)

    def learn(self, text):
        first, second = None, '.'
        pattern = re.compile("[a-zA-Z]+|[,.!?]")
        for match in pattern.finditer(text):
            third = match.group().lower()
            if '.' == second:
                self.first_statistic[third] += 1
            if None not in (first, second):
                self.triple_statistic[first, second][third] += 1
            first, second = second, third

    def _generate_words(self, word_count):
        first_generator = WordGenerator(self.first_statistic)
        triple_generator = {
            prefix: WordGenerator(distribution)
            for prefix, distribution in self.triple_statistic.items()
        }
        first, second = '.', first_generator.generate()
        result = [second.title()]
        while len(result) < word_count or second != '.':
            third = triple_generator[first, second].generate()
            if third in ',.?!':
                result[-1] += third
            elif second in '.?!' or third == 'i':
                result.append(third.title())
            else:
                result.append(third)
            first, second = second, third
        return result

    def generate(self, word_count, max_line_length=100):
        lines = []
        start_index, line_length = 0, 0
        words = self._generate_words(word_count)
        for index, word in enumerate(words):
            if line_length + len(word) > max_line_length:
                line = ' '.join(words[start_index:index])
                lines.append(line)
                start_index, line_length = index, 0
            line_length += len(word) + 1
        line = ' '.join(words[start_index:])
        lines.append(line)
        return '\n'.join(lines)

    def save(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.first_statistic, f)
            pickle.dump(self.triple_statistic, f)


if __name__ == '__main__':
    from sys import stdin
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Markov chain text generator')
    parser.add_argument(
        'size',
        type=int,
        nargs='?',
        help='number of words in generated text'
    )
    parser.add_argument(
        '--database',
        default='statistic.db',
        metavar='FILENAME',
        help='statistic database filename'
    )
    args = parser.parse_args()
    generator = TextGenerator(args.database)
    if args.size:
        text = generator.generate(args.size)
        print(text)
    else:
        text = stdin.read()
        generator.learn(text)
    generator.save()
