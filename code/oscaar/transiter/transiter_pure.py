import numpy as np
import cmath
from sympy import mpmath
import pyfits
from scipy import optimize,fmin,special
from uncertainties import ufloat

def quadbline(x,a,b,c):
    return a*x**2+b*x+c

def heavyside(x):
    if x < 0:
        heavyside=0.0
    elif x == 0:
                heavyside=0.5
    elif x > 0:
                heavyside=1.0
    return heavyside;


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
    
    return NormFlux

def fittransit(NormFlux,Rp,b,vel,midtrantime,gam1,gam2):

        fit,success=optimize.curve_fit(transiter,
                xdata=np.arange(np.size(NormFlux)),
                ydata=NormFlux,
                p0=(0.077,0.535,0.0077,242,0.3,0.1)
                )
        return fit,success

def transiter(x,Rp,b1,vel,midtrantime,gam1,gam2):
    
    Rs=1.0
    p=Rp/Rs

    c2=gam1+2*gam2
    c4=-gam2
    c0=1-c2-c4
    Om=c0/4+c2/6+c4/8

    Flux=np.zeros(np.size(x)) 
    if 0.0<b1<1.0 and  0.0<gam1<1.0 and  0.0<gam2<1.0 and gam1+gam2<1.0: 
        for i in x:
            xpos=vel*(x[i]-midtrantime)
            z=np.sqrt(xpos**2+b1**2)
            a=(z-p)**2
            b=(z+p)**2
            q=p**2-z**2
            eta2=((p**2)/2)*(p**2+2*z**2)
            
            if 1+p < z:
                Flux[i]=1
            elif 0.5+abs(p-0.5) < z <= 1+p:
                
                k=np.sqrt((1-a)/(4*z*p))
                m=k**2
                n2=(a-1)/a
                
                Kk=mpmath.ellipk(m)
                Ek=mpmath.ellipe(m)
                Pik=mpmath.ellippi(n2,m)
                
                K0=np.arccos((p**2+z**2-1)/(2*p*z))
                K1=np.arccos((1-p**2+z**2)/(2*z))
                
                f1=p**2*K0
                f2=np.sqrt((4*z**2-(1+z**2-p**2)**2)/4)
                lamE=(1/np.pi)*(f1+K1-f2)
                
                one1=1/(9*np.pi*np.sqrt(p*z))
                one2=(1-b)*(2*b+a-3)-3*q*(b-2)
                one3=4*p*z*(z**2+7*p**2-4)
                lam1=one1*(one2*Kk+one3*Ek-3*(q/a)*Pik) 
                
                eta1=(1/(2*np.pi))*(K1+2*eta2*K0-0.25*(1+5*p**2+z**2)*np.sqrt((1-a)*(b-1)))
                
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam1+(2/3)*0*(p-z))-c4*eta1)
                
            elif p<= z <= 1-p:
                
                lamE = p**2
                k=(1-a)/(4*z*p)
                
                Kinv=mpmath.ellipk(1/k)
                Einv=mpmath.ellipe(1/k)
                Pinv=mpmath.ellippi((a-b)/a,1/k)
                
                two1=2/(9*np.pi*np.sqrt(1-a))
                two2=1-5*z**2+p**2+q**2
                two3=(1-a)*(z**2+7*p**2-4)
                lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
                
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam2+(2/3))-c4*eta2)
                
            elif 0 <= z <= 0.5-abs(p-0.5):
                lamE = p**2
                k=((1-a)/(4*z*p))
                
                Einv=mpmath.ellipe(1/k)
                Kinv=mpmath.ellipk(1/k)
                Pinv=mpmath.ellippi((a-b)/a,1/k)
                
                two1=2/(9*np.pi*sqrt(1-a))
                two2=1-5*z**2+p**2+q**2
                two3=(1-a)*(z**2+7*p**2-4)
                lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
                
                hh=heavyside(p-z)
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam2+(2.0/3.0)*hh)-c4\
                                   *eta2)
    
    else:
        Flux=np.zeros(np.size(x))

    return Flux


