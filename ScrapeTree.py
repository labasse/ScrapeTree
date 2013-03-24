import re


class ScrapeNode:
    """Base class for scrape nodes"""
    def starts_with_this_line(self, line):
        raise NotImplementedError("Abstract method")

    def scrape(self, line, doc):
        raise NotImplementedError("Abstract method")

    def _get_context_name(self):
        return '.context{0}'.format(id(self))


class ScrapeRegex(ScrapeNode):
    """Scrape node for regex on a single line"""
    def __init__(self, pattern):
        super().__init__()
        self._regex = re.compile(pattern)

    def starts_with_this_line(self, line):
        return self._regex.search(line) is not None

    def scrape(self, line, doc):
        m = self._regex.search(line)
        if m is not None:
            doc.update(m.groupdict())
            return True
        else:
            return False


class ScrapeContainer(ScrapeNode):

    def __init__(self, nodes):
        super().__init__()
        self._nodes = nodes

    def _start_index(self, line, doc=None):
        raise NotImplemented("Abstract method")

    def _last_index(self, doc):
        raise NotImplemented("Abstract method")

    def _index2node(self, index):
        raise NotImplemented("Abstract method")

    def starts_with_this_line(self, line):
        return self._start_index(line) is not None

    def scrape(self, line, doc):
        if self._get_context_name() in doc:
            index = doc[self._get_context_name()]
        else:
            index = self._start_index(line, doc)
            if index is None:
                return False
            doc[self._get_context_name()] = index
        if self._index2node(index).scrape(line, doc) and self._last_index(doc):
            del doc[self._get_context_name()]
            return True
        else:
            return False


class ScrapeSequence(ScrapeContainer):
    """Scrape node using a list of scrape nodes"""
    def __init__(self, nodes):
        super().__init__(nodes)

    def _start_index(self, line, doc=None):
        if doc is not None and self._get_context_name() + '.i' in doc:
            index = doc[self._get_context_name() + '.i']
        else:
            index = 0
        for i in range(index, len(self._nodes)):
            node, optional = self._nodes[i]
            if node.starts_with_this_line(line):
                return i
            if not optional:
                break

    def _last_index(self, doc):
        index = doc[self._get_context_name()] + 1
        if index == len(self._nodes):
            if self._get_context_name() + '.i' in doc:
                del doc[self._get_context_name() + '.i']
            return True
        else:
            del doc[self._get_context_name()]
            doc[self._get_context_name() + '.i'] = index
            return False

    def _index2node(self, index):
        return self._nodes[index][0]


class ScrapeAlternative(ScrapeContainer):
    """ Scrape node branching on a scrape node or another
        according the first encontered """
    def __init__(self, alternatives):
        super().__init__(alternatives)

    def _start_index(self, line, doc=None):
        for i, node in enumerate(self._nodes):
            if node.starts_with_this_line(line):
                return i

    def _last_index(self, doc):
        return True

    def _index2node(self, index):
        return self._nodes[index]


class ScrapeMultiline(ScrapeNode):
    """Scrape node extracting text from multiple lines"""
    def __init__(self, keyname, starting_pattern, ending_pattern):
        self._keyname = keyname
        self._starting_regex = re.compile(starting_pattern)
        self._ending_regex = re.compile(ending_pattern)
        if self._starting_regex.groups == 0 or self._ending_regex.groups == 0:
            raise RuntimeError("Starting and ending pattern must have groups")

    def starts_with_this_line(self, line):
        return self._starting_regex.search(line)

    def scrape(self, line, doc):
        if self._get_context_name() not in doc:
            m = self._starting_regex.search(line)
            if m is None:
                return False
            doc[self._get_context_name()] = []
            line = line[m.end(0):]

        m = self._ending_regex.search(line)
        if m is None:
            doc[self._get_context_name()].append(line)
            return False
        else:
            index = m.start(0)
            doc[self._keyname] = doc[self._get_context_name()]
            doc[self._keyname].append(line[:index])
            del doc[self._get_context_name()]
            return True


class ScrapeKeyValueSequence(ScrapeSequence):

    def __init__(self, keyname, valname, nodes):
        super().__init__([(nodes[0], False), (nodes[1], False)])
        self._keyname = keyname
        self._valname = valname

    def scrape(self, line, doc):
        if self._get_context_name() not in doc:
            if self._start_index(line, doc) is None:
                return False
            else:
                doc[self._get_context_name()] = {}
        if super().scrape(line, doc[self._get_context_name()]):
            doc[doc[self._get_context_name()][self._keyname]] = \
                doc[self._get_context_name()][self._valname]
            del doc[self._get_context_name()]
            return True
        else:
            return False


class ScrapeCollection(ScrapeAlternative):

    def __init__(self, repeat_key, repeat_node, ending_node):
        super().__init__([repeat_node, ending_node])
        self.repeat_key = repeat_key

    def scrape(self, line, doc):
        if self._get_context_name() + '.d' not in doc:
            res = self._start_index(line)
            if res is None:
                return False
            elif res == 0:
                doc[self._get_context_name() + '.d'] = {}
        repeating = (self._get_context_name() + '.d') in doc
        subdoc = doc[self._get_context_name() + '.d'] if repeating else doc
        if super().scrape(line, subdoc):
            if self.repeat_key not in doc:
                doc[self.repeat_key] = []
            if not repeating:
                return True
            doc[self.repeat_key].append(doc[self._get_context_name() + '.d'])
            del doc[self._get_context_name() + '.d']
        return False
