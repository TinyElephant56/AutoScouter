import math
import cv2
frame = cv2.imread('top-down.png')

detections = [[0, (1245, 562), 'red', 0.8556276, (1797, 837), (1880, 881), '', 'side'], [1, (1240, 92), 'red', 0.84159863, (1245, 844), (1340, 894), '', 'side'], [2, (288, 433), 'blue', 0.82309175, (311, 911), (380, 965), '', 'side'], [3, (289, 406), 'blue', 0.79852486, (383, 423), (485, 472), '', 'top'], [4, (1242, 84), 'red', 0.6909942, (1479, 338), (1543, 371), '', 'top'], [5, (220, 220), 'blue', 0.68021494, (630, 875), (688, 922), '', 'side'], [6, (198, 265), 'blue', 0.54173654, (361, 385), (397, 417), '', 'top']]
d = detections.copy()
working = True
while working:
    print('loop')
    shortest = 80 #try to beat this distance
    best_i = None #will be a value
    best_j = None
    for i in d:
        for j in d:
            if i[2] == j[2] and i[7] != 'midpoint' and j[7] != 'midpoint' and i[7] != j[7]:
                if math.dist(i[1], j[1]) < shortest:
                    shortest = math.dist(i[1], j[1])
                    best_i = i
                    best_j = j
    if shortest < 80:
        x1, y1 = best_i[1]
        x2, y2 = best_j[1]
        midpoint = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        print(f"removed {best_i[0]} and {best_j[0]}")
        d.append([(best_i[0]*100+best_j[0]), midpoint, best_i[2], (best_i[3]+best_j[3]), best_i[4], best_i[5], best_i[6], 'midpoint'])
        for k in d[:]:
            if math.dist(midpoint, k[1]) < 100 and k[7] != 'midpoint':
                d.remove(k)
    else:
        working = False

    if len(d) < 2:
        working = False

for robot in d:
    print(robot[1])
    cv2.circle(frame, robot[1], 10, (128, 128, 128), -1)

cv2.imshow('asdhjfk', frame)
cv2.waitKey(0)
cv2.destroyAllWindows()