/*
 
 INTRO:
	 transit1forLMLS.c is an *experimental* transit light curve modeling
	 routine. It is a near-translation of Eric Agol's IDL routines, written 
	 in C for speed and for nonproprietary use (i.e., open source) since 
	 IDL is not free.

 NOTES: 
	 We'll consider this routine experimental for now, though it 
	 passes the early tests that have been thrown at it thus far.
 
	 It agrees with Eric Agol's routines to single precision as of 14 May 
     2013, and performs about 7% faster than the IDL routine in the 
	 generalized case. In the special case where eccentricity=0, there is 
	 potential for a runtime speed-up by a factor of two that is not yet (but 
	 nearly) implemented.
 
	 Currently, this script relies on the Numerical Recipes utils available in
	 the public domain at http://www.nr.com/public-domain.html
 
            ***Important note for calling C functions from Python***
     To import functions from this file into Python code with the ctypes module,
     the C function to be called must have a function prototype defined, i.e.,
     there must be a function definition without a body in the first few lines
     of the code. For example, occultquad() is available for calling from Python
     because its prototype is declared after the #includes with: 
     "void occultquad(double *t, float p,...". This is the function prototype. 
 
 Core Developer: Brett Morris (NASA GSFC)
 
 CITATIONS: 
	 These routines are based on the work in Mandel & Agol (2002),
	 so please cite this paper if you make use of these routines
	 in your research.
 
	 Eric Agol (currently at UW) has posted analogous routines in IDL
	 and FORTRAN on his website. A lot of this code is inspired heavily
	 by those routines. Here's a URL to those routines, as of May 2013:
	 http://www.astro.washington.edu/users/agol/transit.html
	 
	 This implementation of occultquad() was also in part inspired
	 by Gil Nachmani's MATLAB occultquad() routine, which is available
	 on Eric's website as well (same URL).
 
 */


#include "nrutil.h"
#include <math.h>
#include "nrutil.c"
#include <stdlib.h>
#include <time.h>

#define pi 3.14159265358979311600

//void occultquad(double *t, float p, float ap, float P, float i, float gamma1, float gamma2, double e, double longPericenter, double t0, float n, double *F);
void occultquad(double *t, double p, double ap, double P, double i, double gamma1, double gamma2, double e, double longPericenter, double t0, double n, double *F);

// Elliptic integregral approximations
double E(double k);
double PI(double n, double k);
double K(double k);

float *linspace(float beginningPhase, float endPhase, int Npoints)
// Replicate the function "linspace" from MATLAB
{
	float *t;
	int ii;
	t = vector(0,Npoints);

	for (ii=0; ii<Npoints+1; ii++)
	{
		t[ii] = beginningPhase + (float)(endPhase - beginningPhase)*ii/(Npoints+1);
	//	printf("t[ii]=%f\n",t[ii]);
	}
	return t;
    //free_vector(t,0,Npoints);
}


float printVector(double *array, float lengthArray)
{
	int i;
	for (i=0; i<lengthArray; i++)
	{
		printf("array: %.10f\n",array[i]);
	}
	return 0.0;
}

int writeVectorToFile(float *vector, int vectorLength, char *name)
// Write the vector to output file.
{
  FILE *fp;
  int i;
  fp = fopen(name, "w");
  if (fp == NULL) {
	 printf("Could not create desired output file: %s\n",name);
	 exit(0);
  }

  for (i=0; i<vectorLength; ++i)
	 fprintf(fp, "%.12f\n", vector[i]);
  printf("Data file written: %s\n",name);

  return 0;
}

