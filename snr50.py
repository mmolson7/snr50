""" 
    An adaptive task to find the SNR50 for IEEE 
    sentences in a fixed background noise. 

    Subject: The subject name or number, using any convention
    Condition: The experimental condition
    Step Size: The amount to increase/decrease stimulus
    Noise Level (dB): The level in dB of the fixed noise. 
        Note that noise must be played from another device.
    Calibration: Enter "y" or "n" to play the calibration file.
        A sound level meter should be used to record the 
        output level. 
    SLM Output: The level in dB from the sound level meter 
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
#from pydub import AudioSegment, effects

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
    expInfo = {'Subject':'999', 'Condition':'Quiet', 'Step Size':2.0, 'Starting Level': 65.0, 'Noise Level (dB)':70.0, 'Calibration':'n', 'SLM Output':30.0}
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
    [fs, myTarget] = wavfile.read('audio\\' + fileList[counter])
    # Normalization between 1 and -1
    myTarget = ts.doNormalize(myTarget,48000)

    # Present calibration stimulus for testing
    [fs, calStim] = wavfile.read('calibration\\IEEE_cal.wav')
    myTarget = calStim[:int(len(calStim)/2)] # truncate
    # Normalize between +1/-1
    myTarget = ts.doNormalize(myTarget,48000)
    plt.plot(myTarget)
    plt.ylim([-1,1])
    plt.show()

    # Set target level (taken from thisIncrement on each loop iteration)
    myTarget = ts.setRMS(myTarget,thisIncrement,eq='n')
    plt.plot(myTarget)
    plt.ylim([-1,1])
    plt.show()

    ###################################
    ###### STIMULUS PRESENTATION ######
    ###################################
    # Show stimulus text
    # extract one sentence from list as string
    theText = ''.join(sentences[counter+1]) 
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
#######################
#### END STAIRCASE ####
#######################


###############################
#### DATA WRITING/FEEDBACK ####
###############################
approxThreshold = np.average(staircase.reversalIntensities[-2:])
dataFile.write('SNR50: ' + str((approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB)']) + ' dB')
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
print('SNR50:' + str(thisIncrement-expInfo['Noise Level (dB)']) + 'dB')

#  Give some on-screen feedback
feedback1 = visual.TextStim(
    win, pos=[0,+3],
    text = 'Average Speech Performance: ' + str(approxThreshold+SLM_OFFSET) + ' dB' +
        '\nNoise Level: ' + str(expInfo['Noise Level (dB)']) + ' dB' +
        '\n\nSNR50: ' + str((approxThreshold+SLM_OFFSET)-expInfo['Noise Level (dB)']) + ' dB')

feedback1.draw()
win.flip()
event.waitKeys() # wait for participant to respond

win.close()
core.quit()
