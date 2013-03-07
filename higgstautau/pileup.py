from rootpy.tree.filtering import EventFilter

from externaltools import PileupReweighting
from ROOT import Root


def get_pileup_reweighting_tool(year, use_defaults=True):

    # Initialize the pileup reweighting tool
    pileup_tool = Root.TPileupReweighting()
    if year == 2011:
        if use_defaults:
            pileup_tool.AddConfigFile(
                PileupReweighting.get_resource(
                    'mc11b_defaults.prw.root'))
        else:
            pileup_tool.AddConfigFile(
                'lumi/2011/hadhad/'
                'TPileupReweighting.mc11.prw.root')
        # https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/InDetTrackingPerformanceGuidelines
        pileup_tool.SetDataScaleFactors(1./0.97)
        pileup_tool.AddLumiCalcFile(
                'lumi/2011/hadhad/'
                'ilumicalc_histograms_None_178044-191933.root')
    elif year == 2012:
        if use_defaults:
            pileup_tool.AddConfigFile(
                PileupReweighting.get_resource(
                    'mc12a_defaults.prw.root'))
        else:
            pileup_tool.AddConfigFile(
                'lumi/2012/hadhad/'
                'TPileupReweighting.mc12.prw.root')
        # https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/InDetTrackingPerformanceGuidelines
        pileup_tool.SetDataScaleFactors(1./1.11)
        pileup_tool.AddLumiCalcFile(
                'lumi/2012/hadhad/'
                'ilumicalc_histograms_None_200842-215643.root')
    else:
        raise ValueError('No pileup reweighting defined for year %d' %
                year)
    # discard unrepresented data (with mu not simulated in MC)
    pileup_tool.SetUnrepresentedDataAction(2)
    pileup_tool.Initialize()
    return pileup_tool


class PileupTemplates(EventFilter):

    def __init__(self, year, passthrough=False, **kwargs):

        if not passthrough:
            # initialize the pileup reweighting tool
            self.pileup_tool = Root.TPileupReweighting()
            if year == 2011:
                self.pileup_tool.UsePeriodConfig("MC11b")
            elif year == 2012:
                self.pileup_tool.UsePeriodConfig("MC12a")
            self.pileup_tool.Initialize()

        super(PileupTemplates, self).__init__(
                passthrough=passthrough,
                **kwargs)

    def passes(self, event):

        self.pileup_tool.Fill(
            event.RunNumber,
            event.mc_channel_number,
            event.mc_event_weight,
            event.averageIntPerXing)
        return True

    def finalize(self):

        if not self.passthrough:
            # write the pileup reweighting file
            self.pileup_tool.WriteToFile()


class PileupReweight(EventFilter):
    """
    Currently only implements hadhad reweighting
    """
    def __init__(self, tool, tree, passthrough=False, **kwargs):

        if not passthrough:
            self.tree = tree
            self.tool = tool

        super(PileupReweight, self).__init__(
                passthrough=passthrough,
                **kwargs)

    def passes(self, event):

        # set the pileup and period weights
        self.tree.pileup_weight = self.tool.GetPrimaryWeight(
                event.RunNumber,
                event.mc_channel_number,
                event.averageIntPerXing)
        self.tree.period_weight = self.tool.GetPeriodWeight(
                event.RunNumber,
                event.mc_channel_number)
        return True


class averageIntPerXingPatch(EventFilter):
    """
    https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/ExtendedPileupReweighting:

    NOTE (23/01/2013): A bug has been found in the d3pd making code, causing
    all MC12 samples to have a few of the averageIntPerXing values incorrectly set
    (some should be 0 but are set to 1). The bug does not affect data. To resolve
    this, when reading this branch, for both prw file generating and for when
    retrieving pileup weights, you should amend the value with the following line
    of code:

    averageIntPerXing = (isSimulation && lbn==1 && int(averageIntPerXing+0.5)==1) ? 0. : averageIntPerXing;
    """

    def passes(self, event):

        if event.lbn == 1 and int(event.averageIntPerXing + 0.5) == 1:
            event.averageIntPerXing = 0.
        return True
