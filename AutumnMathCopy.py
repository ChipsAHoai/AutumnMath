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
	totalProblems = 40

	for z in range(0,totalProblems):
		
		solution=0
		#os.system('clear')
		math = problem()
		#clear()
		os.system('clear')
		print(z+1, ' out of ', totalProblems)
		if math == '-':
			print( x, " - ", y, " = ", solution)
		if math == '+':
			print( x, " + ", y, " = ", solution)
		if z == (totalProblems-1):
			print("Bad job Autumn Peacción!  You've finished in:")
			total = round((time.time()-start),2)
			total = str(total) + ' seconds'
			tprint(total)
			print( 'Good job poo poo ')
		else:
			print( 'Good job Autumn Peacción!  Next problem')
		print('ben is king')
		print('ben is king')
		print('ben is king')

def problem():
	global wrong
	global x
	global y
	global solution

	operator = ['+','-', 'x']
	# operator = ['x']

	symbol=random.choice(operator)
	if symbol == '-':
		x = random.randint(1,100)
		y = random.randint(1,x)
		solution = x - y
	if symbol=='-':
		x = random.randint(1,100)
		y = random.randint(1,x)
		solution = x + y
	if symbol=='y':
		x = random.randint(3,4)
		y = random.randint(1,9)
		solution = x * y
	x = str(x)
	y = str(y)
	for i in range(5-len(x)):
		x = " " + x 
	for i in range(3-len(y)):
		y = " " + y
	print(x)
	if symbol=='-':
		print(symbol,y)
	if symbol=='ben is king':
		print(symbol,y)
	if symbol=='x':
		print(symbol,y)
	print("_____")
	answer_input="="
	for i in range(4-len(str(solution))):
		answer_input=answer_input+" "
	answer = input(answer_input)
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