double PI(double n, double k)
{
	//Computes the complete elliptical integral of the third kind using the algorithm of Bulirsch (1965):
	// Translation of Eric's "ellpic_bulirsch"
	double m0, kc, c, p, d, e, f, dpi, quantity, g;
	int continueLoop;

	dpi = pi;

	kc = sqrt(1.0-k*k);
	p = n+1.0;
	m0 = 1.0;
	c = 1.0;
	p = sqrt(p);
	d = 1.0/p;
	e = kc;

	continueLoop = 1;
	while (continueLoop == 1) {
		f = c;
		c = d/p+f;
		g = e/p;
		d = (f*g+d)*2.0;
		p = g + p;
		g = m0;
		m0 = kc + m0;
		quantity = fabs(1.0-kc/g);
		if (quantity > 1.0e-13) {
			kc = 2.0*sqrt(e);
			e = kc*m0;
		} else { continueLoop = 0; }
	}
	return 0.5*dpi*(c*m0+d)/(m0*(m0+p));
}

double K(double k)
{
	// Translation of Eric's "ellk"
	// Computes polynomial approximation for the complete elliptic integral
	// of the first kind (Hasting's approximation):

	double m1, a0, a1, a2, a3, a4, b0, b1, b2, b3, b4, ek1, ek2;
	m1 = 1.0-k*k;
	if (k*k > 1) {printf("WARNING: k*k > 1, elliptic integral of first kind, K, will return nan");}
	a0 = 1.386294361120;
	a1 = 0.096663442590;
	a2 = 0.035900923830;
	a3 = 0.037425637130;
	a4 = 0.014511962120;
	b0 = 0.50;
	b1 = 0.124985935970;
	b2 = 0.068802485760;
	b3 = 0.033283553460;
	b4 = 0.004417870120;
	ek1 = a0+m1*(a1+m1*(a2+m1*(a3+m1*a4)));
	ek2 = (b0+m1*(b1+m1*(b2+m1*(b3+m1*b4))))*log(m1);
	return ek1-ek2;
}

double E(double k)
{
	// Translation of Eric's "ellec"
	// Computes polynomial approximation for the complete elliptic integral
	// of the second kind (Hasting's approximation):
	double m1, a1, a2, a3, a4, b1, b2, b3, b4, ee1, ee2;
	m1 = 1.0-k*k;
	a1=0.44325141463;
	a2=0.06260601220;
	a3=0.04757383546;
	a4=0.01736506451;
	b1=0.24998368310;
	b2=0.09200180037;
	b3=0.04069697526;
	b4=0.00526449639;
	ee1 = 1.0+m1*(a1+m1*(a2+m1*(a3+m1*a4)));
	ee2 = m1*(b1+m1*(b2+m1*(b3+m1*b4)))*log(1.0/m1);
	return ee1+ee2;
}

double heaviside(double x)
{
	// Translation of MATLAB's heaviside function
	double result;
	if (x < 0) {
		result = 0;
	} else if (x > 0) {
		result = 1;
	} else if (x == 0) {
		result = 0.5;
	}
	return result;
}

double lam1(double p, double z, double a, double b, double k, double q)
{
	double lam1, en;
	en=1.0/a-1.0; // Eric Agol inspired:  en=1.d0/a-1.d0
	lam1 = (((1.0-b)*(2.0*b+a-3.0)-3.0*q*(b-2.0))*K(k)+4.0*p*z*(z*z+7.0*p*p-4.0)*E(k)-3.0*q/a*PI(en,k))/9.0/pi/sqrt(p*z); // Eric Agol's code inspired
	return lam1;
}

double lam2(double p, double z, double a, double b, double k, double q)
{
	double lam2;
	double invk = 2.0*sqrt(p*z/(1.0-a)); // Eric Agol's code inspired
	double en=b/a-1.0;					// Eric Agol's code inspired
	lam2 = 2.0/9.0/pi/sqrt(1-a) * ( (1-5*z*z+p*p+q*q)*K(invk) + (1-a)*(z*z+7*p*p-4)*E(invk)-3*q/a*PI(en,invk) );
	return lam2;
}

double lam3(double p, double k0, double k1)
{
	double lam3 = 1.0/3.0 + 16*p/9.0/pi*(2*p*p-1)*E(0.5/p) - (1-4*p*p)*(3-8*p*p)/9.0/pi/p*K(0.5/p);
	k0 = acos(1.0-0.5/(p*p)); // Eric Agol's code inspired
	k1 = acos(0.5/p);		  // Eric Agol's code inspired
	return lam3;
}

