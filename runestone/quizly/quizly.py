# Copyright (C) 2011  Bradley N. Miller
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# This files runs during runestone build. It generates the node data
# that is used to render the component by the  quizly.js script.

# Note: An import entry for quizly must be included in runestone/__init__.py

__author__ = "rmorelli"

# Debug flags
DEBUG = True
VERBOSE = False

import os, shutil
from docutils import nodes
from runestone.common import RunestoneIdDirective, RunestoneIdNode
from runestone.server.componentdb import addQuestionToDB, addHTMLToDB
from pathlib import Path

# Template that will load index.html?quizname=the-quiz-name into an <iframe>
# NOTE: Hardcoding the container class.  Temporarily??
QUIZLY_TEMPLATE = """
       <div class="runestone alert alert-warning">
       <div data-component="quizly" id="%(divid)s" data-question_label="%(question_label)s" style="visibility: visible;">
         <iframe height="595" src="../_static/quizly/index.html?backpack=hidden&amp;selector=hidden&amp;quizname=###&amp;hints=true&amp;repeatable=false" style="border: 0px; margin: 1px; padding: 1px;" width="100%%">
         </iframe>
       </div>
       </div>
       """

# Resource files should be stored in the X/_static directory, from where they
# will be automatically copied into build/x/_static, where 'x' is the project name
STATIC_DIR = "./_static"

# Copy the resource files into the _static folder, maintaining proper folder hierarchy
# The resources should be organized as follows:
# _static
# |-quizly
#   |- all_appinventor.js - compressed js files
#   |- all_blockly.js     - compressed js files
#   |- all_quizly.js      - compressed js files
#   |- quizme-helper.js - main source code
#   |- quizzes.js       - quizly quizzes
#   |- index.html       - container for the iframe
#   |- blockly.html     - blockly iframe
#   |- main.css         
#   |- media            - folder of images, etc.
# Perhaps there's a runestone routine to copy files?
# TODO: Test this with MobileCSP units
def copyfiles():
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    QUIZLY_DIR = STATIC_DIR+'/quizly'
    MEDIA_DIR = QUIZLY_DIR+'/media'
    if os.path.exists(QUIZLY_DIR):
        shutil.rmtree(QUIZLY_DIR)
    os.mkdir(QUIZLY_DIR, mode=0o755)
    os.mkdir(QUIZLY_DIR+'/media', mode=0o755)
    js_folder = Path(CURR_DIR).glob('js/*.js')
    html_folder = Path(CURR_DIR).glob('js/*.html')
    media_folder = Path(CURR_DIR).glob('js/media/*')
    css_folder = Path(CURR_DIR).glob('js/*.css')
    files = [x for x in js_folder]
    print('Copying resource files to ' + STATIC_DIR) if VERBOSE else None
    for f in files:
        print(str(f) + ' --> ' + QUIZLY_DIR) if VERBOSE else None
        shutil.copy(f, QUIZLY_DIR)
    files = [x for x in css_folder]
    for f in files:
        print(str(f) + ' --> ' + QUIZLY_DIR) if VERBOSE else None 
        shutil.copy(f, QUIZLY_DIR)
    files = [x for x in html_folder]
    for f in files:
        print(str(f) + ' --> ' + QUIZLY_DIR) if VERBOSE else None 
        shutil.copy(f, QUIZLY_DIR)
    files = [x for x in media_folder]
    for f in files:
        print(str(f) + ' --> ' + MEDIA_DIR) if VERBOSE else None
        shutil.copy(f, MEDIA_DIR)

# Define the quizly directive
def setup(app):
    app.add_directive("quizly", Quizly)
    app.add_node(QuizlyNode, html=(visit_quizly_node, depart_quizly_node))

# The only content needed from quizly.py is the quizname
class QuizlyNode(nodes.General, nodes.Element, RunestoneIdNode):
    def __init__(self, content, **kwargs):
        """
        Arguments:
        - `self`:
        - `content`:
        """
        super(QuizlyNode, self).__init__(**kwargs)
        self.runestone_options = content
        print('DEBUG: QuizlyNode content = ' + str(content)) if DEBUG else None
        self.quizname = str(content['controls'][0])
        self.quizname = str.strip(self.quizname[10:])
        self.template = QUIZLY_TEMPLATE.replace('###', self.quizname)
        print('DEBUG: QuizlyNode self.quizname = ' + self.quizname) if DEBUG else None

# self for these functions is an instance of the writer class.  For example
# in html, self is sphinx.writers.html.SmartyPantsHTMLTranslator
# The node that is passed as a parameter is an instance of our node class.
def visit_quizly_node(self, node):

    node.delimiter = "_start__{}_".format(node.runestone_options["divid"])
    self.body.append(node.delimiter)

    print('DEBUG: visit_quizly_node quizname = ' + node.quizname) if DEBUG else None
    print('DEBUG: visit_quizly_node template = ' + node.template) if DEBUG else None
    print('DEBUG: visit_quizly_node options = ' + str(node.runestone_options)) if DEBUG else None

    res = node.template % (node.runestone_options)
    copyfiles()  # Copy resource files
    print('DEBUG: visit_quizly_node res = ' + res) if DEBUG else None
    self.body.append(res)


def depart_quizly_node(self, node):
    """ This is called at the start of processing an activecode node.  If activecode had recursive nodes
        etc and did not want to do all of the processing in visit_ac_node any finishing touches could be
        added here.
    """
    print('DEBUG: depart_quizly_node') if DEBUG else None
    addHTMLToDB(
        node.runestone_options["divid"],
        node.runestone_options["basecourse"],
        "".join(self.body[self.body.index(node.delimiter) + 1 :]),
    )
    self.body.remove(node.delimiter)


def process_activcode_nodes(app, env, docname):
    pass


def purge_activecodes(app, env, docname):
    pass


# The object created when the quizly directive is parsed in an RST.
# The quizname is the only required argument.
class Quizly(RunestoneIdDirective):
    """
    .. quizly:: some_unique_id, e.g., q1

       :quizname: quiz_eval_expression
    """
    required_arguments = 1
    optional_arguments = 0
    has_content = True
    option_spec = {}

    def run(self):
        super(Quizly, self).run()
        print('DEBUG; Quizly.run()') if DEBUG else None

        addQuestionToDB(self)   # Not sure whether this works?
        document = self.state.document
        rel_filename, filename = document.settings.env.relfn2path(self.arguments[0])

        pathDepth = rel_filename.count("/")
        self.options["quizlyHomePrefix"] = "./" * pathDepth

        plstart = len(self.content)
        if self.content:
            self.options["controls"] = self.content[:plstart]

        quizly_node = QuizlyNode(self.options, rawsource=self.block_text)
        quizly_node.source, quizly_node.line = self.state_machine.get_source_and_line(
            self.lineno
        )
        print('DEBUG: run() self.content = ' + str(self.content)) if DEBUG else None
        print('DEBUG: run() quizly_node = ' + str(quizly_node)) if DEBUG else None
        return [quizly_node]