def transiterout(x,Rp,b1,vel,midtrantime,gam1,gam2):
    
    Rs=1.0
    p=Rp/Rs

    c2=gam1+2*gam2
    c4=-gam2
    c0=1-c2-c4
    Om=c0/4+c2/6+c4/8

    Flux,Ing,Egr=np.zeros(np.size(x)),[],[] 
    if 0.0<b1<1.0 and  0.0<gam1<1.0 and  0.0<gam2<1.0 and gam1+gam2<1.0: 
        for i in x:
            xpos=vel*(x[i]-midtrantime)
            z=np.sqrt(xpos**2+b1**2)
            a=(z-p)**2
            b=(z+p)**2
            q=p**2-z**2
            eta2=((p**2)/2)*(p**2+2*z**2)
            
            if 1+p < z:
                Flux[i]=1
            elif 0.5+abs(p-0.5) < z <= 1+p:
                
                if i < np.size(x)/2:
                    Ing.append(i)
                elif i > np.size(x)/2:
                    Egr.append(i)

                k=np.sqrt((1-a)/(4*z*p))
                m=k**2
                n2=(a-1)/a
                
                Kk=mpmath.ellipk(m)
                Ek=mpmath.ellipe(m)
                Pik=mpmath.ellippi(n2,m)
                
                K0=np.arccos((p**2+z**2-1)/(2*p*z))
                K1=np.arccos((1-p**2+z**2)/(2*z))
                
                f1=p**2*K0
                f2=np.sqrt((4*z**2-(1+z**2-p**2)**2)/4)
                lamE=(1/np.pi)*(f1+K1-f2)
                
                one1=1/(9*np.pi*np.sqrt(p*z))
                one2=(1-b)*(2*b+a-3)-3*q*(b-2)
                one3=4*p*z*(z**2+7*p**2-4)
                lam1=one1*(one2*Kk+one3*Ek-3*(q/a)*Pik) 
                
                eta1=(1/(2*np.pi))*(K1+2*eta2*K0-0.25*(1+5*p**2+z**2)*np.sqrt((1-a)*(b-1)))
                
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam1+(2/3)*0*(p-z))-c4*eta1)
                
            elif p<= z <= 1-p:
                
                lamE = p**2
                k=(1-a)/(4*z*p)
                
                Kinv=mpmath.ellipk(1/k)
                Einv=mpmath.ellipe(1/k)
                Pinv=mpmath.ellippi((a-b)/a,1/k)
                
                two1=2/(9*np.pi*np.sqrt(1-a))
                two2=1-5*z**2+p**2+q**2
                two3=(1-a)*(z**2+7*p**2-4)
                lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
                
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam2+(2/3))-c4*eta2)
                
            elif 0 <= z <= 0.5-abs(p-0.5):
                lamE = p**2
                k=((1-a)/(4*z*p))
                
                Einv=mpmath.ellipe(1/k)
                Kinv=mpmath.ellipk(1/k)
                Pinv=mpmath.ellippi((a-b)/a,1/k)
                
                two1=2/(9*np.pi*sqrt(1-a))
                two2=1-5*z**2+p**2+q**2
                two3=(1-a)*(z**2+7*p**2-4)
                lam2=two1*(two2*Kinv+two3*Einv-3*(q/a)*Pinv)
                
                hh=heavyside(p-z)
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam2+(2.0/3.0)*hh)-c4\
                                   *eta2)
    
    else:
        Flux=np.zeros(np.size(x))

    return Flux,Ing,Egr

poutnames=('Rp','b1','vel','midtrantime','gam1','gam2')
for iz in range(0,np.size(fit)):
        print poutnames[iz],fit[iz],np.sqrt(success[iz][iz])

#Get the values on the output fit parameters                           
Flux,Ing,Egr=transiterout(np.arange(0,np.size(NormFlux)),fit[0],fit[1],fit[2],fit[3],fit[4],fit[5])
Ttot=Egr[np.size(Egr)-1]-Ing[0]
Tfull=Egr[0]-Ing[np.size(Ing)-1]
P=2.2047

#delta=ufloat((1-Flux[fit[3]],1-Flux[fit[3]]+sqrt(success[3][3])))     
delta=1-Flux[fit[3]]
dt=timedays[2]-timedays[1]

aRstar=2*delta**0.25*P/(np.pi*dt*np.sqrt(Ttot**2-Tfull**2))                                                          
inc=(180/np.pi)*np.arccos(fit[1]/aRstar)

print aRstar
print inc


