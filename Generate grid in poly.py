'''
Скрипт генерирует равномерную сетку точеск внутри 
заданного полигона
Шаги по x и y равны и зависят от количества точек
num, которое нужно сгенерировать

Для того, чтобы использовать этот скрипт, 
границы нужно объединить в один объект. 
'''

'''
                   ЗДЕСЬ ВВОДИМ ВХОДНЫЕ ДАННЫЕ 
'''   
#CRS полигона должна быть прямоугольной и из EPSG. МСК не подойдет
layer_name = 'p' #Имя полигонального слоя
num = 100 #количество точек, которое надо сгенерировать
alpha = 45

"""
                     НИЖЕ ИДЕТ КОД ПРОГРАММЫ
"""

from qgis.core import  *
import random
import math

def rotate_(x,y,alpha):
    x = x*math.cos(math.radians(alpha))+y*math.sin(math.radians(alpha))
    y = y*math.cos(math.radians(alpha))-x*math.sin(math.radians(alpha)) 
    return x,y
def create_points(layer, step_x, step_y):
    for poly_feat in layer.getFeatures():
        print(poly_feat)
    xmin = layer.extent().xMinimum()
    xmax = layer.extent().xMaximum()
    ymin = layer.extent().yMinimum()
    ymax = layer.extent().yMaximum()
    
    x = xmin
    y = ymin
    x,y = rotate_(x,y,alpha)

    #Список для wkt записей генерируемых точек
    point_list = ['POINT ({0} {1})'.format(x,y)]
    #Генерируем точки с заданным шагом в экстенте полигона
    while (x>=xmin) and (x<=xmax):
        while (y>=ymin) and (y<=ymax):
            x,y = rotate_(x,y,alpha)
            wkt_ = 'POINT ({0} {1})'.format(x,y)
            point_list.append(wkt_)
            y = y+step_y
        x = x+step_x
        y = ymin
       
    
    #Создаем слой, в который будем закидывать точки
    vl = QgsVectorLayer("Point", "temporary_points", "memory")
    crs = vl.crs()
    crs.createFromId(int(layer.crs().authid().replace('EPSG:','')))
    vl.setCrs(crs)
    pr = vl.dataProvider()
    # Включаем EditMode для слоя
    vl.startEditing()
    # Инициализируем поля для слоя
    pr.addAttributes([QgsField("name", QVariant.Int)])
    i = 0
    
    #Добавляем точки, попадающие внутрь полигона вслой
    for wkt__ in point_list:
        point = QgsGeometry.fromWkt(wkt__)
        if point.intersects(poly_feat.geometry()):
            fet = QgsFeature()
            fet.setGeometry(point)
            fet.setAttributes([i+1])
            pr.addFeatures([fet])
    #Сохраняем слой
    vl.commitChanges()
    return vl, vl.featureCount()


layer = QgsProject.instance().mapLayersByName(layer_name)[0]
xmin = layer.extent().xMinimum()
xmax = layer.extent().xMaximum()
ymin = layer.extent().yMinimum()
ymax = layer.extent().yMaximum()

for feat in layer.getFeatures():
    area = feat.geometry().area()

#Считаем приблизительный размер шага, чтобы дальше его корректировать в зависимости от условий
step_x = math.sqrt(area/num)
step_y = math.sqrt(area/num)
a = create_points(layer, step_x, step_y)

#Оптимальная начальная скорость изменения шага
step_inc = abs(a[1]-num)
print(a[1])
print(num)

'''
Сужаем раницы поиска размера шага. 
1) Определяем шаг, при котором a[i]>num
2) Определяем шаг, при котором a[i]<num
3) Корректируем скорость изменения шага step_inc по этим границам
4) Изменяем шаг и генерируем точки (переменная a), где 
    a[0] - точки, a[1] - получившееся количество точек
5) Цикл перезапускается с уже скорректированным значением шага 
    до тех пор пока не будет получено нужное колечество точек, равное num/
    Т.е. пока не будет выполнено условие a[1]=num 
Таким образом можно приблизительно найти множество, в котором искать нужный шаг
Так делаем итеративно, сужая границы поиска и уменьшая скорость изменения шага,
пока a[1](получившееся количество точек) не станет равной num (необходимое количество точек)
'''
while a[1]!=num:
    while a[1]<num: # Считаем нижнюю границу поиска шага
        step_x-=step_inc
        step_y-=step_inc
        a = create_points(layer, step_x, step_y)
    print('<:', a[1])
    print(step_x)
    while a[1]>num: #Считаем верхнюю границу поиска шага
        step_x+=step_inc
        step_y+=step_inc
        a = create_points(layer, step_x, step_y)
    step_inc = step_inc/3 #Корректировка скорости изменения шага
    print('>:', a[1])
    print(step_x)
#Приблизительный размер шага, рассчитанный изначально, чтобы сравнить с тем, что вышло
print("Приблизительный размер шага:",math.sqrt(area/num) )
#Добавляем слой в проект
QgsProject.instance().addMapLayer(a[0])
a = None