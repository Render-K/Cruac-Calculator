import PySimpleGUI as sg
from ctypes import windll
import numpy as np
import matplotlib.pyplot as plt

windll.shcore.SetProcessDpiAwareness(1)

class CruacCalculator:
    def __init__(self):
        pass

    def dice(self, sides):
        ''' returns random number between 1 and sides '''
        x = np.random.randint(low=1,high=sides+1)
        return x

    def BBN_dice_roll(self, rolls, pool, sides):
        ''' rolls dice according to BBN system (d10, 10 explodes, 1 crit fail)'''
        dice_output = np.zeros((rolls.size,rolls.max()))
        fail = 0
        succeed_at_cost = 0
        for j in range(rolls.shape[0]):
            for i in range(rolls[j]):
                dice_output[j][i] = self.dice(sides[j])
                if dice_output[j][i] == 10:
                    dice_output[j][i] += self.dice(sides[j])
                elif (dice_output[j][i] == 1) and (i==0) and (j==0):
                    succeed_at_cost_dice = self.dice(sides[j])
                    if ((pool[j] < 8) or (succeed_at_cost_dice < 6)):
                        dice_output[j] = np.zeros(rolls[j])
                        fail = 1
                        return dice_output, fail, succeed_at_cost
                    else:
                        dice_output[j][i] = 1
                        succeed_at_cost = 1
        return dice_output, fail, succeed_at_cost

    def no_of_succcesses(self, dice_input, pool, fail, rolls):
        '''converts dice rolls into successes'''
        successes = np.zeros(dice_input.shape)
        for j in range(successes.shape[0]):
            for i in range(rolls[j]):
                if fail == 1:
                    total_successes = 0
                    return total_successes
                else:
                    successes[j][i] = np.floor((dice_input[j][i]+pool[j]-8)/4)
                if successes[j][i] > 5:
                    successes[j][i] = 5
        total_successes = np.sum(successes)
        return total_successes
        

    def histogram1(self, rolls, pool, succeed, side, repeats, range_dice, dice_rolls, no_bins, fig):
        fails = np.zeros(repeats)
        succeed_at_costs = np.zeros(repeats)
        total_successes = np.zeros(repeats)
        for i in range(repeats):
            dice_rolls, fails[i], succeed_at_costs[i] = self.BBN_dice_roll(rolls, pool, side)
            total_successes[i] = np.sum(self.no_of_succcesses(dice_rolls, pool, fails[i], rolls))
        number_in_bins, bin_edges = np.histogram(total_successes, bins=no_bins, range=range_dice)

        width = (bin_edges[1:] - bin_edges[:-1])
        centre = (bin_edges[1:] + bin_edges[:-1])/2
        #yerr = np.sqrt(number_in_bins)
        s = 100/repeats

        ax = fig.add_subplot(1, 1, 1)

        #percentages of successes/fails/etc
        total_fails = np.count_nonzero(fails)
        total_succeed_at_costs = np.count_nonzero(succeed_at_costs)
        total_succeeds = (total_successes>=succeed).sum()
        msg = ""
        msg += 'Percentage of fails: ' + str(100*total_fails/repeats) + '%' + "\n"
        msg += 'Percentage of succeeds at a cost: ' + str(100*total_succeed_at_costs/repeats) + '%' + "\n"
        msg += 'Percentage of times succeeding threshold: ' + str(100*total_succeeds/repeats) + '%' + "\n"

        #histogram
        hist_label = f'Rolls = {rolls} \nPools = {pool} \nSuccesses needed = {succeed}'
        hist_label += f'\nRepeats = {repeats} \n% successes = {100*total_succeeds/repeats}%'
        hist_label += f'\n% fails = {100*total_fails/repeats}%' 
        
        ax.bar(centre, number_in_bins*s, align='center', width=width*0.9, color='g', label=hist_label)
        ax.set_title('Distribution of outcome of rolls for BBN')
        ax.legend()
        ax.set_xlabel('No. of successes')
        ax.set_ylabel('Chance [%]')

        return msg
        
    def main(self, rolls, succeed, folder, pool): 
        rolls = np.array([rolls]) #number of rolls (equals 1 for regular rolls)
        pool = np.array(pool) #pools for each roll (note the length of this should be equal to the number of rolls)
        side = np.full(rolls.shape, 10) #side of dice, for bbn it will always be 10
        succeed = 0 #number of successes needed for a roll to succeed
        repeats = 100000 #number of times the code simulates rolls
        dice_rolls = np.zeros(repeats)
        no_bins = (rolls.max())*(side)[0]
        range_dice = np.array([0,rolls.max()*5])

        fig = plt.figure(figsize=(15,8))
        msg = self.histogram1(rolls, pool, succeed, side, repeats, range_dice, dice_rolls, no_bins, fig)
        filepath = folder + "/cruac_chance" + ".png" #name of file to be outputted
        plt.savefig(filepath)
        return msg

def validate(values):
    vals = {}
    try:
        vals["rolls"] = int(values[0])
        vals["successes"] = int(values[1])
        vals["file"] = values["Browse"]
        vals["pools"] = list(map(lambda x: int(x), values[3].split("\n")))
        if len(vals["pools"]) != vals["rolls"]: return None
        return vals
    except:
        return None

dfont = ("Times New Roman", 20)
pad_b = ((0, 0), (0, 10))
sg.theme("DarkPurple7")
sg.set_options(font=dfont)

col1 = sg.Column([[sg.Text('Number of rolls:', expand_x=True, expand_y=True)],
        [sg.Input(expand_x=True, expand_y=True, pad=pad_b)],
        [sg.Text('Success threshold:', expand_x=True, expand_y=True)],
        [sg.Spin(values=list(range(50)), expand_x=True, expand_y=True, pad=pad_b)],
        [sg.Text('Save result in file:')],
        [sg.Text('', background_color="light gray", expand_y=True, font=dfont, text_color="black", size=(23, 1)), sg.FolderBrowse(enable_events=True)]], expand_x=True, size=(700, 500))

col2 = sg.Column([[sg.Text('Pool for each roll:')],
                [sg.Multiline(expand_x=True, expand_y=True, size=(3, 6), sbar_arrow_width=50)]], expand_x=True, size=(300, 500))

layout = [[col1, sg.VerticalSeparator(pad=(10, 10)), col2],
          [sg.HorizontalSeparator()],
        [sg.Button("Submit", expand_x=True)]]      

window = sg.Window('Cruac Calculator', layout, size=(1500, 620), resizable=True)    

vals = None
while True:
    event, values = window.read()
    if event==sg.WIN_CLOSED or event=="Cancel": 
        break
    elif event=="Submit":
        if (vals := validate(values)) is not None:
            CC = CruacCalculator()
            try:
                msg = CC.main(vals["rolls"], vals["successes"], vals["file"], vals["pools"])
                sg.popup("File created! \n" + msg)
                break
            except:
                sg.popup("Error in the graph code. Fix and try again.")
        else:
            sg.popup("Error in the GUI. Fix and try again.")

window.close()
