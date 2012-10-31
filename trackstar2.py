def trackstar2(scidata, est_x, est_y, hww, est_sigma, plots=None):
    scidata2 = scidata[est_x-hww:est_x+hww,est_y-hww:est_y+hww]
    data2 = scidata2                                ## Crop analysis around
    [dim1,dim2] = data2.shape                       ## the star of interest
    dataerr2 = np.ones([dim1,dim2])*200

    npdata2 = np.array(data2,dtype=float)

    X = np.zeros([dim2,dim1],dtype=int)             ## Create x and y arrays
    X[:] = np.arange(0,dim1)                        ## for plotting the CCD
    Y = np.zeros([dim1,dim2],dtype=int)             ## data in 3D
    Y[:] = np.arange(0,dim2)
    Y = np.transpose(Y)
    if plots == 'on':
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_wireframe(X,Y,npdata2,color='r')

    x = range(0,dim2)
    y = range(0,dim1)
    z = npdata2
    zerr = dataerr2
                                                    ## Create 2D gaussian function
                                                    ## and the chi^2 function that
                                                    ## minuit will attempt to minimize

    def gauss2D(x, y, amp, xcenter, ycenter, sigma, offset):
        return amp*math.exp(((-(x-xcenter)**2)/(2*sigma**2))+
                            ((-(y-ycenter)**2)/(2*sigma**2)))+offset

    def chi2(amp, xcenter, ycenter, sigma, offset):
        c2 = 0.
        for i in range(0,len(x)):
            for j in range(0,len(y)):
                c2 += (gauss2D(x[i], y[j], amp, xcenter, ycenter, sigma, offset)
                       - float(z[i][j]))**2 / float(zerr[i][j])**2
        return c2

    ##minrun = minuit.Minuit(chi2, amp=11, xcenter=3.5, ycenter=5, sigma=2, offset = 1)
    est_offset = np.median(z)
    try: 
        est_amp = np.max(z)-est_offset
        [est_maxx,est_maxy] = np.where(z==np.max(z))
    except ValueError:
        est_amp = 750.
        [est_maxx,est_maxy] = [hww,hww]
##    print "est amp:",est_amp

    minrun = minuit.Minuit(chi2, amp=est_amp, xcenter=est_maxx, ycenter=est_maxy, sigma=est_sigma, offset = est_offset)
    minrun.strategy = 2
    minrun.migrad()                                 ## Suggest initial fit parameters,
    minrun.hesse()                                  ## attempt to fit
    print minrun.values

    amp_fit = minrun.values['amp']                  ## Capture best fit parameters
    xcenter_fit = minrun.values['xcenter'] 
    ycenter_fit = minrun.values['ycenter']
    sigma_fit = minrun.values['sigma']
    offset_fit = minrun.values['offset']

    yfit = np.zeros([dim2,dim1])                    ## Generate plot of best fit
    for i in range(0,len(x)):
        for j in range(0,len(y)):
            yfit[i][j] = gauss2D(x[i], y[j], amp_fit, xcenter_fit, ycenter_fit, sigma_fit, offset_fit)

    if plots == 'on':
        ax.plot_surface(X,Y,yfit, rstride=1, cstride=1)
        plt.show()
    ## *******</from gauss4.py>**********
        
    return [xcenter_fit, ycenter_fit, sigma_fit]