double lam4(double p)
{
	double lam4 = 1.0/3.0 + 2.0/9.0/pi*(4*(2*p*p-1)*E(2*p)+(1-4*p*p)*K(2*p));
	return lam4;
}

double lam5(double p)
{
	double lam5 = 2.0/3.0/pi*acos(1-2*p) - 4.0/9.0/pi*(3+2*p-8*p*p)*sqrt(p*(1-p))-2.0/3.0*heaviside(p-0.5);
	return lam5;
}

double lam6(double p)
{
	double lam6 = -2.0/3.0*sqrt((1-p*p)*(1-p*p)*(1-p*p));
	return lam6;
}

double eta2(double p, double z)
{
	double eta2 = p*p/2.0*(p*p+2.0*z*z);
	return eta2;
}

double eta1(double p, double z, double a, double b, double k1, double k0)
{
	double eta1;
	eta1 = 0.5/pi*(k1+2.0*eta2(p,z)*k0-0.25*(1.0+5.0*p*p+z*z)*sqrt((1.0-a)*(b-1.0)));
	return eta1;

}

double ekepler(double m, double e)
{
	double ekep,eps,pi2,ms,d3,e0,f0,f1,f2,f3,d1,d2;
	eps = 1.0E-10;
	pi2 = 2.0*acos(-1.0);
	ms = fmod(m,pi2);//m % pi2;
	d3 = 1.0E10;
	e0 = ms+e*0.85*sin(ms)/fabs(sin(ms));
	while (fabs(d3) > eps)
	{
		f3 = e*cos(e0);
		f2 = e*sin(e0);
		f1 = 1.0-f3;
		f0 = e0-ms-f2;
		d1 = -1*f0/f1;
		d2 = -1*f0/(f1+0.5*d1*f2);
		d3 = -1*f0/(f1+d2*0.5*(f2+d2*f3/3.0));
		e0 = e0+d3;
	}
	ekep = e0 + m - ms;
	return ekep;
}

double kepler(double m, double e)
{
	double i = 0, f, ekep;
	if (e != 0.0) {
		ekep = ekepler(m,e);
		f = 2.0*atan(sqrt((1.0+e)/(1.0-e))*tan(0.50*ekep));
	} else {
		f = m;
	}
	if (m == 0.0) {f=0.0;}
	return f;
}

int printVector2(float *vector, int Npoints)
{
	char string[Npoints+1];
	int i;
	for (i=0;i<Npoints;i++)
	{
		string[i] = (char) vector[i];
	}
	printf("%s",string);
	return 0;
}

double occultuni(double z, double w)
{
	double xt, kap1, kap0, lambdae, dblcond, dblcondA, dblcondB, muo1;
	if (fabs(w-0.5) < 1.0E-3) {
		w = 0.5;
	}
	if (z > 1.0+w) {
		muo1 = 1.0;
	}
	if (z > fabs(1.0-w) &&  z <= 1.0+w) {
		xt = (1.0-w*w+z*z)/2.0/z;

		if (xt < 1.0) {
			dblcondA = 1;
		} else {
			dblcondA = 0;
		}
		if (xt >= 1.0) {
			dblcondB = 1;
		} else {
			dblcondB = 0;
		}

		kap1 = acos(xt*dblcondA+1.0*dblcondB);
		xt=(w*w+z*z-1.0)/2.0/w/z;

		kap0 = acos(xt*dblcondA+1.0*dblcondB);
		lambdae=w*w*kap0+kap1;
		xt = 4.0*z*z-(1.0+z*z-w*w)*(1.0+z*z-w*w);

		if (xt >= 0.0) {
			dblcond = 1;
		} else {
			dblcond = 0;
		}

		lambdae = (lambdae-0.5*sqrt(xt*dblcond))/pi;
		muo1 = 1.0-lambdae;
	}

	if (z <= 1.0-w) {
		muo1 = 1.0-w*w ;
	}
	return muo1;
}


