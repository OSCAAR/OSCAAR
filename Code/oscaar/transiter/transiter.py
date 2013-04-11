#! /usr/bin/python
import cmath
import numpy as np
from sympy import mpmath
import pyfits
from matplotlib import pyplot
from scipy import optimize,fmin,special
from uncertainties import ufloat

#This is a code written by Nolan Matthews which . . . 


#Define a quadratic equation used for normalizing the data
def quadbline(x,a,b,c):
	y  = (a*x**2+b*x+c)
	return y

#Define Heavyside Step Function
def heavyside(x):
	if x < 0:
		heavyside=0.0
	elif x == 0:
		heavyside=0.5
	elif x > 0:
		heavyside=1.0
	
	return heavyside;
	
#Function that normalizes the data using a quadratic baseline. 
#Input is the data, left/right baseline values (need to ignore the transit)
def normalizedata(data,lL,lR,rL,rR):
	#Pick points on the left and right baseline
	Lbline=data[lL:lR]
	lx=range(lL,lR)
	Rbline=data[rL:rR]
	rx=range(rL,rR)
	
	dataset,x=[],[]
	for ii in range(0,np.size(Lbline)):
		dataset.append(Lbline[ii])
		x.append(lx[ii])
	for ii in range(0,np.size(Rbline)):
		dataset.append(Rbline[ii])
		x.append(rx[ii])

	fit,success=optimize.curve_fit(quadbline,xdata=np.array(x),ydata=dataset)
	a,b,c=fit[0],fit[1],fit[2]
	NormFlux=data[lL:rR]/quadbline(np.arange(lL,rR),a,b,c)
	
	#Check to see if it's normalized. . .
	pyplot.plot(NormFlux)
	pyplot.show()

	return NormFlux

def velconvert(aRstar,dt,P): #a/Rstar, time interval between data points, and Period
	vel=(2*pi*dt*aRstar)/P	#time units need to be comparable. 
	return vel

	
	
	
	
	
#All light curve models are based upon the 
#analytical expressions derived by Erig Agol and 
#Kasey Mandel (Mandel & Agol, 2002). There are existing
#models available. I apply a quadratically limb-
#darkened star. 

#Elliptical integrals are carried out using the 
#mpmath package. 

#New code, curve_fit usable
def transiterin(x,Rp,b1,vel,midtrantime,gam1,gam2):
	
	#Size of star, set to be unitary
	Rs=1.0
	p=Rp/Rs
	
	#Defining the quadratic limb-darkening coeff's. 
	c1=0.0
	c2=gam1+2*gam2
	c2=gam1+2*gam2
	c3=0.0
	c4=-gam2
	c0=1-c1-c2-c3-c4
	Om=c0/4+c2/6+c4/8
	
	#Intializing arrays, counter variable n, 1/2 width of data set bline. 
	Ing,Egr=[],[]
	Flux=zeros(np.size(x))
	for i in x:
		xpos=vel*(x[i]-midtrantime)
		z=sqrt(xpos**2+b1**2)
		a=(z-p)**2
		b=(z+p)**2	
		q=p**2-z**2
		eta2=((p**2)/2)*(p**2+2*z**2) 
		
		if 1+p < z: #Case 1
			
			Flux[i]=1.
		
		elif 0.5+abs(p-0.5)<z<=1+p: #Case 2 Ingress/Egress
			if i < size(x)/2:
				Ing.append(i)
			elif i > size(x)/2:
				Egr.append(i)
			
			k=sqrt((1-a)/(4*z*p))
			m=k**2 #Input for ellip(k/e/pi) functions use this input. 
			n2=(a-1)/a
			nn=n2**2
			
			Kk=special.ellipkm1(m)
			Ek=special.ellipe(m)
			Pik=mpmath.ellippi(n2,m)

			K0=arccos((p**2+z**2-1)/(2*p*z))
			K1=arccos((1-p**2+z**2)/(2*z))
		
			f1=p**2*K0
			f2=sqrt((4*z**2-pow(1+z**2-p**2,2))/4)
			lamE=(1/pi)*(f1+K1-f2)
			
			one1=1/(9*pi*sqrt(p*z))
			one2=(1-b)*(2*b+a-3)-3*q*(b-2)
			one3=4*p*z*(z**2+7*p**2-4)
			lam1=one1*(one2*Kk+one3*Ek-3*(q/a)*Pik)		
			
			eta1=(1/(2*pi))*(K1+2*eta2*K0-0.25*(1+5*p**2+z**2)*sqrt((1-a)*(b-1)))
			
			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam1+(2/3)*0*(p-z))-c4*eta1)
			Flux[i]=Fx	
		elif p <= z <= 1-p: #Case 3, inside the stellar limb, but not covering the stellar center
			lamE = p**2
			k=pow((1-a)/(4*z*p),1)
			m=k**2
			
			Kinv=mpmath.ellipk(1/k)
			Einv=mpmath.ellipe(1/k)
			Pinv=mpmath.ellippi((a-b)/a,1/k)
			Thk=arcsin(xpos)

			two1=2/(9*pi*sqrt(1-a))
			two2=1-5*z**2+p**2+pow(q,2)
			two3=(1-a)*(z**2+7*p**2-4)
			lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)

			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam2+(2/3))-c4*eta2)
			Flux[i]=Fx
			
		elif 0 <= z <= 0.5-abs(p-0.5): #Case 9 
			lamE = p**2
			k=((1-a)/(4*z*p))

			Einv=mpmath.ellipe(1/k)
			Kinv=mpmath.ellipk(1/k)		
			Pinv=mpmath.ellippi((a-b)/a,1/k)
			
			two1=2/(9*pi*sqrt(1-a))
			two2=1-5*z**2+p**2+pow(q,2)
			two3=(1-a)*(z**2+7*p**2-4)
			lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
			
			hh=heavyside(p-z)
			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam2+(2.0/3.0)*hh)-c4*eta2)
			Flux[i]=Fx
		
		else: #If it's anything else, something is off. 
			Flux[i]=0.3

	return Flux

