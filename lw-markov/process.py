import markovify
import os
import re
from BeautifulSoup import BeautifulSoup
from markdown import markdown

# Get raw text as string.
dirpath = './markdown-source/'
text = ''
for filename in os.listdir(dirpath):
	filepath = dirpath + filename

	with open(filepath) as f:
		filetext = f.read()
		asciitext = re.sub(r'[^\x00-\x7f]',r'', filetext)
		html = markdown(asciitext)
		text += ''.join(BeautifulSoup(html).findAll(text=True)) + '\n'

# Build the model.
text_model = markovify.Text(text, state_size=2)

# Print five randomly-generated sentences
for i in range(5):
    print(text_model.make_sentence())

# Print three randomly-generated sentences of no more than 140 characters
for i in range(3):
    print(text_model.make_short_sentence(140))
