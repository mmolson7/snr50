""" 
    An adaptive task to find the SNR50 for IEEE sentences in a fixed 
    background noise. Noise must be played externally (e.g., from 
    Audition). 

    NOTES:
        1. If you run out of stimuli (i.e., do not reach threshold 
        before the stimuli are exhausted), the routine will end 
        and the data will be saved; however, no values will be 
        calculated.
        2. If you press an unexpected key (i.e., anything other 
        than the numbers 1 - 5 from the numpad only), the response
        will be scored as incorrect and the routine will continue.

        SUBJECT: The subject name or number, using any convention.
        CONDITION: The experimental condition.
        LIST NUMBERS: Number of each list to include in playback. 
            Enter numbers separated by spaces.
        STEP SIZE: The amount to increase/decrease stimulus.
        STARTING LEVEL: The desired starting level in dB.
        NOISE LEVEL (DB): The level in dB of the fixed noise. 
            Note that noise must be played from another device.
        CALIBRATION: Enter "y" or "n" to play the calibration file.
            A sound level meter should be used to record the 
            output level. 
        SLM OUTPUT: The level in dB from the sound level meter 
            when playing the calibration file.

    Written by: Travis M. Moore
    Created: May 18, 2022
    Last edited: May 24, 2022
"""

# Import psychopy tools
import this
from psychopy import core, visual, gui, data, event, prefs
from psychopy.tools.filetools import fromFile, toFile
import psychtoolbox as ptb
prefs.hardware['audioLib'] = ['PTB']
from psychopy import sound # Import "sound" AFTER assigning library!!

# Import published modules
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
from scipy.io import wavfile
import csv

sys.path.append('.\\lib') # Point to custom library file
import tmsignals as ts # Custom library
import importlib 
importlib.reload(ts) # Reload custom module on every run

#################################
#### FOLDER/INPUT MANAGEMENT ####
#################################
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
    expInfo = {'Subject':'999', 'Condition':'Quiet', 'List Numbers':'5 8', 'Step Size':2.0, 'Starting Level': 65.0, 'Noise Level (dB)':70.0, 'Calibration':'n', 'SLM Output':80.0}
expInfo['dateStr'] = data.getDateStr()

dlg = gui.DlgFromDict(expInfo, title='Adaptive SNR50 Task',
                      fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)
else:
    core.quit()

# Reference level for calibration and use with offset
REF_LEVEL = -20.0

###################################
#### BEGIN CALIBRATION ROUTINE ####
###################################
# Calibration routine begins here to avoid writing
# a file when just running calibration
if expInfo['Calibration'] == 'y':
    print('Playing calibration file')
    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    # Normalize between 1/-1
    calStim = ts.doNormalize(calStim, 48000)
    # Set target level
    calStim = ts.setRMS(calStim,REF_LEVEL,eq='n')
    sigdur = len(calStim) / fs
    probe = sound.Sound(value=calStim.T,
        secs=sigdur, stereo=-1, volume=1.0, loops=0, 
        sampleRate=fs, blockSize=4800, preBuffer=-1, 
        hamming=False, startTime=0, stopTime=-1, 
        autoLog=True)
    probe.play()
    core.wait(probe.secs+0.001)
    core.quit()
#################################
#### END CALIBRATION ROUTINE ####
#################################

SLM_OFFSET = expInfo['SLM Output'] - REF_LEVEL
STARTING_LEVEL = expInfo['Starting Level'] - SLM_OFFSET
print("\n")
print("SLM OUTPUT: " + str(expInfo['SLM Output']))
print("-")
print("REF LEVEL: " + str(REF_LEVEL))
print("=")
print("SLM OFFSET: " + str(SLM_OFFSET))
print("\n")
print("Desired starting level: " + str(expInfo['Starting Level']))
print("-")
print("SLM OFFSET: " + str(SLM_OFFSET))
print("=")
print("STARTING LEVEL: " + str(STARTING_LEVEL))
print("\n")

# make a text file to save data
fileName = _thisDir + os.sep + 'data' + os.sep + '%s_%s_%s' % (expInfo['Subject'], expInfo['Condition'], expInfo['dateStr'])
dataFile = open(fileName+'.csv', 'w')
dataFile.write('subject,condition,step_size,num_correct,response,slm_output,slm_cf,raw_level,final_level\n')

##########################
#### STIMULI/PARADIGM ####
##########################
# Assign script-wide variables
#fileList = os.listdir('.\\audio')
# Get list of IEEE sentences
#file_csv = open('.\\sentences\\IEEE.csv')
#data_csv = csv.reader(file_csv)
#sentences = list(data_csv)

# Get lists of written sentences
df = pd.read_csv('.\\sentences\\IEEE-DF.csv')
lists = expInfo['List Numbers'].split()
lists = [int(x) for x in lists]
sentences = df.loc[df['list_num'].isin(lists), 'ieee_text']
print(sentences)

