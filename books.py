from pyleri import *

# Create a Grammar Class to define the format
class BookGrammar(Grammar):    
    k_book = Keyword('book')
    r_title = Regex('[a-zA-Z 0-9\']+')
    k_author = Keyword('authors')
    r_author = Regex('[a-zA-Z 0-9\']+')
    k_publication = Keyword('publication_date')
    k_pub = Keyword('pub_date')
    k_pub_date = Choice(k_publication, k_pub)
    r_pub_date = Regex('[0-9]+')
    k_description = Keyword('description')
    r_description = Regex('"([^"]*)"')    
    r_name = Regex('[a-zA-Z 0-9]+')
    t_equals = Token('=')
    k_end_book = Keyword('end_book')
    
    DESCRIPTION = Sequence(k_description, r_description)
    AUTHORS = Sequence(k_author, List(r_author, delimiter=',', mi=1, ma=None))
    PUB_DATE = Sequence(k_pub_date, r_pub_date)
    TITLE = Sequence(k_book, r_title)        

    START = Ref()
    BOOK = Sequence(TITLE, Optional(AUTHORS), Optional(PUB_DATE), Optional(DESCRIPTION))
    ELEM = Choice(BOOK, START)    
    START = Sequence(r_name, t_equals, '[', List(ELEM, delimiter=k_end_book), ']')

class VisitTree:
    def get_collections(self):
        return self.books
    
    def add_book(self, node):
        if hasattr(node.element, 'name'):
            if node.element.name == 'r_title':
                self.book = {}
                self.book['title'] = node.string                
            if node.element.name == 'r_pub_date':
                self.book['publication_date'] = node.string
            # we create the authors collection when we find the author keyword
            if node.element.name == 'k_author':
                self.book['authors'] = []
            # we then add each author to the collection
            if node.element.name == 'r_author':
                self.book['authors'].append(node.string)
            if node.element.name == 'r_description':
                # we remove the delimiting double quotes
                self.book['description'] = node.string[1:-1]                             
                
    def manage_collection(self, node):
        if hasattr(node.element, 'name'):
            # we have found the end of a book          
            if node.element.name == 'k_end_book':                
                self.books[self.name_collection].append(self.book)
                del self.book
            # set the name of the collection
            if node.element.name == 'r_name':
                # set the current name of the collection
                self.name_collection = str.strip(node.string) 

        # start of the collection
        if not hasattr(node.element, 'name') and node.string == '[':            
            # let's check whether this is the first collection
            if not hasattr(self, 'books'):
                self.books = {}        

            # let's store the name of the collection, in case of nested collections  
            self.names_collections.append(self.name_collection)
                
            # create the new collection            
            self.books[self.name_collection] = []

        # end of the collection
        if not hasattr(node.element, 'name') and node.string == ']':
            # let's check whether the last book was added to the collection
            if hasattr(self, 'book'):
                self.books[self.name_collection].append(self.book)
                del self.book
            
            # let's delete the name of the current collection
            del self.name_collection
            
            # let's recover the name of the parent collection, if any
            if(len(self.names_collections) > 0):
                self.name_collection = self.names_collections.pop()
        
    def read_info(self, node):        
        self.add_book(node)
        self.manage_collection(node)
            
    # Returns properties of a node object as a dictionary:
    def node_props(self, node, children):
        self.read_info(node)
        
        return {
            'start': node.start,
            'end': node.end,
            'name': node.element.name if hasattr(node.element, 'name') else None,
            'element': node.element.__class__.__name__,
            'string': node.string,
            'children': children
        }

    # Recursive method to get the children of a node object:
    def get_children(self, children):
        return [self.node_props(c, self.get_children(c.children)) for c in children]

    # The main function that we all visit all the leaves of the tree
    def navigate_parse_tree(self, res):
        # store the names of the collections
        self.names_collections = []    
        start = res.tree.children[0] \
            if res.tree.children else res.tree
        return self.node_props(start, self.get_children(start.children))

def main():
    # Compile your grammar by creating an instance of the Grammar Class.
    book_grammar = BookGrammar()

    # read the data from a file
    in_file = open("data.books","r")        
    text = in_file.read()        
    in_file.close()
    # if the file is valid we navigate the parse tree
    if book_grammar.parse(text).is_valid:
        tree = VisitTree()
        tree.navigate_parse_tree(book_grammar.parse(text))  
        books = tree.get_collections()
        print("Books found:")
        print(books)
    else:
        print("Error, expecting: " + str(book_grammar.parse(text).expecting))

if __name__ == '__main__':
    main()