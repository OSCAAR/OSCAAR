# Descendant of the original 'differ10.2.py'
import os
import math
import numpy as np
import matplotlib.pyplot as plt

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]

lcMatrix = np.vstack([time,lightCurve])

allSigma = np.std(lcMatrix[1,:])
bins = np.arange(97,103)/100.
# the histogram of the data with histtype='step'
fig6 = plt.figure()
n, bins, patches = plt.hist(lightCurve, bins, normed=1, histtype='bar')
plt.title('All data, $\sigma =$ '+trunc(allSigma,5));plt.xlabel('Relative Flux');plt.ylabel('Frequency')
fig6.savefig('plots/histograms/allData.png',fmt='png')
plt.close()
#plt.clf()

## find index at Ingress
ingInd = 0
index = -1
while ingInd == 0:
    index += 1
    if time[index] > ingress:
        ingInd = index
ingressMatrix = lcMatrix[:,0:ingInd]
ingSigma = np.std(ingressMatrix[1,:])

fig3 = plt.figure()
plt.hist(ingressMatrix[1,:], bins, normed=1, histtype='bar')
plt.title('Pre-Ingress, $\sigma =$ '+trunc(ingSigma,5));plt.xlabel('Relative Flux');plt.ylabel('Frequency')
fig3.savefig('plots/histograms/ingress.png',fmt='png')
plt.close()

## find index at Egress
egrInd = 0
index = -1
while egrInd == 0:
    index += 1
    if time[index] > egress:
        egrInd = index
egressMatrix = lcMatrix[:,egrInd:]

egrSigma = np.std(egressMatrix[1,:])
fig4 = plt.figure()
plt.hist(egressMatrix[1,:], bins, normed=1, histtype='bar')
plt.title('Post-Egress, $\sigma =$ '+trunc(egrSigma,5));plt.xlabel('Relative Flux');plt.ylabel('Frequency')
fig4.savefig('plots/histograms/egress.png',fmt='png')
plt.close()
#plt.clf()

## out of transit portion
ootMatrix = np.hstack([ingressMatrix,egressMatrix]) 
ootSigma = np.std(ootMatrix[1,:])
fig5 = plt.figure()
plt.hist(ootMatrix[1,:], bins, normed=1, histtype='bar')
plt.title('Out Of Transit, $\sigma =$ '+trunc(ootSigma,5));plt.xlabel('Relative Flux');plt.ylabel('Frequency')
fig5.savefig('plots/histograms/outOfTransit.png',fmt='png')
plt.close()
#plt.clf()

print "Pre-ingress standard devation:",ingSigma
print "Post-egress standard devation:",egrSigma
print "Out-of-transit standard devation:",ootSigma
if initGui == 'on':
    filename = open('file2.txt', 'w')
    filename.write('done')
    filename.close()
exit()
a = raw_input('')
