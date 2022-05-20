""" 
    An adaptive task to find the SNR50 for IEEE 
    sentences in a fixed background noise. 

    Subject: The subject name or number, using any convention
    Condition: The experimental condition
    Step Size: The amount to increase/decrease stimulus
    Noise Level (dB SPL): The level in dB SPL of the fixed noise. 
        Note that noise must be played from another device.
    Calibration: Enter "y" or "n" to play the calibration file.
        A sound level meter should be used to record the 
        output level. 
    SLM Output: The level in dB SPL from the sound level meter 
        when playing the calibration file.

    Written by: Travis M. Moore
    Created: May 18, 2022
    Last edited: May 19, 2022
"""

# Import psychopy tools
import this
from psychopy import core, visual, gui, data, event, prefs
from psychopy.tools.filetools import fromFile, toFile
import psychtoolbox as ptb
prefs.hardware['audioLib'] = ['PTB']
from psychopy import sound # Import "sound" AFTER assigning library!!

# Import published modules
import numpy, random
import pandas as pd
import os
import sys
from scipy.io import wavfile
import csv

sys.path.append('.\\lib') # Point to custom library file
import tmsignals as ts # Custom library
import importlib 
importlib.reload(ts) # Reload custom module on every run

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Check for existing data folder
if os.path.isdir(_thisDir + os.sep + 'data' + os.sep):
    print("Found data folder.")
else:
    print("No data folder found; creating one.")
    os.mkdir(_thisDir + os.sep + 'data' + os.sep)
    isdir = os.path.isdir(_thisDir + os.sep + 'data' + os.sep)
    if isdir:
        print("Data folder created successfully.")
    else:
        print("Problem creating data folder.")

# Search for previous parameters file
try:
    expInfo = fromFile('lastParams.pickle')
except:
    expInfo = {'Subject':'999', 'List Numbers': '1 2', 'Condition':'Quiet', 'Step Size':2.0, 'Noise Level (dB SPL)':70.0, 'Calibration':'n', 'SLM Output':30.0}
expInfo['dateStr'] = data.getDateStr()

dlg = gui.DlgFromDict(expInfo, title='Adaptive SNR50 Task',
                      fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)
else:
    core.quit()

# print(expInfo['List Numbers'])
# print(type(expInfo['List Numbers']))
# print(expInfo['List Numbers'])


# Calibration routine
if expInfo['Calibration'] == 'y':
    print('Playing calibration file')
    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    # Set target level (taken from thisIncrement on each loop iteration)
    calTone = ts.setRMS(calStim,-50,eq='n')
    sigdur = len(calTone) / fs
    probe = sound.Sound(value=calTone.T,
        secs=sigdur, stereo=-1, volume=1.0, loops=0, 
        sampleRate=fs, blockSize=4800, preBuffer=-1, 
        hamming=False, startTime=0, stopTime=-1, 
        autoLog=True)
    probe.play()
    core.wait(probe.secs+0.001)
    core.quit()


# make a text file to save data
fileName = _thisDir + os.sep + 'data' + os.sep + '%s_%s_%s' % (expInfo['Subject'], expInfo['Condition'], expInfo['dateStr'])
dataFile = open(fileName+'.csv', 'w')
dataFile.write('subject,condition,step_size,num_correct,response,slm_output,slm_cf,raw_level,final_level\n')

# Assign script-wide variables
refLevel = -60.0
SLM_OFFSET = expInfo['SLM Output'] - refLevel
# Get list of audio IEEE sentences - deprecated
#file_csv = open('.\\sentences\\IEEE.csv')
#data_csv = csv.reader(file_csv)
#sentences = list(data_csv)
# Get audio sentences from specified lists
df = pd.read_csv('.\\sentences\\IEEE-DF.csv')
lists = expInfo['List Numbers'].split()
lists = [int(x) for x in lists]
sentences = df.loc[df['list_num'].isin(lists), 'ieee_text']
# Get list of written sentences
fileList = os.listdir('.\\audio')
sentence_nums = df.loc[df['list_num'].isin(lists), 'sentence_num']
fileList = fileList[sentence_nums[0]:sentence_nums[-1]+1]


# Create staircase handler
staircase = data.StairHandler(startVal = refLevel,
                              stepType = 'lin',
                              stepSizes=[expInfo['Step Size']],
                              nup=1,
                              nDown=1,
                              nTrials=2,
                              nReversals=3,
                              applyInitialRule=True,
                              minVal=-100,
                              maxVal=0)

# create window and text objects
win = visual.Window([800,600], screen=0, monitor='testMonitor', 
                    color=(0,0,0), fullscr=False, units='pix',
                    allowGUI=True) 
                    # testMonitor means default visual parameters
                    # allowGUI gives outer menu on window
instr_text = visual.TextStim(win, pos=[0,+3], 
    height=25, color=(-1,-1,-1),
    text='Enter the number of correctly repeated words.')
respond_text = visual.TextStim(win, pos=[0,+3], text='Respond',
    height=50, color=(-1,-1,-1))
#inter1_text = len(myTarget)
# Create text object and update with variables defined above
text_stim = visual.TextStim(win, text="", pos=(0.0, 0.0),
                        color=(-1, -1, -1), units='pix', height=72)
win.flip()

