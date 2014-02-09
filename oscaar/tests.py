'''
Created on Sep 12, 2013

@author: Dharmatej Mikkilineni
'''
import unittest
from oscaarGUI import (OscaarFrame, wx, os, oscaar, InvalidParameter,
                       checkParams)
IL = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                  "testFiles")
IL += os.sep


class Test(unittest.TestCase):

    def setUp(self):
        self.app = wx.PySimpleApp()
        self.of = OscaarFrame(parent=None, objectID=-1)

    def tearDown(self):
        self.of.Destroy()

    def testOscaarFrameSetup(self):
        self.assertEqual(self.of.paths.boxList[1].GetValue(), "")
        self.assertEqual(self.of.paths.boxList[2].GetValue(), "")
        self.assertEqual(self.of.paths.boxList[3].GetValue(), "")
        self.assertEqual(self.of.paths.boxList[4].GetValue(), "")
        self.assertEqual(self.of.paths.boxList[5].GetValue(), "")
        self.assertEqual(self.of.leftBox.userParams["zoom"].GetValue(), "15")
        self.assertEqual(self.of.leftBox.userParams["radius"].GetValue(),
                         "4.5")
        self.assertEqual(self.of.leftBox.userParams["smoothing"].GetValue(),
                         "3")
        self.assertEqual(self.of.radioBox.userParams["ingress"].GetValue(),
                         "2013/05/15")
        self.assertEqual(self.of.radioBox.userParams["ingress1"].GetValue(),
                         "10:06:30")
        self.assertEqual(self.of.radioBox.userParams["egress"].GetValue(),
                         "2013/05/15")
        self.assertEqual(self.of.radioBox.userParams["egress1"].GetValue(),
                         "11:02:35")
        self.assertTrue(self.of.radioBox.userParams["rbTrackPlot1"].GetValue())
        self.assertTrue(self.of.radioBox.userParams["rbPhotPlot1"].GetValue())
        self.assertTrue(self.of.radioBox.userParams["rbFitAfterPhot"
                                                    ].GetValue())

    def testMainGUIErrors(self):

        # This checks the observatory error message.

        tempIP = InvalidParameter('No Values Entered', empty(None, -1), -1,
                                  stringVal='fits',
                                  secondValue='the path to Data Images')
        self.of.singularExistance(wx.EVT_BUTTON, self.of.loadObservatoryFrame,
                                  'observatory')
        self.assertTrue(self.of.IP.string == tempIP.string
                        and self.of.IP.text.GetLabel()
                        == tempIP.text.GetLabel())

        # Dark Frames Error Messages

        self.of.messageFrame = False
        string = IL.rpartition(os.sep)[0].rpartition(os.sep)[0]
        string += os.sep
        invalidString = "\n" + string + "*.fit,\n" + string + "*.fits"
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='fits',
                                  secondValue='the path to Dark Frames')
        self.of.paths.boxList[1].SetValue(string)
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertTrue(self.of.IP.string == tempIP.string
                        and self.of.IP.text.GetLabel()
                        == tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = IL + "simulatedImg-000"
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='fits',
                                  secondValue='the path to Dark Frames')
        self.of.paths.boxList[1].SetValue(IL + "simulatedImg-000")
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertTrue(self.of.IP.string == tempIP.string
                        and self.of.IP.text.GetLabel()
                        == tempIP.text.GetLabel())

        self.of.paths.boxList[1].SetValue(IL + "simulatedImg-???d.fits")

        # Master Flat Error Messages

        self.of.messageFrame = False
        self.of.paths.boxList[2].SetValue(IL + "stars.reg")
        invalidString = IL + "stars.reg"
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='master',
                                  secondValue='path to the Master Flat')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())
        self.of.paths.boxList[2].SetValue(IL + "masterFlat.fits")

        # Data Images Error Messages

        self.of.messageFrame = False
        invalidString = 'No Values Entered'
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='fits',
                                  secondValue='the path to Data Images')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        string = IL.rpartition(os.sep)[0].rpartition(os.sep)[0]
        string += os.sep
        invalidString = "\n" + string + "*.fit,\n" + string + "*.fits"
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='fits',
                                  secondValue='the path to Data Images')
        self.of.paths.boxList[3].SetValue(string)
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())
        self.of.paths.boxList[3].SetValue(IL + "simulatedImg-???r.fits")

        # Regions File Error Messages

        self.of.messageFrame = False
        invalidString = ''
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='emptyReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: \nReference:  "
        self.of.paths.boxList[4].SetValue(', ; ')
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %ssimulatedImg-000r.fits\nReference: " % IL
        self.of.paths.boxList[4].SetValue("%ssimulatedImg-000r.fits" % IL)
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %soutput1.pkl\nReference: %ssimulatedImg" \
                        "-000r.fits" % (IL, IL)

        self.of.paths.boxList[4].SetValue("%soutput1.pkl,%ssimulatedImg-000" \
                                          "r.fits" % (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %sstars.reg\nReference: " % IL

        self.of.paths.boxList[4].SetValue("%smyReg.reg,%ssimulatedImg-000" \
                                          "r.fits;%sstars.reg" % (IL, IL, IL))

        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='outofbounds')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %ssimulatedImg-000f.fits\nReference: %s" \
                        "simulatedImg-???d.fits" % (IL, IL)

        self.of.paths.boxList[4].SetValue("%ssimulatedImg-000f.fits,%s" \
                                          "simulatedImg-???d.fits" % (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %sstars.reg\nReference: %soutput1.pkl" % \
                        (IL, IL)

        self.of.paths.boxList[4].SetValue("%sstars.reg,%soutput1.pkl;" %
                                          (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidRef')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %sstars.reg\nReference: %ssimulatedImg-" \
                        "000d.fits" % (IL, IL)
        self.of.paths.boxList[4].SetValue("%sstars.reg,%ssimulatedImg-000" \
                                          "d.fits" % (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidRefExist')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: \nReference: %smyReg.reg" % IL
        self.of.paths.boxList[4].SetValue("%smyReg.reg;,%smyReg.reg" %
                                          (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidReg')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %smyReg.reg\nReference: " % IL
        self.of.paths.boxList[4].SetValue("%smyReg.reg;%smyReg.reg,;" %
                                          (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidRef')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %smyReg.reg\nReference: %ssimulatedImg-" \
                         "000d.fits" % (IL, IL)

        self.of.paths.boxList[4].SetValue("%smyReg.reg;%smyReg.reg,%s" \
                                           "simulatedImg-000d.fits;" %
                                           (IL, IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='invalidRefExist')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = "\nRegions: %smyReg.reg\nReference: " % IL

        self.of.paths.boxList[4].SetValue("%smyReg.reg;%smyReg.reg;" %
                                          (IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='outofbounds')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = ("\nRegions: %smyReg.reg\nReference: %ssimulatedImg-" \
                         "003r.fits\nBecause ---\nRegions: %smyReg.reg\nIs " \
                         "already associated with:\nReference: %ssimulated" \
                         "Img-000r.fits" % (IL, IL, IL, IL))
        self.of.paths.boxList[4].SetValue("%smyReg.reg;%smyReg.reg,%s" \
                                          "simulatedImg-003r.fits;" %
                                          (IL, IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='regionsDup')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())

        self.of.messageFrame = False
        invalidString = ("\nRegions: %sstars.reg\nReference: %ssimulatedImg-" \
                         "000r.fits\nBecause ---\nRegions: %smyReg.reg\nIs " \
                         "already associated with the reference file." %
                         (IL, IL, IL))

        self.of.paths.boxList[4].SetValue("%smyReg.reg;%sstars.reg,%s" \
                                          "simulatedImg-000r.fits;" %
                                          (IL, IL, IL))
        tempIP = InvalidParameter(invalidString, empty(None, -1), -1,
                                  stringVal='referenceImageDup')
        self.of.runOscaar(wx.EVT_BUTTON)
        self.assertEqual(self.of.IP.string, tempIP.string)
        self.assertEqual(self.of.IP.text.GetLabel(), tempIP.text.GetLabel())
        self.of.paths.boxList[4].SetValue("%sstars.reg" % IL)

    def testCheckParams(self):
        tupleList = [
            (0.11, 'Rp/Rs'),
            (14.1, 'a/Rs'),
            (1.580400, 'per'),
            (90.0, 'inc'),
            (0.0, 'ecc'),
            (2456427.9425593214, 't0'),
            (0.23, 'gamma1'),
            (0.30, 'gamma2'),
            (0.0, 'pericenter'),
            (10, 'saveiteration'),
            (0.30, 'acceptance'),
            (0.20, 'burnfrac'),
            (10000, 'number'),
            ]
        self.failUnless(checkParams(self, tupleList))

class empty(wx.Frame):

    def __init__(self, parent, objectID):
        wx.Frame.__init__(self, None, -1)
        self.messageFrame = False
        self.Center()
        self.Show()


if __name__ == '__main__':
    unittest.main()
