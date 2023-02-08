import winsound
frequency = 1500  # Set Frequency To 2500 Hertz
duration = 500  # Set Duration To 1000 ms == 1 second
winsound.Beep(1500, 500)

while True:
    print('a')
    winsound.Beep(frequency, duration)