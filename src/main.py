from converter import Converter
import argparse

def main():

  parser = argparse.ArgumentParser(description="Convert LaTeX to Word via Markdown.")

  parser.add_argument("filename", help="Input LaTeX file")
  parser.add_argument("-w", "--write-word", action="store_true", help="Write output to Word")
  parser.add_argument("-b", "--bibliography", metavar="BIB_FILE", help="BibTeX file for citations")

  args = parser.parse_args()

  write_word = args.write_word
  bibliography_file = args.bibliography
  filename = args.filename

  with open(filename + ".tex", "r") as file:
    latex_content = file.read()

  converter = Converter(latex_content, bibliography_file)

  converter.process()

  with open(filename + ".md", "w") as file:
    file.write(converter.get_markdown_content())

  if write_word:
    with open(filename + ".docx", "wb") as docx_file:
      docx_file.write(converter.get_word_content())

if __name__ == "__main__":
  main()