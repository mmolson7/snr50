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
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from scipy.io import wavfile
import csv
from pydub import AudioSegment, effects

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
    expInfo = {'Subject':'999', 'Condition':'Quiet', 'Step Size':2.0, 'Starting Level': 65.0, 'Noise Level (dB SPL)':70.0, 'Calibration':'n', 'SLM Output':30.0}
expInfo['dateStr'] = data.getDateStr()

dlg = gui.DlgFromDict(expInfo, title='Adaptive SNR50 Task',
                      fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)
else:
    core.quit()


# Reference level for calibration and use with offset
REF_LEVEL = -10.0

# Calibration routine
if expInfo['Calibration'] == 'y':
    print('Playing calibration file')
    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    # Set target level (taken from thisIncrement on each loop iteration)
    calStim = ts.setRMS(calStim,REF_LEVEL,eq='n')
    calStim = calStim/np.max(calStim)
    sigdur = len(calStim) / fs
    probe = sound.Sound(value=calStim.T,
        secs=sigdur, stereo=-1, volume=1.0, loops=0, 
        sampleRate=fs, blockSize=4800, preBuffer=-1, 
        hamming=False, startTime=0, stopTime=-1, 
        autoLog=True)
    probe.play()
    core.wait(probe.secs+0.001)
    core.quit()

SLM_OFFSET = expInfo['SLM Output'] - REF_LEVEL
STARTING_LEVEL = expInfo['Starting Level'] - SLM_OFFSET

# make a text file to save data
fileName = _thisDir + os.sep + 'data' + os.sep + '%s_%s_%s' % (expInfo['Subject'], expInfo['Condition'], expInfo['dateStr'])
dataFile = open(fileName+'.csv', 'w')
dataFile.write('subject,condition,step_size,num_correct,response,slm_output,slm_cf,raw_level,final_level\n')

# Assign script-wide variables
fileList = os.listdir('.\\audio')
# Get list of IEEE sentences
file_csv = open('.\\sentences\\IEEE.csv')
data_csv = csv.reader(file_csv)
sentences = list(data_csv)

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

# Present stimuli using staircase procedure
counter = -1
for thisIncrement in staircase:
    print("Raw Level: %f " % thisIncrement)
    print("Corrected Level: " + str(thisIncrement+SLM_OFFSET) + " dB SPL")

    counter += 1
    myPath = 'audio\\'
    myFile = fileList[counter]
    myFilePath = myPath + myFile
    [fs, myTarget] = wavfile.read(myFilePath)
    # Set target level (taken from thisIncrement on each loop iteration)

    # Normalization between 1 and -1, but it's sooooooo slow
    #myTarget = [2*(x-np.min(myTarget)) / (np.max(myTarget)-(np.min(myTarget)))-1 for x in myTarget]
    #myTarget = myTarget/np.max(myTarget) # Fast normalization with 1 as max but no min

    # 1/-1 in for fast processing
    # myTarget = myTarget-np.min(myTarget)
    # denom = np.max(myTarget) - np.min(myTarget)
    # myTarget = myTarget/denom
    # myTarget = myTarget * 2
    # myTarget = myTarget -1

    myTarget = ts.doNormalize(myTarget,48000)
    plt.plot(myTarget)
    plt.show()

    myTarget = ts.setRMS(myTarget,thisIncrement,eq='n')




    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    # Set target level (taken from thisIncrement on each loop iteration)
    myTarget = calStim[:int(len(calStim)/2)]
    myTarget = myTarget/np.max(myTarget)
    #myTarget = ts.setRMS(myTarget,thisIncrement-3.5,eq='n')
    # Normalize between +1/-1
    myTarget = ts.doNormalize(myTarget,48000)
    plt.plot(myTarget)
    plt.show()
    myTarget = ts.setRMS(myTarget,thisIncrement,eq='n')



    ###### STIMULUS PRESENTATION ######
    # Show stimulus text
    theText = ''.join(sentences[counter+1])
    #text_stim.setText(theText[4:-1])
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
approxThreshold = np.average(staircase.reversalIntensities[-2:])
dataFile.write('SNR50: ' + str((approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB SPL)']) + ' dB SPL')
core.wait(0.5)
dataFile.close()
staircase.saveAsPickle(fileName)
staircase.saveAsExcel(fileName + '.xlsx', sheetName='trials')

# give feedback in the command line 
print('reversals:')
print(staircase.reversalIntensities)
approxThreshold = np.average(staircase.reversalIntensities[-2:])
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
