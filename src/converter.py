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
    self.section_counter = [0, 0, 0]
    self.label_map = {} 
    self.footnotes = {}
    self.bibliography_keys = []

  def process(self):
    self.markdown_content = self.latex_content

    self.remove_comments()
    self.handle_front_page()
    self.handle_formatting()
    self.handle_section_headers()
    self.handle_footnotes()
    self.handle_bibliography()
    self.handle_complex_environments()
    self.handle_remaining_references()
    self.remove_remaining_commands()
    
    if self.bib_file:
      self.handle_bibliography()
      self.append_bibliography()

  def get_markdown_content(self):
    return self.markdown_content

  def export_word_content(self, filename):
    text = self.markdown_content
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    pypandoc.convert_text(text, "docx", format="md", outputfile=filename)
  
  def remove_comments(self):
    def replace_percent(match):
      if match.group(0).startswith(r'\%'):
        return match.group(0)[1:]  # Remove the escaping backslash
      return ''  # Remove the comment

    self.markdown_content = re.sub(r'\\%|%.*?\n', replace_percent, self.markdown_content, flags=re.DOTALL)

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
  
  def handle_remaining_references(self):
    
    def update_section_counter(header_level):
      if header_level == 1:
        self.section_counter[0] += 1
        self.section_counter[1] = 0
        self.section_counter[2] = 0
      elif header_level == 2:
        self.section_counter[1] += 1
        self.section_counter[2] = 0
      elif header_level == 3:
        self.section_counter[2] += 1

    def get_current_section():
      return '.'.join(str(num) for num in self.section_counter if num > 0)

    def replace_label(match):
      label = match.group(1)
      current_section = get_current_section()
      self.label_map[label] = current_section
      return ""

    self.markdown_content = re.sub(r'\\label{(.*?)}', replace_label, self.markdown_content)

    def replace_ref(match):
      label = match.group(1)
      return f"{self.label_map.get(label, f'Unknown {label}')}"

    self.markdown_content = re.sub(r'\\ref{(.*?)}', replace_ref, self.markdown_content)

    def handle_headers(match):
      header = match.group(0)
      if header.startswith('# '):
        update_section_counter(1)
      elif header.startswith('## '):
        update_section_counter(2)
      elif header.startswith('### '):
        update_section_counter(3)
      return header

    self.markdown_content = re.sub(r'^(# .+|## .+|### .+)', handle_headers, self.markdown_content, flags=re.MULTILINE)

  def replace_figure(self, match):
    figure_content = match.group(0)
    figure_label = self.extract_label(figure_content)
    figure_caption = self.extract_caption(figure_content)
    figure_text = f"\n\n<figure number> Figure {self.figure_count}\n<figure title> {figure_caption}\n\n"
    self.label_map[figure_label] = f"{self.figure_count}" if figure_label else None
    self.figure_count += 1
    return figure_text
    
  def replace_table(self, match):
    table_content = match.group(0)
    table_label = self.extract_label(table_content)
    table_text = f"\n\n<insert table {self.table_count} here>\n\n"
    self.label_map[table_label] = f"{self.table_count}" if table_label else None
    self.table_count += 1
    return table_text
  
  def extract_label(self, content):
    label_match = re.search(r'\\label{(.*?)}', content)
    return label_match.group(1) if label_match else None
  
  def extract_caption(self, content):
    caption_match = re.search(r'\\caption{(.*?)}', content)
    return caption_match.group(1) if caption_match else None
  
  def handle_section_headers(self):
    self.markdown_content = re.sub(r'\\section\{(.*?)\}', r'\n# \1', self.markdown_content)
    self.markdown_content = re.sub(r'\\subsection\{(.*?)\}', r'\n## \1', self.markdown_content)
    self.markdown_content = re.sub(r'\\subsubsection\{(.*?)\}', r'\n### \1', self.markdown_content)

  def handle_front_page(self):
    self.markdown_content = re.sub(r'\\title\{(.*?)\}', r'# \1\n', self.markdown_content)
    self.markdown_content = re.sub(r'\\author\{(.*?)\}', r'**Author:** \1\n', self.markdown_content)

  def handle_formatting(self):
    self.markdown_content = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', self.markdown_content)
    self.markdown_content = re.sub(r'\\emph\{(.*?)\}', r'*\1*', self.markdown_content)

  def handle_footnotes(self):
    footnote_counter = 1

    def replace_footnote(match):
      nonlocal footnote_counter
      footnote_text = match.group(1)
      footnote_reference = f"[^{footnote_counter}]"
      self.footnotes[footnote_counter] = footnote_text
      footnote_counter += 1
      return footnote_reference

    self.markdown_content = re.sub(r'\\footnote\{(.*?)\}', replace_footnote, self.markdown_content)

    if self.footnotes:
      self.markdown_content += "\n\n## Footnotes\n"
      for number, text in self.footnotes.items():
        self.markdown_content += f"[^{number}]: {text}\n"

  def get_entry(self, key):
    for entry in self.bib_database.entries:
      if key == entry.get("ID"):
        if key not in self.bibliography_keys:
            self.bibliography_keys.append(key)
        return entry
    
    print(f"Warning: Key '{key}' not found in bibliography entries.")
    return None
  
  def extract_last_names(self, authors_field):
    # Split the authors by "and" to handle multiple authors
    authors = [author.strip() for author in authors_field.split(' and ')]

    last_names = []
    for author in authors:
        # Handle "Last, First" format
        if ',' in author:
            last_name = author.split(',')[0].strip()
        else:
            # Handle "First Last" format by assuming the last word is the last name
            last_name = author.split()[-1].strip()
        last_names.append(last_name)

    if len(last_names) > 1:
      return ', '.join(last_names[:-1]) + ' and ' + last_names[-1]
    else:
      return last_names[0]

  def handle_bibliography(self):

    def replace_citep(match):
      keys = [key.strip() for key in match.group(1).split(',')]
      citations = []
      for key in keys:
        entry = self.get_entry(key)
        if entry:
          citations.append(f"{self.extract_last_names(entry.get('author', 'Unknown Author'))} {entry.get('year', 'n.d.')}")
      return '(' + '; '.join(citations) + ')'

    def replace_citet(match):
      keys = [key.strip() for key in match.group(1).split(',')]
      citations = []
      for key in keys:
        entry = self.get_entry(key)
        if entry:
          citations.append(f"{self.extract_last_names(entry.get('author', 'Unknown Author'))} ({entry.get('year', 'n.d.')})")
      return '; '.join(citations)

    with open(self.bib_file, errors='replace') as bibtex_file:
      self.bib_database = bibtexparser.load(bibtex_file)

    self.markdown_content = re.sub(r'\\citep\{(.*?)\}', replace_citep, self.markdown_content)
    self.markdown_content = re.sub(r'\\citet\{(.*?)\}', replace_citet, self.markdown_content)
  
  def append_bibliography(self):

    def format_apsa_entry(entry):
      """Format a BibTeX entry in APSA style for Markdown."""
      entry_type = entry.get('ENTRYTYPE', '').lower()
      author = entry.get('author', 'No Author').replace(' and ', ', ')
      year = f"({entry.get('year', 'n.d.')})"
      title = entry.get('title', 'Untitled')

      if entry_type == 'article':
          journal = entry.get('journal', '')
          volume = entry.get('volume', '')
          issue = entry.get('number', '')
          pages = entry.get('pages', '')
          formatted_entry = f"{author} {year}. \"{title}.\" *{journal}* {volume}({issue}): {pages}."

      elif entry_type == 'book':
          publisher = entry.get('publisher', '')
          formatted_entry = f"{author} {year}. *{title}*. {publisher}."

      elif entry_type == 'inproceedings':
          booktitle = entry.get('booktitle', '')
          pages = entry.get('pages', '')
          formatted_entry = f"{author} {year}. \"{title}.\" In *{booktitle}*, pp. {pages}."

      else:
          formatted_entry = f"{author} {year}. *{title}*."

      return formatted_entry
    
    self.markdown_content += "\n\n## References\n"

    for key in self.bibliography_keys:
      entry = self.get_entry(key)
      if entry:
        self.markdown_content += format_apsa_entry(entry) + '\n\n'


  def handle_newcommands(self):

    def extract_newcommands(self, latex_text):
      # Regular expression to match \newcommand definitions
      newcommand_pattern = re.compile(r'\\newcommand{\\(\w+)}\s*\[.*?\]\s*{(.*?)}|\\newcommand{\\(\w+)}\s*{(.*?)}', re.DOTALL)
      
      matches = newcommand_pattern.findall(latex_text)
      
      for match in matches:
        # Extract the command and its body, with support for optional arguments
        if match[0]:
          command = match[0]
          replacement = match[1]
          self.commands[command] = self.create_replacement_function(replacement)
        else:
          command = match[2]
          replacement = match[3]
          self.commands[command] = self.create_replacement_function(replacement)
      
      # Remove the \newcommand definitions from the document to avoid clutter
      latex_text = re.sub(r'\\newcommand{\\\w+}.*?}', '', latex_text)
      
      return latex_text
    
    def create_replacement_function(self, replacement):
      # Create the replacement logic for each \newcommand (for single arguments)
      return lambda arg: replacement.replace('#1', arg)
    
    self.markdown_content = self.extract_newcommands(self.markdown_content)
    
    for command, replacement in self.commands.items():
      self.markdown_content = re.sub(rf'\\{command}\s*{{(.*?)}}', replacement, self.markdown_content)

    