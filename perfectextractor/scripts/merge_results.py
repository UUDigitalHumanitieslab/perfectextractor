import csv
import os

# This short script can be used to merge results if there are
# multiple alignment files between the total set of languages.
# This happens quite frequently in the OpenSubtitles corpus

IN_FILE = 'data/nl-nl.csv'
WINDOW = 4

header = []
merge = dict()
with open(IN_FILE, 'rb') as f:
    csv_reader = csv.reader(f, delimiter=';')
    for n, row in enumerate(csv_reader):
        # Save header row, than skip
        if n == 0:
            header = row
            continue

        # Retrieve the sentence number and allow a window for matching
        merged = False
        sentence_number = int(row[3].split('.')[0])
        for i in range(sentence_number - WINDOW, sentence_number + WINDOW + 1):
            # Create a key for this row
            key = row[2] + '|' + str(i)

            # Check if this key is in the merge-dict, if so, replace all empty values
            if key in merge:
                for j, v in enumerate(merge[key]):
                    if not v:
                        merge[key][j] = row[j]

                merged = True
                break

        # If not, add this as a new pair in the merge-dict
        if not merged:
            key = row[2] + '|' + str(sentence_number)
            merge[key] = row

# Output the merge-dict to a .csv-file
out = os.path.splitext(IN_FILE)[0] + '-merged.csv'
with open(out, 'wb') as f:
    f.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
    csv_writer = csv.writer(f, delimiter=';')

    csv_writer.writerow(header)
    for v in merge.values():
        csv_writer.writerow(v)
