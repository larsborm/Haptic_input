#Author: Lars Borm
#Date: 1 - September - 2017
#Description: Code to control a Haptic input device that relays digital data to the user via touch.


###########################################################################################
import sys

#SainSmart 16 relay board with USB HID control from here: 
#https://github.com/tatobari/hidrelaypy/blob/master/hidrelay.py
sys.path.insert(0, '/home/larsborm/Documents/Haptic_input/hidrelaypy-master/')
#If you get permission error on Ubuntu, add your username to the dailout group:
# sudo usermod -a -G dialout larsborm
import hidrelay_LB
#Dependencies: pyusb
import time
import numpy as np
import random
import csv
import os.path


###########################################################################################

class HapticInput:
    '''
    Class to give haptic inupt to user, using solonoid accuators.
    
    Dependencies: pyusb
    If you encounter permission issues on Ubuntu (and similar presumably)
    Add your username to the dailout group to gain permission:
    sudo usermod -a -G dialout <username>
    
    '''
    #Initiate and connect to Sainsmart 16 relay board with USB HID
    # From: https://github.com/tatobari/hidrelaypy/blob/master/hidrelay.py
    # Which is based on: https://github.com/mvines/relay
    
    def __init__(self):
        self.relay = hidrelay_LB.HIDRelay(verbose=False)
        #Alphabet
        self.braille_numbers ={ 'z':[0,0,0,0],
                              0: [0,1,1,1], '0': [0,1,1,1],
                              1: [1,0,0,0], '1': [1,0,0,0],
                              2: [1,0,1,0], '2': [1,0,1,0],
                              3: [1,1,0,0], '3': [1,1,0,0],
                              4: [1,1,0,1], '4': [1,1,0,1],
                              5: [1,0,0,1], '5': [1,0,0,1],
                              6: [1,1,1,0], '6': [1,1,1,0],
                              7: [1,1,1,1], '7': [1,1,1,1],
                              8: [1,0,1,1], '8': [1,0,1,1],
                              9: [0,1,1,0], '9': [0,1,1,0]}

        self.set_empty()
        time.sleep(0.5)
        self.set_full()
        time.sleep(0.5)
        self.set_empty()
        print 'Ready\n\n'
    
    ###########################################################################################
    #Low level functions
    ###########################################################################################

    #Message construction
    def create_braille(self, number, show_zero=False):
        '''
        Create corresponding Braille pattern for four numbers.
        Each number is made up out of four points following Braille.
        First number in top left corner, second top right etc.
        If number is smaler than 4 digits, padding on the left:
        12 --> [0, 0, 1, 2] which can optionally be displayed.
        Input:
        `number`(int/list): Either an integer with max 4 digits or a 
            list with max four one digit numbers. Like [1,2,3,4]
            Only positive numbers allowed.
        `show_zero`(bool): If True, the braille version of zero will be
            used for the added leading zeros. [0,1,1,1]. Else: [0,0,0,0]
            If leading zeros are specified in the input they will be 
            displayed
        Output:
            4 by 4 numpy array containing four digits as braille numbers

        '''
        #Convert number (int/list) to list of string 
        if type(number) == int:
            if number<0:
                raise KeyError('Error, invalid input: "{}". Input can not be negative'.format(number))
            number = [d for d in str(number)]
            for i in range(4-len(number)):
                if show_zero == True:
                    number.insert(0, '0')
                else:
                    number.insert(0, 'z')

        if type(number) == list:
            number = [str(d) for d in number]
            for i in range(4-len(number)):
                if show_zero == True:
                    number.insert(0, '0')
                else:
                    number.insert(0, 'z')

        #Check format
        if len(number) > 4:
            raise KeyError ('Error, input: "{}" is too long. Max 4 digits'.format(number))

        for i in number:
            if len(i)>1 or i<0:
                print 'Input creat_pattern function: {}'.format(number)
                raise KeyError ('Error, invalid input: "{}". Only single positive digits allowed'.format(i))

        #Convert to braille
        number_braille = []
        for i in number:
            number_braille.append(self.braille_numbers[i])

        #Construct pattern
        template = [[0,0,0,0],
                    [0,0,0,0],
                    [0,0,0,0],
                    [0,0,0,0]]

        template[0] = [number_braille[0][0], number_braille[0][1], 
                       number_braille[1][0], number_braille[1][1]]
        template[1] = [number_braille[0][2], number_braille[0][3], 
                       number_braille[1][2], number_braille[1][3]]
        template[2] = [number_braille[2][0], number_braille[2][1], 
                       number_braille[3][0], number_braille[3][1]]
        template[3] = [number_braille[2][2], number_braille[2][3], 
                       number_braille[3][2], number_braille[3][3]]

        pattern = np.array(template)
        return pattern
    
    
    def create_binary(self, number):
        """
        Convert number to binary and format in 4x4 array.
        (1 is at rtop right corner.)
         Output:
                4 by 4 numpy array containing the numer in binary

        """
        if not (0 <= number <= 65535 and type(number) == int):
            raise ValueError ('Binary input number must be an integer between 0 and 65535, not: {}'.format(number))
      
        pattern = np.flipud(np.array([int(i) for i in'{0:016b}'.format(number)]).reshape(4,4))
        return pattern

    #Set pattern
    def set_pattern(self, pattern): 
        """
        Switch relays on/off acording to pattern.
        Input:
        `pattern`(list/array): 4 by 4 array of zeros and ones. Eiter numpy array
            or a list of 4 sub-lists with length 4.
        (Will work for different sizes of arrays)

        """
        for ir, row in enumerate(pattern):
            for ic, col in enumerate(row):
                relay_n = ir*len(row) + ic
                self.relay.set(relay_n, bool(col))
                
    
    def set_relay(self, relay_n, on_off):
        
        self.relay.set(relay_n, on_off)
        
    #####################################################################################################
    #High level functions
    #####################################################################################################
    
    def set_braille(self, number):
        """
        Create braille 2x2 pattern with max 4 digits.
        Each number is made up out of four points following Braille.
        First number in top left corner, second top right etc.
        If number is smaler than 4 digits, padding on the left:
        12 --> [0, 0, 1, 2]
        Input:
        `number`(int/list): Either an integer with max 4 digits or a 
            list with max four one digit numbers. Like [1,2,3,4]
            Only positive numbers allowed.

        """
        self.set_pattern(self.create_braille(number))
    
    def set_binary(self, number):
        """
        Convert number to binary (max 16 bits: 65535)
        1 will be on relay 3
        Input:
            `number`(int): Number between 0 and 65535 (including)
        
        """
        self.set_pattern(self.create_binary(number))
    
    def set_empty(self):
        """
        switch all relays off.

        """
        pattern = [[0,0,0,0],
                   [0,0,0,0],
                   [0,0,0,0],
                   [0,0,0,0]]
        self.set_pattern(pattern)
        
    def set_full(self):
        """
        Swich all relays on.

        """
        pattern = [[1,1,1,1],
                   [1,1,1,1],
                   [1,1,1,1],
                   [1,1,1,1]]
        self.set_pattern(pattern)

    #####################################################################################################
    #Training functions
    #####################################################################################################
    
    def performace_logfile(self):
        """
        Creates a performace log file with the name: 'performance_log.csv'

        """
        if not os.path.isfile('performance_log.csv'):
            with open('performance_log.csv', 'w') as performance_log:
                writer = csv.writer(performance_log)
                writer.writerow(['date', 'encoding', 'trials_completed', 'correct', 'percentage correct %'])
            
    def performance_logger(self, encoding, trials, correct):
        """
        Writes: 'time', 'number of trials', 'number correct' and 'percentage correct' to 
        the 'performance_log.csv' file

        """
        with open('performance_log.csv', 'a') as performance_log:
            writer = csv.writer(performance_log)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M"), encoding, trials, correct,
                             (float(correct)/float(trials))*100])
    
    def train_braille(self, number_of_digits=4):
        """
        Train to recognize braille patterns.
        Input:
        `number_of_digits`(int): Number o digits to train with. [1-4]

        """
        print number_of_digits
        if number_of_digits>4 or number_of_digits<0 or type(number_of_digits) != int:
            raise ValueError ('number_of_digits should be 1, 2, 3 or 4')
        
        self.performace_logfile()
        n_trials = 0
        n_correct = 0
        try:
            while True:
                n_trials +=1
                number = random.randint(0, int('9'*number_of_digits))
                self.set_braille(number)
                while True:
                    guess = raw_input('Guess the current number: ')
                    try:
                        guess = int(guess)
                        break
                    except ValueError as e:
                        print 'Invalid input'
                if guess == number:
                    print 'Correct!\n\n'
                    n_correct += 1
                else:
                    print 'Wrong, the correct answer is: {}\n\n'.format(number)
                    time.sleep(3)
                self.set_empty()
                time.sleep(1)

        except KeyboardInterrupt:
            self.performance_logger('Braille', n_trials, n_correct)
            print 'Training stopped'
            print 'Out of {} trials, {} were correct.'.format(n_trials, n_correct)
            
    def train_binary(self, number_of_rows=1):
        """
        Train to recognize binary patterns.
        Input:
        `number_of_rows`(int): 

        """
        print number_of_rows
        if number_of_rows>4 or number_of_rows<0 or type(number_of_rows) != int:
            raise ValueError ('number_of_rows should be 1, 2, 3 or 4')
            
        self.performace_logfile()    
        n_trials = 0
        n_correct = 0
        try:
            while True:
                n_trials +=1
                number = random.randint(0, int('1111'*number_of_rows, 2))
                self.set_binary(number)
                while True:
                    guess = raw_input('Guess the current number: ')
                    try:
                        guess = int(guess)
                        break
                    except ValueError as e:
                        print 'Invalid input'
                if guess == number:
                    print 'Correct!\n\n'
                    n_correct += 1
                else:
                    print 'Wrong, the correct answer is: {}\n\n'.format(number)
                    time.sleep(3)
                self.set_empty()
                time.sleep(1)

        except KeyboardInterrupt:
            self.performance_logger('Binary', n_trials, n_correct)
            print 'Training stopped'
            print 'Out of {} trials, {} were correct.'.format(n_trials, n_correct)
            
hi = HapticInput()