#Output curve used to determine orbital/planetary parameters
#Can't use the same one b/c of returned parameters . . . 

def transiterout(x,Rp,b1,vel,midtrantime,gam1,gam2):

	#Size of star, set to be unitary
	Rs=1.0
	p=Rp/Rs
	
	#Defining the quadratic limb-darkening coeff's. 
	c1=0.0
	c2=gam1+2*gam2
	c3=0.0
	c4=-gam2
	c0=1-c1-c2-c3-c4
	Om=c0/4+c2/6+c4/8
	
	#Intializing strings, counter variable n, 1/2 width of data set bline. 
	Ing,Egr=[],[]
	Flux=zeros(size(x))
	ktest=[]
	for i in x:
		xpos=vel*(x[i]-midtrantime)
		z=sqrt(xpos**2+b1**2)
		a=(z-p)**2
		b=(z+p)**2	
		q=p**2-z**2
		eta2=((p**2)/2)*(p**2+2*z**2) 
		
		if 1+p < z: #Case 1
			Flux[i]=1.
		
		elif 0.5+abs(p-0.5)<z<=1+p: #Case 2 Ingress/Egress
			
			#Used to calculate a/Rstar in output model.
			if i < size(x)/2:
				Ing.append(i)
			elif i > size(x)/2:
				Egr.append(i)
			
			k=sqrt((1-a)/(4*z*p))
			ktest.append(k)
			m=k**2 #Input for ellip(k/e/pi) functions use this input. 
			n2=(a-1)/a
			nn=n2**2
			
			Kk=special.ellipk(m)
			Ek=special.ellipe(m)
			Pik=mpmath.ellippi(n2,m)

			K0=arccos((p**2+z**2-1)/(2*p*z))
			K1=arccos((1-p**2+z**2)/(2*z))
		
			f1=p**2*K0
			f2=sqrt((4*z**2-pow(1+z**2-p**2,2))/4)
			lamE=(1/pi)*(f1+K1-f2)
			
			one1=1/(9*pi*sqrt(p*z))
			one2=(1-b)*(2*b+a-3)-3*q*(b-2)
			one3=4*p*z*(z**2+7*p**2-4)
			lam1=one1*(one2*Kk+one3*Ek-3*(q/a)*Pik)		
			
			eta1=(1/(2*pi))*(K1+2*eta2*K0-0.25*(1+5*p**2+z**2)*sqrt((1-a)*(b-1)))
			
			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam1+(2/3)*0*(p-z))-c4*eta1)
			Flux[i]=Fx	
		elif p <= z <= 1-p: #Case 3, inside the stellar limb, but not covering the stellar center
			lamE = p**2
			k=pow((1-a)/(4*z*p),1)
			m=k**2
			
			Kinv=mpmath.ellipk(1/k)
			Einv=mpmath.ellipe(1/k)
			Pinv=mpmath.ellippi((a-b)/a,1/k)

			two1=2/(9*pi*sqrt(1-a))
			two2=1-5*z**2+p**2+pow(q,2)
			two3=(1-a)*(z**2+7*p**2-4)
			lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)

			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam2+(2/3))-c4*eta2)
			Flux[i]=Fx
			
		elif 0 <= z <= 0.5-abs(p-0.5): #Case 9 
			lamE = p**2
			k=((1-a)/(4*z*p))

			Einv=mpmath.ellipe(1/k)
			Kinv=mpmath.ellipk(1/k)		
			Pinv=mpmath.ellippi((a-b)/a,1/k)
			
			two1=2/(9*pi*sqrt(1-a))
			two2=1-5*z**2+p**2+pow(q,2)
			two3=(1-a)*(z**2+7*p**2-4)
			lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
			
			hh=heavyside(p-z)
			fx1=1/(4*Om)
			Fx=1-fx1*((1-c2)*lamE+c2*(lam2+(2.0/3.0)*hh)-c4*eta2)
			Flux[i]=Fx
		
		else:
			Flux[i]=0.3

	return Flux,Ing,Egr