# Get audio files
# NOTE: files must be renames as increasing
# integer values (e.g., 1, 2, 3...)
fileList = os.listdir('.\\audio\\IEEE')
x = [x[:-4] for x in fileList] # strip off '.wav'
fileList = sorted(x, key = int) # sort strings as int
fileList = [x+'.wav' for x in fileList] # add '.wav' back
sentence_nums = df.loc[df['list_num'].isin(lists), 'sentence_num']
sentence_nums = np.array(sentence_nums)
#print(sentence_nums)
fileList = np.array(fileList)
fileList = fileList[sentence_nums]
#print(fileList)

# Create staircase handler
staircase = data.StairHandler(startVal = STARTING_LEVEL,
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

# Create text object and update with variables defined above
text_stim = visual.TextStim(win, text="", font='Arial', pos=(0.0, 0.0),
                        color=(-1, -1, -1), units='pix', height=72)
win.flip()

# Display instructions and wait
instr_text.draw()
win.flip() # to show newly-drawn stimuli

# Pause until keypress
event.waitKeys()

# Initialize variables
thisResp = None

#########################
#### BEGIN STAIRCASE ####
#########################
# Present stimuli using staircase procedure
counter = -1
for thisIncrement in staircase:
    print("Raw Level: %f " % thisIncrement)
    print("Corrected Level: " + str(thisIncrement+SLM_OFFSET) + " dB")

    counter += 1 # for cycling through list of audio file names

    # Initialize stimulus
    try:
        [fs, myTarget] = wavfile.read('audio\\IEEE\\' + fileList[counter])
    except:
        dataFile.close()
        staircase.saveAsPickle(fileName)
        feedback1 = visual.TextStim(
            win, pos=[0,+3],
            text = 'You ran out of lists! The data collected so far have been saved, ' +
                'but you will have to calculate SNR50 manually.')

        feedback1.draw()
        win.flip()
        event.waitKeys() # wait for participant to respond

        win.close()
        core.quit()
    # Normalization between 1 and -1
    myTarget = ts.doNormalize(myTarget,48000)
    #plt.plot(myTarget)
    #plt.show()

    """
    # Present calibration stimulus for testing
    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    myTarget = calStim[:int(len(calStim)/2)] # truncate
    # Normalize between +1/-1
    myTarget = ts.doNormalize(myTarget,48000)
    """

    # Set target level (taken from thisIncrement on each loop iteration)
    myTarget = ts.setRMS(myTarget,thisIncrement,eq='n')
    #plt.plot(myTarget)
    #plt.ylim([-1,1])
    #plt.show()
    #plt.plot(myTarget)
    #plt.show()

    ###################################
    ###### STIMULUS PRESENTATION ######
    ###################################
    # Show stimulus text
    # extract one sentence from list as string
    theText = ''.join(sentences.iloc[counter])
    words = theText.split()
    text_stim.setText('Wait...\n\n' + theText)
    text_stim.setHeight(25)
    text_stim.draw()
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
    text_stim.setText('Respond\n\n' + theText)
    text_stim.setHeight(25)
    text_stim.draw()
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
            else:
                thisKey = int(999)
                thisResp = 999 # make this an int to avoid the program crashing
        event.clearEvents() # clear other (e.g., mouse events: they clog the buffer)

        # Assign pass/fail
        if thisResp == -1: # Must use 1/-1 for psychopy logic
            print("Fail")
        elif thisResp == 1: # Must use 1/-1 for psychopy logic
            print("Pass")
        else: 
            print("Invalid Response!")

        # Update staircase handler and write data to file
        staircase.addData(thisResp)
        dataFile.write('%s,%s,%f,%i,%i,%f,%f,%f,%f\n' %  (expInfo['Subject'], 
            expInfo['Condition'], expInfo['Step Size'], thisKey, thisResp, 
            expInfo['SLM Output'], SLM_OFFSET, thisIncrement, thisIncrement+SLM_OFFSET))
        core.wait(1)
#######################
#### END STAIRCASE ####
#######################


###############################
#### DATA WRITING/FEEDBACK ####
###############################
approxThreshold = np.average(staircase.reversalIntensities[-2:])
approxThresholdCorrected = approxThreshold+SLM_OFFSET
snr50 = (approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB)']
dataFile.write('SNR50: ' + str(snr50) + ' dB')
core.wait(0.5)
dataFile.close()
staircase.saveAsPickle(fileName)
staircase.saveAsExcel(fileName + '.xlsx', sheetName='trials')

# give feedback in the command line 
print('reversals:')
print(staircase.reversalIntensities)
print('Average Speech Performance (raw): %.3f' % (approxThreshold))
print('Average Speech Performance (corrected ): %.3f' % (approxThreshold+SLM_OFFSET))
print('Noise Level (dB): %.3f' % (expInfo['Noise Level (dB)']))
print('SNR50:' + str(snr50) + 'dB')

#  Give some on-screen feedback
feedback1 = visual.TextStim(
    win, pos=[0,+3],
    text = 'Average Speech Performance: ' + str(approxThresholdCorrected) + ' dB' +
        '\nNoise Level: ' + str(expInfo['Noise Level (dB)']) + ' dB' +
        '\n\nSNR50: ' + str(snr50) + ' dB')

feedback1.draw()
win.flip()
event.waitKeys() # wait for participant to respond

win.close()
core.quit()