# Create buttons
button1 = visual.ButtonStim(win,
    text='',pos=(0,0),size=[.2,.1],anchor='center')
button2 = visual.ButtonStim(win,
    text='',pos=(0,-26),size=[.2,.1],anchor='center')
button3 = visual.ButtonStim(win,
    text='',pos=(0,-52),size=[.2,.1],anchor='center')

# Display instructions and wait
instr_text.draw()
win.flip() # to show newly-drawn stimuli

# Pause until keypress
event.waitKeys()

# Initialize variables
thisResp = None

# Present stimuli using staircase procedure
counter = -1
for thisIncrement in staircase:
    print("Raw Level: %f " % thisIncrement)
    print("Corrected Level: " + str(thisIncrement+SLM_OFFSET) + " dB SPL")

    counter += 1
    myPath = 'audio\\'
    myFile = fileList[counter]
    myFilePath = myPath + myFile

    print(myFilePath)
    [fs, myTarget] = wavfile.read(myFilePath)
    print('loaded audio')
    # Set target level (taken from thisIncrement on each loop iteration)
    myTarget = ts.setRMS(myTarget,thisIncrement,eq='n')

    ###### STIMULUS PRESENTATION ######
    # Show stimulus text
    theText = ''.join(sentences.iloc[counter])
    print(theText)
    #text_stim.setText(theText[4:-1])
    #text_stim.setText('Wait...\n\n' + theText)
    #text_stim.setHeight(25)
    #text_stim.draw()
    words = theText.split()
    print(words)
    button1.text = words[0]
    button1.draw()
    button2.text = words[1]
    button2.draw()
    button3.text = words[2]
    button3.draw()
    
    
    
    win.flip()

    # Play stimulus
    sigdur = len(myTarget) / fs
    probe = sound.Sound(value=myTarget.T,
        secs=sigdur, stereo=-1, volume=1.0, loops=0, 
        sampleRate=fs, blockSize=4800, preBuffer=-1, 
        hamming=False, startTime=0, stopTime=-1, 
        autoLog=True)
    probe.play()
    core.wait(probe.secs+0.001)
    
    # Clear the window
    text_stim.setText(" ")
    text_stim.draw()
    win.flip()

    # Post-observation wait period
    core.wait(0.01)
    
    # Prompt the user to respond
    #text_stim.setText('Respond\n\n' + theText)
    text_stim.setHeight(25)
    text_stim.draw()

    button1.text = words[0]
    button1.draw()
    button2.text = words[1]
    button2.draw()
    button3.text = words[2]
    button3.draw()

    win.flip()

    # Get response
    thisResp=None
    while thisResp==None:
        allKeys=event.waitKeys()
        for thisKey in allKeys:
            if thisKey in ['num_1','num_2','num_3','num_4']: 
                thisResp = -1
                thisKey = int(thisKey[-1])
            elif thisKey == 'num_5':
                thisResp = 1
                thisKey = int(thisKey[-1])
            elif thisKey in ['q', 'escape']:
                core.quit() # abort experiment
            #else: thisResp = 999 # make this an int to avoid the program crashing
        event.clearEvents() # clear other (e.g., mouse events: they clog the buffer)

        # Assign pass/fail
        if thisResp == -1: # Must use 1/-1 for psychopy logic
            print("Fail")
        elif thisResp == 1: # Must use 1/-1 for psychopy logic
            print("Pass")
        else: 
            print("Response not recorded!")

        # Update staircase handler and write data to file
        staircase.addData(thisResp)
        dataFile.write('%s,%s,%f,%i,%i,%f,%f,%f,%f\n' %  (expInfo['Subject'], 
            expInfo['Condition'], expInfo['Step Size'], thisKey, thisResp, 
            expInfo['SLM Output'], SLM_OFFSET, thisIncrement, thisIncrement+SLM_OFFSET))
        core.wait(1)

# Staircase has ended
approxThreshold = numpy.average(staircase.reversalIntensities[-2:])
dataFile.write('SNR50: ' + str((approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB SPL)']) + ' dB SPL')
core.wait(0.5)
dataFile.close()
staircase.saveAsPickle(fileName)
staircase.saveAsExcel(fileName + '.xlsx', sheetName='trials')

# give feedback in the command line 
print('reversals:')
print(staircase.reversalIntensities)
approxThreshold = numpy.average(staircase.reversalIntensities[-2:])
print('Mean of final 2 reversals = %.3f' % (approxThreshold+SLM_OFFSET))
print('Mean of 2 reversals = %.3f' % (approxThreshold))
print('SNR50:' + str(thisIncrement-expInfo['Noise Level (dB SPL)']) + 'dB SPL')

#  Give some on-screen feedback
feedback1 = visual.TextStim(
    win, pos=[0,+3],
    #text='Mean of final 2 reversals = %.3f' % (approxThreshold+SLM_OFFSET))
    text = 'Average Speech Performance: ' + str(approxThreshold+SLM_OFFSET) + ' dB SPL' +
        '\nNoise Level: ' + str(expInfo['Noise Level (dB SPL)']) + ' dB SPL' +
        '\n\nSNR50: ' + str((approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB SPL)']) + ' dB SPL')

feedback1.draw()
win.flip()
event.waitKeys() # wait for participant to respond

win.close()
core.quit()
