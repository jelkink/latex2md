import pypandoc
import bibtexparser
import re

class Converter:

  def __init__(self, latex_content, bib_file):
    self.bib_file = bib_file
    self.latex_content = latex_content
    self.markdown_content = ""
    self.figure_count = 1
    self.table_count = 1
    self.label_map = {} 

  def process(self):
    self.markdown_content = self.latex_content

    self.remove_comments()
    self.handle_front_page()
    self.handle_formatting()
    self.handle_section_headers()
    self.handle_footnotes()
    self.handle_complex_environments()
    self.remove_remaining_commands()
    
    if self.bib_file:
      self.handle_bibliography()

  def get_markdown_content(self):
    return self.markdown_content

  def get_word_content(self):
    return pypandoc.convert_text(self.markdown_content, "docx", format="md")
  
  def remove_comments(self):
    self.markdown_content = re.sub(r'%.*?\n', '', self.markdown_content, flags=re.DOTALL)

  def remove_remaining_commands(self):
    commands = re.findall(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^\}]*\})?', self.markdown_content)
    unique_commands = sorted(set(commands))
    print("Remaining LaTeX commands that are not converted:", unique_commands)

    self.markdown_content = re.sub(r'\\.*?\s', '', self.markdown_content)

  def handle_complex_environments(self):
    self.markdown_content = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', 
                     self.replace_figure, self.markdown_content, flags=re.DOTALL)
    
    self.markdown_content = re.sub(r'\\begin\{table\}.*?\\end\{table\}', 
                     self.replace_table, self.markdown_content, flags=re.DOTALL)

    self.markdown_content = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', 
                     '[Equation X here]', self.markdown_content, flags=re.DOTALL)
    
    def replace_ref(match):
      label = match.group(1)
      return f"{self.label_map.get(label, f'Unknown {label}')}"
        
    self.markdown_content = re.sub(r'\\ref{(.*?)}', replace_ref, self.markdown_content)
  
  def replace_figure(self, match):
    figure_content = match.group(0)
    figure_label = self.extract_label(figure_content)
    figure_text = f"![Figure {self.figure_count} here]"
    self.label_map[figure_label] = f"Figure {self.figure_count}" if figure_label else None
    self.figure_count += 1
    return figure_text
    
  def replace_table(self, match):
    table_content = match.group(0)
    table_label = self.extract_label(table_content)
    table_text = f"Table {self.table_count} here"
    self.label_map[table_label] = f"Table {self.table_count}" if table_label else None
    self.table_count += 1
    return table_text
  
  def extract_label(self, content):
    label_match = re.search(r'\\label{(.*?)}', content)
    return label_match.group(1) if label_match else None
  
  def handle_section_headers(self):
    self.markdown_content = re.sub(r'\\section\{(.*?)\}', r'# \1', self.markdown_content)
    self.markdown_content = re.sub(r'\\subsection\{(.*?)\}', r'## \1', self.markdown_content)
    self.markdown_content = re.sub(r'\\subsubsection\{(.*?)\}', r'### \1', self.markdown_content)

  def handle_front_page(self):
    self.markdown_content = re.sub(r'\\title\{(.*?)\}', r'# \1\n', self.markdown_content)
    self.markdown_content = re.sub(r'\\author\{(.*?)\}', r'**Author:** \1\n', self.markdown_content)

  def handle_formatting(self):
    self.markdown_content = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', self.markdown_content)
    self.markdown_content = re.sub(r'\\emph\{(.*?)\}', r'*\1*', self.markdown_content)

  def handle_footnotes(self):
    self.markdown_content = re.sub(r'\\footnote\{(.*?)\}', r'[^\1]', self.markdown_content)

  def handle_bibliography(self):
    self.markdown_content = re.sub(r'\\cite\{(.*?)\}', r'[@\1]', self.markdown_content)
    
    with open(self.bib_file) as bibtex_file:
      bib_database = bibtexparser.load(bibtex_file)

    entries = {}
    for entry in bib_database.entries:
      citation_key = entry.get("ID")
      formatted_entry = f"{entry.get('author', 'Unknown Author')} ({entry.get('year', 'n.d.')}): {entry.get('title', 'No Title')}"
      entries[citation_key] = formatted_entry

    for key, citation_text in entries.items():
      self.markdown_content = re.sub(rf'@{key}', citation_text, self.markdown_content)