#Helper function, groups the data in different time bins
def time_bin(A,nn):	
	
	time_bin=[]
	for i in range(size(A)):
		
		ii,aa=0,0
		tbin=[]
		while ii<nn:
			tbin.append(A[ii-2])
			ii+=1
		time_bin.append(sum(tbin)/nn)
		
	return time_bin

	
#Returning orbital parameters Transits/Occultation Method - Joshua Winn

#Finder Function
def find_nearest(array,value):
    idx = (abs(array-value)).argmin()
    return idx

#Run the fit, import xdata,ydata, inital guesses for the
#parameters. These matter; extremely incorrect values for the 
#initial guess can lead the optimizer to not 
#converge on a solution as precisely. LM finds a local
#minimum not a global. 

#Constraints on the limb-darkening parameters.  

#In any case, the uncertainty in the model should be 
#estimated using a Markov Chain. This will probably take
#a while, if the quality of the transit data is somewhat
#poor it might be better to fix the limb-darkening 
#parameters for improved speed. In addition, the mid transit time could
#possibly be fixed. 

def fittransit(NormFlux,Rp,b,vel,midtrantime,gam1,gam2):
	
	fit,success=optimize.curve_fit(transiterin,
		xdata=arange(size(NormFlux)),ydata=NormFlux,
		p0=(0.077,0.535,0.0077,242,0.3,0.1)
		#p01=
		)
	return fit,success
	
poutnames=('Rp','b1','vel','midtrantime','gam1','gam2')
for iz in range(0,size(fit)):
	print poutnames[iz],fit[iz],sqrt(success[iz][iz])

#Get the values on the output fit parameters
Flux,Ing,Egr=transiterout(arange(0,size(NormFlux)),fit[0],
					fit[1],fit[2],fit[3],fit[4],fit[5])
Ttot=Egr[size(Egr)-1]-Ing[0]
Tfull=Egr[0]-Ing[size(Ing)-1]
P=2.2047
#delta=ufloat((1-Flux[fit[3]],1-Flux[fit[3]]+sqrt(success[3][3])))
delta=1-Flux[fit[3]]
dt=timedays[2]-timedays[1]

aRstar=2*delta**0.25*P/(pi*dt*sqrt(Ttot**2-Tfull**2))
#bmodel=sqrt((1-sqrt(delta))**2-(Tfull/Ttot)**2 * 
#	(1+sqrt(delta))**2/(1-(Tfull/Ttot)**2)) #Not too sure why this doesn't work
inc=(180/pi)*arccos(fit[1]/aRstar)

print aRstar
print inc
#Ttot = 2*sqrt((fit[3]-find_nearest(zPos,1+fit[0]))**2)
#Tfull= 2*sqrt((fit[3]-find_nearest(zPos,1-fit[0]))**2)
#aRstar3=2*delta**0.25 * P/(pi*sqrt(Ttot**2-Tfull**2)*(timedays[2]-timedays[1]))