//void occultquad(double *t, float p, float ap, float P, float i, float gamma1, float gamma2, double e, double longPericenter, double t0, float n, double *F)

void occultquad(double *t, double p, double ap, double P, double i, double gamma1, double gamma2, double e, double longPericenter, double t0, double n, double *F)
{
	double t0overP;
	double *Z, *phi, *new_t, *new_phi; int ii;
	int Npoints = (int)n;
	Z = dvector(0,Npoints);
	phi = dvector(0,Npoints);
    new_t = dvector(0,Npoints);

    for (ii=0; ii<Npoints; ii++) {new_t[ii] = t[ii] - t0;}

    t = new_t;
    t0 = 0.0;

    for (ii=0; ii<Npoints; ii++) {phi[ii] = t[ii]/P - t0;}

	double ti;//, pi = 3.14159265;
	//double c1, c2, c3, c4, c0, omega;
	double omega;
	for (ii=0; ii<Npoints; ii++)
	{
		/*
		; Input parameters (x) are:
		; x(0) = P  (units of day)
		; x(1) = inc = inclination angle (degrees)
		; x(2) = p = R_p/R_* = radius of planet in units of radius of star
		; x(3) = t0 = mid-point of transit
		; x(4) = u1 = linear limb-darkening coefficient
		; x(5) = u2 = quadratic limb-darkening coefficient
		; x(6) = f0 = uneclipsed flux
		; x(7) = a/R_* = semi-major axis divided by R_*
		; x(8) = e = eccentricity
		; x(9) = omega = longitude of pericentre
		; x(10)= sine amplitude
		; x(11)= slope of linear fit
		; x(12)= intercept of linear fit
		 */
		ti = t[ii];
		if (0 == 0)	{	// Use MATLAB version or Erics version. If true, Eric's version.
			double f1,e1,tp, m, f, radius;
			f1 = 1.50*pi-longPericenter*pi/180;

			e1 = e;
			tp = t0+P*sqrt(1.0 - e1*e1)/2.0/pi*(e1*sin(f1)/(1.0+e1*cos(f1))-2.0/sqrt(1.0 - e1*e1)*atan((sqrt(1.0 - e1*e1)*tan(0.5*f1))/(1.0+e1)));

			m = 2.0*pi/P*(ti-tp);
			f = kepler(m,e1);
			radius = ap*(1.0 - e1*e1)/(1.0 + e1*cos(f));
			Z[ii] = radius*sqrt(1.0-(sin(i*pi/180.0)*sin(longPericenter*pi/180.0+f))*(sin(i*pi/180.0)*sin(longPericenter*pi/180.0+f))); //Eric Agol's code inspired
		} else {
			Z[ii] = ap*sqrt(sin(2*pi/P*ti)*sin(2*pi/P*ti) + (cos(pi/180*i)*cos(2*pi/P*ti))*(cos(pi/180*i)*cos(2*pi/P*ti))); // MATLAB VERSION
		}
	}

	/*c1=0;
	c2=gamma1+2*gamma2;
	c3=0;
	c4=-gamma2;
	c0=1-c1-c2-c3-c4;*/
	//omega = c0/(0+4)+c1/(1+4)+c2/(2+4)+c3/(3+4)+c4/(4+4);
	//omega=1.d0-u1/3.d0-u2/6.d0
	omega=1.0-gamma1/3.0-gamma2/6.0;// Eric Agol's code inspired

	int j = 0;
	double z, a, b, k, q, k1, k0, lam_e, F0;
	for (j=0;j<Npoints;j++)
	{
		z = Z[j];
	    a = (z-p)*(z-p);
	    b = (z+p)*(z+p);
	    k = sqrt((1.0-a)/4.0/z/p);
	    q = p*p-z*z;
	    k1=acos((1-p*p+z*z)/2/z);
	    k0=acos((p*p+z*z-1)/2/p/z);

	    // Evaluate lambda_e, MA2002 eq. (1)
	    if (1+p<z || fabs(phi[j])>(p+1)/ap/2/pi) {
	        lam_e = 0;
	    } else if (fabs(1-p)<z && z<=1+p) {
	        lam_e = 1/pi*(p*p*k0+k1-0.5*sqrt(4*z*z-(1+z*z-p*p)*(1+z*z-p*p)));
	    } else if (z<=1-p && z>p-1) {
	        lam_e = p*p;
	    } else if (z<=p-1) {
	        lam_e = 1;
	    }
	    double lam_d, eta_d;
	    // Evaluate lambda_d and eta_d from MA2002 Table (1)
	    if (z>=1+p || p==0 || fabs(phi[j])>(p+1.0)/ap/2.0/pi) { // Case 1
	    	lam_d = 0.0;
	        eta_d = 0.0;
	        //printf("Case 1\n");
	        //    printf("  Case 1 \n");
	      } else if (p<0.5 && z>p && z<1-p) {// Case 3	-- switch order since most time should be spent in case 3
			lam_d = lam2(p,z,a,b,k,q);
			eta_d = eta2(p,z);
		   // printf("Case 3 \n");
			//printf("Case 3\n");
		  } else if (z>=fabs(1.0-p) && z<1+p) { // Case 2 
	        lam_d = lam1(p,z,a,b,k,q);
	        eta_d = eta1(p,z,a,b,k1,k0);
	        //printf("  Case 2 \n");
	        //printf("z:%f \n",z);
	       // printf("Case 2\n");
	      } else if (p<0.5 && z==1-p) {// Case 4
	        lam_d = lam5(p);
	        eta_d = eta2(p,z);
	       // printf("Case 4\n");
	      } else if (p<0.5 && z==p) { // Case 5
	        lam_d = lam4(p);
	        eta_d = eta2(p,z);
	       // printf("Case 5\n");
	      } else if (p==0.5 && z==0.5) { // Case 6
	        lam_d = 1.0/3.0-4.0/pi/9.0;
	        eta_d = 3.0/32.0;
	       // printf("Case 6\n");
	      } else if (p>0.5 && z==p) { // Case 7
	        lam_d = lam3(p, k0, k1);
	        eta_d = eta1(p,z,a,b,k1,k0);
	        //printf("Case 7\n");
	      } else if (p>0.5 && z>=fabs(1.0-p) && z<p) { // Case 8
	        lam_d = lam1(p,z,a,b,k,q);
	        eta_d = eta1(p,z,a,b,k1,k0);
	        //printf("Case 8\n");
	      } else if (p<1 && z>0 && z<=0.5-fabs(p-0.5)) {// Case 9
	        lam_d = lam2(p,z,a,b,k,q);
	        eta_d = eta2(p,z);
	        //printf("Case 9\n");
	      } else if (p<1 && z==0) {  // Case 10
	        lam_d = lam6(p);
	        eta_d=eta2(p,z);
	        //printf("Case 10\n");
	      } else if (p>1 && z<=p-1) {  // Case 11
		    //printf("Case 11\n");
	    	lam_d = 0.0;
	        eta_d = 0.5;
	    }

	    ////F[j] =  1 - 1.0/(4*omega)*( (1-c2)*lam_e + c2*(lam_d+2.0/3.0*heaviside(p-z)) - c4*eta_d );
	    F[j] = 1.0-((1.0-gamma1-2.0*gamma2)*lam_e+(gamma1+2.0*gamma2)*(lam_d+2.0/3.0*heaviside(p-z))+gamma2*eta_d)/omega; // Eric Agol's code inspired
	    /* omega=1.d0-u1/3.d0-u2/6.d0
		F=1.d0-((1.d0-u1-2.d0*u2)*lambdae+(u1+2.d0*u2)*(lambdad+2.d0/3.d0*(p gt z))+u2*etad)/omega*/
	}
	//return 0;
    free_dvector(Z,0,Npoints);
    free_dvector(phi,0,Npoints);
    free_dvector(new_t,0,Npoints);
    //free_dvector(new_phi,0,Npoints);
}
