import random
import os
import time
from art import *

def main():
	global wrong
	global x 
	global y 
	global solution

	wrong = 0
	os.system('clear')
	start = time.time()
	for z in range(1,21):
		
		solution=0
		#os.system('clear')
		math = problem()
		#clear()
		os.system('clear')
		print(z+1, ' out of ', 20)
		if math == 1:
			print( x, " - ", y, " = ", solution)
		else:
			print( x, " + ", y, " = ", solution)
		if z == 20:
			print("Great job Autumn Peacción!  You've finished in:")
			total = round((time.time()-start),2)
			total = str(total) + ' seconds'
			tprint(total)
			print( 'you got ', wrong, ' incorrect answers')
		else:
			print( 'Good job Autumn Peacción!  Next problem')
		print('')
		print('')
		print('')

def problem():
	global wrong
	global x 
	global y
	global solution

	symbol=random.randint(1,2)
	if symbol == 1:
		x = random.randint(1,20)
		y = random.randint(1,x)
		solution = x - y
	else:
		x = random.randint(1,99)
		y = random.randint(1,x)
		solution = x + y
	x = str(x)
	y = str(y)
	for i in range(5-len(x)):
		x = " " + x 
	for i in range(3-len(y)):
		y = " " + y
	print(x)
	if symbol==1:
		print('-',y)
	else:
		print('+',y)
	print("_____")

	answer = input("=  ")
	try:
		answer = int(answer)
	except:
		answer = 0
	#print(x+y)
	
	while answer != solution:
		wrong +=1
		print("wrong answer Autumn Peacción, try again!")
		answer = input("= ")
		try:
			answer = int(answer)
		except:
			answer = 0
	return symbol

if __name__=="__main__":
	os.system('clear')
	main()

