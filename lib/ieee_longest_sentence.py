import pandas as pd
import numpy as np

df = pd.read_csv('.\\sentences\\IEEE-DF.csv')
df2 = df['ieee_text']

word_count = []

counter = 0
for sentence in df2:
    x = ''.join(df2[counter])
    words = x.split()
    #print(words)
    #print(len(words))
    word_count.append(len(words))
    counter += 1
print(word_count)
print(max(word_count))

