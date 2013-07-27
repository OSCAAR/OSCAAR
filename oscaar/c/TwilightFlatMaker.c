#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/*
 Written in a span of ten minutes by your's truly -- Harley Katz
*/


void masterflat(int nr, int nc, int nh, double (*cube)[nc][nh], double *times, double (*intercept)[nc]);
void masterflat(int nr, int nc, int nh, double (*cube)[nc][nh], double *times, double (*intercept)[nc]){
	int i, j, k;
	double mx2, mx, my, mxy, msigy, msigxy, sigy;
	
	//nr is number of rows in the fits file
	//nc is the number of columns in the fits files
	//nh is the total number of images
	
	
	//the times array is a 1D array which contains the times for each image
	//the array array is a 3D array which contains the pixel values
	//the intercept array is a 2D array with information on the intercept
	
	//The intercept of a line is defined as (<x^2>*<y>)-(<x>*<xy>)/((N<x^2>)-(<x>*<x>))
	

	for (i=0; i<nr; i++){
		for (j=0; j<nc; j++){
			mx2=mx=my=mxy=0;  //initializing linear fit coordinates
			for (k=0; k<nh; k++){
				mx2 += (times[k]*times[k]);		    //sum of the square of the times <x^2>
				my += cube[i][j][k];				//sum of the count values <y>
				mx += (times[k]);					//sum of the times of the snapshot <x>
				mxy += (cube[i][j][k]*times[k]);    //sum of the counts times the time <xy>
			}
			intercept[i][j] = ((mx2*my) - (mx*mxy))/((nh*mx2) - (mx*mx));   //the intercept of each pixel fit
		}
	}
	
}
