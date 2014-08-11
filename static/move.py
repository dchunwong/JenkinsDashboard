import os

directories = os.listdir('.')
for dir in directories:
	if dir[0] == '.' or '.py' in dir:
		continue
	files = os.listdir('./'+dir)
	for file in files:
		if 'skip.txt' in file:
			continue
		os.renames(dir+'/'+file, dir+'/HTML/'+file)
