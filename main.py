import csv
import yaml
import random
import atexit
import codecs

from typing import List, Dict, Tuple
from os.path import join
from psychopy import visual, event, logging, gui, core

delay = 5
poprzedni = 0
go_left_cnt = 0
nogo_left_cnt = 0
go_right_cnt = 0
nogo_right_cnt = 0

@atexit.register
def save_beh_results() -> None:  ## nie wywolujemy w kodzie, jak procedura bedzie wylaczona to zostana zapisane dane eksperymentalne. nawet jak nie dojdzie do konca ta prodecudra
    file_name = PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'
    with open(f'results{file_name}', 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def show_image(win: visual.window, file_name, size, key = 'f7'):  #wyswietlanie obrazkow
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()


def show_info(win, file_name, insert=''): #wyswietla tekst
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth=1920)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def read_text_from_file(file_name, insert=''): #do czytania tekstow, wyswietlanie instrukcji z zewnetrznego pliku
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key: str = 'f7') -> None:  #przycisk z klawiatury, by moc sobie wylaczyc w dowolnym momencie procedure
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))

def abort_with_error(err: str) -> None: #wywolana jesli nastapi blad
    logging.critical(err)
    raise Exception(err)



# GLOBALS
RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Session_name', 'Trial_no', 'Stim_type', 'Delay', 'Reaction time', 'Correctness', 'key'])  #Results header

def main():
    global PART_ID
    clock = core.Clock()

    # === Dialog popup ===
    info: Dict = {'ID': '', 'Sex': ['M', "F"], 'Age': '20'}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Experiment title, fill by your name!')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')

    # load config
    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)
    frame_rate: int = conf['FRAME_RATE']
    screen_res: List[int] = conf['SCREEN_RES']

    # === Scene init ===
    win = visual.Window(screen_res, fullscr=False, monitor='testMonitor', units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible

    PART_ID = info['ID'] + info['Sex'] + info['Age']
    logging.LogFile(f'results{PART_ID}.log', level=logging.INFO, filemode='w')  # errors logging
    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(screen_res))



    # === Prepare stimulus here ===
    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    go_left = visual.ImageStim(win=win, image='./images/go_left.png', interpolate=True, size=(conf['STIM_SIZE'], conf['STIM_SIZE']))
    go_right = visual.ImageStim(win=win, image='./images/go_right.png', interpolate=True, size=(conf['STIM_SIZE'], conf['STIM_SIZE']))
    nogo_left = visual.ImageStim(win=win, image='./images/nogo_left.png', interpolate=True, size=(conf['STIM_SIZE'], conf['STIM_SIZE']))
    nogo_right = visual.ImageStim(win=win, image='./images/nogo_right.png', interpolate=True, size=(conf['STIM_SIZE'], conf['STIM_SIZE']))

    global poprzedni, delay
    poprzedni = random.choice([go_left, go_right, nogo_left, nogo_right])



    show_info(win, join('.', 'messages', 'hello.txt'))
    show_info(win, join('.', 'messages', 'before_training.txt'))


    for trial_no in range(conf['TRENING'] + conf['EKSPERYMENT1'] + conf['EKSPERYMENT2'] + conf['EKSPERYMENT3'] + conf['EKSPERYMENT4']):
        if trial_no == 0:  # go
            show_info(win, join('.', 'messages', 'training.txt'))
            sesja = 'Trening'
        elif trial_no == conf['TRENING']:   #    pierwsza czesc eksperymentu
            show_info(win, join('.', 'messages', 'before_experiment.txt'))
            sesja = 'Eksperyment'
        elif trial_no == (conf['TRENING'] + conf['EKSPERYMENT1']):  #    druga czesc eksperymentu
            show_info(win, join('.', 'messages', 'exp2.txt'))
        elif trial_no == (conf['TRENING'] + conf['EKSPERYMENT1'] + conf['EKSPERYMENT2']):  #    trzecia czesc eksperymentu
            show_info(win, join('.', 'messages', 'exp3.txt'))
        elif trial_no == (conf['TRENING'] + conf['EKSPERYMENT1'] + conf['EKSPERYMENT2'] + conf['EKSPERYMENT3']):  #    czwarta czesc eksperymentu
            show_info(win, join('.', 'messages', 'exp4.txt'))

        stim, delay, rt, corr, key_pressed = run_trial(win, conf, clock, fix_cross, go_left, go_right, nogo_left, nogo_right, poprzedni)
        RESULTS.append([PART_ID, sesja, trial_no, stim, delay, rt, corr, key_pressed])

        # it's a good idea to show feedback during training trials
        feedb = "Poprawnie" if corr == 1 else "Niepoprawnie"
        feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])
        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()
        poprzedni = stim
    show_info(win, join('.', 'messages', 'end.txt'))



def run_trial(win, conf, clock, fix_cross, go_left, go_right, nogo_left, nogo_right, poprzedni) : #jeden poszczegolny trial, przyjmue duzo paramterow, i zwraca to co mierzymy w trakcie.

    global delay, go_left_cnt, nogo_left_cnt, go_right_cnt,  nogo_right_cnt

    # === Prepare trial-related stimulus ===
    if poprzedni == go_left or poprzedni == go_right:
        jak = random.choice([1, 1, 1, 2, 2])
        if jak == 1:
            stim = random.choice([go_left, go_right])
            if stim == go_left:
                go_left_cnt += 1
            else:
                go_right_cnt += 1
        else:
            stim = random.choice([nogo_left,nogo_right])
            if delay < 40:
                delay += 5
            if stim == nogo_left:
                nogo_left_cnt += 1
            else:
                nogo_right_cnt += 1
    else:
        stim = random.choice([go_left, go_right])
        if stim == go_left:
            go_left_cnt += 1
        else:
            go_right_cnt += 1

    # === Start pre-trial ===
    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()

    # === Start trial ===
    event.clearEvents()
    win.callOnFlip(clock.reset)


    tak_dlugo_az_nie_bedzie_reakcji = 50
    delay_cnt = 0
    for _ in range(tak_dlugo_az_nie_bedzie_reakcji):  # present stimuli
        if stim == nogo_left and delay_cnt < delay:
            go_left.draw()
            win.flip()
            delay_cnt +=1
        elif stim == nogo_right and delay_cnt < delay:
            go_right.draw()
            win.flip()
            delay_cnt +=1
        else:
            stim.draw()
            win.flip()
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        if reaction:  # break if any button was pressed
            break


    # === Trial ended, prepare data for send  ===
    if reaction:
        key_pressed, rt = reaction[0]
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0

    if stim == go_left and key_pressed == 'd':
        corr = 1
    elif stim == go_right and key_pressed == 'k':
        corr = 1
    elif (stim == nogo_right or stim == nogo_left) and key_pressed == 'no_key':
        corr = 1
    else:
        corr = 0

    if stim == go_left:
        res = 'go_left'
    elif stim == go_right:
        res = 'go_right'
    elif stim == nogo_left:
        res = 'nogo_left'
    elif stim == nogo_right:
        res = 'nogo_right'


    return res, delay, rt, corr, key_pressed  # return all data collected during trial



main()





